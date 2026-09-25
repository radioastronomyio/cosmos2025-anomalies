"""Gate 5.2 hazard repairs: runner guard, uncertain-commit containment, review text.

Three defenses, one per known execution hazard:

1. The historical tension runner refuses production execution before its
   connection factory can be called, with no override flag.
2. The measurement loader's load transaction contains failures without
   destructive cleanup: precommit failures roll back; commits that may have
   succeeded server-side are classified read-only through an independent
   connection and retained, never dropped.
3. ``REVIEW.md`` names the verified join direction and grain and separates
   source fidelity from derived eligibility, so review instructions cannot
   endorse the defective catalog pointer or forbid the authorized derived
   eligibility layer.

Scratch-database tests require the admin environment (run under the scoped
Doppler runtime); they skip otherwise and execute in the gate 5.7 full suite.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.etl import load_specz_all_v11 as loader  # noqa: E402
from src.features import compute_tension_scalars as tension  # noqa: E402

RUNNER_PATH = REPO_ROOT / "src" / "features" / "compute_tension_scalars.py"


# =============================================================================
# Hazard 1: historical runner refuses before any connection
# =============================================================================


def test_runner_cli_refuses_with_explanation_before_connection() -> None:
    result = subprocess.run(
        [sys.executable, str(RUNNER_PATH)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "disabled" in combined
    assert "P2R-05" in combined
    assert "v1 baseline" in combined


def test_runner_main_never_calls_connection_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_if_called(*args, **kwargs):  # pragma: no cover - assertion path
        raise AssertionError("connection factory must not be called")

    monkeypatch.setattr(tension, "get_db_connection", _fail_if_called)
    monkeypatch.setattr(tension, "load_config", _fail_if_called)
    with pytest.raises(SystemExit, match="disabled"):
        tension.main()


def test_runner_has_no_override_flag() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")
    main_body = source[source.index("def main()") :]
    assert "force" not in main_body.lower().replace("refuse", "")
    assert "--" not in main_body  # no argparse surface on the guarded entrypoint


def test_runner_pure_helpers_remain_importable_and_usable() -> None:
    assert tension.SIGMA_SYS_MASS == 0.1
    sql = tension.build_insert_tension_sql("wht_f770w")
    assert "LOG(c.mass)" in sql
    assert tension.format_pct(0.125) == "12.50%"
    assert tension.format_pct(None) == "NULL"


# =============================================================================
# Hazard 2: uncertain-commit containment (fakes)
# =============================================================================


class FakeCursor:
    def __init__(self, statements: list[str]) -> None:
        self._statements = statements

    def copy(self, statement: str):
        self._statements.append(statement)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def write(self, frame) -> None:
        if frame is loader_sentinel.FAIL:
            raise RuntimeError("frame write failed mid-copy")


class loader_sentinel:
    FAIL = object()


class FakeConnection:
    """Records executed statements; simulates commit outcomes on demand."""

    def __init__(self, *, commit_outcome: Exception | None = None) -> None:
        self.statements: list[str] = []
        self.commit_outcome = commit_outcome
        self.committed = False
        self.rolled_back = False

    def execute(self, statement, *args, **kwargs):
        self.statements.append(repr(statement))
        return type("Result", (), {"fetchone": staticmethod(lambda: (1, 1))})()

    def cursor(self):
        return FakeCursor(self.statements)

    def commit(self) -> None:
        self.committed = True  # the server-side success
        if self.commit_outcome is not None:
            raise self.commit_outcome

    def rollback(self) -> None:
        self.rolled_back = True


STATEMENTS = ['CREATE TABLE "source"."specz_compilation_all" (id_specz bigint)']
COPY_STMT = (
    'COPY "source"."specz_compilation_all" (id_specz) FROM STDIN WITH '
    "(FORMAT csv, DELIMITER E'\\t', NULL '\\N')"
)


def _run_load(connection, frames, classifier):
    return loader._load_transaction(
        connection,
        statements=STATEMENTS,
        copy_statement=COPY_STMT,
        frames=frames,
        expected_rows=1,
        classify_uncertain_commit=classifier,
    )


def test_precommit_failure_rolls_back_without_drop() -> None:
    connection = FakeConnection()
    with pytest.raises(RuntimeError, match="mid-copy"):
        _run_load(connection, [b"1\n", loader_sentinel.FAIL], lambda: pytest.fail("no classify"))
    assert connection.rolled_back is True
    assert not any("DROP" in s for s in connection.statements)


def test_uncertain_commit_retains_and_classifies_without_drop() -> None:
    connection = FakeConnection(
        commit_outcome=RuntimeError("connection reset after server-side commit")
    )
    calls: list[object] = []

    def classifier():
        calls.append(True)
        return {"state": "complete", "rows": 1}

    with pytest.raises(RuntimeError, match="connection reset"):
        _run_load(connection, [b"1\n"], classifier)
    assert connection.committed is True  # server-side success happened
    assert calls, "uncertain commit must be classified, not cleaned up"
    assert not any("DROP" in s for s in connection.statements)


def test_uncertain_commit_interruption_is_not_cleaned_up() -> None:
    connection = FakeConnection(commit_outcome=KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        _run_load(connection, [b"1\n"], lambda: {"state": "absent", "rows": 0})
    assert not any("DROP" in s for s in connection.statements)


def test_classification_failure_is_reported_not_worked_around() -> None:
    connection = FakeConnection(commit_outcome=RuntimeError("reset"))

    def broken_classifier():
        raise ConnectionError("probe cannot reach server")

    with pytest.raises(RuntimeError, match="reset"):
        _run_load(connection, [b"1\n"], broken_classifier)
    assert not any("DROP" in s for s in connection.statements)


def test_handler_reports_unknown_classification_state() -> None:
    connection = FakeConnection()
    evidence = loader._handle_load_failure(
        connection,
        commit_attempted=True,
        classify_uncertain_commit=lambda: {"state": "inconsistent", "rows": 5},
    )
    assert evidence["phase"] == "uncertain_commit"
    assert evidence["classification"]["state"] == "inconsistent"
    assert evidence["compensating_drop"] is False


# =============================================================================
# Hazard 2: uncertain-commit containment (scratch database)
# =============================================================================

_scratch = None
try:
    from src.etl import verify_schema_v11_scratch as scratch  # noqa: E402
except ImportError:  # pragma: no cover - module is repository furniture
    scratch = None

ADMIN_ENV_NAMES = (
    "PGSQL01_HOST",
    "PGSQL01_PORT",
    "PGSQL01_ADMIN_USER",
    "PGSQL01_ADMIN_PASSWORD",
)


def _admin_environment_present() -> bool:
    import os

    return all(os.environ.get(name) for name in ADMIN_ENV_NAMES)


requires_admin = pytest.mark.skipif(
    not _admin_environment_present(),
    reason="scratch tests require the scoped Doppler admin environment",
)


class PostCommitRaiseProxy:
    """Wraps a live connection; commit() commits server-side, then raises."""

    def __init__(self, inner) -> None:
        self._inner = inner

    def execute(self, *args, **kwargs):
        return self._inner.execute(*args, **kwargs)

    def cursor(self):
        return self._inner.cursor()

    def commit(self) -> None:
        self._inner.commit()
        raise RuntimeError("simulated client failure after server-side commit")

    def rollback(self) -> None:
        return self._inner.rollback()

    def close(self) -> None:
        return self._inner.close()


@requires_admin
def test_scratch_post_commit_failure_retains_installed_table_and_data() -> None:
    import os

    import psycopg

    name = scratch.validate_scratch_name(scratch.generate_scratch_name())
    admin = {
        "host": os.environ["PGSQL01_HOST"],
        "port": int(os.environ["PGSQL01_PORT"]),
        "user": os.environ["PGSQL01_ADMIN_USER"],
        "password": os.environ["PGSQL01_ADMIN_PASSWORD"],
    }
    with psycopg.connect(dbname="postgres", **admin) as server:
        server.autocommit = True
        server.execute(f'CREATE DATABASE "{name}"')
    try:
        with psycopg.connect(dbname=name, **admin) as connection:
            connection.execute("CREATE SCHEMA source")
            statements = [
                'CREATE TABLE "source"."specz_compilation_all" '
                "(id_specz bigint PRIMARY KEY, specz double precision)"
            ]
            copy_statement = (
                'COPY "source"."specz_compilation_all" (id_specz, specz) '
                "FROM STDIN WITH (FORMAT csv)"
            )
            proxy = PostCommitRaiseProxy(connection)
            with pytest.raises(RuntimeError, match="after server-side commit"):
                loader._load_transaction(
                    proxy,
                    statements=statements,
                    copy_statement=copy_statement,
                    frames=[b"1,0.5\n"],
                    expected_rows=1,
                    classify_uncertain_commit=lambda: {"state": "not-probed"},
                )
            # The independent connection observes the committed table intact.
            retained = connection.execute(
                'SELECT count(*), coalesce(sum(specz), 0) FROM '
                '"source"."specz_compilation_all"'
            ).fetchone()
            assert tuple(retained) == (1, 0.5)
    finally:
        with psycopg.connect(dbname="postgres", **admin) as server:
            server.autocommit = True
            server.execute(f'DROP DATABASE IF EXISTS "{name}"')


@requires_admin
def test_scratch_precommit_failure_leaves_no_table() -> None:
    import os

    import psycopg

    name = scratch.validate_scratch_name(scratch.generate_scratch_name())
    admin = {
        "host": os.environ["PGSQL01_HOST"],
        "port": int(os.environ["PGSQL01_PORT"]),
        "user": os.environ["PGSQL01_ADMIN_USER"],
        "password": os.environ["PGSQL01_ADMIN_PASSWORD"],
    }
    with psycopg.connect(dbname="postgres", **admin) as server:
        server.autocommit = True
        server.execute(f'CREATE DATABASE "{name}"')
    try:
        with psycopg.connect(dbname=name, **admin) as connection:
            connection.execute("CREATE SCHEMA source")
            statements = [
                'CREATE TABLE "source"."specz_compilation_all" '
                "(id_specz bigint PRIMARY KEY)"
            ]

            def failing_frames():
                yield b"1\n"
                raise RuntimeError("simulated mid-copy interruption")

            with pytest.raises(RuntimeError, match="mid-copy"):
                loader._load_transaction(
                    connection,
                    statements=statements,
                    copy_statement=(
                        'COPY "source"."specz_compilation_all" (id_specz) '
                        "FROM STDIN WITH (FORMAT csv)"
                    ),
                    frames=failing_frames(),
                    expected_rows=1,
                    classify_uncertain_commit=lambda: pytest.fail("no classify"),
                )
            exists = connection.execute(
                "SELECT to_regclass('source.specz_compilation_all') IS NOT NULL"
            ).fetchone()[0]
            assert exists is False, "rolled-back transaction must leave no table"
    finally:
        with psycopg.connect(dbname="postgres", **admin) as server:
            server.autocommit = True
            server.execute(f'DROP DATABASE IF EXISTS "{name}"')


@requires_admin
def test_scratch_existing_object_protection_retains_values() -> None:
    import os

    import psycopg

    name = scratch.validate_scratch_name(scratch.generate_scratch_name())
    admin = {
        "host": os.environ["PGSQL01_HOST"],
        "port": int(os.environ["PGSQL01_PORT"]),
        "user": os.environ["PGSQL01_ADMIN_USER"],
        "password": os.environ["PGSQL01_ADMIN_PASSWORD"],
    }
    with psycopg.connect(dbname="postgres", **admin) as server:
        server.autocommit = True
        server.execute(f'CREATE DATABASE "{name}"')
    try:
        with psycopg.connect(dbname=name, **admin) as connection:
            connection.execute("CREATE SCHEMA source")
            connection.execute(
                'CREATE TABLE "source"."specz_compilation_all" '
                "(id_specz bigint PRIMARY KEY, specz double precision)"
            )
            connection.execute(
                'INSERT INTO "source"."specz_compilation_all" VALUES (7, 0.25)'
            )
            connection.commit()
            with pytest.raises(SystemExit, match="already exists"):
                loader._ensure_target_absent(connection)
            retained = connection.execute(
                'SELECT id_specz, specz FROM "source"."specz_compilation_all"'
            ).fetchone()
            assert tuple(retained) == (7, 0.25)
    finally:
        with psycopg.connect(dbname="postgres", **admin) as server:
            server.autocommit = True
            server.execute(f'DROP DATABASE IF EXISTS "{name}"')


# =============================================================================
# Hazard 3: REVIEW.md join/grain/eligibility guidance
# =============================================================================


def test_review_states_verified_join_and_current_mirror_boundary() -> None:
    text = (REPO_ROOT / "REVIEW.md").read_text(encoding="utf-8")
    # The defective catalog pointer must not be presented as a working join.
    assert "id_specz_khostovan25` does **not** resolve" in text
    assert "`id_cosmos25 = photometry_primary.id`" in text
    assert "Id_specz` identifies a compilation entry" in text
    # The mirror boundary is the current twelve-mirror boundary.
    assert "twelve mirrors" in text
    # Source fidelity and derived eligibility are stated as distinct contracts.
    assert "Source fidelity and derived eligibility are different contracts" in text
    assert "approved policy may reject a value for eligibility" in text
    # Grain guidance distinguishes the two compilation surfaces.
    assert "_unique` (one shipped representative row" in text


def test_review_does_not_endorse_defective_pointer_as_join_key() -> None:
    import re

    text = (REPO_ROOT / "REVIEW.md").read_text(encoding="utf-8")
    pattern = re.compile(r"id_specz_khostovan25[^\n]*resolves into")
    assert not pattern.search(text), "REVIEW.md must not claim the link column resolves"
