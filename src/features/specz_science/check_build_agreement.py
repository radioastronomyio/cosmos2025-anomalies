"""Gate 5.4 full-data checks: key equality and independent source reduction.

Runs the builder's staging output against the independent restatements in
``verify.py`` over the complete captured snapshot: key-set equality for both
products, preferred-entry agreement for every source, conflict-flag
agreement, secure-preferred agreement, population A/B agreement, and the
no-Priority-0-preferred invariant. Discrepancies abort with counts and
examples; success prints a compact reconciliation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import canonical as ss_canonical  # noqa: E402
from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402


def main() -> None:
    paths = ss_config.resolve_paths()
    data = ssv.load_snapshot_data(paths=paths)
    products = paths.staging_dir / "products"

    source_records = list(ss_canonical.read_jsonl(products / "sources-presplit.jsonl"))
    measurement_records = list(
        ss_canonical.read_jsonl(products / "measurements.jsonl")
    )

    failures: list[str] = []

    source_keys = [record["catalog_id"] for record in source_records]
    if source_keys != sorted(data.catalog_ids):
        failures.append(
            "source-summary keys differ from the catalog id set "
            f"({len(source_keys)} vs {len(data.catalog_ids)})"
        )
    measurement_keys = [record["id_specz"] for record in measurement_records]
    if measurement_keys != sorted(data.all_by_id):
        failures.append(
            "measurement audit keys differ from the _all entry id set "
            f"({len(measurement_keys)} vs {len(data.all_by_id)})"
        )

    independent_preferred = ssv.preferred_entry_independent(data)
    independent_flags = ssv.conflict_flags_independent(data)

    preferred_disagreements = []
    flag_disagreements = []
    secure_disagreements = []
    tie_disagreements = []
    population_disagreements = []
    priority0_preferred = []
    unmatched_native = []
    unique_members = set(data.unique_by_id)

    by_catalog = {record["catalog_id"]: record for record in source_records}
    for source_id, record in by_catalog.items():
        independent_entry = independent_preferred.get(source_id)
        builder_id = record["preferred_id_specz"]
        independent_id = independent_entry.id_specz if independent_entry else None
        if builder_id != independent_id:
            preferred_disagreements.append(
                (source_id, builder_id, independent_id)
            )
        if builder_id is not None:
            entry = data.unique_by_id.get(builder_id)
            if entry is not None and (entry.priority or 0) == 0:
                priority0_preferred.append(source_id)
        builder_tie = sorted(record["preferred_tied_ids"])
        if builder_id is None:
            independent_tie: list[int] = []
        else:
            winning = independent_entry.confidence_level
            independent_tie = sorted(
                item.id_specz
                for item in data.unique_groups.get(source_id, [])
                if item.numeric_valid_z
                and item.confidence_level == winning
            ) if independent_entry is not None else []
        if builder_tie != independent_tie:
            tie_disagreements.append((source_id, builder_tie, independent_tie))
        flags = independent_flags.get(source_id, {})
        for name in (
            "unique_numeric_conflict",
            "secure_all_conflict",
            "other_measurement_disagreement",
        ):
            if bool(record[name]) is not bool(flags.get(name)):
                flag_disagreements.append((source_id, name))
        if bool(record["preferred_entry_is_secure"]) is not (
            independent_entry is not None and ssv.entry_is_secure(independent_entry)
        ):
            secure_disagreements.append(source_id)
        builder_a = bool(record["population_a"])
        independent_a = source_id in data.all_groups and source_id not in data.unique_groups
        builder_b = bool(record["population_b"])
        independent_b = len(data.unique_groups.get(source_id, [])) > 1
        if builder_a is not independent_a or builder_b is not independent_b:
            population_disagreements.append(source_id)

    for record in measurement_records:
        entry = data.all_by_id[record["id_specz"]]
        for name in Specz_native_fields():
            if record["native_" + name] != getattr(entry, name):
                unmatched_native.append((record["id_specz"], name))
                break
        if record["is_unique_member"] is not (
            record["id_specz"] in unique_members
        ):
            unmatched_native.append((record["id_specz"], "is_unique_member"))
            break

    def summarize(name: str, items: list) -> None:
        if items:
            failures.append(f"{name}: {len(items)} discrepancies, e.g. {items[:3]}")

    summarize("preferred disagreements", preferred_disagreements)
    summarize("tie-list disagreements", tie_disagreements)
    summarize("conflict-flag disagreements", flag_disagreements)
    summarize("secure-preferred disagreements", secure_disagreements)
    summarize("population disagreements", population_disagreements)
    summarize("priority-0 preferred", priority0_preferred)
    summarize("native-field mismatches", unmatched_native)

    if failures:
        print(json.dumps({"status": "FAILED", "failures": failures}, indent=2))
        raise SystemExit(1)

    eligible_basis = sum(
        1 for record in source_records if record["eligibility_basis_primary_pre_split"]
    )
    validation_basis = sum(
        1 for record in source_records if record["eligibility_basis_validation_pre_split"]
    )
    summary = {
        "status": "OK",
        "source_records": len(source_records),
        "measurement_records": len(measurement_records),
        "preferred_agreement": "all sources",
        "conflict_flag_agreement": "all sources",
        "no_priority0_preferred": True,
        "population_a_sources": sum(
            1 for record in source_records if record["population_a"]
        ),
        "population_b_sources": sum(
            1 for record in source_records if record["population_b"]
        ),
        "eligibility_basis_primary_pre_split": eligible_basis,
        "eligibility_basis_validation_pre_split": validation_basis,
        "sources_with_any_conflict_veto": sum(
            1
            for record in source_records
            if record["unique_numeric_conflict"] or record["secure_all_conflict"]
        ),
        "corroboration_statuses": {
            status: sum(
                1
                for record in source_records
                if record["corroboration_status"] == status
            )
            for status in (
                "singly_supported",
                "multiply_supported",
                "not_assessable",
                "conflicting",
            )
        },
    }
    print(json.dumps(summary, indent=2))


def Specz_native_fields():
    return [
        name
        for name in ssv.SpeczEntry.__dataclass_fields__
        if name != "id_specz"
    ]


if __name__ == "__main__":
    main()
