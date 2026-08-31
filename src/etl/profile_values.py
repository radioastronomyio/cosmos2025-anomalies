#!/usr/bin/env python3
"""
Script Name  : profile_values.py
Description  : Profile COSMOS-Web v1.1 source values and sentinel evidence
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Builds deterministic, read-only value profiles for the ETL v2 dictionary.
FITS masks, NaNs, documented sentinels, and conservative sentinel candidates
remain separate states. Numeric vectors are profiled by array index.

Usage
-----
    python src/etl/profile_values.py [--check]

Examples
--------
    python src/etl/profile_values.py --check
        Reprofiles configured live sources and checks the tracked dictionary.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import json
import math
import re
import resource
import sqlite3
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from astropy.io import fits


# =============================================================================
# Configuration
# =============================================================================

CANDIDATE_RULE_VERSION = "cosmos_v11_candidate_sentinel_v1"
CANDIDATE_RULE_TRIGGER = "abs(value)=10^k-1; count>=1000; count*1000>=non_null_count"
NUMERIC_TARGET_TYPES = {
    "smallint",
    "integer",
    "bigint",
    "real",
    "double precision",
}
DOCUMENTED_SENTINELS = {
    ("photometry_primary", "id_specz_khostovan25"): [-999],
}
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
TEXT_PROFILE_CHUNK_ROWS = 50_000


# =============================================================================
# Functions
# =============================================================================


def _json_number(value: np.generic | int | float) -> int | float:
    """Convert one finite NumPy number to a stable JSON-native scalar."""
    native = value.item() if isinstance(value, np.generic) else value
    if isinstance(native, (int, np.integer)):
        return int(native)
    converted = float(native)
    return 0.0 if converted == 0.0 else converted


def _json_typed(value: np.generic | object) -> bool | int | float | str:
    """Convert one NumPy scalar without coercing its logical source type."""
    native = value.item() if isinstance(value, np.generic) else value
    if isinstance(native, bool):
        return native
    if isinstance(native, (int, float)):
        return _json_number(native)
    return str(native)


def _fraction(count: int, denominator: int) -> float:
    """Return a deterministic zero-safe fraction."""
    return count / denominator if denominator else 0.0


def canonical_json(value: Any) -> str:
    """Serialize one compact, key-sorted JSON cell without nonfinite tokens."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _candidate_pattern(value: int | float) -> bool:
    """Return whether abs(value) is exactly 10**k - 1 for integer k >= 2."""
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        return False
    if isinstance(value, (int, np.integer)):
        absolute = abs(int(value))
    else:
        numeric = float(value)
        if not math.isfinite(numeric) or not numeric.is_integer():
            return False
        absolute = abs(int(numeric))
    candidate = 99
    while candidate < absolute:
        candidate = candidate * 10 + 9
    return absolute == candidate


def candidate_sentinels(
    frequencies: dict[int | float, int],
    *,
    non_null_count: int,
    vector_index: int | None,
    documented_sentinel_values: set[int | float],
    documented_valid_values: set[int | float],
) -> list[dict[str, Any]]:
    """Apply the frozen candidate rule with exact integer threshold arithmetic."""
    entries: list[dict[str, Any]] = []
    excluded = documented_sentinel_values | documented_valid_values
    for value, count in sorted(
        frequencies.items(), key=lambda item: _json_number(item[0])
    ):
        if value in excluded or not _candidate_pattern(value):
            continue
        # count >= 0.001 * denominator, compared exactly without float rounding.
        if count < 1_000 or count * 1_000 < non_null_count:
            continue
        entries.append(
            {
                "count": int(count),
                "index": vector_index,
                "non_null_fraction": _fraction(int(count), non_null_count),
                "rule_version": CANDIDATE_RULE_VERSION,
                "value": _json_number(value),
            }
        )
    return entries


def validate_documented_sentinel_evidence(
    values: list[int | float],
    *,
    evidence_text: str,
    source: str,
    locator: str,
    source_sha256: str,
) -> None:
    """Reject documented sentinel claims without exact text and provenance."""
    if (
        not evidence_text
        or not source
        or not locator
        or not re.fullmatch(r"[0-9a-f]{64}", source_sha256)
    ):
        raise ValueError("Documented sentinel provenance incomplete")
    for value in values:
        native = _json_number(value)
        token = str(native)
        if isinstance(native, float) and native.is_integer():
            token = str(int(native))
        if (
            re.search(rf"(?<![0-9.]){re.escape(token)}(?![0-9.])", evidence_text)
            is None
        ):
            raise ValueError(f"Unsupported documented sentinel value: {token}")


def _profile_numeric_details(
    values: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    vector_index: int | None,
) -> tuple[dict[str, Any], dict[int | float, int]]:
    """
    Profile one numeric scalar field or one vector index.

    FITS masks and NaNs are counted independently. The non-null population
    excludes either state but retains infinities; finite summaries exclude
    masks, NaNs, and infinities without changing the source array.
    """
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"Numeric profile expects one dimension, got {array.shape}")
    mask_array = (
        np.zeros(array.shape, dtype=bool) if mask is None else np.asarray(mask, bool)
    )
    if mask_array.shape != array.shape:
        raise ValueError(
            f"Numeric mask shape mismatch: values={array.shape}, mask={mask_array.shape}"
        )

    row_count = int(array.size)
    fits_mask_count = int(np.count_nonzero(mask_array))
    nan_mask = np.isnan(array) & ~mask_array
    nan_count = int(np.count_nonzero(nan_mask))
    non_null_mask = ~mask_array & ~nan_mask
    non_null_count = int(np.count_nonzero(non_null_mask))
    finite_values = array[non_null_mask & np.isfinite(array)]

    top_values: list[dict[str, int | float]] = []
    candidate_frequencies: dict[int | float, int] = {}
    finite_min: int | float | None = None
    finite_max: int | float | None = None
    if finite_values.size:
        unique, counts = np.unique(finite_values, return_counts=True)
        ranked = sorted(
            zip(unique, counts, strict=True),
            key=lambda item: (-int(item[1]), _json_number(item[0])),
        )[:3]
        top_values = [
            {"count": int(count), "value": _json_number(value)}
            for value, count in ranked
        ]
        finite_min = _json_number(unique[0])
        finite_max = _json_number(unique[-1])
        candidate_frequencies = {
            _json_number(value): int(count)
            for value, count in zip(unique, counts, strict=True)
            if _candidate_pattern(_json_number(value))
        }

    return (
        {
            "finite_max": finite_max,
            "finite_min": finite_min,
            "fits_mask_count": fits_mask_count,
            "fits_mask_fraction": _fraction(fits_mask_count, row_count),
            "index": vector_index,
            "nan_count": nan_count,
            "nan_fraction": _fraction(nan_count, row_count),
            "non_null_count": non_null_count,
            "non_null_fraction": _fraction(non_null_count, row_count),
            "row_count": row_count,
            "top_values": top_values,
        },
        candidate_frequencies,
    )


def profile_numeric(
    values: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    vector_index: int | None,
) -> dict[str, Any]:
    """Profile one numeric scalar field or vector index."""
    profile, _ = _profile_numeric_details(values, mask=mask, vector_index=vector_index)
    return profile


def profile_numeric_array(
    values: np.ndarray, *, mask: np.ndarray | None = None
) -> list[dict[str, Any]]:
    """Profile every index of a fixed-width numeric vector independently."""
    array = np.asarray(values)
    if array.ndim != 2:
        raise ValueError(
            f"Numeric vector profile expects two dimensions: {array.shape}"
        )
    mask_array = None if mask is None else np.asarray(mask, bool)
    if mask_array is not None and mask_array.shape != array.shape:
        raise ValueError(
            f"Vector mask shape mismatch: values={array.shape}, mask={mask_array.shape}"
        )
    return [
        profile_numeric(
            array[:, index],
            mask=None if mask_array is None else mask_array[:, index],
            vector_index=index,
        )
        for index in range(array.shape[1])
    ]


def profile_non_numeric(
    values: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    vector_index: int | None,
) -> dict[str, Any]:
    """Profile exact text or boolean values with deterministic tie ordering."""
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"Typed profile expects one dimension, got {array.shape}")
    mask_array = (
        np.zeros(array.shape, dtype=bool) if mask is None else np.asarray(mask, bool)
    )
    if mask_array.shape != array.shape:
        raise ValueError(
            f"Typed mask shape mismatch: values={array.shape}, mask={mask_array.shape}"
        )
    row_count = int(array.size)
    fits_mask_count = int(np.count_nonzero(mask_array))
    non_null = array[~mask_array]
    top_values: list[dict[str, Any]] = []
    if non_null.size:
        unique, counts = np.unique(non_null, return_counts=True)
        ranked = sorted(
            zip(unique, counts, strict=True),
            key=lambda item: (-int(item[1]), _json_typed(item[0])),
        )[:3]
        top_values = [
            {"count": int(count), "value": _json_typed(value)}
            for value, count in ranked
        ]
    non_null_count = int(non_null.size)
    return {
        "fits_mask_count": fits_mask_count,
        "fits_mask_fraction": _fraction(fits_mask_count, row_count),
        "index": vector_index,
        "non_null_count": non_null_count,
        "non_null_fraction": _fraction(non_null_count, row_count),
        "row_count": row_count,
        "top_values": top_values,
    }


def empty_profile_fields() -> dict[str, str | bool]:
    """Return the explicit Gate 3.3 not-applicable convention."""
    return {
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


def build_profile_fields(
    row: dict[str, Any], values: np.ndarray, *, fits_null: object | None
) -> dict[str, str | bool]:
    """Build all profile and sentinel fields for one native dictionary row."""
    array = np.asarray(values)
    mask = None if fits_null is None else np.equal(array, fits_null)
    target_type = str(row["target_type"])
    is_vector = target_type.endswith("[]")
    base_type = target_type.removesuffix("[]")
    profiles: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    documented_values = DOCUMENTED_SENTINELS.get(
        (str(row["target_table"]), str(row["source_column"])), []
    )
    fields = empty_profile_fields()
    if documented_values:
        validate_documented_sentinel_evidence(
            documented_values,
            evidence_text=str(row["description_text"]),
            source=str(row["description_source"]),
            locator=str(row["description_locator"]),
            source_sha256=str(row["description_source_sha256"]),
        )
        fields.update(
            {
                "documented_sentinel_values_json": canonical_json(
                    sorted(documented_values)
                ),
                "documented_sentinel_evidence_text": str(row["description_text"]),
                "documented_sentinel_source": str(row["description_source"]),
                "documented_sentinel_locator": str(row["description_locator"]),
                "documented_sentinel_source_sha256": str(
                    row["description_source_sha256"]
                ),
            }
        )

    if base_type in NUMERIC_TARGET_TYPES:
        if is_vector:
            if array.ndim != 2:
                raise ValueError(f"Vector source shape mismatch: {array.shape}")
            for index in range(array.shape[1]):
                profile, frequencies = _profile_numeric_details(
                    array[:, index],
                    mask=None if mask is None else mask[:, index],
                    vector_index=index,
                )
                profiles.append(profile)
                candidates.extend(
                    candidate_sentinels(
                        frequencies,
                        non_null_count=int(profile["non_null_count"]),
                        vector_index=index,
                        documented_sentinel_values=set(documented_values),
                        documented_valid_values=set(),
                    )
                )
        else:
            profile, frequencies = _profile_numeric_details(
                array, mask=mask, vector_index=None
            )
            profiles.append(profile)
            candidates.extend(
                candidate_sentinels(
                    frequencies,
                    non_null_count=int(profile["non_null_count"]),
                    vector_index=None,
                    documented_sentinel_values=set(documented_values),
                    documented_valid_values=set(),
                )
            )
        kind = "numeric"
    else:
        profiles = [profile_non_numeric(array, mask=mask, vector_index=None)]
        kind = "boolean" if base_type == "boolean" else "text"

    fields.update(
        {
            "profile_json": canonical_json({"kind": kind, "profiles": profiles}),
            "has_fits_mask": any(
                int(profile["fits_mask_count"]) > 0 for profile in profiles
            ),
            "has_nan": any(
                int(profile.get("nan_count", 0)) > 0 for profile in profiles
            ),
            "candidate_sentinel_values_json": canonical_json(candidates),
        }
    )
    return fields


def _bool_cell(value: object) -> bool:
    """Normalize in-memory booleans and their fixed CSV representation."""
    if isinstance(value, bool):
        return value
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Invalid boolean profile cell: {value!r}")


def _reject_nonfinite_json(value: Any) -> None:
    """Reject any decoded nonfinite float recursively."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite JSON profile value")
    if isinstance(value, dict):
        for nested in value.values():
            _reject_nonfinite_json(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_nonfinite_json(nested)


def validate_profile_row(row: dict[str, Any]) -> None:
    """Validate one native profile payload and its separate sentinel cells."""
    try:
        payload = json.loads(str(row["profile_json"]))
        candidates = json.loads(str(row["candidate_sentinel_values_json"]))
        documented = json.loads(str(row["documented_sentinel_values_json"]))
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid profile JSON cell") from exc
    _reject_nonfinite_json(payload)
    _reject_nonfinite_json(candidates)
    _reject_nonfinite_json(documented)

    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Profile payload lacks profiles array")
    target_type = str(row["target_type"])
    base_type = target_type.removesuffix("[]")
    expected_kind = (
        "numeric"
        if base_type in NUMERIC_TARGET_TYPES
        else "boolean"
        if base_type == "boolean"
        else "text"
    )
    if payload.get("kind") != expected_kind:
        raise ValueError(
            f"Profile kind mismatch: expected {expected_kind}, "
            f"observed {payload.get('kind')}"
        )
    is_vector = target_type.endswith("[]")
    element_count = int(row["element_count"])
    expected_profiles = element_count if is_vector else 1
    if len(profiles) != expected_profiles:
        label = "Vector" if is_vector else "Scalar"
        raise ValueError(
            f"{label} profile count mismatch: expected {expected_profiles}, "
            f"observed {len(profiles)}"
        )
    expected_indices = list(range(element_count)) if is_vector else [None]
    if [profile.get("index") for profile in profiles] != expected_indices:
        raise ValueError("Profile index ordering mismatch")

    numeric = expected_kind == "numeric"
    for profile in profiles:
        row_count = int(profile["row_count"])
        mask_count = int(profile["fits_mask_count"])
        non_null_count = int(profile["non_null_count"])
        nan_count = int(profile.get("nan_count", 0))
        if mask_count + nan_count + non_null_count != row_count:
            raise ValueError("Profile population reconciliation mismatch")
        if profile["fits_mask_fraction"] != _fraction(mask_count, row_count):
            raise ValueError("FITS mask fraction mismatch")
        if profile["non_null_fraction"] != _fraction(non_null_count, row_count):
            raise ValueError("Non-null fraction mismatch")
        if numeric and profile["nan_fraction"] != _fraction(nan_count, row_count):
            raise ValueError("NaN fraction mismatch")

    expected_fits_mask = any(
        int(profile["fits_mask_count"]) > 0 for profile in profiles
    )
    expected_nan = any(int(profile.get("nan_count", 0)) > 0 for profile in profiles)
    if _bool_cell(row.get("has_fits_mask")) != expected_fits_mask:
        raise ValueError("FITS mask summary mismatch")
    if _bool_cell(row.get("has_nan")) != expected_nan:
        raise ValueError("NaN summary mismatch")

    required_candidate_fields = {
        "value",
        "count",
        "non_null_fraction",
        "index",
        "rule_version",
    }
    for candidate in candidates:
        if not isinstance(candidate, dict) or not required_candidate_fields <= set(
            candidate
        ):
            raise ValueError("Candidate entry schema mismatch")
        if candidate["rule_version"] != CANDIDATE_RULE_VERSION:
            raise ValueError("Candidate rule version mismatch")
        if candidate["index"] not in expected_indices:
            raise ValueError("Candidate vector index mismatch")
        profile = profiles[expected_indices.index(candidate["index"])]
        count = int(candidate["count"])
        non_null_count = int(profile["non_null_count"])
        if not _candidate_pattern(candidate["value"]):
            raise ValueError("Candidate value pattern mismatch")
        if count < 1_000 or count * 1_000 < non_null_count:
            raise ValueError("Candidate threshold mismatch")
        if candidate["non_null_fraction"] != _fraction(count, non_null_count):
            raise ValueError("Candidate fraction mismatch")

    evidence_fields = (
        "documented_sentinel_evidence_text",
        "documented_sentinel_source",
        "documented_sentinel_locator",
        "documented_sentinel_source_sha256",
    )
    evidence_values = [str(row.get(field, "")) for field in evidence_fields]
    if documented:
        validate_documented_sentinel_evidence(
            documented,
            evidence_text=evidence_values[0],
            source=evidence_values[1],
            locator=evidence_values[2],
            source_sha256=evidence_values[3],
        )
    elif any(evidence_values):
        raise ValueError("Documented sentinel evidence without values")


def validate_profiled_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate complete Gate 3.3 coverage and return audited distributions."""
    native = [row for row in rows if row["column_origin"] == "source_native"]
    metadata = [row for row in rows if row["column_origin"] != "source_native"]
    if len(native) != 1_435 or len(metadata) != 13 or len(rows) != 1_448:
        raise ValueError(
            "Profile row scope mismatch: "
            f"native={len(native)}, metadata={len(metadata)}, total={len(rows)}"
        )
    for row in native:
        validate_profile_row(row)
    empty = empty_profile_fields()
    for row in metadata:
        for field, expected in empty.items():
            observed = row.get(field, "")
            if isinstance(expected, bool):
                observed = _bool_cell(observed)
            if observed != expected:
                raise ValueError(f"Metadata profile field is not applicable: {field}")

    vectors = [row for row in native if str(row["target_type"]).endswith("[]")]
    scalar_fields = len(native) - len(vectors)
    candidates = sum(
        len(json.loads(str(row["candidate_sentinel_values_json"]))) for row in native
    )
    return {
        "native_rows_profiled": len(native),
        "source_tables": len({str(row["target_table"]) for row in native}),
        "scalar_fields": scalar_fields,
        "vector_fields": len(vectors),
        "vector_indices": sum(int(row["element_count"]) for row in vectors),
        "metadata_rows_not_applicable": len(metadata),
        "has_fits_mask": dict(
            Counter(_bool_cell(row["has_fits_mask"]) for row in native)
        ),
        "has_nan": dict(Counter(_bool_cell(row["has_nan"]) for row in native)),
        "documented_sentinel_fields": sum(
            str(row["documented_sentinel_values_json"]) != "[]" for row in native
        ),
        "candidate_fields": sum(
            str(row["candidate_sentinel_values_json"]) != "[]" for row in native
        ),
        "candidate_entries": candidates,
        "candidate_rule_version": CANDIDATE_RULE_VERSION,
    }


def read_tracked_dictionary(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> list[dict[str, str]]:
    """Read the configured tracked dictionary without rebuilding live profiles."""
    config = yaml.safe_load(config_path.read_text())
    dictionary_path = Path(config["dictionary"]["columns_v11"])
    with dictionary_path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _markdown_cell(value: object) -> str:
    """Escape one generated Markdown table cell without changing its content."""
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _index_label(index: int | None) -> str:
    """Render the explicit scalar marker used by the candidate report."""
    return "scalar" if index is None else str(index)


def render_candidate_report(
    rows: list[dict[str, Any]], evidence: dict[str, Any]
) -> str:
    """Render the complete sentinel report from validated dictionary cells."""
    validate_profiled_rows(rows)
    mask_lines: list[str] = []
    nan_lines: list[str] = []
    documented_lines: list[str] = []
    candidate_lines: list[str] = []

    for row in rows:
        if row["column_origin"] != "source_native":
            continue
        payload = json.loads(str(row["profile_json"]))
        table = f"`{_markdown_cell(row['target_table'])}`"
        column = f"`{_markdown_cell(row['source_column'])}`"
        profiles = payload["profiles"]
        profile_by_index = {profile["index"]: profile for profile in profiles}
        for profile in profiles:
            index = _index_label(profile["index"])
            if int(profile["fits_mask_count"]) > 0:
                mask_lines.append(
                    f"| {table} | {column} | {index} | "
                    f"{profile['fits_mask_count']} | {profile['row_count']} | "
                    f"{profile['fits_mask_fraction']} |"
                )
            if int(profile.get("nan_count", 0)) > 0:
                nan_lines.append(
                    f"| {table} | {column} | {index} | {profile['nan_count']} | "
                    f"{profile['row_count']} | {profile['nan_fraction']} |"
                )

        documented_values = json.loads(str(row["documented_sentinel_values_json"]))
        for value in documented_values:
            documented_lines.append(
                f"| {table} | {column} | `{canonical_json(value)}` | "
                f"{_markdown_cell(row['documented_sentinel_evidence_text'])} | "
                f"`{_markdown_cell(row['documented_sentinel_source'])}` | "
                f"{_markdown_cell(row['documented_sentinel_locator'])} | "
                f"`{row['documented_sentinel_source_sha256']}` |"
            )

        candidates = json.loads(str(row["candidate_sentinel_values_json"]))
        for candidate in candidates:
            profile = profile_by_index[candidate["index"]]
            description = str(row.get("description_text", ""))
            domain = (
                description
                if description
                and row.get("description_status") in {"verified", "pattern_expanded"}
                else "unknown"
            )
            candidate_lines.append(
                f"| {table} | {column} | {_index_label(candidate['index'])} | "
                f"`{canonical_json(candidate['value'])}` | {candidate['count']} | "
                f"{profile['non_null_count']} | {candidate['non_null_fraction']} | "
                f"{_markdown_cell(domain)} | "
                f"`{CANDIDATE_RULE_TRIGGER}` | "
                f"`{candidate['rule_version']}` |"
            )

    if len(candidate_lines) != int(evidence["candidate_entries"]):
        raise ValueError("Candidate report reconciliation mismatch")
    report = f"""<!--
---
title: "COSMOS-Web v1.1 Sentinel Candidates"
description: "Generated Gate 3.3 null-state, documented-sentinel, and conservative candidate observations"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "0.1"
status: "Active"
tags:
  - type: reference
  - domain: astronomy
  - domain: etl
related_documents:
  - "[ETL v2 Dictionary](../../data/dictionary/README.md)"
  - "[Unit Conventions](unit-conventions.md)"
---
-->

# COSMOS-Web v1.1 Sentinel Candidates

Generated from the Gate 3.3 dictionary profiles. The four observation classes
below remain independent: one source field can carry FITS masks, NaNs,
documented sentinels, and conservative candidates at the same time.

---

## 1. Scope and Result

The profiler read {evidence["native_rows_profiled"]} native fields across
{evidence["source_tables"]} source tables. It recorded
{evidence["scalar_fields"]} scalar profiles,
{evidence["vector_fields"]} vector fields, and {evidence["vector_indices"]}
separate vector-index profiles. The {evidence["metadata_rows_not_applicable"]}
project metadata rows use the explicit empty/not-applicable convention and
contain no invented observations.

This report contains {evidence["candidate_entries"]} conservative candidate
observations across {evidence["candidate_fields"]} fields. Frequency is not
evidence of sentinel meaning.

## 2. Profile and Candidate Contract

`profile_json` uses compact JSON with lexically sorted object keys. Every
payload has `kind` and `profiles`. A scalar has one profile with `index=null`;
a vector has one profile for every zero-based array index in index order.
Numeric profiles contain row and non-null populations, independent FITS-mask
and NaN counts/fractions, finite min/max, and the three most frequent exact
finite values. Text and boolean profiles contain row/non-null populations,
FITS-mask counts/fractions, and deterministic exact frequent values. JSON never
contains `NaN` or `Infinity` tokens.

Candidate rule version: `{CANDIDATE_RULE_VERSION}`. An undocumented finite
numeric scalar value or a value within one numeric vector index is a candidate
when `abs(value) = 10^k - 1` for integer `k >= 2`, `count >= 1000` and \
`count * 1000 >= non_null_count`, and the value is not documented as a valid
flag/category value. The exact integer comparison is equivalent to at least
0.1% of that field/index non-null population without rounding ambiguity. The
rule runs separately by vector index. Candidate JSON is ordered by index and
numeric value; each entry records value, exact count, non-null fraction, index
or the scalar marker, and rule version.

## 3. FITS Masks

`has_fits_mask` is true for {evidence["has_fits_mask"].get(True, 0)} native
fields and false for {evidence["has_fits_mask"].get(False, 0)}. Only declared
FITS null metadata creates these masks.

| Table | Column | Index | Mask count | Source rows | Fraction |
|-------|--------|------:|-----------:|------------:|---------:|
{chr(10).join(mask_lines) if mask_lines else "| N/A | N/A | N/A | 0 | 0 | 0 |"}

## 4. NaNs

`has_nan` is true for {evidence["has_nan"].get(True, 0)} native fields and false
for {evidence["has_nan"].get(False, 0)}. NaNs are counted independently of FITS
masks.

| Table | Column | Index | NaN count | Source rows | Fraction |
|-------|--------|------:|----------:|------------:|---------:|
{chr(10).join(nan_lines) if nan_lines else "| N/A | N/A | N/A | 0 | 0 | 0 |"}

## 5. Documented Sentinels

Exact upstream evidence supports {evidence["documented_sentinel_fields"]}
native field with documented sentinel values. Empty evidence cells elsewhere
mean that upstream documentation did not explicitly define a sentinel.

| Table | Column | Value | Exact evidence text | Source | Locator | SHA-256 |
|-------|--------|------:|---------------------|--------|---------|----------|
{chr(10).join(documented_lines) if documented_lines else "| N/A | N/A | N/A | N/A | N/A | N/A | N/A |"}

## 6. Conservative Candidate Sentinels

Known physical domain is copied from sourced dictionary semantics when present;
otherwise it is literal `unknown`. It is never inferred from a column name.

| Table | Column | Index | Value | Count | Non-null denominator | Fraction | Known physical domain | Rule trigger | Rule version |
|-------|--------|-------|------:|------:|---------------------:|---------:|-----------------------|--------------|--------------|
{chr(10).join(candidate_lines) if candidate_lines else "| N/A | N/A | N/A | N/A | 0 | 0 | 0 | unknown | N/A | N/A |"}

## 7. Decision Boundary

No source value was changed, nulled, filtered, or relabeled. Documented and
candidate finite values remain source values in the lossless mirror. Scientific
cleaning decisions are deferred to a later approved analysis specification.
"""
    return report


def _fits_table(hdul: fits.HDUList, target_table: str) -> fits.BinTableHDU:
    """Resolve the configured FITS table without loading another copy."""
    if target_table == "lss_overdensity":
        return hdul["OVERDENSITY"]
    tables = [hdu for hdu in hdul if getattr(hdu, "columns", None) is not None]
    if len(tables) != 1:
        raise ValueError(f"Expected one FITS table, observed {len(tables)}")
    return tables[0]


def _profile_fits_rows(
    rows: list[dict[str, Any]], source_path: Path
) -> tuple[str, int]:
    """Profile one FITS source a column at a time through a memory map."""
    with fits.open(source_path, memmap=True, lazy_load_hdus=True) as hdul:
        target_table = str(rows[0]["target_table"])
        hdu = _fits_table(hdul, target_table)
        row_count = len(hdu.data)
        columns = {str(column.name): column for column in hdu.columns}
        for row in rows:
            source_column = str(row["source_column"])
            column = columns.get(source_column)
            if column is None:
                raise ValueError(f"Profile source column missing: {source_column}")
            fields = build_profile_fields(
                row,
                hdu.data[source_column],
                fits_null=column.null,
            )
            row.update(fields)
        return target_table, row_count


def _sqlite_value_type(target_type: str) -> str:
    """Choose an exact SQLite aggregation key type for one text-table field."""
    if target_type in {"smallint", "integer", "bigint"}:
        return "INTEGER"
    if target_type in {"real", "double precision"}:
        return "REAL"
    return "TEXT"


def _parse_text_token(token: str, target_type: str) -> int | float | str:
    """Parse one text-table token according to its dictionary target type."""
    if target_type in {"smallint", "integer", "bigint"}:
        return int(token)
    if target_type in {"real", "double precision"}:
        return float(token)
    return token


def _flush_frequency_buffers(
    connection: sqlite3.Connection,
    buffers: list[Counter[int | float | str]],
) -> None:
    """Merge one bounded chunk of exact frequencies into disk-backed tables."""
    for index, frequencies in enumerate(buffers):
        if not frequencies:
            continue
        connection.executemany(
            f"INSERT INTO f{index}(value, count) VALUES(?, ?) "
            "ON CONFLICT(value) DO UPDATE SET count=count+excluded.count",
            [(value, count) for value, count in frequencies.items()],
        )
        frequencies.clear()
    connection.commit()


def _profile_text_rows(
    rows: list[dict[str, Any]], source_path: Path
) -> tuple[str, int]:
    """Stream one whitespace table through bounded disk-backed aggregators."""
    target_table = str(rows[0]["target_table"])
    target_types = [str(row["target_type"]) for row in rows]
    row_count = 0
    nan_counts = [0] * len(rows)
    candidate_counts: list[Counter[int | float]] = [Counter() for _ in rows]
    buffers: list[Counter[int | float | str]] = [Counter() for _ in rows]

    with tempfile.TemporaryDirectory(prefix="cosmos-profile-") as temp_dir:
        database_path = Path(temp_dir) / "frequencies.sqlite3"
        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")
            for index, target_type in enumerate(target_types):
                connection.execute(
                    f"CREATE TABLE f{index}("
                    f"value {_sqlite_value_type(target_type)} PRIMARY KEY, "
                    "count INTEGER NOT NULL) WITHOUT ROWID"
                )

            with source_path.open() as handle:
                header = handle.readline().split()
                if header != [str(row["source_column"]) for row in rows]:
                    raise ValueError(f"Text profile header mismatch: {source_path}")
                for line_number, line in enumerate(handle, start=2):
                    if not line.strip():
                        continue
                    tokens = line.split()
                    if len(tokens) != len(rows):
                        raise ValueError(
                            f"Text profile width mismatch at {source_path}:{line_number}"
                        )
                    row_count += 1
                    for index, (token, target_type) in enumerate(
                        zip(tokens, target_types, strict=True)
                    ):
                        value = _parse_text_token(token, target_type)
                        if isinstance(value, float) and math.isnan(value):
                            nan_counts[index] += 1
                            continue
                        if isinstance(value, float) and not math.isfinite(value):
                            continue
                        buffers[index][value] += 1
                        if isinstance(value, (int, float)) and _candidate_pattern(
                            value
                        ):
                            candidate_counts[index][value] += 1
                    if row_count % TEXT_PROFILE_CHUNK_ROWS == 0:
                        _flush_frequency_buffers(connection, buffers)
            _flush_frequency_buffers(connection, buffers)

            for index, row in enumerate(rows):
                target_type = target_types[index]
                numeric = target_type in NUMERIC_TARGET_TYPES
                non_null_count = row_count - nan_counts[index]
                top = connection.execute(
                    f"SELECT value, count FROM f{index} "
                    "ORDER BY count DESC, value ASC LIMIT 3"
                ).fetchall()
                top_values = [
                    {"count": int(count), "value": _json_typed(value)}
                    for value, count in top
                ]
                if numeric:
                    finite_min, finite_max = connection.execute(
                        f"SELECT MIN(value), MAX(value) FROM f{index}"
                    ).fetchone()
                    profile = {
                        "finite_max": _json_number(finite_max)
                        if finite_max is not None
                        else None,
                        "finite_min": _json_number(finite_min)
                        if finite_min is not None
                        else None,
                        "fits_mask_count": 0,
                        "fits_mask_fraction": 0.0,
                        "index": None,
                        "nan_count": nan_counts[index],
                        "nan_fraction": _fraction(nan_counts[index], row_count),
                        "non_null_count": non_null_count,
                        "non_null_fraction": _fraction(non_null_count, row_count),
                        "row_count": row_count,
                        "top_values": top_values,
                    }
                    candidates = candidate_sentinels(
                        dict(candidate_counts[index]),
                        non_null_count=non_null_count,
                        vector_index=None,
                        documented_sentinel_values=set(),
                        documented_valid_values=set(),
                    )
                    kind = "numeric"
                else:
                    profile = {
                        "fits_mask_count": 0,
                        "fits_mask_fraction": 0.0,
                        "index": None,
                        "non_null_count": row_count,
                        "non_null_fraction": 1.0 if row_count else 0.0,
                        "row_count": row_count,
                        "top_values": top_values,
                    }
                    candidates = []
                    kind = "text"
                row.update(empty_profile_fields())
                row.update(
                    {
                        "profile_json": canonical_json(
                            {"kind": kind, "profiles": [profile]}
                        ),
                        "has_nan": nan_counts[index] > 0,
                        "candidate_sentinel_values_json": canonical_json(candidates),
                    }
                )
    return target_table, row_count


def profile_dictionary_rows(
    rows: list[dict[str, Any]], config_path: Path = DEFAULT_CONFIG_PATH
) -> dict[str, Any]:
    """Enrich all native rows from configured live sources and validate scope."""
    del config_path  # Source paths are already exact, config-derived dictionary cells.
    started = time.monotonic()
    for row in rows:
        if row["column_origin"] != "source_native":
            row.update(empty_profile_fields())

    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["column_origin"] == "source_native":
            by_source.setdefault(str(row["source_file"]), []).append(row)

    table_rows: dict[str, int] = {}
    for source_file, source_rows in by_source.items():
        source_path = Path(source_file)
        if source_path.suffix.lower() in {".fits", ".fit", ".fts"}:
            table, row_count = _profile_fits_rows(source_rows, source_path)
        else:
            table, row_count = _profile_text_rows(source_rows, source_path)
        table_rows[table] = row_count

    evidence = validate_profiled_rows(rows)
    evidence.update(
        {
            "source_tables": len(table_rows),
            "source_table_rows": table_rows,
            "profiling_duration_seconds": time.monotonic() - started,
            "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        }
    )
    return evidence


def build_profiled_dictionary(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build semantic rows, profile every native value, and merge evidence."""
    if __package__:
        from . import load_dictionary
    else:
        import load_dictionary

    rows, evidence = load_dictionary.build_dictionary(config_path)
    profile_evidence = profile_dictionary_rows(rows, config_path)
    return rows, {**evidence, **profile_evidence}


def _print_evidence(evidence: dict[str, Any]) -> None:
    """Print non-secret runtime facts for worklog and check reconciliation."""
    print(f"native rows profiled: {evidence['native_rows_profiled']}")
    print(
        "profiles: "
        f"{evidence['scalar_fields']} scalar fields, "
        f"{evidence['vector_fields']} vector fields, "
        f"{evidence['vector_indices']} vector indices"
    )
    print(f"source tables: {evidence['source_tables']}")
    print(f"source table rows: {canonical_json(evidence['source_table_rows'])}")
    print(f"FITS mask fields: {canonical_json(evidence['has_fits_mask'])}")
    print(f"NaN fields: {canonical_json(evidence['has_nan'])}")
    print(f"documented sentinel fields: {evidence['documented_sentinel_fields']}")
    print(
        "candidate sentinel observations: "
        f"{evidence['candidate_entries']} across {evidence['candidate_fields']} fields"
    )
    print(f"candidate rule: {evidence['candidate_rule_version']}")
    print(f"profiling duration seconds: {evidence['profiling_duration_seconds']:.3f}")
    print(f"peak RSS MiB: {evidence['peak_rss_mib']:.3f}")


def main() -> None:
    """Build or byte-check the configured Gate 3.3 dictionary artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="regenerate the report from the already profiled dictionary",
    )
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text())
    if __package__:
        from . import load_dictionary
    else:
        import load_dictionary
    output_path = Path(config["dictionary"]["columns_v11"])
    report_path = Path(config["dictionary"]["sentinel_candidates_v11"])
    if args.report_only:
        rows = read_tracked_dictionary(args.config)
        evidence = validate_profiled_rows(rows)
        report_path.write_text(render_candidate_report(rows, evidence))
        print(f"candidate report rows: {evidence['candidate_entries']}")
        print(f"wrote: {report_path}")
        return

    rows, evidence = build_profiled_dictionary(args.config)
    regenerated = load_dictionary.dictionary_csv_text(rows)
    regenerated_report = render_candidate_report(rows, evidence)
    if args.check:
        if not output_path.exists() or output_path.read_text() != regenerated:
            raise SystemExit(
                f"dictionary check FAILED: profiled content differs at {output_path}"
            )
        if not report_path.exists() or report_path.read_text() != regenerated_report:
            raise SystemExit(
                f"candidate report check FAILED: content differs at {report_path}"
            )
        print(
            f"dictionary check PASSED: {len(rows)} profiled rows reproduce "
            "byte-identical"
        )
        print("candidate report check PASSED: content reproduces byte-identical")
    else:
        output_path.write_text(regenerated)
        report_path.write_text(regenerated_report)
        print(f"dictionary rows: {len(rows)}")
        print(f"wrote: {output_path}")
        print(f"wrote: {report_path}")
    _print_evidence(evidence)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
