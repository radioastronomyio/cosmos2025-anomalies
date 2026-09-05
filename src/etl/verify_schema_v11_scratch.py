#!/usr/bin/env python3
"""
Script Name  : verify_schema_v11_scratch.py
Description  : Validate generated ETL v2 DDL in a disposable database
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Creates one narrowly named disposable PostgreSQL database, executes the
generated source-mirror DDL, inspects exact catalogs and comments, exercises
two mutations, and drops the database in ``finally``. Connection variable
names come from config and credentials remain environment-only.

Usage
-----
    doppler run --project ml01 --config dev -- \
      python src/etl/verify_schema_v11_scratch.py

Examples
--------
    doppler run --project ml01 --config dev -- \
      python src/etl/verify_schema_v11_scratch.py
        Runs the complete scratch lifecycle and prints a secret-free summary.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import os
import re
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import psycopg
import yaml
from psycopg import sql

# Direct execution starts with src/etl on sys.path. Add the repository root so
# package imports behave the same under the CLI and pytest.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import generate_schema_v11  # noqa: E402

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
SCRATCH_PREFIX = "cosmos2025_v11_scratch_"
PROTECTED_DATABASES = {"cosmos2025", "cosmos2025_v11"}
PROTECTED_ROLE = "cosmos2025_v11_ro"
SCRATCH_NAME_PATTERN = re.compile(r"^cosmos2025_v11_scratch_[1-9][0-9]*_[0-9a-f]{16}$")


@dataclass(frozen=True)
class ConnectionSettings:
    """Environment-resolved PostgreSQL settings kept out of emitted output."""

    host: str
    port: int
    user: str
    password: str
    maintenance_database: str
    scratch_prefix: str


@dataclass(frozen=True)
class ProtectedState:
    """Presence and stable identity of databases/role outside gate scope."""

    database_oids: dict[str, int]
    role_present: bool


# =============================================================================
# Safety and comparison helpers
# =============================================================================


def generate_scratch_name(*, pid: int | None = None, token: str | None = None) -> str:
    """Generate a PID/random database name that fits PostgreSQL identifiers."""
    actual_pid = os.getpid() if pid is None else pid
    actual_token = secrets.token_hex(8) if token is None else token
    return validate_scratch_name(f"{SCRATCH_PREFIX}{actual_pid}_{actual_token}")


def validate_scratch_name(database_name: str) -> str:
    """Refuse every name outside the single exact generated scratch grammar."""
    if (
        database_name in PROTECTED_DATABASES
        or len(database_name.encode("utf-8")) > 63
        or SCRATCH_NAME_PATTERN.fullmatch(database_name) is None
    ):
        raise ValueError(f"refusing unsafe scratch database name: {database_name!r}")
    return database_name


def resolve_connection_settings(
    config_path: Path, environment: Mapping[str, str] = os.environ
) -> ConnectionSettings:
    """Resolve only configured variable names from an injected environment."""
    config = yaml.safe_load(config_path.read_text())
    try:
        database = config["database"]
        env_names = {
            key: str(database[key])
            for key in ("host_env", "port_env", "user_env", "password_env")
        }
        maintenance_database = str(database["maintenance_database"])
        scratch_prefix = str(database["scratch_prefix"])
    except (KeyError, TypeError) as exc:
        raise ValueError("missing PostgreSQL scratch configuration") from exc
    if maintenance_database in PROTECTED_DATABASES:
        raise ValueError(
            f"refusing protected maintenance database: {maintenance_database}"
        )
    if scratch_prefix != SCRATCH_PREFIX:
        raise ValueError(f"scratch prefix mismatch: {scratch_prefix!r}")
    missing = [name for name in env_names.values() if not environment.get(name)]
    if missing:
        raise ValueError(f"missing injected database environment variables: {missing}")
    try:
        port = int(environment[env_names["port_env"]])
    except ValueError as exc:
        raise ValueError(
            f"invalid port in environment variable {env_names['port_env']}"
        ) from exc
    return ConnectionSettings(
        host=environment[env_names["host_env"]],
        port=port,
        user=environment[env_names["user_env"]],
        password=environment[env_names["password_env"]],
        maintenance_database=maintenance_database,
        scratch_prefix=scratch_prefix,
    )


def scratch_inventory_query(prefix: str) -> tuple[str, str]:
    """Return a literal-prefix inventory query; this helper never drops rows."""
    if prefix != SCRATCH_PREFIX:
        raise ValueError(f"scratch prefix mismatch: {prefix!r}")
    escaped = prefix.replace("!", "!!").replace("_", "!_").replace("%", "!%")
    return (
        "SELECT datname FROM pg_database "
        "WHERE datname LIKE %s ESCAPE '!' ORDER BY datname",
        escaped + "%",
    )


def expected_mirror_columns(
    rows: list[dict[str, str]],
) -> tuple[tuple[str, str, str, int], ...]:
    """Return the exact table/column/type/ordinal contract in generated order."""
    schema = generate_schema_v11.build_schema_contract(rows)
    return tuple(
        (table, column.name, column.sql_type, ordinal)
        for table, columns in schema.items()
        for ordinal, column in enumerate(columns, start=1)
    )


def expected_provenance_columns() -> tuple[tuple[str, str, str, int], ...]:
    """Return the exact fixed provenance column/type/ordinal contract."""
    return tuple(
        ("provenance", field.name, field.sql_type, ordinal)
        for ordinal, field in enumerate(
            generate_schema_v11.PROVENANCE_CONTRACT, start=1
        )
    )


def compare_mirror_columns(
    expected: tuple[tuple[str, str, str, int], ...],
    observed: tuple[tuple[str, str, str, int], ...],
) -> None:
    """Compare the sealed column contract in both directions and exact order."""
    if expected != observed:
        mismatch = next(
            (
                index
                for index, (left, right) in enumerate(
                    zip(expected, observed, strict=False), start=1
                )
                if left != right
            ),
            min(len(expected), len(observed)) + 1,
        )
        raise ValueError(
            "mirror column conformance mismatch: "
            f"expected {len(expected)}, observed {len(observed)}, "
            f"first mismatch {mismatch}"
        )


def _connect(settings: ConnectionSettings, database_name: str) -> psycopg.Connection:
    """Connect without constructing or logging a connection string."""
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        dbname=database_name,
    )


def _scratch_inventory(connection: psycopg.Connection, prefix: str) -> tuple[str, ...]:
    """List only literal-prefix scratch databases."""
    query, parameter = scratch_inventory_query(prefix)
    return tuple(row[0] for row in connection.execute(query, (parameter,)).fetchall())


def _protected_state(connection: psycopg.Connection) -> ProtectedState:
    """Capture only safe names/OIDs and protected-role presence."""
    databases = connection.execute(
        "SELECT datname, oid FROM pg_database WHERE datname = ANY(%s) ORDER BY datname",
        (list(sorted(PROTECTED_DATABASES)),),
    ).fetchall()
    role_present = connection.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)",
        (PROTECTED_ROLE,),
    ).fetchone()[0]
    return ProtectedState(
        database_oids={name: oid for name, oid in databases},
        role_present=role_present,
    )


def _assert_protected_precondition(state: ProtectedState) -> None:
    """Halt unless both sealed databases and the analyst role are present.

    P2R-03 gate 3.6 asserted pre-creation absence. Since the mirror sealed,
    the protected state is presence-plus-identity: this run must leave the
    v1 baseline, the cosmos2025_v11 mirror, and the analyst role untouched.
    """
    if "cosmos2025" not in state.database_oids:
        raise ValueError("protected v1 database is unexpectedly absent")
    if "cosmos2025_v11" not in state.database_oids:
        raise ValueError("sealed cosmos2025_v11 mirror is unexpectedly absent")
    if not state.role_present:
        raise ValueError("analyst role cosmos2025_v11_ro is unexpectedly absent")


def _inspect_columns(
    connection: psycopg.Connection,
) -> tuple[tuple[str, str, str, int], ...]:
    """Inspect exact source table columns using PostgreSQL's canonical types."""
    rows = connection.execute(
        """
        SELECT c.relname, a.attname,
               pg_catalog.format_type(a.atttypid, a.atttypmod), a.attnum
        FROM pg_catalog.pg_attribute AS a
        JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'source'
          AND c.relkind = 'r'
          AND a.attnum > 0
          AND NOT a.attisdropped
        """
    ).fetchall()
    table_order = {
        table: index
        for index, table in enumerate(
            (*generate_schema_v11.MIRROR_TABLE_ORDER, "provenance")
        )
    }
    return tuple(sorted(rows, key=lambda row: (table_order[row[0]], row[3])))


def _inspect_comments(
    connection: psycopg.Connection,
) -> dict[tuple[str, str], str | None]:
    """Read all source-column comments without normalizing text."""
    rows = connection.execute(
        """
        SELECT c.relname, a.attname, pg_catalog.col_description(c.oid, a.attnum)
        FROM pg_catalog.pg_attribute AS a
        JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'source'
          AND c.relkind = 'r'
          AND a.attnum > 0
          AND NOT a.attisdropped
        """
    ).fetchall()
    return {(table, column): comment for table, column, comment in rows}


def _verify_objects_and_columns(
    connection: psycopg.Connection,
    rows: list[dict[str, str]],
    *,
    expected_comment_overrides: Mapping[tuple[str, str], str] | None = None,
) -> dict[str, int]:
    """Verify exact objects, columns, comments, and all named constraints."""
    table_rows = connection.execute(
        """
        SELECT c.relname, c.relkind
        FROM pg_catalog.pg_class AS c
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'source' AND c.relkind <> 'i'
        ORDER BY c.relname
        """
    ).fetchall()
    expected_tables = {
        *generate_schema_v11.MIRROR_TABLE_ORDER,
        "provenance",
    }
    if table_rows != sorted((table, "r") for table in expected_tables):
        raise ValueError(f"source object boundary mismatch: {table_rows}")

    observed_columns = _inspect_columns(connection)
    mirror_columns = tuple(row for row in observed_columns if row[0] != "provenance")
    provenance_columns = tuple(
        row for row in observed_columns if row[0] == "provenance"
    )
    compare_mirror_columns(expected_mirror_columns(rows), mirror_columns)
    if provenance_columns != expected_provenance_columns():
        raise ValueError("provenance column conformance mismatch")

    expected_comments = {
        (comment.table, comment.column): comment.text
        for comment in generate_schema_v11.column_comment_contract(rows)
    }
    expected_comments.update(
        {
            ("provenance", field.name): field.comment
            for field in generate_schema_v11.PROVENANCE_CONTRACT
        }
    )
    if expected_comment_overrides:
        unknown = set(expected_comment_overrides).difference(expected_comments)
        if unknown:
            raise ValueError("column comment override boundary mismatch")
        expected_comments.update(expected_comment_overrides)
    observed_comments = _inspect_comments(connection)
    if observed_comments != expected_comments:
        raise ValueError("column comment conformance mismatch")

    constraint_rows = connection.execute(
        """
        SELECT c.relname, con.conname, con.contype,
               pg_catalog.pg_get_constraintdef(con.oid, true)
        FROM pg_catalog.pg_constraint AS con
        JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'source'
        ORDER BY c.relname, con.conname
        """
    ).fetchall()
    expected_constraints: set[tuple[str, str, str]] = set()
    type_codes = {"primary_key": "p", "unique": "u", "foreign_key": "f"}
    for table, items in generate_schema_v11.table_constraint_contract(rows).items():
        expected_constraints.update(
            (table, item.name, type_codes[item.kind]) for item in items
        )
    array_checks = generate_schema_v11.array_check_contract(rows)
    expected_constraints.update(
        (check.table, check.name, "c") for check in array_checks
    )
    expected_constraints.add(
        (
            "provenance",
            generate_schema_v11.constraint_name(
                "primary_key", "provenance", "table_name"
            ),
            "p",
        )
    )
    expected_constraints.update(
        (
            "provenance",
            generate_schema_v11.constraint_name("check", "provenance", field.name),
            "c",
        )
        for field in generate_schema_v11.PROVENANCE_CONTRACT
        if field.check_expression
    )
    observed_constraint_keys = {
        (table, name, kind) for table, name, kind, _definition in constraint_rows
    }
    if observed_constraint_keys != expected_constraints:
        raise ValueError("named constraint conformance mismatch")
    array_names = {check.name for check in array_checks}
    observed_array_checks = [
        (name, definition)
        for _table, name, kind, definition in constraint_rows
        if kind == "c" and name in array_names
    ]
    if len(observed_array_checks) != 166 or any(
        "array_ndims" not in definition
        or "cardinality" not in definition
        or " IS NULL" not in definition
        for _name, definition in observed_array_checks
    ):
        raise ValueError("array check definition conformance mismatch")
    return {
        "tables": len(expected_tables),
        "mirror_columns": len(mirror_columns),
        "provenance_columns": len(provenance_columns),
        "comments": len(observed_comments),
        "array_checks": len(observed_array_checks),
        "constraints": len(constraint_rows),
    }


def _wrong_array_mutation(
    connection: psycopg.Connection, rows: list[dict[str, str]]
) -> str:
    """Prove a non-null wrong-length array reaches its generated CHECK."""
    row = next(item for item in rows if item["target_type"].endswith("[]"))
    check_name = generate_schema_v11.constraint_name(
        "array_shape_check", row["target_table"], row["target_identifier"]
    )
    statement = sql.SQL(
        "INSERT INTO {}.{} ({}, {}, {}) VALUES (%s, %s, %s::{})"
    ).format(
        sql.Identifier("source"),
        sql.Identifier(row["target_table"]),
        sql.Identifier("id"),
        sql.Identifier("source_row"),
        sql.Identifier(row["target_identifier"]),
        sql.SQL(row["target_type"]),
    )
    try:
        connection.execute(statement, (-9_000_001, -9_000_001, [0.0]))
    except psycopg.errors.CheckViolation as exc:
        connection.rollback()
        if exc.diag.constraint_name != check_name:
            raise ValueError(
                "wrong-length array reached an unexpected constraint"
            ) from exc
        return check_name
    connection.rollback()
    raise ValueError("wrong-length non-null array mutation was accepted")


def _null_array_mutation(connection: psycopg.Connection) -> int:
    """Prove all nullable arrays accept NULL with master dependencies present."""
    primary_id = -9_000_002
    source_row = -9_000_002
    connection.execute(
        'INSERT INTO "source"."photometry_primary" ("id", "source_row") '
        "VALUES (%s, %s)",
        (primary_id, source_row),
    )
    for table in generate_schema_v11.MASTER_EXTENSION_TABLES:
        statement = sql.SQL("INSERT INTO {}.{} ({}, {}) VALUES (%s, %s)").format(
            sql.Identifier("source"),
            sql.Identifier(table),
            sql.Identifier("source_row"),
            sql.Identifier("id"),
        )
        connection.execute(statement, (source_row, primary_id))
    inserted = connection.execute(
        """
        SELECT count(*) FROM (
          SELECT id FROM "source"."photometry_primary" WHERE id = %s
          UNION ALL
          SELECT id FROM "source"."photometry_aper" WHERE id = %s
          UNION ALL
          SELECT id FROM "source"."lephare" WHERE id = %s
          UNION ALL
          SELECT id FROM "source"."cigale" WHERE id = %s
          UNION ALL
          SELECT id FROM "source"."ml_morpho" WHERE id = %s
          UNION ALL
          SELECT id FROM "source"."bulge_disk" WHERE id = %s
          UNION ALL
          SELECT id FROM "source"."galight_morph" WHERE id = %s
        ) AS accepted
        """,
        (primary_id,) * 7,
    ).fetchone()[0]
    connection.rollback()
    if inserted != 7:
        raise ValueError(f"NULL array mutation inserted {inserted}/7 dependency rows")
    return inserted


def _removed_row_mutation(
    connection: psycopg.Connection, rows: list[dict[str, str]]
) -> str:
    """Drop one mirror column transactionally and prove sealed comparison fails."""
    last = expected_mirror_columns(rows)[-1]
    connection.execute(
        sql.SQL("ALTER TABLE {}.{} DROP COLUMN {}").format(
            sql.Identifier("source"),
            sql.Identifier(last[0]),
            sql.Identifier(last[1]),
        )
    )
    observed = tuple(
        row for row in _inspect_columns(connection) if row[0] != "provenance"
    )
    try:
        compare_mirror_columns(expected_mirror_columns(rows), observed)
    except ValueError as exc:
        diagnostic = str(exc)
        connection.rollback()
        if "expected 1448, observed 1447" not in diagnostic:
            raise ValueError("removed-row mutation had unexpected diagnostic") from exc
        return diagnostic
    connection.rollback()
    raise ValueError("one-row-removed dictionary mutation passed conformance")


# =============================================================================
# Live lifecycle
# =============================================================================


def run_scratch_verification(config_path: Path) -> dict[str, object]:
    """Run the complete disposable database lifecycle with finally cleanup."""
    settings = resolve_connection_settings(config_path)
    dictionary_path, ddl_path = generate_schema_v11.configured_paths(config_path)
    rows = generate_schema_v11.read_dictionary(dictionary_path)
    generate_schema_v11.write_or_check(rows, ddl_path, check=True)
    scratch_name = generate_scratch_name()
    created = False
    version = ""
    counts: dict[str, int] = {}
    wrong_array = ""
    null_rows = 0
    removed_row = ""

    with _connect(settings, settings.maintenance_database) as admin:
        admin.autocommit = True
        before = _protected_state(admin)
        _assert_protected_precondition(before)
        existing = _scratch_inventory(admin, settings.scratch_prefix)
        if existing:
            raise ValueError(
                "scratch inventory is not empty before creation: " + ", ".join(existing)
            )
        exact_absent = admin.execute(
            "SELECT NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = %s)",
            (scratch_name,),
        ).fetchone()[0]
        if not exact_absent:
            raise ValueError(
                f"generated scratch database already exists: {scratch_name}"
            )
        try:
            admin.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(scratch_name))
            )
            created = True
            with _connect(settings, scratch_name) as scratch:
                version = scratch.execute("SHOW server_version").fetchone()[0]
                scratch.execute(ddl_path.read_text(encoding="utf-8"))
                scratch.commit()
                counts = _verify_objects_and_columns(scratch, rows)
                wrong_array = _wrong_array_mutation(scratch, rows)
                null_rows = _null_array_mutation(scratch)
                removed_row = _removed_row_mutation(scratch, rows)
                _verify_objects_and_columns(scratch, rows)
        finally:
            if created:
                validate_scratch_name(scratch_name)
                admin.execute(
                    sql.SQL("DROP DATABASE {}").format(sql.Identifier(scratch_name))
                )
                created = False
            remaining = _scratch_inventory(admin, settings.scratch_prefix)
            after = _protected_state(admin)
            if remaining:
                raise ValueError(
                    "scratch cleanup failed; remaining databases: "
                    + ", ".join(remaining)
                )
            if after != before:
                raise ValueError(
                    "protected database/role state changed during scratch run"
                )

    return {
        "host_alias": settings.host,
        "port": settings.port,
        "scratch_database": scratch_name,
        "postgresql_version": version,
        **counts,
        "wrong_array_rejected_by": wrong_array,
        "null_dependency_rows_accepted": null_rows,
        "removed_row_diagnostic": removed_row,
        "cleanup_confirmed": True,
        "scratch_databases_remaining": 0,
        "sealed_databases_unchanged": True,
        "analyst_role_unchanged": True,
    }


def main() -> None:
    """Run scratch verification and print only the approved secret-free facts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    try:
        summary = run_scratch_verification(args.config)
    except (ValueError, psycopg.Error) as exc:
        raise SystemExit(f"schema v1.1 scratch verification FAILED: {exc}") from exc
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("schema v1.1 scratch verification PASSED")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
