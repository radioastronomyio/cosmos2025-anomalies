import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.features.compute_tension_scalars import (  # noqa: E402
    SIGMA_SYS_MASS,
    SIGMA_SYS_SFR,
    build_insert_tension_sql,
    format_pct,
    render_report,
)
from decimal import Decimal


def test_insert_sql_embeds_named_sigma_values_and_zero_error_guards():
    sql = build_insert_tension_sql("wht_f770w")

    assert str(SIGMA_SYS_MASS) in sql
    assert str(SIGMA_SYS_SFR) in sql
    assert "c.mass_err IS NULL OR c.mass_err <= 0" in sql
    assert "c.sfr_inst_err IS NULL OR c.sfr_inst_err <= 0" in sql
    assert "c.sfr_100myr_err IS NULL OR c.sfr_100myr_err <= 0" in sql
    assert "THEN NULL" in sql
    assert "p.wht_f770w > 0 AS has_f770w" in sql


def test_render_report_includes_required_sections_and_context_tables():
    report = render_report(
        generated_at="2026-05-01T00:00:00+00:00",
        sample_attrition=[
            ("Total catalog", 784016, 100.0),
            ("After all four gates", 500000, 63.77),
        ],
        pull_stats={
            "t_mass": {
                "count": 500000,
                "mean": 0.1,
                "median": 0.0,
                "stddev": 1.2,
                "skewness": 0.3,
                "kurtosis": 4.5,
                "min": -8.0,
                "max": 9.0,
                "frac_abs_gt_2": 0.05,
                "frac_abs_gt_3": 0.02,
                "frac_abs_gt_5": 0.005,
            }
        },
        chi2_correlations={
            "abs_t_mass_vs_chi2_red_cig": 0.12,
            "abs_t_sfr_100_vs_chi2_red_cig": 0.18,
        },
        sfr_stability={
            "corr_t_sfr_inst_t_sfr_100": 0.8,
            "sign_mismatch_count": 100,
            "top1000_inst_not_top1000_100": 250,
        },
        zombie_verification={
            "min_log10_cigale_mass": 6.0,
            "max_log10_cigale_mass": 12.5,
            "min_lephare_mass_med": 6.1,
            "max_lephare_mass_med": 12.2,
            "extreme_delta_log_mass_count": 5,
        },
        context={
            "total": 500000,
            "has_f770w_count": 400000,
            "quiescent_count": 100000,
            "groups": [
                {
                    "population": "Quiescent with F770W",
                    "count": 80000,
                    "percentage": 16.0,
                    "median_abs_t_sfr_100": 0.7,
                }
            ],
        },
    )

    for heading in [
        "## A. Sample Attrition",
        "## B. Pull Distribution Analysis",
        "## C. Tension vs Chi2 Decoupling Check",
        "## D. SFR Timescale Stability",
        "## E. Zombie Leakage Verification",
        "## F. F770W Coverage and Quiescent Context",
    ]:
        assert heading in report

    assert "sigma_sys is too low" in report
    assert "Quiescent with F770W" in report
    assert "| |t_mass|" not in report
    assert "|T| >" not in report


def test_format_pct_accepts_decimal_values_from_psycopg():
    assert format_pct(Decimal("0.125")) == "12.50%"
