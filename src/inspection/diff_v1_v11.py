#!/usr/bin/env python3
"""
Script Name  : diff_v1_v11.py
Description  : Classify column and ID-space deltas between the v1 evidence base and the v1.1 holdings
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-16
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Spec P2R-01 gate 1.9 utility. Diffs each v1.1 master extension against two
v1 evidence sources: the documented column lists (docs/reference/
columns-*.txt) and the live psql01 information_schema for the tables the
v1 ETL actually loaded. Every column is classified unchanged / added /
removed / renamed (with both names; similarity-scored, never positional) /
dtype-changed (DB data type vs v1.1 FITS format for common columns). The
ID space of the v1.1 PHOTOMETRY extension is set-compared against live
catalog.photometry_core ids (retained / dropped / new). Read-only against
the database and the holdings.

Usage
-----
    python src/inspection/diff_v1_v11.py

Examples
--------
    python src/inspection/diff_v1_v11.py
        Prints the per-extension classification and ID-space deltas;
        writes the full record to staging/v1-v11-delta.json.
"""

# =============================================================================
# Imports
# =============================================================================

import difflib
import json
import os
import re
import subprocess
import sys
from collections import Counter
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
REFERENCE_DIR = REPO_ROOT / "docs" / "reference"
OUT_JSON = REPO_ROOT / "staging" / "v1-v11-delta.json"

# v1 documented inventory -> v1.1 EXTNAME (inventory filename slug)
EXTENSION_MAP = [
    ("PHOTOMETRY HOTCOLD AND SE++", "columns-photometry.txt", "photometry-hotcold-and-seplusplus"),
    ("LEPHARE", "columns-lephare-photometrric-redshifts.txt", "lephare"),
    ("SE++APER", "columns-non-psf-homogenized-aperture-photometry.txt", "seplusplusaper"),
    ("CIGALE", "columns-cigale-physical-parameters.txt", "cigale"),
    ("ML-MORPHO", "columns-machine-learning-morphological-classifications.txt", "ml-morpho"),
    ("B+D", "columns-bulge-disk-morphological-measurements.txt", "bplusd"),
]

# Loaded v1 tables -> extension; DB names are sanitized (hyphen -> underscore)
DB_TABLE_MAP = {
    "photometry_core": "PHOTOMETRY HOTCOLD AND SE++",
    "lephare": "LEPHARE",
    "cigale": "CIGALE",
    "morphology": "ML-MORPHO",
}

# FITS format letter -> PostgreSQL type family for the dtype-changed check
FITS_TO_PG = {
    "D": "double precision",
    "E": "real",
    "J": "integer",
    "K": "bigint",
    "I": "smallint",
    "A": "text",
    "B": "bytea",
    "L": "boolean",
}

RENAME_THRESHOLD = 0.85


# =============================================================================
# Functions
# =============================================================================


def parse_v1_doc(path: Path) -> list[str]:
    """Column names from a v1 documented inventory.

    Header shape varies (photometry: 2 lines; others: title +
    'Click to expand' + header). Skip everything through the literal
    'Column Name' header line instead of assuming a fixed offset.
    """
    lines = path.read_text().splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("Column Name"))
    except StopIteration as exc:
        raise ValueError(f"no 'Column Name' header in {path}") from exc
    return [line.split("\t")[0] for line in lines[start + 1 :] if line.strip()]


def parse_v11_inventory(path: Path) -> list[tuple[str, str]]:
    """(name, format) pairs from a v1.1 generated inventory."""
    lines = path.read_text().splitlines()
    return [tuple(line.split("\t")[0:2]) for line in lines[2:] if line.strip()]


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


def db_columns(cur, table: str) -> dict[str, str]:
    """Column name -> data type for one loaded v1 table."""
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'catalog' AND table_name = %s ORDER BY ordinal_position",
        (table,),
    )
    return {name: dtype for name, dtype in cur.fetchall()}


def classify(v1_names: list[str], v11_names: list[str]) -> dict:
    """
    Classify columns between the v1 documented list and the v1.1 list.

    Renames pair unmatched v1 names to unmatched v1.1 names by similarity
    (difflib ratio >= RENAME_THRESHOLD); each claim carries both names and
    the score, never a positional inference.
    """
    v1_set, v11_set = set(v1_names), set(v11_names)
    unchanged = sorted(v1_set & v11_set)
    removed_pool = sorted(v1_set - v11_set)
    added_pool = sorted(v11_set - v1_set)

    renames = []
    still_removed = []
    pool = list(added_pool)
    for old in removed_pool:
        best, best_score = None, 0.0
        for candidate in pool:
            score = difflib.SequenceMatcher(None, old, candidate).ratio()
            if score > best_score:
                best, best_score = candidate, score
        if best is not None and best_score >= RENAME_THRESHOLD:
            renames.append({"from": old, "to": best, "similarity": round(best_score, 3)})
            pool.remove(best)
        else:
            still_removed.append(old)

    return {
        "v1_count": len(v1_names),
        "v11_count": len(v11_names),
        "unchanged": unchanged,
        "renamed": renames,
        "removed": still_removed,
        "added": pool,
        "v1_only_duplicates": [name for name, n in Counter(v1_names).items() if n > 1],
    }


def dtype_changed(db_cols: dict[str, str], v11_pairs: list[tuple[str, str]]) -> list[dict]:
    """Compare loaded v1 DB types with v1.1 FITS formats on common columns."""
    changes = []
    for name, fits_format in v11_pairs:
        letter = re.match(r"([A-Z])(\d*)", fits_format)
        fits_letter = letter.group(1) if letter else fits_format
        # DB names sanitize hyphens to underscores
        for db_name, db_type in db_cols.items():
            if db_name == name.replace("-", "_") and fits_letter in FITS_TO_PG:
                if FITS_TO_PG[fits_letter] != db_type:
                    changes.append(
                        {"column": name, "db_type": db_type, "v11_fits_format": fits_format}
                    )
    return changes


def id_space_delta(cur, photom_path: Path) -> dict:
    """Set-compare v1.1 PHOTOMETRY ids against live photometry_core ids."""
    with fits.open(photom_path, memmap=True) as hdul:
        v11_ids = np.asarray(hdul[1].data["id"])
    cur.execute("SELECT id FROM catalog.photometry_core")
    v1_ids = np.array([row[0] for row in cur.fetchall()], dtype=v11_ids.dtype)

    retained = int(np.intersect1d(v11_ids, v1_ids).size)
    dropped = int(np.setdiff1d(v1_ids, v11_ids).size)
    new = int(np.setdiff1d(v11_ids, v1_ids).size)
    return {
        "v1_live_count": int(v1_ids.size),
        "v11_count": int(v11_ids.size),
        "retained": retained,
        "dropped_from_v11": dropped,
        "new_in_v11": new,
        "code_path": "numpy intersect1d/setdiff1d over FITS 'id' column vs SELECT id FROM catalog.photometry_core",
    }


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Run the per-extension delta and the ID-space check."""
    conn = db_connect()
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "extensions": {}}
    try:
        with conn.cursor() as cur:
            for extname, v1_file, v11_file in EXTENSION_MAP:
                v1_names = parse_v1_doc(REFERENCE_DIR / v1_file)
                v11_pairs = parse_v11_inventory(REFERENCE_DIR / f"columns-v1.1-{v11_file}.txt")
                v11_names = [name for name, _fmt in v11_pairs]
                result = classify(v1_names, v11_names)

                table = next((t for t, e in DB_TABLE_MAP.items() if e == extname), None)
                if table:
                    cols = db_columns(cur, table)
                    result["loaded_table"] = table
                    result["loaded_column_count"] = len(cols)
                    result["dtype_changed"] = dtype_changed(cols, v11_pairs)
                    cur.execute(f"SELECT COUNT(*) FROM catalog.{table}")
                    result["loaded_row_count"] = cur.fetchone()[0]
                result["v11_row_count"] = 784016  # from gate 1.8 profile evidence

                # Validation invariant: unchanged + renamed + removed == v1 count
                check = (
                    len(result["unchanged"]) + len(result["renamed"]) + len(result["removed"])
                    == result["v1_count"]
                )
                result["v1_side_sum_ok"] = check
                out["extensions"][extname] = result

            config = yaml.safe_load(CONFIG_PATH.read_text())
            out["id_space"] = id_space_delta(cur, Path(config["catalogs"]["photom_primary"]))
    finally:
        conn.close()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
