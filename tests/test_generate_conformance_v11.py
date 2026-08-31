#!/usr/bin/env python3
"""
Script Name  : test_generate_conformance_v11.py
Description  : Test generated ETL v2 dictionary conformance cases
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Requires the Gate 3.10 generator to emit one explicit, reviewable case for
every sealed dictionary row without hand-enumerating the mirror boundary.

Usage
-----
    pytest tests/test_generate_conformance_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import importlib.util
import json
import sys
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pytest
import yaml


# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "generate_conformance_v11.py"
SCHEMA_MODULE_PATH = REPO_ROOT / "src" / "etl" / "generate_schema_v11.py"
DICTIONARY_PATH = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"


# =============================================================================
# Test utilities
# =============================================================================


def _module():
    """Load production after test start so a missing generator is observable."""
    assert MODULE_PATH.exists(), "Gate 3.10 conformance generator is missing"
    spec = importlib.util.spec_from_file_location(
        "generate_conformance_v11", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows() -> list[dict[str, str]]:
    """Read sealed rows independently of production generation helpers."""
    with DICTIONARY_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _schema_module():
    """Load the separately sealed Gate 3.6 schema contract."""
    spec = importlib.util.spec_from_file_location(
        "generate_schema_v11_for_conformance_test", SCHEMA_MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# =============================================================================
# Generated case boundary
# =============================================================================


def test_generator_emits_one_case_per_sealed_dictionary_row() -> None:
    """Dropping, duplicating, or misclassifying any dictionary row must fail."""
    module = _module()
    cases = module.generate_cases(_rows())

    assert len(cases) == 1_416
    assert len({case["case_id"] for case in cases}) == 1_416
    assert Counter(case["case_group"] for case in cases) == {
        "master_native": 1_349,
        "supplement_native": 22,
        "specz_native": 32,
        "metadata": 13,
    }
    assert Counter(case["column_origin"] for case in cases) == {
        "source_native": 1_403,
        "source_row_metadata": 7,
        "id_injected": 6,
    }


def test_each_case_carries_exact_schema_comment_and_array_contract() -> None:
    """Wrong type, comment, array length, name, or definition must be visible."""
    module = _module()
    schema_module = _schema_module()
    rows = _rows()
    cases = module.generate_cases(rows)
    comments = {
        (item.table, item.column): item.text
        for item in schema_module.column_comment_contract(rows)
    }
    arrays = {
        (item.table, row["target_identifier"]): asdict(item)
        for item, row in zip(
            schema_module.array_check_contract(rows),
            (row for row in rows if row["target_type"].endswith("[]")),
            strict=True,
        )
    }

    assert sum(case["array_constraint_name"] is not None for case in cases) == 166
    for case, row in zip(cases, rows, strict=True):
        key = (row["target_table"], row["target_identifier"])
        expected_array = arrays.get(key)
        assert case["table"] == row["target_table"]
        assert case["column"] == row["target_identifier"]
        assert case["target_type"] == row["target_type"]
        assert case["column_origin"] == row["column_origin"]
        assert case["comment"] == comments[key]
        assert case["element_count"] == int(row["element_count"])
        assert case["array_constraint_name"] == (
            expected_array["name"] if expected_array else None
        )
        assert case["array_constraint_expression"] == (
            expected_array["expression"] if expected_array else None
        )


def test_each_case_carries_exact_value_source_contract() -> None:
    """Wrong source mapping, null facts, or expected population must be visible."""
    module = _module()
    rows = _rows()
    cases = module.generate_cases(rows)
    table_counts: dict[str, set[int]] = {}
    for row in rows:
        if row["profile_json"]:
            table_counts.setdefault(row["target_table"], set()).update(
                profile["row_count"]
                for profile in json.loads(row["profile_json"])["profiles"]
            )

    for case, row in zip(cases, rows, strict=True):
        expected_counts = table_counts[row["target_table"]]
        assert len(expected_counts) == 1
        assert case["source_family"] == row["source_family"]
        assert case["source_file"] == row["source_file"]
        assert case["source_locator"] == row["source_locator"]
        assert case["source_column"] == row["source_column"]
        assert case["source_type"] == row["source_type"]
        assert case["has_fits_mask"] is (row["has_fits_mask"] == "True")
        assert case["has_nan"] is (row["has_nan"] == "True")
        assert case["expected_source_rows"] == next(iter(expected_counts))


def test_generator_rejects_inconsistent_profile_row_counts() -> None:
    """Vector profiles with different populations must not become value cases."""
    module = _module()
    rows = _rows()
    vector_index = next(
        index
        for index, row in enumerate(rows)
        if len(json.loads(row["profile_json"])["profiles"]) > 1
    )
    changed = deepcopy(rows)
    profile = json.loads(changed[vector_index]["profile_json"])
    profile["profiles"][1]["row_count"] -= 1
    changed[vector_index]["profile_json"] = json.dumps(profile)

    with pytest.raises(ValueError, match="profile row-count mismatch"):
        module.generate_cases(changed)


def test_generated_module_is_explicit_importable_and_byte_checked(
    tmp_path: Path,
) -> None:
    """A stale or hand-edited generated case artifact must fail byte identity."""
    module = _module()
    rows = _rows()
    generated = module.generate_module(rows)
    namespace: dict[str, object] = {}
    exec(compile(generated, "conformance_cases_v11.py", "exec"), namespace)

    assert len(namespace["CASES"]) == 1_416
    assert namespace["CASE_COUNTS"] == {
        "master_native": 1_349,
        "supplement_native": 22,
        "specz_native": 32,
        "metadata": 13,
        "native_total": 1_403,
        "array": 166,
    }
    output = tmp_path / "conformance_cases_v11.py"
    module.write_or_check(rows, output, check=False)
    assert output.read_text(encoding="utf-8") == generated
    module.write_or_check(rows, output, check=True)
    output.write_text(generated + "# drift\n", encoding="utf-8")
    with pytest.raises(ValueError, match="generated conformance cases differ"):
        module.write_or_check(rows, output, check=True)


def test_generator_rejects_dictionary_boundary_and_duplicate_case_identity() -> None:
    """Removed, reordered, or duplicate identifiers must not produce cases."""
    module = _module()
    rows = _rows()
    with pytest.raises(ValueError, match="row count mismatch"):
        module.generate_cases(rows[:-1])

    duplicate = deepcopy(rows)
    duplicate[1]["target_identifier"] = duplicate[0]["target_identifier"]
    with pytest.raises(ValueError, match="duplicate target identifier"):
        module.generate_cases(duplicate)


def test_cli_resolves_configured_paths_and_checks_generated_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI must use configured paths and expose byte drift through --check."""
    module = _module()
    output = tmp_path / "cases.py"
    config = tmp_path / "paths.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "dictionary": {
                    "columns_v11": str(DICTIONARY_PATH),
                    "conformance_cases_v11": str(output),
                }
            }
        ),
        encoding="utf-8",
    )
    assert module.configured_paths(config) == (DICTIONARY_PATH, output)

    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--config", str(config)])
    module.main()
    monkeypatch.setattr(
        sys, "argv", [str(MODULE_PATH), "--config", str(config), "--check"]
    )
    module.main()
