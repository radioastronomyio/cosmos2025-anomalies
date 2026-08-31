#!/usr/bin/env python3
"""
Script Name  : test_bootstrap_v11.py
Description  : Test guarded persistent ETL v2 bootstrap and verification
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises Gate 3.7 conversion, fixed-target, fingerprint, role, handoff,
verification, and cleanup contracts without authenticating or touching a live
database. The one persistent lifecycle remains exclusive to the Doppler-backed
production CLI.

Usage
-----
    pytest tests/test_bootstrap_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import ast
import contextlib
import csv
import hashlib
import importlib.util
import inspect
import io
import math
import os
import re
import runpy
import stat
import sys
from pathlib import Path

import numpy as np
import psycopg
import pytest
import yaml

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "bootstrap_v11.py"


# =============================================================================
# Test utilities
# =============================================================================


def _module():
    """Load production only after test start so missing code is a RED failure."""
    assert MODULE_PATH.exists(), "Gate 3.7 bootstrap module is missing"
    spec = importlib.util.spec_from_file_location("bootstrap_v11", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _config(tmp_path: Path) -> Path:
    """Write a complete isolated configuration with named environment keys."""
    path = tmp_path / "config.yaml"
    payload = {
        "repo_root": str(tmp_path),
        "database": {
            "host_env": "TEST_HOST",
            "port_env": "TEST_PORT",
            "user_env": "TEST_ADMIN_USER",
            "password_env": "TEST_ADMIN_PASSWORD",
            "maintenance_database": "postgres",
            "database_name": "cosmos2025",
            "target_database": "cosmos2025_v11",
            "analyst_role": "cosmos2025_v11_ro",
        },
        "dictionary": {
            "columns_v11": str(REPO_ROOT / "data/dictionary/columns-v11.csv"),
            "schema_v11_sql": str(REPO_ROOT / "src/etl/schema_v11.sql"),
        },
        "provenance": {
            "source_manifest_v11": str(
                REPO_ROOT / "docs/reference/data-manifest-v1.1.csv"
            )
        },
        "handoff": {
            "cosmos2025_v11_env": str(
                tmp_path / "internal-files" / "cosmos2025-v11.env"
            ),
        },
        "etl_v2": {"copy_batch_rows": 1000, "minimum_database_free_bytes": 1},
    }
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


# =============================================================================
# Fixed target and persistent-state guards
# =============================================================================


def test_config_resolves_only_fixed_targets_and_environment_names(
    tmp_path: Path,
) -> None:
    """A renamed database, role, baseline, handoff, or literal secret must halt."""
    module = _module()
    path = _config(tmp_path)
    environment = {
        "TEST_HOST": "db-alias",
        "TEST_PORT": "5432",
        "TEST_ADMIN_USER": "bootstrap_owner",
        "TEST_ADMIN_PASSWORD": "admin-test-secret",
    }
    settings = module.resolve_settings(path, environment)
    assert settings.baseline_database == "cosmos2025"
    assert settings.target_database == "cosmos2025_v11"
    assert settings.analyst_role == "cosmos2025_v11_ro"
    assert settings.handoff_path == tmp_path / "internal-files/cosmos2025-v11.env"
    assert settings.password == "admin-test-secret"

    config = yaml.safe_load(path.read_text())
    for key, wrong in (
        ("database_name", "cosmos2025_other"),
        ("target_database", "cosmos2025_v11_other"),
        ("analyst_role", "cosmos2025_v11_rw"),
    ):
        mutated = yaml.safe_load(path.read_text())
        mutated["database"][key] = wrong
        path.write_text(yaml.safe_dump(mutated), encoding="utf-8")
        with pytest.raises(ValueError, match="fixed Gate 3.7 target"):
            module.resolve_settings(path, environment)
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    environment.pop("TEST_ADMIN_PASSWORD")
    with pytest.raises(ValueError) as error:
        module.resolve_settings(path, environment)
    assert "TEST_ADMIN_PASSWORD" in str(error.value)
    assert "admin-test-secret" not in str(error.value)


def test_final_absence_guard_rejects_each_preexisting_resource(tmp_path: Path) -> None:
    """Any pre-existing target resource must prevent a create/load rerun."""
    module = _module()
    handoff = tmp_path / "cosmos2025-v11.env"
    module.assert_targets_absent(
        database_names={"cosmos2025"}, role_names=set(), handoff_path=handoff
    )
    with pytest.raises(ValueError, match="target database already exists"):
        module.assert_targets_absent(
            database_names={"cosmos2025", "cosmos2025_v11"},
            role_names=set(),
            handoff_path=handoff,
        )
    with pytest.raises(ValueError, match="target role already exists"):
        module.assert_targets_absent(
            database_names={"cosmos2025"},
            role_names={"cosmos2025_v11_ro"},
            handoff_path=handoff,
        )
    handoff.write_text("occupied", encoding="utf-8")
    with pytest.raises(ValueError, match="handoff already exists"):
        module.assert_targets_absent(
            database_names={"cosmos2025"}, role_names=set(), handoff_path=handoff
        )


@pytest.mark.parametrize(
    ("kind", "name"),
    [
        ("database", "cosmos2025"),
        ("database", "postgres"),
        ("database", "cosmos2025_v11_extra"),
        ("role", "postgres"),
        ("role", "cosmos2025_v11_ro_extra"),
        ("handoff", "/tmp/cosmos2025-v11.env"),
    ],
)
def test_cleanup_target_validation_cannot_broaden(kind: str, name: str) -> None:
    """Cleanup must reject every resource outside the exact configured target."""
    module = _module()
    with pytest.raises(ValueError, match="refusing unsafe cleanup target"):
        module.validate_cleanup_target(
            kind,
            name,
            expected_handoff=REPO_ROOT / "internal-files/cosmos2025-v11.env",
        )


def test_cleanup_plan_contains_only_resources_created_by_this_process() -> None:
    """A failed run must never reverse a target it did not mark as created."""
    module = _module()
    state = module.CreatedResources(database=True, role=False, handoff=True)
    assert module.cleanup_plan(state) == ("handoff", "database")
    assert module.cleanup_plan(module.CreatedResources()) == ()


# =============================================================================
# Lossless source-to-COPY conversion
# =============================================================================


def test_copy_text_escaping_covers_all_postgresql_control_characters() -> None:
    """Removing one COPY escape must corrupt a real text value boundary."""
    module = _module()
    value = 'tab\tline\nslash\\quote"carriage\rend'
    assert module.copy_text_field(value) == 'tab\\tline\\nslash\\\\quote"carriage\\rend'
    assert module.copy_text_field("") == ""
    assert module.copy_text_field(None) == r"\N"


def test_scalar_conversion_preserves_types_sentinels_infinities_and_signed_zero() -> (
    None
):
    """Cleaning or coercing one valid scalar must change the literal output."""
    module = _module()
    assert module.source_scalar(-999, masked=False) == -999
    assert module.source_scalar(99.0, masked=False) == 99.0
    assert module.source_scalar(np.int32(-7), masked=False) == -7
    assert module.source_scalar(np.bool_(True), masked=False) is True
    assert module.source_scalar(np.bytes_(b"A B"), masked=False) == "A B"
    assert module.source_scalar(float("inf"), masked=False) == float("inf")
    assert module.source_scalar(float("-inf"), masked=False) == float("-inf")
    signed_zero = module.source_scalar(np.float64(-0.0), masked=False)
    assert math.copysign(1.0, signed_zero) == -1.0
    assert module.source_scalar(123, masked=True) is None
    assert module.source_scalar(float("nan"), masked=False) is None


def test_float32_and_float64_copy_literals_round_trip() -> None:
    """Shortening a float literal past its round-trip boundary must lose bits."""
    module = _module()
    for value in (np.float32(1.234567), np.float64(1.2345678901234567)):
        literal = module.copy_scalar_literal(value)
        restored = np.asarray(float(literal), dtype=value.dtype)[()]
        assert restored.tobytes() == np.asarray(value).tobytes()
    assert module.copy_scalar_literal(np.float64(-0.0)) == "-0.0"
    assert module.copy_scalar_literal(float("inf")) == "Infinity"
    assert module.copy_scalar_literal(float("-inf")) == "-Infinity"


def test_array_conversion_preserves_shape_null_elements_and_escaping() -> None:
    """Dropping masks, NaNs, or array quoting must change the array literal."""
    module = _module()
    values = np.asarray([1.0, np.nan, -999.0, np.inf, -0.0])
    converted = module.source_array(
        values, mask=np.asarray([False, False, True, False, False])
    )
    assert converted[0] == 1.0
    assert converted[1] is None
    assert converted[2] is None
    assert converted[3] == float("inf")
    assert math.copysign(1.0, converted[4]) == -1.0
    assert module.postgres_array_literal(converted) == "{1.0,NULL,NULL,Infinity,-0.0}"
    assert module.postgres_array_literal(["a,b", 'q"', r"x\y", None]) == (
        r'{"a,b","q\"","x\\y",NULL}'
    )


def test_copy_row_follows_dictionary_order_and_injects_only_declared_metadata() -> None:
    """Reordering fields or deriving extra metadata must change the emitted row."""
    module = _module()
    rows = [
        {"source_column": "native_b", "column_origin": "source_native"},
        {"source_column": "", "column_origin": "source_row_metadata"},
        {"source_column": "native_a", "column_origin": "source_native"},
        {"source_column": "", "column_origin": "id_injected"},
    ]
    line = module.build_copy_row(
        rows,
        native_values={"native_a": "A", "native_b": "B"},
        source_row=7,
        primary_id=42,
    )
    assert line == b"B\t7\tA\t42\n"


# =============================================================================
# Fingerprint, role, permission, and handoff contracts
# =============================================================================


def test_fingerprint_serialization_is_ordered_deterministic_and_secret_free() -> None:
    """Catalog query order or credential text must not affect a v1 fingerprint."""
    module = _module()
    left = {
        "database_owner": "owner",
        "schemas": [{"name": "b", "owner": "o2"}, {"name": "a", "owner": "o1"}],
        "tables": [
            {"schema": "b", "table": "z", "owner": "o2", "rows": 2},
            {"schema": "a", "table": "x", "owner": "o1", "rows": 1},
        ],
    }
    right = {
        "tables": list(reversed(left["tables"])),
        "schemas": list(reversed(left["schemas"])),
        "database_owner": "owner",
    }
    first = module.serialize_fingerprint(left)
    second = module.serialize_fingerprint(right)
    assert first.content == second.content
    assert first.sha256 == second.sha256
    assert b"password" not in first.content.lower()


def test_role_sql_enforces_exact_read_only_contract() -> None:
    """A widened analyst attribute or grant must change the reviewed SQL contract."""
    module = _module()
    statements = module.role_statements("bootstrap_owner")
    rendered = "\n".join(statements)
    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN" in rendered
    assert 'REVOKE ALL PRIVILEGES ON DATABASE "cosmos2025_v11" FROM PUBLIC' in rendered
    assert 'REVOKE ALL ON SCHEMA "source" FROM PUBLIC' in rendered
    assert 'REVOKE ALL ON SCHEMA "public" FROM PUBLIC' in rendered
    assert 'GRANT CONNECT ON DATABASE "cosmos2025_v11"' in rendered
    assert 'GRANT USAGE ON SCHEMA "source"' in rendered
    assert 'GRANT SELECT ON ALL TABLES IN SCHEMA "source"' in rendered
    assert 'ALTER DEFAULT PRIVILEGES FOR ROLE "bootstrap_owner"' in rendered
    assert "GRANT SELECT ON TABLES" in rendered
    assert "GRANT CREATE" not in rendered


def test_role_password_plan_never_places_secret_in_utility_sql() -> None:
    """A CREATE ROLE placeholder or secret-bearing SQL text must fail the contract."""
    module = _module()
    secret = "Safe_secret-123_" * 4
    plan = module.role_password_plan("cosmos2025_v11_ro", secret)
    assert plan.create_sql == (
        'CREATE ROLE "cosmos2025_v11_ro" NOSUPERUSER NOCREATEDB '
        "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS LOGIN"
    )
    assert plan.set_config_sql == (
        "SELECT pg_catalog.set_config('cosmos2025_v11.analyst_password', %s, true)"
    )
    assert plan.set_config_parameters == (secret,)
    assert "current_setting('cosmos2025_v11.analyst_password')" in plan.apply_sql
    assert secret not in plan.create_sql + plan.set_config_sql + plan.apply_sql
    assert "$1" not in plan.create_sql + plan.apply_sql


def test_analyst_verification_uses_admin_session_impersonation_only() -> None:
    """The operator override must prohibit a direct analyst network connection."""
    module = _module()
    plan = module.analyst_verification_plan("clusteradmin_pg01", "cosmos2025_v11_ro")
    assert plan.authenticated_user == "clusteradmin_pg01"
    assert plan.effective_user == "cosmos2025_v11_ro"
    assert plan.set_authorization_sql == (
        'SET SESSION AUTHORIZATION "cosmos2025_v11_ro"'
    )
    assert plan.reset_authorization_sql == "RESET SESSION AUTHORIZATION"
    assert plan.direct_network_auth_exercised is False
    assert "PASSWORD" not in (plan.set_authorization_sql + plan.reset_authorization_sql)
    assert (
        "analyst_secret"
        not in inspect.signature(module.verify_analyst_matrix).parameters
    )
    assert (
        "analyst_secret"
        not in inspect.signature(module.verify_default_privileges).parameters
    )


def test_analyst_impersonation_survives_matrix_rollbacks_and_resets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Session transitions must commit while denied operations remain rollback-safe."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __init__(self):
            self.current = "bootstrap_owner"
            self.pending = None
            self.commits = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, statement):
            if statement == "SELECT current_user":
                return Result((self.current,))
            if statement.startswith("SET SESSION AUTHORIZATION"):
                self.pending = "cosmos2025_v11_ro"
                return Result(None)
            if statement == "RESET SESSION AUTHORIZATION":
                self.pending = "bootstrap_owner"
                return Result(None)
            if statement == "SELECT session_user, current_user":
                return Result((self.current, self.current))
            raise AssertionError(statement)

        def commit(self):
            self.current = self.pending
            self.pending = None
            self.commits += 1

        def rollback(self):
            self.pending = None

    connection = Connection()
    monkeypatch.setattr(module, "_connect", lambda *_args, **_kwargs: connection)
    with module._impersonated_analyst(settings) as observed:
        assert observed.current == "cosmos2025_v11_ro"
        observed.rollback()
        assert observed.current == "cosmos2025_v11_ro"
    assert connection.current == "bootstrap_owner"
    assert connection.commits == 2


def test_permission_matrix_has_required_positive_and_negative_operations() -> None:
    """Omitting one adversarial operation must shrink the literal matrix boundary."""
    module = _module()
    matrix = module.permission_matrix("bootstrap_owner")
    assert tuple(matrix) == (
        "select",
        "insert",
        "update",
        "delete",
        "create_schema",
        "create_source_table",
        "create_public_table",
        "create_temp_table",
        "alter",
        "truncate",
        "grant",
        "set_admin_role",
    )
    assert matrix["select"].allowed is True
    assert matrix["grant"].statement == (
        'GRANT "bootstrap_owner" TO "cosmos2025_v11_ro"'
    )
    assert all(not item.allowed for name, item in matrix.items() if name != "select")


def test_analyst_matrix_uses_the_verified_primary_row_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Admin finalization must not replace retained-count evidence with a literal."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )

    class Result:
        def fetchone(self):
            return (10,)

    class Connection:
        def execute(self, statement):
            if statement.startswith("SELECT count(*)"):
                return Result()
            raise psycopg.errors.InsufficientPrivilege()

        def rollback(self):
            return None

    @contextlib.contextmanager
    def impersonated(_settings):
        yield Connection()

    monkeypatch.setattr(module, "_impersonated_analyst", impersonated)
    monkeypatch.setattr(module, "_target_snapshot", lambda _connection: (70, ("t",)))
    evidence = module.verify_analyst_matrix(settings, expected_primary_rows=10)
    assert evidence["positive"] == 1
    assert evidence["negative"] == 11
    with pytest.raises(ValueError, match="analyst SELECT count"):
        module.verify_analyst_matrix(settings, expected_primary_rows=11)


def test_handoff_is_exclusive_mode_0600_exact_five_lines_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    """A partial, broad-mode, renamed, or overwritten handoff must fail validation."""
    module = _module()
    path = tmp_path / "cosmos2025-v11.env"
    values = {
        "PGSQL01_HOST": "db-alias",
        "PGSQL01_PORT": "5432",
        "PGSQL01_COSMOS2025_V11_DB": "cosmos2025_v11",
        "PGSQL01_COSMOS2025_V11_USER": "cosmos2025_v11_ro",
        "PGSQL01_COSMOS2025_V11_PASSWORD": "Safe_secret-123",
    }
    module.write_handoff_exclusive(path, values)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    parsed = module.validate_handoff_file(path)
    assert parsed == values
    assert path.read_text(encoding="utf-8").count("\n") == 5
    with pytest.raises(FileExistsError):
        module.write_handoff_exclusive(path, values)
    os.chmod(path, 0o640)
    with pytest.raises(ValueError, match="mode 0600"):
        module.validate_handoff_file(path)


def test_generated_secret_is_shell_safe_strong_and_never_in_summary() -> None:
    """Unsafe punctuation or summary inclusion must expose the credential boundary."""
    module = _module()
    secret = module.generate_analyst_secret()
    assert len(secret) >= 48
    assert re.fullmatch(r"[A-Za-z0-9_-]+", secret)
    summary = module.public_summary(
        {"password": secret, "nested": {"analyst_secret": secret, "rows": 7}}
    )
    assert secret not in repr(summary)
    assert summary == {"nested": {"rows": 7}}


def test_handoff_variable_names_and_public_values_are_exact() -> None:
    """Adding or renaming one credential variable must fail the handoff contract."""
    module = _module()
    values = module.handoff_values(
        host="db-alias", port=5432, analyst_secret="Safe_secret-123"
    )
    assert tuple(values) == (
        "PGSQL01_HOST",
        "PGSQL01_PORT",
        "PGSQL01_COSMOS2025_V11_DB",
        "PGSQL01_COSMOS2025_V11_USER",
        "PGSQL01_COSMOS2025_V11_PASSWORD",
    )
    assert values["PGSQL01_COSMOS2025_V11_DB"] == "cosmos2025_v11"
    assert values["PGSQL01_COSMOS2025_V11_USER"] == "cosmos2025_v11_ro"


# =============================================================================
# Verification query contracts
# =============================================================================


def test_source_row_stats_detect_gap_duplicate_null_and_wrong_bounds() -> None:
    """Every source-row invariant must participate in the post-load decision."""
    module = _module()
    module.validate_source_row_stats((7, 7, 0, 6, 0), expected_rows=7)
    mutations = (
        (7, 6, 0, 6, 0),
        (7, 7, 1, 6, 0),
        (7, 7, 0, 7, 0),
        (7, 7, 0, 6, 1),
    )
    for observed in mutations:
        with pytest.raises(ValueError, match="source_row invariant"):
            module.validate_source_row_stats(observed, expected_rows=7)


def test_unloaded_table_boundary_is_exact() -> None:
    """Loading a supplement or provenance row in Gate 3.7 must fail verification."""
    module = _module()
    assert module.UNLOADED_TABLES == (
        "lss_overdensity",
        "galaxy_groups",
        "galaxy_group_memberships",
        "specz_compilation",
        "provenance",
    )
    module.validate_unloaded_counts({name: 0 for name in module.UNLOADED_TABLES})
    with pytest.raises(ValueError, match="unloaded table is nonempty"):
        module.validate_unloaded_counts(
            {
                name: (1 if name == "provenance" else 0)
                for name in module.UNLOADED_TABLES
            }
        )


def test_database_capacity_parser_requires_fresh_free_space_threshold() -> None:
    """A malformed or undersized database-volume probe must stop preflight."""
    module = _module()
    evidence = module.parse_database_capacity(
        "263085035520 33025359872 216621178880 14%"
    )
    assert evidence.total_bytes == 263_085_035_520
    assert evidence.used_bytes == 33_025_359_872
    assert evidence.available_bytes == 216_621_178_880
    module.require_database_capacity(evidence, minimum_available_bytes=200_000_000_000)
    with pytest.raises(ValueError, match="database volume capacity"):
        module.require_database_capacity(
            evidence, minimum_available_bytes=216_621_178_881
        )
    with pytest.raises(ValueError, match="capacity probe"):
        module.parse_database_capacity("not df output")


def test_copy_statement_quotes_dictionary_order_without_data_values() -> None:
    """Unquoted or reordered identifiers must alter the COPY boundary."""
    module = _module()
    statement = module.copy_statement("photometry_primary", ["id", "select", 'q"x'])
    assert statement == (
        'COPY "source"."photometry_primary" ("id", "select", "q""x") '
        "FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', "
        "NULL '__COSMOS2025_V11_SQL_NULL__')"
    )
    assert "VALUES" not in statement


def test_streaming_csv_chunk_escapes_text_and_uses_unquoted_null_marker() -> None:
    """Tabs, newlines, quotes, backslashes, empty text, and NULL must not collide."""
    module = _module()
    payload = module.serialize_copy_frame(
        [
            [
                "a\tb",
                "line\nx",
                r"slash\q",
                '"quoted"',
                "{1,NULL}",
                None,
                "",
            ]
        ],
        columns=["a", "b", "c", "d", "e", "f", "g"],
    )
    assert payload == (
        b'"a\tb"\t"line\nx"\tslash\\q\t"""quoted"""\t{1,NULL}\t'
        b"__COSMOS2025_V11_SQL_NULL__\t\n"
    )


def test_native_value_conversion_uses_tnull_nan_and_declared_metadata_only() -> None:
    """Ignoring TNULL or inventing metadata must change the extracted row mapping."""
    module = _module()
    dictionary_rows = [
        {
            "source_column": "integer_null",
            "target_identifier": "integer_null",
            "target_type": "integer",
            "column_origin": "source_native",
        },
        {
            "source_column": "vector",
            "target_identifier": "vector",
            "target_type": "real[]",
            "column_origin": "source_native",
        },
        {
            "source_column": "",
            "target_identifier": "source_row",
            "target_type": "bigint",
            "column_origin": "source_row_metadata",
        },
    ]
    columns = {
        "integer_null": np.asarray([5, -99]),
        "vector": np.asarray([[1.0, np.nan], [np.inf, -0.0]], dtype=np.float32),
    }
    first = module.native_values_at(
        dictionary_rows, columns=columns, fits_nulls={"integer_null": -99}, index=0
    )
    second = module.native_values_at(
        dictionary_rows, columns=columns, fits_nulls={"integer_null": -99}, index=1
    )
    assert first == {"integer_null": 5, "vector": [1.0, None]}
    assert second["integer_null"] is None
    assert second["vector"][0] == float("inf")
    assert math.copysign(1.0, second["vector"][1]) == -1.0


def test_vectorized_chunk_formatting_matches_scalar_lossless_rules() -> None:
    """The bulk path must retain the same mask, NaN, precision, and sign contract."""
    module = _module()
    float_row = {"target_type": "real", "source_column": "f"}
    floats = np.asarray([1.234567, -0.0, np.nan, np.inf, -np.inf], dtype=np.float32)
    assert list(module.format_native_chunk(float_row, floats, fits_null=None)) == [
        "1.23456705",
        "-0.0",
        None,
        "Infinity",
        "-Infinity",
    ]
    integer_row = {"target_type": "integer", "source_column": "i"}
    assert list(
        module.format_native_chunk(integer_row, np.asarray([5, -99]), fits_null=-99)
    ) == ["5", None]
    array_row = {"target_type": "double precision[]", "source_column": "a"}
    arrays = np.asarray([[1.0, np.nan], [np.inf, -0.0]], dtype=np.float64)
    assert list(module.format_native_chunk(array_row, arrays, fits_null=None)) == [
        "{1,NULL}",
        "{Infinity,-0.0}",
    ]


def test_role_catalog_validation_rejects_attributes_membership_and_ownership() -> None:
    """One broad attribute, membership, or owned object must fail analyst verification."""
    module = _module()
    exact = module.RoleObservation(
        login=True,
        superuser=False,
        create_database=False,
        create_role=False,
        inherit=False,
        replication=False,
        bypass_rls=False,
        scram_credential_present=True,
        memberships=0,
        owned_objects=0,
    )
    module.validate_role_observation(exact)
    for mutation in (
        module.RoleObservation(**{**exact.__dict__, "inherit": True}),
        module.RoleObservation(**{**exact.__dict__, "scram_credential_present": False}),
        module.RoleObservation(**{**exact.__dict__, "memberships": 1}),
        module.RoleObservation(**{**exact.__dict__, "owned_objects": 1}),
    ):
        with pytest.raises(ValueError, match="analyst role contract"):
            module.validate_role_observation(mutation)


def test_privilege_verifier_uses_oid_overload_and_valid_psycopg_placeholders() -> None:
    """Runtime verifier SQL must avoid client-invalid PostgreSQL format tokens."""
    module = _module()

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __init__(self):
            self.responses = iter(
                (
                    (True, False, False),
                    (True, False, False, False),
                    (True, False),
                    (0,),
                    (0,),
                )
            )
            self.parameterized = []

        def execute(self, statement, parameters=None):
            if parameters is not None:
                self.parameterized.append(statement)
                if re.search(r"%(?![%sbt])", statement):
                    raise psycopg.ProgrammingError(
                        "unsupported placeholder in verifier SQL"
                    )
            return Result(next(self.responses))

    connection = Connection()
    evidence = module._verify_privilege_contract(connection)
    assert evidence["current_tables"] == {"select": True, "write_or_ddl": False}
    assert all(
        re.search(r"%(?![%sbt])", statement) is None
        for statement in connection.parameterized
    )
    table_statement = next(
        statement
        for statement in connection.parameterized
        if "has_table_privilege" in statement
    )
    assert "format(" not in table_statement
    assert "has_table_privilege(%s, c.oid" in table_statement


def test_role_observation_escapes_scram_like_for_psycopg_parameters() -> None:
    """A literal percent must not be parsed as a psycopg value placeholder."""
    module = _module()

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def execute(self, statement, parameters):
            if "FROM pg_authid" in statement:
                assert "LIKE 'SCRAM-SHA-256$%%'" in statement
                return Result((True, False, False, False, False, False, False, True))
            return Result((0,))

    observed = module._role_observation(Connection())
    assert observed.scram_credential_present is True


def test_fingerprint_comparison_requires_byte_and_hash_identity() -> None:
    """Even a valid-looking v1 row-count change must halt the target lifecycle."""
    module = _module()
    baseline = module.serialize_fingerprint(
        {
            "database_owner": "o",
            "schemas": [{"name": "catalog", "owner": "o"}],
            "tables": [{"schema": "catalog", "table": "t", "owner": "o", "rows": 1}],
        }
    )
    module.require_fingerprint_identity(baseline, baseline)
    changed = module.serialize_fingerprint(
        {
            "database_owner": "o",
            "schemas": [{"name": "catalog", "owner": "o"}],
            "tables": [{"schema": "catalog", "table": "t", "owner": "o", "rows": 2}],
        }
    )
    with pytest.raises(ValueError, match="v1 fingerprint changed"):
        module.require_fingerprint_identity(baseline, changed)


def test_handoff_git_evidence_requires_ignored_untracked_and_secret_absent() -> None:
    """Tracked, unignored, staged, or leaked handoff evidence must halt."""
    module = _module()
    exact = module.HandoffGitEvidence(
        ignored=True,
        tracked=False,
        secret_in_tracked=False,
        secret_in_staged=False,
        secret_in_captured_outputs=False,
    )
    module.validate_handoff_git_evidence(exact)
    for field in exact.__dict__:
        value = getattr(exact, field)
        mutation = module.HandoffGitEvidence(**{**exact.__dict__, field: not value})
        with pytest.raises(ValueError, match="handoff Git/secret contract"):
            module.validate_handoff_git_evidence(mutation)


def test_execution_phase_contract_separates_non_idempotent_and_read_only_modes() -> (
    None
):
    """A verify-only invocation must never inherit a create or cleanup phase."""
    module = _module()
    assert module.execution_phases("create-load") == (
        "final_preflight",
        "create_database",
        "execute_reviewed_ddl",
        "load_master_tables",
        "create_role",
        "verify_admin",
        "write_handoff",
        "verify_analyst",
        "verify_v1_fingerprint",
        "verify_handoff_git",
    )
    assert module.execution_phases("verify-only") == (
        "read_handoff",
        "verify_admin",
        "verify_analyst",
        "verify_v1_fingerprint",
        "verify_handoff_git",
    )
    assert module.execution_phases("finalize-admin") == (
        "validate_retained_load",
        "create_role",
        "verify_admin",
        "write_handoff",
        "verify_analyst",
        "verify_v1_fingerprint",
        "verify_handoff_git",
    )
    with pytest.raises(ValueError, match="execution mode"):
        module.execution_phases("rerun")


def test_finalize_admin_requires_database_present_and_role_handoff_absent(
    tmp_path: Path,
) -> None:
    """Administration resume must accept only the exact incomplete-admin state."""
    module = _module()
    handoff = tmp_path / "internal-files" / "cosmos2025-v11.env"
    module.assert_finalize_admin_targets(
        database_names={module.TARGET_DATABASE},
        role_names=set(),
        handoff_path=handoff,
    )
    with pytest.raises(ValueError, match="retained target database is absent"):
        module.assert_finalize_admin_targets(
            database_names=set(), role_names=set(), handoff_path=handoff
        )
    with pytest.raises(ValueError, match="analyst role already exists"):
        module.assert_finalize_admin_targets(
            database_names={module.TARGET_DATABASE},
            role_names={module.ANALYST_ROLE},
            handoff_path=handoff,
        )
    handoff.parent.mkdir(parents=True)
    handoff.touch()
    with pytest.raises(ValueError, match="handoff already exists"):
        module.assert_finalize_admin_targets(
            database_names={module.TARGET_DATABASE},
            role_names=set(),
            handoff_path=handoff,
        )


def test_finalize_admin_orchestrates_without_source_reads_or_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Admin resume must validate retained rows and never re-enter extraction."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )
    calls = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def rollback(self):
            return None

    exact_role = module.RoleObservation(
        login=True,
        superuser=False,
        create_database=False,
        create_role=False,
        inherit=False,
        replication=False,
        bypass_rls=False,
        scram_credential_present=True,
        memberships=0,
        owned_objects=0,
    )
    fingerprint = module.Fingerprint(content=b"v1", sha256="a" * 64)
    git_evidence = module.HandoffGitEvidence(
        ignored=True,
        tracked=False,
        secret_in_tracked=False,
        secret_in_staged=False,
        secret_in_captured_outputs=False,
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("source/COPY path reached")

    monkeypatch.setattr(module, "final_preflight", forbidden)
    monkeypatch.setattr(module, "_manifest_contract", forbidden)
    monkeypatch.setattr(module, "_load_master_table", forbidden)
    monkeypatch.setattr(module, "_read_dictionary", lambda _settings: ["rows"])
    monkeypatch.setattr(
        module,
        "_assert_finalize_admin_live_boundary",
        lambda _settings: calls.append("boundary"),
    )
    monkeypatch.setattr(
        module,
        "validate_retained_load",
        lambda _settings, _rows: (
            calls.append("retained") or {"counts": {"photometry_primary": 10}}
        ),
    )
    monkeypatch.setattr(module, "capture_v1_fingerprint", lambda _settings: fingerprint)
    monkeypatch.setattr(module, "generate_analyst_secret", lambda: "A" * 64)
    monkeypatch.setattr(module, "_connect", lambda *_args, **_kwargs: Connection())
    monkeypatch.setattr(
        module,
        "_create_analyst_role",
        lambda *_args, **_kwargs: calls.append("role"),
    )
    monkeypatch.setattr(module, "_role_observation", lambda _connection: exact_role)
    monkeypatch.setattr(module, "_verify_privilege_contract", lambda _connection: {})
    monkeypatch.setattr(
        module,
        "verify_target_admin",
        lambda *_args, **_kwargs: (
            calls.append("admin")
            or {"status": "exact", "counts": {"photometry_primary": 10}}
        ),
    )
    monkeypatch.setattr(
        module,
        "verify_analyst_matrix",
        lambda _settings, **_kwargs: (
            calls.append("matrix") or {"positive": 1, "negative": 11}
        ),
    )
    monkeypatch.setattr(
        module,
        "verify_default_privileges",
        lambda _settings: calls.append("defaults") or {"remaining": 0},
    )
    monkeypatch.setattr(
        module,
        "write_handoff_exclusive",
        lambda *_args: calls.append("handoff"),
    )
    monkeypatch.setattr(
        module,
        "read_handoff_for_verification",
        lambda _settings: calls.append("read_handoff") or {},
    )
    monkeypatch.setattr(
        module,
        "verify_handoff_git",
        lambda *_args, **_kwargs: calls.append("git") or git_evidence,
    )

    result = module.run_finalize_admin(settings)

    assert result["mode"] == "finalize-admin"
    assert result["status"] == "passed"
    assert result["retained_load_validation"] == {"counts": {"photometry_primary": 10}}
    assert calls == [
        "boundary",
        "retained",
        "role",
        "admin",
        "matrix",
        "defaults",
        "handoff",
        "read_handoff",
        "matrix",
        "git",
    ]


def test_finalize_admin_failure_cleans_role_and_retains_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resumed post-seal failure must never delete the validated database."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def rollback(self):
            return None

    exact_role = module.RoleObservation(
        login=True,
        superuser=False,
        create_database=False,
        create_role=False,
        inherit=False,
        replication=False,
        bypass_rls=False,
        scram_credential_present=True,
        memberships=0,
        owned_objects=0,
    )
    cleanup_calls = []
    monkeypatch.setattr(module, "_read_dictionary", lambda _settings: ["rows"])
    monkeypatch.setattr(module, "_assert_finalize_admin_live_boundary", lambda _s: None)
    monkeypatch.setattr(module, "validate_retained_load", lambda *_args: {})
    monkeypatch.setattr(
        module,
        "capture_v1_fingerprint",
        lambda _settings: module.Fingerprint(content=b"v1", sha256="a" * 64),
    )
    monkeypatch.setattr(module, "generate_analyst_secret", lambda: "A" * 64)
    monkeypatch.setattr(module, "_connect", lambda *_args, **_kwargs: Connection())
    monkeypatch.setattr(module, "_create_analyst_role", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "_role_observation", lambda _connection: exact_role)
    monkeypatch.setattr(module, "_verify_privilege_contract", lambda _connection: {})
    monkeypatch.setattr(
        module,
        "verify_target_admin",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("hidden")),
    )

    def cleanup(_settings, created):
        cleanup_calls.append(created)
        return module.cleanup_plan(created)

    monkeypatch.setattr(module, "cleanup_created_resources", cleanup)
    with pytest.raises(RuntimeError, match="retained=database"):
        module.run_finalize_admin(settings)
    assert cleanup_calls == [
        module.CreatedResources(database=False, role=True, handoff=False)
    ]


def test_post_load_stage_markers_are_fixed_and_secret_free() -> None:
    """Observable live progress must expose only reviewed fixed stage names."""
    module = _module()
    expected = (
        "verify_role",
        "verify_admin",
        "analyst_matrix_before_handoff",
        "verify_default_privileges",
        "write_handoff",
        "analyst_matrix_after_handoff",
        "verify_v1_fingerprint",
        "verify_handoff_git",
    )
    assert tuple(module.POST_LOAD_SUCCESS_STAGES) == expected
    for stage in expected:
        assert module.post_load_stage_marker(stage) == f"stage_completed: {stage}"
    with pytest.raises(ValueError, match="post-load stage"):
        module.post_load_stage_marker("secret=value")


def test_direct_entrypoint_follows_every_definition() -> None:
    """Direct CLI execution must not call main before late validators exist."""
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    entrypoints = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    ]
    assert len(entrypoints) == 1
    assert entrypoints[0].lineno > max(node.end_lineno for node in definitions)


def test_direct_runpy_entry_resolves_late_validation_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A controlled direct-file run must reach a validator defined near EOF."""
    reached = []
    original_trace = sys.gettrace()

    def trace(frame, event, _argument):
        if (
            event == "call"
            and frame.f_code.co_name == "main"
            and Path(frame.f_code.co_filename).resolve() == MODULE_PATH
        ):
            module_globals = frame.f_globals

            def fake_run(_settings):
                assert "validate_source_row_stats" in module_globals
                reached.append(True)
                return {"mode": "direct-smoke", "status": "passed"}

            module_globals["resolve_settings"] = lambda _path: object()
            module_globals["run_create_load"] = fake_run
        return trace

    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--create-load"])
    output = io.StringIO()
    try:
        sys.settrace(trace)
        with contextlib.redirect_stdout(output):
            runpy.run_path(str(MODULE_PATH), run_name="__main__")
    finally:
        sys.settrace(original_trace)
    assert reached == [True]
    assert '"status": "passed"' in output.getvalue()


def test_direct_runpy_dispatches_finalize_admin_without_create_or_verify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The admin-only CLI flag must dispatch only its dedicated lifecycle."""
    reached = []
    original_trace = sys.gettrace()

    def trace(frame, event, _argument):
        if (
            event == "call"
            and frame.f_code.co_name == "main"
            and Path(frame.f_code.co_filename).resolve() == MODULE_PATH
        ):
            module_globals = frame.f_globals
            module_globals["resolve_settings"] = lambda _path: object()
            module_globals["run_create_load"] = lambda _settings: (_ for _ in ()).throw(
                AssertionError("create-load dispatched")
            )
            module_globals["run_verify_only"] = lambda _settings: (_ for _ in ()).throw(
                AssertionError("verify-only dispatched")
            )

            def finalize(_settings):
                reached.append(True)
                return {"mode": "finalize-admin", "status": "passed"}

            module_globals["run_finalize_admin"] = finalize
        return trace

    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--finalize-admin"])
    output = io.StringIO()
    try:
        sys.settrace(trace)
        with contextlib.redirect_stdout(output):
            runpy.run_path(str(MODULE_PATH), run_name="__main__")
    finally:
        sys.settrace(original_trace)
    assert reached == [True]
    assert '"mode": "finalize-admin"' in output.getvalue()


def test_retained_load_validator_checks_exact_database_only_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retained validation must cover exact schema, rows, IDs, owners, and empties."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )
    rows = [
        {
            "target_table": table,
            "target_identifier": "id",
            "target_type": "bigint",
            "column_origin": "source_native",
            "source_file": f"{table}.fits",
            "profile_json": '{"profiles":[{"row_count":10}]}',
        }
        for table in module.MASTER_TABLES
    ]

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        wrong_count = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, statement, parameters=None):
            rendered = (
                statement.as_string(None)
                if isinstance(statement, module.sql.Composable)
                else statement
            )
            if "pg_get_userbyid(datdba)" in rendered:
                return Result(
                    ("bootstrap_owner", "bootstrap_owner", "bootstrap_owner", 0, 0)
                )
            if rendered.startswith('SELECT count(*) FROM "source".'):
                if any(f'"{table}"' in rendered for table in module.UNLOADED_TABLES):
                    return Result((0,))
                if self.wrong_count and '"photometry_primary"' in rendered:
                    return Result((9,))
                return Result((10,))
            if "count(DISTINCT source_row)" in rendered:
                return Result((10, 10, 0, 9, 0))
            if "FROM source.photometry_primary" in rendered:
                return Result((10, 10, 10))
            if " AS e LEFT JOIN " in rendered:
                assert "count(e.id)" in rendered
                assert "count(DISTINCT e.id)" in rendered
                return Result((10, 10, 10, 10, 0))
            if "pg_database_size" in rendered:
                return Result((1024,))
            raise AssertionError(rendered)

        def rollback(self):
            return None

    connection = Connection()
    monkeypatch.setattr(module, "_connect", lambda *_args, **_kwargs: connection)
    monkeypatch.setattr(
        module.verify_schema_v11_scratch,
        "_verify_objects_and_columns",
        lambda *_args: {"tables": 12, "array_checks": 166},
    )
    monkeypatch.setattr(
        module,
        "verify_exact_retained_schema",
        lambda *_args: {"column_nullability": 1429, "constraint_definitions": 192},
    )
    evidence = module.validate_retained_load(settings, rows)
    assert evidence["counts"] == {table: 10 for table in module.MASTER_TABLES}
    assert evidence["unloaded_counts"] == {table: 0 for table in module.UNLOADED_TABLES}
    assert evidence["injected_id_tables"] == 6
    connection.wrong_count = True
    with pytest.raises(ValueError, match="retained load master count"):
        module.validate_retained_load(settings, rows)


def test_lifecycle_failure_diagnostic_is_staged_redacted_and_cleans_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure evidence must retain safe metadata, never exception text or secrets."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )
    created = module.CreatedResources(database=True, role=True, handoff=False)
    cleanup_calls = []

    def cleanup(_settings, observed):
        cleanup_calls.append(observed)
        return ("database", "role")

    monkeypatch.setattr(module, "cleanup_created_resources", cleanup)

    class DatabasePrivilegeError(Exception):
        sqlstate = "42501"

    secret = "never-surface-this-secret"
    failure = module.build_lifecycle_failure_after_cleanup(
        settings,
        created,
        stage="verify_admin",
        error=DatabasePrivilegeError(secret),
    )
    assert cleanup_calls == [created]
    assert str(failure) == (
        "Gate 3.7 failed: stage=verify_admin "
        "exception=DatabasePrivilegeError sqlstate=42501 "
        "reversed=database,role retained=none"
    )
    assert secret not in str(failure)
    assert "DatabasePrivilegeError" in str(failure)
    assert failure.__cause__ is None


def test_phase_aware_failure_cleanup_retains_database_only_after_load_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Post-seal admin failure must retain data while pre-seal failure must not."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )
    created = module.CreatedResources(database=True, role=True, handoff=True)
    cleanup_calls = []

    def cleanup(_settings, observed):
        cleanup_calls.append(observed)
        return module.cleanup_plan(observed)

    monkeypatch.setattr(module, "cleanup_created_resources", cleanup)

    pre_seal = module.build_lifecycle_failure_after_cleanup(
        settings,
        created,
        stage="load_master_tables",
        error=RuntimeError("never surface"),
        loads_sealed=False,
    )
    post_seal = module.build_lifecycle_failure_after_cleanup(
        settings,
        created,
        stage="verify_admin",
        error=RuntimeError("never surface"),
        loads_sealed=True,
    )
    unknown_stage = module.build_lifecycle_failure_after_cleanup(
        settings,
        created,
        stage="unsafe-stage",
        error=RuntimeError("never surface"),
        loads_sealed=True,
    )

    assert cleanup_calls == [
        created,
        module.CreatedResources(database=False, role=True, handoff=True),
        created,
    ]
    assert str(pre_seal).endswith("reversed=handoff,database,role retained=none")
    assert str(post_seal).endswith("reversed=handoff,role retained=database")
    assert str(unknown_stage).endswith(
        "stage=unknown exception=RuntimeError sqlstate=none "
        "reversed=handoff,database,role retained=none"
    )


def test_retained_database_role_cleanup_revokes_only_exact_gate_grants() -> None:
    """Role cleanup must remove retained-DB dependencies without dropping data."""
    module = _module()
    statements = module.retained_role_reversal_statements("bootstrap_owner")
    assert statements == (
        'ALTER DEFAULT PRIVILEGES FOR ROLE "bootstrap_owner" IN SCHEMA "source" '
        'REVOKE SELECT ON TABLES FROM "cosmos2025_v11_ro"',
        'REVOKE SELECT ON ALL TABLES IN SCHEMA "source" FROM "cosmos2025_v11_ro"',
        'REVOKE USAGE ON SCHEMA "source" FROM "cosmos2025_v11_ro"',
        'REVOKE CONNECT ON DATABASE "cosmos2025_v11" FROM "cosmos2025_v11_ro"',
    )
    assert all("DROP OWNED" not in statement for statement in statements)


def test_load_seal_requires_exact_ordered_committed_table_evidence() -> None:
    """Only seven exact validated commits may cross the retained-data boundary."""
    module = _module()

    def evidence(table):
        return module.TableLoadEvidence(
            table=table,
            source_rows=7,
            loaded_rows=7,
            declared_bytes=100,
            observed_bytes=100,
            declared_sha256="a" * 64,
            observed_sha256="a" * 64,
            elapsed_seconds=1.0,
            committed=True,
        )

    exact = [evidence(table) for table in module.MASTER_TABLES]
    assert module.seal_completed_loads(exact) is True
    for mutation in (
        exact[:-1],
        list(reversed(exact)),
        [
            *exact[:-1],
            module.TableLoadEvidence(**{**exact[-1].__dict__, "committed": False}),
        ],
    ):
        with pytest.raises(ValueError, match="sealed load boundary"):
            module.seal_completed_loads(mutation)


def test_lifecycle_failure_diagnostic_redacts_unsafe_metadata_and_cleanup_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cleanup failure diagnostics must not interpolate either exception message."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )

    class UnsafeMetadataError(Exception):
        sqlstate = "secret-state"

    def cleanup(_settings, _created):
        raise RuntimeError("cleanup-secret-must-not-surface")

    monkeypatch.setattr(module, "cleanup_created_resources", cleanup)
    failure = module.build_lifecycle_failure_after_cleanup(
        settings,
        module.CreatedResources(database=True),
        stage="verify_admin",
        error=UnsafeMetadataError("original-secret-must-not-surface"),
    )
    assert str(failure) == (
        "Gate 3.7 failed: stage=cleanup exception=RuntimeError "
        "sqlstate=none cleanup_failed=true original_stage=verify_admin "
        "retained=none"
    )
    assert "secret" not in str(failure)


def test_table_load_evidence_requires_exact_rows_hash_and_transaction_commit() -> None:
    """A short, drifted, or uncommitted table load must fail the gate."""
    module = _module()
    exact = module.TableLoadEvidence(
        table="photometry_primary",
        source_rows=7,
        loaded_rows=7,
        declared_bytes=100,
        observed_bytes=100,
        declared_sha256="a" * 64,
        observed_sha256="a" * 64,
        elapsed_seconds=1.5,
        committed=True,
    )
    module.validate_table_load_evidence(exact)
    for mutation in (
        module.TableLoadEvidence(**{**exact.__dict__, "loaded_rows": 6}),
        module.TableLoadEvidence(**{**exact.__dict__, "observed_sha256": "b" * 64}),
        module.TableLoadEvidence(**{**exact.__dict__, "committed": False}),
    ):
        with pytest.raises(ValueError, match="table load evidence"):
            module.validate_table_load_evidence(mutation)


def test_id_alignment_and_array_observations_are_exact() -> None:
    """One missing ID, FK mismatch, wrong shape, or excess NULL element must halt."""
    module = _module()
    module.validate_id_alignment(
        rows=7,
        nonnull_ids=7,
        distinct_ids=7,
        primary_matches=7,
        fk_violations=0,
    )
    with pytest.raises(ValueError, match="injected ID invariant"):
        module.validate_id_alignment(
            rows=7,
            nonnull_ids=7,
            distinct_ids=7,
            primary_matches=6,
            fk_violations=1,
        )


def test_extension_alignment_qualifies_id_against_both_join_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Joined extension verification must not submit an ambiguous ID reference."""
    module = _module()
    settings = module.resolve_settings(
        _config(tmp_path),
        {
            "TEST_HOST": "db-alias",
            "TEST_PORT": "5432",
            "TEST_ADMIN_USER": "bootstrap_owner",
            "TEST_ADMIN_PASSWORD": "admin-test-secret",
        },
    )
    rows = [
        {
            "target_table": table,
            "target_identifier": "id",
            "target_type": "bigint",
            "column_origin": "source_native",
            "source_file": f"{table}.fits",
            "profile_json": '{"profiles":[{"row_count":1}]}',
        }
        for table in module.MASTER_TABLES
    ]

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

        def execute(self, statement, parameters=None):
            rendered = (
                statement.as_string(None)
                if isinstance(statement, module.sql.Composable)
                else statement
            )
            if "pg_get_userbyid(datdba)" in rendered:
                return Result(
                    ("bootstrap_owner", "bootstrap_owner", "bootstrap_owner", 0, 0)
                )
            if rendered.startswith('SELECT count(*) FROM "source".'):
                if any(f'"{table}"' in rendered for table in module.UNLOADED_TABLES):
                    return Result((0,))
                return Result((1,))
            if "count(DISTINCT source_row)" in rendered:
                return Result((1, 1, 0, 0, 0))
            if "FROM source.photometry_primary" in rendered:
                return Result((1, 1, 1))
            if " AS e LEFT JOIN " in rendered:
                if "count(id)" in rendered or "count(DISTINCT id)" in rendered:
                    raise psycopg.errors.AmbiguousColumn()
                assert "count(e.id)" in rendered
                assert "count(DISTINCT e.id)" in rendered
                return Result((1, 1, 1, 1, 0))
            if "pg_database_size" in rendered:
                return Result((1,))
            raise AssertionError(rendered)

        def rollback(self):
            return None

    exact_role = module.RoleObservation(
        login=True,
        superuser=False,
        create_database=False,
        create_role=False,
        inherit=False,
        replication=False,
        bypass_rls=False,
        scram_credential_present=True,
        memberships=0,
        owned_objects=0,
    )
    monkeypatch.setattr(module, "_connect", lambda *_args, **_kwargs: Connection())
    monkeypatch.setattr(
        module.verify_schema_v11_scratch,
        "_verify_objects_and_columns",
        lambda *_args: {"tables": 11, "columns": 1416},
    )
    monkeypatch.setattr(module, "_verify_null_counts", lambda *_args: 0)
    monkeypatch.setattr(
        module,
        "_verify_arrays",
        lambda _connection, table, *_args: {
            "columns": 166 if table == module.MASTER_TABLES[0] else 0,
            "null_elements": 0,
        },
    )
    monkeypatch.setattr(module, "_verify_sentinels", lambda *_args: 0)
    monkeypatch.setattr(module, "_role_observation", lambda *_args: exact_role)

    evidence = module.verify_target_admin(settings, rows, exercise_wrong_array=False)
    assert evidence["injected_id_tables"] == len(module.MASTER_TABLES) - 1


def test_scalar_null_verifier_excludes_vector_element_null_profiles() -> None:
    """Array element NULLs belong only to the dedicated full-array verifier."""
    module = _module()
    with (REPO_ROOT / "data/dictionary/columns-v11.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    vectors_with_null_elements = [
        row
        for row in rows
        if row["target_type"].endswith("[]") and module._profile_null_count(row) > 0
    ]
    assert len(vectors_with_null_elements) == 12
    vector = next(
        row
        for row in vectors_with_null_elements
        if row["target_table"] == "photometry_primary"
        and row["target_identifier"] == "flux_aper_hst_f814w"
    )
    assert module._profile_null_count(vector) == 2063
    scalar = next(
        row
        for row in rows
        if row["target_table"] == "photometry_primary"
        and row["target_identifier"] == "source_row"
    )

    class Result:
        def __init__(self, values):
            self.values = values

        def fetchone(self):
            return self.values

    class Connection:
        rendered = ""

        def execute(self, statement):
            self.rendered = statement.as_string(None)
            if '"flux_aper_hst_f814w"' in self.rendered:
                return Result((0, 0))
            return Result((0,))

    connection = Connection()
    total = module._verify_null_counts(
        connection, "photometry_primary", [scalar, vector]
    )
    assert total == 0
    assert '"source_row" IS NULL' in connection.rendered
    assert '"flux_aper_hst_f814w"' not in connection.rendered
    module.validate_array_observation(
        rows=7,
        wrong_shape=0,
        target_null_elements=3,
        expected_source_null_elements=3,
    )
    with pytest.raises(ValueError, match="array invariant"):
        module.validate_array_observation(
            rows=7,
            wrong_shape=1,
            target_null_elements=4,
            expected_source_null_elements=3,
        )


def test_retained_schema_contract_rejects_nullability_and_check_definition_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admin resume must reject same-named schema drift before creating a role."""
    module = _module()
    with (REPO_ROOT / "data/dictionary/columns-v11.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    expected_columns = module.expected_retained_column_contract(rows)
    expected_constraints = module.expected_retained_constraint_contract(rows)

    class Result:
        def __init__(self, values):
            self.values = values

        def fetchall(self):
            return self.values

    class Connection:
        columns = list(expected_columns)
        constraints = list(expected_constraints)

        def execute(self, statement):
            if "a.attnotnull" in statement:
                return Result(self.columns)
            if "con.convalidated" in statement:
                return Result(self.constraints)
            raise AssertionError(statement)

    connection = Connection()
    evidence = module.verify_exact_retained_schema(connection, rows)
    assert evidence == {"column_nullability": 1461, "constraint_definitions": 193}

    changed_column = list(connection.columns[0])
    changed_column[-1] = not changed_column[-1]
    connection.columns[0] = tuple(changed_column)
    with pytest.raises(ValueError, match="nullability"):
        module.verify_exact_retained_schema(connection, rows)

    connection.columns = list(expected_columns)
    array_index = next(
        index
        for index, item in enumerate(connection.constraints)
        if item[2] == "c" and "cardinality" in item[-2]
    )
    changed_constraint = list(connection.constraints[array_index])
    changed_constraint[-2] = re.sub(
        r"cardinality\(([^)]+)\) = \d+",
        r"cardinality(\1) = 999",
        changed_constraint[-2],
    )
    connection.constraints[array_index] = tuple(changed_constraint)
    with pytest.raises(ValueError, match="constraint definition"):
        module.verify_exact_retained_schema(connection, rows)


def test_interrupted_handoff_write_removes_exact_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A write/fsync failure must not leave an untracked credential artifact."""
    module = _module()
    path = tmp_path / "cosmos2025-v11.env"
    values = module.handoff_values(host="db-alias", port=5432, analyst_secret="A" * 64)

    def fail_fsync(_descriptor):
        raise OSError("secret-bearing injected failure")

    monkeypatch.setattr(module.os, "fsync", fail_fsync)
    with pytest.raises(OSError):
        module.write_handoff_exclusive(path, values)
    assert not path.exists()
    assert not path.is_symlink()


def test_create_load_absence_guard_rejects_dangling_handoff_symlink(
    tmp_path: Path,
) -> None:
    """Any pre-existing directory entry must block the non-idempotent load."""
    module = _module()
    handoff = tmp_path / "cosmos2025-v11.env"
    handoff.symlink_to(tmp_path / "missing-target")
    with pytest.raises(ValueError, match="handoff already exists"):
        module.assert_targets_absent(
            database_names={module.BASELINE_DATABASE},
            role_names=set(),
            handoff_path=handoff,
        )


@pytest.mark.parametrize(
    ("mode", "runner"),
    (
        ("--create-load", "run_create_load"),
        ("--finalize-admin", "run_finalize_admin"),
        ("--verify-only", "run_verify_only"),
    ),
)
def test_cli_redacts_unexpected_exception_messages(
    mode: str,
    runner: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every direct CLI mode must emit class/SQLSTATE but never exception text."""
    module = _module()
    secret = "never-print-this-admin-secret"

    class InjectedFailure(Exception):
        sqlstate = "XX001"

    monkeypatch.setattr(module, "resolve_settings", lambda _path: object())
    monkeypatch.setattr(
        module,
        runner,
        lambda _settings: (_ for _ in ()).throw(InjectedFailure(secret)),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [str(REPO_ROOT / "src/etl/bootstrap_v11.py"), mode, "--config", str(tmp_path)],
    )
    with pytest.raises(SystemExit) as observed:
        module.main()
    rendered = str(observed.value)
    assert secret not in rendered
    assert "exception=InjectedFailure" in rendered
    assert "sqlstate=XX001" in rendered


def test_reviewed_ddl_payload_is_the_exact_buffer_later_executed(
    tmp_path: Path,
) -> None:
    """DDL identity review must return immutable bytes, not a path to reopen."""
    module = _module()
    with (REPO_ROOT / "data/dictionary/columns-v11.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    ddl_path = tmp_path / "schema-v11.sql"
    original = module.generate_schema_v11.generate_sql(rows).encode("utf-8")
    ddl_path.write_bytes(original)

    payload, digest = module.reviewed_ddl_payload(rows, ddl_path)
    ddl_path.write_text("SELECT 'changed after review';\n", encoding="utf-8")

    assert payload == original
    assert digest == hashlib.sha256(original).hexdigest()
