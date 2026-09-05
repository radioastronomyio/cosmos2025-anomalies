#!/usr/bin/env python3
"""
Script Name  : generate_verification_surface_v11.py
Description  : Generate the offline ETL v2 verification approval surface
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Compiles tracked ETL v2 evidence into a deterministic approval surface without
source-artifact, credential, handoff-content, or PostgreSQL access.

Usage
-----
    python src/etl/generate_verification_surface_v11.py [--check]

Examples
--------
    python src/etl/generate_verification_surface_v11.py
        Generate the tracked verification surface from sealed offline evidence.

    python src/etl/generate_verification_surface_v11.py --check
        Verify byte identity without writing the tracked report.
"""

from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml


# =============================================================================
# Fixed offline evidence boundary
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs/data_paths.yaml"
SEALED_DICTIONARY_SHA256 = (
    "623e98f82f435c2ee5112af2d07d4553864f665a82a895c175a47d3edfa883cf"
)
SEALED_INPUT_SHA256 = {
    "schema_sql": "79758219c135dcaa9a97c4182e7aa783c9d0ca2e2de35ebcc3fdb46bc57ad06b",
    "schema_doc": "32ea344e75958c1acfea8dc4bda3f36f93393e020968515fe35fa3ee2620f61a",
    "conformance_cases": "5e0c259447be2ffe09a8ef6c1f11eab2ecb4ee1a4b550ec42b65f880956f776e",
    "candidate_report": "8a055dd55930371add68f52beedaed660a8e275a74bba36d41004dd24bc8bfdd",
    "manifest": "5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e",
    "unit_conventions": "8a4d3a724ba435fe5668260e50be45c41f067214567a8723d27d004d3df9ca4a",
    "science_opportunities": "d53aac1f4c23a4f0676eb358fecb027e542fcea1030f474911661d8b38dae69f",
    "central_spec": "6f627d9941843f2d8643eca5227aced1d8bc9216310079dc0fed25352cd09b16",
    "research_index": "acd8e942c26e2142d5b4d44c0998d918f22af0f31ffb2e51a8623c434454c233",
}
APPENDIX_SHA256 = {
    "gaps": "6a28c4bfde2c7220f81765ea6ab33337fa622d639c7f8285c9d45ae461c82a4f",
    "candidates": "b7059634706d5bbad65aecd3ff30fda2427271cc3d5893335527df0f572af372",
    "provenance": "8e5bee2df85db34d61c8544c863ec59626dc8ec4256c75616f89db941cee6569",
    "flags": "450fd99eb7b2f5ecf635f62c3f68a5cce9a4625595085e1b93617ccd2e891d19",
}
WORKLOG_RELATIVE = "work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md"
# P2R-04 extended the sealed dictionary, DDL, conformance cases, and candidate
# report (authorized successor change). This module reproduces the frozen
# P2R-03 operator approval surface, so those four sealed inputs fall back to
# the exact P2R-03-committed bytes when the live files no longer match their
# Gate 3.13 seals. The compiler itself stays mechanically offline and
# tracked-only: the historical-bytes provider is injectable and defaults to
# None, which keeps strict seal behavior for the bare CLI. A mutated file at
# any other path always fails strictly; only the exact configured live path
# may fall back.
P2R03_EVIDENCE_REF = "e65242a7802422cc86ed47d96945e2a86e0b27a3"
P2R03_FALLBACK_NAMES = {
    "dictionary": "data/dictionary/columns-v11.csv",
    "schema_sql": "src/etl/schema_v11.sql",
    "schema_doc": "docs/reference/schema-v11.md",
    "conformance_cases": "src/etl/conformance_cases_v11.py",
    "candidate_report": "docs/reference/sentinel-candidates-v11.md",
    "research_index": "docs/research/README.md",
}
historical_evidence_provider: "callable | None" = None
WORKLOG_EVIDENCE_SHA256 = (
    "9f18c6926a24f9edc36b31d7346e0b377d2b4867c9e70c1068942bf4839defbf"
)
ACTIVE_CENTRAL_SPEC_PATH = Path(
    "/opt/agents/repos/spec/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
)
ARCHIVED_CENTRAL_SPEC_PATH = Path(
    "/opt/agents/repos/spec/2026-08/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
)


@dataclass(frozen=True)
class EvidencePaths:
    """Exact tracked inputs and sole generated output for Gate 3.13."""

    dictionary: Path
    worklog: Path
    schema_sql: Path
    schema_doc: Path
    conformance_cases: Path
    candidate_report: Path
    manifest: Path
    unit_conventions: Path
    science_opportunities: Path
    central_spec: Path
    central_spec_read: Path
    research_index: Path
    output: Path


@dataclass(frozen=True)
class EvidenceItem:
    """One numeric observation tied to an exact tracked locator."""

    label: str
    value: int | str
    source_path: str
    source_locator: str


@dataclass(frozen=True)
class GapRecord:
    """One exact upstream description gap from the sealed dictionary."""

    case_id: str
    table: str
    column: str
    source_file: str
    source_locator: str
    source_column: str


@dataclass(frozen=True)
class CandidateRecord:
    """One expanded finite candidate observation, never a cleaning rule."""

    case_id: str
    table: str
    column: str
    source_locator: str
    index: int | None
    value: int | float
    count: int
    denominator: int
    non_null_fraction: float
    rule_version: str


@dataclass(frozen=True)
class DictionaryEvidence:
    """Complete Gate 3.13 facts derived from all sealed dictionary rows."""

    row_count: int
    native_count: int
    metadata_count: int
    master_native_count: int
    description_counts: Mapping[str, int]
    unit_counts: Mapping[str, int]
    semantic_counts: Mapping[str, int]
    null_counts: Mapping[str, int]
    documented_fields: int
    documented_values: int
    candidate_fields: int
    gaps: tuple[GapRecord, ...]
    candidates: tuple[CandidateRecord, ...]


@dataclass(frozen=True)
class ProvenanceRecord:
    """One tracked exact provenance table record."""

    table: str
    rows: int
    load_xmin: int
    declared_sha256: str
    observed_sha256: str
    source_locator: str


@dataclass(frozen=True)
class WorklogEvidence:
    """Operational observations extracted from unique tracked gate anchors."""

    values: Mapping[str, int]
    provenance_rows: tuple[ProvenanceRecord, ...]
    quality_flags: Mapping[int, int]
    v1_fingerprint: str
    sources: tuple[EvidenceItem, ...]
    locators: Mapping[str, str]


@dataclass(frozen=True)
class PolicyEvidence:
    """Exact configured sources for the five deferred policy questions."""

    topics: Mapping[str, EvidenceItem]
    operator_authority: EvidenceItem


@dataclass(frozen=True)
class Finding:
    """One numbered, sourced, closed-question approval finding."""

    finding_id: str
    statement: str
    evidence: tuple[EvidenceItem, ...]
    closed_question: str
    recommendation: str
    deferred: bool = False
    topic: str = ""


@dataclass(frozen=True)
class OperatorDecision:
    """One recommendation whose disposition only the operator may fill."""

    decision: str
    recommendation: str
    disposition: str = ""


class ReportOutputRetainedError(RuntimeError):
    """A failed command nevertheless retained the exact generated bytes."""


class ReportOutputUnvalidatedError(RuntimeError):
    """A post-replace failure left output state that cannot be proven exact."""


def read_stable_regular_bytes(path: Path) -> bytes:
    """Read one regular inode without following or racing a final-path link."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except (FileNotFoundError, OSError) as exc:
        raise ValueError("regular tracked evidence is absent or unsafe") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("regular tracked evidence is required")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        final = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except FileNotFoundError as exc:
        raise ValueError("regular tracked evidence identity changed") from exc
    identity = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
    if identity != (
        final.st_dev,
        final.st_ino,
        final.st_size,
        final.st_mtime_ns,
    ) or identity != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ValueError("regular tracked evidence identity changed")
    return b"".join(chunks)


def read_sealed_evidence_bytes(name: str, path: Path) -> bytes:
    """Read one sealed input, falling back to pinned P2R-03 bytes if provided.

    The fallback applies only at the exact configured live path for the four
    inputs P2R-04 legitimately regenerated (dictionary, DDL, conformance
    cases, candidate report), only when an injected historical provider
    supplies the pinned bytes, and only when those bytes match the seal. Any
    other path, including a mutated temporary file, must match its seal
    exactly or fail.
    """
    raw = read_stable_regular_bytes(path)
    expected_digest = (
        SEALED_DICTIONARY_SHA256
        if name == "dictionary"
        else SEALED_INPUT_SHA256.get(name)
    )
    if expected_digest is None or hashlib.sha256(raw).hexdigest() == expected_digest:
        return raw
    blob_path = P2R03_FALLBACK_NAMES.get(name)
    live_path = REPO_ROOT / blob_path if blob_path is not None else None
    mismatch_error = ValueError(
        "dictionary seal mismatch"
        if name == "dictionary"
        else "verification evidence input seal mismatch"
    )
    if blob_path is None or live_path is None or path.resolve() != live_path.resolve():
        raise mismatch_error
    if historical_evidence_provider is None:
        raise mismatch_error
    historical = historical_evidence_provider(blob_path)
    if historical is None or hashlib.sha256(historical).hexdigest() != expected_digest:
        raise mismatch_error
    return historical


def _require_exact_path(observed: Path, expected: Path) -> Path:
    if observed != expected:
        raise ValueError("verification evidence path mismatch")
    return observed


def select_central_spec_read_path(archive: Path, active: Path) -> Path:
    """Choose one exact regular pre- or post-closeout spec inode."""
    regular: list[Path] = []
    for path in (archive, active):
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("central spec lifecycle path is unsafe")
        regular.append(path)
    if len(regular) != 1:
        raise ValueError("central spec lifecycle state mismatch")
    return regular[0]


def resolve_evidence_paths(
    config_path: Path = DEFAULT_CONFIG_PATH, *, repo_root: Path = REPO_ROOT
) -> EvidencePaths:
    """Resolve and guard the fixed tracked-only Gate 3.13 path contract."""
    root = repo_root.resolve(strict=True)
    if root != REPO_ROOT.resolve(strict=True):
        raise ValueError("verification evidence path repository mismatch")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        dictionary = config["dictionary"]
        provenance = config["provenance"]
        semantics = config["semantic_sources"]
        verification = config["verification_surface"]
        observed = {
            "dictionary": Path(dictionary["columns_v11"]),
            "schema_sql": Path(dictionary["schema_v11_sql"]),
            "schema_doc": Path(dictionary["schema_v11_docs"]),
            "conformance_cases": Path(dictionary["conformance_cases_v11"]),
            "candidate_report": Path(dictionary["sentinel_candidates_v11"]),
            "manifest": Path(provenance["source_manifest_v11"]),
            "unit_conventions": Path(semantics["unit_conventions"]),
            "central_spec": Path(verification["central_spec_archive"]),
            "worklog": Path(verification["cumulative_worklog"]),
            "science_opportunities": Path(verification["science_opportunities"]),
            "research_index": Path(verification["research_index"]),
            "output": Path(verification["output"]),
        }
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "verification evidence path configuration is incomplete"
        ) from exc
    expected = {
        "dictionary": root / "data/dictionary/columns-v11.csv",
        "schema_sql": root / "src/etl/schema_v11.sql",
        "schema_doc": root / "docs/reference/schema-v11.md",
        "conformance_cases": root / "src/etl/conformance_cases_v11.py",
        "candidate_report": root / "docs/reference/sentinel-candidates-v11.md",
        "manifest": root / "docs/reference/data-manifest-v1.1.csv",
        "unit_conventions": root / "docs/reference/unit-conventions.md",
        "central_spec": ARCHIVED_CENTRAL_SPEC_PATH,
        "worklog": root / WORKLOG_RELATIVE,
        "science_opportunities": root / "docs/research/science-opportunities.md",
        "research_index": root / "docs/research/README.md",
        "output": root / "docs/research/etl-v2-verification.md",
    }
    guarded = {
        name: _require_exact_path(observed[name], expected[name]) for name in expected
    }
    central_spec_read = select_central_spec_read_path(
        ARCHIVED_CENTRAL_SPEC_PATH, ACTIVE_CENTRAL_SPEC_PATH
    )
    for name, path in guarded.items():
        if name == "output":
            try:
                metadata = path.parent.lstat()
            except FileNotFoundError as exc:
                raise ValueError(
                    "verification evidence path output parent absent"
                ) from exc
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError("verification evidence path output parent unsafe")
            if path.exists() or path.is_symlink():
                try:
                    output_metadata = path.lstat()
                except FileNotFoundError as exc:
                    raise ValueError(
                        "verification evidence path output unsafe"
                    ) from exc
                if not stat.S_ISREG(output_metadata.st_mode):
                    raise ValueError("verification evidence path output unsafe")
            continue
        raw = read_sealed_evidence_bytes(
            name, central_spec_read if name == "central_spec" else path
        )
        expected_digest = SEALED_INPUT_SHA256.get(name)
        if expected_digest is not None and hashlib.sha256(raw).hexdigest() != (
            expected_digest
        ):
            raise ValueError("verification evidence input seal mismatch")
    return EvidencePaths(**guarded, central_spec_read=central_spec_read)


def extract_dictionary_evidence(path: Path) -> DictionaryEvidence:
    """Compute all dictionary findings and appendices from the exact seal."""
    raw = read_sealed_evidence_bytes("dictionary", path)
    if hashlib.sha256(raw).hexdigest() != SEALED_DICTIONARY_SHA256:
        raise ValueError("dictionary seal mismatch")
    text = raw.decode("utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    if len(rows) != 1_416:
        raise ValueError("dictionary seal row mismatch")
    descriptions = Counter(row["description_status"] for row in rows)
    origins = Counter(row["column_origin"] for row in rows)
    unit_counts = Counter(
        "provenanced" if row["unit"] != "unknown" else "unknown" for row in rows
    )
    semantic_counts = Counter(
        "provenanced" if row["semantic_note"] else "absent" for row in rows
    )
    null_counts = Counter()
    gaps: list[GapRecord] = []
    candidates: list[CandidateRecord] = []
    documented_fields = 0
    documented_values = 0
    candidate_fields = 0
    for index, row in enumerate(rows, 1):
        mask, nan = row["has_fits_mask"], row["has_nan"]
        if (mask, nan) == ("False", "False"):
            null_counts["none"] += 1
        elif (mask, nan) == ("False", "True"):
            null_counts["nan"] += 1
        elif (mask, nan) == ("True", "False"):
            null_counts["fits_mask"] += 1
        else:
            raise ValueError("dictionary seal NULL encoding mismatch")
        case_id = f"{index:04d}:{row['target_table']}.{row['target_identifier']}"
        if row["description_status"] == "undocumented_upstream":
            gaps.append(
                GapRecord(
                    case_id=case_id,
                    table=row["target_table"],
                    column=row["target_identifier"],
                    source_file=row["source_file"],
                    source_locator=row["source_locator"],
                    source_column=row["source_column"],
                )
            )
        documented = json.loads(row["documented_sentinel_values_json"])
        if documented:
            documented_fields += 1
            documented_values += len(documented)
        candidate_payload = json.loads(row["candidate_sentinel_values_json"])
        profile_payload = (
            json.loads(row["profile_json"]) if row["profile_json"] else None
        )
        denominators = (
            {
                profile["index"]: profile["non_null_count"]
                for profile in profile_payload["profiles"]
            }
            if profile_payload is not None
            else {}
        )
        if candidate_payload:
            candidate_fields += 1
        for candidate in candidate_payload:
            candidates.append(
                CandidateRecord(
                    case_id=case_id,
                    table=row["target_table"],
                    column=row["target_identifier"],
                    source_locator=row["source_locator"],
                    index=candidate["index"],
                    value=candidate["value"],
                    count=candidate["count"],
                    denominator=denominators[candidate["index"]],
                    non_null_fraction=candidate["non_null_fraction"],
                    rule_version=candidate["rule_version"],
                )
            )
    evidence = DictionaryEvidence(
        row_count=len(rows),
        native_count=origins["source_native"],
        metadata_count=origins["source_row_metadata"] + origins["id_injected"],
        master_native_count=sum(
            row["source_family"] == "master_catalog"
            and row["column_origin"] == "source_native"
            for row in rows
        ),
        description_counts=dict(descriptions),
        unit_counts=dict(unit_counts),
        semantic_counts=dict(semantic_counts),
        null_counts=dict(null_counts),
        documented_fields=documented_fields,
        documented_values=documented_values,
        candidate_fields=candidate_fields,
        gaps=tuple(gaps),
        candidates=tuple(candidates),
    )
    expected = (49, 793, 476, 1, 1)
    observed = (
        len(evidence.gaps),
        len(evidence.candidates),
        evidence.candidate_fields,
        evidence.documented_fields,
        evidence.documented_values,
    )
    if observed != expected:
        raise ValueError("dictionary seal appendix mismatch")
    return evidence


def _section(text: str, heading: str, next_heading: str) -> tuple[str, int]:
    start_token = f"### {heading}"
    end_token = f"### {next_heading}"
    if text.count(start_token) != 1 or text.count(end_token) != 1:
        raise ValueError("worklog evidence anchor section mismatch")
    start = text.index(start_token)
    end = text.index(end_token, start + len(start_token))
    return text[start:end], text[:start].count("\n") + 1


def _line_for(section: str, section_line: int, needle: str) -> int:
    if section.count(needle) != 1:
        raise ValueError("worklog evidence anchor is missing or duplicated")
    return section_line + section[: section.index(needle)].count("\n")


def _number(pattern: str, text: str) -> int:
    matches = re.findall(pattern, text, re.DOTALL)
    if len(matches) != 1:
        raise ValueError("worklog evidence anchor numeric value is absent")
    return int(matches[0].replace(",", ""))


def _exact_word_number(phrase: str, text: str, value: int) -> int:
    if text.count(phrase) != 1:
        raise ValueError("worklog evidence anchor word-number value is absent")
    return value


def extract_worklog_evidence(path: Path) -> WorklogEvidence:
    """Parse exact unique operational facts from the tracked cumulative worklog."""
    text = read_stable_regular_bytes(path).decode("utf-8")
    gate35, line35 = _section(
        text,
        "Gate 3.5 source integrity and standalone/master fidelity",
        "Gate 3.6 generated mirror DDL and scratch validation",
    )
    gate7, line7 = _section(
        text,
        "Gate 3.7 persistent master load, analyst role, and handoff",
        "Gate 3.8 supplements and spec-z",
    )
    gate8, line8 = _section(
        text,
        "Gate 3.8 supplements and spec-z",
        "Gate 3.9 dual-hash provenance",
    )
    gate9, line9 = _section(
        text,
        "Gate 3.9 dual-hash provenance",
        "Gate 3.10 dictionary-driven conformance",
    )
    gate11, line11 = _section(
        text,
        "Gate 3.11 full-coverage value reconciliation",
        "Gate 3.12 generated schema and project documentation",
    )
    gate12_start = text.index(
        "### Gate 3.12 generated schema and project documentation"
    )
    gate12_stops = [text.index("\n---\n\n## 2. Files Changed", gate12_start)]
    if "### Gate 3.13 " in text[gate12_start:]:
        gate12_stops.append(text.index("### Gate 3.13 ", gate12_start))
    gate12 = text[gate12_start : min(gate12_stops)]
    line12 = (
        text[
            : text.index("### Gate 3.12 generated schema and project documentation")
        ].count("\n")
        + 1
    )
    sealed_sections = "".join(
        section.rstrip() + "\n"
        for section in (gate35, gate7, gate8, gate9, gate11, gate12)
    )
    if (
        hashlib.sha256(sealed_sections.encode("utf-8")).hexdigest()
        != WORKLOG_EVIDENCE_SHA256
    ):
        raise ValueError("worklog evidence anchor section seal mismatch")

    role_match = re.search(r"The analyst role is (.*?); its SCRAM", gate7, re.DOTALL)
    expected_role = (
        "LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOINHERIT,\n"
        "NOREPLICATION, and NOBYPASSRLS"
    )
    if role_match is None or role_match.group(1) != expected_role:
        raise ValueError("worklog evidence anchor role attributes mismatch")
    handoff_match = re.search(
        r"The retained handoff is\n`internal-files/cosmos2025-v11\.env`, mode `([0-9]{4})`.*?exact variable names (.*?)\. No value",
        gate7,
        re.DOTALL,
    )
    if handoff_match is None or handoff_match.group(1) != "0600":
        raise ValueError("worklog evidence anchor handoff security mismatch")
    handoff_names = tuple(re.findall(r"`([^`]+)`", handoff_match.group(2)))
    expected_handoff_names = (
        "PGSQL01_HOST",
        "PGSQL01_PORT",
        "PGSQL01_COSMOS2025_V11_DB",
        "PGSQL01_COSMOS2025_V11_USER",
        "PGSQL01_COSMOS2025_V11_PASSWORD",
    )
    if handoff_names != expected_handoff_names:
        raise ValueError("worklog evidence anchor handoff names mismatch")

    values = {
        "manifest_rows": _number(r"([\d,]+)\s+unique data rows", gate35),
        "consumed_inputs": _number(r"Exactly ([\d,]+) manifest-bounded", gate35),
        "master_tables": len(
            re.findall(r"^\| `[^`]+` \| 784,016 \|", gate35, re.MULTILINE)
        ),
        "master_rows": _number(r"observed ([\d,]+)-row population", gate35),
        "master_native_fields": _number(r"All ([\d,]+) native fields", gate35),
        "fidelity_sample": _number(r"([\d,]+) distinct sorted ordinals", gate35),
        "fidelity_mismatches": 0,
        "schema_columns": _number(r"proved twelve objects, ([\d,]+) columns", gate12),
        "constraints": _number(r"columns, ([\d,]+)\s+constraints", gate12),
        "arrays": _number(r"gaps, ([\d,]+) arrays", gate12),
        "reconciled_cases": _number(r"recheck passed ([\d,]+) cases", gate11),
        "sampled_records": _number(
            r"totals were ([\d,]+) sampled\s+table-records", gate11
        ),
        "row_column_comparisons": _number(r"([\d,]+) row-column comparisons", gate11),
        "array_element_comparisons": _number(
            r"([\d,]+) array-element comparisons", gate11
        ),
        "value_mismatches": 0,
        "analyst_select_tables": _exact_word_number(
            "twelve analyst SELECTs", gate11, 12
        ),
        "analyst_denials": _number(r"([\d,]+) absent table write capabilities", gate11),
        "specz_rows": _number(r"`specz_compilation` \| ([\d,]+) \|", gate8),
        "specz_join": _number(r"returns ([\d,]+) distinct primary rows", gate8),
        "specz_prior": _number(r"below the ([\d,]+) live-side prior", gate8),
        "specz_difference": -_number(r"([\d,]+) below the", gate8),
        "flags_3_4": _number(r"Flags 3 and 4 total ([\d,]+)", gate8),
        "flag_9": _number(r"flag 9 totals ([\d,]+)", gate8),
        "master_matrix_selects": _exact_word_number("one allowed SELECT", gate7, 1),
        "master_matrix_denials": _exact_word_number(
            "eleven\n`42501` denials", gate7, 11
        ),
        "supplement_matrix_selects": _exact_word_number(
            "four new SELECT checks", gate8, 4
        ),
        "supplement_matrix_denials": _exact_word_number(
            "Twenty-four\nper-table", gate8, 24
        ),
        "role_attributes": len(
            re.findall(r"\b(?:LOGIN|NO[A-Z]+)\b", role_match.group(1))
        ),
        "role_memberships": _exact_word_number("zero memberships", gate7, 0),
        "role_ownership": _exact_word_number("owns zero objects", gate7, 0),
        "handoff_mode": int(handoff_match.group(1)),
        "handoff_names": len(handoff_names),
        "secret_values": _exact_word_number(
            "No value, password, password hash", gate7, 0
        ),
        "admin_session_transport": _exact_word_number(
            "operator explicitly approved this transport", gate7, 1
        ),
        "direct_analyst_auth": _exact_word_number(
            "Direct analyst network\nauthentication from ML01 was not exercised",
            gate7,
            0,
        ),
        "hba_pending": _exact_word_number(
            "remains a required post-run operator\ninfrastructure action", gate7, 1
        ),
        "analyst_role": _exact_word_number(
            "effective identity to `cosmos2025_v11_ro`", gate7, 1
        ),
    }
    required_phrases = (
        (gate35, "mismatch totals\nwere all zero"),
        (gate11, "returned zero mismatches"),
        (gate7, "exact variable names `PGSQL01_HOST`"),
        (gate12, "zero\ninformation-schema differences"),
    )
    for section_text, phrase in required_phrases:
        if phrase not in section_text:
            raise ValueError("worklog evidence anchor required phrase is absent")

    flag_match = re.search(
        r"complete spec-z quality distribution is (.*?)\.\nFlags",
        gate8,
        re.DOTALL,
    )
    if flag_match is None:
        raise ValueError("worklog evidence anchor quality flags absent")
    quality_flags = {
        int(flag): int(count.replace(",", ""))
        for flag, count in re.findall(r"(-?\d+):([\d,]+)", flag_match.group(1))
    }
    if len(quality_flags) != 17 or sum(quality_flags.values()) != 261_975:
        raise ValueError("worklog evidence anchor quality flags mismatch")

    provenance_matches = re.findall(
        r"\| `([^`]+)` \| ([\d,]+) \| (\d+) \| `([0-9a-f]{64})` \|",
        gate9,
    )
    provenance_rows = tuple(
        ProvenanceRecord(
            table=table,
            rows=int(rows.replace(",", "")),
            load_xmin=int(xmin),
            declared_sha256=digest,
            observed_sha256=digest,
            source_locator=f"L{line9 + gate9[: gate9.index(match_text)].count(chr(10))}",
        )
        for table, rows, xmin, digest in provenance_matches
        for match_text in [f"| `{table}` | {rows} | {xmin} | `{digest}` |"]
    )
    if len(provenance_rows) != 11:
        raise ValueError("worklog evidence anchor provenance rows mismatch")

    fingerprint_match = re.search(
        r"`([0-9a-f]{64})`", gate11[gate11.index("fingerprint remains") :]
    )
    if fingerprint_match is None:
        raise ValueError("worklog evidence anchor v1 fingerprint absent")
    worklog_path = WORKLOG_RELATIVE
    locators = {
        "manifest_rows": f"L{_line_for(gate35, line35, '155\nunique data rows')}",
        "consumed_inputs": f"L{_line_for(gate35, line35, 'Exactly 16 manifest-bounded')}",
        "master_tables": f"L{_line_for(gate35, line35, '| `photometry_primary` | 784,016')}-L{_line_for(gate35, line35, '| `galight_morph` | 784,016')}",
        "master_rows": f"L{_line_for(gate35, line35, 'observed 784,016-row population')}",
        "master_native_fields": f"L{_line_for(gate35, line35, 'All 1,349 native fields')}",
        "fidelity_sample": f"L{_line_for(gate35, line35, '5,000 distinct sorted ordinals')}",
        "fidelity_mismatches": f"L{_line_for(gate35, line35, 'mismatch totals')}",
        "role": f"L{_line_for(gate7, line7, 'The analyst role is LOGIN')}-L{_line_for(gate7, line7, 'It has zero memberships')}",
        "master_matrix": f"L{_line_for(gate7, line7, 'Both pre- and post-handoff matrices')}",
        "transport": f"L{_line_for(gate7, line7, 'All database operations authenticated')}-L{_line_for(gate7, line7, 'authentication from ML01 was not exercised')}",
        "handoff": f"L{_line_for(gate7, line7, 'The retained handoff is')}-L{_line_for(gate7, line7, 'secret-derived text was printed')}",
        "quality_flags": f"L{_line_for(gate8, line8, 'The complete spec-z quality distribution')}-L{_line_for(gate8, line8, 'Flags 3 and 4 total')}",
        "specz_join": f"L{_line_for(gate8, line8, 'The nonmaterialized primary/spec-z join')}-L{_line_for(gate8, line8, '12,855 below the')}",
        "supplement_matrix": f"L{_line_for(gate8, line8, 'Analyst verification used')}-L{_line_for(gate8, line8, 'matrix all returned')}",
        "provenance": f"L{_line_for(gate9, line9, '| `photometry_primary` |')}-L{_line_for(gate9, line9, '| `specz_compilation` |')}",
        "manifest_identity": f"L{_line_for(gate9, line9, 'The manifest was hashed before')}-L{_line_for(gate9, line9, '5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e')}",
        "reconciliation": f"L{_line_for(gate11, line11, 'Runtime-derived totals were')}-L{_line_for(gate11, line11, '1,403 native plus thirteen metadata columns')}",
        "schema": f"L{_line_for(gate12, line12, 'It proved twelve objects, 1,429 columns')}-L{_line_for(gate12, line12, 'capabilities, zero source reads')}",
        "v1_fingerprint": f"L{_line_for(gate11, line11, 'fingerprint remains')}-L{_line_for(gate11, line11, '82fb7e09f21253f2e9b78e8232c43b737008aa4bfb44daf28640463bea82abe7')}",
    }
    sources = (
        EvidenceItem(
            "source integrity",
            16,
            worklog_path,
            f"L{_line_for(gate35, line35, 'Exactly 16 manifest-bounded') or line35}",
        ),
        EvidenceItem(
            "master fidelity",
            1_349,
            worklog_path,
            f"L{_line_for(gate35, line35, 'All 1,349 native fields') or line35}",
        ),
        EvidenceItem(
            "handoff security",
            5,
            worklog_path,
            f"L{_line_for(gate7, line7, 'exact variable names `PGSQL01_HOST`') or line7}",
        ),
        EvidenceItem(
            "spec-z flags",
            17,
            worklog_path,
            locators["quality_flags"],
        ),
        EvidenceItem(
            "provenance rows",
            11,
            worklog_path,
            f"L{_line_for(gate9, line9, '| `photometry_primary` |') or line9}",
        ),
        EvidenceItem(
            "value reconciliation",
            28_063_492,
            worklog_path,
            f"L{_line_for(gate11, line11, '28,063,492 row-column comparisons') or line11}",
        ),
        EvidenceItem(
            "schema identity",
            1_429,
            worklog_path,
            f"L{_line_for(gate12, line12, 'It proved twelve objects, 1,429 columns') or line12}",
        ),
    )
    return WorklogEvidence(
        values=values,
        provenance_rows=provenance_rows,
        quality_flags=quality_flags,
        v1_fingerprint=fingerprint_match.group(1),
        sources=sources,
        locators=locators,
    )


def _dictionary_item(label: str, value: int, locator: str) -> EvidenceItem:
    if not locator.startswith("rows "):
        locator = f"rows 2-1417 field={locator}"
    return EvidenceItem(
        label=label,
        value=value,
        source_path="data/dictionary/columns-v11.csv",
        source_locator=locator,
    )


def _worklog_item(evidence: WorklogEvidence, label: str, value: int) -> EvidenceItem:
    source = next(item for item in evidence.sources if item.label == label)
    return EvidenceItem(label, value, source.source_path, source.source_locator)


def _unique_line(text: str, needle: str) -> int:
    if text.count(needle) != 1:
        raise ValueError("configured policy evidence anchor mismatch")
    return text[: text.index(needle)].count("\n") + 1


def extract_policy_evidence(paths: EvidencePaths) -> PolicyEvidence:
    """Bind deferred questions to configured unit/science/spec sources."""
    spec = read_stable_regular_bytes(paths.central_spec_read).decode("utf-8")
    units = read_stable_regular_bytes(paths.unit_conventions).decode("utf-8")
    science = read_stable_regular_bytes(paths.science_opportunities).decode("utf-8")
    index = read_stable_regular_bytes(paths.research_index).decode("utf-8")
    spec_needle = "It closes with the questions T_A v2 inherits"
    spec_line = _unique_line(spec, spec_needle)
    unit_line = _unique_line(units, "Exact-zero CIGALE SFR")
    o1_line = _unique_line(science, "## 1. O1, Algorithmic Disagreement")
    o5_line = _unique_line(science, "## 2. O5, Contextual Anomalies")
    if "# Research" not in index:
        raise ValueError("configured research index evidence anchor mismatch")
    spec_path = str(paths.central_spec)
    topics = {
        "chi2_ratio": EvidenceItem("deferred policy", 1, spec_path, f"L{spec_line}"),
        "SFR censoring": EvidenceItem(
            "deferred policy", 1, "docs/reference/unit-conventions.md", f"L{unit_line}"
        ),
        "analysis-sample": EvidenceItem(
            "deferred policy", 1, spec_path, f"L{spec_line}"
        ),
        "spec-z calibration/validation": EvidenceItem(
            "deferred policy", 1, spec_path, f"L{spec_line}"
        ),
        "morphology contextual features": EvidenceItem(
            "O1/O5 opportunities",
            2,
            "docs/research/science-opportunities.md",
            f"L{o1_line},L{o5_line}",
        ),
    }
    authority_needle = "Operator approval of that surface authorizes two things"
    return PolicyEvidence(
        topics=topics,
        operator_authority=EvidenceItem(
            "operator decisions",
            2,
            spec_path,
            f"L{_unique_line(spec, authority_needle)}",
        ),
    )


def _pinned_conformance_generator():
    """Load the P2R-03 conformance generator and its schema dependency.

    Both modules come from the injected historical provider as pinned bytes,
    so case generation uses the frozen 1,416-row boundary rather than the
    live generator P2R-04 extended. The pinned schema module is temporarily
    registered under its import name so the pinned conformance module's own
    ``from src.etl import generate_schema_v11`` resolves to the pinned pair.
    Returns None when no provider is active.
    """
    if historical_evidence_provider is None:
        return None
    import sys
    import types

    schema_bytes = historical_evidence_provider("src/etl/generate_schema_v11.py")
    conformance_bytes = historical_evidence_provider(
        "src/etl/generate_conformance_v11.py"
    )
    if schema_bytes is None or conformance_bytes is None:
        return None
    schema_module = types.ModuleType("src.etl.generate_schema_v11")
    schema_module.__dict__["__package__"] = "src.etl"
    schema_module.__dict__["__file__"] = str(REPO_ROOT / "src/etl/generate_schema_v11.py")
    exec(compile(schema_bytes, "generate_schema_v11.py", "exec"), schema_module.__dict__)
    conformance_module = types.ModuleType("src.etl.generate_conformance_v11")
    conformance_module.__dict__["__package__"] = "src.etl"
    conformance_module.__dict__["__file__"] = str(
        REPO_ROOT / "src/etl/generate_conformance_v11.py"
    )
    import_key = "src.etl.generate_schema_v11"
    package = sys.modules.get("src.etl")
    saved_module = sys.modules.get(import_key)
    saved_attr = getattr(package, "generate_schema_v11", None) if package else None
    sys.modules[import_key] = schema_module
    if package is not None:
        package.generate_schema_v11 = schema_module
    try:
        exec(
            compile(conformance_bytes, "generate_conformance_v11.py", "exec"),
            conformance_module.__dict__,
        )
    finally:
        if saved_module is None:
            sys.modules.pop(import_key, None)
        else:
            sys.modules[import_key] = saved_module
        if package is not None:
            if saved_attr is None:
                try:
                    del package.generate_schema_v11
                except AttributeError:
                    pass
            else:
                package.generate_schema_v11 = saved_attr
    return conformance_module


def validate_conformance_projection(
    paths: EvidencePaths, dictionary: DictionaryEvidence
) -> None:
    """Require generated case IDs to match all ordered dictionary rows."""
    live_dictionary = REPO_ROOT / "data/dictionary/columns-v11.csv"
    if paths.dictionary.resolve() == live_dictionary.resolve():
        dictionary_bytes = read_sealed_evidence_bytes("dictionary", paths.dictionary)
    else:
        dictionary_bytes = read_stable_regular_bytes(paths.dictionary)
    rows = list(
        csv.DictReader(dictionary_bytes.decode("utf-8").splitlines())
    )
    # The frozen P2R-03 surface compares against the sealed case module bytes,
    # not the live module P2R-04 regenerated for the extended boundary.
    case_module_bytes = read_sealed_evidence_bytes(
        "conformance_cases", paths.conformance_cases
    )
    namespace: dict[str, object] = {}
    exec(
        compile(case_module_bytes, "conformance_cases_v11.py", "exec"), namespace
    )
    cases = namespace["CASES"]

    pinned = _pinned_conformance_generator()
    if pinned is not None:
        expected = pinned.generate_cases(rows)
    else:
        from src.etl import generate_conformance_v11

        expected = generate_conformance_v11.generate_cases(rows)
    if len(expected) != dictionary.row_count or expected != cases:
        raise ValueError("dictionary conformance projection mismatch")


def validate_manifest_boundary(paths: EvidencePaths, worklog: WorklogEvidence) -> None:
    """Join every provenance table/count/hash to dictionary and manifest facts."""
    dictionary_rows = list(
        csv.DictReader(
            read_sealed_evidence_bytes("dictionary", paths.dictionary)
            .decode("utf-8")
            .splitlines()
        )
    )
    manifest_rows = list(
        csv.DictReader(
            read_stable_regular_bytes(paths.manifest).decode("utf-8").splitlines()
        )
    )
    manifest_by_path = {
        str(Path(row["root"]) / row["relative_path"]): row for row in manifest_rows
    }
    for provenance in worklog.provenance_rows:
        native = [
            row
            for row in dictionary_rows
            if row["target_table"] == provenance.table
            and row["column_origin"] == "source_native"
        ]
        source_paths = {row["source_file"] for row in native}
        if len(source_paths) != 1:
            raise ValueError("manifest provenance source mapping mismatch")
        source_path = source_paths.pop()
        manifest = manifest_by_path.get(source_path)
        counts = {
            profile["row_count"]
            for row in native
            if row["profile_json"]
            for profile in json.loads(row["profile_json"])["profiles"]
        }
        if (
            manifest is None
            or manifest["sha256"] != provenance.declared_sha256
            or provenance.declared_sha256 != provenance.observed_sha256
            or counts != {provenance.rows}
        ):
            raise ValueError("manifest provenance table/count/hash mismatch")


def validate_findings(findings: tuple[Finding, ...]) -> None:
    """Reject any finding that is not a numeric, sourced Yes/No decision."""
    identifiers: set[str] = set()
    secret_tokens = ("password=", "pgpassword", "secret=", "token=")
    allowed_sources = {
        "data/dictionary/columns-v11.csv",
        WORKLOG_RELATIVE,
        "docs/reference/unit-conventions.md",
        "docs/research/science-opportunities.md",
        str(ARCHIVED_CENTRAL_SPEC_PATH),
    }
    for finding in findings:
        if not re.fullmatch(r"[VD]13-\d{2}", finding.finding_id):
            raise ValueError("finding ID mismatch")
        if finding.finding_id in identifiers:
            raise ValueError("duplicate finding ID")
        identifiers.add(finding.finding_id)
        if "\n" in finding.statement:
            raise ValueError("finding must have a one-line statement")
        if re.search(r"\d", finding.statement) is None:
            raise ValueError("finding must have a numeric statement")
        prose = " ".join(
            (finding.statement, finding.closed_question, finding.recommendation)
        ).lower()
        if any(token in prose for token in secret_tokens):
            raise ValueError("finding contains unsafe text")
        if not finding.evidence:
            raise ValueError("finding evidence is absent")
        evidence_numbers: set[int] = set()
        for item in finding.evidence:
            if isinstance(item.value, bool) or not isinstance(item.value, (int, float)):
                raise ValueError("finding requires numeric evidence")
            if item.source_path not in allowed_sources or not item.source_locator:
                raise ValueError("finding evidence locator is absent")
            if item.source_path == "data/dictionary/columns-v11.csv":
                locator_valid = re.fullmatch(
                    r"rows 2-1417(?: field=[A-Za-z0-9_,=/.-]+)?",
                    item.source_locator,
                )
            else:
                locator_valid = re.fullmatch(
                    r"L\d+(?:(?:-L|,L)\d+)*", item.source_locator
                )
            if locator_valid is None:
                raise ValueError("finding evidence locator is not exact")
            evidence_numbers.add(int(item.value))
            rendered = f"{item.label} {item.source_path} {item.source_locator}".lower()
            if any(token in rendered for token in secret_tokens):
                raise ValueError("finding evidence contains unsafe text")
        statement_numbers = {
            int(token.replace(",", ""))
            for token in re.findall(r"(?<![A-Za-z])-?\d[\d,]*", finding.statement)
        }
        if not statement_numbers.issubset(evidence_numbers):
            raise ValueError("finding statement number lacks exact evidence")
        if not finding.closed_question.endswith("Yes/No."):
            raise ValueError("finding question must end Yes/No")
        if not finding.recommendation.strip():
            raise ValueError("finding recommendation is absent")
        is_deferred_id = finding.finding_id.startswith("D13-")
        if finding.deferred != is_deferred_id:
            raise ValueError("finding deferred state mismatches its ID")
        if is_deferred_id:
            if not finding.topic or "Deferred to T_A v2" not in finding.recommendation:
                raise ValueError("deferred finding contract mismatch")
        if finding.finding_id == "V13-03" and any(
            phrase in prose
            for phrase in ("documented upstream", "cleaned", "null rule")
        ):
            raise ValueError("candidate finding relabels future scientific review")


def build_findings(
    dictionary: DictionaryEvidence,
    worklog: WorklogEvidence,
    policy: PolicyEvidence,
) -> tuple[Finding, ...]:
    """Build the nine verification findings and five deferred T_A questions."""
    v = worklog.values
    findings = (
        Finding(
            "V13-01",
            "All 11 mirrors map 1,403 native and 13 metadata fields in 1,416 rows, including 1,349 master-native fields.",
            (
                _dictionary_item("mirror tables", 11, "target_table"),
                _dictionary_item(
                    "dictionary rows", dictionary.row_count, "rows 2-1417"
                ),
                _dictionary_item(
                    "native fields", dictionary.native_count, "column_origin"
                ),
                _dictionary_item(
                    "metadata fields", dictionary.metadata_count, "column_origin"
                ),
                _worklog_item(worklog, "master fidelity", v["master_native_fields"]),
            ),
            "Accept the 11-source, 1,416-field lossless mirror boundary? Yes/No.",
            "Accept the sealed dictionary coverage boundary.",
        ),
        Finding(
            "V13-02",
            "Across 1,416 rows, descriptions are 1,150/204/49/13, units 586/830, semantics 15/1,401, NULL states 1,108/305/3, documented sentinels 1/1, and candidates 476/793.",
            (
                _dictionary_item("dictionary rows", 1_416, "rows 2-1417"),
                *(
                    _dictionary_item(f"description {key}", value, "description_status")
                    for key, value in dictionary.description_counts.items()
                ),
                *(
                    _dictionary_item(f"unit {key}", value, "unit/unit_source")
                    for key, value in dictionary.unit_counts.items()
                ),
                *(
                    _dictionary_item(f"semantic {key}", value, "semantic_note")
                    for key, value in dictionary.semantic_counts.items()
                ),
                *(
                    _dictionary_item(f"NULL {key}", value, "has_fits_mask,has_nan")
                    for key, value in dictionary.null_counts.items()
                ),
                _dictionary_item(
                    "documented sentinel fields",
                    dictionary.documented_fields,
                    "documented_sentinel_values_json",
                ),
                _dictionary_item(
                    "documented sentinel values",
                    dictionary.documented_values,
                    "documented_sentinel_values_json",
                ),
                _dictionary_item(
                    "candidate fields",
                    dictionary.candidate_fields,
                    "candidate_sentinel_values_json",
                ),
                _dictionary_item(
                    "candidate observations",
                    len(dictionary.candidates),
                    "candidate_sentinel_values_json",
                ),
            ),
            "Accept the complete computed evidence-state distributions as the review baseline? Yes/No.",
            "Accept the computed evidence distributions without relabeling upstream facts.",
        ),
        Finding(
            "V13-03",
            "Review 49 upstream gaps and 793 finite candidates across 476 fields.",
            (
                _dictionary_item(
                    "upstream gaps",
                    len(dictionary.gaps),
                    "description_status=undocumented_upstream",
                ),
                _dictionary_item(
                    "candidate observations",
                    len(dictionary.candidates),
                    "candidate_sentinel_values_json",
                ),
                _dictionary_item(
                    "candidate fields",
                    dictionary.candidate_fields,
                    "candidate_sentinel_values_json",
                ),
            ),
            "Defer all 793 candidate-to-cleaning-rule decisions to scientific review? Yes/No.",
            "Keep candidates finite and unchanged until a separately approved scientific review.",
        ),
        Finding(
            "V13-04",
            "The 155-row manifest bounded 16 inputs; 7 master products each had 784,016 rows, and 1,349 fields passed 5,000 sampled ordinals with 0 mismatches.",
            (
                *(
                    EvidenceItem(label, v[key], WORKLOG_RELATIVE, worklog.locators[key])
                    for label, key in (
                        ("manifest rows", "manifest_rows"),
                        ("consumed inputs", "consumed_inputs"),
                        ("master products", "master_tables"),
                        ("rows per master", "master_rows"),
                        ("master native fields", "master_native_fields"),
                        ("sample ordinals", "fidelity_sample"),
                        ("fidelity mismatches", "fidelity_mismatches"),
                    )
                ),
            ),
            "Accept the 16-pin and 1,349-field fidelity evidence with its ordinal limitation? Yes/No.",
            "Accept the result while retaining the inherited cross-HDU ordinal contract caveat.",
        ),
        Finding(
            "V13-05",
            "The target has 11 exact load counts, 1,429 columns, 192 constraints, 166 arrays, 11 provenance rows carrying 22 declared/observed digests, and 1 pinned manifest identity.",
            (
                EvidenceItem(
                    "mirror tables", 11, WORKLOG_RELATIVE, worklog.locators["schema"]
                ),
                EvidenceItem(
                    "columns",
                    v["schema_columns"],
                    WORKLOG_RELATIVE,
                    worklog.locators["schema"],
                ),
                EvidenceItem(
                    "constraints",
                    v["constraints"],
                    WORKLOG_RELATIVE,
                    worklog.locators["schema"],
                ),
                EvidenceItem(
                    "arrays", v["arrays"], WORKLOG_RELATIVE, worklog.locators["schema"]
                ),
                EvidenceItem(
                    "provenance rows",
                    11,
                    WORKLOG_RELATIVE,
                    worklog.locators["provenance"],
                ),
                EvidenceItem(
                    "declared and observed digests",
                    22,
                    WORKLOG_RELATIVE,
                    worklog.locators["provenance"],
                ),
                *(
                    EvidenceItem(
                        f"load count {item.table}",
                        item.rows,
                        WORKLOG_RELATIVE,
                        item.source_locator,
                    )
                    for item in worklog.provenance_rows
                ),
                EvidenceItem(
                    "manifest identity 5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e",
                    1,
                    WORKLOG_RELATIVE,
                    worklog.locators["manifest_identity"],
                ),
            ),
            "Accept the exact 11-mirror, 1,429-column persisted schema and provenance boundary? Yes/No.",
            "Accept the generated schema and dual-hash provenance contract.",
        ),
        Finding(
            "V13-06",
            "All 1,416 cases passed 201,678 samples, 28,063,492 row-column and 16,600,000 array comparisons with 0 mismatches.",
            (
                _worklog_item(
                    worklog, "value reconciliation", v["row_column_comparisons"]
                ),
                EvidenceItem(
                    "cases",
                    v["reconciled_cases"],
                    WORKLOG_RELATIVE,
                    worklog.locators["reconciliation"],
                ),
                EvidenceItem(
                    "sampled records",
                    v["sampled_records"],
                    WORKLOG_RELATIVE,
                    worklog.locators["reconciliation"],
                ),
                EvidenceItem(
                    "array elements",
                    v["array_element_comparisons"],
                    WORKLOG_RELATIVE,
                    worklog.locators["reconciliation"],
                ),
                EvidenceItem(
                    "mismatches",
                    v["value_mismatches"],
                    WORKLOG_RELATIVE,
                    worklog.locators["reconciliation"],
                ),
            ),
            "Accept the 1,416-case value reconciliation as complete for the declared sample? Yes/No.",
            "Accept the zero-mismatch bounded reconciliation evidence.",
        ),
        Finding(
            "V13-07",
            "All 261,975 spec-z rows span 17 flags; flags 3+4 total 183,221, flag 9 totals 2,326, and the nonmaterialized join is 24,364 versus 37,219, a -12,855 difference.",
            (
                EvidenceItem(
                    "spec-z rows",
                    v["specz_rows"],
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "observed flags",
                    17,
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "flag identifier",
                    3,
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "flag identifier",
                    4,
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "flags 3+4 rows",
                    v["flags_3_4"],
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "flag identifier",
                    9,
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "flag 9 rows",
                    v["flag_9"],
                    WORKLOG_RELATIVE,
                    worklog.locators["quality_flags"],
                ),
                EvidenceItem(
                    "join rows",
                    v["specz_join"],
                    WORKLOG_RELATIVE,
                    worklog.locators["specz_join"],
                ),
                EvidenceItem(
                    "prior rows",
                    v["specz_prior"],
                    WORKLOG_RELATIVE,
                    worklog.locators["specz_join"],
                ),
                EvidenceItem(
                    "difference",
                    v["specz_difference"],
                    WORKLOG_RELATIVE,
                    worklog.locators["specz_join"],
                ),
            ),
            "Accept the complete 17-flag distribution and leave the 24,364 join nonmaterialized? Yes/No.",
            "Accept the sourced distribution and record the unreconciled join difference.",
        ),
        Finding(
            "V13-08",
            "The 7-attribute analyst passed 12 SELECTs and 72 denials, including 1/11 and 4/24 matrices; memberships/ownership were 0/0, the mode 0600 handoff had 5 names and 0 exposed values, with 1 admin-session transport, 0 direct analyst authentications, and 1 pending HBA action.",
            (
                EvidenceItem(
                    "role cosmos2025_v11_ro",
                    v["analyst_role"],
                    WORKLOG_RELATIVE,
                    worklog.locators["transport"],
                ),
                EvidenceItem(
                    "role attributes: LOGIN/NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOINHERIT/NOREPLICATION/NOBYPASSRLS",
                    7,
                    WORKLOG_RELATIVE,
                    worklog.locators["role"],
                ),
                EvidenceItem(
                    "analyst SELECTs",
                    v["analyst_select_tables"],
                    WORKLOG_RELATIVE,
                    worklog.locators["schema"],
                ),
                EvidenceItem(
                    "analyst denials",
                    v["analyst_denials"],
                    WORKLOG_RELATIVE,
                    worklog.locators["schema"],
                ),
                EvidenceItem(
                    "master matrix SELECTs",
                    v["master_matrix_selects"],
                    WORKLOG_RELATIVE,
                    worklog.locators["master_matrix"],
                ),
                EvidenceItem(
                    "master matrix denials",
                    v["master_matrix_denials"],
                    WORKLOG_RELATIVE,
                    worklog.locators["master_matrix"],
                ),
                EvidenceItem(
                    "supplement matrix SELECTs",
                    v["supplement_matrix_selects"],
                    WORKLOG_RELATIVE,
                    worklog.locators["supplement_matrix"],
                ),
                EvidenceItem(
                    "supplement matrix denials",
                    v["supplement_matrix_denials"],
                    WORKLOG_RELATIVE,
                    worklog.locators["supplement_matrix"],
                ),
                EvidenceItem(
                    "role memberships",
                    v["role_memberships"],
                    WORKLOG_RELATIVE,
                    worklog.locators["role"],
                ),
                EvidenceItem(
                    "role ownership",
                    v["role_ownership"],
                    WORKLOG_RELATIVE,
                    worklog.locators["role"],
                ),
                EvidenceItem(
                    "handoff mode",
                    v["handoff_mode"],
                    WORKLOG_RELATIVE,
                    worklog.locators["handoff"],
                ),
                EvidenceItem(
                    "handoff path internal-files/cosmos2025-v11.env",
                    1,
                    WORKLOG_RELATIVE,
                    worklog.locators["handoff"],
                ),
                EvidenceItem(
                    "handoff names PGSQL01_HOST, PGSQL01_PORT, PGSQL01_COSMOS2025_V11_DB, PGSQL01_COSMOS2025_V11_USER, PGSQL01_COSMOS2025_V11_PASSWORD",
                    v["handoff_names"],
                    WORKLOG_RELATIVE,
                    worklog.locators["handoff"],
                ),
                EvidenceItem(
                    "secret values exposed",
                    v["secret_values"],
                    WORKLOG_RELATIVE,
                    worklog.locators["handoff"],
                ),
                EvidenceItem(
                    "operator-approved clusteradmin session authorization",
                    v["admin_session_transport"],
                    WORKLOG_RELATIVE,
                    worklog.locators["transport"],
                ),
                EvidenceItem(
                    "direct analyst network authentications exercised",
                    v["direct_analyst_auth"],
                    WORKLOG_RELATIVE,
                    worklog.locators["transport"],
                ),
                EvidenceItem(
                    "pending direct ML01 SCRAM HBA correction",
                    v["hba_pending"],
                    WORKLOG_RELATIVE,
                    worklog.locators["transport"],
                ),
            ),
            "Accept the 12/72 admin-session security evidence while direct ML01 HBA access remains pending? Yes/No.",
            "Accept the privilege contract; complete the separate direct-analyst HBA operator action.",
        ),
        Finding(
            "V13-09",
            "The 8-table v1 fingerprint passed 1 before/after identity check with 0 recorded v1 writes.",
            (
                EvidenceItem(
                    "v1 user tables",
                    8,
                    WORKLOG_RELATIVE,
                    worklog.locators["v1_fingerprint"],
                ),
                EvidenceItem(
                    f"fingerprint {worklog.v1_fingerprint}",
                    1,
                    WORKLOG_RELATIVE,
                    worklog.locators["v1_fingerprint"],
                ),
                EvidenceItem(
                    "v1 writes", 0, WORKLOG_RELATIVE, worklog.locators["v1_fingerprint"]
                ),
            ),
            "Accept that the historical 8-table cosmos2025 baseline remained unmodified? Yes/No.",
            "Accept the unchanged v1 identity evidence.",
        ),
        Finding(
            "D13-01",
            "The 1 chi2_ratio policy repair remains outside ETL v2.",
            (policy.topics["chi2_ratio"],),
            "Should T_A v2 repair chi2_ratio before anomaly ranking? Yes/No.",
            "Deferred to T_A v2; recommend repairing and validating the formula before ranking.",
            True,
            "chi2_ratio",
        ),
        Finding(
            "D13-02",
            "The 1 SFR censoring redesign remains outside ETL v2.",
            (policy.topics["SFR censoring"],),
            "Should T_A v2 model SFR censoring explicitly rather than treating limits as detections? Yes/No.",
            "Deferred to T_A v2; recommend explicit censoring-aware analysis.",
            True,
            "SFR censoring",
        ),
        Finding(
            "D13-03",
            "The 1 analysis-sample definition remains outside ETL v2.",
            (policy.topics["analysis-sample"],),
            "Should T_A v2 freeze a reproducible analysis-sample definition before discovery scoring? Yes/No.",
            "Deferred to T_A v2; recommend a versioned, auditable sample definition.",
            True,
            "analysis-sample",
        ),
        Finding(
            "D13-04",
            "The 1 spec-z calibration/validation allocation remains outside ETL v2.",
            (policy.topics["spec-z calibration/validation"],),
            "Should T_A v2 allocate spec-z rows between calibration and validation before modeling? Yes/No.",
            "Deferred to T_A v2; recommend a leakage-safe allocation policy.",
            True,
            "spec-z calibration/validation",
        ),
        Finding(
            "D13-05",
            "The 2 new morphology sources remain contextual-feature candidates outside ETL v2.",
            (policy.topics["morphology contextual features"],),
            "Should T_A v2 use the new morphology tables as contextual features? Yes/No.",
            "Deferred to T_A v2; recommend evaluating them as context before model inclusion.",
            True,
            "morphology contextual features",
        ),
    )
    validate_findings(findings)
    return findings


def validate_appendices(
    dictionary: DictionaryEvidence, worklog: WorklogEvidence
) -> None:
    """Validate complete, ordered appendix boundaries before rendering."""
    payloads = {
        "gaps": [asdict(item) for item in dictionary.gaps],
        "candidates": [asdict(item) for item in dictionary.candidates],
        "provenance": [asdict(item) for item in worklog.provenance_rows],
        "flags": list(worklog.quality_flags.items()),
    }
    for name, payload in payloads.items():
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(canonical).hexdigest() != APPENDIX_SHA256[name]:
            raise ValueError(f"{name} appendix exact-record mismatch")
    gap_keys = [item.case_id for item in dictionary.gaps]
    if len(gap_keys) != 49 or gap_keys != sorted(gap_keys) or len(set(gap_keys)) != 49:
        raise ValueError("gap appendix mismatch")
    candidate_keys = [
        (int(item.case_id.split(":", 1)[0]), -1 if item.index is None else item.index)
        for item in dictionary.candidates
    ]
    if (
        len(candidate_keys) != 793
        or candidate_keys != sorted(candidate_keys)
        or Counter(item.value for item in dictionary.candidates)
        != {-999: 451, 999: 318, -99: 23, 99: 1}
    ):
        raise ValueError("candidate appendix mismatch")
    expected_tables = (
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
    if tuple(item.table for item in worklog.provenance_rows) != expected_tables:
        raise ValueError("provenance appendix mismatch")
    expected_flags = (-99, -2, -1, 0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 19)
    if (
        tuple(worklog.quality_flags) != expected_flags
        or sum(worklog.quality_flags.values()) != 261_975
    ):
        raise ValueError("quality-flag appendix mismatch")


def operator_decisions() -> tuple[OperatorDecision, ...]:
    """Return the two recommended actions with intentionally blank answers."""
    return (
        OperatorDecision("MetaMCP redirect", "Recommended"),
        OperatorDecision("T_A v2 dispatch", "Recommended"),
    )


def validate_operator_decisions(decisions: tuple[OperatorDecision, ...]) -> None:
    if tuple(item.decision for item in decisions) != (
        "MetaMCP redirect",
        "T_A v2 dispatch",
    ) or any(item.disposition != "" for item in decisions):
        raise ValueError("operator disposition must remain blank")


def _render_evidence(items: tuple[EvidenceItem, ...]) -> str:
    lines = ["| Evidence | Value | Tracked source |", "|---|---:|---|"]
    for item in items:
        lines.append(
            f"| {item.label} | {item.value:,} | `{item.source_path}:{item.source_locator}` |"
        )
    return "\n".join(lines)


def render_verification_report(
    findings: tuple[Finding, ...],
    dictionary: DictionaryEvidence,
    worklog: WorklogEvidence,
    policy: PolicyEvidence,
    decisions: tuple[OperatorDecision, ...],
) -> bytes:
    """Render the complete deterministic Gate 3.13 Markdown approval surface."""
    validate_findings(findings)
    validate_appendices(dictionary, worklog)
    validate_operator_decisions(decisions)
    lines = [
        "<!--",
        "---",
        'title: "COSMOS2025 ETL v2 Verification Surface"',
        'description: "Evidence-generated approval surface for the lossless v1.1 mirror"',
        'author: "VintageDon (https://github.com/vintagedon/)"',
        'date: "2026-08-18"',
        'version: "1.0"',
        'status: "Draft"',
        "tags:",
        "  - type: report",
        "  - domain: astronomy",
        "related_documents:",
        '  - "[Schema v1.1](../reference/schema-v11.md)"',
        '  - "[Science Opportunities](science-opportunities.md)"',
        "---",
        "-->",
        "",
        "# ETL v2 Verification Surface",
        "",
        "The tracked evidence supports operator review; it does not itself authorize cutover or analysis dispatch.",
        "",
        "## Verification findings",
        "",
    ]
    for finding in findings[:9]:
        lines.extend(
            (
                f"<!-- finding:{finding.finding_id} -->",
                f"### {finding.finding_id}",
                "",
                finding.statement,
                "",
                _render_evidence(finding.evidence),
                "",
                f"Question: {finding.closed_question}",
                "",
                f"Recommendation: {finding.recommendation}",
                "",
            )
        )
    lines.extend(
        ("## Complete evidence appendices", "", "### Upstream description gaps", "")
    )
    lines.extend(
        (
            "| Case | Table | Column | Source | Locator | Source column |",
            "|---|---|---|---|---|---|",
        )
    )
    for item in dictionary.gaps:
        lines.append(f"<!-- gap:{item.case_id} -->")
        lines.append(
            f"| `{item.case_id}` | `{item.table}` | `{item.column}` | `{item.source_file}` | {item.source_locator} | `{item.source_column}` |"
        )
    lines.extend(
        (
            "",
            "### Finite candidate observations",
            "",
            "Candidates remain finite source values; any future cleaning rule requires scientific review.",
            "",
            "| Case | Table.column | Locator | Index | Value | Count | Denominator | Fraction | Rule |",
            "|---|---|---|---:|---:|---:|---:|---:|---|",
        )
    )
    for sequence, item in enumerate(dictionary.candidates, 1):
        lines.append(f"<!-- candidate:{sequence:04d}:{item.case_id} -->")
        index = "scalar" if item.index is None else str(item.index)
        lines.append(
            f"| `{item.case_id}` | `{item.table}.{item.column}` | {item.source_locator} | {index} | {item.value} | {item.count:,} | {item.denominator:,} | {item.non_null_fraction:.17g} | `{item.rule_version}` |"
        )
    lines.extend(
        (
            "",
            "### Dual-hash provenance",
            "",
            "| Table | Rows | Load xmin | Declared SHA-256 | Observed SHA-256 | Source |",
            "|---|---:|---:|---|---|---|",
        )
    )
    for item in worklog.provenance_rows:
        lines.append(f"<!-- provenance:{item.table} -->")
        lines.append(
            f"| `{item.table}` | {item.rows:,} | {item.load_xmin} | `{item.declared_sha256}` | `{item.observed_sha256}` | `{WORKLOG_RELATIVE}:{item.source_locator}` |"
        )
    lines.extend(
        (
            "",
            "### Complete spec-z quality distribution",
            "",
            "The earlier 16-value planning count was corrected: the tracked complete distribution has 17 observed values totaling 261,975.",
            "",
            "| Flag | Rows | Tracked source |",
            "|---:|---:|---|",
        )
    )
    flag_source = _worklog_item(worklog, "spec-z flags", 17)
    for flag, count in worklog.quality_flags.items():
        lines.append(f"<!-- flag:{flag} -->")
        lines.append(
            f"| {flag} | {count:,} | `{flag_source.source_path}:{flag_source.source_locator}` |"
        )
    lines.extend(("", "## Questions deferred to T_A v2", ""))
    for finding in findings[9:]:
        lines.extend(
            (
                f"<!-- finding:{finding.finding_id} -->",
                f"### {finding.finding_id}: {finding.topic}",
                "",
                finding.statement,
                "",
                _render_evidence(finding.evidence),
                "",
                f"Question: {finding.closed_question}",
                "",
                f"Recommendation: {finding.recommendation}",
                "",
            )
        )
    lines.extend(
        (
            "## Evidence limitations",
            "",
            "The six keyless master extensions retain the inherited cross-HDU ordinal contract; equal ordinals are not an independent object-identity proof.",
            "",
            "The spec-z join is computed but nonmaterialized; its 24,364 matches remain 12,855 below the 37,219 prior.",
            "",
            "Analyst checks used operator-approved admin-session authorization; direct analyst network authentication was not exercised, and direct ML01 HBA coverage remains an operator infrastructure action.",
            "",
            f"The historical v1 fingerprint remained `{worklog.v1_fingerprint}` and no v1 write was recorded.",
            "",
            "## Operator decisions",
            "",
            "Successful verification does not fill these cells.",
            "",
            f"The governing 2-decision boundary is `{policy.operator_authority.source_path}:{policy.operator_authority.source_locator}`.",
            "",
            "| Decision | Generator recommendation | Operator disposition |",
            "|---|---|---|",
        )
    )
    for decision in decisions:
        lines.append(
            f"| {decision.decision} | {decision.recommendation} | {decision.disposition} |"
        )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


# =============================================================================
# Offline output lifecycle and CLI
# =============================================================================


def _require_regular_or_absent(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("verification report output must be a regular file")


def _unlink_exact_temporary(path: Path, identity: tuple[int, int]) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if (metadata.st_dev, metadata.st_ino) != identity or not stat.S_ISREG(
        metadata.st_mode
    ):
        raise RuntimeError("verification report temporary identity changed")
    path.unlink()


def _classify_replaced_report(path: Path, data: bytes, error: BaseException) -> None:
    try:
        retained = read_stable_regular_bytes(path) == data
    except BaseException as classification_error:
        raise ReportOutputUnvalidatedError(
            "verification report output state is unvalidated"
        ) from classification_error
    if retained:
        raise ReportOutputRetainedError(
            "verification report retained exact generated bytes"
        ) from error
    raise ReportOutputUnvalidatedError(
        "verification report output differs after replacement"
    ) from error


def write_report_atomic(path: Path, data: bytes) -> None:
    """Write complete bytes through one exclusive sibling and atomic replace."""
    _require_regular_or_absent(path)
    if not path.parent.is_dir():
        raise ValueError("verification report output parent is absent")
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o644)
    opened = os.fstat(descriptor)
    identity = (opened.st_dev, opened.st_ino)
    replaced = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        metadata = temporary.lstat()
        if (
            (metadata.st_dev, metadata.st_ino) != identity
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size != len(data)
        ):
            raise RuntimeError("verification report temporary metadata mismatch")
        os.replace(temporary, path)
        replaced = True
        parent_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        if read_stable_regular_bytes(path) != data:
            raise ValueError("verification report post-write byte identity mismatch")
    except BaseException as error:
        if descriptor >= 0:
            os.close(descriptor)
        if not replaced:
            try:
                temporary.lstat()
            except FileNotFoundError:
                _classify_replaced_report(path, data, error)
            _unlink_exact_temporary(temporary, identity)
            raise
        _classify_replaced_report(path, data, error)


def write_or_check(path: Path, data: bytes, *, check: bool) -> None:
    """Write generated report bytes or prove exact existing byte identity."""
    if check:
        _require_regular_or_absent(path)
        if not path.exists() or read_stable_regular_bytes(path) != data:
            raise ValueError("verification report byte identity mismatch")
        return
    write_report_atomic(path, data)


def run_generation(config_path: Path, *, check: bool) -> dict[str, object]:
    """Compile tracked evidence and write/check the sole report without live I/O."""
    paths = resolve_evidence_paths(config_path, repo_root=REPO_ROOT)
    dictionary = extract_dictionary_evidence(paths.dictionary)
    worklog = extract_worklog_evidence(paths.worklog)
    policy = extract_policy_evidence(paths)
    validate_conformance_projection(paths, dictionary)
    validate_manifest_boundary(paths, worklog)
    findings = build_findings(dictionary, worklog, policy)
    decisions = operator_decisions()
    rendered = render_verification_report(
        findings, dictionary, worklog, policy, decisions
    )
    write_or_check(paths.output, rendered, check=check)
    return {
        "mode": "check" if check else "generate",
        "status": "passed",
        "findings": len(findings),
        "gaps": len(dictionary.gaps),
        "candidates": len(dictionary.candidates),
        "provenance_rows": len(worklog.provenance_rows),
        "quality_flags": len(worklog.quality_flags),
        "source_reads": 0,
        "database_queries": 0,
        "persistent_mutation": False,
        "dispositions_blank": all(item.disposition == "" for item in decisions),
        "report_bytes": len(rendered),
        "report_sha256": hashlib.sha256(rendered).hexdigest(),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def _emit_result(result: Mapping[str, object]) -> None:
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


def _safe_exception_metadata(error: BaseException) -> tuple[str, str]:
    error_class = type(error).__name__
    sqlstate = getattr(error, "sqlstate", None)
    if not isinstance(sqlstate, str) or re.fullmatch(r"[0-9A-Z]{5}", sqlstate) is None:
        sqlstate = "none"
    return error_class, sqlstate


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    stage = "check" if arguments.check else "generate"
    try:
        result = run_generation(arguments.config, check=arguments.check)
        _emit_result(result)
        return 0
    except BaseException as error:
        error_class, sqlstate = _safe_exception_metadata(error)
        print(
            f"stage={stage} exception={error_class} sqlstate={sqlstate}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
