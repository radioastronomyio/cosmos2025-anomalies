"""Frozen policy loading and validation for the P2R-05 spec-z science surface.

The tracked file ``configs/specz_science_policy_v1.yaml`` is the single source
of science policy. ``load_frozen_policy`` validates it against the structure
and value domains the operator approved with spec v1.0 and returns an
immutable view. Any missing field, unexpected key, wrong type, or
out-of-domain value raises ``PolicyError``. There are no defaults to fill in
and no override surface: a value the file does not state is a defect, not a
silent zero.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_PATH = REPO_ROOT / "configs" / "specz_science_policy_v1.yaml"

POLICY_ID = "p2r05-specz-policy-v1"
APPROVED_SPEC_SHA256 = (
    "7f481111ad826dd80b01106eeec71bfdaf0f5c649c0cc79b8661a0087af2757b"
)

VALID_TILE_DOMAIN = (
    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
)


class PolicyError(Exception):
    """Raised when the policy file deviates from the approved contract."""


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_float(value: Any) -> bool:
    return isinstance(value, float)


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


def _check_keys(
    section: Mapping[str, Any],
    expected: tuple[str, ...],
    where: str,
) -> None:
    actual = set(section)
    missing = sorted(set(expected) - actual)
    extra = sorted(actual - set(expected))
    if missing or extra:
        raise PolicyError(
            f"{where}: missing keys {missing}, unexpected keys {extra}"
        )


def _check_bool(section: Mapping[str, Any], key: str, where: str, expected: bool) -> None:
    value = section[key]
    if not _is_bool(value) or value is not expected:
        raise PolicyError(
            f"{where}.{key}: expected bool {expected}, got {value!r}"
        )


def _check_int(section: Mapping[str, Any], key: str, where: str, expected: int) -> None:
    value = section[key]
    if not _is_int(value) or value != expected:
        raise PolicyError(
            f"{where}.{key}: expected int {expected}, got {value!r}"
        )


def _check_str(section: Mapping[str, Any], key: str, where: str, expected: str) -> None:
    value = section[key]
    if not _is_str(value) or value != expected:
        raise PolicyError(
            f"{where}.{key}: expected {expected!r}, got {value!r}"
        )


def _check_int_list(
    value: Any, where: str, expected: tuple[int, ...]
) -> None:
    if not isinstance(value, list) or not all(_is_int(item) for item in value):
        raise PolicyError(f"{where}: expected list of ints, got {value!r}")
    if tuple(sorted(value)) != tuple(sorted(expected)):
        raise PolicyError(
            f"{where}: expected exactly {list(expected)}, got {value!r}"
        )


def _check_str_list(
    value: Any, where: str, expected: tuple[str, ...], *, ordered: bool = False
) -> None:
    if not isinstance(value, list) or not all(_is_str(item) for item in value):
        raise PolicyError(f"{where}: expected list of strings, got {value!r}")
    if ordered:
        if tuple(value) != expected:
            raise PolicyError(
                f"{where}: expected ordered {list(expected)}, got {value!r}"
            )
    elif tuple(sorted(value)) != tuple(sorted(expected)):
        raise PolicyError(
            f"{where}: expected exactly {list(expected)}, got {value!r}"
        )


TOP_LEVEL_KEYS = (
    "policy_id",
    "spec_identity",
    "association",
    "numeric_validity",
    "quality",
    "secure_measurement",
    "preferred_reported_z",
    "conflict",
    "classification",
    "eligibility",
    "splits",
    "diagnostics",
    "sensitivity",
    "upstream_report",
    "adoption",
)

BASE_FLAG_CONFIDENCE = {1: 50, 2: 80, 3: 95, 4: 97, 9: 85}
RECOGNIZED_MEASURED_FLAGS = (1, 2, 3, 4, 9, 11, 12, 13, 14, 19)
SECURE_FLAGS = (3, 4, 13, 14)
NON_MEASURED_FLAGS = (0, 10)
BROAD_LINE_FLAGS = (11, 12, 13, 14, 19)
CONFLICT_FLAGS = (
    "unique_numeric_conflict",
    "secure_all_conflict",
    "other_measurement_disagreement",
)
SENSITIVITY_VARIANT_NAMES = (
    "min_confidence_97",
    "abs_threshold_0p001",
    "normalized_0p005",
)


def _validate(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise PolicyError(f"policy root: expected mapping, got {type(document)!r}")
    _check_keys(document, TOP_LEVEL_KEYS, "policy root")
    _check_str(document, "policy_id", "policy root", POLICY_ID)

    identity = document["spec_identity"]
    _check_keys(identity, ("version", "sha256"), "spec_identity")
    _check_str(identity, "version", "spec_identity", "1.0")
    _check_str(identity, "sha256", "spec_identity", APPROVED_SPEC_SHA256)

    association = document["association"]
    _check_keys(
        association,
        (
            "compilation_join_column",
            "catalog_join_column",
            "catalog_relation",
            "no_association_sentinel",
            "retain_all_measurements",
            "summarize_all_catalog_sources",
            "population_a_ineligible_for_secure_use",
            "promote_priority_zero",
        ),
        "association",
    )
    _check_str(association, "compilation_join_column", "association", "id_cosmos25")
    _check_str(association, "catalog_join_column", "association", "id")
    _check_str(association, "catalog_relation", "association", "photometry_primary")
    _check_int(association, "no_association_sentinel", "association", -999)
    _check_bool(association, "retain_all_measurements", "association", True)
    _check_bool(association, "summarize_all_catalog_sources", "association", True)
    _check_bool(
        association, "population_a_ineligible_for_secure_use", "association", True
    )
    _check_bool(association, "promote_priority_zero", "association", False)

    numeric = document["numeric_validity"]
    _check_keys(
        numeric,
        (
            "require_non_null",
            "require_finite",
            "require_strictly_positive",
            "upper_redshift_limit",
        ),
        "numeric_validity",
    )
    _check_bool(numeric, "require_non_null", "numeric_validity", True)
    _check_bool(numeric, "require_finite", "numeric_validity", True)
    _check_bool(numeric, "require_strictly_positive", "numeric_validity", True)
    if numeric["upper_redshift_limit"] is not None:
        raise PolicyError(
            "numeric_validity.upper_redshift_limit: P-02 introduces no ceiling; "
            f"expected null, got {numeric['upper_redshift_limit']!r}"
        )

    quality = document["quality"]
    _check_keys(
        quality,
        (
            "recognized_measured_flags",
            "base_flag_confidence",
            "broad_line_offset",
            "non_measured_flags",
            "unrecognized_flags_unclassified",
        ),
        "quality",
    )
    _check_int_list(
        quality["recognized_measured_flags"],
        "quality.recognized_measured_flags",
        RECOGNIZED_MEASURED_FLAGS,
    )
    base = quality["base_flag_confidence"]
    if not isinstance(base, dict) or {
        key: value for key, value in base.items()
    } != BASE_FLAG_CONFIDENCE:
        raise PolicyError(
            f"quality.base_flag_confidence: expected {BASE_FLAG_CONFIDENCE}, got {base!r}"
        )
    if not all(_is_int(key) and _is_int(value) for key, value in base.items()):
        raise PolicyError(
            f"quality.base_flag_confidence: non-integer key or value in {base!r}"
        )
    _check_int(quality, "broad_line_offset", "quality", 10)
    _check_int_list(
        quality["non_measured_flags"], "quality.non_measured_flags", NON_MEASURED_FLAGS
    )
    _check_bool(
        quality, "unrecognized_flags_unclassified", "quality", True
    )

    secure = document["secure_measurement"]
    _check_keys(
        secure,
        (
            "allowed_flags",
            "confidence_min",
            "confidence_max",
            "require_mapping_consistency",
            "require_numeric_valid_z",
        ),
        "secure_measurement",
    )
    _check_int_list(secure["allowed_flags"], "secure_measurement.allowed_flags", SECURE_FLAGS)
    _check_int(secure, "confidence_min", "secure_measurement", 95)
    _check_int(secure, "confidence_max", "secure_measurement", 100)
    _check_bool(secure, "require_mapping_consistency", "secure_measurement", True)
    _check_bool(secure, "require_numeric_valid_z", "secure_measurement", True)

    preferred = document["preferred_reported_z"]
    _check_keys(
        preferred,
        (
            "candidate_surface",
            "candidate_predicate",
            "confidence_domain",
            "tie_break",
            "value_source",
        ),
        "preferred_reported_z",
    )
    _check_str(preferred, "candidate_surface", "preferred_reported_z", "unique")
    _check_str(preferred, "candidate_predicate", "preferred_reported_z", "numeric_valid")
    domain = preferred["confidence_domain"]
    if (
        not isinstance(domain, list)
        or len(domain) != 2
        or not all(_is_int(item) for item in domain)
        or domain != [0, 100]
    ):
        raise PolicyError(
            f"preferred_reported_z.confidence_domain: expected [0, 100], got {domain!r}"
        )
    _check_str(preferred, "tie_break", "preferred_reported_z", "ascending_id_specz")
    _check_str(preferred, "value_source", "preferred_reported_z", "copy_selected_row")

    conflict = document["conflict"]
    _check_keys(
        conflict,
        (
            "metric",
            "threshold",
            "agreement_is_equality_or_within_threshold",
            "veto_flags",
            "audit_flags",
            "minimum_entries_to_assess",
        ),
        "conflict",
    )
    _check_str(conflict, "metric", "conflict", "absolute_difference")
    threshold = conflict["threshold"]
    if not _is_float(threshold) or not threshold > 0.0:
        raise PolicyError(
            f"conflict.threshold: expected positive float, got {threshold!r}"
        )
    _check_bool(
        conflict,
        "agreement_is_equality_or_within_threshold",
        "conflict",
        True,
    )
    _check_str_list(
        conflict["veto_flags"],
        "conflict.veto_flags",
        ("unique_numeric_conflict", "secure_all_conflict"),
    )
    _check_str_list(
        conflict["audit_flags"], "conflict.audit_flags", CONFLICT_FLAGS
    )
    _check_int(conflict, "minimum_entries_to_assess", "conflict", 2)

    classification = document["classification"]
    _check_keys(
        classification,
        (
            "photometric_type_relation",
            "photometric_type_column",
            "galaxy_type",
            "stellar_type",
            "qso_type",
            "stellar_type_vetoes_secure_use",
            "broad_line_flags",
            "broad_line_predicate",
            "photometric_qso_type",
        ),
        "classification",
    )
    _check_str(classification, "photometric_type_relation", "classification", "lephare")
    _check_str(classification, "photometric_type_column", "classification", "type")
    _check_int(classification, "galaxy_type", "classification", 0)
    _check_int(classification, "stellar_type", "classification", 1)
    _check_int(classification, "qso_type", "classification", 2)
    _check_bool(
        classification, "stellar_type_vetoes_secure_use", "classification", True
    )
    _check_int_list(
        classification["broad_line_flags"],
        "classification.broad_line_flags",
        BROAD_LINE_FLAGS,
    )
    _check_str(
        classification,
        "broad_line_predicate",
        "classification",
        "any_numeric_valid_all_measurement",
    )
    _check_int(classification, "photometric_qso_type", "classification", 2)

    eligibility = document["eligibility"]
    _check_keys(
        eligibility,
        ("primary_galaxy", "separate_validation", "mutually_exclusive"),
        "eligibility",
    )
    primary = eligibility["primary_galaxy"]
    _check_keys(
        primary,
        (
            "requires_resolved_association",
            "requires_secure_preferred_unique_entry",
            "requires_neither_veto_conflict",
            "requires_photometric_type",
            "requires_no_broad_line_evidence",
            "requires_valid_split_assignment",
        ),
        "eligibility.primary_galaxy",
    )
    for key in (
        "requires_resolved_association",
        "requires_secure_preferred_unique_entry",
        "requires_neither_veto_conflict",
        "requires_no_broad_line_evidence",
        "requires_valid_split_assignment",
    ):
        _check_bool(primary, key, "eligibility.primary_galaxy", True)
    _check_int(
        primary, "requires_photometric_type", "eligibility.primary_galaxy", 0
    )
    separate = eligibility["separate_validation"]
    _check_keys(
        separate,
        (
            "requires_resolved_association",
            "requires_secure_preferred_unique_entry",
            "requires_neither_veto_conflict",
            "requires_valid_split_assignment",
            "allowed_photometric_types",
            "requires_broad_line_or_photometric_qso",
        ),
        "eligibility.separate_validation",
    )
    for key in (
        "requires_resolved_association",
        "requires_secure_preferred_unique_entry",
        "requires_neither_veto_conflict",
        "requires_valid_split_assignment",
        "requires_broad_line_or_photometric_qso",
    ):
        _check_bool(separate, key, "eligibility.separate_validation", True)
    _check_int_list(
        separate["allowed_photometric_types"],
        "eligibility.separate_validation.allowed_photometric_types",
        (0, 2),
    )
    _check_bool(eligibility, "mutually_exclusive", "eligibility", True)

    splits = document["splits"]
    _check_keys(
        splits,
        (
            "salt",
            "hash_algorithm",
            "encoding",
            "trailing_newline",
            "sort_key",
            "valid_tile_domain",
            "holdout_count",
            "validation_count",
            "development_count",
            "unassigned_label",
            "rebalancing_prohibited",
        ),
        "splits",
    )
    _check_str(splits, "salt", "splits", "cosmos2025-p2r05-spatial-v1")
    _check_str(splits, "hash_algorithm", "splits", "sha256")
    _check_str(splits, "encoding", "splits", "utf-8")
    _check_bool(splits, "trailing_newline", "splits", False)
    _check_str(splits, "sort_key", "splits", "digest_hex_then_tile")
    _check_str_list(
        splits["valid_tile_domain"], "splits.valid_tile_domain", VALID_TILE_DOMAIN
    )
    _check_int(splits, "holdout_count", "splits", 4)
    _check_int(splits, "validation_count", "splits", 4)
    _check_int(splits, "development_count", "splits", 12)
    _check_str(splits, "unassigned_label", "splits", "unassigned")
    _check_bool(splits, "rebalancing_prohibited", "splits", True)

    diagnostics = document["diagnostics"]
    _check_keys(
        diagnostics,
        (
            "magnitude_band",
            "color_blue_band",
            "color_red_band",
            "color_display_domain",
            "color_not_evaluated_label",
        ),
        "diagnostics",
    )
    _check_str(diagnostics, "magnitude_band", "diagnostics", "mag_auto_f444w")
    _check_str(diagnostics, "color_blue_band", "diagnostics", "mag_auto_f150w")
    _check_str(diagnostics, "color_red_band", "diagnostics", "mag_auto_f277w")
    color_domain = diagnostics["color_display_domain"]
    if (
        not isinstance(color_domain, list)
        or len(color_domain) != 2
        or not all(_is_float(item) for item in color_domain)
        or color_domain != [-10.0, 50.0]
    ):
        raise PolicyError(
            f"diagnostics.color_display_domain: expected [-10.0, 50.0], got {color_domain!r}"
        )
    _check_str(
        diagnostics,
        "color_not_evaluated_label",
        "diagnostics",
        "color_not_evaluated_display_domain",
    )

    sensitivity = document["sensitivity"]
    _check_keys(
        sensitivity,
        ("preserve_baseline_ordering", "share_frozen_partitions", "variants"),
        "sensitivity",
    )
    _check_bool(sensitivity, "preserve_baseline_ordering", "sensitivity", True)
    _check_bool(sensitivity, "share_frozen_partitions", "sensitivity", True)
    variants = sensitivity["variants"]
    if not isinstance(variants, list) or len(variants) != 3:
        raise PolicyError(
            f"sensitivity.variants: expected exactly three variants, got {variants!r}"
        )
    expected_variant_values = {
        "min_confidence_97": {"dimension": "confidence_min", "confidence_min": 97},
        "abs_threshold_0p001": {"dimension": "conflict_threshold", "threshold": 0.001},
        "normalized_0p005": {
            "dimension": "normalized_conflict_threshold",
            "normalized_threshold": 0.005,
        },
    }
    for variant in variants:
        if not isinstance(variant, dict) or "name" not in variant:
            raise PolicyError(f"sensitivity.variants: malformed variant {variant!r}")
        name = variant["name"]
        if name not in expected_variant_values:
            raise PolicyError(
                f"sensitivity.variants: unexpected variant name {name!r}; "
                f"expected {list(SENSITIVITY_VARIANT_NAMES)}"
            )
        expected_fields = {"name": name, **expected_variant_values[name]}
        if dict(variant) != expected_fields:
            raise PolicyError(
                f"sensitivity.variants[{name}]: expected {expected_fields}, got {variant!r}"
            )
    names = [variant["name"] for variant in variants]
    if sorted(names) != sorted(SENSITIVITY_VARIANT_NAMES):
        raise PolicyError(
            f"sensitivity.variants: expected all of {SENSITIVITY_VARIANT_NAMES}, got {names!r}"
        )

    upstream = document["upstream_report"]
    _check_keys(upstream, ("transmission", "renumbering_status"), "upstream_report")
    _check_str(upstream, "transmission", "upstream_report", "prohibited")
    _check_str(
        upstream, "renumbering_status", "upstream_report", "hypothesis_unconfirmed"
    )

    adoption = document["adoption"]
    _check_keys(adoption, ("product_state", "consumer_alias_prohibited"), "adoption")
    _check_str(adoption, "product_state", "adoption", "pending_scientific_adoption")
    _check_bool(adoption, "consumer_alias_prohibited", "adoption", True)

    return document


def load_frozen_policy(path: Path | None = None) -> Mapping[str, Any]:
    """Load and validate the frozen policy file, returning a read-only view.

    The path parameter exists for tests exercising validation failures; the
    executed build always reads the tracked default. Returns a
    ``MappingProxyType`` so no caller can mutate science policy in memory.
    """
    resolved = path if path is not None else DEFAULT_POLICY_PATH
    try:
        document = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PolicyError(f"policy file missing: {resolved}") from error
    except yaml.YAMLError as error:
        raise PolicyError(f"policy file is not valid YAML: {error}") from error
    validated = _validate(document)
    return MappingProxyType(validated)


def policy_semantic_digest(path: Path | None = None) -> str:
    """SHA-256 over the exact policy bytes, separating semantics from storage."""
    resolved = path if path is not None else DEFAULT_POLICY_PATH
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def flag_expected_confidence(policy: Mapping[str, Any], flag: int) -> int | None:
    """Expected confidence for a recognized measured flag, else ``None``.

    Implements the P-02 mapping: the base-flag table for flags 1-9, and the
    same table after subtracting the broad-line offset for flags 11-19.
    Flags 0/10 do not denote a measured redshift; unrecognized values are
    unclassified and return ``None``.
    """
    quality = policy["quality"]
    base = {int(key): int(value) for key, value in quality["base_flag_confidence"].items()}
    offset = int(quality["broad_line_offset"])
    non_measured = set(int(value) for value in quality["non_measured_flags"])
    recognized = set(int(value) for value in quality["recognized_measured_flags"])
    if flag in non_measured or flag not in recognized:
        return None
    return base.get(flag, base.get(flag - offset))
