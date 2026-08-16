#!/usr/bin/env python3
"""
COSMOS2025 Post-ETL Verification

Purpose:
    Runs a structured series of checks against the cosmos2025 database on
    psql01 and writes both Markdown and HTML reports.  The verification covers
    row counts, sentinel residuals, NULL distributions, cross-table integrity,
    value ranges, unit validation, and science-readiness spot checks.

    A "PASS" means the data loaded correctly and is consistent with known
    properties of the COSMOS-Web DR1 catalog.  "FAIL" indicates a data
    integrity problem that must be resolved before analysis.  "WARN" flags
    unexpected-but-possible conditions.  "INFO" records reference values.

Usage:
    source /opt/agents/venv/bin/activate
    doppler run --project ml01 --config prd -- \
        python src/etl/verify_catalog.py
    (run from /opt/agents/repos/cosmos2025-anomalies)

Output:
    docs/verification-report.md         — Markdown summary of all checks
    docs/phase1-verification-report.html — Full HTML report with embedded charts

Dependencies:
    matplotlib (Agg backend), numpy, psycopg2, pyyaml
"""

import base64
import io
import logging
import os
import sys
import time
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import psycopg2
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

REPO_ROOT = "/opt/agents/repos/cosmos2025-anomalies"
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "verification-report.md")
HTML_REPORT_PATH = os.path.join(REPO_ROOT, "docs", "phase1-verification-report.html")

EXPECTED_CORE_ROWS = 784016

# COSMOS-Web DR1 field boundaries (approximate, degrees).
# Source: Shuntov et al. 2025, COSMOS-Web primary catalog documentation.
# The survey covers ~0.54 deg² centered on RA~150.1, Dec~2.2.
RA_MIN, RA_MAX = 149.3, 150.8
DEC_MIN, DEC_MAX = 1.5, 3.0


def load_config():
    """Load data_paths.yaml from the repository configs directory.

    Returns:
        dict: Parsed YAML config.
    """
    with open(os.path.join(REPO_ROOT, "configs", "data_paths.yaml")) as f:
        return yaml.safe_load(f)


def get_db_connection(config):
    """Connect to PostgreSQL on psql01 using Doppler-injected credentials.

    Args:
        config: Parsed data_paths.yaml dict.

    Returns:
        psycopg2.connection: Open connection to the cosmos2025 database.
    """
    db = config["database"]
    return psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["database_name"],
    )


class Check:
    """Single verification check with pass/fail/warn status."""

    def __init__(self, name, status, detail, value=None):
        self.name = name
        self.status = status  # PASS, FAIL, WARN, INFO
        self.detail = detail
        self.value = value

    def icon(self):
        return {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(
            self.status, "?"
        )


def run_checks(conn):
    """Execute all verification checks. Returns list of (section, [Check])."""
    cur = conn.cursor()
    sections = []

    # =========================================================================
    # 1. ROW COUNTS
    # =========================================================================
    checks = []
    core_tables = {
        "photometry_core": EXPECTED_CORE_ROWS,
        "lephare": EXPECTED_CORE_ROWS,
        "cigale": EXPECTED_CORE_ROWS,
        "morphology": EXPECTED_CORE_ROWS,
    }
    for table, expected in core_tables.items():
        cur.execute(f"SELECT COUNT(*) FROM catalog.{table}")
        count = cur.fetchone()[0]
        status = "PASS" if count == expected else "FAIL"
        checks.append(
            Check(
                f"catalog.{table} row count",
                status,
                f"{count:,} rows (expected {expected:,})",
                count,
            )
        )

    for table in ("lss_overdensity", "galaxy_groups", "galaxy_group_memberships"):
        cur.execute(f"SELECT COUNT(*) FROM catalog.{table}")
        count = cur.fetchone()[0]
        status = "PASS" if count > 0 else "FAIL"
        checks.append(
            Check(f"catalog.{table} row count", status, f"{count:,} rows", count)
        )

    sections.append(("Row Counts", checks))

    # =========================================================================
    # 2. COLUMN COUNTS
    # =========================================================================
    checks = []
    for table in (
        "photometry_core",
        "lephare",
        "cigale",
        "morphology",
        "lss_overdensity",
        "galaxy_groups",
        "galaxy_group_memberships",
    ):
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = 'catalog' AND table_name = %s",
            (table,),
        )
        col_count = cur.fetchone()[0]
        checks.append(
            Check(
                f"catalog.{table} columns",
                "INFO",
                f"{col_count} columns",
                col_count,
            )
        )

    sections.append(("Column Counts", checks))

    # =========================================================================
    # 3. SENTINEL RESIDUAL CHECKS
    # =========================================================================
    checks = []

    sentinel_queries = [
        (
            "lephare.zfinal = -99",
            "SELECT COUNT(*) FROM catalog.lephare WHERE zfinal = -99",
        ),
        (
            "lephare.zfinal = -99.0",
            "SELECT COUNT(*) FROM catalog.lephare WHERE zfinal = -99.0",
        ),
        (
            "lephare.mass_med = -999",
            "SELECT COUNT(*) FROM catalog.lephare WHERE mass_med = -999",
        ),
        (
            "lephare.sfr_med = -999",
            "SELECT COUNT(*) FROM catalog.lephare WHERE sfr_med = -999",
        ),
        (
            "lephare.law_minchi2 = -999",
            "SELECT COUNT(*) FROM catalog.lephare WHERE law_minchi2 = -999",
        ),
        (
            "lephare.mod_minchi2_phys = -99",
            "SELECT COUNT(*) FROM catalog.lephare WHERE mod_minchi2_phys = -99",
        ),
        ("cigale.mass = -999", "SELECT COUNT(*) FROM catalog.cigale WHERE mass = -999"),
        (
            "cigale.sfr_inst = -999",
            "SELECT COUNT(*) FROM catalog.cigale WHERE sfr_inst = -999",
        ),
        (
            "morphology.morph_flag_f444w = 999999",
            "SELECT COUNT(*) FROM catalog.morphology WHERE morph_flag_f444w = 999999",
        ),
        (
            "morphology.morph_flag_f150w = 999999",
            "SELECT COUNT(*) FROM catalog.morphology WHERE morph_flag_f150w = 999999",
        ),
        (
            "photometry_core.id_specz_khostovan25 = -999",
            "SELECT COUNT(*) FROM catalog.photometry_core WHERE id_specz_khostovan25 = -999",
        ),
        (
            "photometry_core.mag_err_model_f444w = -999",
            "SELECT COUNT(*) FROM catalog.photometry_core WHERE mag_err_model_f444w = -999",
        ),
    ]

    for label, query in sentinel_queries:
        cur.execute(query)
        count = cur.fetchone()[0]
        status = "PASS" if count == 0 else "FAIL"
        checks.append(
            Check(
                f"No residual {label}",
                status,
                f"{count:,} rows with sentinel",
                count,
            )
        )

    sections.append(("Sentinel Residual Checks (should all be 0)", checks))

    # =========================================================================
    # 4. NULL DISTRIBUTION (sentinels should now be NULL)
    # =========================================================================
    checks = []

    null_queries = [
        (
            "lephare.zfinal IS NULL",
            "SELECT COUNT(*) FROM catalog.lephare WHERE zfinal IS NULL",
        ),
        (
            "lephare.mass_med IS NULL",
            "SELECT COUNT(*) FROM catalog.lephare WHERE mass_med IS NULL",
        ),
        (
            "lephare.sfr_med IS NULL",
            "SELECT COUNT(*) FROM catalog.lephare WHERE sfr_med IS NULL",
        ),
        (
            "lephare.law_minchi2 IS NULL",
            "SELECT COUNT(*) FROM catalog.lephare WHERE law_minchi2 IS NULL",
        ),
        (
            "cigale.mass IS NULL",
            "SELECT COUNT(*) FROM catalog.cigale WHERE mass IS NULL",
        ),
        (
            "cigale.sfr_inst IS NULL",
            "SELECT COUNT(*) FROM catalog.cigale WHERE sfr_inst IS NULL",
        ),
        (
            "cigale.ssfr_cigale IS NULL",
            "SELECT COUNT(*) FROM catalog.cigale WHERE ssfr_cigale IS NULL",
        ),
        (
            "morphology.morph_flag_f444w IS NULL",
            "SELECT COUNT(*) FROM catalog.morphology WHERE morph_flag_f444w IS NULL",
        ),
        (
            "morphology.morph_flag_f150w IS NULL",
            "SELECT COUNT(*) FROM catalog.morphology WHERE morph_flag_f150w IS NULL",
        ),
        (
            "photometry_core.id_specz_khostovan25 IS NULL",
            "SELECT COUNT(*) FROM catalog.photometry_core WHERE id_specz_khostovan25 IS NULL",
        ),
    ]

    for label, query in null_queries:
        cur.execute(query)
        count = cur.fetchone()[0]
        pct = count / EXPECTED_CORE_ROWS * 100
        status = "PASS" if count > 0 else "WARN"
        checks.append(Check(label, status, f"{count:,} NULL ({pct:.1f}%)", count))

    sections.append(("NULL Distribution (converted sentinels)", checks))

    # =========================================================================
    # 5. CROSS-TABLE JOIN INTEGRITY
    # =========================================================================
    checks = []

    for table in ("lephare", "cigale", "morphology"):
        cur.execute(
            f"SELECT COUNT(*) FROM catalog.photometry_core p "
            f"LEFT JOIN catalog.{table} t ON p.id = t.id "
            f"WHERE t.id IS NULL"
        )
        missing = cur.fetchone()[0]
        status = "PASS" if missing == 0 else "FAIL"
        checks.append(
            Check(
                f"photometry_core -> {table} join completeness",
                status,
                f"{missing:,} IDs in photometry_core missing from {table}",
                missing,
            )
        )

    for table in ("lephare", "cigale", "morphology"):
        cur.execute(
            f"SELECT COUNT(*) FROM catalog.{table} t "
            f"LEFT JOIN catalog.photometry_core p ON t.id = p.id "
            f"WHERE p.id IS NULL"
        )
        orphans = cur.fetchone()[0]
        status = "PASS" if orphans == 0 else "FAIL"
        checks.append(
            Check(
                f"{table} -> photometry_core (no orphans)",
                status,
                f"{orphans:,} orphan IDs in {table}",
                orphans,
            )
        )

    cur.execute(
        "SELECT COUNT(*) FROM catalog.lss_overdensity l "
        "LEFT JOIN catalog.photometry_core p ON l.id = p.id "
        "WHERE p.id IS NULL"
    )
    lss_orphans = cur.fetchone()[0]
    status = "PASS" if lss_orphans == 0 else "WARN"
    checks.append(
        Check(
            "lss_overdensity -> photometry_core (no orphans)",
            status,
            f"{lss_orphans:,} LSS IDs not in photometry_core",
            lss_orphans,
        )
    )

    cur.execute(
        "SELECT COUNT(DISTINCT galid) FROM catalog.galaxy_group_memberships gm "
        "LEFT JOIN catalog.photometry_core p ON gm.galid = p.id "
        "WHERE p.id IS NULL"
    )
    mem_orphans = cur.fetchone()[0]
    status = "PASS" if mem_orphans == 0 else "WARN"
    checks.append(
        Check(
            "group_memberships.galid -> photometry_core",
            status,
            f"{mem_orphans:,} membership galids not in photometry_core",
            mem_orphans,
        )
    )

    cur.execute(
        "SELECT COUNT(DISTINCT gm.group_id) FROM catalog.galaxy_group_memberships gm "
        "LEFT JOIN catalog.galaxy_groups g ON gm.group_id = g.group_id "
        "WHERE g.group_id IS NULL"
    )
    grp_orphans = cur.fetchone()[0]
    status = "PASS" if grp_orphans == 0 else "WARN"
    checks.append(
        Check(
            "group_memberships.group_id -> galaxy_groups",
            status,
            f"{grp_orphans:,} membership group_ids not in galaxy_groups",
            grp_orphans,
        )
    )

    sections.append(("Cross-Table Join Integrity", checks))

    # =========================================================================
    # 6. UNIT VALIDATION
    # =========================================================================
    # CRITICAL DISTINCTION: The two SED fitters report in different unit spaces.
    #
    # LePhare reports physical quantities in LOG10 space:
    #   mass_med = log10(M / M_sun), range ~3 to ~13
    #   sfr_med  = log10(SFR / M_sun yr-1), range ~ -5 to ~4
    #   ssfr_med = log10(sSFR / yr-1), range ~ -14 to ~ -6
    #
    # CIGALE reports in LINEAR space:
    #   mass     = M / M_sun, range ~1e3 to ~1e13
    #   sfr_inst = SFR / M_sun yr-1, range ~1e-5 to ~1e4
    #
    # This section confirms each column's value range is consistent with its
    # expected unit space.  A mismatch would indicate a unit-conversion bug
    # in the ETL or an unexpected catalog format change.
    checks = []

    # LePhare mass_med: log10(M/M_sun), expected range ~3 to ~13
    cur.execute(
        "SELECT MIN(mass_med), MAX(mass_med), AVG(mass_med), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mass_med) "
        "FROM catalog.lephare WHERE mass_med IS NOT NULL"
    )
    lm_min, lm_max, lm_avg, lm_med = cur.fetchone()
    lm_ok = 0 < lm_min and lm_max < 15
    checks.append(
        Check(
            "lephare.mass_med is log10(M/M_sun)",
            "PASS" if lm_ok else "FAIL",
            f"range=[{lm_min:.2f}, {lm_max:.2f}], median={lm_med:.2f} (expected ~3 to ~13)",
        )
    )

    # LePhare sfr_med: log10(SFR / M_sun yr-1), expected range ~ -5 to ~4
    cur.execute(
        "SELECT MIN(sfr_med), MAX(sfr_med), AVG(sfr_med), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sfr_med) "
        "FROM catalog.lephare WHERE sfr_med IS NOT NULL"
    )
    ls_min, ls_max, ls_avg, ls_med = cur.fetchone()
    ls_ok = ls_min < 0 and ls_max < 10
    checks.append(
        Check(
            "lephare.sfr_med is log10(SFR/M_sun yr-1)",
            "PASS" if ls_ok else "FAIL",
            f"range=[{ls_min:.2f}, {ls_max:.2f}], median={ls_med:.2f} (expected ~ -5 to ~4)",
        )
    )

    # LePhare ssfr_med: log10(sSFR / yr-1), expected range ~ -14 to ~ -6
    cur.execute(
        "SELECT MIN(ssfr_med), MAX(ssfr_med), AVG(ssfr_med), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ssfr_med) "
        "FROM catalog.lephare WHERE ssfr_med IS NOT NULL"
    )
    lss_min, lss_max, lss_avg, lss_med = cur.fetchone()
    lss_ok = lss_min < -5 and lss_max < 0
    checks.append(
        Check(
            "lephare.ssfr_med is log10(sSFR/yr-1)",
            "PASS" if lss_ok else "WARN",
            f"range=[{lss_min:.2f}, {lss_max:.2f}], median={lss_med:.2f} (expected ~ -14 to ~ -6)",
        )
    )

    # CIGALE mass: linear M_sun, expected range ~1e3 to ~1e13
    cur.execute(
        "SELECT MIN(mass), MAX(mass), "
        "MIN(LOG10(mass)) FILTER (WHERE mass > 0), "
        "MAX(LOG10(mass)) FILTER (WHERE mass > 0), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LOG10(mass)) "
        "FROM catalog.cigale WHERE mass IS NOT NULL AND mass > 0"
    )
    cm_min, cm_max, cm_log_min, cm_log_max, cm_log_med = cur.fetchone()
    cm_ok = cm_log_min > -15 and cm_log_max < 15
    checks.append(
        Check(
            "cigale.mass is linear M_sun",
            "PASS" if cm_ok else "FAIL",
            f"linear range=[{cm_min:.2e}, {cm_max:.2e}], log10 range=[{cm_log_min:.2f}, {cm_log_max:.2f}], log10 median={cm_log_med:.2f}",
        )
    )

    # CIGALE sfr_inst: linear M_sun/yr, expected range ~1e-5 to ~1e4
    cur.execute(
        "SELECT MIN(sfr_inst), MAX(sfr_inst), "
        "MIN(LOG10(sfr_inst)) FILTER (WHERE sfr_inst > 0), "
        "MAX(LOG10(sfr_inst)) FILTER (WHERE sfr_inst > 0), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LOG10(sfr_inst)) "
        "FROM catalog.cigale WHERE sfr_inst IS NOT NULL AND sfr_inst > 0"
    )
    cs_min, cs_max, cs_log_min, cs_log_max, cs_log_med = cur.fetchone()
    cs_ok = cs_log_max < 10
    checks.append(
        Check(
            "cigale.sfr_inst is linear M_sun/yr",
            "PASS" if cs_ok else "FAIL",
            f"linear range=[{cs_min:.2e}, {cs_max:.2e}], log10 range=[{cs_log_min:.2f}, {cs_log_max:.2f}], log10 median={cs_log_med:.2f}",
        )
    )

    # ssfr_cigale: linear yr-1 (derived as sfr_inst / mass)
    cur.execute(
        "SELECT MIN(LOG10(ssfr_cigale)), MAX(LOG10(ssfr_cigale)), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LOG10(ssfr_cigale)) "
        "FROM catalog.cigale WHERE ssfr_cigale IS NOT NULL AND ssfr_cigale > 0"
    )
    css_log_min, css_log_max, css_log_med = cur.fetchone()
    checks.append(
        Check(
            "cigale.ssfr_cigale is linear yr-1",
            "INFO",
            f"log10 range=[{css_log_min:.2f}, {css_log_max:.2f}], log10 median={css_log_med:.2f} (expected ~ -14 to ~ -6)",
        )
    )

    sections.append(("Unit Validation (LePhare=log10, CIGALE=linear)", checks))

    # =========================================================================
    # 7. VALUE RANGE CHECKS
    # =========================================================================
    checks = []

    cur.execute(
        "SELECT MIN(ra), MAX(ra), MIN(dec), MAX(dec) FROM catalog.photometry_core"
    )
    ra_min, ra_max, dec_min, dec_max = cur.fetchone()
    ra_ok = RA_MIN <= ra_min and ra_max <= RA_MAX
    dec_ok = DEC_MIN <= dec_min and dec_max <= DEC_MAX
    checks.append(
        Check(
            "RA range within COSMOS field",
            "PASS" if ra_ok else "WARN",
            f"[{ra_min:.4f}, {ra_max:.4f}] (expected ~[{RA_MIN}, {RA_MAX}])",
        )
    )
    checks.append(
        Check(
            "Dec range within COSMOS field",
            "PASS" if dec_ok else "WARN",
            f"[{dec_min:.4f}, {dec_max:.4f}] (expected ~[{DEC_MIN}, {DEC_MAX}])",
        )
    )

    # Morphology probabilities should sum to ~1
    cur.execute(
        "SELECT AVG(sph_f444w_mean + disk_f444w_mean + irr_f444w_mean + bd_f444w_mean), "
        "MIN(sph_f444w_mean + disk_f444w_mean + irr_f444w_mean + bd_f444w_mean), "
        "MAX(sph_f444w_mean + disk_f444w_mean + irr_f444w_mean + bd_f444w_mean) "
        "FROM catalog.morphology "
        "WHERE sph_f444w_mean IS NOT NULL"
    )
    prob_avg, prob_min, prob_max = cur.fetchone()
    prob_ok = 0.99 <= prob_avg <= 1.01
    checks.append(
        Check(
            "F444W morphology probs sum to ~1.0",
            "PASS" if prob_ok else "WARN",
            f"avg={prob_avg:.4f}, range=[{prob_min:.4f}, {prob_max:.4f}]",
        )
    )

    # density_excess should be centered around 1 (1+delta)
    cur.execute(
        "SELECT MIN(density_excess), MAX(density_excess), AVG(density_excess), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY density_excess) "
        "FROM catalog.lss_overdensity"
    )
    de_min, de_max, de_avg, de_med = cur.fetchone()
    checks.append(
        Check(
            "density_excess distribution",
            "INFO",
            f"min={de_min:.3f}, max={de_max:.3f}, mean={de_avg:.3f}, median={de_med:.3f}",
        )
    )

    # ssfr_cigale: should have values where both mass and sfr are valid
    cur.execute(
        "SELECT COUNT(*) FROM catalog.cigale WHERE ssfr_cigale IS NOT NULL AND ssfr_cigale > 0"
    )
    ssfr_valid = cur.fetchone()[0]
    checks.append(
        Check(
            "ssfr_cigale valid count",
            "PASS" if ssfr_valid > 0 else "FAIL",
            f"{ssfr_valid:,} sources with ssfr_cigale > 0",
            ssfr_valid,
        )
    )

    sections.append(("Value Range Checks", checks))

    # =========================================================================
    # 8. QUALITY FLAG DISTRIBUTION
    # =========================================================================
    checks = []

    cur.execute(
        "SELECT warn_flag, COUNT(*) FROM catalog.photometry_core "
        "GROUP BY warn_flag ORDER BY warn_flag"
    )
    wf_rows = cur.fetchall()
    for wf, cnt in wf_rows:
        pct = cnt / EXPECTED_CORE_ROWS * 100
        checks.append(
            Check(f"warn_flag = {wf}", "INFO", f"{cnt:,} sources ({pct:.1f}%)", cnt)
        )

    cur.execute("SELECT COUNT(*) FROM catalog.photometry_core WHERE flag_star = true")
    stars = cur.fetchone()[0]
    checks.append(
        Check(
            "flag_star = true",
            "INFO",
            f"{stars:,} stars ({stars / EXPECTED_CORE_ROWS * 100:.1f}%)",
            stars,
        )
    )

    cur.execute(
        "SELECT type, COUNT(*) FROM catalog.lephare GROUP BY type ORDER BY type"
    )
    type_rows = cur.fetchall()
    for tp, cnt in type_rows:
        label = {0: "galaxy", 1: "star", 2: "QSO"}.get(tp, f"type={tp}")
        checks.append(
            Check(f"lephare.type = {tp} ({label})", "INFO", f"{cnt:,} sources", cnt)
        )

    sections.append(("Quality Flag & Classification Distribution", checks))

    # =========================================================================
    # 9. CIGALE NaN COVERAGE (expect ~16-25%)
    # =========================================================================
    checks = []

    cur.execute(
        "SELECT COUNT(*) FROM catalog.cigale WHERE mass IS NULL AND sfr_inst IS NULL"
    )
    cigale_null = cur.fetchone()[0]
    pct = cigale_null / EXPECTED_CORE_ROWS * 100
    checks.append(
        Check(
            "CIGALE fully NULL (unfittable sources)",
            "INFO",
            f"{cigale_null:,} sources ({pct:.1f}%)",
            cigale_null,
        )
    )

    # Also check individual column NULL rates
    for col in ("mass", "sfr_inst", "sfr_100myr", "chi2_best_fit"):
        cur.execute(f"SELECT COUNT(*) FROM catalog.cigale WHERE {col} IS NULL")
        cnt = cur.fetchone()[0]
        pct = cnt / EXPECTED_CORE_ROWS * 100
        checks.append(
            Check(f"cigale.{col} IS NULL", "INFO", f"{cnt:,} ({pct:.1f}%)", cnt)
        )

    sections.append(("CIGALE NULL Coverage", checks))

    # =========================================================================
    # 10. F770W ZERO-WEIGHT COVERAGE
    # =========================================================================
    checks = []

    cur.execute("SELECT COUNT(*) FROM catalog.photometry_core WHERE wht_f770w = 0")
    f770w_zero = cur.fetchone()[0]
    pct = f770w_zero / EXPECTED_CORE_ROWS * 100
    checks.append(
        Check(
            "F770W zero-weight (no MIRI coverage)",
            "INFO",
            f"{f770w_zero:,} sources ({pct:.1f}%)",
            f770w_zero,
        )
    )

    sections.append(("MIRI F770W Coverage", checks))

    # =========================================================================
    # 11. CROSS-CODE MASS/SFR COMPARISON (O1 readiness)
    # =========================================================================
    # This section measures the disagreement between LePhare and CIGALE for
    # stellar mass and star formation rate — the core data product for
    # Opportunity O1 ("Algorithmic Disagreement").
    #
    # The key thresholds and their scientific meaning:
    #   |delta log M*| > 0.3 dex  —  mild disagreement, O1 candidate threshold
    #   |delta log M*| > 0.5 dex  —  strong disagreement, suggests fundamentally
    #                                 different SED interpretations (e.g. obscured
    #                                 AGN vs star-forming galaxy)
    #   |delta log M*| > 1.0 dex  —  extreme disagreement, almost certainly a
    #                                 physically distinct population
    #   |delta log SFR| > 0.5 dex —  O1 SFR candidate threshold
    #   |delta log SFR| > 1.0 dex —  strong SFR disagreement
    #   |delta log SFR| > 2.0 dex —  extreme SFR disagreement
    #
    # CRITICAL: LePhare values are log10, CIGALE values are linear.
    # Correct comparison: mass_med - LOG10(mass), sfr_med - LOG10(sfr_inst)
    checks = []

    # Count sources valid for dual-code comparison
    cur.execute(
        "SELECT COUNT(*) FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0"
    )
    dual_valid = cur.fetchone()[0]
    checks.append(
        Check(
            "Sources with valid mass from both codes",
            "INFO",
            f"{dual_valid:,} sources",
            dual_valid,
        )
    )

    # Delta log mass: mass_med (already log10) - LOG10(cigale.mass)
    cur.execute(
        "SELECT "
        "  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ABS(l.mass_med - LOG10(c.mass))), "
        "  PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY ABS(l.mass_med - LOG10(c.mass))), "
        "  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ABS(l.mass_med - LOG10(c.mass))), "
        "  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ABS(l.mass_med - LOG10(c.mass))), "
        "  MAX(ABS(l.mass_med - LOG10(c.mass))) "
        "FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0"
    )
    p50, p90, p95, p99, mx = cur.fetchone()
    checks.append(
        Check(
            "|delta log M*| percentiles (mass_med - log10(mass))",
            "INFO",
            f"p50={p50:.3f}, p90={p90:.3f}, p95={p95:.3f}, p99={p99:.3f}, max={mx:.3f}",
        )
    )

    # O1 mass candidates: |delta log M*| > 0.3 dex
    cur.execute(
        "SELECT COUNT(*) FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0 "
        "AND ABS(l.mass_med - LOG10(c.mass)) > 0.3"
    )
    o1_mass = cur.fetchone()[0]
    o1_mass_pct = o1_mass / dual_valid * 100 if dual_valid > 0 else 0
    checks.append(
        Check(
            "|delta log M*| > 0.3 dex (O1 mass candidates)",
            "INFO",
            f"{o1_mass:,} sources ({o1_mass_pct:.1f}% of dual-valid)",
            o1_mass,
        )
    )

    # O1 mass candidates at 0.5 dex
    cur.execute(
        "SELECT COUNT(*) FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0 "
        "AND ABS(l.mass_med - LOG10(c.mass)) > 0.5"
    )
    o1_mass_05 = cur.fetchone()[0]
    checks.append(
        Check(
            "|delta log M*| > 0.5 dex",
            "INFO",
            f"{o1_mass_05:,} sources",
            o1_mass_05,
        )
    )

    # O1 mass candidates at 1.0 dex
    cur.execute(
        "SELECT COUNT(*) FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0 "
        "AND ABS(l.mass_med - LOG10(c.mass)) > 1.0"
    )
    o1_mass_10 = cur.fetchone()[0]
    checks.append(
        Check(
            "|delta log M*| > 1.0 dex",
            "INFO",
            f"{o1_mass_10:,} sources",
            o1_mass_10,
        )
    )

    # SFR comparison: sfr_med (log10) - LOG10(sfr_inst)
    cur.execute(
        "SELECT COUNT(*) FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.sfr_med IS NOT NULL AND c.sfr_inst > 0"
    )
    sfr_dual = cur.fetchone()[0]
    checks.append(
        Check(
            "Sources with valid SFR from both codes",
            "INFO",
            f"{sfr_dual:,} sources",
            sfr_dual,
        )
    )

    cur.execute(
        "SELECT "
        "  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ABS(l.sfr_med - LOG10(c.sfr_inst))), "
        "  PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY ABS(l.sfr_med - LOG10(c.sfr_inst))), "
        "  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ABS(l.sfr_med - LOG10(c.sfr_inst))), "
        "  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ABS(l.sfr_med - LOG10(c.sfr_inst))), "
        "  MAX(ABS(l.sfr_med - LOG10(c.sfr_inst))) "
        "FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.sfr_med IS NOT NULL AND c.sfr_inst > 0"
    )
    sp50, sp90, sp95, sp99, smx = cur.fetchone()
    checks.append(
        Check(
            "|delta log SFR| percentiles (sfr_med - log10(sfr_inst))",
            "INFO",
            f"p50={sp50:.3f}, p90={sp90:.3f}, p95={sp95:.3f}, p99={sp99:.3f}, max={smx:.3f}",
        )
    )

    # SFR disagreement thresholds
    for thresh in (0.5, 1.0, 2.0):
        cur.execute(
            "SELECT COUNT(*) FROM catalog.lephare l "
            "JOIN catalog.cigale c ON l.id = c.id "
            "WHERE l.sfr_med IS NOT NULL AND c.sfr_inst > 0 "
            f"AND ABS(l.sfr_med - LOG10(c.sfr_inst)) > {thresh}"
        )
        cnt = cur.fetchone()[0]
        checks.append(
            Check(
                f"|delta log SFR| > {thresh} dex",
                "INFO",
                f"{cnt:,} sources",
                cnt,
            )
        )

    # Top 5 mass disagreements (spot check)
    cur.execute(
        "SELECT l.id, l.mass_med AS lp_log_mass, LOG10(c.mass) AS cig_log_mass, "
        "       l.mass_med - LOG10(c.mass) AS delta_log_mass, "
        "       p.warn_flag "
        "FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "JOIN catalog.photometry_core p ON l.id = p.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0 "
        "ORDER BY ABS(l.mass_med - LOG10(c.mass)) DESC "
        "LIMIT 5"
    )
    top5 = cur.fetchall()
    for i, (sid, lp, cig, delta, wf) in enumerate(top5):
        checks.append(
            Check(
                f"Top {i + 1} mass outlier (id={sid})",
                "INFO",
                f"LP={lp:.2f}, CIG={cig:.2f}, delta={delta:+.2f} dex, warn_flag={wf}",
            )
        )

    sections.append(("Cross-Code Mass/SFR Comparison (O1 Readiness)", checks))

    # =========================================================================
    # 12. SUPPLEMENTARY CATALOG SANITY
    # =========================================================================
    checks = []

    cur.execute("SELECT COUNT(*) FROM catalog.lss_overdensity")
    lss_count = cur.fetchone()[0]
    pct = lss_count / EXPECTED_CORE_ROWS * 100
    checks.append(
        Check(
            "LSS overdensity coverage",
            "INFO",
            f"{lss_count:,} / {EXPECTED_CORE_ROWS:,} ({pct:.1f}%) of sources have LSS data",
            lss_count,
        )
    )

    cur.execute("SELECT MIN(z), MAX(z), AVG(z) FROM catalog.galaxy_groups")
    gz_min, gz_max, gz_avg = cur.fetchone()
    checks.append(
        Check(
            "Group redshift range",
            "INFO",
            f"z = [{gz_min:.3f}, {gz_max:.3f}], mean={gz_avg:.3f} (expected max ~3.7)",
        )
    )

    cur.execute(
        "SELECT AVG(cnt) FROM ("
        "  SELECT group_id, COUNT(*) AS cnt "
        "  FROM catalog.galaxy_group_memberships GROUP BY group_id"
        ") sub"
    )
    avg_mem = cur.fetchone()[0]
    checks.append(
        Check("Avg memberships per group", "INFO", f"{avg_mem:.1f} members/group")
    )

    cur.execute("SELECT COUNT(DISTINCT galid) FROM catalog.galaxy_group_memberships")
    distinct_gals = cur.fetchone()[0]
    checks.append(
        Check(
            "Distinct galaxies in group memberships",
            "INFO",
            f"{distinct_gals:,} unique galaxies",
            distinct_gals,
        )
    )

    sections.append(("Supplementary Catalog Sanity", checks))

    # =========================================================================
    # 13. INDEX VERIFICATION
    # =========================================================================
    checks = []

    cur.execute(
        "SELECT indexname FROM pg_indexes WHERE schemaname = 'catalog' ORDER BY indexname"
    )
    indexes = [r[0] for r in cur.fetchall()]
    checks.append(
        Check(
            "Indexes present",
            "INFO",
            f"{len(indexes)} indexes: {', '.join(indexes)}",
        )
    )

    sections.append(("Index Verification", checks))

    cur.close()
    return sections


SUBSAMPLE_SIZE = 50000
RANDOM_SEED = 42


def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _chart_cross_code_mass(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT LOG10(c.mass), l.mass_med, p.warn_flag "
        "FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "JOIN catalog.photometry_core p ON l.id = p.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0 "
        "ORDER BY RANDOM() LIMIT %s",
        (SUBSAMPLE_SIZE,),
    )
    rows = cur.fetchall()
    cur.close()
    cig_log = np.array([r[0] for r in rows])
    lp_log = np.array([r[1] for r in rows])
    wf = np.array([r[2] for r in rows])

    fig, ax = plt.subplots(figsize=(8, 7))
    clean = wf == 0
    ax.scatter(
        cig_log[clean],
        lp_log[clean],
        s=1,
        alpha=0.15,
        c="#4C72B0",
        label="warn_flag=0",
        rasterized=True,
    )
    ax.scatter(
        cig_log[~clean],
        lp_log[~clean],
        s=4,
        alpha=0.4,
        c="#DD4444",
        label="warn_flag≠0",
        rasterized=True,
    )
    lo, hi = 5, 13
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="1:1")
    ax.set_xlabel("log10(CIGALE mass / M☉)")
    ax.set_ylabel("LePhare mass_med")
    ax.set_title("LePhare vs CIGALE Stellar Mass")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.legend(markerscale=8, fontsize=9)
    ax.set_aspect("equal")
    return _fig_to_base64(fig)


def _chart_delta_mass_histogram(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT l.mass_med - LOG10(c.mass) "
        "FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.mass_med IS NOT NULL AND c.mass > 0"
    )
    delta = np.array([r[0] for r in cur.fetchall()])
    cur.close()

    clipped = delta[(delta >= -3) & (delta <= 3)]
    n_clipped = len(delta) - len(clipped)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(clipped, bins=120, color="#4C72B0", edgecolor="none", alpha=0.85)
    for v, c, ls in [
        (-0.3, "#DD4444", "--"),
        (0.3, "#DD4444", "--"),
        (-0.5, "#222222", ":"),
        (0.5, "#222222", ":"),
    ]:
        ax.axvline(v, color=c, linestyle=ls, lw=1)
    left_tail = int(np.sum(clipped < -0.3))
    right_tail = int(np.sum(clipped > 0.3))
    ax.annotate(
        f"|Δ|>0.3: {left_tail + right_tail:,}",
        xy=(0.98, 0.95),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
    )
    ax.set_xlabel("Δlog M★ (LePhare − CIGALE)")
    ax.set_ylabel("Count")
    ax.set_title(f"Cross-Code Stellar Mass Disagreement ({n_clipped:,} clipped)")
    return _fig_to_base64(fig)


def _chart_delta_sfr_histogram(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT l.sfr_med - LOG10(c.sfr_inst) "
        "FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id "
        "WHERE l.sfr_med IS NOT NULL AND c.sfr_inst > 0"
    )
    delta = np.array([r[0] for r in cur.fetchall()])
    cur.close()

    clipped = delta[(delta >= -5) & (delta <= 5)]
    n_clipped = len(delta) - len(clipped)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(clipped, bins=120, color="#55A868", edgecolor="none", alpha=0.85)
    for v, c, ls in [
        (-0.5, "#DD4444", "--"),
        (0.5, "#DD4444", "--"),
        (-1.0, "#222222", ":"),
        (1.0, "#222222", ":"),
    ]:
        ax.axvline(v, color=c, linestyle=ls, lw=1)
    left_tail = int(np.sum(clipped < -0.5))
    right_tail = int(np.sum(clipped > 0.5))
    ax.annotate(
        f"|Δ|>0.5: {left_tail + right_tail:,}",
        xy=(0.98, 0.95),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
    )
    ax.set_xlabel("Δlog SFR (LePhare − CIGALE)")
    ax.set_ylabel("Count")
    ax.set_title(f"Cross-Code SFR Disagreement ({n_clipped:,} clipped)")
    return _fig_to_base64(fig)


def _chart_warn_flag_bar(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT warn_flag, COUNT(*) FROM catalog.photometry_core "
        "GROUP BY warn_flag ORDER BY warn_flag"
    )
    rows = cur.fetchall()
    cur.close()
    flags = [str(r[0]) for r in rows]
    counts = [r[1] for r in rows]
    total = sum(counts)

    fig, ax = plt.subplots(figsize=(8, max(3, len(flags) * 0.6)))
    y_pos = np.arange(len(flags))
    bars = ax.barh(y_pos, counts, color="#4C72B0", edgecolor="none")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"warn_flag = {f}" for f in flags])
    for i, cnt in enumerate(counts):
        pct = cnt / total * 100
        ax.text(
            cnt + total * 0.005, i, f"{cnt:,} ({pct:.1f}%)", va="center", fontsize=9
        )
    ax.set_xlabel("Source Count")
    ax.set_title("Quality Flag Distribution")
    ax.set_xlim(0, max(counts) * 1.25)
    plt.tight_layout()
    return _fig_to_base64(fig)


def _chart_lephare_type_pie(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT type, COUNT(*) FROM catalog.lephare GROUP BY type ORDER BY type"
    )
    rows = cur.fetchall()
    cur.close()
    labels_map = {0: "Galaxy", 1: "Star", 2: "QSO"}
    labels = [labels_map.get(r[0], f"type={r[0]}") for r in rows]
    sizes = [r[1] for r in rows]
    colors = ["#4C72B0", "#DD4444", "#55A868"]

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors[: len(sizes)],
        startangle=90,
        textprops={"fontsize": 10},
    )
    ax.set_title("LePhare Source Classification")
    return _fig_to_base64(fig)


def _chart_cigale_mass_chi2(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT LOG10(mass), LOG10(chi2_red_best_fit) "
        "FROM catalog.cigale "
        "WHERE mass > 0 AND chi2_red_best_fit > 0 "
        "ORDER BY RANDOM() LIMIT %s",
        (SUBSAMPLE_SIZE,),
    )
    rows = cur.fetchall()
    cur.close()
    log_mass = np.array([r[0] for r in rows])
    log_chi2 = np.array([r[1] for r in rows])

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(log_mass, log_chi2, s=1, alpha=0.15, c="#C44E52", rasterized=True)
    ax.set_xlabel("log10(CIGALE mass / M☉)")
    ax.set_ylabel("log10(χ²_red)")
    ax.set_title("CIGALE Fit Quality vs Stellar Mass")
    ax.set_xlim(5, 13)
    ax.set_ylim(-2, 4)
    return _fig_to_base64(fig)


def _chart_redshift_distribution(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT l.zfinal FROM catalog.lephare l "
        "JOIN catalog.photometry_core p ON l.id = p.id "
        "WHERE l.zfinal IS NOT NULL AND l.type = 0 AND p.warn_flag = 0"
    )
    z = np.array([r[0] for r in cur.fetchall()])
    cur.close()

    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.arange(0, np.ceil(z.max()) + 0.1, 0.1)
    ax.hist(z, bins=bins, color="#8172B3", edgecolor="none", alpha=0.85)
    ax.set_xlabel("z_phot (zfinal)")
    ax.set_ylabel("Count")
    ax.set_title(f"Photometric Redshift Distribution (Clean Galaxies, N={len(z):,})")
    return _fig_to_base64(fig)


def _chart_sky_coverage(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT ra, dec, warn_flag FROM catalog.photometry_core "
        "ORDER BY RANDOM() LIMIT %s",
        (SUBSAMPLE_SIZE,),
    )
    rows = cur.fetchall()
    cur.close()
    ra = np.array([r[0] for r in rows])
    dec = np.array([r[1] for r in rows])
    wf = np.array([r[2] for r in rows])

    fig, ax = plt.subplots(figsize=(8, 6))
    clean = wf == 0
    ax.scatter(
        ra[clean],
        dec[clean],
        s=0.5,
        alpha=0.2,
        c="#4C72B0",
        label="warn_flag=0",
        rasterized=True,
    )
    ax.scatter(
        ra[~clean],
        dec[~clean],
        s=2,
        alpha=0.4,
        c="#DD4444",
        label="warn_flag≠0",
        rasterized=True,
    )
    ax.set_xlabel("RA (deg)")
    ax.set_ylabel("Dec (deg)")
    ax.set_title("COSMOS-Web DR1 Sky Coverage")
    ax.legend(markerscale=8, fontsize=9)
    ax.invert_xaxis()
    return _fig_to_base64(fig)


def generate_charts(conn):
    log.info("Generating charts for HTML report...")
    charts = {}
    chart_funcs = [
        ("cross_code_mass", _chart_cross_code_mass),
        ("delta_mass_hist", _chart_delta_mass_histogram),
        ("delta_sfr_hist", _chart_delta_sfr_histogram),
        ("warn_flag_bar", _chart_warn_flag_bar),
        ("lephare_type_pie", _chart_lephare_type_pie),
        ("cigale_mass_chi2", _chart_cigale_mass_chi2),
        ("redshift_dist", _chart_redshift_distribution),
        ("sky_coverage", _chart_sky_coverage),
    ]
    for name, func in chart_funcs:
        log.info(f"  Generating {name}...")
        charts[name] = func(conn)
    log.info("Charts complete.")
    return charts


def write_report(sections, elapsed):
    """Write markdown report from check results."""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# COSMOS2025 ETL Verification Report")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append(f"Runtime: {elapsed:.1f}s")
    lines.append(f"Database: cosmos2025 on psql01 (10.25.20.8)")
    lines.append("")

    # Unit reference block
    lines.append("**Unit Reference (critical for cross-code comparison):**")
    lines.append("")
    lines.append("| Column | Units | Space |")
    lines.append("|--------|-------|-------|")
    lines.append("| lephare.mass_med / mass_l68 / mass_u68 | log10(M/M_sun) | log10 |")
    lines.append(
        "| lephare.sfr_med / sfr_l68 / sfr_u68 | log10(SFR / M_sun yr-1) | log10 |"
    )
    lines.append(
        "| lephare.ssfr_med / ssfr_l68 / ssfr_u68 | log10(sSFR / yr-1) | log10 |"
    )
    lines.append("| cigale.mass / mass_err | M_sun | linear |")
    lines.append("| cigale.sfr_inst / sfr_100myr | M_sun yr-1 | linear |")
    lines.append("| cigale.ssfr_cigale (derived) | yr-1 | linear |")
    lines.append("")
    lines.append(
        "Cross-code comparison formula: `delta = lephare_log10_value - LOG10(cigale_linear_value)`"
    )
    lines.append("")

    # Summary counts
    total = sum(len(checks) for _, checks in sections)
    passed = sum(1 for _, checks in sections for c in checks if c.status == "PASS")
    failed = sum(1 for _, checks in sections for c in checks if c.status == "FAIL")
    warned = sum(1 for _, checks in sections for c in checks if c.status == "WARN")
    info = sum(1 for _, checks in sections for c in checks if c.status == "INFO")

    overall = "PASS" if failed == 0 else "FAIL"
    lines.append(
        f"**Overall: {overall}** | {passed} passed, {failed} failed, "
        f"{warned} warnings, {info} info | {total} checks total"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    for section_name, checks in sections:
        lines.append(f"## {section_name}")
        lines.append("")
        lines.append("| Status | Check | Detail |")
        lines.append("|--------|-------|--------|")
        for c in checks:
            lines.append(f"| {c.icon()} {c.status} | {c.name} | {c.detail} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by `src/etl/verify_catalog.py`*")

    report = "\n".join(lines)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    return report


HTML_CSS = """\
body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color: #333; background: #f5f5f5; }
.header { background: #2c3e50; color: #fff; padding: 28px 0; margin-bottom: 0; }
.header-inner { max-width: 1100px; margin: 0 auto; padding: 0 24px; }
.header h1 { margin: 0 0 6px 0; font-size: 1.6em; font-weight: 600; }
.header .meta { font-size: 0.9em; color: #bdc3c7; }
.header .meta span { margin-right: 24px; }
.content { max-width: 1100px; margin: 0 auto; padding: 24px; background: #fff; min-height: 60vh; }
.summary-box { display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }
.summary-card { flex: 1; min-width: 140px; padding: 16px; border-radius: 6px; text-align: center; }
.summary-card.pass { background: #e8f5e9; color: #2e7d32; }
.summary-card.fail { background: #ffebee; color: #c62828; }
.summary-card.warn { background: #fff8e1; color: #f57f17; }
.summary-card.info { background: #e3f2fd; color: #1565c0; }
.summary-card .num { font-size: 2em; font-weight: 700; }
.summary-card .lbl { font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }
.unit-ref { background: #fffde7; border: 1px solid #fff176; border-radius: 6px; padding: 16px 20px; margin: 20px 0; }
.unit-ref h3 { margin: 0 0 8px 0; font-size: 1em; color: #f57f17; }
.unit-ref table { width: 100%; border-collapse: collapse; font-size: 0.88em; }
.unit-ref th, .unit-ref td { padding: 4px 10px; text-align: left; border-bottom: 1px solid #fff9c4; }
.unit-ref th { font-weight: 600; color: #555; }
h2 { border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 32px; color: #2c3e50; }
table.checks { width: 100%; border-collapse: collapse; margin: 12px 0 24px 0; font-size: 0.9em; }
table.checks th { background: #f0f0f0; text-align: left; padding: 8px 10px; font-weight: 600; color: #555; border-bottom: 2px solid #ddd; }
table.checks td { padding: 7px 10px; border-bottom: 1px solid #eee; vertical-align: top; }
table.checks tr:nth-child(even) td { background: #fafafa; }
table.checks td.status { width: 90px; font-weight: 600; white-space: nowrap; }
.chart-section { text-align: center; margin: 32px 0; }
.chart-section h2 { text-align: left; }
.chart-grid { display: flex; flex-wrap: wrap; gap: 24px; justify-content: center; }
.chart-card { max-width: 800px; width: 100%; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden; background: #fff; }
.chart-card img { width: 100%; height: auto; display: block; }
.footer { text-align: center; color: #999; font-size: 0.82em; padding: 24px 0; border-top: 1px solid #eee; margin-top: 32px; }
@media print {
  .header { background: #fff !important; color: #000 !important; }
  .header .meta { color: #666 !important; }
  .content { padding: 0; }
  .chart-card { box-shadow: none; border: 1px solid #ccc; }
}
"""


def write_html_report(sections, elapsed, charts):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    total = sum(len(checks) for _, checks in sections)
    passed = sum(1 for _, checks in sections for c in checks if c.status == "PASS")
    failed = sum(1 for _, checks in sections for c in checks if c.status == "FAIL")
    warned = sum(1 for _, checks in sections for c in checks if c.status == "WARN")
    info = sum(1 for _, checks in sections for c in checks if c.status == "INFO")
    overall = "PASS" if failed == 0 else "FAIL"
    overall_icon = "✅" if overall == "PASS" else "❌"

    status_colors = {
        "PASS": "#2e7d32",
        "FAIL": "#c62828",
        "WARN": "#f57f17",
        "INFO": "#1565c0",
    }

    html_parts = []
    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html lang='en'><head>")
    html_parts.append(
        f"<meta charset='utf-8'><title>COSMOS2025 Phase 1 Verification Report</title>"
    )
    html_parts.append(f"<style>{HTML_CSS}</style>")
    html_parts.append("</head><body>")

    html_parts.append("<div class='header'><div class='header-inner'>")
    html_parts.append("<h1>COSMOS2025 Phase 1 Verification Report</h1>")
    html_parts.append(f"<div class='meta'>")
    html_parts.append(f"<span>Generated: {now}</span>")
    html_parts.append(f"<span>Runtime: {elapsed:.1f}s</span>")
    html_parts.append(f"<span>Database: cosmos2025 on psql01 (10.25.20.8)</span>")
    html_parts.append(f"<span>Overall: {overall_icon} {overall}</span>")
    html_parts.append(f"</div></div></div>")

    html_parts.append("<div class='content'>")

    html_parts.append(f"""
<div class="summary-box">
  <div class="summary-card pass"><div class="num">{passed}</div><div class="lbl">Passed</div></div>
  <div class="summary-card fail"><div class="num">{failed}</div><div class="lbl">Failed</div></div>
  <div class="summary-card warn"><div class="num">{warned}</div><div class="lbl">Warnings</div></div>
  <div class="summary-card info"><div class="num">{info}</div><div class="lbl">Info</div></div>
</div>
""")

    html_parts.append("""\
<div class="unit-ref">
<h3>⚠ Unit Reference — Critical for Cross-Code Comparison</h3>
<table>
<tr><th>Column</th><th>Units</th><th>Space</th></tr>
<tr><td>lephare.mass_med / mass_l68 / mass_u68</td><td>log10(M/M☉)</td><td>log10</td></tr>
<tr><td>lephare.sfr_med / sfr_l68 / sfr_u68</td><td>log10(SFR / M☉ yr⁻¹)</td><td>log10</td></tr>
<tr><td>lephare.ssfr_med / ssfr_l68 / ssfr_u68</td><td>log10(sSFR / yr⁻¹)</td><td>log10</td></tr>
<tr><td>cigale.mass / mass_err</td><td>M☉</td><td>linear</td></tr>
<tr><td>cigale.sfr_inst / sfr_100myr</td><td>M☉ yr⁻¹</td><td>linear</td></tr>
<tr><td>cigale.ssfr_cigale (derived)</td><td>yr⁻¹</td><td>linear</td></tr>
</table>
<p style="font-size:0.88em;color:#888;margin-top:8px;">Cross-code formula: <code>delta = lephare_log10_value − LOG10(cigale_linear_value)</code></p>
</div>
""")

    for section_name, checks in sections:
        html_parts.append(f"<h2>{section_name}</h2>")
        html_parts.append(
            "<table class='checks'><tr><th class='status'>Status</th><th>Check</th><th>Detail</th></tr>"
        )
        for c in checks:
            col = status_colors.get(c.status, "#333")
            html_parts.append(
                f"<tr><td class='status' style='color:{col}'>{c.icon()} {c.status}</td>"
                f"<td>{c.name}</td><td>{c.detail}</td></tr>"
            )
        html_parts.append("</table>")

    chart_titles = [
        ("cross_code_mass", "LePhare vs CIGALE Stellar Mass"),
        ("delta_mass_hist", "Cross-Code Stellar Mass Disagreement"),
        ("delta_sfr_hist", "Cross-Code SFR Disagreement"),
        ("warn_flag_bar", "Quality Flag Distribution"),
        ("lephare_type_pie", "LePhare Source Classification"),
        ("cigale_mass_chi2", "CIGALE Fit Quality vs Stellar Mass"),
        ("redshift_dist", "Photometric Redshift Distribution"),
        ("sky_coverage", "COSMOS-Web DR1 Sky Coverage"),
    ]

    html_parts.append(
        "<div class='chart-section'><h2>Charts</h2><div class='chart-grid'>"
    )
    for key, title in chart_titles:
        if key in charts:
            html_parts.append(
                f"<div class='chart-card'>"
                f"<img src='data:image/png;base64,{charts[key]}' alt='{title}' />"
                f"</div>"
            )
    html_parts.append("</div></div>")

    html_parts.append(
        f"<div class='footer'>Generated by <code>src/etl/verify_catalog.py</code></div>"
    )
    html_parts.append("</div></body></html>")

    html_content = "\n".join(html_parts)

    os.makedirs(os.path.dirname(HTML_REPORT_PATH), exist_ok=True)
    with open(HTML_REPORT_PATH, "w") as f:
        f.write(html_content)

    size_mb = os.path.getsize(HTML_REPORT_PATH) / (1024 * 1024)
    log.info(f"HTML report size: {size_mb:.1f} MB")
    return html_content


def main():
    t0 = time.time()
    log.info("Starting COSMOS2025 ETL verification")

    config = load_config()
    conn = get_db_connection(config)

    try:
        sections = run_checks(conn)
        charts = generate_charts(conn)
    finally:
        conn.close()

    elapsed = time.time() - t0
    report = write_report(sections, elapsed)
    html_report = write_html_report(sections, elapsed, charts)

    log.info(f"Verification complete in {elapsed:.1f}s")
    log.info(f"Markdown report written to {REPORT_PATH}")
    log.info(f"HTML report written to {HTML_REPORT_PATH}")

    summary_lines = []
    for section_name, checks in sections:
        for c in checks:
            summary_lines.append(f"{c.icon()} {c.status} | {c.name} | {c.detail}")
    print("\n" + "\n".join(summary_lines))
    print(f"\nReports: {REPORT_PATH} | {HTML_REPORT_PATH}")


if __name__ == "__main__":
    main()
