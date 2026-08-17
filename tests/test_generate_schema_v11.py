#!/usr/bin/env python3
"""
Script Name  : test_generate_schema_v11.py
Description  : Test generated ETL v2 source-mirror DDL contracts
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises Gate 3.6 schema generation from the sealed dictionary and the
versioned provenance contract. Tests use the tracked dictionary as a sealed
input and controlled copies for byte-reproducibility mutations.

Usage
-----
    pytest tests/test_generate_schema_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import importlib.util
import re
import sys
from copy import deepcopy
from pathlib import Path

import pytest

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "generate_schema_v11.py"
DICTIONARY_PATH = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"
EXPECTED_TABLES = (
    "photometry_primary",
    "photometry_aper",
    "lephare",
    "cigale",
    "ml_morpho",
    "bulge_disk",
    "galight_morph",
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
    "specz_compilation",
)
EXPECTED_COUNTS = (288, 150, 45, 58, 152, 463, 206, 4, 14, 4, 32)


# =============================================================================
# Test utilities
# =============================================================================


def _module():
    """Load production only after a test starts so missing code is a RED failure."""
    assert MODULE_PATH.exists(), "Gate 3.6 DDL generator module is missing"
    spec = importlib.util.spec_from_file_location("generate_schema_v11", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows() -> list[dict[str, str]]:
    """Read the sealed dictionary independently of production helpers."""
    with DICTIONARY_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# =============================================================================
# Static generation contract
# =============================================================================


def test_table_boundary_column_order_and_type_passthrough() -> None:
    """Wrong tables, reordered columns, or remapped types must fail generation."""
    module = _module()
    rows = _rows()
    schema = module.build_schema_contract(rows)

    assert tuple(schema) == EXPECTED_TABLES
    assert tuple(len(schema[table]) for table in schema) == EXPECTED_COUNTS
    assert sum(map(len, schema.values())) == 1_416
    for table, contract_rows in schema.items():
        expected = [row for row in rows if row["target_table"] == table]
        assert [column.name for column in contract_rows] == [
            row["target_identifier"] for row in expected
        ]
        assert [column.sql_type for column in contract_rows] == [
            row["target_type"] for row in expected
        ]


def test_generated_sql_has_only_authorized_schema_and_tables() -> None:
    """Any analytical or extra infrastructure object must alter this boundary."""
    module = _module()
    sql = module.generate_sql(_rows())

    assert re.findall(r'^CREATE SCHEMA ("[^"]+");$', sql, re.MULTILINE) == ['"source"']
    assert re.findall(r'^CREATE TABLE "source"\."([^"]+)" \($', sql, re.MULTILINE) == [
        *EXPECTED_TABLES,
        "provenance",
    ]
    forbidden = (
        "CREATE VIEW",
        "CREATE MATERIALIZED VIEW",
        "CREATE FUNCTION",
        "CREATE TRIGGER",
        "CREATE SEQUENCE",
        '"analysis"',
        '"staging"',
    )
    assert not any(token in sql for token in forbidden)


def test_all_array_columns_have_nullable_safe_exact_length_checks() -> None:
    """A missing null, dimension, or cardinality clause must lose array coverage."""
    module = _module()
    rows = _rows()
    arrays = [row for row in rows if row["target_type"].endswith("[]")]
    assert len(arrays) == 166

    checks = module.array_check_contract(rows)
    assert len(checks) == 166
    for check, row in zip(checks, arrays, strict=True):
        quoted = module.quote_identifier(row["target_identifier"])
        assert quoted in check.expression
        assert f"{quoted} IS NULL OR" in check.expression
        assert f"array_ndims({quoted}) = 1" in check.expression
        assert f"cardinality({quoted}) = {row['element_count']}" in check.expression
        assert len(check.name.encode("utf-8")) <= 63
        assert re.fullmatch(r"[a-z_][a-z0-9_]*", check.name)
    assert len({check.name for check in checks}) == 166


def test_constraint_names_are_bounded_and_collision_resistant() -> None:
    """Long similar identifiers must not rely on PostgreSQL name truncation."""
    module = _module()
    first = module.constraint_name("array", "x" * 100, "column" + "y" * 100)
    second = module.constraint_name("array", "x" * 100, "column" + "y" * 99 + "z")
    assert first != second
    assert len(first.encode("utf-8")) <= 63
    assert len(second.encode("utf-8")) <= 63


def test_master_key_contract_is_exact_and_supplements_are_unconstrained() -> None:
    """Missing master keys or invented supplement keys must change the contract."""
    module = _module()
    constraints = module.table_constraint_contract(_rows())

    assert [
        (item.kind, item.columns) for item in constraints["photometry_primary"]
    ] == [
        ("primary_key", ("id",)),
        ("unique", ("source_row",)),
    ]
    for table in EXPECTED_TABLES[1:7]:
        assert [(item.kind, item.columns) for item in constraints[table]] == [
            ("primary_key", ("source_row",)),
            ("unique", ("id",)),
            ("foreign_key", ("id",)),
        ]
        assert constraints[table][-1].references == (
            "photometry_primary",
            ("id",),
        )
    for table in EXPECTED_TABLES[7:]:
        assert constraints[table] == ()


def test_provenance_contract_is_versioned_importable_and_fidelity_safe() -> None:
    """Field drift, weak digests, or loss of table identity must fail."""
    module = _module()
    contract = module.PROVENANCE_CONTRACT
    assert module.PROVENANCE_CONTRACT_VERSION == "1.0.0"
    assert tuple(field.name for field in contract) == (
        "table_name",
        "source_file",
        "source_path",
        "manifest_sha256",
        "observed_sha256",
        "source_rows",
        "loaded_rows",
        "load_timestamp",
        "manifest_ref",
        "manifest_ref_sha256",
        "catalog_version",
        "supplement_version",
        "notes",
    )
    assert contract[0].primary_key is True
    assert all(field.comment for field in contract)
    assert contract[3].sql_type == "text"
    assert contract[4].sql_type == "text"
    assert contract[9].sql_type == "text"
    assert "64" in contract[3].check_expression
    assert "64" in contract[4].check_expression
    assert "64" in contract[9].check_expression


def test_every_column_has_one_separated_provenance_aware_comment() -> None:
    """Omitted evidence sections or fake upstream prose must fail comment coverage."""
    module = _module()
    rows = _rows()
    comments = module.column_comment_contract(rows)

    assert len(comments) == 1_416
    assert len(module.PROVENANCE_CONTRACT) == 13
    assert (
        sum(
            line.startswith("COMMENT ON COLUMN ")
            for line in module.generate_sql(rows).splitlines()
        )
        == 1_429
    )
    undocumented = next(
        comment
        for row, comment in zip(rows, comments, strict=True)
        if row["description_status"] == "undocumented_upstream"
    )
    assert "Description status: undocumented_upstream" in undocumented.text
    assert "Description: [undocumented upstream]" in undocumented.text
    for heading in (
        "Description:",
        "Description provenance:",
        "Unit:",
        "Unit provenance:",
        "Semantic note:",
        "Semantic-note provenance:",
        "Null/profile facts:",
        "Documented sentinel evidence:",
        "Candidate observations:",
    ):
        assert heading in undocumented.text
    assert "retained source values" in undocumented.text
    assert "NULL rules" not in undocumented.text


def test_sql_literal_and_identifier_escaping_preserves_source_prose() -> None:
    """An apostrophe or quote must not break generated SQL serialization."""
    module = _module()
    assert module.quote_identifier('a"b') == '"a""b"'
    assert module.sql_literal("catalog's value") == "'catalog''s value'"
    rows = _rows()
    comments = module.column_comment_contract(rows)
    comment = next(
        item
        for row, item in zip(rows, comments, strict=True)
        if row["target_identifier"] == "survey"
        and row["target_table"] == "specz_compilation"
    )
    assert "survey'" in comment.text
    assert "survey''" in comment.sql


def test_write_check_is_byte_identical_and_rejects_hand_drift(tmp_path: Path) -> None:
    """A one-byte hand edit must make --check fail against fresh generation."""
    module = _module()
    output = tmp_path / "schema_v11.sql"
    rows = _rows()
    generated = module.generate_sql(rows)

    module.write_or_check(rows, output, check=False)
    assert output.read_bytes() == generated.encode("utf-8")
    module.write_or_check(rows, output, check=True)

    output.write_text(generated + "-- hand drift\n", encoding="utf-8")
    with pytest.raises(ValueError, match="generated SQL differs"):
        module.write_or_check(rows, output, check=True)


def test_removed_dictionary_row_fails_full_sealed_conformance() -> None:
    """A valid-looking schema from 1,415 rows must fail the sealed comparison."""
    module = _module()
    rows = _rows()
    mutated = deepcopy(rows[:-1])
    with pytest.raises(ValueError, match="sealed dictionary row count"):
        module.build_schema_contract(mutated)
