"""Gate 5.1 machine checks: frozen policy validation and split algorithm.

These tests enforce the approved contract mechanically: the tracked policy
file validates against the approved structure and value domains; any missing
field, unexpected key, wrong type, or out-of-domain value fails by name; the
flag/confidence mapping matches the compilation README's documented system;
and the P-06 tile algorithm is deterministic, order-independent, and sensitive
to salt changes.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from src.features.specz_science import policy as ss_policy
from src.features.specz_science import splits as ss_splits

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def approved_document() -> dict:
    return yaml.safe_load(
        ss_policy.DEFAULT_POLICY_PATH.read_text(encoding="utf-8")
    )


def _write_variant(document: dict, tmp_path: Path) -> Path:
    path = tmp_path / "policy-variant.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def test_frozen_policy_loads_and_is_read_only() -> None:
    loaded = ss_policy.load_frozen_policy()
    assert loaded["policy_id"] == ss_policy.POLICY_ID
    with pytest.raises(TypeError):
        loaded["policy_id"] = "mutated"  # type: ignore[index]


def test_missing_key_fails_by_name(approved_document: dict, tmp_path: Path) -> None:
    for section, key in (
        ("association", "no_association_sentinel"),
        ("quality", "base_flag_confidence"),
        ("conflict", "threshold"),
        ("splits", "salt"),
    ):
        variant = copy.deepcopy(approved_document)
        del variant[section][key]
        with pytest.raises(ss_policy.PolicyError, match=key):
            ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))


def test_missing_top_level_section_fails(approved_document: dict, tmp_path: Path) -> None:
    variant = copy.deepcopy(approved_document)
    del variant["eligibility"]
    with pytest.raises(ss_policy.PolicyError, match="eligibility"):
        ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))


def test_extra_key_fails_by_name(approved_document: dict, tmp_path: Path) -> None:
    variant = copy.deepcopy(approved_document)
    variant["conflict"]["threshold_z"] = 0.005
    with pytest.raises(ss_policy.PolicyError, match="threshold_z"):
        ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))
    variant = copy.deepcopy(approved_document)
    variant["extra_section"] = {}
    with pytest.raises(ss_policy.PolicyError, match="extra_section"):
        ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))


def test_wrong_type_fails(approved_document: dict, tmp_path: Path) -> None:
    variant = copy.deepcopy(approved_document)
    variant["conflict"]["threshold"] = "0.005"
    with pytest.raises(ss_policy.PolicyError, match="conflict.threshold"):
        ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))
    variant = copy.deepcopy(approved_document)
    variant["secure_measurement"]["confidence_min"] = True
    with pytest.raises(ss_policy.PolicyError, match="confidence_min"):
        ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))


@pytest.mark.parametrize(
    "mutation",
    [
        # Out-of-domain values rejected across sections.
        lambda d: d["conflict"].__setitem__("threshold", 0.0),
        lambda d: d["conflict"].__setitem__("threshold", -0.005),
        lambda d: d["quality"]["recognized_measured_flags"].remove(19),
        lambda d: d["quality"]["recognized_measured_flags"].append(5),
        lambda d: d["quality"]["base_flag_confidence"].__setitem__(3, 94),
        lambda d: d["secure_measurement"]["allowed_flags"].append(2),
        lambda d: d["secure_measurement"].__setitem__("confidence_min", 90),
        lambda d: d["numeric_validity"].__setitem__("upper_redshift_limit", 20.0),
        lambda d: d["association"].__setitem__("no_association_sentinel", -99),
        lambda d: d["classification"]["broad_line_flags"].remove(19),
        lambda d: d["eligibility"]["separate_validation"]["allowed_photometric_types"].append(1),
        lambda d: d["preferred_reported_z"].__setitem__("confidence_domain", [0, 1]),
        lambda d: d["splits"]["valid_tile_domain"].remove("B10"),
        lambda d: d["splits"].__setitem__("holdout_count", 5),
        lambda d: d["splits"].__setitem__("salt", "cosmos2025-p2r05-spatial-v2"),
        lambda d: d["sensitivity"]["variants"].pop(),
        lambda d: d["sensitivity"]["variants"][0].__setitem__("confidence_min", 96),
        lambda d: d["adoption"].__setitem__("product_state", "adopted"),
        lambda d: d["upstream_report"].__setitem__("transmission", "authorized"),
        lambda d: d["spec_identity"].__setitem__("sha256", "0" * 64),
    ],
)
def test_out_of_domain_values_fail(
    approved_document: dict, tmp_path: Path, mutation
) -> None:
    variant = copy.deepcopy(approved_document)
    mutation(variant)
    with pytest.raises(ss_policy.PolicyError):
        ss_policy.load_frozen_policy(_write_variant(variant, tmp_path))


def test_flag_confidence_mapping_matches_compilation_readme() -> None:
    """Base flags per the pinned compilation README quality table."""
    policy = ss_policy.load_frozen_policy()
    expected = {1: 50, 2: 80, 3: 95, 4: 97, 9: 85, 11: 50, 12: 80, 13: 95, 14: 97, 19: 85}
    for flag, confidence in expected.items():
        assert ss_policy.flag_expected_confidence(policy, flag) == confidence
    # Flags 0/10 do not denote a measured redshift; unknown flags unclassified.
    for flag in (0, 10, 5, 6, -1, -3, 99):
        assert ss_policy.flag_expected_confidence(policy, flag) is None


def test_tile_map_partitions_and_determinism() -> None:
    policy = ss_policy.load_frozen_policy()
    mapping = ss_splits.tile_map(policy)
    assert len(mapping) == 20
    assert set(mapping) == set(ss_policy.VALID_TILE_DOMAIN)
    counts = {
        name: sum(1 for value in mapping.values() if value == name)
        for name in ss_splits.ASSIGNMENT_VALUES
        if name != ss_splits.UNASSIGNED
    }
    assert counts == {
        ss_splits.HOLDOUT: 4,
        ss_splits.VALIDATION: 4,
        ss_splits.DEVELOPMENT: 12,
    }
    assert ss_splits.tile_map(policy) == mapping
    assert ss_splits.canonical_tile_map_digest(mapping) == (
        ss_splits.canonical_tile_map_digest(dict(reversed(list(mapping.items()))))
    )


def test_tile_map_is_order_independent_and_salt_sensitive(
    approved_document: dict, tmp_path: Path
) -> None:
    baseline = ss_splits.tile_map(ss_policy.load_frozen_policy())
    shuffled = copy.deepcopy(approved_document)
    shuffled["splits"]["valid_tile_domain"] = list(
        reversed(shuffled["splits"]["valid_tile_domain"])
    )
    path = _write_variant(shuffled, tmp_path)
    # The written variant differs only in domain order; validate manually
    # because strict loaders reject nothing here, then compare maps.
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert ss_splits.tile_map(document) == baseline
    resalted = copy.deepcopy(approved_document)
    resalted["splits"]["salt"] = "cosmos2025-p2r05-spatial-v0"
    document = yaml.safe_load(_write_variant(resalted, tmp_path).read_text(encoding="utf-8"))
    assert ss_splits.tile_map(document) != baseline


def test_assign_tile_null_and_out_of_domain_are_unassigned() -> None:
    mapping = ss_splits.tile_map(ss_policy.load_frozen_policy())
    assert ss_splits.assign_tile(mapping, None) == ss_splits.UNASSIGNED
    assert ss_splits.assign_tile(mapping, "C7") == ss_splits.UNASSIGNED
    assert ss_splits.assign_tile(mapping, "") == ss_splits.UNASSIGNED
    known = next(iter(mapping))
    assert ss_splits.assign_tile(mapping, known) == mapping[known]


def test_tile_map_rejects_duplicate_domain(approved_document: dict) -> None:
    variant = copy.deepcopy(approved_document)
    variant["splits"]["valid_tile_domain"] = [
        *(label for label in variant["splits"]["valid_tile_domain"] if label != "B10"),
        "A1",
    ]
    with pytest.raises(ss_policy.PolicyError, match="duplicate"):
        ss_splits.tile_map(variant)


def test_tile_map_rejects_mismatched_counts(approved_document: dict) -> None:
    variant = copy.deepcopy(approved_document)
    variant["splits"]["development_count"] = 11
    with pytest.raises(ss_policy.PolicyError, match="do not sum"):
        ss_splits.tile_map(variant)


def test_policy_file_bytes_match_tracked_path() -> None:
    assert ss_policy.DEFAULT_POLICY_PATH == (
        REPO_ROOT / "configs" / "specz_science_policy_v1.yaml"
    )
    assert ss_policy.policy_semantic_digest() == ss_policy.policy_semantic_digest(
        ss_policy.DEFAULT_POLICY_PATH
    )
