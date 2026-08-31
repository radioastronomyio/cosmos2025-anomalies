#!/usr/bin/env python3
"""
Script Name  : test_load_supplements_v11.py
Description  : Test guarded supplement and spec-z mirror loading
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises Gate 3.8 source boundaries, quality-flag evidence, empty-target
guards, streaming conversion, exact reversal, and read-only verification.

Usage
-----
    pytest tests/test_load_supplements_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from astropy.io import fits

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src/etl/load_supplements_v11.py"
DICTIONARY_PATH = REPO_ROOT / "data/dictionary/columns-v11.csv"
CONFIG_PATH = REPO_ROOT / "configs/data_paths.yaml"


# =============================================================================
# Test utilities
# =============================================================================


def _module():
    """Load production only after test start so missing behavior is RED."""
    assert MODULE_PATH.exists(), "Gate 3.8 supplement loader is missing"
    spec = importlib.util.spec_from_file_location("load_supplements_v11", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _dictionary_rows() -> list[dict[str, str]]:
    """Read the tracked dictionary as an independent test input."""
    with DICTIONARY_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# =============================================================================
# Contract tests
# =============================================================================


def test_gate38_contract_is_config_driven_native_only_and_exactly_54_fields() -> None:
    """A skipped, duplicated, metadata, or hardcoded source field must halt."""
    module = _module()
    contract = module.resolve_gate38_contract(CONFIG_PATH, _dictionary_rows())

    assert tuple(contract.tables) == (
        "lss_overdensity",
        "galaxy_groups",
        "galaxy_group_memberships",
        "specz_compilation",
    )
    assert {table: len(rows) for table, rows in contract.tables.items()} == {
        "lss_overdensity": 4,
        "galaxy_groups": 14,
        "galaxy_group_memberships": 4,
        "specz_compilation": 32,
    }
    assert sum(len(rows) for rows in contract.tables.values()) == 54
    assert {
        row["column_origin"] for rows in contract.tables.values() for row in rows
    } == {"source_native"}
    configured = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert contract.paths == {
        "lss_overdensity": Path(configured["supplementary"]["lss_overdensity"]),
        "galaxy_groups": Path(configured["supplementary"]["group_catalog_groups"]),
        "galaxy_group_memberships": Path(
            configured["supplementary"]["group_catalog_memberships"]
        ),
        "specz_compilation": Path(configured["specz"]["unique_fits"]),
    }

    duplicate = [dict(row) for row in _dictionary_rows()]
    duplicate.append(
        dict(next(row for row in duplicate if row["target_table"] == "lss_overdensity"))
    )
    with pytest.raises(ValueError, match="exactly once"):
        module.resolve_gate38_contract(CONFIG_PATH, duplicate)


def test_gate38_empty_guard_includes_provenance_and_refuses_partial_state() -> None:
    """A prior row in any Gate 3.8/provenance target must stop before COPY."""
    module = _module()
    exact = {
        "lss_overdensity": 0,
        "galaxy_groups": 0,
        "galaxy_group_memberships": 0,
        "specz_compilation": 0,
        "provenance": 0,
    }
    module.assert_gate38_targets_empty(exact)
    for table in exact:
        changed = {**exact, table: 1}
        with pytest.raises(ValueError, match="preflight-zero"):
            module.assert_gate38_targets_empty(changed)


def test_quality_flag_evidence_preserves_every_value_and_sourced_definitions() -> None:
    """Quality evidence must report all flags without a secure-row policy."""
    module = _module()
    evidence = module.quality_flag_definition_evidence(_dictionary_rows())
    assert evidence["source"] == (
        "/opt/agents/repos/reference-files/speczcompilation/README.md"
    )
    assert evidence["locator"] == "Quality Assessment Flagging System, lines 60-70"
    assert evidence["definitions"] == {
        "4": {"confidence_percent": 97, "description": "Very Reliable Redshift"},
        "3": {"confidence_percent": 95, "description": "Reliable Redshift"},
        "2": {
            "confidence_percent": 80,
            "description": "Moderate Detection of Emission Lines",
        },
        "1": {"confidence_percent": 50, "description": "Tentative Measurement"},
        "0": {"confidence_percent": None, "description": "No Measurement"},
        "9": {
            "confidence_percent": 85,
            "description": "Single Line Detection with Good S/N",
        },
        "+10": {
            "confidence_percent": None,
            "description": "Broad Line Feature (e.g., BL-AGN)",
        },
    }
    flags = [4, 4, 3, 9, 14, 0, -99]
    assert module.summarize_quality_flags(flags) == {
        "distribution": {-99: 1, 0: 1, 3: 1, 4: 2, 9: 1, 14: 1},
        "flags_3_or_4": 3,
        "flag_9": 1,
        "rows": 7,
    }


def test_supplement_version_evidence_is_deferred_from_provenance_rows() -> None:
    """Gate 3.8 must capture release evidence but leave provenance empty."""
    module = _module()
    assert module.supplement_version_evidence() == {
        "lss_overdensity": "v1-release-on-v1.1-holdings",
        "galaxy_groups": "v1-release-on-v1.1-holdings",
        "galaxy_group_memberships": "v1-release-on-v1.1-holdings",
    }
    assert module.membership_group_relationship_evidence() == {
        "defined_by_pinned_source": False,
        "anti_join_exercised": False,
        "reason": "no pinned Toni source document defines ID as a group foreign key",
    }


# =============================================================================
# Streaming and lifecycle tests
# =============================================================================


def test_fits_stream_preserves_finite_sentinels_and_nulls_only_mask_nan(
    tmp_path: Path,
) -> None:
    """Mask/NaN conversion may not erase finite -99/-999 source values."""
    module = _module()
    path = tmp_path / "source.fits"
    hdu = fits.BinTableHDU.from_columns(
        (
            fits.Column(
                name="id", format="K", array=np.array([1, -999, -99]), null=-999
            ),
            fits.Column(
                name="value", format="D", array=np.array([1.5, np.nan, -999.0])
            ),
        )
    )
    hdu.writeto(path)
    rows = (
        {
            "source_column": "id",
            "target_identifier": "id",
            "target_type": "bigint",
            "column_origin": "source_native",
        },
        {
            "source_column": "value",
            "target_identifier": "value",
            "target_type": "double precision",
            "column_origin": "source_native",
        },
    )

    observation = module.inspect_fits_source(path, rows)
    frames = list(module.iter_fits_copy_frames(path, rows, batch_rows=2))
    rendered = b"".join(frames).decode("utf-8")

    assert observation.row_count == 3
    assert observation.source_columns == ("id", "value")
    assert len(frames) == 2
    assert rendered.splitlines() == [
        "1\t1.5",
        f"{module.COPY_NULL_MARKER}\t{module.COPY_NULL_MARKER}",
        "-99\t-999",
    ]


def test_text_stream_is_bounded_exact_order_and_preserves_finite_sentinels(
    tmp_path: Path,
) -> None:
    """Whitespace text COPY must preserve raw values and reject column drift."""
    module = _module()
    path = tmp_path / "groups.txt"
    path.write_text("ID RA\n1 1.5\n-99 nan\n3 -999\n", encoding="utf-8")
    rows = (
        {
            "source_column": "ID",
            "target_identifier": "id",
            "target_type": "bigint",
            "column_origin": "source_native",
        },
        {
            "source_column": "RA",
            "target_identifier": "ra",
            "target_type": "double precision",
            "column_origin": "source_native",
        },
    )

    observation = module.inspect_text_source(path, rows)
    frames = list(module.iter_text_copy_frames(path, rows, batch_rows=2))

    assert observation.row_count == 3
    assert observation.source_columns == ("ID", "RA")
    assert len(frames) == 2
    assert b"".join(frames).decode("utf-8").splitlines() == [
        "1\t1.5",
        f"-99\t{module.COPY_NULL_MARKER}",
        "3\t-999",
    ]
    with pytest.raises(ValueError, match="source column boundary"):
        module.inspect_text_source(path, tuple(reversed(rows)))


def test_gate38_copy_statement_accepts_only_native_allowlisted_tables() -> None:
    """COPY must target one fixed table and all dictionary columns exactly once."""
    module = _module()
    rows = (
        {
            "source_column": "ID",
            "target_identifier": "id",
            "target_type": "bigint",
            "column_origin": "source_native",
        },
        {
            "source_column": "RA",
            "target_identifier": "ra",
            "target_type": "double precision",
            "column_origin": "source_native",
        },
    )
    assert module.gate38_copy_statement("galaxy_groups", rows) == (
        'COPY "source"."galaxy_groups" ("id", "ra") FROM STDIN WITH '
        "(FORMAT csv, DELIMITER E'\\t', NULL '__COSMOS2025_V11_SQL_NULL__')"
    )
    with pytest.raises(ValueError, match="outside Gate 3.8"):
        module.gate38_copy_statement("photometry_primary", rows)
    with pytest.raises(ValueError, match="native dictionary"):
        module.gate38_copy_statement(
            "galaxy_groups", ({**rows[0], "column_origin": "source_row_metadata"},)
        )


def test_table_load_evidence_and_reverse_plan_require_exact_committed_rows() -> None:
    """A partial/unpinned load cannot seal or widen failure cleanup."""
    module = _module()
    exact = module.TableLoadEvidence(
        table="lss_overdensity",
        source_rows=3,
        loaded_rows=3,
        declared_bytes=10,
        observed_bytes=10,
        declared_sha256="a" * 64,
        observed_sha256="a" * 64,
        committed=True,
    )
    module.validate_table_load_evidence(exact)
    assert module.gate38_cleanup_plan(("lss_overdensity", "galaxy_groups")) == (
        "galaxy_groups",
        "lss_overdensity",
    )
    with pytest.raises(ValueError, match="load evidence"):
        module.validate_table_load_evidence(
            module.TableLoadEvidence(**{**exact.__dict__, "loaded_rows": 2})
        )
    with pytest.raises(ValueError, match="cleanup boundary"):
        module.gate38_cleanup_plan(("lss_overdensity", "photometry_primary"))


def test_one_table_load_streams_real_frames_and_commits_only_exact_count(
    tmp_path: Path,
) -> None:
    """A table transaction must commit only after source/COPY counts agree."""
    module = _module()
    path = tmp_path / "groups.txt"
    path.write_text("ID RA\n1 1.5\n2 -99\n", encoding="utf-8")
    rows = (
        {
            "source_column": "ID",
            "target_identifier": "id",
            "target_type": "bigint",
            "column_origin": "source_native",
        },
        {
            "source_column": "RA",
            "target_identifier": "ra",
            "target_type": "double precision",
            "column_origin": "source_native",
        },
    )

    class Result:
        def fetchone(self):
            return (2,)

    class Copy:
        def __init__(self):
            self.frames = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def write(self, frame):
            self.frames.append(frame)

    class Cursor:
        def __init__(self, copy):
            self.copy_handle = copy

        def copy(self, statement):
            assert 'COPY "source"."galaxy_groups"' in statement
            return self.copy_handle

    class Connection:
        def __init__(self):
            self.copy_handle = Copy()
            self.commits = 0
            self.rollbacks = 0

        def cursor(self):
            return Cursor(self.copy_handle)

        def execute(self, _statement):
            return Result()

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

    connection = Connection()
    pin = SimpleNamespace(
        declared_bytes=path.stat().st_size,
        observed_bytes=path.stat().st_size,
        declared_sha256="b" * 64,
        observed_sha256="b" * 64,
    )

    evidence = module.load_gate38_table(
        connection,
        "galaxy_groups",
        path,
        rows,
        pin,
        batch_rows=1,
    )

    assert evidence.source_rows == evidence.loaded_rows == 2
    assert evidence.committed is True
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert b"".join(connection.copy_handle.frames) == b"1\t1.5\n2\t-99\n"


def test_failure_reversal_truncates_only_committed_gate38_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Post-commit failure cleanup must never target master/admin resources."""
    module = _module()
    statements = []

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, statement):
            rendered = (
                statement.as_string(None)
                if hasattr(statement, "as_string")
                else statement
            )
            statements.append(rendered)
            if rendered.startswith("SELECT count(*)"):
                return Result((0,))
            return Result((None,))

        def commit(self):
            return None

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection())
    reversed_tables = module.cleanup_committed_gate38_rows(
        object(), ("lss_overdensity", "galaxy_groups")
    )

    assert reversed_tables == ("galaxy_groups", "lss_overdensity")
    truncates = [
        statement for statement in statements if statement.startswith("TRUNCATE")
    ]
    assert truncates == [
        'TRUNCATE "source"."galaxy_groups"',
        'TRUNCATE "source"."lss_overdensity"',
    ]
    rendered = "\n".join(statements)
    assert "photometry_primary" not in rendered
    assert "DROP" not in rendered
    assert "ROLE" not in rendered


def test_failure_diagnostic_is_redacted_and_reports_exact_row_reversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lifecycle errors must hide messages while exposing safe reversal evidence."""
    module = _module()
    calls = []
    monkeypatch.setattr(
        module,
        "cleanup_committed_gate38_rows",
        lambda _settings, committed: (
            calls.append(committed) or tuple(reversed(committed))
        ),
    )

    class InjectedFailure(Exception):
        sqlstate = "XX001"

    secret = "never-print-this-secret"
    failure = module.build_gate38_failure_after_cleanup(
        object(),
        ("lss_overdensity", "galaxy_groups"),
        stage="verify_admin",
        error=InjectedFailure(secret),
    )
    rendered = str(failure)
    assert secret not in rendered
    assert "stage=verify_admin" in rendered
    assert "exception=InjectedFailure" in rendered
    assert "sqlstate=XX001" in rendered
    assert "reversed=galaxy_groups,lss_overdensity" in rendered
    assert calls == [("lss_overdensity", "galaxy_groups")]


def test_analyst_verifier_selects_all_four_and_retains_negative_matrix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Analyst verification must add four SELECTs without weakening denials."""
    module = _module()
    counts = {
        "lss_overdensity": 2,
        "galaxy_groups": 3,
        "galaxy_group_memberships": 4,
        "specz_compilation": 5,
    }

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def execute(self, statement):
            rendered = statement.as_string(None)
            table = next(table for table in counts if f'"{table}"' in rendered)
            return Result((counts[table],))

        def rollback(self):
            return None

    @contextmanager
    def impersonated(_settings):
        yield Connection()

    monkeypatch.setattr(module, "_impersonated_analyst", impersonated)
    monkeypatch.setattr(
        module,
        "_master_negative_matrix",
        lambda _settings: {"positive": 1, "negative": 11, "unchanged": True},
    )
    monkeypatch.setattr(
        module,
        "verify_gate38_table_denials",
        lambda _settings, _counts: {"positive": 4, "negative": 24, "unchanged": True},
    )

    evidence = module.verify_gate38_analyst(object(), counts)
    assert evidence == {
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
        "supplement_selects": counts,
        "supplement_matrix": {"positive": 4, "negative": 24, "unchanged": True},
        "master_matrix": {"positive": 1, "negative": 11, "unchanged": True},
    }


def test_admin_observation_requires_exact_counts_flags_and_empty_provenance() -> None:
    """Admin verification must reject drift without forcing historical priors."""
    module = _module()
    source_counts = {
        "lss_overdensity": 2,
        "galaxy_groups": 3,
        "galaxy_group_memberships": 4,
        "specz_compilation": 5,
    }
    flags = {-99: 1, 3: 1, 4: 2, 9: 1}
    exact = module.validate_gate38_admin_observation(
        source_counts=source_counts,
        target_counts={**source_counts, "provenance": 0},
        source_flags=module.summarize_quality_flags([-99, 3, 4, 4, 9]),
        target_flags=module.summarize_quality_flags([-99, 3, 4, 4, 9]),
        primary_specz_matches=2,
    )
    assert exact["quality_flags"]["distribution"] == flags
    assert exact["quality_flags"]["flags_3_or_4"] == 3
    assert exact["quality_flags"]["flag_9"] == 1
    assert exact["primary_specz_matches"] == 2
    assert exact["live_prior"] == 37_219
    assert exact["discrepancy"] == -37_217
    with pytest.raises(ValueError, match="count mismatch"):
        module.validate_gate38_admin_observation(
            source_counts=source_counts,
            target_counts={**source_counts, "provenance": 1},
            source_flags=module.summarize_quality_flags([-99, 3, 4, 4, 9]),
            target_flags=module.summarize_quality_flags([-99, 3, 4, 4, 9]),
            primary_specz_matches=2,
        )


def test_analyst_grant_is_exact_four_table_allowlist() -> None:
    """The gate may extend SELECT only to its four already-created tables."""
    module = _module()
    statements = module.gate38_grant_statements()
    assert len(statements) == 4
    assert {statement.as_string(None) for statement in statements} == {
        f'GRANT SELECT ON TABLE "source"."{table}" TO "cosmos2025_v11_ro"'
        for table in module.GATE38_TABLES
    }
    rendered = "\n".join(statement.as_string(None) for statement in statements)
    assert "ALL TABLES" not in rendered
    assert "provenance" not in rendered
    assert "GRANT ALL" not in rendered


def test_persistent_handoff_validation_returns_metadata_only(tmp_path: Path) -> None:
    """Preflight must call the real Gate 3.7 validator without exposing values."""
    module = _module()
    path = tmp_path / "handoff.env"
    path.write_text(
        "PGSQL01_HOST=db.invalid\n"
        "PGSQL01_PORT=5432\n"
        "PGSQL01_COSMOS2025_V11_DB=cosmos2025_v11\n"
        "PGSQL01_COSMOS2025_V11_USER=cosmos2025_v11_ro\n"
        "PGSQL01_COSMOS2025_V11_PASSWORD=do-not-render\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    evidence = module.validate_persistent_handoff_metadata(path)
    assert evidence == {
        "regular": True,
        "mode": "0600",
        "variable_names": module.bootstrap_v11.HANDOFF_NAMES,
        "values_rendered": False,
    }
    assert "do-not-render" not in repr(evidence)


def test_retained_handoff_security_rejects_host_port_and_admin_secret_drift(
    tmp_path: Path,
) -> None:
    """Finalize must bind the handoff to config and separate analyst/admin secrets."""
    module = _module()
    repo_root = tmp_path / "repo"
    path = repo_root / "internal-files/cosmos2025-v11.env"
    path.parent.mkdir(parents=True)

    def write(host: str, port: str, secret: str) -> None:
        path.write_text(
            f"PGSQL01_HOST={host}\n"
            f"PGSQL01_PORT={port}\n"
            "PGSQL01_COSMOS2025_V11_DB=cosmos2025_v11\n"
            "PGSQL01_COSMOS2025_V11_USER=cosmos2025_v11_ro\n"
            f"PGSQL01_COSMOS2025_V11_PASSWORD={secret}\n",
            encoding="utf-8",
        )
        path.chmod(0o600)

    settings = SimpleNamespace(
        repo_root=repo_root,
        handoff_path=path,
        host="db.internal",
        port=5432,
        password="admin-only",
    )
    write("db.internal", "5432", "analyst-only")
    evidence = module.validate_retained_handoff_security(settings)
    assert evidence["values_rendered"] is False
    assert "analyst-only" not in repr(evidence)
    write("wrong.internal", "5432", "analyst-only")
    with pytest.raises(ValueError, match="host mismatch"):
        module.validate_retained_handoff_security(settings)
    write("db.internal", "9999", "analyst-only")
    with pytest.raises(ValueError, match="port mismatch"):
        module.validate_retained_handoff_security(settings)
    write("db.internal", "5432", "admin-only")
    with pytest.raises(ValueError, match="admin credential"):
        module.validate_retained_handoff_security(settings)


def test_source_observations_reconcile_to_every_sealed_profile_count() -> None:
    """A source/dictionary population drift must stop before COPY."""
    module = _module()
    contract = module.resolve_gate38_contract(CONFIG_PATH, _dictionary_rows())
    observations = {
        table: module.SourceObservation(
            module._profile_row_count(rows),
            tuple(row["source_column"] for row in rows),
        )
        for table, rows in contract.tables.items()
    }
    assert module.validate_source_observations(contract, observations) == {
        table: observation.row_count for table, observation in observations.items()
    }
    drift = dict(observations)
    drift["lss_overdensity"] = module.SourceObservation(
        observations["lss_overdensity"].row_count + 1,
        observations["lss_overdensity"].source_columns,
    )
    with pytest.raises(ValueError, match="sealed profile"):
        module.validate_source_observations(contract, drift)


def test_schema_verifier_includes_exact_nullability_and_constraint_definitions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same-named column/constraint drift must not pass the structural check."""
    module = _module()
    calls = []
    monkeypatch.setattr(
        module.verify_schema_v11_scratch,
        "_verify_objects_and_columns",
        lambda connection, rows: (
            calls.append(("objects", connection, rows)) or {"objects": 12}
        ),
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "verify_exact_retained_schema",
        lambda connection, rows: (
            calls.append(("exact", connection, rows))
            or {"column_nullability": 1416, "constraint_definitions": 192}
        ),
    )
    connection = object()
    rows = _dictionary_rows()
    assert module.verify_gate38_schema(connection, rows) == {
        "objects": 12,
        "column_nullability": 1416,
        "constraint_definitions": 192,
    }
    assert [call[0] for call in calls] == ["objects", "exact"]


def test_supplement_negative_matrix_denies_writes_and_ddl_on_every_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All four new SELECT grants must retain per-table write/DDL denial."""
    module = _module()
    counts = {table: index + 1 for index, table in enumerate(module.GATE38_TABLES)}

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __init__(self):
            self.rollbacks = 0

        def execute(self, statement):
            rendered = statement.as_string(None)
            if rendered.startswith("SELECT count(*)"):
                table = next(table for table in counts if f'"{table}"' in rendered)
                return Result((counts[table],))
            raise module.psycopg.errors.InsufficientPrivilege("redacted")

        def rollback(self):
            self.rollbacks += 1

    connection = Connection()

    @contextmanager
    def impersonated(_settings):
        yield connection

    monkeypatch.setattr(module, "_impersonated_analyst", impersonated)
    evidence = module.verify_gate38_table_denials(
        SimpleNamespace(user="clusteradmin_pg01"), counts
    )
    assert evidence == {"positive": 4, "negative": 24, "unchanged": True}
    assert connection.rollbacks == 28


def test_no_grant_probe_requires_admin_option_instead_of_table_warning_noop() -> None:
    """The deterministic grant probe must require an unavailable ADMIN OPTION."""
    module = _module()
    operations = module._gate38_denied_operations(
        "lss_overdensity", "clusteradmin_pg01"
    )
    grant = operations[-1].as_string(None)
    assert grant == 'GRANT "clusteradmin_pg01" TO "cosmos2025_v11_ro"'
    assert "PUBLIC" not in grant
    assert "ON TABLE" not in grant


def test_load_orchestration_tracks_all_commits_before_post_load_reversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A post-load failure must pass exactly four committed tables to cleanup."""
    module = _module()
    events = []
    counts = {table: index + 1 for index, table in enumerate(module.GATE38_TABLES)}
    contract = SimpleNamespace(
        paths={table: Path(f"/{table}") for table in module.GATE38_TABLES},
        tables={table: ({"source_column": "x"},) for table in module.GATE38_TABLES},
    )
    pins = {
        table: SimpleNamespace(
            declared_bytes=1,
            observed_bytes=1,
            declared_sha256="a" * 64,
            observed_sha256="a" * 64,
        )
        for table in module.GATE38_TABLES
    }
    preflight = {
        "rows": [],
        "contract": contract,
        "pins": pins,
        "sources": {
            table: module.SourceObservation(count, ("x",))
            for table, count in counts.items()
        },
        "source_flags": {"rows": counts["specz_compilation"]},
        "select_acl": {table: False for table in module.GATE38_TABLES},
        "v1_fingerprint": SimpleNamespace(sha256="v1"),
    }
    monkeypatch.setattr(
        module,
        "final_gate38_preflight",
        lambda _settings: events.append("preflight") or preflight,
    )

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection())

    def load(_connection, table, _path, _rows, pin, *, batch_rows):
        assert events[0] == "preflight"
        events.append(table)
        return module.TableLoadEvidence(
            table,
            counts[table],
            counts[table],
            pin.declared_bytes,
            pin.observed_bytes,
            pin.declared_sha256,
            pin.observed_sha256,
            True,
        )

    monkeypatch.setattr(module, "load_gate38_table", load)
    monkeypatch.setattr(
        module,
        "apply_gate38_select_grants",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("hidden")),
    )
    cleanup_calls = []

    def failure(
        _settings,
        committed,
        *,
        stage,
        error,
        loads_sealed,
        granted_tables,
        expected_counts,
    ):
        cleanup_calls.append(
            (
                tuple(committed),
                stage,
                type(error).__name__,
                loads_sealed,
                tuple(granted_tables),
                dict(expected_counts),
            )
        )
        return module.Gate38Failure("safe")

    monkeypatch.setattr(module, "build_gate38_failure_after_cleanup", failure)
    with pytest.raises(module.Gate38Failure, match="safe"):
        module.run_gate38_load(SimpleNamespace(copy_batch_rows=2))
    assert events == ["preflight", *module.GATE38_TABLES]
    assert cleanup_calls == [
        (
            module.GATE38_TABLES,
            "grant_analyst_select",
            "RuntimeError",
            True,
            module.GATE38_TABLES,
            counts,
        )
    ]


def test_verify_only_orchestration_preserves_provenance_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read-only mode must expose Gate 3.9 evidence without inserting provenance."""
    module = _module()
    counts = {table: index + 1 for index, table in enumerate(module.GATE38_TABLES)}
    rows = _dictionary_rows()
    contract = module.resolve_gate38_contract(CONFIG_PATH, rows)
    pins = {
        table: SimpleNamespace(
            declared_bytes=1,
            observed_bytes=1,
            declared_sha256="a" * 64,
            observed_sha256="a" * 64,
        )
        for table in module.GATE38_TABLES
    }
    monkeypatch.setattr(
        module.bootstrap_v11, "_read_dictionary", lambda _settings: rows
    )
    monkeypatch.setattr(module, "resolve_gate38_contract", lambda *_args: contract)
    monkeypatch.setattr(module, "fresh_gate38_pins", lambda *_args: pins)
    monkeypatch.setattr(
        module,
        "_source_observations",
        lambda _contract: {
            table: module.SourceObservation(
                count,
                tuple(row["source_column"] for row in contract.tables[table]),
            )
            for table, count in counts.items()
        },
    )
    monkeypatch.setattr(module, "validate_source_observations", lambda *_args: counts)
    monkeypatch.setattr(
        module,
        "_source_quality_flags",
        lambda _contract: {"rows": counts["specz_compilation"]},
    )
    monkeypatch.setattr(module, "verify_gate38_admin", lambda *_args: {"ok": True})
    monkeypatch.setattr(module, "verify_gate38_analyst", lambda *_args: {"ok": True})
    monkeypatch.setattr(
        module, "validate_retained_handoff_security", lambda _settings: {"mode": "0600"}
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "capture_v1_fingerprint",
        lambda _settings: SimpleNamespace(sha256="v1"),
    )
    settings = SimpleNamespace(config_path=CONFIG_PATH, handoff_path=Path("ignored"))
    result = module.run_gate38_verify_only(settings)
    assert result["mode"] == "verify-only"
    assert result["provenance_rows"] == 0
    assert result["supplement_versions_for_gate_3_9"] == {
        "lss_overdensity": module.SUPPLEMENT_VERSION,
        "galaxy_groups": module.SUPPLEMENT_VERSION,
        "galaxy_group_memberships": module.SUPPLEMENT_VERSION,
    }


def test_cli_redacts_unexpected_exception_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Direct CLI failures may emit class/SQLSTATE but never exception text."""
    module = _module()
    secret = "never-render-this-message"
    monkeypatch.setattr(
        module.bootstrap_v11, "resolve_settings", lambda _path: object()
    )
    monkeypatch.setattr(
        module,
        "run_gate38_verify_only",
        lambda _settings: (_ for _ in ()).throw(ValueError(secret)),
    )
    assert module.main(["--verify-only"]) == 1
    captured = capsys.readouterr()
    assert secret not in captured.out + captured.err
    assert "stage=cli exception=ValueError sqlstate=none" in captured.err


def test_final_preflight_invokes_exact_schema_master_empty_and_handoff_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The immediately-before-load boundary must compose every persistent guard."""
    module = _module()
    events = []
    rows = _dictionary_rows()
    contract = module.resolve_gate38_contract(CONFIG_PATH, rows)
    sources = {
        table: module.SourceObservation(
            module._profile_row_count(table_rows),
            tuple(row["source_column"] for row in table_rows),
        )
        for table, table_rows in contract.tables.items()
    }
    monkeypatch.setattr(
        module.bootstrap_v11, "_read_dictionary", lambda _settings: rows
    )
    monkeypatch.setattr(module, "resolve_gate38_contract", lambda *_args: contract)
    monkeypatch.setattr(
        module, "fresh_gate38_pins", lambda *_args: events.append("pins") or {}
    )
    monkeypatch.setattr(
        module,
        "_source_observations",
        lambda _contract: events.append("sources") or sources,
    )

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def rollback(self):
            events.append("rollback")

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection())
    monkeypatch.setattr(
        module,
        "verify_gate38_schema",
        lambda *_args: events.append("schema") or {"exact": True},
    )
    monkeypatch.setattr(
        module,
        "_target_counts",
        lambda *_args: (
            events.append("empty") or {table: 0 for table in module.GATE38_EMPTY_TABLES}
        ),
    )
    monkeypatch.setattr(
        module,
        "_master_invariants",
        lambda *_args: events.append("masters") or {"primary_rows": 784_016},
    )
    role = module.bootstrap_v11.RoleObservation(
        True, False, False, False, False, False, False, True, 0, 0
    )
    monkeypatch.setattr(module.bootstrap_v11, "_role_observation", lambda _c: role)
    monkeypatch.setattr(
        module.bootstrap_v11, "validate_role_observation", lambda _r: None
    )
    monkeypatch.setattr(
        module,
        "validate_retained_handoff_security",
        lambda _settings: events.append("handoff") or {"mode": "0600"},
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "capture_v1_fingerprint",
        lambda _settings: SimpleNamespace(sha256="v1"),
    )
    monkeypatch.setattr(
        module,
        "_source_quality_flags",
        lambda _contract: {
            "rows": sources["specz_compilation"].row_count,
            "distribution": {},
        },
    )
    monkeypatch.setattr(
        module,
        "gate38_select_acl",
        lambda _settings: {table: True for table in module.GATE38_TABLES},
    )
    settings = SimpleNamespace(config_path=CONFIG_PATH, handoff_path=Path("ignored"))
    result = module.final_gate38_preflight(settings)
    assert result["empty_counts"] == {table: 0 for table in module.GATE38_EMPTY_TABLES}
    assert events == [
        "pins",
        "sources",
        "schema",
        "empty",
        "masters",
        "rollback",
        "handoff",
    ]


def test_admin_verifier_invokes_full_value_role_privilege_and_acl_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admin verification must compose structure, fidelity, role, and ACL checks."""
    module = _module()
    events = []
    rows = _dictionary_rows()
    counts = {table: index + 1 for index, table in enumerate(module.GATE38_TABLES)}
    flags = module.summarize_quality_flags([-99, 3, 4, 9])

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

        def fetchone(self):
            return self.rows

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, statement):
            if "GROUP BY flag" in statement:
                return Result([(-99, 1), (3, 1), (4, 1), (9, 1)])
            if 'JOIN "source"."specz_compilation"' in statement:
                return Result((2, 2))
            raise AssertionError(statement)

        def rollback(self):
            events.append("rollback")

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection())
    monkeypatch.setattr(
        module,
        "verify_gate38_schema",
        lambda *_args: events.append("schema") or {"exact": True},
    )
    monkeypatch.setattr(
        module,
        "_target_counts",
        lambda *_args: {**counts, "provenance": 0},
    )
    monkeypatch.setattr(module.bootstrap_v11, "_verify_null_counts", lambda *_args: 0)
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_verify_arrays",
        lambda *_args: {"columns": 0, "null_elements": 0},
    )
    monkeypatch.setattr(module.bootstrap_v11, "_verify_sentinels", lambda *_args: 0)
    role = module.bootstrap_v11.RoleObservation(
        True, False, False, False, False, False, False, True, 0, 0
    )
    monkeypatch.setattr(module.bootstrap_v11, "_role_observation", lambda _c: role)
    monkeypatch.setattr(
        module.bootstrap_v11, "validate_role_observation", lambda _r: None
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_verify_privilege_contract",
        lambda _c: events.append("privileges") or {"exact": True},
    )
    monkeypatch.setattr(
        module,
        "_verify_gate38_acl",
        lambda _c: events.append("acl") or {"exact": True},
    )
    result = module.verify_gate38_admin(object(), rows, counts, flags)
    assert result["provenance_rows"] == 0
    assert result["primary_specz_matches"] == 2
    assert events == ["schema", "privileges", "acl", "rollback"]


def test_context_exit_failure_cannot_escape_first_table_cleanup_tracking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A commit followed by context-exit failure must still reverse that table."""
    module = _module()
    table = module.GATE38_TABLES[0]
    contract = SimpleNamespace(
        paths={name: Path(f"/{name}") for name in module.GATE38_TABLES},
        tables={name: ({"source_column": "x"},) for name in module.GATE38_TABLES},
    )
    pins = {
        name: SimpleNamespace(
            declared_bytes=1,
            observed_bytes=1,
            declared_sha256="a" * 64,
            observed_sha256="a" * 64,
        )
        for name in module.GATE38_TABLES
    }
    monkeypatch.setattr(
        module,
        "final_gate38_preflight",
        lambda _settings: {
            "rows": [],
            "contract": contract,
            "pins": pins,
            "sources": {
                name: module.SourceObservation(1, ("x",))
                for name in module.GATE38_TABLES
            },
            "source_flags": {"rows": 1},
            "select_acl": {name: False for name in module.GATE38_TABLES},
            "v1_fingerprint": SimpleNamespace(sha256="v1"),
        },
    )

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            raise KeyboardInterrupt

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection())
    monkeypatch.setattr(
        module,
        "load_gate38_table",
        lambda _connection, name, _path, _rows, pin, *, batch_rows: (
            module.TableLoadEvidence(
                name,
                1,
                1,
                pin.declared_bytes,
                pin.observed_bytes,
                pin.declared_sha256,
                pin.observed_sha256,
                True,
            )
        ),
    )
    calls = []

    def failure(
        _settings,
        committed,
        *,
        stage,
        error,
        loads_sealed,
        granted_tables,
        expected_counts,
    ):
        calls.append(
            (
                tuple(committed),
                stage,
                type(error).__name__,
                loads_sealed,
                tuple(granted_tables),
                dict(expected_counts),
            )
        )
        return module.Gate38Failure("safe")

    monkeypatch.setattr(module, "build_gate38_failure_after_cleanup", failure)
    with pytest.raises(module.Gate38Failure, match="safe"):
        module.run_gate38_load(SimpleNamespace(copy_batch_rows=1))
    assert calls == [
        (
            (table,),
            f"load_{table}",
            "KeyboardInterrupt",
            False,
            (),
            {name: 1 for name in module.GATE38_TABLES},
        )
    ]


def test_phase_aware_failure_cleans_preseal_but_retains_postseal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Count-validated four-table seal must switch cleanup to grant-only reversal."""
    module = _module()
    events = []
    counts = {table: index + 1 for index, table in enumerate(module.GATE38_TABLES)}
    monkeypatch.setattr(
        module,
        "cleanup_committed_gate38_rows",
        lambda _settings, tables: (
            events.append(("truncate", tuple(tables))) or tuple(reversed(tables))
        ),
    )
    monkeypatch.setattr(
        module,
        "revoke_gate38_select_grants",
        lambda _settings, tables: (
            events.append(("revoke", tuple(tables))) or tuple(tables)
        ),
    )
    monkeypatch.setattr(
        module,
        "validate_retained_gate38_counts",
        lambda _settings, expected: (
            events.append(("retain", dict(expected))) or dict(expected)
        ),
    )
    error = RuntimeError("hidden")
    preseal = module.build_gate38_failure_after_cleanup(
        object(),
        ("lss_overdensity",),
        stage="load_lss_overdensity",
        error=error,
        loads_sealed=False,
        granted_tables=(),
        expected_counts=None,
    )
    assert "reversed=lss_overdensity" in str(preseal)
    assert events == [("truncate", ("lss_overdensity",))]
    events.clear()
    postseal = module.build_gate38_failure_after_cleanup(
        object(),
        module.GATE38_TABLES,
        stage="verify_analyst",
        error=error,
        loads_sealed=True,
        granted_tables=("lss_overdensity", "galaxy_groups"),
        expected_counts=counts,
    )
    assert (
        "retained=lss_overdensity,galaxy_groups,galaxy_group_memberships,specz_compilation"
        in str(postseal)
    )
    assert "revoked=lss_overdensity,galaxy_groups" in str(postseal)
    assert events == [
        ("revoke", ("lss_overdensity", "galaxy_groups")),
        ("retain", counts),
    ]


def test_grant_application_and_reversal_touch_only_newly_missing_selects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pre-existing Gate 3.7 SELECT grants must never be claimed or revoked."""
    module = _module()
    statements = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, statement):
            statements.append(statement.as_string(None))

        def commit(self):
            return None

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection())
    prior = {
        "lss_overdensity": True,
        "galaxy_groups": False,
        "galaxy_group_memberships": True,
        "specz_compilation": False,
    }
    applied = module.apply_gate38_select_grants(object(), prior)
    assert applied == ("galaxy_groups", "specz_compilation")
    assert statements == [
        'GRANT SELECT ON TABLE "source"."galaxy_groups" TO "cosmos2025_v11_ro"',
        'GRANT SELECT ON TABLE "source"."specz_compilation" TO "cosmos2025_v11_ro"',
    ]
    statements.clear()
    revoked = module.revoke_gate38_select_grants(object(), applied)
    assert revoked == applied
    assert statements == [
        'REVOKE SELECT ON TABLE "source"."galaxy_groups" FROM "cosmos2025_v11_ro"',
        'REVOKE SELECT ON TABLE "source"."specz_compilation" FROM "cosmos2025_v11_ro"',
    ]


def test_finalize_admin_is_source_free_and_performs_no_copy_or_truncate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resume must validate retained data and restore access without source reads."""
    module = _module()
    events = []
    counts = {table: index + 1 for index, table in enumerate(module.GATE38_TABLES)}
    monkeypatch.setattr(
        module,
        "validate_retained_gate38",
        lambda _settings: (
            events.append("validate_retained")
            or {"counts": counts, "v1_fingerprint": "v1"}
        ),
    )
    monkeypatch.setattr(
        module,
        "gate38_select_acl",
        lambda _settings: {table: False for table in module.GATE38_TABLES},
    )
    monkeypatch.setattr(
        module,
        "apply_gate38_select_grants",
        lambda _settings, _prior: events.append("grant") or module.GATE38_TABLES,
    )
    monkeypatch.setattr(
        module,
        "verify_retained_gate38_admin",
        lambda *_args: events.append("verify_admin") or {"ok": True},
    )
    monkeypatch.setattr(
        module,
        "verify_gate38_analyst",
        lambda _settings, expected: (
            events.append(("verify_analyst", dict(expected))) or {"ok": True}
        ),
    )
    monkeypatch.setattr(
        module,
        "fresh_gate38_pins",
        lambda *_args: (_ for _ in ()).throw(AssertionError("source read")),
    )
    monkeypatch.setattr(
        module,
        "_source_observations",
        lambda *_args: (_ for _ in ()).throw(AssertionError("source read")),
    )
    result = module.run_gate38_finalize_admin(object())
    assert events == [
        "validate_retained",
        "grant",
        "verify_admin",
        ("verify_analyst", counts),
    ]
    assert result["mode"] == "finalize-admin"
    assert result["source_reads"] == 0
    assert result["copy_operations"] == 0
    assert result["truncate_operations"] == 0


def test_cli_accepts_guarded_finalize_admin_mode() -> None:
    """Administration resume must be explicit and mutually exclusive."""
    module = _module()
    arguments = module.parse_args(["--finalize-admin"])
    assert arguments.finalize_admin is True
    assert arguments.load is False
    assert arguments.verify_only is False
