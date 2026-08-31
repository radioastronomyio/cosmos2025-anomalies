#!/usr/bin/env python3
"""
Script Name  : characterize_specz_linkage_v11.py
Description  : Characterizes the corrected spec-z linkage, recovery populations, and selection function
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
P2R-04 gate 4.7 evidence command. Characterizes, from the sealed mirror and
re-read sources, everything the successor policy unit needs: the corrected
join path through Id_COSMOS25 with multiplicity distributions, recovery
population A (catalog sources present only in the measurement-level surface,
including where the deduplication's chosen representative went), recovery
population B (catalog sources named by more than one galaxy-level entry,
with redshift agreement), and the spectroscopic selection function of the
defective id_specz_khostovan25 column with surface-labelled precision and
recall.

This gate decides nothing. It writes no rows, creates no view, builds no
join, applies no confidence threshold, and promotes no measurement. Redshift
comparisons exclude sentinel values by the explicit rule specz > -90 and
handle duplicates per group. The deduplication representative for population
A is identified inside the compilation by nearest corrected-coordinate
separation among Priority=1 entries (a compilation self-crossmatch), never
by repairing the catalog column.

Usage
-----
    doppler run --project ml01 --config dev -- \
        python src/etl/characterize_specz_linkage_v11.py

Examples
--------
    Default invocation writes the full JSON enumeration to the gitignored
    staging directory and prints the decision-relevant summaries.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import json
import os
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import psycopg2
import yaml
from astropy.coordinates import SkyCoord
import astropy.units as u

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"

LINK_SENTINEL = -999
C25_SENTINEL = -999
COORD_FLOOR = -900.0
USABLE_Z_FLOOR = -90.0
REPRESENTATIVE_RADIUS_ARCSEC = 5.0
ZAGREEMENT_ABS_TOL = 0.005

# =============================================================================
# Functions
# =============================================================================


def load_config() -> dict:
    with open(CONFIG_PATH) as fh:
        return yaml.safe_load(fh)


def connect_readonly(config: dict):
    db = config["database"]
    return psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["target_database"],
        options="-c default_transaction_read_only=on",
    )


def fetch_table(cur, table, columns):
    cur.execute(
        f'SELECT {", ".join(columns)} FROM source."{table}"'
    )
    return list(zip(*cur.fetchall()))


def separation_matrix(ra1, dec1, ra2, dec2):
    return SkyCoord(
        np.asarray(ra1, float) * u.deg, np.asarray(dec1, float) * u.deg
    ).separation(
        SkyCoord(np.asarray(ra2, float) * u.deg, np.asarray(dec2, float) * u.deg)
    ).arcsec


def distribution(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items())}


def main() -> None:
    config = load_config()
    conn = connect_readonly(config)
    try:
        cur = conn.cursor()
        cat_id, cat_ra, cat_dec, cat_link = fetch_table(
            cur,
            "photometry_primary",
            ("id", "ra", "dec", "id_specz_khostovan25"),
        )
        cat_id = np.asarray(cat_id, dtype=np.int64)
        cat_ra = np.asarray(cat_ra, dtype=float)
        cat_dec = np.asarray(cat_dec, dtype=float)
        cat_link = np.asarray(cat_link, dtype=np.int64)

        uni_cols = (
            "id_specz", "ra_corrected", "dec_corrected", "priority",
            "specz", "flag", "confidence_level", "survey",
            "id_cosmos25",
        )
        uni = fetch_table(cur, "specz_compilation_unique", uni_cols)
        uni = {
            name: np.asarray(values)
            for name, values in zip(uni_cols, uni)
        }
        all_tab = fetch_table(cur, "specz_compilation_all", uni_cols)
        all_tab = {
            name: np.asarray(values)
            for name, values in zip(uni_cols, all_tab)
        }
    finally:
        conn.close()

    for table, data in (("unique", uni), ("all", all_tab)):
        data["id_specz"] = data["id_specz"].astype(np.int64)
        data["priority"] = data["priority"].astype(np.int64)
        data["flag"] = data["flag"].astype(np.int64)
        data["confidence_level"] = data["confidence_level"].astype(np.int64)
        data["survey"] = data["survey"].astype(np.int64)
        data["id_cosmos25"] = data["id_cosmos25"].astype(np.int64)
        data["specz"] = data["specz"].astype(float)
        data["ra_corrected"] = data["ra_corrected"].astype(float)
        data["dec_corrected"] = data["dec_corrected"].astype(float)

    evidence: dict = {}

    # ------------------------------------------------------------------
    # Section 1: the corrected path through Id_COSMOS25.
    # ------------------------------------------------------------------
    valid_u = uni["id_cosmos25"] >= 0
    valid_a = all_tab["id_cosmos25"] >= 0
    galaxy_sources = np.unique(uni["id_cosmos25"][valid_u])
    measurement_sources = np.unique(all_tab["id_cosmos25"][valid_a])
    galaxy_set = set(galaxy_sources.tolist())
    measurement_set = set(measurement_sources.tolist())

    galaxy_mult = Counter(
        uni["id_cosmos25"][valid_u].tolist()
    )
    measurement_mult = Counter(all_tab["id_cosmos25"][valid_a].tolist())
    usable_u = valid_u & np.isfinite(uni["specz"]) & (uni["specz"] > USABLE_Z_FLOOR)
    usable_sources = np.unique(uni["id_cosmos25"][usable_u])

    by_confidence: dict[int, int] = {}
    for value in np.unique(uni["confidence_level"][usable_u]):
        by_confidence[int(value)] = int(
            np.unique(uni["id_cosmos25"][usable_u & (uni["confidence_level"] == value)]).size
        )

    evidence["corrected_path"] = {
        "surface": "source.specz_compilation_unique / _all via Id_COSMOS25",
        "distinct_sources_galaxy": int(galaxy_sources.size),
        "distinct_sources_measurement": int(measurement_sources.size),
        "galaxy_subset_of_measurement": bool(galaxy_set <= measurement_set),
        "multiplicity_galaxy": distribution(Counter(galaxy_mult.values())),
        "multiplicity_measurement": distribution(Counter(measurement_mult.values())),
        "usable_z_rule": "finite specz > -90 (sentinels -99/-999.x excluded; no confidence threshold applied)",
        "usable_z_sources_galaxy": int(usable_sources.size),
        "usable_z_sources_by_confidence_value_galaxy": {
            str(k): v for k, v in sorted(by_confidence.items())
        },
        "confidence_values_observed_galaxy_usable": sorted(
            int(v) for v in np.unique(uni["confidence_level"][usable_u])
        ),
    }

    # ------------------------------------------------------------------
    # Section 2: recovery population A — measurement-only catalog sources.
    # ------------------------------------------------------------------
    only_measurement = np.sort(np.fromiter(measurement_set - galaxy_set, dtype=np.int64))
    cat_index = {int(cid): index for index, cid in enumerate(cat_id)}

    a_mask = valid_a & np.isin(all_tab["id_cosmos25"], only_measurement)
    a_rows = np.flatnonzero(a_mask)
    priority_a = all_tab["priority"][a_rows]
    all_priority_zero = bool((priority_a == 0).all())

    galaxy_valid_idx = np.flatnonzero(valid_u)
    galaxy_coords = SkyCoord(
        uni["ra_corrected"][galaxy_valid_idx] * u.deg,
        uni["dec_corrected"][galaxy_valid_idx] * u.deg,
    )

    population_a: list[dict] = []
    representative_named_same = 0
    representative_named_other = 0
    representative_none = 0
    representative_seps: list[float] = []
    catalog_sep_representative_destination: list[float] = []
    entries_per_a_source: Counter = Counter()

    by_source = defaultdict(list)
    for row in a_rows:
        by_source[int(all_tab["id_cosmos25"][row])].append(int(row))

    for source in sorted(by_source):
        rows = by_source[source]
        entries_per_a_source[len(rows)] += 1
        cat_pos = cat_index[source]
        entry_sep = separation_matrix(
            all_tab["ra_corrected"][rows],
            all_tab["dec_corrected"][rows],
            [cat_ra[cat_pos]] * len(rows),
            [cat_dec[cat_pos]] * len(rows),
        )
        detail = {
            "catalog_id": source,
            "entries": [
                {
                    "id_specz": int(all_tab["id_specz"][row]),
                    "priority": int(all_tab["priority"][row]),
                    "flag": int(all_tab["flag"][row]),
                    "confidence_level": int(all_tab["confidence_level"][row]),
                    "survey": int(all_tab["survey"][row]),
                    "specz": float(all_tab["specz"][row]),
                    "separation_arcsec": float(sep),
                }
                for row, sep in zip(rows, entry_sep)
            ],
        }
        # Where did the deduplication's chosen representative go? Nearest
        # Priority=1 entry by corrected-coordinate separation.
        entry_coords = SkyCoord(
            all_tab["ra_corrected"][rows] * u.deg,
            all_tab["dec_corrected"][rows] * u.deg,
        )
        best = None
        for e_index, e_coord in enumerate(entry_coords):
            seps = galaxy_coords.separation(e_coord).arcsec
            order = np.argsort(seps)[:1]
            candidate_index = int(galaxy_valid_idx[order[0]])
            candidate_sep = float(seps[order[0]])
            if candidate_sep > REPRESENTATIVE_RADIUS_ARCSEC:
                continue
            if best is None or candidate_sep < best["separation_arcsec"]:
                best = {
                    "separation_arcsec": candidate_sep,
                    "representative_id_specz": int(uni["id_specz"][candidate_index]),
                    "representative_names_catalog_id": int(
                        uni["id_cosmos25"][candidate_index]
                    ),
                    "representative_flag": int(uni["flag"][candidate_index]),
                    "representative_confidence": int(
                        uni["confidence_level"][candidate_index]
                    ),
                    "via_entry_id_specz": int(all_tab["id_specz"][rows[e_index]]),
                }
        if best is None:
            representative_none += 1
            detail["representative"] = {
                "found_within_arcsec": REPRESENTATIVE_RADIUS_ARCSEC,
                "result": "none_within_radius",
            }
        else:
            named = best["representative_names_catalog_id"]
            if named == source:
                representative_named_same += 1
            else:
                representative_named_other += 1
                dest_pos = cat_index.get(named)
                if dest_pos is not None:
                    catalog_sep_representative_destination.append(
                        float(
                            separation_matrix(
                                [cat_ra[cat_pos]],
                                [cat_dec[cat_pos]],
                                [cat_ra[dest_pos]],
                                [cat_dec[dest_pos]],
                            )[0]
                        )
                    )
            representative_seps.append(best["separation_arcsec"])
            detail["representative"] = best
        population_a.append(detail)

    def stats(values):
        if not values:
            return {"n": 0}
        q = np.percentile(values, [0, 50, 90, 100])
        return {
            "n": len(values),
            "min": float(q[0]),
            "median": float(q[1]),
            "p90": float(q[2]),
            "max": float(q[3]),
        }

    evidence["population_a"] = {
        "definition": "catalog sources with measurement-level Id_COSMOS25 entries but no galaxy-level entry",
        "sources": int(only_measurement.size),
        "entries": int(a_rows.size),
        "all_entries_priority_zero": all_priority_zero,
        "entries_per_source": distribution(entries_per_a_source),
        "flag_distribution": distribution(
            Counter(all_tab["flag"][a_rows].tolist())
        ),
        "confidence_distribution": distribution(
            Counter(all_tab["confidence_level"][a_rows].tolist())
        ),
        "entry_to_catalog_separation_arcsec": stats(
            [
                entry["separation_arcsec"]
                for source in population_a
                for entry in source["entries"]
            ]
        ),
        "representative_search": (
            "nearest Priority=1 entry by corrected-coordinate separation "
            f"within {REPRESENTATIVE_RADIUS_ARCSEC} arcsec (compilation self-crossmatch)"
        ),
        "representative_found": representative_named_same
        + representative_named_other,
        "representative_names_same_catalog_source": representative_named_same,
        "representative_names_other_catalog_source": representative_named_other,
        "representative_none_within_radius": representative_none,
        "entry_to_representative_separation_arcsec": stats(representative_seps),
        "catalog_source_to_representative_destination_separation_arcsec": stats(
            catalog_sep_representative_destination
        ),
        "per_source": population_a,
    }

    # ------------------------------------------------------------------
    # Section 3: recovery population B — multiply-named galaxy sources.
    # ------------------------------------------------------------------
    multi = sorted(
        source for source, count in galaxy_mult.items() if count > 1
    )
    b_mask = valid_u & np.isin(uni["id_cosmos25"], multi)
    b_rows = np.flatnonzero(b_mask)
    population_b: list[dict] = []
    agreement_stats: list[dict] = []
    b_by_source = defaultdict(list)
    for row in b_rows:
        b_by_source[int(uni["id_cosmos25"][row])].append(int(row))

    for source in sorted(b_by_source):
        rows = b_by_source[source]
        cat_pos = cat_index[source]
        seps = separation_matrix(
            uni["ra_corrected"][rows],
            uni["dec_corrected"][rows],
            [cat_ra[cat_pos]] * len(rows),
            [cat_dec[cat_pos]] * len(rows),
        )
        z_values = uni["specz"][rows]
        usable = np.isfinite(z_values) & (z_values > USABLE_Z_FLOOR)
        excluded = int((~usable).sum())
        group = {
            "catalog_id": source,
            "entries": [
                {
                    "id_specz": int(uni["id_specz"][row]),
                    "specz": float(uni["specz"][row]),
                    "flag": int(uni["flag"][row]),
                    "confidence_level": int(uni["confidence_level"][row]),
                    "survey": int(uni["survey"][row]),
                    "separation_arcsec": float(sep),
                }
                for row, sep in zip(rows, seps)
            ],
            "sentinel_z_excluded": excluded,
        }
        if usable.sum() >= 2:
            usable_z = sorted(z_values[usable].tolist())
            delta = max(usable_z) - min(usable_z)
            group["usable_z_values"] = usable_z
            group["max_abs_delta_z"] = float(delta)
            group["agree_within_0.005"] = bool(delta <= ZAGREEMENT_ABS_TOL)
            agreement_stats.append(
                {"catalog_id": source, "max_abs_delta_z": float(delta)}
            )
        population_b.append(group)

    deltas = [item["max_abs_delta_z"] for item in agreement_stats]
    evidence["population_b"] = {
        "definition": "catalog sources named by more than one galaxy-level entry",
        "sources": len(multi),
        "entries": int(b_rows.size),
        "entries_per_source": distribution(
            Counter(len(rows) for rows in b_by_source.values())
        ),
        "flag_distribution": distribution(Counter(uni["flag"][b_rows].tolist())),
        "confidence_distribution": distribution(
            Counter(uni["confidence_level"][b_rows].tolist())
        ),
        "survey_distribution": distribution(
            Counter(uni["survey"][b_rows].tolist())
        ),
        "entry_to_catalog_separation_arcsec": stats(
            [
                entry["separation_arcsec"]
                for source in population_b
                for entry in source["entries"]
            ]
        ),
        "redshift_rule": "sentinels excluded by finite specz > -90; per-group reporting, no arbitrary duplicate selection",
        "sentinel_excluded_total": sum(
            group["sentinel_z_excluded"] for group in population_b
        ),
        "groups_with_two_plus_usable_z": len(agreement_stats),
        "agreement_tolerance_abs_delta_z": ZAGREEMENT_ABS_TOL,
        "groups_agreeing_within_tolerance": sum(
            1 for delta in deltas if delta <= ZAGREEMENT_ABS_TOL
        ),
        "max_abs_delta_z_distribution": stats(deltas),
        "per_source": population_b,
    }

    # ------------------------------------------------------------------
    # Section 4: the selection function of the defective column.
    # ------------------------------------------------------------------
    flagged = cat_link != LINK_SENTINEL
    flagged_ids = cat_id[flagged]
    link_values = np.unique(cat_link[flagged])
    resolving = np.isin(link_values, uni["id_specz"])
    resolving_values = set(link_values[resolving].tolist())

    # Corrected-path attachment for every catalog source.
    galaxy_positive = galaxy_set
    measurement_positive = measurement_set

    flagged_set = set(flagged_ids.tolist())
    tp_g = len(flagged_set & galaxy_positive)
    fp_g = len(flagged_set - galaxy_positive)
    fn_g = len(galaxy_positive - flagged_set)
    tn_g = int(cat_id.size) - tp_g - fp_g - fn_g
    tp_m = len(flagged_set & measurement_positive)
    fp_m = len(flagged_set - measurement_positive)
    fn_m = len(measurement_positive - flagged_set)
    tn_m = int(cat_id.size) - tp_m - fp_m - fn_m

    # Confidence/flag distributions of galaxy-level entries attached via the
    # corrected path, split by whether the source's defective link resolves.
    resolves_by_catalog = {
        int(cid): int(cat_link[cat_index[int(cid)]]) in resolving_values
        for cid in flagged_ids.tolist()
    }

    attached_flag = {"resolve": Counter(), "no_resolve": Counter()}
    attached_conf = {"resolve": Counter(), "no_resolve": Counter()}
    attached_none = {"resolve": 0, "no_resolve": 0}
    for row in np.flatnonzero(valid_u):
        source = int(uni["id_cosmos25"][row])
        if source not in flagged_set:
            continue
        bucket = "resolve" if resolves_by_catalog[source] else "no_resolve"
        attached_flag[bucket][int(uni["flag"][row])] += 1
        attached_conf[bucket][int(uni["confidence_level"][row])] += 1
    for cid in flagged_ids.tolist():
        bucket = "resolve" if resolves_by_catalog[cid] else "no_resolve"
        if cid not in galaxy_set:
            attached_none[bucket] += 1

    evidence["selection_function"] = {
        "defective_column": "photometry_primary.id_specz_khostovan25",
        "resolving_rule": "distinct non-sentinel link value present in galaxy-level Id_specz",
        "flagged_sources": len(flagged_set),
        "resolving_flagged_sources": int(resolving.sum()),
        "non_resolving_flagged_sources": int((~resolving).sum()),
        "precision_recall": {
            "against_galaxy_level": {
                "surface": "source.specz_compilation_unique via Id_COSMOS25",
                "tp": tp_g, "fp": fp_g, "fn": fn_g, "tn": tn_g,
                "precision": round(tp_g / (tp_g + fp_g), 6),
                "recall": round(tp_g / (tp_g + fn_g), 6),
                "denominator_positive": tp_g + fn_g,
            },
            "against_measurement_level": {
                "surface": "source.specz_compilation_all via Id_COSMOS25",
                "tp": tp_m, "fp": fp_m, "fn": fn_m, "tn": tn_m,
                "precision": round(tp_m / (tp_m + fp_m), 6),
                "recall": round(tp_m / (tp_m + fn_m), 6),
                "denominator_positive": tp_m + fn_m,
            },
        },
        "corrected_path_attached_galaxy_entries_flag_distribution": {
            bucket: distribution(counter)
            for bucket, counter in attached_flag.items()
        },
        "corrected_path_attached_galaxy_entries_confidence_distribution": {
            bucket: distribution(counter)
            for bucket, counter in attached_conf.items()
        },
        "flagged_sources_with_no_corrected_path_galaxy_entry": attached_none,
    }

    # ------------------------------------------------------------------
    # Post-state guarantees and evidence output.
    # ------------------------------------------------------------------
    conn = connect_readonly(config)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT count(*) FROM pg_views WHERE schemaname = 'source'"
        )
        views = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*) FROM pg_matviews WHERE schemaname = 'source'"
        )
        matviews = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*) FROM pg_namespace WHERE nspname = 'analysis'"
        )
        analysis = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM source.provenance")
        provenance = cur.fetchone()[0]
    finally:
        conn.close()
    evidence["post_state"] = {
        "source_views": int(views),
        "source_materialized_views": int(matviews),
        "analysis_schema_exists": bool(analysis),
        "provenance_rows": int(provenance),
        "rows_written_by_this_script": 0,
    }

    out_path = Path(config["specz_linkage"]["evidence_dir"]) / (
        "specz-linkage-g47-characterization.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(evidence, fh, indent=2, default=str)

    summary = {
        key: value
        for key, value in evidence.items()
        if key not in {"population_a", "population_b"}
    }
    summary["population_a"] = {
        k: v for k, v in evidence["population_a"].items() if k != "per_source"
    }
    summary["population_b"] = {
        k: v for k, v in evidence["population_b"].items() if k != "per_source"
    }
    print(json.dumps(summary, indent=2, default=str))
    print(f"full enumeration written: {out_path}")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
