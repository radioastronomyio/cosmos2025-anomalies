#!/usr/bin/env python3
"""
Script Name  : verify_specz_linkage_v11.py
Description  : Reproduces the P2R-04 spec-z linkage evidence against prior observations
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Gate 4.1 evidence command for spec P2R-04. Re-reads the two pinned spec-z
compilation FITS artifacts and the read-only `cosmos2025_v11.source` mirror,
reproduces every prior observation in the spec's table with an observed
counterpart, and establishes identifier semantics, namespace validity,
defective-path geometry, and value-range incompatibility by measurement.

The script is read-only: it opens one read-only PostgreSQL transaction, never
writes to any database, and infers, repairs, or materializes no linkage. Its
JSON evidence lands in the gitignored staging directory; the committed
worklog and review surface carry the observed numbers.

Usage
-----
    doppler run --project ml01 --config dev -- \
        python src/etl/verify_specz_linkage_v11.py

Examples
--------
    doppler run --project ml01 --config dev -- \
        python src/etl/verify_specz_linkage_v11.py
        Reproduces all sixteen prior observations and the four establishments.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import psycopg2
import yaml
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"

# Sentinel conventions used by the pinned artifacts. The link sentinel and the
# Id_COSMOS25 sentinel are both -999 in the shipped data; the usable-redshift
# cut at -90 separates the -99/-999 sentinel family from physical z >= 0
# without applying a confidence or quality threshold.
LINK_SENTINEL = -999
C25_SENTINEL = -999
COORD_FLOOR = -900.0
USABLE_Z_FLOOR = -90.0
MUTATION_ARCSEC = 0.5

# Prior expectations from spec P2R-04, stated as priors and never forced.
PRIORS = {
    "link_distinct": 37219,
    "link_resolving_galaxy": 24364,
    "link_not_resolving": 12855,
    "link_min": 223,
    "link_max": 165312,
    "id_specz_all_min": 1,
    "id_specz_all_max": 487666,
    "rows_all": 482579,
    "rows_unique": 261975,
    "namespace_sep_max": 0.0,
    "crossmatch_median": 0.084,
    "crossmatch_max": 0.998,
    "defective_median": 4054.0,
    "sources_unique": 45007,
    "sources_all": 46039,
    "usable_z_sources": 39165,
    "flagged_absent_unique": 3062,
    "flagged_absent_all": 2378,
    "multi_named_groups": 185,
    "multi_named_rows": 371,
}

# =============================================================================
# Functions
# =============================================================================


def load_config() -> dict:
    with open(CONFIG_PATH) as fh:
        return yaml.safe_load(fh)


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
            total += len(chunk)
    return digest.hexdigest(), total


def pin_against_manifest(config: dict, fits_path: Path) -> dict:
    """Freshly hash one artifact and compare with its manifest-declared pin."""
    manifest_path = Path(config["provenance"]["source_manifest_v11"])
    rel = None
    with open(manifest_path, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["relative_path"].endswith(fits_path.name):
                rel = row
                break
    if rel is None:
        raise SystemExit(f"no manifest row for {fits_path.name}")
    observed_sha, observed_bytes = sha256_file(fits_path)
    result = {
        "file": str(fits_path),
        "manifest_sha256": rel["sha256"],
        "observed_sha256": observed_sha,
        "manifest_bytes": int(rel["bytes"]),
        "observed_bytes": observed_bytes,
    }
    result["sha_match"] = result["manifest_sha256"] == result["observed_sha256"]
    result["bytes_match"] = result["manifest_bytes"] == result["observed_bytes"]
    return result


def connect_readonly(config: dict):
    db = config["database"]
    conn = psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["target_database"],
        options="-c default_transaction_read_only=on",
    )
    return conn


def load_catalog(conn) -> dict:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ra, dec, id_specz_khostovan25 "
        "FROM source.photometry_primary ORDER BY id"
    )
    rows = cur.fetchall()
    n = len(rows)
    out = {
        "id": np.fromiter((r[0] for r in rows), dtype=np.int64, count=n),
        "ra": np.fromiter((r[1] for r in rows), dtype=float, count=n),
        "dec": np.fromiter((r[2] for r in rows), dtype=float, count=n),
        "link": np.fromiter((r[3] for r in rows), dtype=np.int64, count=n),
    }
    if not np.array_equal(out["id"], np.arange(n, dtype=np.int64)):
        raise SystemExit("catalog id not contiguous zero-based; index shortcut invalid")
    return out


def column_float(table: Table, name: str) -> np.ndarray:
    col = table[name]
    if hasattr(col, "mask"):
        return np.asarray(col.filled(np.nan), dtype=float)
    return np.asarray(col, dtype=float)


def column_int(table: Table, name: str) -> np.ndarray:
    return np.asarray(table[name]).astype(np.int64)


def dist_stats(values: np.ndarray) -> dict:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if not v.size:
        return {"n": 0}
    q = np.percentile(v, [0, 50, 90, 99, 100])
    return {
        "n": int(v.size),
        "min": float(q[0]),
        "median": float(q[1]),
        "p90": float(q[2]),
        "p99": float(q[3]),
        "max": float(q[4]),
    }


def separation_arcsec(ra1, dec1, ra2, dec2) -> np.ndarray:
    return SkyCoord(
        np.asarray(ra1, float) * u.deg, np.asarray(dec1, float) * u.deg
    ).separation(
        SkyCoord(np.asarray(ra2, float) * u.deg, np.asarray(dec2, float) * u.deg)
    ).arcsec


def check(name: str, observed, prior) -> dict:
    agree = observed == prior
    return {
        "observation": name,
        "prior": prior,
        "observed": observed,
        "agreement": bool(agree),
    }


def galaxy_priority1_equality(all_tab: Table, uni_tab: Table) -> dict:
    """Column-set equality plus per-column value equality including masks/NaN."""
    result = {"column_set_equal": list(all_tab.colnames) == list(uni_tab.colnames)}
    if not result["column_set_equal"]:
        result["all_columns"] = list(all_tab.colnames)
        result["unique_columns"] = list(uni_tab.colnames)
        return result
    prio = column_int(all_tab, "Priority")
    subset = all_tab[prio == 1]
    result["subset_rows"] = int(len(subset))
    result["unique_rows"] = int(len(uni_tab))
    if len(subset) != len(uni_tab):
        result["row_count_equal"] = False
        return result
    result["row_count_equal"] = True

    # Try positional alignment first; fall back to Id_specz-keyed alignment.
    positional = True
    mismatched = []
    for name in all_tab.colnames:
        a, b = subset[name], uni_tab[name]
        a_mask = np.asarray(getattr(a, "mask", np.zeros(len(a), bool)))
        b_mask = np.asarray(getattr(b, "mask", np.zeros(len(b), bool)))
        if not np.array_equal(a_mask, b_mask):
            positional = False
            mismatched.append(f"{name}:mask")
            continue
        av = column_float(subset, name) if a.dtype.kind == "f" else None
        bv = column_float(uni_tab, name) if b.dtype.kind == "f" else None
        if av is not None:
            equal = np.array_equal(av, bv, equal_nan=True)
        else:
            equal = np.array_equal(
                np.asarray(a), np.asarray(b)
            )
        if not equal:
            positional = False
            mismatched.append(name)
    result["alignment"] = "positional" if positional else "sort_by_id_specz"
    if positional:
        result["per_column_equal"] = True
        result["mismatched_columns"] = []
        return result

    # Keyed alignment by the (established-unique) Id_specz.
    order_a = np.argsort(column_int(subset, "Id_specz"), kind="stable")
    order_b = np.argsort(column_int(uni_tab, "Id_specz"), kind="stable")
    keyed_equal = True
    for name in all_tab.colnames:
        a = subset[name][order_a]
        b = uni_tab[name][order_b]
        a_mask = np.asarray(getattr(a, "mask", np.zeros(len(a), bool)))
        b_mask = np.asarray(getattr(b, "mask", np.zeros(len(b), bool)))
        if not np.array_equal(a_mask, b_mask):
            keyed_equal = False
            mismatched.append(f"{name}:mask")
            continue
        if a.dtype.kind == "f":
            equal = np.array_equal(
                column_float(subset, name)[order_a],
                column_float(uni_tab, name)[order_b],
                equal_nan=True,
            )
        else:
            equal = np.array_equal(np.asarray(a), np.asarray(b))
        if not equal:
            keyed_equal = False
            if name not in mismatched:
                mismatched.append(name)
    result["per_column_equal"] = bool(keyed_equal)
    result["mismatched_columns"] = sorted(set(mismatched))
    return result


def main() -> None:
    config = load_config()
    evidence: dict = {}

    # ------------------------------------------------------------------
    # Source pinning: freshly observed hashes versus manifest declarations.
    # ------------------------------------------------------------------
    all_path = Path(config["specz"]["all_fits"])
    uni_path = Path(config["specz"]["unique_fits"])
    pins = {
        "all": pin_against_manifest(config, all_path),
        "unique": pin_against_manifest(config, uni_path),
    }
    evidence["source_pins"] = pins
    for key, pin in pins.items():
        if not (pin["sha_match"] and pin["bytes_match"]):
            raise SystemExit(f"manifest pin mismatch for {key}: {pin}")
    manifest_sha, _ = sha256_file(Path(config["provenance"]["source_manifest_v11"]))
    evidence["manifest_csv_sha256"] = manifest_sha

    # ------------------------------------------------------------------
    # Fresh reads: pinned FITS artifacts and the read-only mirror.
    # ------------------------------------------------------------------
    all_tab = Table.read(all_path, memmap=True)
    uni_tab = Table.read(uni_path, memmap=True)
    conn = connect_readonly(config)
    try:
        cat = load_catalog(conn)
    finally:
        conn.close()

    ids_all = column_int(all_tab, "Id_specz")
    ids_uni = column_int(uni_tab, "Id_specz")
    c25_all = column_int(all_tab, "Id_COSMOS25")
    c25_uni = column_int(uni_tab, "Id_COSMOS25")
    ra_corr_all = column_float(all_tab, "ra_corrected")
    dec_corr_all = column_float(all_tab, "dec_corrected")
    ra_corr_uni = column_float(uni_tab, "ra_corrected")
    dec_corr_uni = column_float(uni_tab, "dec_corrected")
    ra25_all = column_float(all_tab, "ra_COSMOS25")
    dec25_all = column_float(all_tab, "dec_COSMOS25")
    ra25_uni = column_float(uni_tab, "ra_COSMOS25")
    dec25_uni = column_float(uni_tab, "dec_COSMOS25")
    z_uni = column_float(uni_tab, "specz")
    tfields_all = len(all_tab.colnames)
    tfields_uni = len(uni_tab.colnames)

    cat_id, cat_ra, cat_dec, cat_link = (
        cat["id"], cat["ra"], cat["dec"], cat["link"]
    )

    # ------------------------------------------------------------------
    # Prior-observation reproduction.
    # ------------------------------------------------------------------
    linked = cat_link != LINK_SENTINEL
    link_values = cat_link[linked]
    link_distinct = np.unique(link_values)
    uni_id_set = set(ids_uni.tolist())

    resolving_mask = np.isin(link_distinct, ids_uni)
    resolving = int(resolving_mask.sum())

    src_uni = c25_uni[c25_uni >= 0]
    src_all = c25_all[c25_all >= 0]
    distinct_uni = np.unique(src_uni)
    distinct_all = np.unique(src_all)

    usable_rows_uni = (
        (c25_uni >= 0)
        & np.isfinite(z_uni)
        & (z_uni > USABLE_Z_FLOOR)
    )

    flagged_ids = cat_id[linked]
    absent_unique = np.setdiff1d(flagged_ids, distinct_uni)
    absent_all = np.setdiff1d(flagged_ids, distinct_all)

    counts_per_source = np.unique(src_uni, return_counts=True)[1]
    multi_mask = counts_per_source > 1
    multi_groups = int(multi_mask.sum())
    multi_rows = int(counts_per_source[multi_mask].sum())

    checks = [
        check("link_distinct", int(link_distinct.size), PRIORS["link_distinct"]),
        check("link_resolving_galaxy", resolving, PRIORS["link_resolving_galaxy"]),
        check(
            "link_not_resolving",
            int(link_distinct.size - resolving),
            PRIORS["link_not_resolving"],
        ),
        check("link_min", int(link_distinct.min()), PRIORS["link_min"]),
        check("link_max", int(link_distinct.max()), PRIORS["link_max"]),
        check("id_specz_all_min", int(ids_all.min()), PRIORS["id_specz_all_min"]),
        check("id_specz_all_max", int(ids_all.max()), PRIORS["id_specz_all_max"]),
        check("rows_all", int(len(all_tab)), PRIORS["rows_all"]),
        check("rows_unique", int(len(uni_tab)), PRIORS["rows_unique"]),
        check("sources_unique", int(distinct_uni.size), PRIORS["sources_unique"]),
        check("sources_all", int(distinct_all.size), PRIORS["sources_all"]),
        check(
            "usable_z_sources",
            int(np.unique(c25_uni[usable_rows_uni]).size),
            PRIORS["usable_z_sources"],
        ),
        check(
            "flagged_absent_unique", int(absent_unique.size),
            PRIORS["flagged_absent_unique"],
        ),
        check(
            "flagged_absent_all", int(absent_all.size),
            PRIORS["flagged_absent_all"],
        ),
        check("multi_named_groups", multi_groups, PRIORS["multi_named_groups"]),
        check("multi_named_rows", multi_rows, PRIORS["multi_named_rows"]),
    ]
    evidence["prior_checks"] = checks

    # ------------------------------------------------------------------
    # Establishment 1: identifier semantics.
    # ------------------------------------------------------------------
    evidence["id_specz_unique_all"] = {
        "total": int(ids_all.size),
        "distinct": int(np.unique(ids_all).size),
        "unique": bool(np.unique(ids_all).size == ids_all.size),
    }
    evidence["id_specz_unique_unique"] = {
        "total": int(ids_uni.size),
        "distinct": int(np.unique(ids_uni).size),
        "unique": bool(np.unique(ids_uni).size == ids_uni.size),
    }
    evidence["galaxy_priority1_equality"] = galaxy_priority1_equality(
        all_tab, uni_tab
    )
    evidence["tfields"] = {"all": tfields_all, "unique": tfields_uni}

    # ------------------------------------------------------------------
    # Establishment 2: namespace validity via separation distributions.
    # ------------------------------------------------------------------
    def namespace_check(c25, ra25, dec25, label):
        valid_id = c25 >= 0
        valid_coord = (
            np.isfinite(ra25) & np.isfinite(dec25)
            & (ra25 > COORD_FLOOR) & (dec25 > COORD_FLOOR)
        )
        both = valid_id & valid_coord
        excluded = {
            "rows_total": int(c25.size),
            "excluded_sentinel_id": int((~valid_id).sum()),
            "excluded_valid_id_invalid_coord": int(
                (valid_id & ~valid_coord).sum()
            ),
            "compared": int(both.sum()),
        }
        seps = separation_arcsec(
            ra25[both], dec25[both], cat_ra[c25[both]], cat_dec[c25[both]]
        )
        stats = dist_stats(seps)
        return {"surface": label, "exclusions": excluded, "separation": stats}

    evidence["namespace_validity"] = [
        namespace_check(c25_all, ra25_all, dec25_all, "measurement_level"),
        namespace_check(c25_uni, ra25_uni, dec25_uni, "galaxy_level"),
    ]
    ns_all = evidence["namespace_validity"][0]
    checks.append(
        check(
            "namespace_sep_max_measurement",
            round(ns_all["separation"]["max"], 12),
            PRIORS["namespace_sep_max"],
        )
    )

    # ------------------------------------------------------------------
    # Establishment 3: defective-path geometry versus the compilation's own
    # crossmatch. Both distributions, not a summary verdict.
    # ------------------------------------------------------------------
    valid_cross = (
        (c25_all >= 0)
        & np.isfinite(ra_corr_all)
        & np.isfinite(dec_corr_all)
        & (ra_corr_all > COORD_FLOOR)
        & (dec_corr_all > COORD_FLOOR)
    )
    cross_seps = separation_arcsec(
        ra_corr_all[valid_cross],
        dec_corr_all[valid_cross],
        cat_ra[c25_all[valid_cross]],
        cat_dec[c25_all[valid_cross]],
    )
    cross_stats = dist_stats(cross_seps)

    # Defective path: catalog source versus the galaxy-level entry named by
    # its stored link value, over the resolving values only.
    uni_order = np.argsort(ids_uni, kind="stable")
    sorted_uni_ids = ids_uni[uni_order]
    pos = np.searchsorted(sorted_uni_ids, link_distinct)
    pos_clipped = np.clip(pos, 0, sorted_uni_ids.size - 1)
    hit = sorted_uni_ids[pos_clipped] == link_distinct
    link_row = uni_order[pos_clipped[hit]]
    defective_seps = separation_arcsec(
        ra_corr_uni[link_row],
        dec_corr_uni[link_row],
        cat_ra[np.searchsorted(cat_id, link_distinct[hit])],
        cat_dec[np.searchsorted(cat_id, link_distinct[hit])],
    )
    defective_stats = dist_stats(defective_seps)

    evidence["geometry"] = {
        "compilation_crossmatch": {
            **cross_stats,
            "surface": "measurement_level rows with valid Id_COSMOS25 and valid corrected coordinates",
            "excluded_rows": int((~valid_cross).sum()),
        },
        "defective_path": {
            **defective_stats,
            "surface": "resolving stored link values joined to galaxy-level Id_specz",
            "excluded_rows": int((~hit).sum()),
        },
    }
    checks.append(
        check(
            "crossmatch_median", round(cross_stats["median"], 3),
            PRIORS["crossmatch_median"],
        )
    )
    checks.append(
        check(
            "crossmatch_max", round(cross_stats["max"], 3),
            PRIORS["crossmatch_max"],
        )
    )
    checks.append(
        check(
            "defective_median", round(defective_stats["median"], 0),
            PRIORS["defective_median"],
        )
    )

    # ------------------------------------------------------------------
    # Establishment 4: value-range incompatibility.
    # ------------------------------------------------------------------
    evidence["value_range"] = {
        "stored_link_range": [int(link_distinct.min()), int(link_distinct.max())],
        "compilation_id_specz_range": [int(ids_all.min()), int(ids_all.max())],
        "stored_values_exceeding_compilation_max": int(
            (link_distinct > ids_all.max()).sum()
        ),
        "compilation_range_span_fraction": float(
            (link_distinct.max() - link_distinct.min())
            / (ids_all.max() - ids_all.min())
        ),
    }

    # ------------------------------------------------------------------
    # Mutation test: perturb one stored coordinate in a scratch copy and
    # prove the namespace check reports a non-zero separation.
    # ------------------------------------------------------------------
    both_all = (c25_all >= 0) & (ra25_all > COORD_FLOOR) & (dec25_all > COORD_FLOOR)
    idx = int(np.flatnonzero(both_all)[0])
    ra_mut = ra25_all.copy()
    ra_mut[idx] += MUTATION_ARCSEC / 3600.0
    mut_sep = float(
        separation_arcsec(
            [ra_mut[idx]], [dec25_all[idx]], [cat_ra[c25_all[idx]]],
            [cat_dec[c25_all[idx]]],
        )[0]
    )
    evidence["mutation_test"] = {
        "row_index": idx,
        "perturbation_arcsec": MUTATION_ARCSEC,
        "reported_separation_arcsec": mut_sep,
        "nonzero_reported": bool(mut_sep > 0),
    }

    # ------------------------------------------------------------------
    # Emit evidence.
    # ------------------------------------------------------------------
    evidence["prior_checks"] = checks
    out_path = Path(config["specz_linkage"]["gate_4_1_evidence"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(evidence, fh, indent=2, sort_keys=False)

    print(f"source pins: {json.dumps(pins, indent=2)}")
    print(f"manifest csv sha256: {manifest_sha}")
    print(f"TFIELDS all={tfields_all} unique={tfields_uni}")
    print(f"Id_specz uniqueness: {json.dumps(evidence['id_specz_unique_all'])}")
    print(
        "galaxy == Priority-1 equality: "
        f"{json.dumps(evidence['galaxy_priority1_equality'])}"
    )
    for ns in evidence["namespace_validity"]:
        print(f"namespace [{ns['surface']}]: {json.dumps(ns, indent=2)}")
    print(f"geometry: {json.dumps(evidence['geometry'], indent=2)}")
    print(f"value_range: {json.dumps(evidence['value_range'], indent=2)}")
    print(f"mutation_test: {json.dumps(evidence['mutation_test'], indent=2)}")
    print("\nprior observations (prior | observed | agreement):")
    for c in checks:
        print(f"  {c['observation']}: {c['prior']} | {c['observed']} | {c['agreement']}")
    disagreements = [c for c in checks if not c["agreement"]]
    print(f"\ndisagreements: {len(disagreements)}")
    print(f"evidence written: {out_path}")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
