#!/usr/bin/env python3
"""
Script Name  : generate_schema_docs_v11.py
Description  : Generate the verified ETL v2 schema reference
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Builds a deterministic schema-documentation contract from the sealed v1.1
dictionary. Live PostgreSQL observation and output orchestration are added by
the same Gate 3.12 contract without reading immutable source artifacts.
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
import stat
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import (  # noqa: E402
    bootstrap_v11,
    generate_conformance_v11,
    generate_schema_v11,
    verify_conformance_v11,
)
from src.etl.conformance_cases_v11 import CASES  # noqa: E402


# =============================================================================
# Fixed presentation contract
# =============================================================================

ALLOWED_TRANSFORMS = {
    "verbatim",
    "evidence_cell",
    "null_encoding",
    "profile_evidence",
    "section",
}
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
SEALED_ROWS_SHA256 = "7ac2b647835ef6dbc03f8ebc845b291790ad70472a5293c88b8f514b68f947ed"
SEALED_CSV_SHA256 = "a20457c8c5c1785ebce0442a17c1fa06bdef9c1300c199d21776f7c0d22cfcd5"


@dataclass(frozen=True)
class FieldSurface:
    """One sealed dictionary field's explicit documentation destination."""

    destination: str
    transform: str


FIELD_SURFACE: Mapping[str, FieldSurface] = {
    "source_family": FieldSurface("source identity", "verbatim"),
    "source_file": FieldSurface("source artifact", "verbatim"),
    "source_locator": FieldSurface("source locator", "verbatim"),
    "source_column": FieldSurface("source column", "verbatim"),
    "source_type": FieldSurface("source type", "verbatim"),
    "element_count": FieldSurface("shape", "verbatim"),
    "target_table": FieldSurface("table section", "section"),
    "target_identifier": FieldSurface("target column", "verbatim"),
    "target_type": FieldSurface("target type", "verbatim"),
    "column_origin": FieldSurface("origin", "verbatim"),
    "description_text": FieldSurface("description", "evidence_cell"),
    "description_source": FieldSurface("description evidence", "evidence_cell"),
    "description_locator": FieldSurface("description evidence", "evidence_cell"),
    "description_source_sha256": FieldSurface("description evidence", "evidence_cell"),
    "description_status": FieldSurface("description status", "evidence_cell"),
    "unit": FieldSurface("unit", "evidence_cell"),
    "unit_source": FieldSurface("unit evidence", "evidence_cell"),
    "unit_locator": FieldSurface("unit evidence", "evidence_cell"),
    "unit_source_sha256": FieldSurface("unit evidence", "evidence_cell"),
    "semantic_note": FieldSurface("semantic note", "evidence_cell"),
    "semantic_note_source": FieldSurface("semantic evidence", "evidence_cell"),
    "semantic_note_locator": FieldSurface("semantic evidence", "evidence_cell"),
    "semantic_note_source_sha256": FieldSurface("semantic evidence", "evidence_cell"),
    "profile_json": FieldSurface("profile-derived evidence", "profile_evidence"),
    "has_fits_mask": FieldSurface("NULL encoding", "null_encoding"),
    "has_nan": FieldSurface("NULL encoding", "null_encoding"),
    "documented_sentinel_values_json": FieldSurface(
        "documented sentinel", "evidence_cell"
    ),
    "documented_sentinel_evidence_text": FieldSurface(
        "documented sentinel evidence", "evidence_cell"
    ),
    "documented_sentinel_source": FieldSurface(
        "documented sentinel evidence", "evidence_cell"
    ),
    "documented_sentinel_locator": FieldSurface(
        "documented sentinel evidence", "evidence_cell"
    ),
    "documented_sentinel_source_sha256": FieldSurface(
        "documented sentinel evidence", "evidence_cell"
    ),
    "candidate_sentinel_values_json": FieldSurface(
        "candidate sentinels", "evidence_cell"
    ),
}


@dataclass(frozen=True)
class DocumentationColumn:
    """One ordered dictionary row prepared for documentation rendering."""

    case_id: str
    row: Mapping[str, str]
    row_count: int
    null_encoding: str


@dataclass(frozen=True)
class DocumentationContract:
    """Complete immutable schema-documentation input derived from the seal."""

    columns: tuple[DocumentationColumn, ...]
    table_order: tuple[str, ...]
    table_row_counts: Mapping[str, int]
    undocumented_case_ids: tuple[str, ...]


@dataclass(frozen=True)
class InformationSchemaColumn:
    """One ordered live information_schema column observation."""

    table: str
    column: str
    ordinal: int
    data_type: str


@dataclass(frozen=True)
class LiveDocumentationObservation:
    """Bounded live evidence supplied to the pure document renderer."""

    catalog: verify_conformance_v11.CatalogSnapshot
    information_schema_columns: tuple[InformationSchemaColumn, ...]
    physical_counts: Mapping[str, int]


class DocumentationOutputRetainedError(RuntimeError):
    """A post-replace failure left the exact generated bytes in place."""


class DocumentationOutputUnvalidatedError(RuntimeError):
    """A post-replace failure left output identity impossible to prove."""


def validate_field_surface(
    rows: Sequence[Mapping[str, str]],
    surface: Mapping[str, FieldSurface] = FIELD_SURFACE,
) -> None:
    """Require one explicit, valid destination for every sealed CSV field."""
    if not rows:
        raise ValueError("field surface requires dictionary rows")
    headers = set(rows[0])
    if any(set(row) != headers for row in rows) or set(surface) != headers:
        raise ValueError("field surface does not match sealed dictionary headers")
    if any(
        not item.destination.strip() or item.transform not in ALLOWED_TRANSFORMS
        for item in surface.values()
    ):
        raise ValueError("field surface contains an invalid destination")


def _sealed_boolean(row: Mapping[str, str], field: str) -> bool:
    """Parse one exact title-case boolean from the sealed dictionary."""
    value = row[field]
    if value not in {"True", "False"}:
        raise ValueError(f"invalid sealed boolean: {field}")
    return value == "True"


def _profile_row_count(row: Mapping[str, str]) -> int | None:
    """Return one native field's exact population from its sealed profiles."""
    payload = row["profile_json"]
    if not payload:
        if row["column_origin"] == "source_native":
            raise ValueError("native dictionary row lacks profile evidence")
        return None
    try:
        profiles = json.loads(payload)["profiles"]
        counts = {profile["row_count"] for profile in profiles}
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed profile evidence") from exc
    if (
        not profiles
        or len(counts) != 1
        or any(not isinstance(count, int) or count < 0 for count in counts)
    ):
        raise ValueError("profile row-count mismatch")
    return counts.pop()


def _null_encoding(row: Mapping[str, str]) -> str:
    """Describe only the two source-mirror NULL encodings authorized by spec."""
    encodings: list[str] = []
    if _sealed_boolean(row, "has_fits_mask"):
        encodings.append("FITS mask")
    if _sealed_boolean(row, "has_nan"):
        encodings.append("NaN")
    observed = " + ".join(encodings) if encodings else "none observed"
    return f"{observed}; finite sentinels preserved"


def _validate_sealed_dictionary_rows(rows: Sequence[Mapping[str, str]]) -> None:
    """Bind all ordered row fields to the sealed artifact and tracked cases."""
    serializable = [dict(row) for row in rows]
    canonical = json.dumps(
        serializable,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != SEALED_ROWS_SHA256:
        raise ValueError("documentation dictionary seal mismatch")
    if generate_conformance_v11.generate_cases(serializable) != CASES:
        raise ValueError("documentation conformance seal mismatch")


def build_documentation_contract(
    rows: Sequence[Mapping[str, str]],
) -> DocumentationContract:
    """Build the exact 1,448-case documentation contract from sealed rows."""
    validate_field_surface(rows)
    _validate_sealed_dictionary_rows(rows)
    if len(rows) != 1_448:
        raise ValueError("documentation dictionary row boundary mismatch")
    table_order = tuple(generate_schema_v11.MIRROR_TABLE_ORDER)
    expected_tables = set(table_order)
    if {row["target_table"] for row in rows} != expected_tables:
        raise ValueError("documentation table boundary mismatch")

    observed_counts: dict[str, set[int]] = {table: set() for table in table_order}
    origins: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()
    prepared: list[tuple[str, Mapping[str, str], int | None, str]] = []
    for index, row in enumerate(rows, start=1):
        key = (row["target_table"], row["target_identifier"])
        if key in seen:
            raise ValueError("duplicate documentation column")
        seen.add(key)
        count = _profile_row_count(row)
        if count is not None:
            observed_counts[key[0]].add(count)
        origins[row["column_origin"]] += 1
        prepared.append(
            (f"{index:04d}:{key[0]}.{key[1]}", row, count, _null_encoding(row))
        )

    if origins != {
        "source_native": 1_435,
        "source_row_metadata": 7,
        "id_injected": 6,
    }:
        raise ValueError("documentation origin boundary mismatch")
    if any(len(counts) != 1 for counts in observed_counts.values()):
        raise ValueError("documentation table profile count mismatch")
    table_row_counts = {table: observed_counts[table].pop() for table in table_order}
    columns = tuple(
        DocumentationColumn(
            case_id=case_id,
            row=row,
            row_count=count
            if count is not None
            else table_row_counts[row["target_table"]],
            null_encoding=null_encoding,
        )
        for case_id, row, count, null_encoding in prepared
    )
    undocumented = tuple(
        column.case_id
        for column in columns
        if column.row["description_status"] == "undocumented_upstream"
    )
    if len(undocumented) != 78:
        raise ValueError("undocumented-upstream boundary mismatch")
    return DocumentationContract(
        columns=columns,
        table_order=table_order,
        table_row_counts=table_row_counts,
        undocumented_case_ids=undocumented,
    )


def _expected_information_schema(
    contract: DocumentationContract,
) -> tuple[InformationSchemaColumn, ...]:
    """Return the exact ordered live-column boundary represented by the document."""
    expected: list[InformationSchemaColumn] = []
    for table in contract.table_order:
        table_columns = (
            column for column in contract.columns if column.row["target_table"] == table
        )
        for ordinal, column in enumerate(table_columns, start=1):
            expected.append(
                InformationSchemaColumn(
                    table=table,
                    column=column.row["target_identifier"],
                    ordinal=ordinal,
                    data_type=column.row["target_type"],
                )
            )
    expected.extend(
        InformationSchemaColumn(
            table="provenance",
            column=field.name,
            ordinal=ordinal,
            data_type=field.sql_type,
        )
        for ordinal, field in enumerate(generate_schema_v11.PROVENANCE_CONTRACT, 1)
    )
    return tuple(expected)


def validate_live_observation(
    contract: DocumentationContract,
    observation: LiveDocumentationObservation,
) -> dict[str, int]:
    """Require exact catalog, information-schema, and physical-count agreement."""
    conformance = verify_conformance_v11.validate_snapshot(CASES, observation.catalog)
    if observation.information_schema_columns != _expected_information_schema(contract):
        raise ValueError("information-schema/document column diff is nonempty")
    if dict(observation.physical_counts) != dict(contract.table_row_counts):
        raise ValueError("physical count differs from sealed profile")
    if dict(observation.catalog.provenance_loaded_rows) != dict(
        observation.physical_counts
    ):
        raise ValueError("physical count differs from provenance registration")
    return {
        **conformance,
        "documented_mirror_columns": len(contract.columns),
        "documented_provenance_fields": len(generate_schema_v11.PROVENANCE_CONTRACT),
        "physical_counts": len(observation.physical_counts),
        "information_schema_diff": 0,
    }


def _information_schema_query(contract: DocumentationContract) -> str:
    """Return one ordered, canonical information-schema observation query."""
    order = " ".join(
        f"WHEN '{table}' THEN {index}"
        for index, table in enumerate((*contract.table_order, "provenance"), 1)
    )
    return f"""
        /* documentation_information_schema */
        SELECT table_name, column_name, ordinal_position,
               CASE
                 WHEN data_type='ARRAY' AND udt_name='_float8'
                   THEN 'double precision[]'
                 WHEN data_type='ARRAY' AND udt_name='_float4'
                   THEN 'real[]'
                 ELSE data_type
               END AS canonical_type
        FROM information_schema.columns
        WHERE table_schema='source'
        ORDER BY CASE table_name {order} ELSE 999 END, ordinal_position
    """


def _physical_count_query(contract: DocumentationContract) -> str:
    """Return one fixed-table UNION query for all twelve exact physical counts."""
    statements = [
        "SELECT '{}'::text AS table_name, count(*)::bigint AS row_count "
        'FROM "source".{}'.format(table, generate_schema_v11.quote_identifier(table))
        for table in contract.table_order
    ]
    return "/* documentation_physical_counts */\n" + "\nUNION ALL\n".join(statements)


def capture_live_observation(
    connection: object,
    contract: DocumentationContract,
) -> LiveDocumentationObservation:
    """Capture and validate the full documentation boundary in seven queries."""
    catalog = verify_conformance_v11.capture_catalog_snapshot(connection)
    information_rows = connection.execute(
        _information_schema_query(contract)
    ).fetchall()
    information_schema_columns = tuple(
        InformationSchemaColumn(table, column, ordinal, data_type)
        for table, column, ordinal, data_type in information_rows
    )
    physical_counts = dict(
        connection.execute(_physical_count_query(contract)).fetchall()
    )
    observation = LiveDocumentationObservation(
        catalog=catalog,
        information_schema_columns=information_schema_columns,
        physical_counts=physical_counts,
    )
    validate_live_observation(contract, observation)
    return observation


# =============================================================================
# Exact output lifecycle
# =============================================================================


def _require_regular_or_absent(path: Path) -> None:
    """Reject a symlink or nonregular pre-existing documentation target."""
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError("documentation output must be an exact regular file")


def _read_regular_bytes(path: Path) -> bytes:
    """Read one exact regular inode without following a final-path symlink."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("documentation output must be an exact regular file")
        blocks: list[bytes] = []
        while block := os.read(descriptor, 1024 * 1024):
            blocks.append(block)
        final = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
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
        raise ValueError("documentation output identity changed during read")
    return b"".join(blocks)


def _unlink_exact_temporary(path: Path, identity: tuple[int, int]) -> None:
    """Remove only the exact run-owned temporary inode after failure."""
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return
    if (observed.st_dev, observed.st_ino) != identity or not stat.S_ISREG(
        observed.st_mode
    ):
        raise RuntimeError("documentation temporary identity changed")
    path.unlink()


def _raise_committed_output_state(
    path: Path, data: bytes, error: BaseException
) -> None:
    """Classify an ambiguous or known post-replace failure without retrying."""
    try:
        retained = _read_regular_bytes(path) == data
    except BaseException as classification_error:
        raise DocumentationOutputUnvalidatedError(
            "documentation output state is unvalidated"
        ) from classification_error
    if retained:
        raise DocumentationOutputRetainedError(
            "documentation output retained exact generated bytes"
        ) from error
    raise DocumentationOutputUnvalidatedError(
        "documentation output differs after replacement"
    ) from error


def write_document_atomic(path: Path, data: bytes) -> None:
    """Write complete bytes through one exclusive sibling and atomic replace."""
    _require_regular_or_absent(path)
    if not path.parent.is_dir():
        raise ValueError("documentation output parent is absent")
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
        observed = temporary.lstat()
        if (
            (observed.st_dev, observed.st_ino) != identity
            or not stat.S_ISREG(observed.st_mode)
            or observed.st_size != len(data)
        ):
            raise RuntimeError("documentation temporary metadata mismatch")
        os.replace(temporary, path)
        replaced = True
        parent_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        if _read_regular_bytes(path) != data:
            raise ValueError("documentation post-write byte identity mismatch")
    except BaseException as error:
        if descriptor >= 0:
            os.close(descriptor)
        if not replaced:
            try:
                temporary.lstat()
            except FileNotFoundError:
                _raise_committed_output_state(path, data, error)
            _unlink_exact_temporary(temporary, identity)
            raise
        _raise_committed_output_state(path, data, error)


def write_or_check(path: Path, data: bytes, *, check: bool) -> None:
    """Atomically write generated bytes or prove an exact existing artifact."""
    if check:
        _require_regular_or_absent(path)
        if not path.exists() or _read_regular_bytes(path) != data:
            raise ValueError("documentation byte identity mismatch")
        return
    write_document_atomic(path, data)


# =============================================================================
# Guarded live orchestration and CLI
# =============================================================================


def _configured_paths(
    config_path: Path, settings: bootstrap_v11.Settings
) -> tuple[Path, Path]:
    """Require the exact repo seal and generated-document destination."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        dictionary = config["dictionary"]
        dictionary_path = Path(dictionary["columns_v11"])
        output_path = Path(dictionary["schema_v11_docs"])
    except (KeyError, TypeError) as exc:
        raise ValueError("missing schema-documentation path configuration") from exc
    repo_root = Path(settings.repo_root)
    if repo_root.resolve(strict=True) != REPO_ROOT.resolve(strict=True):
        raise ValueError("documentation dictionary repository boundary mismatch")
    expected_dictionary = repo_root / "data/dictionary/columns-v11.csv"
    if dictionary_path != expected_dictionary:
        raise ValueError("documentation dictionary path mismatch")
    try:
        dictionary_metadata = dictionary_path.lstat()
    except FileNotFoundError as exc:
        raise ValueError("documentation dictionary is absent") from exc
    if not stat.S_ISREG(dictionary_metadata.st_mode):
        raise ValueError("documentation dictionary must be an exact regular file")
    if (
        hashlib.sha256(_read_regular_bytes(dictionary_path)).hexdigest()
        != SEALED_CSV_SHA256
    ):
        raise ValueError("documentation dictionary seal mismatch")
    expected_output = repo_root / "docs/reference/schema-v11.md"
    if output_path != expected_output:
        raise ValueError("documentation output path mismatch")
    try:
        parent_metadata = output_path.parent.lstat()
    except FileNotFoundError as exc:
        raise ValueError("documentation output parent is absent") from exc
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise ValueError("documentation output parent must be an exact directory")
    _require_regular_or_absent(output_path)
    return dictionary_path, output_path


def _read_dictionary(path: Path) -> list[dict[str, str]]:
    """Read the configured sealed CSV without opening any source artifact."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_generate_check(config_path: Path, *, check: bool) -> dict[str, object]:
    """Generate or check documentation from one protected read-only observation."""
    settings = bootstrap_v11.resolve_settings(config_path)
    dictionary_path, output_path = _configured_paths(config_path, settings)
    contract = build_documentation_contract(_read_dictionary(dictionary_path))
    before = verify_conformance_v11._protected_identity(settings)
    pending_error: BaseException | None = None
    rendered: bytes | None = None
    result: dict[str, object] | None = None
    try:
        with bootstrap_v11._connect(settings, settings.target_database) as connection:
            try:
                connection.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
                )
                observation = capture_live_observation(connection, contract)
            finally:
                connection.rollback()
        rendered = render_schema_document(contract, observation)
        result = {
            "mode": "check" if check else "generate_check",
            "status": "passed",
            "document": str(output_path),
            "document_bytes": len(rendered),
            "document_sha256": hashlib.sha256(rendered).hexdigest(),
            **validate_live_observation(contract, observation),
            "undocumented_upstream": len(contract.undocumented_case_ids),
            "array_columns": sum(
                column.row["target_type"].endswith("[]") for column in contract.columns
            ),
            "protected_identity_unchanged": True,
            "persistent_mutation": False,
            "source_reads": 0,
        }
    except BaseException as error:
        pending_error = error

    after = verify_conformance_v11._protected_identity(settings)
    if after != before:
        raise ValueError("protected identity changed during documentation generation")
    if pending_error is not None:
        raise pending_error.with_traceback(pending_error.__traceback__)
    if rendered is None or result is None:
        raise RuntimeError("documentation result is absent")
    write_or_check(output_path, rendered, check=check)
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse config-driven generate or non-writing check mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def _emit_result(result: Mapping[str, object]) -> None:
    """Emit only allowlisted, value-free JSON evidence."""
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the guarded CLI with class/SQLSTATE-only failure diagnostics."""
    arguments = parse_args(argv)
    stage = "check" if arguments.check else "generate_check"
    try:
        result = run_generate_check(arguments.config, check=arguments.check)
        _emit_result(result)
        return 0
    except BaseException as error:
        error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
        print(
            f"stage={stage} exception={error_class} sqlstate={sqlstate}",
            file=sys.stderr,
        )
        return 1


# =============================================================================
# Deterministic Markdown rendering
# =============================================================================


def _markdown_cell(value: object) -> str:
    """Escape one value for a stable single-line Markdown table cell."""
    text = str(value) if value not in {None, ""} else "[not documented]"
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("`", "&#96;")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )


def _evidence_cell(text: str, source: str, locator: str, source_sha256: str) -> str:
    """Render separate evidence fields without composing new source prose."""
    return "<br>".join(
        (
            _markdown_cell(text),
            f"source={_markdown_cell(source)}",
            f"locator={_markdown_cell(locator)}",
            f"sha256={_markdown_cell(source_sha256)}",
        )
    )


def _profile_evidence(row: Mapping[str, str], row_count: int) -> str:
    """Transform profile JSON into bounded exact evidence plus its byte digest."""
    payload = row["profile_json"]
    if not payload:
        return f"rows={row_count}; project metadata; profile=[not applicable]"
    parsed = json.loads(payload)
    profiles = parsed["profiles"]
    indices = [profile["index"] for profile in profiles]
    mask_count = sum(profile["fits_mask_count"] for profile in profiles)
    nan_count = sum(profile.get("nan_count", 0) for profile in profiles)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return (
        f"rows={row_count}; kind={parsed['kind']}; profiles={len(profiles)}; "
        f"indices={json.dumps(indices, separators=(',', ':'))}; "
        f"fits_mask_count={mask_count}; nan_count={nan_count}; "
        f"profile_sha256={digest}"
    )


def _source_cell(row: Mapping[str, str]) -> str:
    """Render all five source identity fields together."""
    return "<br>".join(
        (
            f"family={_markdown_cell(row['source_family'])}",
            f"file={_markdown_cell(row['source_file'])}",
            f"locator={_markdown_cell(row['source_locator'])}",
            f"column={_markdown_cell(row['source_column'])}",
            f"type={_markdown_cell(row['source_type'])}",
        )
    )


def _documented_sentinel_cell(row: Mapping[str, str]) -> str:
    """Render documented sentinel values and all independent evidence fields."""
    return "<br>".join(
        (
            f"values={_markdown_cell(row['documented_sentinel_values_json'])}",
            f"evidence={_markdown_cell(row['documented_sentinel_evidence_text'])}",
            f"source={_markdown_cell(row['documented_sentinel_source'])}",
            f"locator={_markdown_cell(row['documented_sentinel_locator'])}",
            f"sha256={_markdown_cell(row['documented_sentinel_source_sha256'])}",
        )
    )


def _render_field_surface() -> list[str]:
    """Render the machine-validated mapping for every sealed dictionary field."""
    lines = [
        "## Dictionary field surface",
        "",
        "Every sealed CSV field has one explicit presentation destination or named transformation.",
        "",
        "| Dictionary field | Documentation destination | Transform |",
        "|------------------|---------------------------|-----------|",
    ]
    lines.extend(
        f"| `{field}` | {surface.destination} | `{surface.transform}` |"
        for field, surface in FIELD_SURFACE.items()
    )
    lines.append("")
    return lines


def _render_provenance_contract() -> list[str]:
    """Render the fixed project-infrastructure table separately from mirrors."""
    lines = [
        "## Provenance infrastructure",
        "",
        "`source.provenance` is project infrastructure, not a thirteenth source mirror. "
        f"Provenance contract version {generate_schema_v11.PROVENANCE_CONTRACT_VERSION} "
        "contains thirteen fields and one registered row for each of the twelve mirrors.",
        "",
        "| Field | PostgreSQL type | Nullable | Primary key | Check | Comment |",
        "|-------|-----------------|----------|-------------|-------|---------|",
    ]
    for field in generate_schema_v11.PROVENANCE_CONTRACT:
        lines.append(f"<!-- provenance-field:{field.name} -->")
        lines.append(
            "| `{}` | `{}` | {} | {} | {} | {} |".format(
                field.name,
                field.sql_type,
                "yes" if field.nullable else "no",
                "yes" if field.primary_key else "no",
                _markdown_cell(field.check_expression),
                _markdown_cell(field.comment),
            )
        )
    lines.append("")
    return lines


def _render_gap_inventory(contract: DocumentationContract) -> list[str]:
    """Render every exact upstream description gap as a reviewable inventory."""
    by_id = {column.case_id: column for column in contract.columns}
    lines = [
        "## Upstream documentation gaps",
        "",
        "Exactly 49 mirror columns remain `undocumented_upstream`; names, units, "
        "and meanings were not inferred.",
        "",
        "| Case | Target | Source column | Source artifact | Locator |",
        "|------|--------|---------------|-----------------|---------|",
    ]
    for case_id in contract.undocumented_case_ids:
        column = by_id[case_id]
        row = column.row
        lines.append(f"<!-- undocumented-upstream:{case_id} -->")
        lines.append(
            f"| `{case_id}` | `{row['target_table']}.{row['target_identifier']}` | "
            f"{_markdown_cell(row['source_column'])} | "
            f"{_markdown_cell(row['source_file'])} | "
            f"{_markdown_cell(row['source_locator'])} |"
        )
    lines.append("")
    return lines


def _render_table(
    table: str,
    columns: Sequence[DocumentationColumn],
    row_count: int,
) -> list[str]:
    """Render one complete ordered mirror listing with every required surface."""
    artifacts = sorted({column.row["source_file"] for column in columns})
    locators = sorted({column.row["source_locator"] for column in columns})
    lines = [
        f"## `source.{table}`",
        "",
        f"Rows: **{row_count:,}**. Columns: **{len(columns):,}**.",
        "",
        "Source artifacts: " + "; ".join(f"`{item}`" for item in artifacts) + ".",
        "",
        "Source locators: " + "; ".join(f"`{item}`" for item in locators) + ".",
        "",
        "| Case / target | Source identity | Origin | Target type | Elements | Unit evidence | Description evidence | Semantic evidence | NULL / profile evidence | Documented sentinel evidence | Candidate sentinels |",
        "|---------------|-----------------|--------|-------------|---------:|---------------|----------------------|-------------------|-------------------------|------------------------------|---------------------|",
    ]
    for column in columns:
        row = column.row
        lines.append(f"<!-- schema-case:{column.case_id} -->")
        unit = _evidence_cell(
            row["unit"],
            row["unit_source"],
            row["unit_locator"],
            row["unit_source_sha256"],
        )
        description = "<br>".join(
            (
                _evidence_cell(
                    row["description_text"],
                    row["description_source"],
                    row["description_locator"],
                    row["description_source_sha256"],
                ),
                f"status={_markdown_cell(row['description_status'])}",
            )
        )
        semantic = _evidence_cell(
            row["semantic_note"],
            row["semantic_note_source"],
            row["semantic_note_locator"],
            row["semantic_note_source_sha256"],
        )
        profile = "<br>".join(
            (
                column.null_encoding,
                _profile_evidence(row, column.row_count),
                f"has_fits_mask={row['has_fits_mask']}; has_nan={row['has_nan']}",
            )
        )
        lines.append(
            "| `{case}`<br>`{target}` | {source} | `{origin}` | `{target_type}` | "
            "{elements} | {unit} | {description} | {semantic} | {profile} | "
            "{documented} | {candidate} |".format(
                case=column.case_id,
                target=row["target_identifier"],
                source=_source_cell(row),
                origin=row["column_origin"],
                target_type=row["target_type"],
                elements=row["element_count"],
                unit=unit,
                description=description,
                semantic=semantic,
                profile=profile,
                documented=_documented_sentinel_cell(row),
                candidate=_markdown_cell(row["candidate_sentinel_values_json"]),
            )
        )
    lines.append("")
    return lines


def render_schema_document(
    contract: DocumentationContract,
    observation: LiveDocumentationObservation,
) -> bytes:
    """Render the complete verified schema reference as deterministic bytes."""
    if dict(observation.physical_counts) != dict(contract.table_row_counts):
        raise ValueError("documentation physical count mismatch")
    columns_by_table = {
        table: tuple(
            column for column in contract.columns if column.row["target_table"] == table
        )
        for table in contract.table_order
    }
    lines = [
        "<!--",
        "---",
        'title: "COSMOS-Web v1.1 Source Mirror Schema"',
        'description: "Generated field-complete reference for the verified ETL v2 PostgreSQL mirror"',
        'author: "VintageDon (https://github.com/vintagedon/)"',
        'date: "2026-08-18"',
        'version: "1.0"',
        'status: "Active"',
        "tags:",
        "  - type: reference",
        "  - domain: data-engineering",
        "  - domain: cosmos-web",
        "  - tech: postgresql",
        "related_documents:",
        '  - "[Reference Index](README.md)"',
        '  - "[Project State](../project-state.md)"',
        '  - "[Dictionary Contract](../../data/dictionary/README.md)"',
        "---",
        "-->",
        "",
        "# COSMOS-Web v1.1 Source Mirror Schema",
        "",
        "Generated from the sealed 1,448-row dictionary and a verified live "
        "`cosmos2025_v11.source` catalog observation. The twelve mirror tables "
        "are lossless source representations after declared target casting. "
        "Cleaned, expanded, or science-derived products belong in a future "
        "`analysis` schema.",
        "",
        "Only FITS masks and NaN become SQL NULL. Every finite sentinel remains "
        "a source value unless a future analysis contract explicitly changes it.",
        "",
        "## Mirror boundary",
        "",
        "| Table | Rows | Columns |",
        "|-------|-----:|--------:|",
    ]
    for table in contract.table_order:
        lines.append(
            f"| `source.{table}` | {observation.physical_counts[table]:,} | "
            f"{len(columns_by_table[table]):,} |"
        )
    lines.extend(
        (
            "",
            "## Spec-z compilation boundary",
            "",
            "The Khostovan et al. compilation ships two distinct upstream "
            "products, mirrored as two distinct tables with their own "
            "provenance rows. `source.specz_compilation_all` is the "
            "measurement-level artifact (`specz_compilation_COSMOS_DR1.1_all.fits`, "
            "482,579 rows, one row per redshift measurement). "
            "`source.specz_compilation_unique` is the galaxy-level artifact "
            "(`specz_compilation_COSMOS_DR1.1_unique.fits`, 261,975 rows, one "
            "row per spectroscopic source after deduplication by the highest "
            "quality flag, ties to the most recent redshift; definition at the "
            "pinned checkout `specz_compilation/README.md`, List of Surveys "
            "section, SHA-256 "
            "`43992cf6a30d5893d9421dd1d0b837e1f8dc4975a92e8372ba8cb3b7be78d0c1`). "
            "Both artifacts are shipped upstream; neither is derived in this "
            "repository. The observed relationship, measured at spec P2R-04 "
            "gate 4.1 from the pinned artifacts, is full row-and-column "
            "equality between the galaxy-level table and the measurement-level "
            "rows at `Priority = 1` (column sets identical; positional "
            "per-column value equality including masks and NaN). The catalog "
            "column `id_specz_khostovan25` does not resolve against either "
            "artifact's `Id_specz` namespace; see the semantic note on "
            "`photometry_primary.id_specz_khostovan25` and the review surface "
            "`docs/research/specz-linkage-evidence.md`.",
            "",
            "## Identifier and relational metadata contract",
            "",
            "Every listing places the exact source column beside its PostgreSQL "
            "target identifier, including all punctuation and case mappings. "
            "Normalization follows the frozen Gate 3.1 contract:",
            "",
            "1. Lowercase the exact `source_column`.",
            "2. Replace every maximal run outside `[a-z0-9_]` with one underscore.",
            "3. Prefix `c_` when the result does not begin with `[a-z_]` or equals "
            "a PostgreSQL Appendix C reserved word.",
            "4. Halt on an invalid result, a duplicate table/target pair, or an "
            "identifier longer than 63 UTF-8 bytes. PostgreSQL truncation and "
            "collision repair are forbidden; identifiers are never hand-disambiguated.",
            "",
            "The authorized metadata names are explicit rather than normalized. Seven "
            "master tables carry a zero-based `source_row`; the other six master "
            "extensions receive primary-photometry `id` at the same upstream ordinal. "
            "This injected-ID contract depends on the verified cross-HDU upstream ordinal "
            "alignment and is not an independent source-key join.",
            "",
            "## Array index to aperture mapping",
            "",
            "Primary-photometry five-element aperture vectors use index order "
            "**0.2, 0.3, 0.5, 0.75, 1** arcsecond diameter, sourced from "
            "`cosmosweb-dr1-detailed-column-descriptions.txt` section 1 descriptions.",
            "",
            "SE++ aperture-photometry five-element vectors use index order "
            "**0.1, 0.25, 0.5, 1.0, 1.5** arcsecond diameter, sourced from "
            "`cosmosweb-dr1-detailed-column-descriptions.txt` section 3 descriptions.",
            "",
        )
    )
    lines.extend(_render_field_surface())
    lines.extend(_render_provenance_contract())
    lines.extend(_render_gap_inventory(contract))
    for table in contract.table_order:
        lines.extend(
            _render_table(
                table,
                columns_by_table[table],
                observation.physical_counts[table],
            )
        )
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    raise SystemExit(main())
