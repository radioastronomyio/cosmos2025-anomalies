#!/usr/bin/env python3
"""
Script Name  : test_load_provenance_v11.py
Description  : Test guarded Gate 3.9 provenance registration and verification
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises the exact twelve-row evidence boundary, the amended registration
timestamp semantics, mutation detection, and post-commit retention policy.

Usage
-----
    pytest tests/test_load_provenance_v11.py -v
"""

import importlib.util
import io
import sys
from contextlib import redirect_stderr
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "load_provenance_v11.py"
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"


def _module():
    """Load production only after the test starts so missing code is RED."""
    assert MODULE_PATH.exists(), "Gate 3.9 provenance registrar is missing"
    spec = importlib.util.spec_from_file_location("load_provenance_v11", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pins(module):
    return {
        table: SimpleNamespace(
            path=f"/immutable/{table}.fits",
            declared_sha256=f"{index:064x}",
            observed_sha256=f"{index:064x}",
            declared_bytes=index,
            observed_bytes=index,
        )
        for index, table in enumerate(module.PROVENANCE_TABLES, start=1)
    }


def _expected(module):
    counts = {
        table: index * 10
        for index, table in enumerate(module.PROVENANCE_TABLES, start=1)
    }
    xmins = {
        table: 11_000_000 + index
        for index, table in enumerate(module.PROVENANCE_TABLES, start=1)
    }
    return module.build_expected_provenance(
        pins=_pins(module),
        source_counts=counts,
        loaded_counts=counts,
        xmins=xmins,
        manifest_ref=Path("/immutable/data-manifest-v1.1.csv"),
        manifest_ref_sha256="a" * 64,
    )


def test_build_expected_provenance_preserves_independent_evidence_and_versions():
    """All twelve records must preserve exact paths, digests, counts, and XIDs."""
    module = _module()
    rows = _expected(module)

    assert tuple(row.table_name for row in rows) == module.PROVENANCE_TABLES
    assert len(rows) == 12
    assert all(row.manifest_sha256 == row.observed_sha256 for row in rows)
    assert all(row.source_file == Path(row.source_path).name for row in rows)
    assert all(row.source_rows == row.loaded_rows for row in rows)
    assert all(row.catalog_version == "v1.1" for row in rows)
    supplements = set(module.SUPPLEMENT_TABLES)
    assert {row.table_name: row.supplement_version for row in rows} == {
        table: ("v1" if table in supplements else "not_applicable")
        for table in module.PROVENANCE_TABLES
    }
    for index, row in enumerate(rows, start=1):
        assert f"load_transaction_xmin={11_000_000 + index}" in row.notes
        assert "track_commit_timestamp was off" in row.notes
        assert "actual commit timestamp is unavailable" in row.notes
        assert ("v1-release product on v1.1 holdings" in row.notes) == (
            row.table_name in supplements
        )


def test_all_twelve_source_paths_are_config_selected_without_abbreviation():
    """Provenance paths must come from the exact configured artifact boundary."""
    module = _module()
    paths = module._source_paths(CONFIG_PATH)
    assert tuple(paths) == module.PROVENANCE_TABLES
    assert all(path.is_absolute() for path in paths.values())
    assert paths["photometry_primary"].name == (
        "COSMOSWeb_mastercatalog_v1.1_photom_primary.fits"
    )
    assert paths["galaxy_group_memberships"].name == "memberships.txt"
    assert paths["specz_compilation_unique"].name == (
        "specz_compilation_COSMOS_DR1.1_unique.fits"
    )
    assert paths["specz_compilation_all"].name == (
        "specz_compilation_COSMOS_DR1.1_all.fits"
    )


def test_expected_provenance_rejects_boundary_hash_count_and_xmin_drift():
    """The constructor must reject copied hashes and incomplete live evidence."""
    module = _module()
    pins = _pins(module)
    counts = {table: 1 for table in module.PROVENANCE_TABLES}
    xmins = {table: 100 + i for i, table in enumerate(module.PROVENANCE_TABLES)}
    kwargs = {
        "pins": pins,
        "source_counts": counts,
        "loaded_counts": counts,
        "xmins": xmins,
        "manifest_ref": Path("/immutable/manifest.csv"),
        "manifest_ref_sha256": "b" * 64,
    }

    bad_pins = dict(pins)
    bad_pins[module.PROVENANCE_TABLES[0]] = SimpleNamespace(
        **{
            **vars(pins[module.PROVENANCE_TABLES[0]]),
            "observed_sha256": "f" * 64,
        }
    )
    with pytest.raises(ValueError, match="digest mismatch"):
        module.build_expected_provenance(**{**kwargs, "pins": bad_pins})
    with pytest.raises(ValueError, match="table boundary"):
        module.build_expected_provenance(
            **{**kwargs, "loaded_counts": dict(list(counts.items())[:-1])}
        )
    with pytest.raises(ValueError, match="count mismatch"):
        module.build_expected_provenance(
            **{
                **kwargs,
                "loaded_counts": {**counts, module.PROVENANCE_TABLES[0]: 2},
            }
        )
    with pytest.raises(ValueError, match="xmin"):
        module.build_expected_provenance(
            **{**kwargs, "xmins": {**xmins, module.PROVENANCE_TABLES[0]: 0}}
        )


def test_validate_observation_detects_all_required_mutation_classes():
    """Wrong hash/path/count/version/timestamp/set/XID evidence must fail."""
    module = _module()
    expected = _expected(module)
    timestamp = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
    observed = tuple(
        module.ProvenanceObservation(**vars(row), load_timestamp=timestamp)
        for row in expected
    )
    assert module.validate_provenance_observation(expected, observed) == timestamp

    first = observed[0]
    mutations = {
        "hash": replace(first, observed_sha256="f" * 64),
        "path": replace(first, source_path="/wrong/path.fits"),
        "count": replace(first, loaded_rows=first.loaded_rows + 1),
        "version": replace(first, catalog_version="wrong"),
        "timestamp": replace(
            first,
            load_timestamp=datetime(2026, 8, 18, 12, 1, tzinfo=timezone.utc),
        ),
        "xmin": replace(first, notes=first.notes.replace("11000001", "999")),
    }
    for label, mutation in mutations.items():
        changed = (mutation, *observed[1:])
        with pytest.raises(ValueError, match=label):
            module.validate_provenance_observation(expected, changed)
    with pytest.raises(ValueError, match="set"):
        module.validate_provenance_observation(expected, observed[:-1])


class _Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _RegistrationConnection:
    """Small transactional double that exposes SQL shape and commit ordering."""

    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.executed = []
        self.inserted = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, parameters=None):
        text = str(statement)
        self.executed.append((text, parameters))
        if "SELECT count(*) FROM" in text:
            return _Result((0,))
        if "count(*), count(DISTINCT load_timestamp)" in text:
            return _Result((12, 1, self.timestamp))
        return _Result()

    class _Cursor:
        def __init__(self, connection):
            self.connection = connection

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def executemany(self, statement, parameters):
            self.connection.executed.append((str(statement), None))
            self.connection.inserted.extend(parameters)

    def cursor(self):
        """Match psycopg: executemany belongs to Cursor, not Connection."""
        return self._Cursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


def test_registration_transaction_uses_one_database_timestamp_and_exact_comment():
    """The insert and amended generated COMMENT must commit atomically."""
    module = _module()
    timestamp = datetime(2026, 8, 18, 13, 0, tzinfo=timezone.utc)
    connection = _RegistrationConnection(timestamp)

    assert module.register_provenance_transaction(connection, _expected(module)) == (
        timestamp
    )
    rendered = "\n".join(statement for statement, _ in connection.executed)
    assert 'COMMENT ON COLUMN "source"."provenance"."load_timestamp"' in rendered
    assert "provenance-registration transaction" in rendered
    assert "transaction_timestamp()" in rendered
    assert "DELETE" not in rendered
    assert "TRUNCATE" not in rendered
    assert len(connection.inserted) == 12
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_precommit_insert_failure_rolls_back_without_commit():
    """A failure after COMMENT but before commit must roll back the transaction."""
    module = _module()

    class FailingCursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def executemany(self, statement, parameters):
            raise RuntimeError("injected precommit failure")

    connection = _RegistrationConnection(
        datetime(2026, 8, 18, 13, 0, tzinfo=timezone.utc)
    )
    connection.cursor = lambda: FailingCursor()
    with pytest.raises(RuntimeError, match="injected precommit failure"):
        module.register_provenance_transaction(connection, _expected(module))
    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert any("COMMENT ON COLUMN" in statement for statement, _ in connection.executed)


def test_postcommit_verifier_failure_is_redacted_and_retains_rows(monkeypatch):
    """A post-commit defect must never delete already registered provenance."""
    module = _module()
    timestamp = datetime(2026, 8, 18, 13, 0, tzinfo=timezone.utc)
    connection = _RegistrationConnection(timestamp)

    def connect():
        return connection

    def fail_verify():
        raise RuntimeError("sensitive unexpected detail")

    with pytest.raises(
        module.ProvenanceFailure,
        match=r"stage=verify_postcommit exception=RuntimeError sqlstate=none retained=12",
    ) as captured:
        module.run_registration(_expected(module), connect, fail_verify)
    assert "sensitive" not in str(captured.value)
    assert connection.commits == 1
    assert all("DELETE" not in statement for statement, _ in connection.executed)
    assert all("TRUNCATE" not in statement for statement, _ in connection.executed)


def test_cli_redacts_unexpected_exception_text(monkeypatch):
    """Direct execution may expose stage/class/SQLSTATE but never exception text."""
    module = _module()
    monkeypatch.setattr(module, "run_provenance_load", lambda settings: 1 / 0)
    monkeypatch.setattr(module, "resolve_settings", lambda config: object())
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        assert module.main(["--load"]) == 1
    assert "ZeroDivisionError" in stderr.getvalue()
    assert "division by zero" not in stderr.getvalue()


def test_pre_registration_schema_allows_only_exact_old_or_amended_comment(monkeypatch):
    """Every schema field stays exact while the one authorized COMMENT can change."""
    module = _module()
    captured = []
    monkeypatch.setattr(
        module,
        "_provenance_comment",
        lambda connection: module.PRE_AMENDMENT_COMMENT,
    )
    monkeypatch.setattr(
        module.load_supplements_v11.verify_schema_v11_scratch,
        "_verify_objects_and_columns",
        lambda connection, rows, *, expected_comment_overrides: (
            captured.append(expected_comment_overrides) or {"tables": 12}
        ),
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "verify_exact_retained_schema",
        lambda connection, rows: {"constraints": 192},
    )
    assert module.verify_pre_registration_schema(object(), []) == {
        "tables": 12,
        "constraints": 192,
    }
    assert captured == [
        {("provenance", "load_timestamp"): module.PRE_AMENDMENT_COMMENT}
    ]

    monkeypatch.setattr(module, "_provenance_comment", lambda connection: "drift")
    with pytest.raises(ValueError, match="pre-registration.*comment"):
        module.verify_pre_registration_schema(object(), [])


def test_manifest_digest_guards_the_exact_contract_and_pin_read_window(monkeypatch):
    """Stored manifest digest must identify the same bytes used for declared pins."""
    module = _module()
    settings = SimpleNamespace(manifest_path=Path("/immutable/manifest.csv"))
    monkeypatch.setattr(
        module.bootstrap_v11, "_manifest_contract", lambda value: object()
    )
    monkeypatch.setattr(
        module.verify_source_fidelity,
        "pin_manifest_input",
        lambda table, path, contract: SimpleNamespace(table=table, path=str(path)),
    )
    digests = iter(("a" * 64, "b" * 64))
    monkeypatch.setattr(
        module.verify_source_fidelity, "sha256_of", lambda path: next(digests)
    )
    paths = {table: Path(f"/{table}") for table in module.PROVENANCE_TABLES}
    with pytest.raises(ValueError, match="manifest changed"):
        module.fresh_manifest_evidence(settings, paths)


class _ClassifyConnection:
    def __init__(self, module, expected, *, committed, close_error=False):
        self.module = module
        self.expected = expected
        self.committed = committed
        self.close_error = close_error

    def execute(self, statement, parameters=None):
        text = str(statement)
        if "SELECT count(*) FROM" in text:
            return _Result((12 if self.committed else 0,))
        raise AssertionError(text)

    def rollback(self):
        pass

    def close(self):
        if self.close_error:
            raise RuntimeError("close detail")


@pytest.mark.parametrize("comment_kind", ["old", "amended"])
def test_rollback_classifier_accepts_both_authorized_empty_comments(
    monkeypatch, comment_kind
):
    """An empty rollback is exact under either authorized schema-comment state."""
    module = _module()
    expected = _expected(module)
    connection = _ClassifyConnection(module, expected, committed=False)
    comment = (
        module.PRE_AMENDMENT_COMMENT
        if comment_kind == "old"
        else module.generate_schema_v11.PROVENANCE_CONTRACT[7].comment
    )
    monkeypatch.setattr(module, "_provenance_comment", lambda value: comment)
    assert module.classify_registration_state(lambda: connection, expected) == (
        "rolled_back",
        None,
    )


def test_ambiguous_commit_and_close_are_reclassified_as_retained(monkeypatch):
    """Commit-return/close failures must reconnect before reporting retention."""
    module = _module()
    expected = _expected(module)
    timestamp = datetime(2026, 8, 18, 14, 0, tzinfo=timezone.utc)
    first = _ClassifyConnection(module, expected, committed=True, close_error=True)
    subsequent = _ClassifyConnection(module, expected, committed=True)
    connections = iter((first, subsequent, subsequent))
    monkeypatch.setattr(
        module,
        "register_provenance_transaction",
        lambda connection, rows: (_ for _ in ()).throw(RuntimeError("commit detail")),
    )
    monkeypatch.setattr(
        module,
        "classify_registration_state",
        lambda connect, rows: ("committed", timestamp),
    )
    verified = []

    assert (
        module.run_registration(
            expected, lambda: next(connections), lambda: verified.append(True)
        )
        == timestamp
    )
    assert verified == [True]


def test_verify_only_rebuilds_fresh_evidence_and_never_registers(monkeypatch):
    """Verify-only may re-read evidence but cannot execute registration."""
    module = _module()
    settings = object()
    expected = _expected(module)
    monkeypatch.setattr(
        module,
        "build_live_expected",
        lambda value, *, require_provenance_zero: {
            "expected": expected,
            "v1_fingerprint": "v1",
            "zero": require_provenance_zero,
        },
    )
    monkeypatch.setattr(
        module,
        "verify_persistent_provenance",
        lambda value, rows, *, expected_v1_fingerprint: {
            "rows": len(rows),
            "v1": expected_v1_fingerprint,
        },
    )
    monkeypatch.setattr(
        module,
        "register_provenance_transaction",
        lambda *args: pytest.fail("verify-only attempted registration"),
    )
    result = module.run_provenance_verify_only(settings)
    assert result["mode"] == "verify-only"
    assert result["verification"] == {"rows": 12, "v1": "v1"}


def test_verify_only_preobservation_failure_reports_unvalidated_retention(monkeypatch):
    """A source/config failure cannot assert a database row count it never read."""
    module = _module()
    monkeypatch.setattr(
        module,
        "build_live_expected",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("sensitive")),
    )
    with pytest.raises(
        module.ProvenanceFailure,
        match=r"stage=verify_only exception=RuntimeError .* retained=unvalidated",
    ) as captured:
        module.run_provenance_verify_only(object())
    assert "sensitive" not in str(captured.value)


def test_load_orchestration_preflights_registers_then_verifies(monkeypatch):
    """Persistent mode must cross the one allowed transaction before verification."""
    module = _module()
    expected = _expected(module)
    settings = object()
    calls = []
    monkeypatch.setattr(
        module,
        "build_live_expected",
        lambda value, *, require_provenance_zero: (
            calls.append(("preflight", require_provenance_zero))
            or {"expected": expected, "v1_fingerprint": "v1"}
        ),
    )
    monkeypatch.setattr(module, "_connect_target", lambda value: object())
    monkeypatch.setattr(
        module,
        "verify_persistent_provenance",
        lambda value, rows, *, expected_v1_fingerprint: (
            calls.append(("verify", len(rows), expected_v1_fingerprint)) or {"rows": 12}
        ),
    )

    def run_registration(rows, connect, verify):
        calls.append(("register", len(rows)))
        verify()
        return datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(module, "run_registration", run_registration)
    result = module.run_provenance_load(settings)
    assert result["status"] == "passed"
    assert calls == [
        ("preflight", True),
        ("register", 12),
        ("verify", 12, "v1"),
    ]


def test_post_registration_output_failure_reports_retained_rows(monkeypatch):
    """A failure after the commit boundary cannot claim preflight/zero retention."""
    module = _module()
    expected = _expected(module)
    monkeypatch.setattr(
        module,
        "build_live_expected",
        lambda settings, *, require_provenance_zero: {
            "expected": expected,
            "v1_fingerprint": "v1",
        },
    )
    monkeypatch.setattr(module, "_connect_target", lambda settings: object())
    monkeypatch.setattr(
        module,
        "run_registration",
        lambda rows, connect, verify: datetime(2026, 8, 18, 16, 0, tzinfo=timezone.utc),
    )
    calls = 0

    def fail_second_print(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise BrokenPipeError("sensitive output detail")

    monkeypatch.setattr("builtins.print", fail_second_print)
    with pytest.raises(
        module.ProvenanceFailure,
        match=r"stage=post_registration exception=BrokenPipeError .* retained=12",
    ) as captured:
        module.run_provenance_load(object())
    assert "sensitive" not in str(captured.value)
