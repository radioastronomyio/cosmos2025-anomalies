"""Gate 5.7 independent verifier: installed product versus native input.

A separately expressed check that never calls the builders in ``build.py``
and never uses builder totals as its oracle: it streams the installed
product rows through the analyst connection and reproduces membership,
preferred entries, conflict flags, eligibility booleans, split identity,
population flags, and exclusion reasons from the captured snapshot using
the independent restatements in ``verify.py`` plus a locally recomputed
tile map. Any single differing source or measurement fails the check with
identifiers attached.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import install as ssi  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402

SALT = "cosmos2025-p2r05-spatial-v1"
DOMAIN = [f"{letter}{number}" for letter in "AB" for number in range(1, 11)]
BROAD_LINE_FLAGS = (11, 12, 13, 14, 19)


def independent_tile_map() -> dict[str, str]:
    ranked = sorted(
        (hashlib.sha256(f"{SALT}|{tile}".encode()).hexdigest(), tile)
        for tile in DOMAIN
    )
    return {
        tile: "holdout" if i < 4 else "validation" if i < 8 else "development"
        for i, (_, tile) in enumerate(ranked)
    }


def independent_reasons(
    *,
    unique_entries,
    all_entries,
    preferred,
    unique_conflict,
    secure_conflict,
    lephare_type,
    assigned_split,
) -> list[str]:
    """Restate the exclusion-reason set for one source from primitives."""
    reasons: list[str] = []
    if not unique_entries and not all_entries:
        reasons.append("no_association")
    if all_entries and not unique_entries:
        reasons.append("population_a_no_unique_entries")
    if unique_entries and preferred is None:
        reasons.append("no_numeric_valid_unique_candidate")
    if preferred is not None:
        if not preferred.numeric_valid_z:
            reasons.append("preferred_z_not_numeric_valid")
        if preferred.flag not in (3, 4, 13, 14):
            reasons.append("preferred_flag_not_in_secure_domain")
        confidence = preferred.confidence_level
        if confidence is None or not 0 <= confidence <= 100:
            reasons.append("preferred_confidence_out_of_domain")
        elif not 95 <= confidence <= 100:
            reasons.append("preferred_confidence_below_95")
        expected = ssv.flag_confidence(preferred.flag)
        if expected is not None and confidence != expected:
            reasons.append("preferred_flag_confidence_mapping_inconsistent")
    if unique_conflict:
        reasons.append("unique_numeric_conflict")
    if secure_conflict:
        reasons.append("secure_all_conflict")
    if lephare_type == 1:
        reasons.append("photometric_type_stellar")
    if lephare_type is None or lephare_type not in (0, 1, 2):
        reasons.append("photometric_type_unknown_or_missing")
    broad = any(
        entry.numeric_valid_z and entry.flag in BROAD_LINE_FLAGS
        for entry in all_entries
    )
    if broad:
        reasons.append("broad_line_evidence_present")
    if not broad and lephare_type != 2:
        reasons.append("no_broad_line_or_photometric_qso_evidence")
    if assigned_split == "unassigned":
        reasons.append("split_unassigned")
    return sorted(set(reasons))


def main() -> None:
    paths = ss_config.resolve_paths()
    data = ssv.load_snapshot_data(paths=paths)
    finalize = json.loads(
        (paths.staging_dir / "products" / "finalize-summary.json").read_text(encoding="utf-8")
    )
    run_id = finalize["run_id"]
    mapping = independent_tile_map()
    preferred = ssv.preferred_entry_independent(data)
    flags = ssv.conflict_flags_independent(data)

    connection, _ = ss_config.connect_analyst(paths=paths)
    failures: list[str] = []
    counters = {
        "sources_checked": 0,
        "measurements_checked": 0,
        "native_field_rows_checked": 0,
    }

    sources_stream = ssi._stream_installed(
        connection,
        ssi.SOURCES,
        run_id,
        "run_id, catalog_id",
        ssi._expected_columns(ssi.SOURCES),
    )
    for record in sources_stream:
        source_id = record["catalog_id"]
        counters["sources_checked"] += 1
        independent_entry = preferred.get(source_id)
        expected_preferred = (
            independent_entry.id_specz if independent_entry else None
        )
        if record["preferred_id_specz"] != expected_preferred:
            failures.append(
                f"source {source_id}: preferred {record['preferred_id_specz']} != {expected_preferred}"
            )
        expected_z = independent_entry.specz if independent_entry else None
        if record["preferred_reported_z"] != expected_z:
            failures.append(f"source {source_id}: preferred z differs")
        flag = flags.get(source_id, {})
        for name in (
            "unique_numeric_conflict",
            "secure_all_conflict",
            "other_measurement_disagreement",
        ):
            if bool(record[name]) is not bool(flag.get(name)):
                failures.append(f"source {source_id}: flag {name} differs")
        tile = data.catalog[source_id].tile
        expected_split = mapping.get(tile, "unassigned")
        if record["assigned_split"] != expected_split:
            failures.append(
                f"source {source_id}: split {record['assigned_split']} != {expected_split}"
            )
        secure_entry = independent_entry is not None and ssv.entry_is_secure(
            independent_entry
        )
        veto = bool(flag.get("unique_numeric_conflict")) or bool(
            flag.get("secure_all_conflict")
        )
        valid_split = expected_split != "unassigned"
        lephare = data.lephare_type.get(source_id)
        broad = any(
            entry.numeric_valid_z and entry.flag in BROAD_LINE_FLAGS
            for entry in data.all_groups.get(source_id, [])
        )
        expected_primary = (
            secure_entry and not veto and valid_split and lephare == 0 and not broad
        )
        expected_validation = (
            secure_entry
            and not veto
            and valid_split
            and lephare in (0, 2)
            and (broad or lephare == 2)
        )
        if bool(record["eligibility_primary_galaxy"]) is not expected_primary:
            failures.append(f"source {source_id}: primary eligibility differs")
        if bool(record["eligibility_separate_validation"]) is not expected_validation:
            failures.append(f"source {source_id}: validation eligibility differs")
        expected_reasons = independent_reasons(
            unique_entries=data.unique_groups.get(source_id, []),
            all_entries=data.all_groups.get(source_id, []),
            preferred=independent_entry,
            unique_conflict=bool(flag.get("unique_numeric_conflict")),
            secure_conflict=bool(flag.get("secure_all_conflict")),
            lephare_type=lephare,
            assigned_split=expected_split,
        )
        if sorted(record["exclusion_reasons"]) != expected_reasons:
            failures.append(
                f"source {source_id}: reasons {sorted(record['exclusion_reasons'])} != {expected_reasons}"
            )
        if len(failures) > 25:
            break

    if len(failures) <= 25:
        measurements_stream = ssi._stream_installed(
            connection,
            ssi.MEASUREMENTS,
            run_id,
            "run_id, id_specz",
            ssi._expected_columns(ssi.MEASUREMENTS),
        )
        native_fields = [
            name
            for name in ssv.SpeczEntry.__dataclass_fields__
            if name != "id_specz"
        ]
        for record in measurements_stream:
            counters["measurements_checked"] += 1
            entry = data.all_by_id[record["id_specz"]]
            for name in native_fields:
                if record["native_" + name] != getattr(entry, name):
                    failures.append(
                        f"measurement {record['id_specz']}: native {name} differs"
                    )
                    break
            counters["native_field_rows_checked"] += 1
            expected_status = (
                "no_association_sentinel"
                if entry.id_cosmos25 is None or entry.id_cosmos25 == -999
                else "associated"
                if entry.id_cosmos25 in data.catalog_ids
                else "unresolved_identifier"
            )
            if record["association_status"] != expected_status:
                failures.append(
                    f"measurement {record['id_specz']}: association {record['association_status']} != {expected_status}"
                )
            expected_resolved = (
                entry.id_cosmos25 if expected_status == "associated" else None
            )
            if record["resolved_catalog_id"] != expected_resolved:
                failures.append(
                    f"measurement {record['id_specz']}: resolved id "
                    f"{record['resolved_catalog_id']} != {expected_resolved}"
                )
            if bool(record["secure_measurement"]) is not ssv.entry_is_secure(entry):
                failures.append(f"measurement {record['id_specz']}: secure differs")
            if len(failures) > 25:
                break

    connection.close()
    if failures:
        print(
            json.dumps(
                {"status": "FAILED", "failures": failures[:25], **counters},
                indent=2,
            )
        )
        raise SystemExit(1)
    print(json.dumps({"status": "OK", **counters}, indent=2))


if __name__ == "__main__":
    main()
