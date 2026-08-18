#!/usr/bin/env python3
"""
Script Name  : test_verify_conformance_v11.py
Description  : Test batched ETL v2 dictionary conformance verification
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises the Gate 3.10 local validator against complete catalog snapshots so
every generated dictionary case is checked without a database round trip.

Usage
-----
    pytest tests/test_verify_conformance_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import importlib.util
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "verify_conformance_v11.py"
CASES_PATH = REPO_ROOT / "src" / "etl" / "conformance_cases_v11.py"
LIVE_COUNTS = {
    "photometry_primary": 784_016,
    "photometry_aper": 784_016,
    "lephare": 784_016,
    "cigale": 784_016,
    "ml_morpho": 784_016,
    "bulge_disk": 784_016,
    "galight_morph": 784_016,
    "lss_overdensity": 164_155,
    "galaxy_groups": 1_678,
    "galaxy_group_memberships": 1_745_652,
    "specz_compilation": 261_975,
}


# =============================================================================
# Test utilities
# =============================================================================


def _load(path: Path, name: str):
    """Load one production module after test start."""
    assert path.exists(), f"required Gate 3.10 module is missing: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _module():
    return _load(MODULE_PATH, "verify_conformance_v11")


def _cases():
    return _load(CASES_PATH, "conformance_cases_v11_for_test").CASES


def _complete_snapshot(module, cases):
    """Create a complete observed-catalog fixture from public case contracts."""
    columns = {
        (case["table"], case["column"]): module.ColumnObservation(
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
        for case in cases
    }
    columns.update(module.expected_provenance_columns())
    tables = (*module.MIRROR_TABLES, "provenance")
    return module.CatalogSnapshot(
        objects=tuple((table, "r") for table in sorted(tables)),
        columns=columns,
        constraints=module.expected_constraints(),
        provenance_tables=module.MIRROR_TABLES,
        provenance_count=11,
        provenance_loaded_rows=LIVE_COUNTS,
        table_acls={
            table: (True, False, False, False, False, False, False) for table in tables
        },
    )


class _Cursor:
    """Minimal catalog cursor double returning complete PostgreSQL-shaped rows."""

    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _SnapshotConnection:
    """Return one complete fixture while recording the bounded query count."""

    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.queries: list[str] = []

    def execute(self, query, params=None):
        del params
        sql_text = str(query)
        self.queries.append(sql_text)
        if "catalog_snapshot_objects" in sql_text:
            return _Cursor(list(self.snapshot.objects))
        if "catalog_snapshot_columns" in sql_text:
            return _Cursor(
                [
                    (table, column, value.target_type, value.not_null, value.comment)
                    for (table, column), value in self.snapshot.columns.items()
                ]
            )
        if "catalog_snapshot_constraints" in sql_text:
            return _Cursor(list(self.snapshot.constraints))
        if "catalog_snapshot_provenance" in sql_text:
            return _Cursor(
                [
                    (name, self.snapshot.provenance_loaded_rows[name])
                    for name in self.snapshot.provenance_tables
                ]
            )
        if "catalog_snapshot_acls" in sql_text:
            return _Cursor(
                [(table, *values) for table, values in self.snapshot.table_acls.items()]
            )
        raise AssertionError("unexpected catalog snapshot query")

    def rollback(self):
        return None


class _ConnectionContext:
    """Context manager for the one live snapshot connection."""

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        return False


class _MutationConnection:
    """Transactional scratch double exposing comment/type mutation state."""

    def __init__(self):
        self.state = "baseline"
        self.rollbacks = 0
        self.commits = 0

    def execute(self, statement, params=None):
        del params
        text = str(statement)
        if text.startswith("COMMENT ON COLUMN"):
            self.state = "comment"
        elif text.startswith("ALTER TABLE"):
            self.state = "type"
        return _Cursor([])

    def rollback(self):
        self.state = "baseline"
        self.rollbacks += 1

    def commit(self):
        self.state = "baseline"
        self.commits += 1


class _AmbiguousCreateContext:
    """Simulate CREATE success followed by connection-context exit failure."""

    def __init__(self):
        self.autocommit = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        raise RuntimeError("ambiguous close")

    def execute(self, statement, params=None):
        del params
        if "SELECT EXISTS" in str(statement):
            return _CursorWithOne((False,))
        return _Cursor([])


class _CursorWithOne(_Cursor):
    def fetchone(self):
        return self._rows


# =============================================================================
# Complete snapshot contract
# =============================================================================


def test_complete_snapshot_validates_every_explicit_case_once() -> None:
    """Skipping any generated row assertion must change the reported boundary."""
    module = _module()
    cases = _cases()
    report = module.validate_snapshot(cases, _complete_snapshot(module, cases))

    assert report == {
        "case_assertions": 1_416,
        "master_native": 1_349,
        "supplement_native": 22,
        "specz_native": 32,
        "metadata": 13,
        "native_total": 1_403,
        "array_assertions": 166,
        "objects": 12,
        "columns": 1_429,
        "constraints": 192,
        "provenance_rows": 11,
        "analyst_select_tables": 12,
        "analyst_denied_capabilities": 72,
    }


def test_runtime_constraint_contract_uses_generated_cases_not_a_default_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A different cwd/default path must not decouple live checks from cases."""
    module = _module()
    monkeypatch.chdir(tmp_path)

    assert len(module.expected_constraints()) == 192


def test_array_case_element_count_is_bound_to_named_dimension_constraint() -> None:
    """Changing only a case's array cardinality must fail its explicit assertion."""
    module = _module()
    cases = list(deepcopy(_cases()))
    snapshot = _complete_snapshot(module, cases)
    array_case = next(case for case in cases if case["array_constraint_name"])
    array_case["element_count"] += 1

    with pytest.raises(ValueError, match="array element-count mismatch"):
        module.validate_snapshot(cases, snapshot)


def test_count_preserving_origin_and_group_swaps_fail_per_case() -> None:
    """Global origin/group totals must not hide wrong per-column evidence."""
    module = _module()
    cases = deepcopy(_cases())
    snapshot = _complete_snapshot(module, cases)
    first = next(
        case
        for case in cases
        if case["table"] == "photometry_primary" and case["column"] == "source_row"
    )
    second = next(
        case for case in cases if case["table"] == "lephare" and case["column"] == "id"
    )
    first["column_origin"], second["column_origin"] = (
        second["column_origin"],
        first["column_origin"],
    )
    with pytest.raises(ValueError, match="conformance origin mismatch"):
        module.validate_snapshot(cases, snapshot)

    cases = deepcopy(_cases())
    master = next(case for case in cases if case["case_group"] == "master_native")
    supplement = next(
        case for case in cases if case["case_group"] == "supplement_native"
    )
    master["case_group"], supplement["case_group"] = (
        supplement["case_group"],
        master["case_group"],
    )
    with pytest.raises(ValueError, match="conformance case-group mismatch"):
        module.validate_snapshot(cases, _complete_snapshot(module, cases))


@pytest.mark.parametrize(
    "mutation",
    ("reorder", "duplicate_id", "table", "column", "array_name", "array_expression"),
)
def test_explicit_case_identity_and_array_mutations_fail(mutation: str) -> None:
    """Row order/identity and both named array fields must remain exact."""
    module = _module()
    cases = list(deepcopy(_cases()))
    snapshot = _complete_snapshot(module, cases)
    if mutation == "reorder":
        cases[0], cases[1] = cases[1], cases[0]
        message = "generated case identity mismatch"
    elif mutation == "duplicate_id":
        cases[1]["case_id"] = cases[0]["case_id"]
        message = "generated case boundary mismatch"
    elif mutation == "table":
        cases[0]["table"] = "lephare"
        message = "generated case identity mismatch"
    elif mutation == "column":
        cases[0]["column"] = "segment_id"
        message = "generated case identity mismatch"
    else:
        array_case = next(case for case in cases if case["array_constraint_name"])
        if mutation == "array_name":
            array_case["array_constraint_name"] = "wrong_array_check"
            message = "array constraint mismatch"
        else:
            array_case["array_constraint_expression"] += " AND false"
            message = "array constraint mismatch"
    with pytest.raises(ValueError, match=message):
        module.validate_snapshot(cases, snapshot)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("type", "conformance type mismatch"),
        ("comment", "conformance comment mismatch"),
        ("object_missing", "source object boundary mismatch"),
        ("object_extra", "source object boundary mismatch"),
        ("constraint_missing", "source constraint boundary mismatch"),
        ("constraint_extra", "source constraint boundary mismatch"),
        ("provenance_set", "provenance row coverage mismatch"),
        ("provenance_count", "provenance row coverage mismatch"),
        ("provenance_contract", "provenance column contract mismatch"),
        ("acl", "analyst table ACL boundary mismatch"),
        ("origin", "generated column-origin boundary mismatch"),
    ),
)
def test_snapshot_boundary_mutations_fail_exactly(mutation: str, message: str) -> None:
    """Each realistic catalog or generated-case drift must lose conformance."""
    module = _module()
    cases = deepcopy(_cases())
    snapshot = _complete_snapshot(module, cases)
    if mutation == "type":
        key = (cases[0]["table"], cases[0]["column"])
        columns = dict(snapshot.columns)
        columns[key] = replace(columns[key], target_type="integer")
        snapshot = replace(snapshot, columns=columns)
    elif mutation == "comment":
        key = (cases[0]["table"], cases[0]["column"])
        columns = dict(snapshot.columns)
        columns[key] = replace(columns[key], comment="drift")
        snapshot = replace(snapshot, columns=columns)
    elif mutation == "object_missing":
        snapshot = replace(snapshot, objects=snapshot.objects[:-1])
    elif mutation == "object_extra":
        snapshot = replace(snapshot, objects=(*snapshot.objects, ("extra", "r")))
    elif mutation == "constraint_missing":
        snapshot = replace(snapshot, constraints=snapshot.constraints[:-1])
    elif mutation == "constraint_extra":
        snapshot = replace(
            snapshot,
            constraints=(*snapshot.constraints, ("extra", "extra", "c")),
        )
    elif mutation == "provenance_set":
        snapshot = replace(snapshot, provenance_tables=snapshot.provenance_tables[:-1])
    elif mutation == "provenance_count":
        snapshot = replace(snapshot, provenance_count=10)
    elif mutation == "provenance_contract":
        columns = dict(snapshot.columns)
        key = ("provenance", "table_name")
        columns[key] = replace(columns[key], target_type="integer")
        snapshot = replace(snapshot, columns=columns)
    elif mutation == "acl":
        acls = dict(snapshot.table_acls)
        acls["specz_compilation"] = (True, True, False, False, False, False, False)
        snapshot = replace(snapshot, table_acls=acls)
    elif mutation == "origin":
        cases[0]["column_origin"] = "id_injected"
    with pytest.raises(ValueError, match=message):
        module.validate_snapshot(cases, snapshot)


def test_catalog_capture_uses_five_batched_queries_not_per_case() -> None:
    """A query added inside the 1,416-case loop must violate the query budget."""
    module = _module()
    cases = _cases()
    expected = _complete_snapshot(module, cases)
    connection = _SnapshotConnection(expected)

    observed = module.capture_catalog_snapshot(connection)

    assert observed == expected
    assert len(connection.queries) == 5


def test_live_orchestration_reuses_snapshot_and_runs_all_security_matrices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Skipping a production security surface must make live evidence incomplete."""
    module = _module()
    cases = _cases()
    expected_snapshot = _complete_snapshot(module, cases)
    connection = _SnapshotConnection(expected_snapshot)
    connection_calls: list[str] = []
    settings = SimpleNamespace(target_database="cosmos2025_v11")
    fingerprint = SimpleNamespace(sha256="v1-fixed")
    monkeypatch.setattr(module, "EXPECTED_V1_FINGERPRINT", "v1-fixed")
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_connect",
        lambda _settings, database: (
            connection_calls.append(database) or _ConnectionContext(connection)
        ),
    )
    monkeypatch.setattr(
        module.bootstrap_v11, "capture_v1_fingerprint", lambda _settings: fingerprint
    )
    monkeypatch.setattr(
        module.bootstrap_v11, "_role_observation", lambda _connection: {"exact": True}
    )
    monkeypatch.setattr(
        module.bootstrap_v11, "validate_role_observation", lambda _observation: None
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "verify_analyst_matrix",
        lambda _settings, expected_primary_rows: {
            "positive": 1,
            "negative": 11,
            "expected_primary_rows": expected_primary_rows,
        },
    )
    monkeypatch.setattr(
        module.load_supplements_v11,
        "validate_retained_handoff_security",
        lambda _settings: {"mode": "0600", "values_rendered": False},
    )
    monkeypatch.setattr(
        module.load_supplements_v11,
        "verify_gate38_analyst",
        lambda _settings, counts: {
            "positive": 4,
            "negative": 24,
            "counts": dict(counts),
        },
    )
    monkeypatch.setattr(
        module.load_provenance_v11,
        "verify_provenance_analyst",
        lambda _settings, expected_rows: {
            "positive": 1,
            "negative": 6,
            "rows": expected_rows,
        },
    )

    report = module.run_live(settings)

    assert connection_calls == ["cosmos2025_v11"]
    assert len(connection.queries) == 5
    assert report["conformance"]["case_assertions"] == 1_416
    assert report["master_matrix"] == {
        "positive": 1,
        "negative": 11,
        "expected_primary_rows": 784_016,
    }
    assert report["gate38_matrix"]["positive"] == 4
    assert report["gate38_matrix"]["negative"] == 24
    assert report["provenance_matrix"] == {
        "positive": 1,
        "negative": 6,
        "rows": 11,
    }
    assert report["v1_fingerprint"] == "v1-fixed"
    assert report["v1_unchanged"] is True
    assert report["direct_network_auth_exercised"] is False


def test_scratch_name_guard_rejects_persistent_and_prefix_only_targets() -> None:
    """No scratch cleanup path may accept a persistent or non-random database."""
    module = _module()
    prefix = "cosmos2025_v11_scratch_"

    accepted = "cosmos2025_v11_scratch_0123456789abcdef0123456789abcdef"
    assert module.validate_scratch_name(prefix, accepted) == accepted
    for refused in (
        "cosmos2025",
        "cosmos2025_v11",
        "cosmos2025_v11_scratch_",
        "cosmos2025_v11_scratch_short",
        "other_0123456789abcdef0123456789abcdef",
    ):
        with pytest.raises(ValueError, match="unsafe scratch database name"):
            module.validate_scratch_name(prefix, refused)


def test_scratch_lifecycle_detects_both_mutations_rolls_back_and_cleans(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Comment/type proofs must each fail, roll back, and drop the exact scratch."""
    module = _module()
    settings = SimpleNamespace(config_path=Path("config"))
    connection = _MutationConnection()
    events: list[tuple[str, str]] = []
    name = "cosmos2025_v11_scratch_0123456789abcdef0123456789abcdef"
    monkeypatch.setattr(
        module, "_scratch_prefix", lambda _settings: "cosmos2025_v11_scratch_"
    )
    monkeypatch.setattr(
        module.uuid, "uuid4", lambda: SimpleNamespace(hex=name.rsplit("_", 1)[1])
    )
    monkeypatch.setattr(module, "_protected_identity", lambda _settings: "unchanged")
    monkeypatch.setattr(
        module, "_reviewed_ddl", lambda _settings: "CREATE SCHEMA source;"
    )
    monkeypatch.setattr(
        module,
        "_create_scratch_database",
        lambda _settings, database: events.append(("create", database)),
    )
    monkeypatch.setattr(
        module,
        "_drop_scratch_database",
        lambda _settings, database: events.append(("drop", database)),
    )
    monkeypatch.setattr(
        module,
        "_connect_scratch",
        lambda _settings, _database: _ConnectionContext(connection),
    )
    monkeypatch.setattr(module, "_insert_scratch_provenance", lambda _connection: None)

    def validate_scratch(current):
        if current.state == "comment":
            raise ValueError("conformance comment mismatch")
        if current.state == "type":
            raise ValueError("conformance type mismatch")
        return {"case_assertions": 1_416}

    monkeypatch.setattr(module, "_validate_scratch_snapshot", validate_scratch)

    report = module.run_scratch_mutations(settings)

    assert events == [("create", name), ("drop", name)]
    assert connection.commits == 1
    assert connection.rollbacks == 2
    assert report == {
        "baseline_case_assertions": 1_416,
        "comment_mutation_detected": True,
        "type_mutation_detected": True,
        "transactions_rolled_back": 2,
        "scratch_absent": True,
        "protected_identity_unchanged": True,
    }


@pytest.mark.parametrize(
    ("failure", "message"),
    (
        ("cleanup", "cleanup failed"),
        ("target_drift", "protected identity changed"),
        ("missing_detection", "scratch mutation was not detected"),
    ),
)
def test_scratch_lifecycle_failure_paths_stop_without_success(
    failure: str, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cleanup, protected drift, and a missed mutation must each stop the run."""
    module = _module()
    settings = SimpleNamespace(config_path=Path("config"))
    connection = _MutationConnection()
    name = "cosmos2025_v11_scratch_0123456789abcdef0123456789abcdef"
    monkeypatch.setattr(
        module, "_scratch_prefix", lambda _settings: "cosmos2025_v11_scratch_"
    )
    monkeypatch.setattr(
        module.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex=name.rsplit("_", 1)[1]),
    )
    identities = iter(("before", "after" if failure == "target_drift" else "before"))
    monkeypatch.setattr(
        module, "_protected_identity", lambda _settings: next(identities)
    )
    monkeypatch.setattr(
        module, "_reviewed_ddl", lambda _settings: "CREATE SCHEMA source;"
    )
    monkeypatch.setattr(module, "_create_scratch_database", lambda *_args: None)
    if failure == "cleanup":
        monkeypatch.setattr(
            module,
            "_drop_scratch_database",
            lambda *_args: (_ for _ in ()).throw(RuntimeError("cleanup failed")),
        )
    else:
        monkeypatch.setattr(module, "_drop_scratch_database", lambda *_args: None)
    monkeypatch.setattr(
        module,
        "_connect_scratch",
        lambda *_args: _ConnectionContext(connection),
    )
    monkeypatch.setattr(module, "_insert_scratch_provenance", lambda *_args: None)

    def validate_scratch(current):
        if failure == "missing_detection":
            return {"case_assertions": 1_416}
        if current.state == "comment":
            raise ValueError("conformance comment mismatch")
        if current.state == "type":
            raise ValueError("conformance type mismatch")
        return {"case_assertions": 1_416}

    monkeypatch.setattr(module, "_validate_scratch_snapshot", validate_scratch)

    with pytest.raises((ValueError, RuntimeError), match=message):
        module.run_scratch_mutations(settings)


def test_ambiguous_create_exit_cleans_the_confirmed_absent_scratch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A post-CREATE context failure must not leave an untracked database."""
    module = _module()
    settings = SimpleNamespace(maintenance_database="postgres")
    name = "cosmos2025_v11_scratch_0123456789abcdef0123456789abcdef"
    dropped: list[str] = []
    monkeypatch.setattr(
        module, "_scratch_prefix", lambda _settings: "cosmos2025_v11_scratch_"
    )
    monkeypatch.setattr(
        module,
        "_connect_database",
        lambda _settings, _database: _AmbiguousCreateContext(),
    )
    monkeypatch.setattr(
        module,
        "_drop_scratch_database",
        lambda _settings, database: dropped.append(database),
    )

    with pytest.raises(RuntimeError, match="ambiguous close"):
        module._create_scratch_database(settings, name)
    assert dropped == [name]


@pytest.mark.parametrize("kind", ("symlink", "dangling", "non_0600"))
def test_protected_handoff_identity_rejects_unsafe_paths_without_following(
    kind: str, tmp_path: Path
) -> None:
    """Protected identity must reject unsafe handoffs before reading targets."""
    module = _module()
    handoff_dir = tmp_path / "internal-files"
    handoff_dir.mkdir()
    path = handoff_dir / "cosmos2025-v11.env"
    content = (
        "PGSQL01_HOST=db\n"
        "PGSQL01_PORT=5432\n"
        "PGSQL01_COSMOS2025_V11_DB=cosmos2025_v11\n"
        "PGSQL01_COSMOS2025_V11_USER=cosmos2025_v11_ro\n"
        "PGSQL01_COSMOS2025_V11_PASSWORD=analyst-secret\n"
    )
    if kind == "symlink":
        target = tmp_path / "must-not-read"
        target.write_text(content, encoding="utf-8")
        target.chmod(0o600)
        path.symlink_to(target)
    elif kind == "dangling":
        path.symlink_to(tmp_path / "missing-target")
    else:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o644)
    settings = SimpleNamespace(
        handoff_path=path,
        repo_root=tmp_path,
        host="db",
        port=5432,
        password="admin-secret",
    )

    with pytest.raises(ValueError, match="handoff"):
        module._capture_handoff_identity(settings)


def test_cli_redacts_unexpected_exception_messages(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unexpected CLI failures must not render credentials or exception text."""
    module = _module()
    monkeypatch.setattr(
        module.bootstrap_v11, "resolve_settings", lambda _path: object()
    )
    monkeypatch.setattr(
        module,
        "run_live",
        lambda _settings: (_ for _ in ()).throw(RuntimeError("secret-token")),
    )

    assert module.main(["--live"]) == 1
    captured = capsys.readouterr()
    assert "secret-token" not in captured.err
    assert captured.err.strip() == "stage=live exception=RuntimeError sqlstate=none"
