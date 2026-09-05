#!/usr/bin/env python3
"""
Script Name  : validate_dictionary_seal.py
Description  : Validate the frozen COSMOS-Web v1.1 dictionary seal
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Reads the tracked unified dictionary and formal README without re-profiling
live source catalogs. Composes the Gate 3.1, 3.2, and 3.3 validators, then
checks the frozen Gate 3.4 counts, vocabularies, JSON schemas, and Git ignores.

Usage
-----
    python src/etl/validate_dictionary_seal.py [options]

Examples
--------
    python src/etl/validate_dictionary_seal.py
        Validates the tracked dictionary and prints audited seal counts.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


# Direct execution starts with src/etl on sys.path. Add the repository root so
# the same production imports work under the CLI and pytest.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import load_dictionary, profile_values  # noqa: E402


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"


def configured_dictionary_path(config_path: Path = DEFAULT_CONFIG_PATH) -> Path:
    """Resolve the sealed dictionary path from the repository path contract."""
    config = yaml.safe_load(config_path.read_text())
    try:
        value = config["dictionary"]["columns_v11"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Missing dictionary.columns_v11 configuration") from exc
    return Path(str(value))


DICTIONARY_PATH = configured_dictionary_path()
README_PATH = DICTIONARY_PATH.with_name("README.md")
SEALED_CSV_SHA256 = "324d3ea17b23a57223d84043559b8fa94c87c95c4710b3719f31358cd881e8b8"
SEALED_PREFIX_SHA256 = (
    "62018697ee5ba499ec6bda70926c623ccc92f62f11b1f7a422fd3b72a1104bde"
)
SEALED_PREFIX_FIELDS = load_dictionary.CSV_FIELDS[:23]

ALLOWED_SOURCE_FAMILIES = {
    "master_catalog",
    "hatamnia_lss",
    "toni_groups",
    "toni_memberships",
    "specz_compilation",
}
ALLOWED_TARGET_TABLES = {
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
    "specz_compilation_unique",
    "specz_compilation_all",
}
ALLOWED_ORIGINS = {"source_native", "source_row_metadata", "id_injected"}
EXPECTED_ORIGINS = {
    "source_native": 1_435,
    "source_row_metadata": 7,
    "id_injected": 6,
}
EXPECTED_NATIVE_TABLE_COUNTS = {
    "photometry_primary": 287,
    "photometry_aper": 148,
    "lephare": 43,
    "cigale": 56,
    "ml_morpho": 150,
    "bulge_disk": 461,
    "galight_morph": 204,
    "lss_overdensity": 4,
    "galaxy_groups": 14,
    "galaxy_group_memberships": 4,
    "specz_compilation_unique": 32,
    "specz_compilation_all": 32,
}
EXPECTED_SOURCE_FAMILY_COUNTS = {
    "master_catalog": 1_362,
    "hatamnia_lss": 4,
    "toni_groups": 14,
    "toni_memberships": 4,
    "specz_compilation": 64,
}
EXPECTED_STATUSES = {
    "verified": 1_153,
    "pattern_expanded": 204,
    "undocumented_upstream": 78,
    "project_derived": 13,
}
ALLOWED_UNITS = {
    "unknown",
    "microJy",
    "AB mag",
    "arcsecond",
    "Myr",
    "1/yr",
    "deg",
    "Msol",
    "Msol yr-1",
    "yr-1",
    "dimensionless",
    "M_sol",
    "M_sol/yr",
    "yr",
    "degrees",
    "dex/Myr",
}
UNAUTHORIZED_IDENTIFIERS = {"ssfr_cigale"}

NUMERIC_PROFILE_KEYS = {
    "finite_max",
    "finite_min",
    "fits_mask_count",
    "fits_mask_fraction",
    "index",
    "nan_count",
    "nan_fraction",
    "non_null_count",
    "non_null_fraction",
    "row_count",
    "top_values",
}
TYPED_PROFILE_KEYS = {
    "fits_mask_count",
    "fits_mask_fraction",
    "index",
    "non_null_count",
    "non_null_fraction",
    "row_count",
    "top_values",
}
CANDIDATE_KEYS = {
    "count",
    "index",
    "non_null_fraction",
    "rule_version",
    "value",
}
PROVENANCE_GROUPS = (
    (
        "description_source",
        "description_locator",
        "description_source_sha256",
    ),
    ("unit_source", "unit_locator", "unit_source_sha256"),
    (
        "semantic_note_source",
        "semantic_note_locator",
        "semantic_note_source_sha256",
    ),
)
README_CONTROLLED_VALUES = (
    ALLOWED_SOURCE_FAMILIES
    | ALLOWED_TARGET_TABLES
    | ALLOWED_ORIGINS
    | set(EXPECTED_STATUSES)
    | ALLOWED_UNITS
    | {
        "D",
        "E",
        "K",
        "J",
        "I",
        "L",
        "nA",
        "nD",
        "nE",
        "text integer",
        "text decimal",
        "text string",
        "generated zero-based row ordinal",
        "smallint",
        "integer",
        "bigint",
        "real",
        "double precision",
        "boolean",
        "text",
        "real[]",
        "double precision[]",
        "True",
        "False",
        "null",
        profile_values.CANDIDATE_RULE_VERSION,
    }
)
README_SCHEMA_KEYS = (
    {"kind", "profiles", "count", "value", "rule_version"}
    | NUMERIC_PROFILE_KEYS
    | TYPED_PROFILE_KEYS
    | CANDIDATE_KEYS
)


# =============================================================================
# CSV and documentation validation
# =============================================================================


def read_dictionary(
    path: Path = DICTIONARY_PATH,
) -> tuple[list[str], list[dict[str, str]]]:
    """Read one physical-line CSV and reject header, width, or newline drift."""
    raw = path.read_bytes()
    if b"\r" in raw:
        raise ValueError("Dictionary CSV contains a carriage return")
    text = raw.decode("utf-8")
    records = list(csv.reader(io.StringIO(text, newline="")))
    if not records:
        raise ValueError("Dictionary CSV is empty")
    if len(text.splitlines()) != len(records):
        raise ValueError("Dictionary CSV contains an embedded newline")
    header = records[0]
    if header != list(load_dictionary.CSV_FIELDS):
        raise ValueError("Dictionary header mismatch")
    widths = {len(record) for record in records}
    if widths != {len(header)}:
        raise ValueError(f"Ragged dictionary CSV: widths={sorted(widths)}")
    rows = [dict(zip(header, record, strict=True)) for record in records[1:]]
    return header, rows


def documented_readme_fields(readme_text: str) -> set[str]:
    """Return exact formal field rows from the README's fixed-field section."""
    try:
        section = readme_text.split("## 3. Fixed CSV Fields", 1)[1].split(
            "## 4. Controlled Structural Vocabularies", 1
        )[0]
    except IndexError as exc:
        raise ValueError("README lacks the fixed CSV field section") from exc
    return set(re.findall(r"^\| `([a-z0-9_]+)` \|", section, flags=re.MULTILINE))


def validate_readme_contract(readme_text: str) -> None:
    """Require every frozen field, controlled literal, and JSON schema key."""
    if documented_readme_fields(readme_text) != set(load_dictionary.CSV_FIELDS):
        raise ValueError("README field coverage mismatch")
    missing_values = sorted(
        value for value in README_CONTROLLED_VALUES if f"`{value}`" not in readme_text
    )
    missing_keys = sorted(
        key
        for key in README_SCHEMA_KEYS
        if f'"{key}"' not in readme_text and f"`{key}`" not in readme_text
    )
    required_representation_phrases = (
        "empty cell",
        "the two characters `[]`",
        "`NaN`",
        "`Infinity`",
        "`-Infinity`",
        "tokens are rejected",
    )
    missing_phrases = [
        phrase
        for phrase in required_representation_phrases
        if phrase not in readme_text
    ]
    if missing_values or missing_keys or missing_phrases:
        raise ValueError(
            "README controlled vocabulary/schema mismatch: "
            f"values={missing_values}, keys={missing_keys}, "
            f"representations={missing_phrases}"
        )


def _prefix_digest(rows: list[dict[str, str]]) -> str:
    """Hash the canonical first-23-field CSV projection."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=SEALED_PREFIX_FIELDS, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(
        {field: row[field] for field in SEALED_PREFIX_FIELDS} for row in rows
    )
    return hashlib.sha256(output.getvalue().encode("utf-8")).hexdigest()


# =============================================================================
# Frozen row and JSON validation
# =============================================================================


def _complete_or_empty(row: dict[str, str], fields: tuple[str, ...]) -> None:
    """Reject a provenance group whose controlled cells are partly populated."""
    populated = [bool(row[field]) for field in fields]
    if any(populated) and not all(populated):
        raise ValueError(f"Partial provenance group: {fields}")
    if populated[-1] and re.fullmatch(r"[0-9a-f]{64}", row[fields[-1]]) is None:
        raise ValueError(f"Invalid provenance SHA-256: {fields[-1]}")


def _finite_number(value: object) -> bool:
    """Return whether a JSON value is a finite non-boolean number."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _nonnegative_int(value: object) -> bool:
    """Return whether a JSON value is a nonnegative non-boolean integer."""
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _fraction_value(value: object) -> bool:
    """Return whether a JSON value is a finite fraction."""
    return _finite_number(value) and 0 <= value <= 1


def _validate_top_values(profile: dict[str, Any], kind: str) -> None:
    """Validate exact categorical schemas, types, bounds, and stable order."""
    top_values = profile["top_values"]
    if not isinstance(top_values, list) or len(top_values) > 3:
        raise ValueError("Top-values cardinality mismatch")
    for entry in top_values:
        if not isinstance(entry, dict) or set(entry) != {"count", "value"}:
            raise ValueError("Top-value schema mismatch")
        if not _nonnegative_int(entry["count"]) or entry["count"] == 0:
            raise ValueError("Top-value count mismatch")
        value = entry["value"]
        if kind == "numeric" and not _finite_number(value):
            raise ValueError("Numeric top value is not finite")
        if kind == "text" and not isinstance(value, str):
            raise ValueError("Text top value has wrong type")
        if kind == "boolean" and not isinstance(value, bool):
            raise ValueError("Boolean top value has wrong type")
        if entry["count"] > profile["non_null_count"]:
            raise ValueError("Top-value count exceeds non-null population")
    expected = sorted(top_values, key=lambda entry: (-entry["count"], entry["value"]))
    if top_values != expected:
        raise ValueError("Top-value ordering mismatch")


def _validate_profile_schema(row: dict[str, str]) -> None:
    """Validate exact profile and sentinel schemas beyond Gate 3.3 arithmetic."""
    try:
        payload = json.loads(row["profile_json"])
        documented = json.loads(row["documented_sentinel_values_json"])
        candidates = json.loads(row["candidate_sentinel_values_json"])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON cell") from exc
    if profile_values.canonical_json(payload) != row["profile_json"]:
        raise ValueError("Noncanonical profile JSON")
    if (
        profile_values.canonical_json(documented)
        != row["documented_sentinel_values_json"]
    ):
        raise ValueError("Noncanonical documented-sentinel JSON")
    if (
        profile_values.canonical_json(candidates)
        != row["candidate_sentinel_values_json"]
    ):
        raise ValueError("Noncanonical candidate-sentinel JSON")

    if not isinstance(payload, dict) or set(payload) != {"kind", "profiles"}:
        raise ValueError("Profile root schema mismatch")
    kind = payload["kind"]
    if kind not in {"numeric", "text", "boolean"}:
        raise ValueError("Profile kind is outside the controlled vocabulary")
    profiles = payload["profiles"]
    expected_keys = NUMERIC_PROFILE_KEYS if kind == "numeric" else TYPED_PROFILE_KEYS
    for profile in profiles:
        if not isinstance(profile, dict) or set(profile) != expected_keys:
            raise ValueError("Per-index profile schema mismatch")
        for count_field in ("row_count", "fits_mask_count", "non_null_count"):
            if not _nonnegative_int(profile[count_field]):
                raise ValueError(f"Profile count mismatch: {count_field}")
        for fraction_field in ("fits_mask_fraction", "non_null_fraction"):
            if not _fraction_value(profile[fraction_field]):
                raise ValueError(f"Profile fraction mismatch: {fraction_field}")
        if kind == "numeric":
            if not _nonnegative_int(profile["nan_count"]):
                raise ValueError("Profile NaN count mismatch")
            if not _fraction_value(profile["nan_fraction"]):
                raise ValueError("Profile NaN fraction mismatch")
            extrema = (profile["finite_min"], profile["finite_max"])
            if any(
                value is not None and not _finite_number(value) for value in extrema
            ):
                raise ValueError("Profile extrema are not finite or null")
            if (extrema[0] is None) != (extrema[1] is None):
                raise ValueError("Profile extrema are partially null")
            if extrema[0] is not None and extrema[0] > extrema[1]:
                raise ValueError("Profile extrema ordering mismatch")
        _validate_top_values(profile, kind)

    if not isinstance(documented, list) or any(
        not _finite_number(value) for value in documented
    ):
        raise ValueError("Documented-sentinel schema mismatch")
    if documented != sorted(set(documented)):
        raise ValueError("Documented-sentinel ordering mismatch")

    prior_key: tuple[int, int | float] | None = None
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_KEYS:
            raise ValueError("Candidate entry schema mismatch")
        if not _nonnegative_int(candidate["count"]) or candidate["count"] == 0:
            raise ValueError("Candidate count mismatch")
        if not _fraction_value(candidate["non_null_fraction"]):
            raise ValueError("Candidate fraction mismatch")
        if not _finite_number(candidate["value"]):
            raise ValueError("Candidate value is not finite")
        if candidate["value"] in documented:
            raise ValueError("Candidate overlaps documented sentinel")
        index = candidate["index"]
        if index is not None and (not _nonnegative_int(index)):
            raise ValueError("Candidate index mismatch")
        key = (-1 if index is None else index, candidate["value"])
        if prior_key is not None and key <= prior_key:
            raise ValueError("Candidate ordering mismatch")
        prior_key = key


def validate_rows(rows: list[dict[str, str]], readme_text: str) -> dict[str, Any]:
    """Compose production validators and enforce the frozen Gate 3.4 seal."""
    load_dictionary.validate_dictionary(rows)
    load_dictionary.validate_semantics(rows)
    profile_evidence = profile_values.validate_profiled_rows(rows)

    validate_readme_contract(readme_text)
    origins = Counter(row["column_origin"] for row in rows)
    if set(origins) != ALLOWED_ORIGINS or dict(origins) != EXPECTED_ORIGINS:
        raise ValueError(f"Column-origin count mismatch: {dict(origins)}")
    families = Counter(row["source_family"] for row in rows)
    if (
        set(families) != ALLOWED_SOURCE_FAMILIES
        or dict(families) != EXPECTED_SOURCE_FAMILY_COUNTS
    ):
        raise ValueError(f"Source-family count mismatch: {dict(families)}")
    native = [row for row in rows if row["column_origin"] == "source_native"]
    tables = Counter(row["target_table"] for row in native)
    if (
        set(tables) != ALLOWED_TARGET_TABLES
        or dict(tables) != EXPECTED_NATIVE_TABLE_COUNTS
    ):
        raise ValueError(f"Native target-table count mismatch: {dict(tables)}")
    statuses = Counter(row["description_status"] for row in rows)
    if dict(statuses) != EXPECTED_STATUSES:
        raise ValueError(f"Description-status count mismatch: {dict(statuses)}")
    if {row["unit"] for row in rows} != ALLOWED_UNITS:
        raise ValueError("Unit controlled vocabulary mismatch")
    if any(row["target_identifier"] in UNAUTHORIZED_IDENTIFIERS for row in rows):
        raise ValueError("Unauthorized science-derived identifier")

    metadata = [row for row in rows if row["column_origin"] != "source_native"]
    if any(row["description_status"] != "project_derived" for row in metadata):
        raise ValueError("Metadata description status mismatch")
    if any(row["description_status"] == "project_derived" for row in native):
        raise ValueError("Native row has project-derived description")

    for row in rows:
        for group in PROVENANCE_GROUPS:
            _complete_or_empty(row, group)
        if row["description_text"] != load_dictionary.canonicalize_description(
            row["description_text"]
        ):
            raise ValueError("Description whitespace is not canonical")
        if row["unit"] == "unknown" and any(
            row[field] for field in PROVENANCE_GROUPS[1]
        ):
            raise ValueError("Unknown unit has provenance")
        if row["unit"] != "unknown" and not all(
            row[field] for field in PROVENANCE_GROUPS[1]
        ):
            raise ValueError("Known unit lacks provenance")
        if bool(row["semantic_note"]) != all(
            bool(row[field]) for field in PROVENANCE_GROUPS[2]
        ):
            raise ValueError("Semantic-note provenance mismatch")
        if row["has_fits_mask"] not in {"True", "False"}:
            raise ValueError("Invalid has_fits_mask representation")
        if row["has_nan"] not in {"True", "False"}:
            raise ValueError("Invalid has_nan representation")
        if not row["documented_sentinel_values_json"]:
            raise ValueError("Empty documented-sentinel representation")
        if not row["candidate_sentinel_values_json"]:
            raise ValueError("Empty candidate-sentinel representation")

        documented = json.loads(row["documented_sentinel_values_json"])
        documented_evidence_fields = (
            "documented_sentinel_evidence_text",
            "documented_sentinel_source",
            "documented_sentinel_locator",
            "documented_sentinel_source_sha256",
        )
        documented_evidence = [row[field] for field in documented_evidence_fields]
        if bool(documented) != all(bool(value) for value in documented_evidence):
            raise ValueError("Documented-sentinel provenance mismatch")
        if any(documented_evidence) and not all(documented_evidence):
            raise ValueError("Partial documented-sentinel provenance")
        if documented_evidence[0] != load_dictionary.canonicalize_description(
            documented_evidence[0]
        ):
            raise ValueError("Sentinel evidence whitespace is not canonical")
        if (
            documented_evidence[-1]
            and re.fullmatch(r"[0-9a-f]{64}", documented_evidence[-1]) is None
        ):
            raise ValueError("Invalid documented-sentinel SHA-256")
        if row["column_origin"] == "source_native":
            _validate_profile_schema(row)

    if _prefix_digest(rows) != SEALED_PREFIX_SHA256:
        raise ValueError("First 23 dictionary fields drifted from the seal")
    return {
        "rows": len(rows),
        "native_rows": len(native),
        "metadata_rows": len(metadata),
        "master_native_rows": sum(
            row["source_family"] == "master_catalog" for row in native
        ),
        "readme_fields": len(documented_readme_fields(readme_text)),
        "origin_counts": dict(origins),
        "native_table_counts": dict(tables),
        "status_counts": dict(statuses),
        "profile_evidence": profile_evidence,
    }


# =============================================================================
# Git ignore and artifact validation
# =============================================================================


def _git(
    args: list[str], *, repo_root: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    """Run one read-only Git query from the repository root."""
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)


def validate_git_ignore_contract(
    *, repo_root: Path = REPO_ROOT, dictionary_path: Path = DICTIONARY_PATH
) -> None:
    """Require the narrow dictionary exception and representative ignores."""
    try:
        relative = dictionary_path.resolve().relative_to(repo_root.resolve()).as_posix()
        readme_relative = (
            dictionary_path.with_name("README.md")
            .resolve()
            .relative_to(repo_root.resolve())
            .as_posix()
        )
    except ValueError as exc:
        raise ValueError("Configured dictionary is outside the repository") from exc
    for args in (["check-ignore", relative], ["check-ignore", "-v", relative]):
        result = _git(args, repo_root=repo_root)
        if result.returncode != 1 or result.stdout or result.stderr:
            raise ValueError(f"Tracked dictionary is unexpectedly ignored: {args}")
    eligibility = _git(["check-ignore", "--no-index", relative], repo_root=repo_root)
    if eligibility.returncode != 1 or eligibility.stdout or eligibility.stderr:
        raise ValueError("Dictionary lacks the exact narrow negation")
    winning = _git(["check-ignore", "-v", "--no-index", relative], repo_root=repo_root)
    rule_text, separator, observed_path = winning.stdout.strip().partition("\t")
    pattern = rule_text.rsplit(":", 2)[-1]
    expected_pattern = f"!{relative}"
    if (
        winning.returncode != 0
        or not separator
        or observed_path != relative
        or pattern != expected_pattern
    ):
        raise ValueError(
            "Dictionary lacks the exact narrow negation: "
            f"expected {expected_pattern!r}, observed {pattern!r}"
        )
    tracked = _git(
        [
            "ls-files",
            "--error-unmatch",
            relative,
            readme_relative,
        ],
        repo_root=repo_root,
    )
    if tracked.returncode != 0:
        raise ValueError("Dictionary CSV or README is not tracked")
    ignored_samples = (
        "data/staging/profile-temp.csv",
        "data/arbitrary.csv",
        "data/interim/staging.parquet",
        "data/dictionary/profiler-temp.csv",
    )
    result = _git(["check-ignore", "-v", *ignored_samples], repo_root=repo_root)
    observed = {line.rsplit("\t", 1)[-1] for line in result.stdout.splitlines()}
    if result.returncode != 0 or observed != set(ignored_samples):
        raise ValueError("General data/staging ignore contract drifted")


def validate_seal(
    dictionary_path: Path = DICTIONARY_PATH,
    readme_path: Path = README_PATH,
    *,
    enforce_artifact_sha: bool = True,
    check_git_ignore: bool = True,
) -> dict[str, Any]:
    """Validate the exact tracked artifact, formal documentation, and ignores."""
    if enforce_artifact_sha:
        observed_sha = hashlib.sha256(dictionary_path.read_bytes()).hexdigest()
        if observed_sha != SEALED_CSV_SHA256:
            raise ValueError(f"Dictionary artifact SHA-256 mismatch: {observed_sha}")
    _, rows = read_dictionary(dictionary_path)
    evidence = validate_rows(rows, readme_path.read_text())
    if check_git_ignore:
        validate_git_ignore_contract(dictionary_path=dictionary_path)
    return evidence


# =============================================================================
# Entry Point
# =============================================================================


def _arguments() -> argparse.Namespace:
    """Parse tracked-artifact defaults and controlled mutation-test options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--dictionary", type=Path)
    parser.add_argument("--readme", type=Path)
    parser.add_argument(
        "--skip-artifact-sha",
        action="store_true",
        help="Validate a controlled mutation without the tracked-file digest.",
    )
    parser.add_argument(
        "--skip-git-ignore",
        action="store_true",
        help="Skip repository ignore checks for a temporary mutation file.",
    )
    return parser.parse_args()


def main() -> None:
    """Validate and report the tracked Gate 3.4 seal."""
    args = _arguments()
    dictionary_path = args.dictionary or configured_dictionary_path(args.config)
    readme_path = args.readme or dictionary_path.with_name("README.md")
    evidence = validate_seal(
        dictionary_path,
        readme_path,
        enforce_artifact_sha=not args.skip_artifact_sha,
        check_git_ignore=not args.skip_git_ignore,
    )
    print("dictionary seal PASSED")
    print(
        f"rows: {evidence['rows']} ({evidence['native_rows']} native, "
        f"{evidence['metadata_rows']} metadata)"
    )
    print(f"master native rows: {evidence['master_native_rows']}")
    print(f"README fields: {evidence['readme_fields']}/32")


if __name__ == "__main__":
    main()
