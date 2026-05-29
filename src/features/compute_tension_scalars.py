#!/usr/bin/env python3
"""
Phase 2 tension scalar computation for COSMOS2025.

Creates the plausibility-filtered analysis sample, materializes cross-code
LePhare/CIGALE disagreement metrics, and writes a markdown diagnostic report.

Usage:
    source /opt/agents/venv/bin/activate
    cd /opt/repos/cosmos2025-anomalies
    python src/features/compute_tension_scalars.py

Outputs:
    catalog.v_analysis_sample
        Materialized view containing one `id` column for the clean analysis
        sample.
    catalog.tension_scalars
        Persistent table containing raw deltas, propagated uncertainties,
        error-normalized tension metrics, chi2 context, and quality metadata.
    docs/phase2-tension-diagnostic-report.md
        Markdown validation report summarizing sample attrition and tension
        distribution diagnostics.
"""

import math
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import yaml
from dotenv import load_dotenv

# AI NOTE: These sigma_sys values are calibration parameters, not permanent
# physical constants. Starting values come from Pacifici et al. 2023
# (CANDELS), and the spec06 diagnostic report confirmed they are adequate for
# this COSMOS-Web run.
SIGMA_SYS_MASS = 0.1
SIGMA_SYS_SFR = 0.2
LN10 = 2.302585

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = Path("/opt/agents/.env")
REPORT_PATH = REPO_ROOT / "docs" / "phase2-tension-diagnostic-report.md"


def load_config():
    """Load repository path and database configuration.

    Returns:
        dict: Parsed `configs/data_paths.yaml` contents.

    Side effects:
        Reads the YAML configuration file from the repository.
    """
    with open(REPO_ROOT / "configs" / "data_paths.yaml") as f:
        return yaml.safe_load(f)


def get_db_connection(config):
    """Open a PostgreSQL connection using environment-backed credentials.

    Args:
        config: Parsed repository configuration containing the `database`
            section and environment variable names.

    Returns:
        psycopg2.connection: Open connection to the configured database.

    Side effects:
        Loads `/opt/agents/.env` into the process environment.
    """
    load_dotenv(ENV_FILE)
    db = config["database"]
    return psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["database_name"],
    )


def execute(cur, sql):
    """Execute a SQL statement through an existing cursor.

    Args:
        cur: Open psycopg2 cursor.
        sql: SQL statement to execute.

    Returns:
        None.

    Side effects:
        Mutates database state for DDL and DML statements.
    """
    cur.execute(sql)


def fetch_one(cur, sql):
    """Execute a scalar query and return its first column.

    Args:
        cur: Open psycopg2 cursor.
        sql: SQL statement expected to return at most one meaningful row.

    Returns:
        First column of the first row, or None if the query returns no rows.

    Side effects:
        Advances the cursor result set.
    """
    cur.execute(sql)
    row = cur.fetchone()
    return row[0] if row else None


def verify_f770w_column(cur):
    """Confirm the F770W weight column name in the live database.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        str: The verified column name, currently `wht_f770w`.

    Raises:
        RuntimeError: If the expected column is absent.

    Side effects:
        Queries PostgreSQL information schema.
    """
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'catalog'
          AND table_name = 'photometry_core'
          AND column_name = 'wht_f770w'
        """
    )
    if cur.fetchone() is None:
        raise RuntimeError("catalog.photometry_core.wht_f770w was not found")
    return "wht_f770w"


def create_analysis_sample(cur):
    """Create and refresh the plausibility-filtered analysis sample view.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        None.

    Side effects:
        Drops and recreates `catalog.v_analysis_sample`, creates its unique
        index, and refreshes the materialized view.
    """
    execute(cur, "DROP MATERIALIZED VIEW IF EXISTS catalog.v_analysis_sample")
    execute(
        cur,
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS catalog.v_analysis_sample AS
        SELECT p.id
        FROM catalog.photometry_core p
        JOIN catalog.lephare l ON l.id = p.id
        JOIN catalog.cigale c ON c.id = p.id
        WHERE p.warn_flag = 0
          AND l.type = 0
          AND p.flag_star_hsc = 0
          AND c.mass IS NOT NULL
          AND c.sfr_inst IS NOT NULL
          AND c.mass > 1e6
          AND l.mass_med > 6.0
          -- AI NOTE: `sfr_inst = 0.0` or `sfr_100myr = 0.0` would make
          -- LOG10(SFR) undefined. Exclude exact-zero SFR at the sample gate
          -- rather than manufacturing infinite downstream tension values.
          AND c.sfr_inst > 0
          AND c.sfr_100myr > 0
          AND l.nbfilt >= 5
        """,
    )
    execute(cur, "CREATE UNIQUE INDEX v_analysis_sample_id_idx ON catalog.v_analysis_sample (id)")
    execute(cur, "REFRESH MATERIALIZED VIEW catalog.v_analysis_sample")


def create_tension_table(cur):
    """Create the persistent table that stores Phase 2 tension metrics.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        None.

    Side effects:
        Drops and recreates `catalog.tension_scalars`.
    """
    execute(cur, "DROP TABLE IF EXISTS catalog.tension_scalars")
    execute(
        cur,
        """
        CREATE TABLE catalog.tension_scalars (
            id INTEGER PRIMARY KEY REFERENCES catalog.photometry_core(id),
            delta_log_mass DOUBLE PRECISION,
            delta_log_sfr_inst DOUBLE PRECISION,
            delta_log_sfr_100 DOUBLE PRECISION,
            delta_log_ssfr DOUBLE PRECISION,
            sigma_log_mass_lp DOUBLE PRECISION,
            sigma_log_mass_cig DOUBLE PRECISION,
            sigma_log_sfr_lp DOUBLE PRECISION,
            sigma_log_sfr_cig_inst DOUBLE PRECISION,
            sigma_log_sfr_cig_100 DOUBLE PRECISION,
            t_mass DOUBLE PRECISION,
            t_sfr_inst DOUBLE PRECISION,
            t_sfr_100 DOUBLE PRECISION,
            chi2_best_lp DOUBLE PRECISION,
            chi2_red_cig DOUBLE PRECISION,
            chi2_ratio DOUBLE PRECISION,
            chi2_red_pctile DOUBLE PRECISION,
            nbfilt INTEGER,
            has_f770w BOOLEAN,
            is_quiescent_lp BOOLEAN
        )
        """,
    )


def build_insert_tension_sql(f770w_column):
    """Build SQL that computes and inserts all tension scalar rows.

    Args:
        f770w_column: Verified F770W weight column in `photometry_core`.

    Returns:
        str: INSERT statement for `catalog.tension_scalars`.

    Side effects:
        None. This function only returns SQL text.
    """
    return f"""
    INSERT INTO catalog.tension_scalars (
        id,
        delta_log_mass,
        delta_log_sfr_inst,
        delta_log_sfr_100,
        delta_log_ssfr,
        sigma_log_mass_lp,
        sigma_log_mass_cig,
        sigma_log_sfr_lp,
        sigma_log_sfr_cig_inst,
        sigma_log_sfr_cig_100,
        t_mass,
        t_sfr_inst,
        t_sfr_100,
        chi2_best_lp,
        chi2_red_cig,
        chi2_ratio,
        chi2_red_pctile,
        nbfilt,
        has_f770w,
        is_quiescent_lp
    )
    WITH base AS (
        SELECT
            s.id,
            -- AI NOTE: Unit mismatch hidden constraint. LePhare physical
            -- parameters are already log10 values. CIGALE physical parameters
            -- are linear. Cross-code deltas must use:
            -- lephare_log10 - LOG10(cigale_linear).
            l.mass_med - LOG(c.mass) AS delta_log_mass,
            l.sfr_med - LOG(c.sfr_inst) AS delta_log_sfr_inst,
            l.sfr_med - LOG(c.sfr_100myr) AS delta_log_sfr_100,
            CASE
                WHEN c.ssfr_cigale IS NULL OR c.ssfr_cigale <= 0 THEN NULL
                ELSE l.ssfr_med - LOG(c.ssfr_cigale)
            END AS delta_log_ssfr,
            (l.mass_u68 - l.mass_l68) / 2.0 AS sigma_log_mass_lp,
            CASE
                -- AI NOTE: CIGALE errors are linear. Propagate to log space
                -- with sigma_log = err / (val * ln(10)), and guard zero or
                -- missing errors so pulls become NULL rather than infinite.
                WHEN c.mass_err IS NULL OR c.mass_err <= 0 THEN NULL
                ELSE c.mass_err / (c.mass * {LN10})
            END AS sigma_log_mass_cig,
            (l.sfr_u68 - l.sfr_l68) / 2.0 AS sigma_log_sfr_lp,
            CASE
                WHEN c.sfr_inst_err IS NULL OR c.sfr_inst_err <= 0 THEN NULL
                ELSE c.sfr_inst_err / (c.sfr_inst * {LN10})
            END AS sigma_log_sfr_cig_inst,
            CASE
                WHEN c.sfr_100myr_err IS NULL OR c.sfr_100myr_err <= 0 THEN NULL
                ELSE c.sfr_100myr_err / (c.sfr_100myr * {LN10})
            END AS sigma_log_sfr_cig_100,
            l.chi2_best AS chi2_best_lp,
            c.chi2_red_best_fit AS chi2_red_cig,
            l.chi2_best / NULLIF(c.chi2_red_best_fit, 0) AS chi2_ratio,
            PERCENT_RANK() OVER (ORDER BY c.chi2_red_best_fit) * 100.0 AS chi2_red_pctile,
            l.nbfilt,
            p.{f770w_column} > 0 AS has_f770w,
            l.ssfr_med < -11.0 AS is_quiescent_lp
        FROM catalog.v_analysis_sample s
        JOIN catalog.photometry_core p ON p.id = s.id
        JOIN catalog.lephare l ON l.id = s.id
        JOIN catalog.cigale c ON c.id = s.id
    )
    SELECT
        id,
        delta_log_mass,
        delta_log_sfr_inst,
        delta_log_sfr_100,
        delta_log_ssfr,
        sigma_log_mass_lp,
        sigma_log_mass_cig,
        sigma_log_sfr_lp,
        sigma_log_sfr_cig_inst,
        sigma_log_sfr_cig_100,
        CASE
            WHEN sigma_log_mass_cig IS NULL THEN NULL
            ELSE delta_log_mass / SQRT(
                POWER(sigma_log_mass_lp, 2) +
                POWER(sigma_log_mass_cig, 2) +
                POWER({SIGMA_SYS_MASS}, 2)
            )
        END AS t_mass,
        CASE
            WHEN sigma_log_sfr_cig_inst IS NULL THEN NULL
            ELSE delta_log_sfr_inst / SQRT(
                POWER(sigma_log_sfr_lp, 2) +
                POWER(sigma_log_sfr_cig_inst, 2) +
                POWER({SIGMA_SYS_SFR}, 2)
            )
        END AS t_sfr_inst,
        CASE
            WHEN sigma_log_sfr_cig_100 IS NULL THEN NULL
            ELSE delta_log_sfr_100 / SQRT(
                POWER(sigma_log_sfr_lp, 2) +
                POWER(sigma_log_sfr_cig_100, 2) +
                POWER({SIGMA_SYS_SFR}, 2)
            )
        END AS t_sfr_100,
        chi2_best_lp,
        chi2_red_cig,
        chi2_ratio,
        chi2_red_pctile,
        nbfilt,
        has_f770w,
        is_quiescent_lp
    FROM base
    """


def populate_tension_table(cur, f770w_column):
    """Populate the tension table and create ranking indexes.

    Args:
        cur: Open psycopg2 cursor.
        f770w_column: Verified F770W weight column name.

    Returns:
        None.

    Side effects:
        Inserts one row per analysis-sample source and creates indexes on the
        primary ranking columns.
    """
    execute(cur, build_insert_tension_sql(f770w_column))
    execute(cur, "CREATE INDEX tension_scalars_t_mass_idx ON catalog.tension_scalars (t_mass)")
    execute(cur, "CREATE INDEX tension_scalars_t_sfr_100_idx ON catalog.tension_scalars (t_sfr_100)")


def fetch_sample_attrition(cur):
    """Fetch source counts after each analysis-sample gate.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        list[tuple[str, int, float]]: Stage label, source count, and percent
        of the full catalog surviving that stage.

    Side effects:
        Runs count queries against the catalog tables and analysis sample.
    """
    stages = [
        (
            "Total catalog",
            "SELECT COUNT(*) FROM catalog.photometry_core",
        ),
        (
            "After Gate 1: catalog security",
            """
            SELECT COUNT(*)
            FROM catalog.photometry_core p
            JOIN catalog.lephare l ON l.id = p.id
            WHERE p.warn_flag = 0
              AND l.type = 0
              AND p.flag_star_hsc = 0
            """,
        ),
        (
            "After Gates 1+2: convergence",
            """
            SELECT COUNT(*)
            FROM catalog.photometry_core p
            JOIN catalog.lephare l ON l.id = p.id
            JOIN catalog.cigale c ON c.id = p.id
            WHERE p.warn_flag = 0
              AND l.type = 0
              AND p.flag_star_hsc = 0
              AND c.mass IS NOT NULL
              AND c.sfr_inst IS NOT NULL
            """,
        ),
        (
            "After Gates 1+2+3: physical plausibility",
            """
            SELECT COUNT(*)
            FROM catalog.photometry_core p
            JOIN catalog.lephare l ON l.id = p.id
            JOIN catalog.cigale c ON c.id = p.id
            WHERE p.warn_flag = 0
              AND l.type = 0
              AND p.flag_star_hsc = 0
              AND c.mass IS NOT NULL
              AND c.sfr_inst IS NOT NULL
              AND c.mass > 1e6
              AND l.mass_med > 6.0
              AND c.sfr_inst > 0
              AND c.sfr_100myr > 0
            """,
        ),
        (
            "After all four gates",
            "SELECT COUNT(*) FROM catalog.v_analysis_sample",
        ),
    ]
    total = None
    rows = []
    for label, sql in stages:
        count = fetch_one(cur, sql)
        if total is None:
            total = count
        pct = (count / total * 100.0) if total else 0.0
        rows.append((label, count, pct))
    return rows


def fetch_pull_stats(cur):
    """Compute summary statistics for tension pull distributions.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        dict: Per-scalar count, location, spread, tail fraction, skewness, and
        excess kurtosis.

    Side effects:
        Runs aggregate queries against `catalog.tension_scalars`.
    """
    stats = {}
    for column in ("t_mass", "t_sfr_100", "t_sfr_inst"):
        cur.execute(
            f"""
            WITH s AS (
                SELECT {column} AS value
                FROM catalog.tension_scalars
                WHERE {column} IS NOT NULL
            )
            SELECT
                COUNT(*)::BIGINT,
                AVG(value),
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value),
                STDDEV_SAMP(value),
                MIN(value),
                MAX(value),
                AVG(CASE WHEN ABS(value) > 2 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN ABS(value) > 3 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN ABS(value) > 5 THEN 1.0 ELSE 0.0 END)
            FROM s
            """
        )
        count, mean, median, stddev, min_value, max_value, gt2, gt3, gt5 = cur.fetchone()
        cur.execute(
            f"""
            WITH s AS (
                SELECT {column} AS value
                FROM catalog.tension_scalars
                WHERE {column} IS NOT NULL
            ),
            moments AS (
                SELECT value, AVG(value) OVER () AS mean, STDDEV_SAMP(value) OVER () AS stddev
                FROM s
            )
            SELECT
                AVG(POWER((value - mean) / NULLIF(stddev, 0), 3)),
                AVG(POWER((value - mean) / NULLIF(stddev, 0), 4)) - 3.0
            FROM moments
            """
        )
        skewness, kurtosis = cur.fetchone()
        stats[column] = {
            "count": count,
            "mean": mean,
            "median": median,
            "stddev": stddev,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "min": min_value,
            "max": max_value,
            "frac_abs_gt_2": gt2,
            "frac_abs_gt_3": gt3,
            "frac_abs_gt_5": gt5,
        }
    return stats


def fetch_scalar(cur, sql):
    """Fetch a scalar query result as a float when present.

    Args:
        cur: Open psycopg2 cursor.
        sql: Scalar SQL statement.

    Returns:
        float | None: Converted scalar value, or None.

    Side effects:
        Advances the cursor result set.
    """
    value = fetch_one(cur, sql)
    return float(value) if value is not None else None


def fetch_chi2_correlations(cur):
    """Compute tension-vs-chi2 decoupling diagnostics.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        dict: Pearson correlations between absolute tension metrics and
        CIGALE reduced chi2.

    Side effects:
        Runs correlation queries against `catalog.tension_scalars`.
    """
    return {
        "abs_t_mass_vs_chi2_red_cig": fetch_scalar(
            cur,
            """
            SELECT CORR(ABS(t_mass), chi2_red_cig)
            FROM catalog.tension_scalars
            WHERE t_mass IS NOT NULL AND chi2_red_cig IS NOT NULL
            """,
        ),
        "abs_t_sfr_100_vs_chi2_red_cig": fetch_scalar(
            cur,
            """
            SELECT CORR(ABS(t_sfr_100), chi2_red_cig)
            FROM catalog.tension_scalars
            WHERE t_sfr_100 IS NOT NULL AND chi2_red_cig IS NOT NULL
            """,
        ),
    }


def fetch_sfr_stability(cur):
    """Compute instantaneous-vs-100 Myr SFR tension stability diagnostics.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        dict: SFR tension correlation, sign mismatch count, and top-1000
        ranking instability count.

    Side effects:
        Runs aggregate and ranking queries against `catalog.tension_scalars`.
    """
    return {
        "corr_t_sfr_inst_t_sfr_100": fetch_scalar(
            cur,
            """
            SELECT CORR(t_sfr_inst, t_sfr_100)
            FROM catalog.tension_scalars
            WHERE t_sfr_inst IS NOT NULL AND t_sfr_100 IS NOT NULL
            """,
        ),
        "sign_mismatch_count": fetch_one(
            cur,
            """
            SELECT COUNT(*)
            FROM catalog.tension_scalars
            WHERE t_sfr_inst IS NOT NULL
              AND t_sfr_100 IS NOT NULL
              AND SIGN(t_sfr_inst) <> SIGN(t_sfr_100)
            """,
        ),
        "top1000_inst_not_top1000_100": fetch_one(
            cur,
            """
            WITH inst AS (
                SELECT id
                FROM catalog.tension_scalars
                WHERE t_sfr_inst IS NOT NULL
                ORDER BY ABS(t_sfr_inst) DESC
                LIMIT 1000
            ),
            avg100 AS (
                SELECT id
                FROM catalog.tension_scalars
                WHERE t_sfr_100 IS NOT NULL
                ORDER BY ABS(t_sfr_100) DESC
                LIMIT 1000
            )
            SELECT COUNT(*)
            FROM inst
            LEFT JOIN avg100 USING (id)
            WHERE avg100.id IS NULL
            """,
        ),
    }


def fetch_zombie_verification(cur):
    """Fetch plausibility-floor diagnostics for residual zombie leakage.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        dict: CIGALE and LePhare mass ranges plus the count of residual
        extreme mass-disagreement outliers.

    Side effects:
        Joins the tension table back to source SED fitting tables.
    """
    cur.execute(
        """
        SELECT
            MIN(LOG(c.mass)),
            MAX(LOG(c.mass)),
            MIN(l.mass_med),
            MAX(l.mass_med),
            COUNT(*) FILTER (WHERE ABS(t.delta_log_mass) > 3.0)
        FROM catalog.tension_scalars t
        JOIN catalog.cigale c ON c.id = t.id
        JOIN catalog.lephare l ON l.id = t.id
        """
    )
    row = cur.fetchone()
    return {
        "min_log10_cigale_mass": row[0],
        "max_log10_cigale_mass": row[1],
        "min_lephare_mass_med": row[2],
        "max_lephare_mass_med": row[3],
        "extreme_delta_log_mass_count": row[4],
    }


def fetch_context(cur):
    """Fetch F770W coverage and LePhare quiescent-context diagnostics.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        dict: Overall counts and four subgroup rows for quiescent and F770W
        coverage combinations.

    Side effects:
        Runs aggregate queries against `catalog.tension_scalars`.
    """
    total = fetch_one(cur, "SELECT COUNT(*) FROM catalog.tension_scalars")
    has_f770w_count = fetch_one(
        cur, "SELECT COUNT(*) FROM catalog.tension_scalars WHERE has_f770w"
    )
    quiescent_count = fetch_one(
        cur, "SELECT COUNT(*) FROM catalog.tension_scalars WHERE is_quiescent_lp"
    )
    cur.execute(
        """
        SELECT
            is_quiescent_lp,
            has_f770w,
            COUNT(*)::BIGINT,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ABS(t_sfr_100))
                FILTER (WHERE t_sfr_100 IS NOT NULL)
        FROM catalog.tension_scalars
        GROUP BY is_quiescent_lp, has_f770w
        """
    )
    labels = {
        (True, True): "Quiescent with F770W",
        (True, False): "Quiescent without F770W",
        (False, True): "Star-forming with F770W",
        (False, False): "Star-forming without F770W",
    }
    groups_by_key = {
        (is_quiescent, has_f770w): {
            "population": labels[(is_quiescent, has_f770w)],
            "count": count,
            "percentage": (count / total * 100.0) if total else 0.0,
            "median_abs_t_sfr_100": median_abs_t,
        }
        for is_quiescent, has_f770w, count, median_abs_t in cur.fetchall()
    }
    groups = [
        groups_by_key.get(
            key,
            {
                "population": label,
                "count": 0,
                "percentage": 0.0,
                "median_abs_t_sfr_100": None,
            },
        )
        for key, label in labels.items()
    ]
    return {
        "total": total,
        "has_f770w_count": has_f770w_count,
        "quiescent_count": quiescent_count,
        "groups": groups,
    }


def format_number(value, digits=3):
    """Format a numeric report value for markdown tables.

    Args:
        value: Numeric or string-like value to format.
        digits: Decimal places for float values.

    Returns:
        str: Human-readable table cell value.

    Side effects:
        None.
    """
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        return f"{value:,.{digits}f}"
    return str(value)


def format_pct(fraction):
    """Format a fractional value as a percentage string.

    Args:
        fraction: Fractional value such as 0.125, or None.

    Returns:
        str: Percentage string with two decimal places, or `NULL`.

    Side effects:
        None.
    """
    if fraction is None:
        return "NULL"
    return f"{float(fraction) * 100.0:.2f}%"


def render_report(
    generated_at,
    sample_attrition,
    pull_stats,
    chi2_correlations,
    sfr_stability,
    zombie_verification,
    context,
):
    """Render the diagnostic report as markdown.

    Args:
        generated_at: ISO timestamp for the report run.
        sample_attrition: Gate-by-gate source counts.
        pull_stats: Summary statistics for the tension metrics.
        chi2_correlations: Tension-vs-chi2 correlation diagnostics.
        sfr_stability: Instantaneous-vs-100 Myr SFR stability diagnostics.
        zombie_verification: Mass-floor and extreme-outlier diagnostics.
        context: F770W and quiescent subgroup diagnostics.

    Returns:
        str: Complete markdown report.

    Side effects:
        None.
    """
    lines = [
        "# Phase 2 Tension Scalar Diagnostic Report",
        "",
        f"Generated: {generated_at}",
        "",
        "Sigma systematics used for this run:",
        f"- Mass: {SIGMA_SYS_MASS:.3f} dex",
        f"- SFR: {SIGMA_SYS_SFR:.3f} dex",
        "",
        "## A. Sample Attrition",
        "",
        "| Stage | Sources | Catalog Survival |",
        "|---|---:|---:|",
    ]
    for label, count, pct in sample_attrition:
        lines.append(f"| {label} | {count:,} | {pct:.2f}% |")

    lines.extend(
        [
            "",
            "## B. Pull Distribution Analysis",
            "",
            "| Scalar | Count | Mean | Median | Std | Skewness | Excess Kurtosis | Min | Max | abs(T) > 2 | abs(T) > 3 | abs(T) > 5 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for column in ("t_mass", "t_sfr_100", "t_sfr_inst"):
        stats = pull_stats.get(column, {})
        lines.append(
            "| {column} | {count} | {mean} | {median} | {stddev} | {skewness} | "
            "{kurtosis} | {min} | {max} | {gt2} | {gt3} | {gt5} |".format(
                column=column,
                count=format_number(stats.get("count")),
                mean=format_number(stats.get("mean")),
                median=format_number(stats.get("median")),
                stddev=format_number(stats.get("stddev")),
                skewness=format_number(stats.get("skewness")),
                kurtosis=format_number(stats.get("kurtosis")),
                min=format_number(stats.get("min")),
                max=format_number(stats.get("max")),
                gt2=format_pct(stats.get("frac_abs_gt_2")),
                gt3=format_pct(stats.get("frac_abs_gt_3")),
                gt5=format_pct(stats.get("frac_abs_gt_5")),
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: if the bulk distribution is well-calibrated, the standard deviation should be near 1.0 and the mean near 0.0. Heavy tails (excess kurtosis) confirm survival of anomalous populations. If the standard deviation is substantially greater than 1.0, sigma_sys is too low. If substantially less, sigma_sys is too high.",
            "",
            "## C. Tension vs Chi2 Decoupling Check",
            "",
            "| Pair | Pearson r |",
            "|---|---:|",
            f"| abs(t_mass) vs chi2_red_cig | {format_number(chi2_correlations.get('abs_t_mass_vs_chi2_red_cig'))} |",
            f"| abs(t_sfr_100) vs chi2_red_cig | {format_number(chi2_correlations.get('abs_t_sfr_100_vs_chi2_red_cig'))} |",
            "",
            "Interpretation: if correlation is strong (|r| > 0.3), the systematic floor is insufficient and tension is tracking fit quality rather than physical disagreement. This would indicate sigma_sys needs to be increased.",
            "",
            "## D. SFR Timescale Stability",
            "",
            "| Diagnostic | Value |",
            "|---|---:|",
            f"| Pearson r: t_sfr_inst vs t_sfr_100 | {format_number(sfr_stability.get('corr_t_sfr_inst_t_sfr_100'))} |",
            f"| Sign mismatch count | {format_number(sfr_stability.get('sign_mismatch_count'))} |",
            f"| Top 1000 by abs(t_sfr_inst) not in top 1000 by abs(t_sfr_100) | {format_number(sfr_stability.get('top1000_inst_not_top1000_100'))} |",
            "",
            "Interpretation: high instability suggests instantaneous SFR artifacts; t_sfr_100 should be the primary scalar for downstream anomaly detection.",
            "",
            "## E. Zombie Leakage Verification",
            "",
            "| Diagnostic | Value |",
            "|---|---:|",
            f"| Min LOG10(CIGALE mass) | {format_number(zombie_verification.get('min_log10_cigale_mass'))} |",
            f"| Max LOG10(CIGALE mass) | {format_number(zombie_verification.get('max_log10_cigale_mass'))} |",
            f"| Min LePhare mass_med | {format_number(zombie_verification.get('min_lephare_mass_med'))} |",
            f"| Max LePhare mass_med | {format_number(zombie_verification.get('max_lephare_mass_med'))} |",
            f"| Sources with abs(delta_log_mass) > 3.0 dex | {format_number(zombie_verification.get('extreme_delta_log_mass_count'))} |",
            "",
            "## F. F770W Coverage and Quiescent Context",
            "",
        ]
    )
    total = context.get("total") or 0
    has_f770w_count = context.get("has_f770w_count") or 0
    quiescent_count = context.get("quiescent_count") or 0
    lines.extend(
        [
            f"- F770W coverage: {has_f770w_count:,} / {total:,} ({(has_f770w_count / total * 100.0) if total else 0.0:.2f}%)",
            f"- LePhare quiescent: {quiescent_count:,} / {total:,} ({(quiescent_count / total * 100.0) if total else 0.0:.2f}%)",
            "",
            "| Population | Count | Percentage | Median abs(t_sfr_100) |",
            "|---|---:|---:|---:|",
        ]
    )
    for group in context.get("groups", []):
        lines.append(
            f"| {group['population']} | {group['count']:,} | "
            f"{group['percentage']:.2f}% | {format_number(group['median_abs_t_sfr_100'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_report(cur):
    """Generate and write the Phase 2 diagnostic markdown report.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        None.

    Side effects:
        Queries diagnostic statistics and writes
        `docs/phase2-tension-diagnostic-report.md`.
    """
    report = render_report(
        generated_at=datetime.now(timezone.utc).isoformat(),
        sample_attrition=fetch_sample_attrition(cur),
        pull_stats=fetch_pull_stats(cur),
        chi2_correlations=fetch_chi2_correlations(cur),
        sfr_stability=fetch_sfr_stability(cur),
        zombie_verification=fetch_zombie_verification(cur),
        context=fetch_context(cur),
    )
    REPORT_PATH.write_text(report)


def run_validations(cur):
    """Print validation checks for created Phase 2 database objects.

    Args:
        cur: Open psycopg2 cursor.

    Returns:
        None.

    Side effects:
        Prints validation counts to stdout.
    """
    validations = [
        (
            "analysis sample row count",
            "SELECT COUNT(*) FROM catalog.v_analysis_sample",
        ),
        (
            "tension scalar row count",
            "SELECT COUNT(*) FROM catalog.tension_scalars",
        ),
        (
            "analysis sample rows with NULL CIGALE mass or SFR",
            """
            SELECT COUNT(*)
            FROM catalog.v_analysis_sample s
            JOIN catalog.cigale c ON c.id = s.id
            WHERE c.mass IS NULL OR c.sfr_inst IS NULL
            """,
        ),
        (
            "analysis sample rows below CIGALE mass floor",
            """
            SELECT COUNT(*)
            FROM catalog.v_analysis_sample s
            JOIN catalog.cigale c ON c.id = s.id
            WHERE c.mass <= 1e6
            """,
        ),
        (
            "analysis sample rows with non-positive SFR",
            """
            SELECT COUNT(*)
            FROM catalog.v_analysis_sample s
            JOIN catalog.cigale c ON c.id = s.id
            WHERE c.sfr_inst <= 0 OR c.sfr_100myr <= 0
            """,
        ),
        (
            "analysis sample rows with nbfilt < 5",
            """
            SELECT COUNT(*)
            FROM catalog.v_analysis_sample s
            JOIN catalog.lephare l ON l.id = s.id
            WHERE l.nbfilt < 5
            """,
        ),
        (
            "NULL primary scalar rows",
            """
            SELECT COUNT(*)
            FROM catalog.tension_scalars
            WHERE delta_log_mass IS NULL OR t_mass IS NULL OR t_sfr_100 IS NULL
            """,
        ),
        (
            "infinite tension rows",
            """
            SELECT COUNT(*)
            FROM catalog.tension_scalars
            WHERE t_mass IN ('Infinity'::float8, '-Infinity'::float8)
               OR t_sfr_inst IN ('Infinity'::float8, '-Infinity'::float8)
               OR t_sfr_100 IN ('Infinity'::float8, '-Infinity'::float8)
            """,
        ),
        (
            "NULL chi2_red_pctile rows",
            "SELECT COUNT(*) FROM catalog.tension_scalars WHERE chi2_red_pctile IS NULL",
        ),
    ]
    for label, sql in validations:
        print(f"  {label}: {fetch_one(cur, sql):,}")
    cur.execute(
        """
        SELECT MIN(chi2_red_pctile), MAX(chi2_red_pctile)
        FROM catalog.tension_scalars
        """
    )
    min_pct, max_pct = cur.fetchone()
    print(f"  chi2_red_pctile range: {min_pct:.3f} to {max_pct:.3f}")


def main():
    """Run the end-to-end Phase 2 tension scalar workflow.

    Returns:
        None.

    Side effects:
        Opens a database connection, recreates the materialized view and
        tension table, writes the diagnostic report, and prints progress to
        stdout.
    """
    print("Loading configuration...")
    config = load_config()
    with get_db_connection(config) as conn:
        with conn.cursor() as cur:
            print("Verifying F770W weight column...")
            f770w_column = verify_f770w_column(cur)
            print("Creating materialized view...")
            create_analysis_sample(cur)
            print("Creating tension scalar table...")
            create_tension_table(cur)
            print("Computing tension scalars...")
            populate_tension_table(cur, f770w_column)
            print("Validating database objects...")
            run_validations(cur)
            print("Generating diagnostic report...")
            generate_report(cur)
        conn.commit()
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
