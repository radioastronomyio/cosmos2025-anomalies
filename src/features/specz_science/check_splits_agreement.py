"""Gate 5.5 full-data checks: independent tile-map and assignment reproduction.

Recomputes the P-06 tile map with a locally restated SHA-256 ranking (no
imports from ``splits.py``), compares it to the map recorded in the finalize
summary, and re-derives every catalog source's assignment from its native
tile against ``splits.jsonl`` and ``sources.jsonl``. Also asserts
measurement/source split agreement, the eligibility conjunctions with the
split gate, mutual exclusivity, and zero unassigned on the native domain.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import canonical as ss_canonical  # noqa: E402
from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402

SALT = "cosmos2025-p2r05-spatial-v1"
DOMAIN = [f"{letter}{number}" for letter in "AB" for number in range(1, 11)]


def independent_tile_map() -> dict[str, str]:
    """Restated P-06 algorithm; deliberately not importing the builder."""
    ranked = sorted(
        (hashlib.sha256(f"{SALT}|{tile}".encode("utf-8")).hexdigest(), tile)
        for tile in DOMAIN
    )
    assignment = {}
    for index, (_, tile) in enumerate(ranked):
        if index < 4:
            assignment[tile] = "holdout"
        elif index < 8:
            assignment[tile] = "validation"
        else:
            assignment[tile] = "development"
    return assignment


def main() -> None:
    paths = ss_config.resolve_paths()
    products = paths.staging_dir / "products"
    summary = json.loads(
        (products / "finalize-summary.json").read_text(encoding="utf-8")
    )
    data = ssv.load_snapshot_data(paths=paths)

    failures: list[str] = []
    expected_map = independent_tile_map()
    if dict(sorted(expected_map.items())) != summary["tile_map"]:
        failures.append("recorded tile map differs from independent recomputation")

    splits = {
        record["catalog_id"]: record
        for record in ss_canonical.read_jsonl(products / "splits.jsonl")
    }
    if set(splits) != data.catalog_ids:
        failures.append("split records do not cover the catalog id set exactly")

    mismatches = 0
    wrong_native = 0
    for source_id, record in splits.items():
        native_tile = data.catalog[source_id].tile
        if record["native_tile"] != native_tile:
            wrong_native += 1
        expected = expected_map.get(native_tile, "unassigned")
        if record["assigned_split"] != expected:
            mismatches += 1
    if wrong_native:
        failures.append(f"{wrong_native} split records carry a wrong native tile")
    if mismatches:
        failures.append(f"{mismatches} assignments differ from independent map")

    measurement_source_split_conflicts = 0
    sources = {
        record["catalog_id"]: record
        for record in ss_canonical.read_jsonl(products / "sources.jsonl")
    }
    for source_id, record in sources.items():
        if record["assigned_split"] != splits[source_id]["assigned_split"]:
            measurement_source_split_conflicts += 1
        valid_split = splits[source_id]["assigned_split"] != "unassigned"
        expected_primary = (
            record["eligibility_basis_primary_pre_split"] and valid_split
        )
        expected_validation = (
            record["eligibility_basis_validation_pre_split"] and valid_split
        )
        if record["eligibility_primary_galaxy"] != expected_primary:
            measurement_source_split_conflicts += 1
        if record["eligibility_separate_validation"] != expected_validation:
            measurement_source_split_conflicts += 1
        if record["eligibility_primary_galaxy"] and record["eligibility_separate_validation"]:
            failures.append(f"source {source_id} is eligible for both populations")
    if measurement_source_split_conflicts:
        failures.append(
            f"{measurement_source_split_conflicts} split/finalization inconsistencies"
        )

    counts = {
        "holdout_sources": sum(
            1 for r in splits.values() if r["assigned_split"] == "holdout"
        ),
        "validation_sources": sum(
            1 for r in splits.values() if r["assigned_split"] == "validation"
        ),
        "development_sources": sum(
            1 for r in splits.values() if r["assigned_split"] == "development"
        ),
        "unassigned_sources": sum(
            1 for r in splits.values() if r["assigned_split"] == "unassigned"
        ),
    }
    eligible_primary_tiles = {
        splits[source_id]["assigned_split"]
        for source_id, record in sources.items()
        if record["eligibility_primary_galaxy"]
    }
    eligible_validation_tiles = {
        splits[source_id]["assigned_split"]
        for source_id, record in sources.items()
        if record["eligibility_separate_validation"]
    }

    if failures:
        print(json.dumps({"status": "FAILED", "failures": failures}, indent=2))
        raise SystemExit(1)

    print(
        json.dumps(
            {
                "status": "OK",
                "tile_map_matches_independent_recomputation": True,
                "assignment_mismatches": 0,
                "split_counts": counts,
                "eligible_primary_split_distribution": sorted(eligible_primary_tiles),
                "eligible_validation_split_distribution": sorted(eligible_validation_tiles),
                "eligibility_mutually_exclusive": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
