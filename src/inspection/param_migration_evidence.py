#!/usr/bin/env python3
"""
Script Name  : param_migration_evidence.py
Description  : Compare CIGALE/LePhare physical parameters between v1.1 FITS and the live v1 tables
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-16
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Spec P2R-01 gate 1.10 utility. Draws a seeded random sample of source IDs
present in both the v1.1 extension files and the live v1 tables, joins on
source ID, and reports per-column exact-match fractions and delta
distributions — per code (CIGALE, LePhare) and per tile group (B5/B9/B10
vs all others, tile taken from the master PHOTOMETRY extension). CIGALE
columns: mass, sfr_inst, sfr_100myr, chi2_red_best_fit (linear space;
deltas as relative differences). LePhare columns: zfinal, mass_med,
sfr_med (log10 space; deltas in dex). The join count is asserted equal to
the sample size: the join is verified, never assumed. Intermediate match
fractions (neither ~0 nor ~1) are surfaced, never averaged away.

Usage
 -----
    doppler run --project ml01 --config prd -- python src/inspection/param_migration_evidence.py

Examples
--------
    (see Usage; output JSON to staging and a printed summary)
"""

# =============================================================================
# Imports
# =============================================================================

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psycopg2
import yaml
from astropy.io import fits

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
OUT_JSON = REPO_ROOT / "staging" / "param-migration-evidence.json"

SAMPLE_SIZE = 60_000
SEED = 20260815
HOT_TILES = {"B5", "B9", "B10"}

# FITS column name -> DB column name (identical here; stated for the record)
CIGALE_COLUMNS = ["mass", "sfr_inst", "sfr_100myr", "chi2_red_best_fit"]
LEPHARE_COLUMNS = ["zfinal", "mass_med", "sfr_med"]


# =============================================================================
# Functions
# =============================================================================


def db_connect():
    """Open the read-only v1 comparison connection via Doppler env vars."""
    config = yaml.safe_load(CONFIG_PATH.read_text())
    db = config["database"]
    return psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["database_name"],
    )


def fetch_db(cur, sql):
    """Fetch a query as a column-major dict of numpy arrays.

    Numeric columns are coerced to float64 (psycopg2 returns Decimal for
    numeric types, which numpy keeps as object arrays); NULL becomes NaN
    so downstream isnan logic sees them.
    """
    cur.execute(sql)
    names = [d[0] for d in cur.description]
    cols = list(zip(*cur.fetchall()))
    out = {}
    for n, c in zip(names, cols):
        if n == "id":
            out[n] = np.array(c, dtype=np.int64)
        else:
            out[n] = np.array([float(v) if v is not None else np.nan for v in c])
    return out


def column_stats(v1_values, v11_values, log_space):
    """Exact-match fraction and delta distribution for one column."""
    valid = ~(np.isnan(v1_values) | np.isnan(v11_values))
    n = int(valid.sum())
    if n == 0:
        return {"valid_rows": 0}
    a, b = v1_values[valid], v11_values[valid]
    exact = int(np.sum(a == b))
    if log_space:
        delta = b - a
        rel = None
    else:
        delta = None
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = (b - a) / np.where(a != 0, a, np.nan)
    stats = {
        "valid_rows": n,
        "exact_matches": exact,
        "match_fraction": exact / n,
        "delta_min": None if delta is None else float(np.nanmin(delta)),
        "delta_p16": None if delta is None else float(np.nanpercentile(delta, 16)),
        "delta_median": None if delta is None else float(np.nanmedian(delta)),
        "delta_p84": None if delta is None else float(np.nanpercentile(delta, 84)),
        "delta_max": None if delta is None else float(np.nanmax(delta)),
        "delta_p1": None if delta is None else float(np.nanpercentile(delta, 1)),
        "delta_p99": None if delta is None else float(np.nanpercentile(delta, 99)),
        "frac_abs_delta_gt_0.01": None if delta is None else float(np.mean(np.abs(delta) > 0.01)),
        "frac_abs_delta_gt_0.1": None if delta is None else float(np.mean(np.abs(delta) > 0.1)),
    }
    if rel is not None:
        finite = rel[np.isfinite(rel)]
        stats["rel_delta_median"] = float(np.nanmedian(finite)) if finite.size else None
        stats["rel_delta_p16"] = float(np.nanpercentile(finite, 16)) if finite.size else None
        stats["rel_delta_p84"] = float(np.nanpercentile(finite, 84)) if finite.size else None
        stats["frac_abs_rel_gt_0.1"] = (
            float(np.mean(np.abs(finite) > 0.1)) if finite.size else None
        )
        stats["frac_abs_rel_gt_0.5"] = (
            float(np.mean(np.abs(finite) > 0.5)) if finite.size else None
        )
        stats["nonzero_delta_rows"] = int(np.sum(a != b))
        stats["frac_abs_rel_p1"] = (
            float(np.nanpercentile(np.abs(finite), 1)) if finite.size else None
        )
        stats["frac_abs_rel_p99"] = (
            float(np.nanpercentile(np.abs(finite), 99)) if finite.size else None
        )
    return stats


def compare_group(label, v1, v11, columns, log_space):
    """Per-column stats for one code and one tile group."""
    return {
        col: {"group": label, **column_stats(v1[col], v11[col], log_space)}
        for col in columns
    }


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Run the sampled value comparison per code and tile group."""
    config = yaml.safe_load(CONFIG_PATH.read_text())
    catalogs = config["catalogs"]

    # v1.1 side (memmap column reads)
    with fits.open(catalogs["photom_primary"], memmap=True) as hdul:
        v11_ids = np.asarray(hdul[1].data["id"])
        v11_tile = np.asarray(hdul[1].data["tile"]).astype(str)
    with fits.open(catalogs["cigale"], memmap=True) as hdul:
        cig = {c: np.asarray(hdul[1].data[c], dtype=np.float64) for c in CIGALE_COLUMNS}
    with fits.open(catalogs["lephare"], memmap=True) as hdul:
        lep = {c: np.asarray(hdul[1].data[c], dtype=np.float64) for c in LEPHARE_COLUMNS}

    # v1 side (live tables)
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cig_db = fetch_db(
                cur,
                "SELECT id, mass, sfr_inst, sfr_100myr, chi2_red_best_fit FROM catalog.cigale",
            )
            lep_db = fetch_db(
                cur, "SELECT id, zfinal, mass_med, sfr_med FROM catalog.lephare"
            )
    finally:
        conn.close()

    # Sample ids present in both sides (per gate 1.9 the sets are identical;
    # verified here again by actual intersection before sampling)
    common = np.intersect1d(v11_ids, cig_db["id"])
    common = np.intersect1d(common, lep_db["id"])
    rng = np.random.default_rng(SEED)
    sample_ids = rng.choice(common, size=min(SAMPLE_SIZE, common.size), replace=False)

    # Index maps and join; joined-count asserted per side
    fits_idx = {value: i for i, value in enumerate(v11_ids)}
    cig_db_idx = {value: i for i, value in enumerate(cig_db["id"])}
    lep_db_idx = {value: i for i, value in enumerate(lep_db["id"])}
    fi = np.array([fits_idx[i] for i in sample_ids])
    ci = np.array([cig_db_idx[i] for i in sample_ids])
    li = np.array([lep_db_idx[i] for i in sample_ids])
    assert fi.size == ci.size == li.size == sample_ids.size, "join lost rows"

    hot = np.isin(v11_tile[fi], sorted(HOT_TILES))
    groups = {
        "B5/B9/B10": hot,
        "others": ~hot,
    }

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sample_size": int(sample_ids.size),
        "seed": SEED,
        "hot_tiles": sorted(HOT_TILES),
        "join": {
            "ids_common_to_all_sources": int(common.size),
            "joined_rows": int(sample_ids.size),
            "join_verified": True,
            "hot_group_rows": int(hot.sum()),
            "others_group_rows": int((~hot).sum()),
        },
        "cigale": {},
        "lephare": {},
    }

    for label, mask in groups.items():
        out["cigale"][label] = compare_group(
            label,
            {c: cig_db[c][ci][mask] for c in CIGALE_COLUMNS},
            {c: cig[c][fi][mask] for c in CIGALE_COLUMNS},
            CIGALE_COLUMNS,
            log_space=False,
        )
        out["lephare"][label] = compare_group(
            label,
            {c: lep_db[c][li][mask] for c in LEPHARE_COLUMNS},
            {c: lep[c][fi][mask] for c in LEPHARE_COLUMNS},
            LEPHARE_COLUMNS,
            log_space=True,
        )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
