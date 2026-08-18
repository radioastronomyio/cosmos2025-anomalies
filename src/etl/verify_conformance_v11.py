#!/usr/bin/env python3
"""
Script Name  : verify_conformance_v11.py
Description  : Verify dictionary-driven ETL v2 database conformance
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Captures the fixed source schema in batched PostgreSQL catalog queries and
evaluates all generated dictionary cases in memory. Persistent operation is
read-only; destructive detection proofs are limited to a guarded scratch DB.

Usage
-----
    doppler run --project ml01 --config dev -- \
      python src/etl/verify_conformance_v11.py --live
"""

from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import psycopg
import yaml
from psycopg import sql

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import (  # noqa: E402
    bootstrap_v11,
    generate_schema_v11,
    load_provenance_v11,
    load_supplements_v11,
)
from src.etl.conformance_cases_v11 import CASES  # noqa: E402


# =============================================================================
# Configuration
# =============================================================================

MIRROR_TABLES = generate_schema_v11.MIRROR_TABLE_ORDER
MASTER_TABLES = MIRROR_TABLES[:7]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
EXPECTED_TABLES = (*MIRROR_TABLES, "provenance")
EXPECTED_GROUP_COUNTS = {
    "master_native": 1_349,
    "supplement_native": 22,
    "specz_native": 32,
    "metadata": 13,
}
EXPECTED_ORIGIN_COUNTS = {
    "source_native": 1_403,
    "source_row_metadata": 7,
    "id_injected": 6,
}
EXPECTED_V1_FINGERPRINT = load_supplements_v11.EXPECTED_V1_FINGERPRINT
PROTECTED_DATABASES = {"cosmos2025", "cosmos2025_v11"}


@dataclass(frozen=True)
class ColumnObservation:
    """One canonical PostgreSQL source-column catalog observation."""

    target_type: str
    not_null: bool
    comment: str | None


@dataclass(frozen=True)
class CatalogSnapshot:
    """All bounded catalog evidence evaluated by the local case validator."""

    objects: tuple[tuple[str, str], ...]
    columns: Mapping[tuple[str, str], ColumnObservation]
    constraints: tuple[tuple[object, ...], ...]
    provenance_tables: tuple[str, ...]
    provenance_count: int
    provenance_loaded_rows: Mapping[str, int]
    table_acls: Mapping[str, tuple[bool, bool, bool, bool, bool, bool, bool]]


@dataclass(frozen=True)
class ProtectedIdentity:
    """Secret-safe persistent identity retained across scratch-only mutations."""

    database_oids: tuple[tuple[str, int], ...]
    analyst_role_oid: int
    v1_fingerprint: str
    target_snapshot: CatalogSnapshot
    handoff_identity: tuple[int, int, int, int, int, int, bytes]


def validate_scratch_name(prefix: str, database_name: str) -> str:
    """Accept only the configured prefix plus one full random UUID token."""
    pattern = re.compile(rf"{re.escape(prefix)}[0-9a-f]{{32}}")
    if database_name in PROTECTED_DATABASES or pattern.fullmatch(database_name) is None:
        raise ValueError("unsafe scratch database name")
    return database_name


# =============================================================================
# Expected contracts
# =============================================================================


def expected_provenance_columns() -> dict[tuple[str, str], ColumnObservation]:
    """Return the fixed 13-field provenance column contract."""
    return {
        ("provenance", field.name): ColumnObservation(
            target_type=field.sql_type,
            not_null=not field.nullable,
            comment=field.comment,
        )
        for field in generate_schema_v11.PROVENANCE_CONTRACT
    }


def expected_constraints(
    cases: Sequence[Mapping[str, object]] = CASES,
) -> tuple[tuple[object, ...], ...]:
    """Return exact constraint metadata derived from the generated case set."""
    rows = [
        {
            "target_table": str(case["table"]),
            "target_identifier": str(case["column"]),
            "target_type": str(case["target_type"]),
            "element_count": str(case["element_count"]),
            "column_origin": str(case["column_origin"]),
        }
        for case in cases
    ]
    return bootstrap_v11.expected_retained_constraint_contract(rows)


# =============================================================================
# Batched catalog capture
# =============================================================================


def capture_catalog_snapshot(connection: object) -> CatalogSnapshot:
    """Capture the complete conformance boundary in five batched queries."""
    objects = tuple(
        connection.execute(
            """
            /* catalog_snapshot_objects */
            SELECT c.relname, c.relkind
            FROM pg_catalog.pg_class AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid=c.relnamespace
            WHERE n.nspname='source' AND c.relkind <> 'i'
            ORDER BY c.relname
            """
        ).fetchall()
    )
    column_rows = connection.execute(
        """
        /* catalog_snapshot_columns */
        SELECT c.relname, a.attname,
               pg_catalog.format_type(a.atttypid, a.atttypmod),
               a.attnotnull, pg_catalog.col_description(c.oid, a.attnum)
        FROM pg_catalog.pg_attribute AS a
        JOIN pg_catalog.pg_class AS c ON c.oid=a.attrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid=c.relnamespace
        WHERE n.nspname='source' AND c.relkind='r'
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY c.relname, a.attnum
        """
    ).fetchall()
    columns = {
        (table, column): ColumnObservation(target_type, not_null, comment)
        for table, column, target_type, not_null, comment in column_rows
    }
    constraint_rows = connection.execute(
        """
        /* catalog_snapshot_constraints */
        SELECT c.relname, con.conname, con.contype,
               ARRAY(
                 SELECT a.attname
                 FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, position)
                 JOIN pg_catalog.pg_attribute AS a
                   ON a.attrelid=con.conrelid AND a.attnum=key.attnum
                 ORDER BY key.position
               ),
               rn.nspname, rc.relname,
               ARRAY(
                 SELECT a.attname
                 FROM unnest(con.confkey) WITH ORDINALITY AS key(attnum, position)
                 JOIN pg_catalog.pg_attribute AS a
                   ON a.attrelid=con.confrelid AND a.attnum=key.attnum
                 ORDER BY key.position
               ),
               CASE WHEN con.contype='c'
                 THEN pg_catalog.pg_get_expr(con.conbin, con.conrelid, true)
                 ELSE NULL
               END,
               con.convalidated
        FROM pg_catalog.pg_constraint AS con
        JOIN pg_catalog.pg_class AS c ON c.oid=con.conrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid=c.relnamespace
        LEFT JOIN pg_catalog.pg_class AS rc ON rc.oid=con.confrelid
        LEFT JOIN pg_catalog.pg_namespace AS rn ON rn.oid=rc.relnamespace
        WHERE n.nspname='source'
        ORDER BY c.relname, con.conname
        """
    ).fetchall()
    constraints = tuple(
        (
            table,
            name,
            kind,
            tuple(keys or ()),
            ref_schema,
            ref_table,
            tuple(ref_keys or ()),
            bootstrap_v11._normalize_check_expression(expression)
            if expression is not None
            else None,
            validated,
        )
        for (
            table,
            name,
            kind,
            keys,
            ref_schema,
            ref_table,
            ref_keys,
            expression,
            validated,
        ) in constraint_rows
    )
    provenance_rows = connection.execute(
        """
        /* catalog_snapshot_provenance */
        SELECT table_name, loaded_rows FROM "source"."provenance"
        """
    ).fetchall()
    provenance_loaded_rows = {row[0]: row[1] for row in provenance_rows}
    observed_provenance = set(provenance_loaded_rows)
    provenance_tables = tuple(
        table for table in MIRROR_TABLES if table in observed_provenance
    ) + tuple(sorted(observed_provenance.difference(MIRROR_TABLES)))
    acl_rows = connection.execute(
        """
        /* catalog_snapshot_acls */
        SELECT c.relname,
               has_table_privilege(%s, c.oid, 'SELECT'),
               has_table_privilege(%s, c.oid, 'INSERT'),
               has_table_privilege(%s, c.oid, 'UPDATE'),
               has_table_privilege(%s, c.oid, 'DELETE'),
               has_table_privilege(%s, c.oid, 'TRUNCATE'),
               has_table_privilege(%s, c.oid, 'REFERENCES'),
               has_table_privilege(%s, c.oid, 'TRIGGER')
        FROM pg_catalog.pg_class AS c
        JOIN pg_catalog.pg_namespace AS n ON n.oid=c.relnamespace
        WHERE n.nspname='source' AND c.relkind='r'
        ORDER BY c.relname
        """,
        (bootstrap_v11.ANALYST_ROLE,) * 7,
    ).fetchall()
    table_acls = {row[0]: tuple(row[1:]) for row in acl_rows}
    return CatalogSnapshot(
        objects=objects,
        columns=columns,
        constraints=constraints,
        provenance_tables=provenance_tables,
        provenance_count=len(provenance_rows),
        provenance_loaded_rows=provenance_loaded_rows,
        table_acls=table_acls,
    )


# =============================================================================
# Local validation
# =============================================================================


def _expected_origin_and_group(table: str, column: str) -> tuple[str, str]:
    """Bind every fixed table/column to its independent origin classification."""
    if table in MASTER_TABLES and column == "source_row":
        return "source_row_metadata", "metadata"
    if table in MASTER_TABLES[1:] and column == "id":
        return "id_injected", "metadata"
    if table in MASTER_TABLES:
        return "source_native", "master_native"
    if table == "specz_compilation":
        return "source_native", "specz_native"
    return "source_native", "supplement_native"


def validate_case(case: Mapping[str, object], snapshot: CatalogSnapshot) -> None:
    """Evaluate one explicit dictionary case against cached observations."""
    key = (str(case["table"]), str(case["column"]))
    expected_origin, expected_group = _expected_origin_and_group(*key)
    if case["column_origin"] != expected_origin:
        raise ValueError(f"conformance origin mismatch: {case['case_id']}")
    if case["case_group"] != expected_group:
        raise ValueError(f"conformance case-group mismatch: {case['case_id']}")
    observed = snapshot.columns.get(key)
    if observed is None:
        raise ValueError(f"conformance column missing: {case['case_id']}")
    if observed.target_type != case["target_type"]:
        raise ValueError(f"conformance type mismatch: {case['case_id']}")
    if observed.comment != case["comment"]:
        raise ValueError(f"conformance comment mismatch: {case['case_id']}")
    constraint_name = case["array_constraint_name"]
    if constraint_name is None:
        return
    normalized = bootstrap_v11._normalize_check_expression(
        str(case["array_constraint_expression"])
    )
    column = str(case["column"])
    if (
        f"array_ndims({column}) = 1" not in normalized
        or f"cardinality({column}) = {int(case['element_count'])}" not in normalized
    ):
        raise ValueError(f"array element-count mismatch: {case['case_id']}")
    matching = [
        item
        for item in snapshot.constraints
        if item[0] == key[0] and item[1] == constraint_name and item[2] == "c"
    ]
    if len(matching) != 1 or matching[0][7] != normalized:
        raise ValueError(f"array constraint mismatch: {case['case_id']}")


def validate_snapshot(
    cases: Sequence[Mapping[str, object]], snapshot: CatalogSnapshot
) -> dict[str, int]:
    """Validate the entire fixed database boundary and every generated case."""
    if len(cases) != 1_416 or len({case["case_id"] for case in cases}) != 1_416:
        raise ValueError("generated case boundary mismatch")
    for index, case in enumerate(cases, start=1):
        expected_id = f"{index:04d}:{case['table']}.{case['column']}"
        if case["case_id"] != expected_id:
            raise ValueError("generated case identity mismatch")
    group_counts = Counter(str(case["case_group"]) for case in cases)
    origin_counts = Counter(str(case["column_origin"]) for case in cases)
    if group_counts != EXPECTED_GROUP_COUNTS:
        raise ValueError("generated case-group boundary mismatch")
    if origin_counts != EXPECTED_ORIGIN_COUNTS:
        raise ValueError("generated column-origin boundary mismatch")

    expected_objects = tuple((table, "r") for table in sorted(EXPECTED_TABLES))
    if snapshot.objects != expected_objects:
        raise ValueError("source object boundary mismatch")
    expected_column_keys = {
        (str(case["table"]), str(case["column"])) for case in cases
    } | set(expected_provenance_columns())
    if set(snapshot.columns) != expected_column_keys:
        raise ValueError("source column boundary mismatch")
    for key, expected in expected_provenance_columns().items():
        if snapshot.columns[key] != expected:
            raise ValueError("provenance column contract mismatch")

    for case in cases:
        validate_case(case, snapshot)

    canonical_constraints = expected_constraints(cases)
    if snapshot.constraints != canonical_constraints:
        raise ValueError("source constraint boundary mismatch")
    if len(canonical_constraints) != 192:
        raise ValueError("canonical constraint count mismatch")
    if snapshot.provenance_count != 11 or snapshot.provenance_tables != MIRROR_TABLES:
        raise ValueError("provenance row coverage mismatch")
    if set(snapshot.provenance_loaded_rows) != set(MIRROR_TABLES) or any(
        not isinstance(count, int) or count < 0
        for count in snapshot.provenance_loaded_rows.values()
    ):
        raise ValueError("provenance loaded-row boundary mismatch")

    expected_acl = (True, False, False, False, False, False, False)
    if set(snapshot.table_acls) != set(EXPECTED_TABLES) or any(
        value != expected_acl for value in snapshot.table_acls.values()
    ):
        raise ValueError("analyst table ACL boundary mismatch")

    return {
        "case_assertions": len(cases),
        **EXPECTED_GROUP_COUNTS,
        "native_total": origin_counts["source_native"],
        "array_assertions": sum(
            case["array_constraint_name"] is not None for case in cases
        ),
        "objects": len(snapshot.objects),
        "columns": len(snapshot.columns),
        "constraints": len(snapshot.constraints),
        "provenance_rows": snapshot.provenance_count,
        "analyst_select_tables": len(snapshot.table_acls),
        "analyst_denied_capabilities": 6 * len(snapshot.table_acls),
    }


# =============================================================================
# Persistent read-only orchestration
# =============================================================================


def run_live(settings: bootstrap_v11.Settings) -> dict[str, object]:
    """Run the generated conformance and complete analyst security surfaces."""
    before = bootstrap_v11.capture_v1_fingerprint(settings)
    with bootstrap_v11._connect(settings, settings.target_database) as connection:
        snapshot = capture_catalog_snapshot(connection)
        conformance = validate_snapshot(CASES, snapshot)
        role = bootstrap_v11._role_observation(connection)
        bootstrap_v11.validate_role_observation(role)
        connection.rollback()
    handoff = load_supplements_v11.validate_retained_handoff_security(settings)
    master_matrix = bootstrap_v11.verify_analyst_matrix(
        settings,
        expected_primary_rows=snapshot.provenance_loaded_rows["photometry_primary"],
    )
    gate38_counts = {
        table: snapshot.provenance_loaded_rows[table]
        for table in load_supplements_v11.GATE38_TABLES
    }
    gate38_matrix = load_supplements_v11.verify_gate38_analyst(settings, gate38_counts)
    provenance_matrix = load_provenance_v11.verify_provenance_analyst(
        settings, expected_rows=11
    )
    after = bootstrap_v11.capture_v1_fingerprint(settings)
    if before.sha256 != after.sha256:
        raise ValueError("v1 fingerprint changed during conformance verification")
    if before.sha256 != EXPECTED_V1_FINGERPRINT:
        raise ValueError("v1 fingerprint identity mismatch")
    return {
        "conformance": conformance,
        "role": {"exact": True},
        "handoff": handoff,
        "master_matrix": master_matrix,
        "gate38_matrix": gate38_matrix,
        "provenance_matrix": provenance_matrix,
        "v1_fingerprint": before.sha256,
        "v1_unchanged": True,
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
    }


# =============================================================================
# Guarded disposable mutation proof
# =============================================================================


def _scratch_prefix(settings: bootstrap_v11.Settings) -> str:
    """Read the scratch namespace from the same configured database contract."""
    config = yaml.safe_load(settings.config_path.read_text(encoding="utf-8"))
    try:
        prefix = str(config["database"]["scratch_prefix"])
    except (KeyError, TypeError) as exc:
        raise ValueError("missing PostgreSQL scratch prefix configuration") from exc
    if not prefix or prefix in PROTECTED_DATABASES:
        raise ValueError("unsafe scratch prefix configuration")
    return prefix


def _connect_database(
    settings: bootstrap_v11.Settings, database: str
) -> psycopg.Connection:
    """Connect with keyword credentials and no rendered connection string."""
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        dbname=database,
    )


def _create_scratch_database(settings: bootstrap_v11.Settings, database: str) -> None:
    """Create only one exact absent, prefix-guarded random scratch database."""
    validate_scratch_name(_scratch_prefix(settings), database)
    confirmed_absent = False
    try:
        with _connect_database(settings, settings.maintenance_database) as admin:
            admin.autocommit = True
            exists = admin.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname=%s)",
                (database,),
            ).fetchone()[0]
            if exists:
                raise ValueError("generated scratch database already exists")
            confirmed_absent = True
            admin.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database))
            )
    except BaseException:
        if confirmed_absent:
            _drop_scratch_database(settings, database)
        raise


def _drop_scratch_database(settings: bootstrap_v11.Settings, database: str) -> None:
    """Drop and prove absence of only the exact database created by this run."""
    validate_scratch_name(_scratch_prefix(settings), database)
    with _connect_database(settings, settings.maintenance_database) as admin:
        admin.autocommit = True
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database)))
        remains = admin.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname=%s)",
            (database,),
        ).fetchone()[0]
        if remains:
            raise RuntimeError("scratch database cleanup failed")


def _connect_scratch(
    settings: bootstrap_v11.Settings, database: str
) -> psycopg.Connection:
    """Open only an exact prefix-guarded random scratch database."""
    validate_scratch_name(_scratch_prefix(settings), database)
    return _connect_database(settings, database)


def _reviewed_ddl(settings: bootstrap_v11.Settings) -> str:
    """Return only bytes freshly reproduced from the sealed dictionary."""
    dictionary_path, ddl_path = generate_schema_v11.configured_paths(
        settings.config_path
    )
    rows = generate_schema_v11.read_dictionary(dictionary_path)
    generated = generate_schema_v11.generate_sql(rows).encode("utf-8")
    if ddl_path.read_bytes() != generated:
        raise ValueError("reviewed generated DDL byte identity mismatch")
    return generated.decode("utf-8")


def _insert_scratch_provenance(connection: psycopg.Connection) -> None:
    """Populate the exact provenance row set with explicitly synthetic facts."""
    digest = "0" * 64
    manifest_ref = "scratch://gate-3.10/manifest"
    for table in MIRROR_TABLES:
        connection.execute(
            """
            INSERT INTO "source"."provenance" (
              table_name, source_file, source_path, manifest_sha256,
              observed_sha256, source_rows, loaded_rows, load_timestamp,
              manifest_ref, manifest_ref_sha256, catalog_version,
              supplement_version, notes
            ) VALUES (%s, %s, %s, %s, %s, 0, 0,
                      transaction_timestamp(), %s, %s, %s, %s, %s)
            """,
            (
                table,
                f"{table}.scratch",
                f"scratch://gate-3.10/{table}",
                digest,
                digest,
                manifest_ref,
                digest,
                "v1.1",
                "not_applicable",
                "synthetic Gate 3.10 scratch-only provenance",
            ),
        )


def _validate_scratch_snapshot(connection: psycopg.Connection) -> dict[str, int]:
    """Run the exact production snapshot validator against the scratch schema."""
    return validate_snapshot(CASES, capture_catalog_snapshot(connection))


def _capture_handoff_identity(
    settings: bootstrap_v11.Settings,
) -> tuple[int, int, int, int, int, int, bytes]:
    """Validate then digest one stable regular mode-0600 inode without following."""
    load_supplements_v11.validate_retained_handoff_security(settings)
    path = settings.handoff_path
    before = path.lstat()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or stat.S_IMODE(opened.st_mode) != 0o600
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise ValueError("handoff identity or mode changed before digest")
        while block := os.read(descriptor, 65_536):
            digest.update(block)
        final = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    stable = (
        opened.st_dev,
        opened.st_ino,
        opened.st_mode,
        opened.st_size,
        opened.st_mtime_ns,
        opened.st_ctime_ns,
    )
    if stable != (
        final.st_dev,
        final.st_ino,
        final.st_mode,
        final.st_size,
        final.st_mtime_ns,
        final.st_ctime_ns,
    ) or stable != (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ValueError("handoff identity changed during digest")
    return (*stable, digest.digest())


def _protected_identity(settings: bootstrap_v11.Settings) -> ProtectedIdentity:
    """Capture protected DB, role, v1, target catalog, and handoff identity."""
    with _connect_database(settings, settings.maintenance_database) as maintenance:
        database_rows = maintenance.execute(
            "SELECT datname, oid FROM pg_database WHERE datname=ANY(%s) ORDER BY datname",
            (sorted(PROTECTED_DATABASES),),
        ).fetchall()
        role_row = maintenance.execute(
            "SELECT oid FROM pg_roles WHERE rolname=%s",
            (bootstrap_v11.ANALYST_ROLE,),
        ).fetchone()
        maintenance.rollback()
    if {row[0] for row in database_rows} != PROTECTED_DATABASES or role_row is None:
        raise ValueError("protected database or role identity is absent")
    with bootstrap_v11._connect(settings, settings.target_database) as target:
        target_snapshot = capture_catalog_snapshot(target)
        target.rollback()
    handoff_identity = _capture_handoff_identity(settings)
    v1 = bootstrap_v11.capture_v1_fingerprint(settings)
    return ProtectedIdentity(
        database_oids=tuple(database_rows),
        analyst_role_oid=role_row[0],
        v1_fingerprint=v1.sha256,
        target_snapshot=target_snapshot,
        handoff_identity=handoff_identity,
    )


def _require_mutation_failure(
    connection: psycopg.Connection, statement: str, expected_text: str
) -> None:
    """Require one intended validator failure and roll back the mutation."""
    try:
        connection.execute(statement)
        try:
            _validate_scratch_snapshot(connection)
        except ValueError as exc:
            if expected_text not in str(exc):
                raise ValueError("scratch mutation caused unintended failure") from exc
        else:
            raise ValueError("scratch mutation was not detected")
    finally:
        connection.rollback()
    _validate_scratch_snapshot(connection)


def run_scratch_mutations(settings: bootstrap_v11.Settings) -> dict[str, object]:
    """Prove comment/type detection in one random scratch and clean exactly."""
    prefix = _scratch_prefix(settings)
    scratch = validate_scratch_name(prefix, prefix + uuid.uuid4().hex)
    before = _protected_identity(settings)
    created = False
    cleanup_complete = False
    baseline: dict[str, int] = {}
    try:
        _create_scratch_database(settings, scratch)
        created = True
        with _connect_scratch(settings, scratch) as connection:
            connection.execute(_reviewed_ddl(settings))
            connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA source TO {}").format(
                    sql.Identifier(bootstrap_v11.ANALYST_ROLE)
                )
            )
            connection.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA source TO {}").format(
                    sql.Identifier(bootstrap_v11.ANALYST_ROLE)
                )
            )
            _insert_scratch_provenance(connection)
            connection.commit()
            baseline = _validate_scratch_snapshot(connection)
            _require_mutation_failure(
                connection,
                'COMMENT ON COLUMN "source"."photometry_primary"."segment_id" '
                "IS 'gate_3_10_scratch_comment_drift'",
                "conformance comment mismatch",
            )
            _require_mutation_failure(
                connection,
                'ALTER TABLE "source"."photometry_primary" '
                'ALTER COLUMN "segment_id" TYPE integer',
                "conformance type mismatch",
            )
    finally:
        if created:
            _drop_scratch_database(settings, scratch)
            cleanup_complete = True
    after = _protected_identity(settings)
    if after != before:
        raise ValueError("protected identity changed during scratch proof")
    return {
        "baseline_case_assertions": baseline["case_assertions"],
        "comment_mutation_detected": True,
        "type_mutation_detected": True,
        "transactions_rolled_back": 2,
        "scratch_absent": cleanup_complete,
        "protected_identity_unchanged": True,
    }


# =============================================================================
# CLI
# =============================================================================


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse mutually exclusive persistent-read and disposable-scratch modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--scratch-mutations", action="store_true")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Gate 3.10 while redacting all unexpected exception messages."""
    stage = "cli"
    try:
        arguments = parse_args(argv)
        settings = bootstrap_v11.resolve_settings(arguments.config)
        stage = "live" if arguments.live else "scratch_mutations"
        result = (
            run_live(settings) if arguments.live else run_scratch_mutations(settings)
        )
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), default=str))
        return 0
    except BaseException as error:
        error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
        print(
            f"stage={stage} exception={error_class} sqlstate={sqlstate}",
            file=sys.stderr,
        )
        return 1


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    raise SystemExit(main())
