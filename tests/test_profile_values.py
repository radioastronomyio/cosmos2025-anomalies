#!/usr/bin/env python3
"""
Script Name  : test_profile_values.py
Description  : Test Gate 3.3 value and sentinel profiling contracts
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Gate 3.3 tests for numeric and typed profiles, independent FITS-mask and NaN
states, per-index vector behavior, candidate sentinel selection, canonical
JSON, exact documented evidence, and the generated live dictionary artifact.

Usage
-----
    pytest tests/test_profile_values.py -v

Examples
--------
    pytest tests/test_profile_values.py::test_numeric_profile_separates_masks_nans_and_finite_values -v
        Runs the scalar null-state and exact-frequency contract.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import importlib
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest


# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


# =============================================================================
# Test utilities
# =============================================================================


def profiling_module():
    """Import the production profiler after asserting that it exists."""
    module_name = "src.etl.profile_values"
    assert importlib.util.find_spec(module_name) is not None, (
        "Gate 3.3 profiler module must exist"
    )
    return importlib.import_module(module_name)


# =============================================================================
# Numeric profile tests
# =============================================================================


def test_numeric_profile_separates_masks_nans_and_finite_values() -> None:
    """Merging masks/NaNs or nulling finite sentinels must change this result."""
    profiler = profiling_module()
    values = np.array([99.0, 99.0, np.nan, np.inf, -999.0, 5.0, 5.0, 7.0])
    mask = np.array([False, False, False, False, False, False, True, False])

    profile = profiler.profile_numeric(values, mask=mask, vector_index=None)

    assert profile == {
        "finite_max": 99.0,
        "finite_min": -999.0,
        "fits_mask_count": 1,
        "fits_mask_fraction": 0.125,
        "index": None,
        "nan_count": 1,
        "nan_fraction": 0.125,
        "non_null_count": 6,
        "non_null_fraction": 0.75,
        "row_count": 8,
        "top_values": [
            {"count": 2, "value": 99.0},
            {"count": 1, "value": -999.0},
            {"count": 1, "value": 5.0},
        ],
    }


def test_numeric_vectors_are_profiled_independently_by_index() -> None:
    """Flattening a vector must fail distinct per-index counts and null states."""
    profiler = profiling_module()
    values = np.array(
        [
            [1.0, 99.0],
            [np.nan, 99.0],
            [3.0, 5.0],
            [4.0, 5.0],
        ]
    )
    mask = np.array(
        [
            [False, False],
            [False, False],
            [True, False],
            [False, False],
        ]
    )

    profiles = profiler.profile_numeric_array(values, mask=mask)

    assert [profile["index"] for profile in profiles] == [0, 1]
    assert profiles[0]["fits_mask_count"] == 1
    assert profiles[0]["nan_count"] == 1
    assert profiles[0]["non_null_count"] == 2
    assert profiles[0]["top_values"] == [
        {"count": 1, "value": 1.0},
        {"count": 1, "value": 4.0},
    ]
    assert profiles[1]["fits_mask_count"] == 0
    assert profiles[1]["nan_count"] == 0
    assert profiles[1]["top_values"] == [
        {"count": 2, "value": 5.0},
        {"count": 2, "value": 99.0},
    ]


# =============================================================================
# Candidate and evidence tests
# =============================================================================


def test_candidate_rule_uses_exact_pattern_and_non_null_denominator() -> None:
    """Wrong rounding, denominator, or pattern logic must change boundaries."""
    profiler = profiling_module()
    entries = profiler.candidate_sentinels(
        {
            -999: 2_000,
            -99: 1_999,
            99: 2_000,
            100: 50_000,
            999: 2_001,
        },
        non_null_count=2_000_000,
        vector_index=None,
        documented_sentinel_values={-999},
        documented_valid_values={99},
    )

    assert entries == [
        {
            "count": 2_001,
            "index": None,
            "non_null_fraction": 0.0010005,
            "rule_version": "cosmos_v11_candidate_sentinel_v1",
            "value": 999,
        }
    ]


def test_candidate_rule_accepts_exact_absolute_floor_boundary_per_index() -> None:
    """At-threshold candidates pass independently for each vector index."""
    profiler = profiling_module()
    below = profiler.candidate_sentinels(
        {-99: 999, 99: 999},
        non_null_count=1_000_000,
        vector_index=2,
        documented_sentinel_values=set(),
        documented_valid_values=set(),
    )
    at_threshold = profiler.candidate_sentinels(
        {-99: 1_000, 99: 1_000},
        non_null_count=1_000_000,
        vector_index=2,
        documented_sentinel_values=set(),
        documented_valid_values=set(),
    )

    assert below == []
    assert at_threshold == [
        {
            "count": 1_000,
            "index": 2,
            "non_null_fraction": 0.001,
            "rule_version": "cosmos_v11_candidate_sentinel_v1",
            "value": -99,
        },
        {
            "count": 1_000,
            "index": 2,
            "non_null_fraction": 0.001,
            "rule_version": "cosmos_v11_candidate_sentinel_v1",
            "value": 99,
        },
    ]


def test_candidate_pattern_keeps_large_integer_arithmetic_exact() -> None:
    """Integer candidates above float precision must retain their exact value."""
    profiler = profiling_module()
    exact_large_integer = 999_999_999_999_999_999

    entries = profiler.candidate_sentinels(
        {exact_large_integer: 1_000},
        non_null_count=1_000,
        vector_index=None,
        documented_sentinel_values=set(),
        documented_valid_values=set(),
    )

    assert entries == [
        {
            "count": 1_000,
            "index": None,
            "non_null_fraction": 1.0,
            "rule_version": "cosmos_v11_candidate_sentinel_v1",
            "value": exact_large_integer,
        }
    ]


def test_canonical_json_is_compact_stable_and_rejects_nonfinite_tokens() -> None:
    """Unstable keys or permissive NaN/Infinity JSON must fail serialization."""
    profiler = profiling_module()
    payload = [
        {
            "value": -99,
            "rule_version": "cosmos_v11_candidate_sentinel_v1",
            "non_null_fraction": 0.001,
            "index": None,
            "count": 1_000,
        }
    ]
    assert profiler.canonical_json(payload) == (
        '[{"count":1000,"index":null,"non_null_fraction":0.001,'
        '"rule_version":"cosmos_v11_candidate_sentinel_v1","value":-99}]'
    )
    with pytest.raises(ValueError, match="Out of range float values"):
        profiler.canonical_json({"value": np.nan})
    with pytest.raises(ValueError, match="Out of range float values"):
        profiler.canonical_json({"value": np.inf})


def test_documented_sentinel_requires_exact_supporting_numeric_token() -> None:
    """Unsupported assertions must not borrow unrelated sentinel evidence."""
    profiler = profiling_module()
    evidence = (
        "Unique ID of the source corresponding to the Id_specz of the Khostovan "
        "et al. (2025) spec-z compilation. -999 if no specz match"
    )
    source_hash = "3e7dde1db9d541ce8593b12cbf0690130422e746ce7db78cc238f27ed724366b"

    profiler.validate_documented_sentinel_evidence(
        [-999],
        evidence_text=evidence,
        source="/configured/upstream/descriptions.txt",
        locator="section 1, line 36, Description",
        source_sha256=source_hash,
    )
    with pytest.raises(ValueError, match="Unsupported documented sentinel value"):
        profiler.validate_documented_sentinel_evidence(
            [-99],
            evidence_text=evidence,
            source="/configured/upstream/descriptions.txt",
            locator="section 1, line 36, Description",
            source_sha256=source_hash,
        )
    with pytest.raises(ValueError, match="provenance incomplete"):
        profiler.validate_documented_sentinel_evidence(
            [-999],
            evidence_text=evidence,
            source="",
            locator="section 1, line 36, Description",
            source_sha256=source_hash,
        )


# =============================================================================
# Typed payload and row-enrichment tests
# =============================================================================


def test_text_and_boolean_profiles_preserve_exact_typed_values() -> None:
    """String coercion or nondeterministic ties must change typed top values."""
    profiler = profiling_module()
    text = profiler.profile_non_numeric(
        np.array(["B", "A", "B", "A", "C"]),
        mask=np.array([False, False, False, False, True]),
        vector_index=None,
    )
    boolean = profiler.profile_non_numeric(
        np.array([True, False, True, False, True]),
        mask=None,
        vector_index=None,
    )

    assert text == {
        "fits_mask_count": 1,
        "fits_mask_fraction": 0.2,
        "index": None,
        "non_null_count": 4,
        "non_null_fraction": 0.8,
        "row_count": 5,
        "top_values": [
            {"count": 2, "value": "A"},
            {"count": 2, "value": "B"},
        ],
    }
    assert boolean["top_values"] == [
        {"count": 3, "value": True},
        {"count": 2, "value": False},
    ]


def test_profile_fields_keep_documented_and_candidate_values_finite() -> None:
    """Profiling must record sentinel observations without nulling source values."""
    profiler = profiling_module()
    evidence = (
        "Unique ID of the source corresponding to the Id_specz of the Khostovan "
        "et al. (2025) spec-z compilation. -999 if no specz match"
    )
    row = {
        "target_table": "photometry_primary",
        "source_column": "id_specz_khostovan25",
        "target_type": "bigint",
        "element_count": 1,
        "description_text": evidence,
        "description_source": "/configured/upstream/descriptions.txt",
        "description_locator": "section 1, line 36, Description",
        "description_source_sha256": (
            "3e7dde1db9d541ce8593b12cbf0690130422e746ce7db78cc238f27ed724366b"
        ),
    }
    values = np.concatenate(
        [
            np.full(10, -999, dtype=np.int64),
            np.full(1_000, 999, dtype=np.int64),
            np.array([1], dtype=np.int64),
        ]
    )

    fields = profiler.build_profile_fields(row, values, fits_null=None)
    payload = json.loads(fields["profile_json"])

    assert fields["documented_sentinel_values_json"] == "[-999]"
    assert fields["documented_sentinel_evidence_text"] == evidence
    assert fields["candidate_sentinel_values_json"] == (
        '[{"count":1000,"index":null,"non_null_fraction":0.9891196834817013,'
        '"rule_version":"cosmos_v11_candidate_sentinel_v1","value":999}]'
    )
    assert payload["profiles"][0]["finite_min"] == -999
    assert payload["profiles"][0]["non_null_count"] == 1_011
    assert fields["has_fits_mask"] is False
    assert fields["has_nan"] is False


def test_declared_fits_null_is_masked_without_name_or_value_guessing() -> None:
    """Only declared FITS TNULL metadata may mask a finite integer encoding."""
    profiler = profiling_module()
    row = {
        "target_table": "ml_morpho",
        "source_column": "morph_flag_f277w",
        "target_type": "bigint",
        "element_count": 1,
        "description_text": "Morphological classification flag",
        "description_source": "/configured/upstream/descriptions.txt",
        "description_locator": "section 5, line 721, Description",
        "description_source_sha256": "a" * 64,
    }
    values = np.array([999_999, 999_999, 3], dtype=np.int64)

    declared = profiler.build_profile_fields(row, values, fits_null=999_999)
    undeclared = profiler.build_profile_fields(row, values, fits_null=None)

    declared_payload = json.loads(declared["profile_json"])["profiles"][0]
    undeclared_payload = json.loads(undeclared["profile_json"])["profiles"][0]
    assert declared["has_fits_mask"] is True
    assert declared_payload["fits_mask_count"] == 2
    assert declared_payload["finite_max"] == 3
    assert undeclared["has_fits_mask"] is False
    assert undeclared_payload["finite_max"] == 999_999


def test_metadata_profile_fields_use_explicit_not_applicable_convention() -> None:
    """Project metadata rows must not receive invented live observations."""
    profiler = profiling_module()
    assert profiler.empty_profile_fields() == {
        "profile_json": "",
        "has_fits_mask": False,
        "has_nan": False,
        "documented_sentinel_values_json": "[]",
        "documented_sentinel_evidence_text": "",
        "documented_sentinel_source": "",
        "documented_sentinel_locator": "",
        "documented_sentinel_source_sha256": "",
        "candidate_sentinel_values_json": "[]",
    }


# =============================================================================
# Profile validation and tracked artifact tests
# =============================================================================


def test_profile_validator_rejects_vector_flattening_and_candidate_drift() -> None:
    """A flattened vector or incomplete candidate entry must halt validation."""
    profiler = profiling_module()
    row = {
        "target_table": "photometry_primary",
        "source_column": "flux_aper_f115w",
        "target_type": "double precision[]",
        "element_count": 2,
        **profiler.empty_profile_fields(),
    }
    row.update(
        {
            "profile_json": profiler.canonical_json(
                {
                    "kind": "numeric",
                    "profiles": [
                        {
                            "finite_max": 1.0,
                            "finite_min": 1.0,
                            "fits_mask_count": 0,
                            "fits_mask_fraction": 0.0,
                            "index": 0,
                            "nan_count": 0,
                            "nan_fraction": 0.0,
                            "non_null_count": 1,
                            "non_null_fraction": 1.0,
                            "row_count": 1,
                            "top_values": [{"count": 1, "value": 1.0}],
                        },
                        {
                            "finite_max": 99.0,
                            "finite_min": 99.0,
                            "fits_mask_count": 0,
                            "fits_mask_fraction": 0.0,
                            "index": 1,
                            "nan_count": 0,
                            "nan_fraction": 0.0,
                            "non_null_count": 1_000_000,
                            "non_null_fraction": 1.0,
                            "row_count": 1_000_000,
                            "top_values": [{"count": 1_000, "value": 99.0}],
                        },
                    ],
                }
            ),
            "candidate_sentinel_values_json": profiler.canonical_json(
                [
                    {
                        "count": 1_000,
                        "index": 1,
                        "non_null_fraction": 0.001,
                        "rule_version": "cosmos_v11_candidate_sentinel_v1",
                        "value": 99.0,
                    }
                ]
            ),
        }
    )
    profiler.validate_profile_row(row)

    flattened = deepcopy(row)
    flattened_payload = json.loads(flattened["profile_json"])
    flattened_payload["profiles"] = flattened_payload["profiles"][:1]
    flattened["profile_json"] = profiler.canonical_json(flattened_payload)
    with pytest.raises(ValueError, match="Vector profile count mismatch"):
        profiler.validate_profile_row(flattened)

    incomplete = deepcopy(row)
    candidate = json.loads(incomplete["candidate_sentinel_values_json"])[0]
    del candidate["rule_version"]
    incomplete["candidate_sentinel_values_json"] = profiler.canonical_json([candidate])
    with pytest.raises(ValueError, match="Candidate entry schema mismatch"):
        profiler.validate_profile_row(incomplete)

    wrong_kind = deepcopy(row)
    wrong_kind_payload = json.loads(wrong_kind["profile_json"])
    wrong_kind_payload["kind"] = "text"
    wrong_kind["profile_json"] = profiler.canonical_json(wrong_kind_payload)
    with pytest.raises(ValueError, match="Profile kind mismatch"):
        profiler.validate_profile_row(wrong_kind)

    wrong_nan_summary = deepcopy(row)
    wrong_nan_summary["has_nan"] = True
    with pytest.raises(ValueError, match="NaN summary mismatch"):
        profiler.validate_profile_row(wrong_nan_summary)


def test_tracked_dictionary_has_complete_gate_33_profiles() -> None:
    """Missing native profiles, metadata invention, or ragged CSV must fail."""
    profiler = profiling_module()
    rows = profiler.read_tracked_dictionary()
    dictionary_path = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"
    raw_records = list(csv.reader(dictionary_path.read_text().splitlines()))

    assert len(rows) == 1_416
    assert len(raw_records) == 1_417
    assert {len(record) for record in raw_records} == {32}
    assert list(rows[0])[-9:] == [
        "profile_json",
        "has_fits_mask",
        "has_nan",
        "documented_sentinel_values_json",
        "documented_sentinel_evidence_text",
        "documented_sentinel_source",
        "documented_sentinel_locator",
        "documented_sentinel_source_sha256",
        "candidate_sentinel_values_json",
    ]
    evidence = profiler.validate_profiled_rows(rows)
    assert evidence["native_rows_profiled"] == 1_403
    assert evidence["source_tables"] == 11
    assert evidence["scalar_fields"] == 1_237
    assert evidence["vector_fields"] == 166
    assert evidence["vector_indices"] == 830
    assert evidence["metadata_rows_not_applicable"] == 13


def test_direct_profiler_cli_resolves_repository_imports() -> None:
    """Direct script execution must not depend on pytest's repository path."""
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "src" / "etl" / "profile_values.py"),
            "--help",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--check" in result.stdout


def test_candidate_report_is_generated_from_every_dictionary_observation() -> None:
    """Omitted candidates or collapsed null states must change report output."""
    profiler = profiling_module()
    rows = profiler.read_tracked_dictionary()
    evidence = profiler.validate_profiled_rows(rows)

    report = profiler.render_candidate_report(rows, evidence)

    assert report.startswith('<!--\n---\ntitle: "COSMOS-Web v1.1 Sentinel Candidates"')
    assert "## 3. FITS Masks" in report
    assert "## 4. NaNs" in report
    assert "## 5. Documented Sentinels" in report
    assert "## 6. Conservative Candidate Sentinels" in report
    assert "| Rule trigger | Rule version |" in report
    assert "`abs(value) = 10^k - 1` for integer `k >= 2`" in report
    assert "`count >= 1000` and `count * 1000 >= non_null_count`" in report
    assert "cosmos_v11_candidate_sentinel_v1" in report
    assert (
        report.count("| `cosmos_v11_candidate_sentinel_v1` |")
        == evidence["candidate_entries"]
    )
    assert (
        report.count(
            "| `abs(value)=10^k-1; count>=1000; "
            "count*1000>=non_null_count` | `cosmos_v11_candidate_sentinel_v1` |"
        )
        == evidence["candidate_entries"]
    )
    assert "No source value was changed, nulled, filtered, or relabeled" in report
