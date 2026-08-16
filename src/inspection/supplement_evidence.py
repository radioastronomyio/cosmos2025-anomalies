#!/usr/bin/env python3
"""
Script Name  : supplement_evidence.py
Description  : Compare on-disk LSS and group supplements against the live loaded tables at value level
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-16
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Spec P2R-01 gate 1.11 utility. Establishes whether the local supplement
files are byte-identical in content to what the v1 ETL loaded: row counts
computed from the files (never assumed), plus a seeded sampled value check
on the join key and one payload column per supplement. LSS: the
OVERDENSITY binary table (id, density_excess) vs catalog.lss_overdensity.
Groups: toni/groups.txt (ID, LAMBDA) vs catalog.galaxy_groups on every
row. Memberships: toni/memberships.txt (GALID, ID, ASSOC_PROB) vs
catalog.galaxy_group_memberships on a 5,000-row sample. Read-only.

Usage
-----
    doppler run --project ml01 --config prd -- python src/inspection/supplement_evidence.py

Examples
--------
    (see Usage; writes JSON to staging and prints the comparison)
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
OUT_JSON = REPO_ROOT / "staging" / "supplement-evidence.json"
SEED = 20260815
LSS_SAMPLE = 2_000
MEMBERSHIP_SAMPLE = 5_000

# =============================================================================
# Functions
# =============================================================================


def db_connect():
    """Open the read-only comparison connection via Doppler env vars."""
    config = yaml.safe_load(CONFIG_PATH.read_text())
    db = config["database"]
    return psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["database_name"],
    )


def value_comparison(pairs_file, pairs_db):
    """Exact and near-equality stats for aligned (key, payload) pairs."""
    keys_file = {int(k): float(v) for k, v in pairs_file}
    keys_db = {int(k): float(v) for k, v in pairs_db}
    common = set(keys_file) & set(keys_db)
    exact = sum(1 for k in common if keys_file[k] == keys_db[k])
    close = sum(1 for k in common if abs(keys_file[k] - keys_db[k]) <= 1e-9 * max(1.0, abs(keys_file[k])))
    return {
        "file_rows": len(keys_file),
        "db_rows": len(keys_db),
        "common_keys": len(common),
        "file_only_keys": len(set(keys_file) - set(keys_db)),
        "db_only_keys": len(set(keys_db) - set(keys_file)),
        "payload_exact_matches": exact,
        "payload_matches_within_1e-9rel": close,
    }


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Run the supplement value-level comparison."""
    config = yaml.safe_load(CONFIG_PATH.read_text())
    supp = config["supplementary"]
    rng = np.random.default_rng(SEED)
    conn = db_connect()
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": SEED}

    try:
        with conn.cursor() as cur:
            # --- LSS: OVERDENSITY table vs catalog.lss_overdensity ---
            with fits.open(supp["lss_overdensity"], memmap=True) as hdul:
                extnames = [h.header.get("EXTNAME", "") for h in hdul]
                overdensity = hdul["OVERDENSITY"].data
                lss_rows = int(len(overdensity))
                lss_ids = np.asarray(overdensity["id"])
                lss_de = np.asarray(overdensity["density_excess"], dtype=np.float64)
            cur.execute("SELECT COUNT(*) FROM catalog.lss_overdensity")
            lss_db_rows = cur.fetchone()[0]
            sample = rng.choice(lss_rows, size=min(LSS_SAMPLE, lss_rows), replace=False)
            out["lss"] = {
                "file": supp["lss_overdensity"],
                "fits_extnames": extnames,
                "file_rows": lss_rows,
                "db_rows": lss_db_rows,
                "sample": value_comparison(
                    zip(lss_ids[sample], lss_de[sample]),
                    _fetch_pairs(cur, "SELECT id, density_excess FROM catalog.lss_overdensity WHERE id = ANY(%s)", [int(i) for i in lss_ids[sample]]),
                ),
            }

            # --- Groups: full-file comparison on (ID, LAMBDA) ---
            groups_file = []
            for line in Path(supp["group_catalog_groups"]).read_text().splitlines()[1:]:
                fields = line.split()
                if fields:
                    groups_file.append((int(fields[0]), float(fields[8])))  # ID, LAMBDA
            out["groups"] = {
                "file": supp["group_catalog_groups"],
                "file_rows": len(groups_file),
                "comparison": value_comparison(
                    groups_file,
                    _fetch_pairs_all(cur, "SELECT group_id, lambda FROM catalog.galaxy_groups"),
                ),
            }

            # --- Memberships: sampled (GALID, ASSOC_PROB) keyed by (galid, group_id) ---
            mem_file = []
            for line in Path(supp["group_catalog_memberships"]).read_text().splitlines()[1:]:
                fields = line.split()
                if fields:
                    mem_file.append((int(fields[0]), int(fields[2]), float(fields[3])))
            mem_sample_idx = rng.choice(len(mem_file), size=min(MEMBERSHIP_SAMPLE, len(mem_file)), replace=False)
            mem_sample = [mem_file[i] for i in mem_sample_idx]
            cur.execute(
                "SELECT galid, group_id, assoc_prob FROM catalog.galaxy_group_memberships"
            )
            mem_db = {(int(g), int(gr)): float(a) for g, gr, a in cur.fetchall()}
            exact = sum(1 for g, gr, a in mem_sample if (g, gr) in mem_db and mem_db[(g, gr)] == a)
            close = sum(
                1
                for g, gr, a in mem_sample
                if (g, gr) in mem_db and abs(mem_db[(g, gr)] - a) <= 1e-9 * max(1.0, abs(a))
            )
            out["memberships"] = {
                "file": supp["group_catalog_memberships"],
                "file_rows": len(mem_file),
                "db_rows": len(mem_db),
                "sample_rows": len(mem_sample),
                "key_and_payload_exact_matches": exact,
                "matches_within_1e-9rel": close,
            }
    finally:
        conn.close()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


def _fetch_pairs(cur, sql, ids):
    """Fetch (key, payload) pairs for a sampled id list."""
    cur.execute(sql, (ids,))
    return cur.fetchall()


def _fetch_pairs_all(cur, sql):
    """Fetch all (key, payload) pairs."""
    cur.execute(sql)
    return cur.fetchall()


if __name__ == "__main__":
    main()
