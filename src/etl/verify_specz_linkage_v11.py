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
# The independent spherical-law-of-cosines route has a double-precision
# rounding bound well below 0.01 arcsec at the roughly one-degree median.
# Retaining 0.01 arcsec leaves several orders of magnitude for library-level
# trigonometric variation without accepting an observationally meaningful
# disagreement between the two calculations.
ALL_LINKS_CROSSCHECK_TOLERANCE_ARCSEC = 0.01

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
    # All-links population: every stored non-sentinel catalog link paired to
    # its measurement-level Id_specz row in specz_compilation_all.
    "defective_median": 4054.34,
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
    return out


def session_identity_and_readonly(conn) -> dict:
    """Record and require the single connection's identity and read-only state."""
    cur = conn.cursor()
    cur.execute(
        "SELECT current_database(), current_user, session_user, "
        "current_setting('default_transaction_read_only'), "
        "current_setting('transaction_read_only')"
    )
    database, current_user, session_user, default_read_only, transaction_read_only = (
        cur.fetchone()
    )
    facts = {
        "database": database,
        "current_user": current_user,
        "session_user": session_user,
        "default_transaction_read_only": default_read_only,
        "transaction_read_only": transaction_read_only,
    }
    if default_read_only != "on" or transaction_read_only != "on":
        raise SystemExit(f"read-only session requirement failed: {facts}")
    return facts


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


def catalog_rows_for_ids(
    catalog_id: np.ndarray, wanted: np.ndarray
) -> np.ndarray:
    """Resolve catalog identifiers to catalog row positions by explicit lookup.

    Subscripting a catalog array with an identifier is only correct while
    ``photometry_primary.id`` is contiguous, zero-based, and in ascending row
    order. Nothing in the schema enforces that, and a catalog that stops
    satisfying it returns a different source rather than an error, which is
    the same latent-error class the amendment chain exists to correct. This
    lookup removes the precondition instead of assuming it, and halts on an
    identifier the catalog does not carry rather than pairing silently.

    Parameters
    ----------
    catalog_id : np.ndarray
        The catalog's ``id`` column, in catalog row order.
    wanted : np.ndarray
        Identifiers to resolve, in the order the caller needs them back.

    Returns
    -------
    np.ndarray
        Row positions into the catalog arrays, aligned with ``wanted``.
    """
    order = np.argsort(catalog_id, kind="stable")
    sorted_ids = catalog_id[order]
    positions = np.searchsorted(sorted_ids, wanted)
    in_bounds = positions < sorted_ids.size
    found = np.zeros(wanted.size, dtype=bool)
    found[in_bounds] = sorted_ids[positions[in_bounds]] == wanted[in_bounds]
    if not bool(found.all()):
        missing = np.unique(wanted[~found])
        raise SystemExit(
            "catalog identifier absent from photometry_primary.id: "
            f"first {missing[:10].tolist()}, "
            f"{int((~found).sum())} of {int(wanted.size)} unresolved"
        )
    return order[positions]


def pair_catalog_link_carriers(
    catalog_link: np.ndarray, target_ids: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Associate stored catalog links with target rows by Id_specz value.

    The returned catalog rows are the sources that carry a stored link. They
    are deliberately selected from link positions, never from catalog IDs.
    """
    carrier_rows = np.flatnonzero(catalog_link != LINK_SENTINEL)
    carried_links = catalog_link[carrier_rows]
    target_order = np.argsort(target_ids, kind="stable")
    sorted_target_ids = target_ids[target_order]
    positions = np.searchsorted(sorted_target_ids, carried_links)
    in_bounds = positions < sorted_target_ids.size
    matched = np.zeros(carried_links.size, dtype=bool)
    matched[in_bounds] = (
        sorted_target_ids[positions[in_bounds]] == carried_links[in_bounds]
    )
    return carrier_rows[matched], target_order[positions[matched]], carried_links[matched]


def independent_all_links_median_arcsec(
    catalog_ra: np.ndarray,
    catalog_dec: np.ndarray,
    catalog_link: np.ndarray,
    all_ids: np.ndarray,
    all_ra: np.ndarray,
    all_dec: np.ndarray,
) -> float:
    """Recompute the all-links median through independent mapping and geometry."""
    coordinates_by_id = {
        int(identifier): (float(ra), float(dec))
        for identifier, ra, dec in zip(all_ids, all_ra, all_dec, strict=True)
    }
    primary_ra = []
    primary_dec = []
    linked_ra = []
    linked_dec = []
    for ra, dec, link in zip(catalog_ra, catalog_dec, catalog_link, strict=True):
        if link == LINK_SENTINEL:
            continue
        try:
            target_ra, target_dec = coordinates_by_id[int(link)]
        except KeyError as exc:
            raise SystemExit(f"stored link absent from measurement table: {link}") from exc
        primary_ra.append(float(ra))
        primary_dec.append(float(dec))
        linked_ra.append(target_ra)
        linked_dec.append(target_dec)

    ra1 = np.deg2rad(np.asarray(primary_ra))
    dec1 = np.deg2rad(np.asarray(primary_dec))
    ra2 = np.deg2rad(np.asarray(linked_ra))
    dec2 = np.deg2rad(np.asarray(linked_dec))
    cosine = (
        np.sin(dec1) * np.sin(dec2)
        + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2)
    )
    separations = np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0))) * 3600.0
    return float(np.median(separations))


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
        evidence["database_session"] = session_identity_and_readonly(conn)
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
        matched_rows = catalog_rows_for_ids(cat_id, c25[both])
        seps = separation_arcsec(
            ra25[both], dec25[both], cat_ra[matched_rows], cat_dec[matched_rows]
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
    cross_rows = catalog_rows_for_ids(cat_id, c25_all[valid_cross])
    cross_seps = separation_arcsec(
        ra_corr_all[valid_cross],
        dec_corr_all[valid_cross],
        cat_ra[cross_rows],
        cat_dec[cross_rows],
    )
    cross_stats = dist_stats(cross_seps)

    # All-links population: each catalog source carrying a non-sentinel link
    # pairs with its measurement-level Id_specz row and corrected coordinates.
    all_carrier_rows, all_link_rows, all_carried_links = pair_catalog_link_carriers(
        cat_link, ids_all
    )
    if all_carrier_rows.size != link_distinct.size:
        raise SystemExit(
            "all stored links must resolve in specz_compilation_all: "
            f"matched={all_carrier_rows.size} expected={link_distinct.size}"
        )
    all_link_seps = separation_arcsec(
        cat_ra[all_carrier_rows],
        cat_dec[all_carrier_rows],
        ra_corr_all[all_link_rows],
        dec_corr_all[all_link_rows],
    )
    all_link_stats = dist_stats(all_link_seps)

    # Resolving-subset population: the same carrying catalog sources, limited
    # to links present in the deduplicated Priority-1 table. Its coordinates
    # remain those of the selected spectroscopic measurement.
    resolving_carrier_rows, resolving_link_rows, resolving_carried_links = (
        pair_catalog_link_carriers(cat_link, ids_uni)
    )
    resolving_link_seps = separation_arcsec(
        cat_ra[resolving_carrier_rows],
        cat_dec[resolving_carrier_rows],
        ra_corr_uni[resolving_link_rows],
        dec_corr_uni[resolving_link_rows],
    )
    resolving_link_stats = dist_stats(resolving_link_seps)

    crosscheck_median = independent_all_links_median_arcsec(
        cat_ra, cat_dec, cat_link, ids_all, ra_corr_all, dec_corr_all
    )
    crosscheck_difference = abs(all_link_stats["median"] - crosscheck_median)
    if crosscheck_difference > ALL_LINKS_CROSSCHECK_TOLERANCE_ARCSEC:
        raise SystemExit(
            "all-links geometry cross-check disagrees: "
            f"difference={crosscheck_difference} arcsec"
        )

    evidence["geometry"] = {
        "compilation_crossmatch": {
            **cross_stats,
            "surface": "measurement_level rows with valid Id_COSMOS25 and valid corrected coordinates",
            "excluded_rows": int((~valid_cross).sum()),
        },
        "defective_path": {
            **all_link_stats,
            "population": "all_links",
            "surface": (
                "all stored non-sentinel catalog links paired to "
                "specz_compilation_all.Id_specz"
            ),
            "coordinate_basis": "specz_compilation_all.ra_corrected/dec_corrected",
            "excluded_rows": int(link_distinct.size - all_carried_links.size),
        },
        "defective_path_resolving_subset": {
            **resolving_link_stats,
            "population": "resolving_subset",
            "surface": (
                "stored catalog links present in specz_compilation_unique, paired "
                "to its selected measurement Id_specz row"
            ),
            "coordinate_basis": "specz_compilation_unique.ra_corrected/dec_corrected",
            "excluded_rows": int(link_distinct.size - resolving_carried_links.size),
        },
        "defective_path_all_links_crosscheck": {
            "population": "all_links",
            "method": "independent dictionary association plus clamped spherical law of cosines",
            "median": crosscheck_median,
            "primary_median": all_link_stats["median"],
            "absolute_difference_arcsec": crosscheck_difference,
            "tolerance_arcsec": ALL_LINKS_CROSSCHECK_TOLERANCE_ARCSEC,
            "tolerance_basis": (
                "0.01 arcsec exceeds double-precision spherical-law-of-cosines "
                "rounding at the approximately one-degree median by several orders"
            ),
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
            "defective_median", round(all_link_stats["median"], 2),
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
    mut_row = int(catalog_rows_for_ids(cat_id, c25_all[idx : idx + 1])[0])
    mut_sep = float(
        separation_arcsec(
            [ra_mut[idx]], [dec25_all[idx]], [cat_ra[mut_row]],
            [cat_dec[mut_row]],
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
    print(f"database session: {json.dumps(evidence['database_session'])}")
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
