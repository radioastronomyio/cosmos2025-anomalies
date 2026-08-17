#!/usr/bin/env python3
"""
Script Name  : test_load_dictionary.py
Description  : Test the v1.1 unified load-dictionary builder and validator
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Gate 3.1 tests for deterministic PostgreSQL identifiers, lossless FITS
type mapping, validator diagnostics, and reconciliation of the generated
dictionary against the configured live source structures. Tests use only
read-only source access and write temporary or repository output files.

Usage
-----
    pytest tests/test_load_dictionary.py -v

Examples
--------
    pytest tests/test_load_dictionary.py::test_identifier_rules_prevent_invalid_postgresql_names -v
        Runs the focused identifier mutation checks.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.etl import load_dictionary  # noqa: E402


# =============================================================================
# Identifier tests
# =============================================================================


def test_identifier_rules_prevent_invalid_postgresql_names() -> None:
    """Case, punctuation, leading digits, and reserved words normalize."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from src.etl.load_dictionary import sanitize_identifier; "
                "print(sanitize_identifier('Flux.F444W-error')); "
                "print(sanitize_identifier('1MAG')); "
                "print(sanitize_identifier('select')); "
                "print(sanitize_identifier('system_user'))"
            ),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "flux_f444w_error",
        "c_1mag",
        "c_select",
        "c_system_user",
    ]


# =============================================================================
# Type-mapping tests
# =============================================================================


def test_fits_mapping_prevents_precision_loss_and_vector_flattening() -> None:
    """Every authorized scalar, string, and vector TFORM maps literally."""
    expected = {
        "D": ("double precision", 1),
        "E": ("real", 1),
        "K": ("bigint", 1),
        "J": ("integer", 1),
        "I": ("smallint", 1),
        "L": ("boolean", 1),
        "3A": ("text", 3),
        "20A": ("text", 20),
        "5D": ("double precision[]", 5),
        "5E": ("real[]", 5),
    }
    mapping = getattr(load_dictionary, "fits_type_mapping", None)
    assert callable(mapping), "load dictionary must expose FITS type mapping"
    assert {source: mapping(source) for source in expected} == expected


# =============================================================================
# Validator mutation tests
# =============================================================================


def native_row(**updates: str | int) -> dict[str, str | int]:
    """Return one independently specified valid scalar FITS dictionary row."""
    row: dict[str, str | int] = {
        "source_family": "master_catalog",
        "source_file": "/read-only/example.fits",
        "source_locator": "HDU 1 [EXAMPLE]",
        "source_column": "Flux",
        "source_type": "D",
        "element_count": 1,
        "target_table": "example",
        "target_identifier": "flux",
        "target_type": "double precision",
        "column_origin": "source_native",
    }
    row.update(updates)
    return row


def test_wrong_d_mapping_fails_with_type_mapping_diagnostic() -> None:
    """Mutating D from double precision to real must halt validation."""
    validator = getattr(load_dictionary, "validate_dictionary", None)
    assert callable(validator), "load dictionary must expose its validator"
    with pytest.raises(ValueError, match="Type mapping mismatch"):
        validator([native_row(target_type="real")])


def test_identifier_collision_fails_with_collision_diagnostic() -> None:
    """Two distinct source names may not normalize to one table identifier."""
    rows = [
        native_row(source_column="Flux-A", target_identifier="flux_a"),
        native_row(source_column="Flux A", target_identifier="flux_a"),
    ]
    with pytest.raises(ValueError, match="Identifier collision"):
        load_dictionary.validate_dictionary(rows)


def test_overlength_identifier_fails_with_length_diagnostic() -> None:
    """A 64-byte identifier must halt before PostgreSQL can truncate it."""
    long_identifier = "a" * 64
    with pytest.raises(ValueError, match="Identifier over 63 bytes"):
        load_dictionary.validate_dictionary(
            [
                native_row(
                    source_column=long_identifier,
                    target_identifier=long_identifier,
                )
            ]
        )


# =============================================================================
# Live source reconciliation tests
# =============================================================================


def test_live_dictionary_uses_exact_declared_target_table_set() -> None:
    """A source-like table alias must not replace a declared mirror table."""
    rows, _ = load_dictionary.build_dictionary(
        REPO_ROOT / "configs" / "data_paths.yaml"
    )
    assert {str(row["target_table"]) for row in rows} == {
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
    }


def test_live_inventory_reconciles_every_source_field_and_metadata_row() -> None:
    """Dropping any configured source table or metadata row changes literals."""
    builder = getattr(load_dictionary, "build_dictionary", None)
    assert callable(builder), "load dictionary must expose its live builder"
    rows, evidence = builder(REPO_ROOT / "configs" / "data_paths.yaml")

    assert evidence["native_counts"] == {
        "photometry_primary": 287,
        "lephare": 43,
        "photometry_aper": 148,
        "cigale": 56,
        "ml_morpho": 150,
        "bulge_disk": 461,
        "galight_morph": 204,
        "lss_overdensity": 4,
        "galaxy_groups": 14,
        "galaxy_group_memberships": 4,
        "specz_compilation": 32,
    }
    assert evidence["master_tfields_total"] == 1_349
    assert evidence["master_prior_expectation"] == 1_349
    assert evidence["master_prior_difference"] == 0
    assert evidence["native_total"] == 1_403
    assert evidence["origin_counts"] == {
        "source_native": 1_403,
        "source_row_metadata": 7,
        "id_injected": 6,
    }
    assert len(rows) == 1_416


def test_cli_writes_configured_csv_without_contextual_id_rename(tmp_path: Path) -> None:
    """The CLI must use configured output and retain Toni ID as target id."""
    config = yaml.safe_load((REPO_ROOT / "configs" / "data_paths.yaml").read_text())
    output = tmp_path / "columns-v11.csv"
    config["dictionary"] = {"columns_v11": str(output)}
    config_path = tmp_path / "data_paths.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "src" / "etl" / "load_dictionary.py"),
            "--config",
            str(config_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dictionary rows: 1416" in result.stdout
    with output.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1_416
    toni_id = [
        row
        for row in rows
        if row["target_table"] == "galaxy_groups" and row["source_column"] == "ID"
    ]
    assert [row["target_identifier"] for row in toni_id] == ["id"]


def test_default_check_reproduces_tracked_dictionary_byte_identical() -> None:
    """Source/header or serialization drift must fail the repository check."""
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "src" / "etl" / "load_dictionary.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "dictionary check PASSED: 1416 rows reproduce byte-identical" in result.stdout
    )


def tracked_rows() -> list[dict[str, str]]:
    """Read the committed dictionary with no production helpers."""
    path = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_tracked_dictionary_preserves_master_id_lineage_and_identifier_rules() -> None:
    """ID injection, exact source names, and target namespace stay distinct."""
    rows = tracked_rows()
    native_master_ids = [
        row["target_table"]
        for row in rows
        if row["source_family"] == "master_catalog"
        and row["column_origin"] == "source_native"
        and row["source_column"].lower() == "id"
    ]
    assert native_master_ids == ["photometry_primary"]
    assert {
        row["target_table"] for row in rows if row["column_origin"] == "id_injected"
    } == {
        "lephare",
        "photometry_aper",
        "cigale",
        "ml_morpho",
        "bulge_disk",
        "galight_morph",
    }
    assert all(row["target_type"] for row in rows)
    assert len(rows) == len(
        {(row["target_table"], row["target_identifier"]) for row in rows}
    )
    assert all(
        re.fullmatch(r"[a-z_][a-z0-9_]*", row["target_identifier"])
        and len(row["target_identifier"].encode("utf-8")) <= 63
        and row["target_identifier"] not in load_dictionary.POSTGRESQL_RESERVED_WORDS
        for row in rows
    )
    assert not any(row["target_identifier"] == "ssfr_cigale" for row in rows)


def test_tracked_dictionary_records_every_live_vector_element_count() -> None:
    """The 166 live vector fields remain arrays with their observed counts."""
    vectors = Counter(
        (row["source_type"], row["element_count"], row["target_type"])
        for row in tracked_rows()
        if row["target_type"].endswith("[]")
    )
    assert vectors == {
        ("5D", "5", "double precision[]"): 18,
        ("5E", "5", "real[]"): 148,
    }
