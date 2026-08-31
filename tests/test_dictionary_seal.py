#!/usr/bin/env python3
"""
Script Name  : test_dictionary_seal.py
Description  : Test the frozen COSMOS-Web v1.1 dictionary seal
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Gate 3.4 tests read the tracked unified dictionary without live profiling.
They verify formal README coverage before exercising the production seal
validator and its fixed structural, semantic, profile, and ignore contract.

Usage
-----
    pytest tests/test_dictionary_seal.py -v

Examples
--------
    pytest tests/test_dictionary_seal.py::test_readme_defines_every_csv_field -v
        Checks exact field-definition coverage against the tracked header.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml


# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
DICTIONARY_PATH = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"
README_PATH = REPO_ROOT / "data" / "dictionary" / "README.md"
VALIDATOR_PATH = REPO_ROOT / "src" / "etl" / "validate_dictionary_seal.py"

sys.path.insert(0, str(REPO_ROOT))

from src.etl import validate_dictionary_seal  # noqa: E402


# =============================================================================
# Test utilities
# =============================================================================


def tracked_rows() -> tuple[list[str], list[dict[str, str]]]:
    """Read the sealed artifact independently of production helpers."""
    with DICTIONARY_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    """Write a controlled mutation with the frozen CSV serialization."""
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_mutated_cli(path: Path) -> subprocess.CompletedProcess[str]:
    """Run the validator against a temporary artifact without Git checks."""
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--dictionary",
            str(path),
            "--readme",
            str(README_PATH),
            "--skip-artifact-sha",
            "--skip-git-ignore",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


# =============================================================================
# Documentation seal tests
# =============================================================================


def test_readme_defines_every_csv_field() -> None:
    """Removing any formal field row must make README coverage incomplete."""
    with DICTIONARY_PATH.open(newline="") as handle:
        header = next(csv.reader(handle))
    readme = README_PATH.read_text()
    field_section = readme.split("## 3. Fixed CSV Fields", 1)[1].split(
        "## 4. Controlled Structural Vocabularies", 1
    )[0]
    documented = set(
        re.findall(r"^\| `([a-z0-9_]+)` \|", field_section, flags=re.MULTILINE)
    )
    assert len(header) == 32
    assert documented == set(header)


def test_validator_rejects_undocumented_controlled_value() -> None:
    """Removing one controlled source family must invalidate documentation."""
    _, rows = tracked_rows()
    incomplete = README_PATH.read_text().replace("toni_groups", "toni-group-removed")
    with pytest.raises(ValueError, match="README controlled vocabulary"):
        validate_dictionary_seal.validate_rows(rows, incomplete)


def test_cli_resolves_default_artifact_from_config(tmp_path: Path) -> None:
    """A configured dictionary relocation must change the default seal target."""
    relocated = tmp_path / "dictionary"
    relocated.mkdir()
    dictionary = relocated / "columns-v11.csv"
    readme = relocated / "README.md"
    dictionary.write_bytes(DICTIONARY_PATH.read_bytes())
    readme.write_text(README_PATH.read_text())
    config = yaml.safe_load((REPO_ROOT / "configs" / "data_paths.yaml").read_text())
    config["dictionary"]["columns_v11"] = str(dictionary)
    config_path = tmp_path / "data_paths.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--config",
            str(config_path),
            "--skip-git-ignore",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "dictionary seal PASSED" in result.stdout


# =============================================================================
# Executable seal tests
# =============================================================================


def test_fast_seal_cli_accepts_the_tracked_dictionary() -> None:
    """Any frozen count, vocabulary, schema, or README drift must halt."""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dictionary seal PASSED" in result.stdout
    assert "rows: 1448 (1435 native, 13 metadata)" in result.stdout
    assert "README fields: 32/32" in result.stdout


def test_cli_rejects_empty_column_origin(tmp_path: Path) -> None:
    """An empty controlled origin must fail before a mutated seal can pass."""
    header, rows = tracked_rows()
    mutated = deepcopy(rows)
    mutated[0]["column_origin"] = ""
    path = tmp_path / "empty-origin.csv"
    write_rows(path, header, mutated)

    result = run_mutated_cli(path)

    assert result.returncode != 0
    assert "column_origin" in result.stdout + result.stderr


def test_validator_rejects_duplicate_identifier_within_specz_all(
    tmp_path: Path,
) -> None:
    """P2R-04 gate 4.2: duplicate specz_compilation_all identifiers must fail."""
    header, rows = tracked_rows()
    specz_all = [
        index
        for index, row in enumerate(rows)
        if row["target_table"] == "specz_compilation_all"
    ]
    assert len(specz_all) >= 2
    rows[specz_all[1]]["target_identifier"] = rows[specz_all[0]][
        "target_identifier"
    ]
    path = tmp_path / "duplicate-specz-identifier.csv"
    write_rows(path, header, rows)

    result = run_mutated_cli(path)

    assert result.returncode != 0
    assert "Identifier collision" in result.stdout + result.stderr


def test_validator_rejects_candidate_json_schema(tmp_path: Path) -> None:
    """An extra candidate-object key must invalidate the frozen schema."""
    header, rows = tracked_rows()
    candidate_row = next(
        row
        for row in rows
        if len(json.loads(row["candidate_sentinel_values_json"])) > 1
    )
    entries = json.loads(candidate_row["candidate_sentinel_values_json"])
    entries[0]["unsealed"] = True
    candidate_row["candidate_sentinel_values_json"] = json.dumps(
        entries, separators=(",", ":"), sort_keys=True
    )
    path = tmp_path / "candidate-schema.csv"
    write_rows(path, header, rows)

    result = run_mutated_cli(path)

    assert result.returncode != 0
    assert "Candidate entry schema mismatch" in result.stdout + result.stderr


def test_validator_rejects_candidate_json_order(tmp_path: Path) -> None:
    """Reordering valid candidate objects must invalidate stable entry order."""
    header, rows = tracked_rows()
    candidate_row = next(
        row
        for row in rows
        if len(json.loads(row["candidate_sentinel_values_json"])) > 1
    )
    entries = json.loads(candidate_row["candidate_sentinel_values_json"])
    entries.reverse()
    candidate_row["candidate_sentinel_values_json"] = json.dumps(
        entries, separators=(",", ":"), sort_keys=True
    )
    path = tmp_path / "candidate-order.csv"
    write_rows(path, header, rows)

    result = run_mutated_cli(path)

    assert result.returncode != 0
    assert "Candidate ordering mismatch" in result.stdout + result.stderr


def test_validator_rejects_documented_sentinel_candidate_overlap(
    tmp_path: Path,
) -> None:
    """A documented value may not also appear as a sentinel candidate."""
    header, rows = tracked_rows()
    row = next(item for item in rows if item["documented_sentinel_values_json"] != "[]")
    profile = json.loads(row["profile_json"])["profiles"][0]
    documented = json.loads(row["documented_sentinel_values_json"])[0]
    top_value = next(
        entry for entry in profile["top_values"] if entry["value"] == documented
    )
    row["candidate_sentinel_values_json"] = json.dumps(
        [
            {
                "count": top_value["count"],
                "index": None,
                "non_null_fraction": (top_value["count"] / profile["non_null_count"]),
                "rule_version": "cosmos_v11_candidate_sentinel_v1",
                "value": documented,
            }
        ],
        separators=(",", ":"),
        sort_keys=True,
    )
    path = tmp_path / "documented-candidate-overlap.csv"
    write_rows(path, header, rows)

    result = run_mutated_cli(path)

    assert result.returncode != 0
    assert "Candidate overlaps documented sentinel" in result.stdout + result.stderr


def test_validator_rejects_first_23_field_drift(tmp_path: Path) -> None:
    """A plausible sourced-description edit must change the sealed prefix."""
    header, rows = tracked_rows()
    row = next(item for item in rows if item["description_status"] == "verified")
    row["description_text"] = f"{row['description_text']} altered"
    path = tmp_path / "prefix-drift.csv"
    write_rows(path, header, rows)

    result = run_mutated_cli(path)

    assert result.returncode != 0
    assert "First 23 dictionary fields drifted" in result.stdout + result.stderr


def test_read_dictionary_rejects_ragged_and_embedded_newline_csv(
    tmp_path: Path,
) -> None:
    """A missing cell or quoted physical newline must fail line-oriented CSV."""
    ragged = tmp_path / "ragged.csv"
    ragged.write_text(
        ",".join(validate_dictionary_seal.load_dictionary.CSV_FIELDS) + "\nonly\n"
    )
    with pytest.raises(ValueError, match="Ragged dictionary CSV"):
        validate_dictionary_seal.read_dictionary(ragged)

    header, rows = tracked_rows()
    rows[0]["description_text"] = "line one\nline two"
    embedded = tmp_path / "embedded.csv"
    write_rows(embedded, header, rows)
    with pytest.raises(ValueError, match="embedded newline"):
        validate_dictionary_seal.read_dictionary(embedded)


def test_git_ignore_exception_remains_narrow() -> None:
    """Only the sealed CSV exception may bypass general data ignores."""
    validate_dictionary_seal.validate_git_ignore_contract()


def test_git_ignore_validator_detects_removed_negation(tmp_path: Path) -> None:
    """A tracked CSV is insufficient when its future staging exception is lost."""
    repo = tmp_path / "repo"
    dictionary = repo / "data" / "dictionary" / "columns-v11.csv"
    readme = dictionary.with_name("README.md")
    dictionary.parent.mkdir(parents=True)
    dictionary.write_text("header\n")
    readme.write_text("# fixture\n")
    gitignore = repo / ".gitignore"
    gitignore.write_text(
        "data/staging/\ndata/interim/\n*.csv\n*.parquet\n"
        "!data/dictionary/columns-v11.csv\n"
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "add",
            ".gitignore",
            "data/dictionary/README.md",
            "data/dictionary/columns-v11.csv",
        ],
        cwd=repo,
        check=True,
    )
    validate_dictionary_seal.validate_git_ignore_contract(
        repo_root=repo, dictionary_path=dictionary
    )

    gitignore.write_text("data/staging/\ndata/interim/\n*.csv\n*.parquet\n")
    with pytest.raises(ValueError, match="narrow negation"):
        validate_dictionary_seal.validate_git_ignore_contract(
            repo_root=repo, dictionary_path=dictionary
        )
