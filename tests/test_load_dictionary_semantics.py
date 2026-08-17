#!/usr/bin/env python3
"""
Script Name  : test_load_dictionary_semantics.py
Description  : Test Gate 3.2 semantic reconciliation and provenance
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Gate 3.2 tests for canonical source descriptions, exact provenance,
asymmetric GALIGHT Table 1 expansion, metadata status, independently
sourced units, and separation of project semantic notes from descriptions.
The live source artifacts are opened read-only.

Usage
-----
    pytest tests/test_load_dictionary_semantics.py -v

Examples
--------
    pytest tests/test_load_dictionary_semantics.py::test_galight_expansion_is_exact_and_asymmetric -v
        Runs the 204-row expansion and 208-row negative mutation check.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import hashlib
import io
import re
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
sys.path.insert(0, str(REPO_ROOT))

from src.etl import load_dictionary  # noqa: E402


# =============================================================================
# Test utilities
# =============================================================================


def canonicalize_independently(text: str) -> str:
    """Apply the frozen whitespace rule without production helpers."""
    return re.sub(r"\s+", " ", text).strip()


def sha256_independently(path: Path) -> str:
    """Hash one evidence artifact without production helpers."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@pytest.fixture(scope="module")
def semantic_dictionary() -> tuple[list[dict[str, str | int]], dict[str, object]]:
    """Build the live semantic dictionary once for focused assertions."""
    return load_dictionary.build_dictionary(CONFIG_PATH)


def one_row(
    rows: list[dict[str, str | int]], target_table: str, source_column: str
) -> dict[str, str | int]:
    """Select one exact dictionary row and reject ambiguous fixtures."""
    matches = [
        row
        for row in rows
        if row["target_table"] == target_table and row["source_column"] == source_column
    ]
    assert len(matches) == 1
    return matches[0]


# =============================================================================
# Canonical description tests
# =============================================================================


def test_description_canonicalization_collapses_every_whitespace_run() -> None:
    """Newlines, tabs, and repeated spaces must become one ASCII space."""
    canonicalizer = getattr(load_dictionary, "canonicalize_description", None)
    assert callable(canonicalizer), "semantic builder must expose canonicalization"
    cited_block = "  [3/780605]  Source identifier (matches\r\n\tPOINTS.id)  "
    assert canonicalizer(cited_block) == (
        "[3/780605] Source identifier (matches POINTS.id)"
    )


def test_verified_descriptions_equal_independently_canonicalized_source_blocks(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """A parser rewrite must not compose or paraphrase cited descriptions."""
    rows, _ = semantic_dictionary
    config = yaml.safe_load(CONFIG_PATH.read_text())
    detailed_path = Path(config["semantic_sources"]["master_descriptions"])
    source_line = detailed_path.read_text().splitlines()[48]
    source_name, source_block = source_line.split("\t", 1)
    assert source_name == "flux_auto_hst-f814w"
    row = one_row(rows, "photometry_primary", source_name)
    assert row["description_text"] == canonicalize_independently(source_block)
    assert row["description_locator"] == "section 1, line 49, Description"
    assert row["description_source_sha256"] == sha256_independently(detailed_path)

    lss = one_row(rows, "lss_overdensity", "id")
    assert lss["description_text"] == (
        "[3/780605] Source identifier (matches POINTS.id)"
    )
    assert lss["description_locator"] == "OVERDENSITY, lines 92-93, Explanations"


def test_lss_units_cite_units_column_separately_from_descriptions(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """Hatamnia degree units must cite Units, not Explanations."""
    rows, _ = semantic_dictionary
    config = yaml.safe_load(CONFIG_PATH.read_text())
    source_path = Path(config["semantic_sources"]["lss_readme"])
    source_hash = sha256_independently(source_path)
    for source_column, line_number in (("RA", 94), ("Dec", 95)):
        row = one_row(rows, "lss_overdensity", source_column)
        assert row["description_locator"] == (
            f"OVERDENSITY, line {line_number}, Explanations"
        )
        assert row["unit"] == "deg"
        assert row["unit_source"] == str(source_path)
        assert row["unit_locator"] == (f"OVERDENSITY, line {line_number}, Units")
        assert row["unit_source_sha256"] == source_hash


# =============================================================================
# Status and provenance tests
# =============================================================================


def test_semantic_statuses_and_provenance_are_complete(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """Missing evidence or status drift must change literal audited counts."""
    rows, evidence = semantic_dictionary
    required_fields = {
        "description_text",
        "description_source",
        "description_locator",
        "description_source_sha256",
        "description_status",
        "unit",
        "unit_source",
        "unit_locator",
        "unit_source_sha256",
        "semantic_note",
        "semantic_note_source",
        "semantic_note_locator",
        "semantic_note_source_sha256",
    }
    assert all(required_fields <= row.keys() for row in rows)
    assert Counter(str(row["description_status"]) for row in rows) == {
        "verified": 1_150,
        "pattern_expanded": 204,
        "undocumented_upstream": 49,
        "project_derived": 13,
    }
    assert evidence["description_status_counts"] == {
        "verified": 1_150,
        "pattern_expanded": 204,
        "undocumented_upstream": 49,
        "project_derived": 13,
    }
    for row in rows:
        if row["description_status"] in {"verified", "pattern_expanded"}:
            assert row["description_text"]
            assert row["description_source"]
            assert row["description_locator"]
            assert re.fullmatch(r"[0-9a-f]{64}", str(row["description_source_sha256"]))
        if row["description_status"] == "undocumented_upstream":
            assert row["description_text"] == ""


def test_undocumented_and_project_derived_mutations_halt_validation(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """Names cannot become prose, and native rows cannot become metadata."""
    rows, _ = semantic_dictionary
    validator = getattr(load_dictionary, "validate_semantics", None)
    assert callable(validator), "semantic builder must expose semantic validation"

    composed = deepcopy(rows)
    ebv = one_row(composed, "cigale", "ebv_stars")
    ebv["description_text"] = "Stellar color excess"
    with pytest.raises(ValueError, match="Undocumented description must be empty"):
        validator(composed)

    native_metadata = deepcopy(rows)
    one_row(native_metadata, "cigale", "mass")["description_status"] = "project_derived"
    with pytest.raises(ValueError, match="Project-derived status on native row"):
        validator(native_metadata)

    missing_hash = deepcopy(rows)
    one_row(missing_hash, "photometry_primary", "id")["description_source_sha256"] = ""
    with pytest.raises(ValueError, match="Description provenance incomplete"):
        validator(missing_hash)


def test_metadata_and_undocumented_rows_follow_frozen_precedence(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """Exactly thirteen constructed rows, two E(B-V) gaps, and Toni gaps remain."""
    rows, _ = semantic_dictionary
    metadata = [row for row in rows if row["description_status"] == "project_derived"]
    assert Counter(str(row["column_origin"]) for row in metadata) == {
        "source_row_metadata": 7,
        "id_injected": 6,
    }
    assert all(row["description_text"] for row in metadata)
    assert not any(
        row["column_origin"] == "source_native"
        and row["description_status"] == "project_derived"
        for row in rows
    )

    for name in ("ebv_stars", "ebv_stars_err"):
        row = one_row(rows, "cigale", name)
        assert row["description_status"] == "undocumented_upstream"
        assert row["description_text"] == ""
        assert row["unit"] == "unknown"

    toni = [
        row
        for row in rows
        if row["source_family"] in {"toni_groups", "toni_memberships"}
    ]
    assert len(toni) == 18
    assert {row["description_status"] for row in toni} == {"undocumented_upstream"}


# =============================================================================
# GALIGHT Table 1 tests
# =============================================================================


def test_galight_expansion_is_exact_and_asymmetric(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """The live 204-row pattern set must reject a 208-row symmetric mutation."""
    rows, evidence = semantic_dictionary
    galight = [
        row
        for row in rows
        if row["target_table"] == "galight_morph"
        and row["column_origin"] == "source_native"
    ]
    assert len(galight) == 204
    assert evidence["galight_category_counts"] == {
        "single_sersic": 40,
        "bulge_disk_parameters": 40,
        "bulge_disk_errors": 32,
        "point_source": 44,
        "fit_statistics": 24,
        "statmorph": 24,
    }
    for filter_name in ("F115W", "F150W", "F277W", "F444W"):
        per_filter = [
            row
            for row in galight
            if f"filter={filter_name}" in str(row["description_locator"])
        ]
        assert len(per_filter) == 51
        names = {str(row["source_column"]) for row in per_filter}
        lower_filter = filter_name.lower()
        assert f"nsersic_bulge_{lower_filter}_bd_err" not in names
        assert f"nsersic_disk_{lower_filter}_bd_err" not in names
        for component in ("bulge", "disk"):
            assert {
                f"{parameter}_{component}_{lower_filter}_bd_err"
                for parameter in ("rearc", "mag", "qratio", "phi")
            } <= names

    sample = one_row(galight, "galight_morph", "rearc_f115w_sersic")
    assert sample["description_text"] == (
        "Half-light radius (arcsecond) of Sérsic model in xxx filter"
    )
    assert "arXiv:2606.14869v1" in str(sample["description_source"])
    assert "pattern=rearc_xxx_sersic" in str(sample["description_locator"])
    assert "filter=F115W" in str(sample["description_locator"])
    assert sample["description_source_sha256"] == (
        "f4d369c1f3c093dc5990895ac7f95ceecead318339e9fe1b8b823fb51675f0bc"
    )

    symmetric = deepcopy(rows)
    for filter_name in ("f115w", "f150w", "f277w", "f444w"):
        added = deepcopy(
            one_row(symmetric, "galight_morph", f"rearc_bulge_{filter_name}_bd_err")
        )
        added["source_column"] = f"nsersic_bulge_{filter_name}_bd_err"
        added["target_identifier"] = f"nsersic_bulge_{filter_name}_bd_err"
        added["description_locator"] = str(added["description_locator"]).replace(
            "pattern=rearc_bulge_xxx_bd_err",
            "pattern=nsersic_bulge_xxx_bd_err",
        )
        symmetric.append(added)
    assert (
        len(
            [
                row
                for row in symmetric
                if row["target_table"] == "galight_morph"
                and row["column_origin"] == "source_native"
            ]
        )
        == 208
    )
    with pytest.raises(ValueError, match="GALIGHT pattern set mismatch"):
        load_dictionary.validate_semantics(symmetric)


# =============================================================================
# Units, semantic notes, and serialization tests
# =============================================================================


def test_units_and_semantic_notes_use_independent_evidence_fields(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """Unit and parameter-space facts must not be inferred or concatenated."""
    rows, evidence = semantic_dictionary
    assert one_row(rows, "photometry_primary", "flux_auto_hst-f814w")["unit"] == (
        "microJy"
    )
    assert one_row(rows, "lss_overdensity", "RA")["unit"] == "deg"
    assert one_row(rows, "galight_morph", "rearc_f115w_sersic")["unit"] == ("arcsecond")
    assert one_row(rows, "galight_morph", "mag_f115w_sersic")["unit"] == ("unknown")
    for row in rows:
        if row["unit"] != "unknown":
            assert row["unit_source"]
            assert row["unit_locator"]
            assert re.fullmatch(r"[0-9a-f]{64}", str(row["unit_source_sha256"]))

    lephare_columns = {
        "mass_l68",
        "mass_med",
        "mass_u68",
        "sfr_l68",
        "sfr_med",
        "sfr_u68",
        "ssfr_l68",
        "ssfr_med",
        "ssfr_u68",
    }
    cigale_columns = {
        "mass",
        "mass_err",
        "sfr_inst",
        "sfr_inst_err",
        "sfr_100myr",
        "sfr_100myr_err",
    }
    noted = [row for row in rows if row["semantic_note"]]
    assert {
        str(row["source_column"]) for row in noted if row["target_table"] == "lephare"
    } == lephare_columns
    assert {
        str(row["source_column"]) for row in noted if row["target_table"] == "cigale"
    } == cigale_columns
    assert len(noted) == 15
    assert evidence["semantic_note_count"] == 15
    unit_conventions = REPO_ROOT / "docs" / "reference" / "unit-conventions.md"
    expected_hash = sha256_independently(unit_conventions)
    assert {row["semantic_note_source_sha256"] for row in noted} == {expected_hash}
    assert all(
        "unit-conventions.md" in str(row["semantic_note_source"]) for row in noted
    )
    assert all("log10" not in str(row["description_text"]) for row in noted)
    assert all("linear space" not in str(row["description_text"]) for row in noted)
    assert not any(row["target_identifier"] == "ssfr_cigale" for row in rows)


def test_csv_schema_is_fixed_and_contains_no_embedded_newlines(
    semantic_dictionary: tuple[list[dict[str, str | int]], dict[str, object]],
) -> None:
    """Semantic enrichment must preserve a rectangular line-oriented CSV."""
    rows, _ = semantic_dictionary
    expected_header = [
        "source_family",
        "source_file",
        "source_locator",
        "source_column",
        "source_type",
        "element_count",
        "target_table",
        "target_identifier",
        "target_type",
        "column_origin",
        "description_text",
        "description_source",
        "description_locator",
        "description_source_sha256",
        "description_status",
        "unit",
        "unit_source",
        "unit_locator",
        "unit_source_sha256",
        "semantic_note",
        "semantic_note_source",
        "semantic_note_locator",
        "semantic_note_source_sha256",
    ]
    serialized = load_dictionary.dictionary_csv_text(rows)
    parsed = list(csv.reader(io.StringIO(serialized, newline="")))
    assert parsed[0] == expected_header
    assert len(parsed) == 1_417
    assert {len(record) for record in parsed} == {len(expected_header)}
    assert all(
        "\n" not in str(value) and "\r" not in str(value)
        for row in rows
        for value in row.values()
    )
