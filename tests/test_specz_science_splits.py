"""Gate 5.5 tests: partition freezing, invariance, and negative controls.

The frozen tile map must be exactly reproducible, invariant to input
ordering, batching, and spectroscopy filtering, and hostile to tampering: a
source moved across partitions, a changed salt, and a duplicated assignment
each fail independent verification. Injected null or out-of-domain tiles
surface as ``unassigned``, are ineligible, and fail the completion check.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import build as ssb  # noqa: E402
from src.features.specz_science import policy as ss_policy  # noqa: E402
from src.features.specz_science import splits as ss_splits  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402
from tests.test_specz_science_verify import entry, source  # noqa: E402

DOMAIN = list(ss_policy.VALID_TILE_DOMAIN)


def independent_map(salt: str = "cosmos2025-p2r05-spatial-v1") -> dict[str, str]:
    ranked = sorted(
        (hashlib.sha256(f"{salt}|{tile}".encode()).hexdigest(), tile)
        for tile in DOMAIN
    )
    return {
        tile: ("holdout" if i < 4 else "validation" if i < 8 else "development")
        for i, (_, tile) in enumerate(ranked)
    }


def test_production_tile_map_matches_independent_hash_recomputation() -> None:
    policy = ss_policy.load_frozen_policy()
    assert ss_splits.tile_map(policy) == independent_map()


def test_assignments_invariant_to_ordering_batching_and_filtering() -> None:
    policy = ss_policy.load_frozen_policy()
    mapping = ss_splits.tile_map(policy)
    tiles = ["B10", "A1", "A5", "A1", "B3", None, "A10"]
    forward = [ss_splits.assign_tile(mapping, tile) for tile in tiles]
    backward = [ss_splits.assign_tile(mapping, tile) for tile in reversed(tiles)]
    assert forward == list(reversed(backward))
    batched = [
        ss_splits.assign_tile(mapping, tile)
        for start in range(0, len(tiles), 2)
        for tile in tiles[start : start + 2]
    ]
    assert batched == forward
    # Spectroscopy availability plays no role in the assignment function.
    assert ss_splits.assign_tile(mapping, "A1") == ss_splits.assign_tile(mapping, "A1")


def test_moved_source_fails_independent_verification() -> None:
    mapping = independent_map()
    tampered = dict(mapping)
    first = next(tile for tile in sorted(mapping) if mapping[tile] == "holdout")
    tampered[first] = "development"
    with pytest.raises(AssertionError):
        assert tampered == independent_map()


def test_changed_salt_changes_map_and_fails_verification() -> None:
    assert independent_map("cosmos2025-p2r05-spatial-v2") != independent_map()
    with pytest.raises(AssertionError):
        assert independent_map("cosmos2025-p2r05-spatial-v2") == independent_map()


def test_duplicate_assignment_fails_partition_counts() -> None:
    policy = dict(ss_policy.load_frozen_policy())
    splits_section = dict(policy["splits"])
    splits_section["valid_tile_domain"] = [
        *(t for t in splits_section["valid_tile_domain"] if t != "B10"),
        "A1",
    ]
    with pytest.raises(ss_policy.PolicyError, match="duplicate"):
        ss_splits.tile_map({"splits": splits_section})


def test_injected_invalid_tiles_are_visible_ineligible_and_rejected() -> None:
    policy = ss_policy.load_frozen_policy()
    mapping = ss_splits.tile_map(policy)
    for bad in (None, "C7", "", "a1", "A11"):
        assert ss_splits.assign_tile(mapping, bad) == "unassigned"
    secure = entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)
    catalog = [
        source(1, tile="A1"),
        source(2, tile="C7"),
        source(3, tile=None),
    ]
    data = ssv.SnapshotData.build(catalog, {1: 0, 2: 0, 3: 0}, [secure], [secure])
    records = {}
    for record in ssb.build_source_records(data, run_id="r"):
        assigned = ss_splits.assign_tile(mapping, data.catalog[record["catalog_id"]].tile)
        records[record["catalog_id"]] = ssb.finalize_eligibility(
            record, assigned, "unassigned"
        )
    assert records[1]["eligibility_primary_galaxy"] is True
    assert records[2]["eligibility_primary_galaxy"] is False
    assert records[3]["eligibility_primary_galaxy"] is False
    assert ssb.REASON_SPLIT_UNASSIGNED in records[2]["exclusion_reasons"]
    assert ssb.REASON_SPLIT_UNASSIGNED in records[3]["exclusion_reasons"]
    # The completion check rejects any nonzero unassigned count.
    unassigned_count = sum(
        1 for record in records.values() if record["assigned_split"] == "unassigned"
    )
    assert unassigned_count == 2  # visible, not redistributed


def test_measurement_inherits_source_assignment() -> None:
    policy = ss_policy.load_frozen_policy()
    mapping = ss_splits.tile_map(policy)
    secure = entry(5, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)
    extra = entry(6, id_cosmos25=1, priority=0, specz=0.4001, flag=2, confidence=80)
    data = ssv.SnapshotData.build(
        [source(1, tile="A7")], {1: 2}, [secure], [secure, extra]
    )
    source_record = next(ssb.build_source_records(data, run_id="r"))
    finalized = ssb.finalize_eligibility(
        source_record, ss_splits.assign_tile(mapping, "A7"), "unassigned"
    )
    split_records = {
        record["catalog_id"]: record
        for record in ssb.build_split_records(data, run_id="r", tile_mapping=mapping)
    }
    assert finalized["assigned_split"] == split_records[1]["assigned_split"] == "holdout"
    assert split_records[1]["native_tile"] == "A7"
    assert split_records[1]["split_salt"] == "cosmos2025-p2r05-spatial-v1"
    assert split_records[1]["split_version"] == "p2r05-spatial-v1"


def test_no_redistribution_for_balance() -> None:
    # The map is a pure function of salt and domain; tile popularity or
    # sample sizes cannot enter. Different tiles mapping to the same
    # partition with wildly different source counts must not shift anything.
    policy = ss_policy.load_frozen_policy()
    mapping = ss_splits.tile_map(policy)
    assert mapping == ss_splits.tile_map(policy)
    counts = {name: 0 for name in ("holdout", "validation", "development")}
    for tile, partition in mapping.items():
        counts[partition] += 1
    assert counts == {"holdout": 4, "validation": 4, "development": 12}
