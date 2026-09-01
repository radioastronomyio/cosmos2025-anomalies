#!/usr/bin/env python3
"""
Script Name  : test_generate_schema_docs_v11.py
Description  : Test generated ETL v2 schema documentation and live boundaries
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import stat
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import generate_schema_docs_v11 as module  # noqa: E402
from src.etl.conformance_cases_v11 import CASES  # noqa: E402


DICTIONARY_PATH = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"
ASSET_HASHES = {
    "README.md": "2ee5e30fb3313eb770f72ffce5f9783dd2863a93c64f9e66c0707e29d11b8af8",
    "architecture-section-infographic.jpg": "d725e47889c9402c7c788ffa01cd893ccd15d8f7fc89f5f3109adf3b34bfc24c",
    "dataset-composition-section-infographic.jpg": "af5f3cd365bbbcc5178b28ed75bedc3e4a9dc7f9a72a0bfa347d8af407a2b299",
    "icon.svg": "1bfca99860d59c8123a3514fde6d3279ad93b46d5abc5b945f38ee946c735d09",
    "repo-banner.jpg": "d9b16f87dca019f6f0bd27503f63987385b0dd7c680ca4b14c747a2a15d83ea8",
}


def dictionary_rows() -> list[dict[str, str]]:
    """Read the sealed dictionary exactly as the generator consumes it."""
    with DICTIONARY_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def renderer_inputs() -> tuple[
    module.DocumentationContract, module.LiveDocumentationObservation
]:
    """Return a complete pure rendering fixture without PostgreSQL access."""
    contract = module.build_documentation_contract(dictionary_rows())
    observation = module.LiveDocumentationObservation(
        catalog=None,  # type: ignore[arg-type]
        information_schema_columns=(),
        physical_counts=contract.table_row_counts,
    )
    return contract, observation


def complete_catalog_snapshot():
    """Build one exact Gate 3.10-shaped catalog observation."""
    verify = module.verify_conformance_v11
    columns = {
        (case["table"], case["column"]): verify.ColumnObservation(
            target_type=case["target_type"],
            not_null=(
                case["column"] in {"id", "source_row"}
                and case["table"]
                in {
                    "photometry_primary",
                    "photometry_aper",
                    "lephare",
                    "cigale",
                    "ml_morpho",
                    "bulge_disk",
                    "galight_morph",
                }
            ),
            comment=case["comment"],
        )
        for case in CASES
    }
    columns.update(verify.expected_provenance_columns())
    tables = (*verify.MIRROR_TABLES, "provenance")
    counts = module.build_documentation_contract(dictionary_rows()).table_row_counts
    return verify.CatalogSnapshot(
        objects=tuple((table, "r") for table in sorted(tables)),
        columns=columns,
        constraints=verify.expected_constraints(),
        provenance_tables=verify.MIRROR_TABLES,
        provenance_count=12,
        provenance_loaded_rows=counts,
        table_acls={
            table: (True, False, False, False, False, False, False) for table in tables
        },
    )


def complete_information_schema(
    contract: module.DocumentationContract,
) -> tuple[module.InformationSchemaColumn, ...]:
    """Create the literal ordered information-schema boundary by hand."""
    rows: list[module.InformationSchemaColumn] = []
    for table in contract.table_order:
        for ordinal, column in enumerate(
            (item for item in contract.columns if item.row["target_table"] == table),
            start=1,
        ):
            rows.append(
                module.InformationSchemaColumn(
                    table=table,
                    column=column.row["target_identifier"],
                    ordinal=ordinal,
                    data_type=column.row["target_type"],
                )
            )
    for ordinal, field in enumerate(module.generate_schema_v11.PROVENANCE_CONTRACT, 1):
        rows.append(
            module.InformationSchemaColumn(
                table="provenance",
                column=field.name,
                ordinal=ordinal,
                data_type=field.sql_type,
            )
        )
    return tuple(rows)


def complete_live_observation() -> tuple[
    module.DocumentationContract, module.LiveDocumentationObservation
]:
    """Build one complete live boundary with independent expected values."""
    contract = module.build_documentation_contract(dictionary_rows())
    return contract, module.LiveDocumentationObservation(
        catalog=complete_catalog_snapshot(),
        information_schema_columns=complete_information_schema(contract),
        physical_counts=contract.table_row_counts,
    )


class CursorRows:
    """Minimal cursor that returns complete PostgreSQL-shaped rows."""

    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class DocumentationSnapshotConnection:
    """Serve one exact seven-query documentation snapshot and record SQL."""

    def __init__(self, observation: module.LiveDocumentationObservation):
        self.observation = observation
        self.queries: list[str] = []
        self.rollbacks = 0

    def execute(self, query, params=None):
        del params
        text = str(query)
        self.queries.append(text)
        if "SET TRANSACTION" in text:
            return CursorRows([])
        snapshot = self.observation.catalog
        if "catalog_snapshot_objects" in text:
            return CursorRows(list(snapshot.objects))
        if "catalog_snapshot_columns" in text:
            return CursorRows(
                [
                    (table, column, item.target_type, item.not_null, item.comment)
                    for (table, column), item in snapshot.columns.items()
                ]
            )
        if "catalog_snapshot_constraints" in text:
            return CursorRows(list(snapshot.constraints))
        if "catalog_snapshot_provenance" in text:
            return CursorRows(
                [
                    (table, snapshot.provenance_loaded_rows[table])
                    for table in snapshot.provenance_tables
                ]
            )
        if "catalog_snapshot_acls" in text:
            return CursorRows(
                [(table, *values) for table, values in snapshot.table_acls.items()]
            )
        if "documentation_information_schema" in text:
            return CursorRows(
                [
                    (item.table, item.column, item.ordinal, item.data_type)
                    for item in self.observation.information_schema_columns
                ]
            )
        if "documentation_physical_counts" in text:
            return CursorRows(list(self.observation.physical_counts.items()))
        raise AssertionError("unexpected documentation snapshot query")

    def rollback(self):
        self.rollbacks += 1


class ConnectionContext:
    """Context manager preserving one recording connection."""

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        return False


def configure_temp_documentation_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, SimpleNamespace]:
    """Create one exact temporary path contract for orchestration tests."""
    repo_root = tmp_path / "repo"
    dictionary = repo_root / "data/dictionary/columns-v11.csv"
    output = repo_root / "docs/reference/schema-v11.md"
    dictionary.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    dictionary.write_bytes(DICTIONARY_PATH.read_bytes())
    config = tmp_path / "paths.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "dictionary": {
                    "columns_v11": str(dictionary),
                    "schema_v11_docs": str(output),
                }
            }
        ),
        encoding="utf-8",
    )
    settings = SimpleNamespace(target_database="cosmos2025_v11", repo_root=repo_root)
    monkeypatch.setattr(module, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        module.bootstrap_v11, "resolve_settings", lambda _path: settings
    )
    return config, output, settings


def test_field_surface_covers_every_sealed_header_and_rejects_mapping_drift() -> None:
    """Dropping or inventing one field must make schema provenance incomplete."""
    rows = dictionary_rows()
    expected = set(rows[0])
    assert len(expected) == 32
    assert set(module.FIELD_SURFACE) == expected

    missing = dict(module.FIELD_SURFACE)
    missing.pop("semantic_note_locator")
    with pytest.raises(ValueError, match="field surface"):
        module.validate_field_surface(rows, missing)

    extra = dict(module.FIELD_SURFACE)
    extra["invented_field"] = module.FieldSurface("invented", "verbatim")
    with pytest.raises(ValueError, match="field surface"):
        module.validate_field_surface(rows, extra)


def test_documentation_contract_covers_exact_dictionary_boundaries() -> None:
    """A missing/reclassified row must change a hand-checked boundary."""
    contract = module.build_documentation_contract(dictionary_rows())

    assert len(contract.columns) == 1_448
    assert Counter(column.row["target_table"] for column in contract.columns) == {
        "photometry_primary": 288,
        "lephare": 45,
        "photometry_aper": 150,
        "cigale": 58,
        "ml_morpho": 152,
        "bulge_disk": 463,
        "galight_morph": 206,
        "lss_overdensity": 4,
        "galaxy_groups": 14,
        "galaxy_group_memberships": 4,
        "specz_compilation_unique": 32,
        "specz_compilation_all": 32,
    }
    assert Counter(column.row["column_origin"] for column in contract.columns) == {
        "source_native": 1_435,
        "source_row_metadata": 7,
        "id_injected": 6,
    }
    assert len(contract.undocumented_case_ids) == 78
    assert (
        sum(column.row["target_type"].endswith("[]") for column in contract.columns)
        == 166
    )
    assert len(module.generate_schema_v11.PROVENANCE_CONTRACT) == 13


@pytest.mark.parametrize(
    "mutation",
    ("reordered", "element_count", "semantic_evidence", "profile_evidence"),
)
def test_documentation_contract_rejects_any_sealed_row_surface_drift(
    mutation: str,
) -> None:
    """Counts alone cannot authorize reordered or altered dictionary evidence."""
    rows = dictionary_rows()
    if mutation == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "element_count":
        rows[0]["element_count"] = "999"
    elif mutation == "semantic_evidence":
        rows[0]["semantic_note_locator"] += "#drift"
    else:
        payload = json.loads(rows[0]["profile_json"])
        payload["profiles"][0]["finite_max"] += 1
        rows[0]["profile_json"] = json.dumps(payload, separators=(",", ":"))

    with pytest.raises(ValueError, match="seal"):
        module.build_documentation_contract(rows)


def test_profile_evidence_derives_rows_and_nulls_without_relabeling_sentinels() -> None:
    """A finite sentinel must never be described as a mirror NULL encoding."""
    contract = module.build_documentation_contract(dictionary_rows())
    candidates = [
        column
        for column in contract.columns
        if json.loads(column.row["candidate_sentinel_values_json"])
    ]
    assert len(candidates) == 494
    assert all(
        "finite sentinels preserved" in column.null_encoding for column in candidates
    )
    assert contract.table_row_counts == {
        "photometry_primary": 784_016,
        "lephare": 784_016,
        "photometry_aper": 784_016,
        "cigale": 784_016,
        "ml_morpho": 784_016,
        "bulge_disk": 784_016,
        "galight_morph": 784_016,
        "lss_overdensity": 164_155,
        "galaxy_groups": 1_678,
        "galaxy_group_memberships": 1_745_652,
        "specz_compilation_unique": 261_975,
        "specz_compilation_all": 482_579,
    }


def test_renderer_emits_every_ordered_case_and_provenance_field_once() -> None:
    """Omitting or duplicating one column must break the documented schema set."""
    contract, observation = renderer_inputs()
    rendered = module.render_schema_document(contract, observation).decode("utf-8")

    cases = re.findall(r"<!-- schema-case:([^ ]+) -->", rendered)
    provenance = re.findall(r"<!-- provenance-field:([^ ]+) -->", rendered)
    assert len(cases) == len(set(cases)) == 1_448
    assert cases[0] == "0001:photometry_primary.id"
    assert cases[-1] == "1448:specz_compilation_all.groupsize"
    assert provenance == [
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
    ]


def test_renderer_includes_required_contract_sections_and_field_destinations() -> None:
    """Removing a required caveat or evidence surface must make the reference incomplete."""
    contract, observation = renderer_inputs()
    rendered = module.render_schema_document(contract, observation).decode("utf-8")

    for literal in (
        "Provenance contract version 1.0.1",
        "0.2, 0.3, 0.5, 0.75, 1",
        "0.1, 0.25, 0.5, 1.0, 1.5",
        "future `analysis` schema",
        "finite sentinels preserved",
        "upstream ordinal",
        "Lowercase the exact `source_column`",
        "outside `[a-z0-9_]` with one underscore",
        "Prefix `c_`",
        "PostgreSQL Appendix C reserved word",
        "63 UTF-8 bytes",
        "truncation and collision repair are forbidden",
    ):
        assert literal in rendered
    assert rendered.count("<!-- undocumented-upstream:") == 78
    for field, surface in module.FIELD_SURFACE.items():
        assert (
            f"| `{field}` | {surface.destination} | `{surface.transform}` |" in rendered
        )


def test_renderer_accepts_text_and_boolean_profiles_without_numeric_nan_keys() -> None:
    """Treat absent nonnumeric NaN counters as structurally inapplicable, not missing."""
    contract, observation = renderer_inputs()
    rendered = module.render_schema_document(contract, observation).decode("utf-8")

    assert "0003:photometry_primary.tile" in rendered
    assert "0083:photometry_primary.flag_star" in rendered
    assert "kind=text" in rendered
    assert "kind=boolean" in rendered


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("missing", "information-schema"),
        ("extra", "information-schema"),
        ("reordered", "information-schema"),
        ("wrong_type", "information-schema"),
        ("wrong_count", "physical count"),
    ),
)
def test_live_observation_rejects_schema_and_count_drift(
    mutation: str, message: str
) -> None:
    """Any live/document set, order, type, or count drift must halt rendering."""
    contract, observation = complete_live_observation()
    info = list(observation.information_schema_columns)
    counts = dict(observation.physical_counts)
    if mutation == "missing":
        info.pop()
    elif mutation == "extra":
        info.append(module.InformationSchemaColumn("extra", "column", 1, "text"))
    elif mutation == "reordered":
        info[0], info[1] = info[1], info[0]
    elif mutation == "wrong_type":
        info[0] = replace(info[0], data_type="integer")
    else:
        counts["photometry_primary"] += 1
    mutated = replace(
        observation,
        information_schema_columns=tuple(info),
        physical_counts=counts,
    )
    with pytest.raises(ValueError, match=message):
        module.validate_live_observation(contract, mutated)


def test_capture_live_observation_uses_seven_batched_read_queries() -> None:
    """A per-column/count round-trip regression must violate the fixed query budget."""
    contract, expected = complete_live_observation()
    connection = DocumentationSnapshotConnection(expected)

    observed = module.capture_live_observation(connection, contract)

    assert observed == expected
    assert len(connection.queries) == 7
    assert (
        sum("documentation_information_schema" in item for item in connection.queries)
        == 1
    )
    assert (
        sum("documentation_physical_counts" in item for item in connection.queries) == 1
    )
    count_query = connection.queries[-1]
    assert count_query.count("count(*)") == 12
    assert "INSERT" not in count_query.upper()
    assert "UPDATE" not in count_query.upper()
    assert "DELETE" not in count_query.upper()


def test_atomic_writer_and_check_mode_preserve_existing_output_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed fsync/check must not alter the reviewed pre-existing document."""
    output = tmp_path / "schema-v11.md"
    output.write_bytes(b"reviewed-before\n")

    with pytest.raises(ValueError, match="byte identity"):
        module.write_or_check(output, b"different\n", check=True)
    assert output.read_bytes() == b"reviewed-before\n"

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(module.os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="synthetic fsync failure"):
        module.write_document_atomic(output, b"new-complete-bytes\n")
    assert output.read_bytes() == b"reviewed-before\n"
    assert list(tmp_path.glob(".schema-v11.md.*.tmp")) == []


@pytest.mark.parametrize(
    ("stage", "retained"),
    (
        ("write", False),
        ("flush", False),
        ("replace", False),
        ("replace_return", True),
        ("parent_fsync", True),
        ("post_read", True),
    ),
)
def test_atomic_writer_classifies_every_failure_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    retained: bool,
) -> None:
    """Every injected writer failure must have one exact output state."""
    output = tmp_path / "schema-v11.md"
    output.write_bytes(b"reviewed-before\n")
    generated = b"generated-complete\n"
    real_fdopen = module.os.fdopen

    class FailingFile:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            self.handle.__enter__()
            return self

        def __exit__(self, exc_type, exc, traceback):
            return self.handle.__exit__(exc_type, exc, traceback)

        def write(self, data):
            if stage == "write":
                raise OSError("synthetic write failure")
            return self.handle.write(data)

        def flush(self):
            if stage == "flush":
                raise OSError("synthetic flush failure")
            return self.handle.flush()

        def fileno(self):
            return self.handle.fileno()

    monkeypatch.setattr(
        module.os,
        "fdopen",
        lambda descriptor, mode: FailingFile(real_fdopen(descriptor, mode)),
    )
    if stage == "replace":
        monkeypatch.setattr(
            module.os,
            "replace",
            lambda *_args: (_ for _ in ()).throw(OSError("synthetic replace failure")),
        )
    elif stage == "replace_return":
        real_replace = module.os.replace

        def replace_then_fail(source, destination):
            real_replace(source, destination)
            raise OSError("synthetic replace-return failure")

        monkeypatch.setattr(module.os, "replace", replace_then_fail)
    elif stage == "parent_fsync":
        fsync_calls = 0

        def fail_parent_fsync(_descriptor):
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == 2:
                raise OSError("synthetic parent fsync failure")

        monkeypatch.setattr(module.os, "fsync", fail_parent_fsync)
    elif stage == "post_read":
        real_read = module._read_regular_bytes
        read_calls = 0

        def fail_first_read(path):
            nonlocal read_calls
            read_calls += 1
            if read_calls == 1:
                raise OSError("synthetic post-read failure")
            return real_read(path)

        monkeypatch.setattr(module, "_read_regular_bytes", fail_first_read)

    expected_error = module.DocumentationOutputRetainedError if retained else OSError
    with pytest.raises(expected_error):
        module.write_document_atomic(output, generated)
    assert output.read_bytes() == (generated if retained else b"reviewed-before\n")
    assert list(tmp_path.glob(".schema-v11.md.*.tmp")) == []


def test_atomic_writer_marks_post_replace_state_unvalidated_when_recheck_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unverifiable committed inode must never look like a pre-replace failure."""
    output = tmp_path / "schema-v11.md"
    output.write_bytes(b"reviewed-before\n")
    monkeypatch.setattr(module, "_read_regular_bytes", lambda _path: b"drifted")

    with pytest.raises(module.DocumentationOutputUnvalidatedError):
        module.write_document_atomic(output, b"generated-complete\n")
    assert list(tmp_path.glob(".schema-v11.md.*.tmp")) == []


def test_gate312_call_graph_has_no_source_reader_or_sql_write_surface() -> None:
    """Documentation generation is catalog-read-only and never opens holdings."""
    source = (REPO_ROOT / "src/etl/generate_schema_docs_v11.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imported.intersection(
        {"astropy", "astropy.io.fits", "numpy", "pandas", "pyarrow"}
    )
    sql_text = "\n".join(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    assert (
        re.search(
            r"\b(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|ALTER|DROP|GRANT|REVOKE|COPY)\b",
            sql_text,
            re.IGNORECASE,
        )
        is None
    )
    run_source = ast.unparse(
        next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run_generate_check"
        )
    )
    assert "verify_source_fidelity" not in run_source
    assert "reconcile_values_v11" not in run_source


def test_atomic_writer_rejects_symlink_and_writes_regular_bytes(tmp_path: Path) -> None:
    """Following a final-path symlink or leaving nonregular output is forbidden."""
    target = tmp_path / "outside.md"
    target.write_bytes(b"outside\n")
    linked = tmp_path / "schema-v11.md"
    linked.symlink_to(target)
    with pytest.raises(ValueError, match="regular file"):
        module.write_document_atomic(linked, b"must-not-follow\n")
    assert target.read_bytes() == b"outside\n"

    output = tmp_path / "new-schema.md"
    module.write_document_atomic(output, b"generated\n")
    observed = output.lstat()
    assert stat.S_ISREG(observed.st_mode)
    assert output.read_bytes() == b"generated\n"
    module.write_or_check(output, b"generated\n", check=True)


@pytest.mark.parametrize(
    "mutation", ("wrong_dictionary", "wrong_output", "symlink", "dangling_symlink")
)
def test_configured_paths_reject_drift_and_unsafe_final_targets(
    tmp_path: Path, mutation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configuration cannot redirect sealed input or generated output."""
    dictionary = tmp_path / "data/dictionary/columns-v11.csv"
    output = tmp_path / "docs/reference/schema-v11.md"
    dictionary.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    configured_dictionary = dictionary
    configured_output = output
    if mutation == "wrong_dictionary":
        configured_dictionary = tmp_path / "other.csv"
    elif mutation == "wrong_output":
        configured_output = tmp_path / "other.md"
    elif mutation == "symlink":
        target = tmp_path / "outside.md"
        target.write_bytes(b"outside\n")
        output.symlink_to(target)
    else:
        output.symlink_to(tmp_path / "absent.md")
    config = tmp_path / "paths.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "dictionary": {
                    "columns_v11": str(configured_dictionary),
                    "schema_v11_docs": str(configured_output),
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    with pytest.raises(ValueError, match="documentation (dictionary|output)"):
        module._configured_paths(config, SimpleNamespace(repo_root=tmp_path))


def test_run_generate_check_uses_one_read_only_connection_and_closes_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dropping transaction or after-identity checks must fail orchestration evidence."""
    contract, expected = complete_live_observation()
    connection = DocumentationSnapshotConnection(expected)
    repo_root = tmp_path / "repo"
    dictionary = repo_root / "data/dictionary/columns-v11.csv"
    output = repo_root / "docs/reference/schema-v11.md"
    dictionary.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    dictionary.write_bytes(DICTIONARY_PATH.read_bytes())
    config = tmp_path / "paths.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "dictionary": {
                    "columns_v11": str(dictionary),
                    "schema_v11_docs": str(output),
                }
            }
        ),
        encoding="utf-8",
    )
    settings = SimpleNamespace(target_database="cosmos2025_v11", repo_root=repo_root)
    protected = object()
    identities: list[object] = []
    monkeypatch.setattr(
        module.bootstrap_v11, "resolve_settings", lambda _path: settings
    )
    monkeypatch.setattr(module, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_connect",
        lambda observed, database: ConnectionContext(connection),
    )

    def identity(observed):
        identities.append(observed)
        return protected

    monkeypatch.setattr(module.verify_conformance_v11, "_protected_identity", identity)

    result = module.run_generate_check(config, check=False)

    assert output.read_bytes() == module.render_schema_document(contract, expected)
    assert len(connection.queries) == 8
    assert "REPEATABLE READ" in connection.queries[0]
    assert "READ ONLY" in connection.queries[0]
    assert connection.rollbacks == 1
    assert identities == [settings, settings]
    assert result["information_schema_diff"] == 0
    assert result["documented_mirror_columns"] == 1_448
    assert result["protected_identity_unchanged"] is True


def test_check_mode_compares_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A check-only invocation must succeed against read-only artifact permissions."""
    contract, expected = complete_live_observation()
    repo_root = tmp_path / "repo"
    dictionary = repo_root / "data/dictionary/columns-v11.csv"
    output = repo_root / "docs/reference/schema-v11.md"
    dictionary.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    dictionary.write_bytes(DICTIONARY_PATH.read_bytes())
    output.write_bytes(module.render_schema_document(contract, expected))
    output.chmod(0o444)
    config = tmp_path / "paths.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "dictionary": {
                    "columns_v11": str(dictionary),
                    "schema_v11_docs": str(output),
                }
            }
        ),
        encoding="utf-8",
    )
    connection = DocumentationSnapshotConnection(expected)
    settings = SimpleNamespace(target_database="cosmos2025_v11", repo_root=repo_root)
    monkeypatch.setattr(
        module.bootstrap_v11, "resolve_settings", lambda _path: settings
    )
    monkeypatch.setattr(module, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_connect",
        lambda *_args: ConnectionContext(connection),
    )
    monkeypatch.setattr(
        module.verify_conformance_v11, "_protected_identity", lambda _settings: "same"
    )

    result = module.run_generate_check(config, check=True)

    assert result["mode"] == "check"
    assert stat.S_IMODE(output.stat().st_mode) == 0o444


@pytest.mark.parametrize("after_failure", ("drift", "exception"))
def test_identity_failure_precedes_any_document_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, after_failure: str
) -> None:
    """A failed after-identity observation must leave reviewed bytes untouched."""
    contract, observation = complete_live_observation()
    del contract
    connection = DocumentationSnapshotConnection(observation)
    config, output, _settings = configure_temp_documentation_repo(tmp_path, monkeypatch)
    output.write_bytes(b"reviewed-before\n")
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_connect",
        lambda *_args: ConnectionContext(connection),
    )
    calls = 0

    def identity(_observed):
        nonlocal calls
        calls += 1
        if calls == 1:
            return "before"
        if after_failure == "exception":
            raise RuntimeError("synthetic after-identity failure")
        return "after"

    monkeypatch.setattr(module.verify_conformance_v11, "_protected_identity", identity)

    with pytest.raises((RuntimeError, ValueError)):
        module.run_generate_check(config, check=False)
    assert calls == 2
    assert output.read_bytes() == b"reviewed-before\n"


@pytest.mark.parametrize("failure", ("connect", "catalog", "render"))
def test_every_live_or_render_failure_still_performs_after_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """The protected bracket must close without touching output on every failure."""
    _contract, observation = complete_live_observation()
    connection = DocumentationSnapshotConnection(observation)
    config, output, _settings = configure_temp_documentation_repo(tmp_path, monkeypatch)
    output.write_bytes(b"reviewed-before\n")
    identities: list[str] = []
    monkeypatch.setattr(
        module.verify_conformance_v11,
        "_protected_identity",
        lambda _settings: identities.append("observed") or "same",
    )
    if failure == "connect":
        monkeypatch.setattr(
            module.bootstrap_v11,
            "_connect",
            lambda *_args: (_ for _ in ()).throw(RuntimeError("connect failure")),
        )
    else:
        monkeypatch.setattr(
            module.bootstrap_v11,
            "_connect",
            lambda *_args: ConnectionContext(connection),
        )
        target = (
            "capture_live_observation"
            if failure == "catalog"
            else "render_schema_document"
        )
        monkeypatch.setattr(
            module,
            target,
            lambda *_args: (_ for _ in ()).throw(RuntimeError(f"{failure} failure")),
        )

    with pytest.raises(RuntimeError, match=failure):
        module.run_generate_check(config, check=False)
    assert identities == ["observed", "observed"]
    assert output.read_bytes() == b"reviewed-before\n"


def test_cli_redacts_failure_text_and_success_rendering_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Neither loader failures nor BrokenPipe details may escape the CLI boundary."""
    monkeypatch.setattr(
        module,
        "run_generate_check",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("analyst-secret immutable-source-value")
        ),
    )
    assert module.main([]) == 1
    first = capsys.readouterr()
    assert "RuntimeError" in first.err
    assert "analyst-secret" not in first.err
    assert "immutable-source-value" not in first.err

    monkeypatch.setattr(
        module, "run_generate_check", lambda *_args, **_kwargs: {"ok": True}
    )
    monkeypatch.setattr(
        module,
        "_emit_result",
        lambda _result: (_ for _ in ()).throw(BrokenPipeError("row-value")),
    )
    assert module.main([]) == 1
    second = capsys.readouterr()
    assert "BrokenPipeError" in second.err
    assert "row-value" not in second.err


def test_direct_file_help_reaches_cli_without_database_access() -> None:
    """Removing direct-entry path setup must break the supported script invocation."""
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "src/etl/generate_schema_docs_v11.py"),
            "--help",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--check" in result.stdout


def test_direct_entrypoint_follows_every_function_and_class_definition() -> None:
    """Default direct execution must not call main before renderers exist."""
    source = (REPO_ROOT / "src/etl/generate_schema_docs_v11.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    entrypoints = [
        (index, statement)
        for index, statement in enumerate(tree.body)
        if isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and ast.unparse(statement.test) == "__name__ == '__main__'"
    ]
    assert len(entrypoints) == 1
    index, entrypoint = entrypoints[0]
    assert index == len(tree.body) - 1
    assert all(
        statement.lineno < entrypoint.lineno
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )


def test_all_asset_paths_and_bytes_remain_exact_while_root_uses_supplied_icon() -> None:
    """Deleting/restyling any asset or presenting a stale diagram must fail."""
    assets = REPO_ROOT / "assets"
    observed = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in assets.iterdir()
        if path.is_file()
    }
    assert observed == ASSET_HASHES
    icon = assets / "icon.svg"
    assert icon.stat().st_size == 1_205

    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    image_paths = re.findall(r"!\[[^]]*\]\(([^)]+)\)", root_readme)
    assert "assets/icon.svg" in image_paths
    assert "assets/repo-banner.jpg" not in image_paths
    assert "assets/architecture-section-infographic.jpg" not in image_paths
    assert "assets/dataset-composition-section-infographic.jpg" not in image_paths


def test_runtime_config_separates_v1_baseline_v11_runtime_and_admin_bootstrap() -> None:
    """Conflating analyst runtime with bootstrap admin credentials must fail."""
    config = yaml.safe_load(
        (REPO_ROOT / "configs/data_paths.yaml").read_text(encoding="utf-8")
    )
    database = config["database"]
    assert database["baseline_v1"] == {
        "database_name": "cosmos2025",
        "schema": "catalog",
        "access": "read_only",
    }
    assert database["runtime_v11"] == {
        "host_env": "PGSQL01_HOST",
        "port_env": "PGSQL01_PORT",
        "database_env": "PGSQL01_COSMOS2025_V11_DB",
        "user_env": "PGSQL01_COSMOS2025_V11_USER",
        "password_env": "PGSQL01_COSMOS2025_V11_PASSWORD",
        "database_name": "cosmos2025_v11",
        "schema": "source",
        "access": "read_only",
    }
    assert database["user_env"] == "PGSQL01_ADMIN_USER"
    assert database["password_env"] == "PGSQL01_ADMIN_PASSWORD"
    assert database["database_name"] == "cosmos2025"
    assert database["target_database"] == "cosmos2025_v11"


@pytest.mark.parametrize(
    ("path", "required"),
    (
        (
            "AGENTS.md",
            ("/opt/agents/repos/spec", "FITS masks and NaN", "finite sentinel"),
        ),
        ("README.md", ("cosmos2025_v11", "seven", "spec-z", "MetaMCP", "T_A v2")),
        (
            "docs/project-state.md",
            (
                "cosmos2025_v11",
                "source.provenance",
                "MetaMCP",
                "T_A v2",
                "/opt/agents/repos/spec",
                "archive/index",
            ),
        ),
        ("spec/README.md", ("/opt/agents/repos/spec", "dispatch authority", "archive")),
        (
            "configs/README.md",
            ("PGSQL01_COSMOS2025_V11_DB", "bootstrap", "read-only"),
        ),
        ("docs/reference/README.md", ("schema-v11.md", "generated", "1,448")),
        ("src/etl/README.md", ("generate_schema_docs_v11.py", "one", "read-only")),
        ("tests/README.md", ("test_generate_schema_docs_v11.py", "1,448", "assets")),
    ),
)
def test_operational_orientation_surfaces_agree(
    path: str, required: tuple[str, ...]
) -> None:
    """Leaving one public router on the retired v1 posture must fail agreement."""
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    for literal in required:
        assert literal in text, f"{path} lacks {literal}"


def test_specz_config_records_materialized_gate35_pinned_input() -> None:
    """The runtime config must not retain the retired LFS-pointer warning."""
    text = (REPO_ROOT / "configs/data_paths.yaml").read_text(encoding="utf-8")
    specz = text.split("\nspecz:\n", 1)[1].split("\n# ETL output", 1)[0]
    assert "materialized" in specz
    assert "Gate 3.5" in specz
    assert "SHA-256-pinned" in specz
    assert "pointer files" not in specz
