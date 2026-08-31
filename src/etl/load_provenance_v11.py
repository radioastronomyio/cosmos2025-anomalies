#!/usr/bin/env python3
"""
Script Name  : load_provenance_v11.py
Description  : Register and verify exact Gate 3.9 mirror provenance
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Builds provenance records from separately declared and freshly observed
Gate 3.5 evidence. Persistent registration is transactional and records one
PostgreSQL transaction timestamp after all mirror loads have been verified.

Usage
-----
    doppler run --project ml01 --config dev -- \
      python src/etl/load_provenance_v11.py --load

    doppler run --project ml01 --config dev -- \
      python src/etl/load_provenance_v11.py --verify-only
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import psycopg
import yaml
from psycopg import sql

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import (  # noqa: E402
    bootstrap_v11,
    generate_schema_v11,
    load_supplements_v11,
    verify_source_fidelity,
)
from src.etl.generate_schema_v11 import MIRROR_TABLE_ORDER  # noqa: E402

PROVENANCE_TABLES = MIRROR_TABLE_ORDER
SUPPLEMENT_TABLES = (
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
)
CATALOG_VERSION = "v1.1"
NOT_APPLICABLE = "not_applicable"
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
EXPECTED_V1_FINGERPRINT = load_supplements_v11.EXPECTED_V1_FINGERPRINT
PRE_AMENDMENT_COMMENT = "Timestamp at which the table load completed."


class ProvenanceFailure(RuntimeError):
    """A redaction-safe Gate 3.9 lifecycle diagnostic."""


@dataclass(frozen=True)
class ExpectedProvenance:
    """One exact source/live provenance contract before registration time."""

    table_name: str
    source_file: str
    source_path: str
    manifest_sha256: str
    observed_sha256: str
    source_rows: int
    loaded_rows: int
    manifest_ref: str
    manifest_ref_sha256: str
    catalog_version: str
    supplement_version: str
    notes: str


@dataclass(frozen=True)
class ProvenanceObservation(ExpectedProvenance):
    """One persisted provenance row including its registration timestamp."""

    load_timestamp: datetime


def _require_exact_keys(label: str, values: Mapping[str, Any]) -> None:
    """Require evidence for the exact twelve-table ordered boundary."""
    if set(values) != set(PROVENANCE_TABLES):
        raise ValueError(f"provenance table boundary mismatch: {label}")


def _notes(table: str, xmin: int) -> str:
    """Describe exact load XID evidence without inventing commit time."""
    text = (
        f"load_transaction_xmin={xmin}; actual commit timestamp is unavailable "
        "because track_commit_timestamp was off"
    )
    if table in SUPPLEMENT_TABLES:
        text += "; v1-release product on v1.1 holdings"
    return text


def build_expected_provenance(
    *,
    pins: Mapping[str, Any],
    source_counts: Mapping[str, int],
    loaded_counts: Mapping[str, int],
    xmins: Mapping[str, int],
    manifest_ref: Path,
    manifest_ref_sha256: str,
) -> tuple[ExpectedProvenance, ...]:
    """Build exact rows from independent manifest, source, and live evidence."""
    for label, values in (
        ("pins", pins),
        ("source_counts", source_counts),
        ("loaded_counts", loaded_counts),
        ("xmins", xmins),
    ):
        _require_exact_keys(label, values)
    if len(manifest_ref_sha256) != 64:
        raise ValueError("manifest reference digest mismatch")

    rows: list[ExpectedProvenance] = []
    for table in PROVENANCE_TABLES:
        pin = pins[table]
        if (
            pin.declared_sha256 != pin.observed_sha256
            or pin.declared_bytes != pin.observed_bytes
            or len(pin.declared_sha256) != 64
        ):
            raise ValueError(f"source digest mismatch: {table}")
        if source_counts[table] != loaded_counts[table]:
            raise ValueError(f"source/loaded count mismatch: {table}")
        if not isinstance(xmins[table], int) or xmins[table] <= 0:
            raise ValueError(f"load xmin mismatch: {table}")
        path = Path(pin.path)
        rows.append(
            ExpectedProvenance(
                table_name=table,
                source_file=path.name,
                source_path=str(path),
                manifest_sha256=pin.declared_sha256,
                observed_sha256=pin.observed_sha256,
                source_rows=source_counts[table],
                loaded_rows=loaded_counts[table],
                manifest_ref=str(manifest_ref),
                manifest_ref_sha256=manifest_ref_sha256,
                catalog_version=CATALOG_VERSION,
                supplement_version=(
                    "v1" if table in SUPPLEMENT_TABLES else NOT_APPLICABLE
                ),
                notes=_notes(table, xmins[table]),
            )
        )
    return tuple(rows)


def validate_provenance_observation(
    expected: Sequence[ExpectedProvenance],
    observed: Sequence[ProvenanceObservation],
) -> datetime:
    """Reject every field, set, or shared-registration-time mutation."""
    expected_by_table = {row.table_name: row for row in expected}
    observed_by_table = {row.table_name: row for row in observed}
    if (
        len(expected_by_table) != len(PROVENANCE_TABLES)
        or len(observed_by_table) != len(PROVENANCE_TABLES)
        or set(expected_by_table) != set(PROVENANCE_TABLES)
        or set(observed_by_table) != set(PROVENANCE_TABLES)
    ):
        raise ValueError("provenance table set mismatch")
    timestamps = {row.load_timestamp for row in observed}
    if len(timestamps) != 1:
        raise ValueError("provenance timestamp mismatch")
    timestamp = timestamps.pop()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("provenance timestamp mismatch")

    for table in PROVENANCE_TABLES:
        wanted = expected_by_table[table]
        found = observed_by_table[table]
        if (
            found.manifest_sha256 != wanted.manifest_sha256
            or found.observed_sha256 != wanted.observed_sha256
            or found.manifest_ref_sha256 != wanted.manifest_ref_sha256
            or found.manifest_sha256 != found.observed_sha256
        ):
            raise ValueError(f"provenance hash mismatch: {table}")
        if (
            found.source_path != wanted.source_path
            or found.source_file != wanted.source_file
            or found.manifest_ref != wanted.manifest_ref
        ):
            raise ValueError(f"provenance path mismatch: {table}")
        if (
            found.source_rows != wanted.source_rows
            or found.loaded_rows != wanted.loaded_rows
        ):
            raise ValueError(f"provenance count mismatch: {table}")
        if (
            found.catalog_version != wanted.catalog_version
            or found.supplement_version != wanted.supplement_version
        ):
            raise ValueError(f"provenance version mismatch: {table}")
        if found.notes != wanted.notes:
            raise ValueError(f"provenance xmin/notes mismatch: {table}")
    return timestamp


def provenance_timestamp_comment_sql() -> str:
    """Return the exact generated amended COMMENT statement."""
    field = next(
        item
        for item in generate_schema_v11.PROVENANCE_CONTRACT
        if item.name == "load_timestamp"
    )
    return (
        'COMMENT ON COLUMN "source"."provenance"."load_timestamp" IS '
        f"{generate_schema_v11.sql_literal(field.comment)};"
    )


INSERT_PROVENANCE_SQL = """
INSERT INTO "source"."provenance" (
    table_name, source_file, source_path, manifest_sha256, observed_sha256,
    source_rows, loaded_rows, load_timestamp, manifest_ref,
    manifest_ref_sha256, catalog_version, supplement_version, notes
) VALUES (%s, %s, %s, %s, %s, %s, %s, transaction_timestamp(),
          %s, %s, %s, %s, %s)
"""


def _insert_parameters(row: ExpectedProvenance) -> tuple[Any, ...]:
    """Keep the database-generated timestamp out of the client parameter set."""
    return (
        row.table_name,
        row.source_file,
        row.source_path,
        row.manifest_sha256,
        row.observed_sha256,
        row.source_rows,
        row.loaded_rows,
        row.manifest_ref,
        row.manifest_ref_sha256,
        row.catalog_version,
        row.supplement_version,
        row.notes,
    )


def register_provenance_transaction(
    connection: Any, expected: Sequence[ExpectedProvenance]
) -> datetime:
    """Atomically apply the amended COMMENT and twelve provenance rows."""
    if tuple(row.table_name for row in expected) != PROVENANCE_TABLES:
        raise ValueError("provenance registration table boundary mismatch")
    try:
        count = connection.execute(
            'SELECT count(*) FROM "source"."provenance"'
        ).fetchone()[0]
        if count != 0:
            raise ValueError("provenance registration requires preflight-zero")
        connection.execute(provenance_timestamp_comment_sql())
        with connection.cursor() as cursor:
            cursor.executemany(
                INSERT_PROVENANCE_SQL, [_insert_parameters(row) for row in expected]
            )
        observation = connection.execute(
            "SELECT count(*), count(DISTINCT load_timestamp), min(load_timestamp) "
            'FROM "source"."provenance"'
        ).fetchone()
        if observation is None or observation[:2] != (12, 1):
            raise ValueError("provenance registration timestamp boundary mismatch")
        connection.commit()
        return observation[2]
    except BaseException:
        connection.rollback()
        raise


def _safe_failure(
    stage: str, error: BaseException, *, retained: int | str
) -> ProvenanceFailure:
    """Render class/SQLSTATE/lifecycle only, never exception text."""
    error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
    return ProvenanceFailure(
        f"stage={stage} exception={error_class} sqlstate={sqlstate} retained={retained}"
    )


def classify_registration_state(
    connect_factory: Any, expected: Sequence[ExpectedProvenance]
) -> tuple[str, datetime | None]:
    """Resolve an ambiguous commit as exact empty-old or exact committed-new."""
    connection = None
    try:
        connection = connect_factory()
        count = connection.execute(
            'SELECT count(*) FROM "source"."provenance"'
        ).fetchone()[0]
        comment = _provenance_comment(connection)
        if count == 0 and comment in {
            PRE_AMENDMENT_COMMENT,
            generate_schema_v11.PROVENANCE_CONTRACT[7].comment,
        }:
            connection.rollback()
            return "rolled_back", None
        if (
            count == 12
            and comment == generate_schema_v11.PROVENANCE_CONTRACT[7].comment
        ):
            timestamp = validate_provenance_observation(
                expected, _read_provenance(connection)
            )
            connection.rollback()
            return "committed", timestamp
        connection.rollback()
        raise ValueError("ambiguous provenance registration state")
    finally:
        if connection is not None:
            connection.close()


def run_registration(
    expected: Sequence[ExpectedProvenance],
    connect_factory: Any,
    verify_callback: Any,
) -> datetime:
    """Register once; retain committed rows if later verification fails."""
    connection = None
    timestamp: datetime | None = None
    registration_error: BaseException | None = None
    close_error: BaseException | None = None
    try:
        connection = connect_factory()
        timestamp = register_provenance_transaction(connection, expected)
    except BaseException as error:
        registration_error = error
    finally:
        if connection is not None:
            try:
                connection.close()
            except BaseException as error:
                close_error = error
    if registration_error is not None or close_error is not None:
        original = registration_error if registration_error is not None else close_error
        assert original is not None
        try:
            state, classified_timestamp = classify_registration_state(
                connect_factory, expected
            )
        except BaseException as classification_error:
            raise _safe_failure(
                "classify_registration",
                classification_error,
                retained="unvalidated",
            ) from None
        if state == "rolled_back":
            raise _safe_failure("register", original, retained=0) from None
        timestamp = classified_timestamp
    if timestamp is None:
        raise _safe_failure(
            "classify_registration", RuntimeError(), retained="unvalidated"
        ) from None
    try:
        verify_callback()
    except BaseException as error:
        raise _safe_failure("verify_postcommit", error, retained=12) from None
    return timestamp


resolve_settings = bootstrap_v11.resolve_settings


def _source_paths(config_path: Path) -> dict[str, Path]:
    """Resolve all twelve source artifacts only through repository config."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        catalogs = config["catalogs"]
        supplementary = config["supplementary"]
        specz = config["specz"]
        paths = {
            "photometry_primary": Path(catalogs["photom_primary"]),
            "photometry_aper": Path(catalogs["photom_secondary"]),
            "lephare": Path(catalogs["lephare"]),
            "cigale": Path(catalogs["cigale"]),
            "ml_morpho": Path(catalogs["ml_morph"]),
            "bulge_disk": Path(catalogs["bulgedisk"]),
            "galight_morph": Path(catalogs["galight_morph"]),
            "lss_overdensity": Path(supplementary["lss_overdensity"]),
            "galaxy_groups": Path(supplementary["group_catalog_groups"]),
            "galaxy_group_memberships": Path(
                supplementary["group_catalog_memberships"]
            ),
            "specz_compilation_unique": Path(specz["unique_fits"]),
            "specz_compilation_all": Path(specz["all_fits"]),
        }
    except (KeyError, TypeError) as error:
        raise ValueError("missing Gate 3.9 source path configuration") from error
    _require_exact_keys("configured source paths", paths)
    return paths


def _dictionary_table_rows(
    rows: Sequence[dict[str, str]], table: str
) -> tuple[dict[str, str], ...]:
    """Select one table's source-native rows in sealed order."""
    selected = tuple(
        row
        for row in rows
        if row["target_table"] == table and row["column_origin"] == "source_native"
    )
    if not selected:
        raise ValueError(f"missing source-native dictionary rows: {table}")
    return selected


def _profile_count(rows: Sequence[Mapping[str, str]]) -> int:
    """Require one exact physical row count across every source profile."""
    counts = {
        int(profile["row_count"])
        for row in rows
        for profile in json.loads(row["profile_json"])["profiles"]
    }
    if len(counts) != 1:
        raise ValueError("sealed source row-count mismatch")
    return counts.pop()


def observe_source_counts(
    rows: Sequence[dict[str, str]], paths: Mapping[str, Path]
) -> dict[str, int]:
    """Freshly read each physical source's exact table boundary and row count."""
    counts: dict[str, int] = {}
    for table in PROVENANCE_TABLES:
        table_rows = _dictionary_table_rows(rows, table)
        observation = (
            load_supplements_v11.inspect_text_source(paths[table], table_rows)
            if table in {"galaxy_groups", "galaxy_group_memberships"}
            else load_supplements_v11.inspect_fits_source(paths[table], table_rows)
        )
        expected_columns = tuple(row["source_column"] for row in table_rows)
        if observation.source_columns != expected_columns:
            raise ValueError(f"source column boundary mismatch: {table}")
        profile_count = _profile_count(table_rows)
        if observation.row_count != profile_count:
            raise ValueError(f"source/profile count mismatch: {table}")
        counts[table] = observation.row_count
    return counts


def fresh_manifest_evidence(
    settings: bootstrap_v11.Settings, paths: Mapping[str, Path]
) -> tuple[dict[str, verify_source_fidelity.InputEvidence], str]:
    """Pin twelve inputs and bind them to one stable manifest byte identity."""
    digest_before = verify_source_fidelity.sha256_of(settings.manifest_path)
    manifest = bootstrap_v11._manifest_contract(settings)
    pins = {
        table: verify_source_fidelity.pin_manifest_input(table, paths[table], manifest)
        for table in PROVENANCE_TABLES
    }
    digest_after = verify_source_fidelity.sha256_of(settings.manifest_path)
    if digest_after != digest_before:
        raise ValueError("source manifest changed during Gate 3.9 pin reads")
    return pins, digest_before


def _target_snapshot(connection: Any) -> tuple[dict[str, int], dict[str, int]]:
    """Read exact mirror counts and one transaction xmin per loaded table."""
    counts: dict[str, int] = {}
    xmins: dict[str, int] = {}
    for table in PROVENANCE_TABLES:
        count, xid_count, minimum, maximum = connection.execute(
            sql.SQL(
                "SELECT count(*), count(DISTINCT xmin::text), "
                "min(xmin::text::bigint), max(xmin::text::bigint) FROM {}.{}"
            ).format(sql.Identifier("source"), sql.Identifier(table))
        ).fetchone()
        if count <= 0 or xid_count != 1 or minimum != maximum or minimum <= 0:
            raise ValueError(f"mirror load xmin boundary mismatch: {table}")
        counts[table] = count
        xmins[table] = minimum
    return counts, xmins


def _provenance_comment(connection: Any) -> str | None:
    """Read the live amended-column comment without mutating it."""
    return connection.execute(
        """
        SELECT col_description(c.oid, a.attnum)
        FROM pg_class c
        JOIN pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_attribute a ON a.attrelid=c.oid
        WHERE n.nspname='source' AND c.relname='provenance'
          AND a.attname='load_timestamp' AND NOT a.attisdropped
        """
    ).fetchone()[0]


def verify_pre_registration_schema(
    connection: Any, rows: Sequence[dict[str, str]]
) -> dict[str, int]:
    """Keep schema exact while allowing only the authorized COMMENT transition."""
    comment = _provenance_comment(connection)
    amended = generate_schema_v11.PROVENANCE_CONTRACT[7].comment
    if comment not in {PRE_AMENDMENT_COMMENT, amended}:
        raise ValueError("pre-registration provenance comment mismatch")
    structure = (
        load_supplements_v11.verify_schema_v11_scratch._verify_objects_and_columns(
            connection,
            list(rows),
            expected_comment_overrides={
                ("provenance", "load_timestamp"): comment,
            },
        )
    )
    structure.update(bootstrap_v11.verify_exact_retained_schema(connection, rows))
    return structure


def _read_provenance(connection: Any) -> tuple[ProvenanceObservation, ...]:
    """Read all fixed fields in table order for strict comparison."""
    rows = connection.execute(
        """
        SELECT table_name, source_file, source_path, manifest_sha256,
               observed_sha256, source_rows, loaded_rows, manifest_ref,
               manifest_ref_sha256, catalog_version, supplement_version,
               notes, load_timestamp
        FROM "source"."provenance"
        ORDER BY array_position(%s::text[], table_name)
        """,
        (list(PROVENANCE_TABLES),),
    ).fetchall()
    return tuple(ProvenanceObservation(*row) for row in rows)


def _connect_target(settings: bootstrap_v11.Settings) -> psycopg.Connection:
    """Open the fixed target using the approved clusteradmin transport."""
    return bootstrap_v11._connect(settings, settings.target_database)


def _verify_provenance_acl(connection: Any) -> dict[str, bool]:
    """Require SELECT-only analyst capability on the provenance table."""
    observed = connection.execute(
        """
        SELECT has_table_privilege(%s, c.oid, 'SELECT'),
               has_table_privilege(%s, c.oid, 'INSERT'),
               has_table_privilege(%s, c.oid, 'UPDATE'),
               has_table_privilege(%s, c.oid, 'DELETE'),
               has_table_privilege(%s, c.oid, 'TRUNCATE'),
               has_table_privilege(%s, c.oid, 'REFERENCES'),
               has_table_privilege(%s, c.oid, 'TRIGGER')
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='source' AND c.relname='provenance' AND c.relkind='r'
        """,
        (bootstrap_v11.ANALYST_ROLE,) * 7,
    ).fetchone()
    if observed != (True, False, False, False, False, False, False):
        raise ValueError("provenance analyst ACL mismatch")
    return {"select": True, "write_or_ddl": False}


def verify_provenance_analyst(
    settings: bootstrap_v11.Settings, *, expected_rows: int = 11
) -> dict[str, Any]:
    """Prove analyst SELECT and deterministic write/DDL/GRANT denial."""
    operations = (
        'INSERT INTO "source"."provenance" DEFAULT VALUES',
        'UPDATE "source"."provenance" SET notes=notes WHERE false',
        'DELETE FROM "source"."provenance" WHERE false',
        'TRUNCATE "source"."provenance"',
        'ALTER TABLE "source"."provenance" ADD COLUMN gate_3_9_forbidden integer',
        sql.SQL("GRANT {} TO {}").format(
            sql.Identifier(settings.user), sql.Identifier(bootstrap_v11.ANALYST_ROLE)
        ),
    )
    denied = 0
    with bootstrap_v11._impersonated_analyst(settings) as connection:
        count = connection.execute(
            'SELECT count(*) FROM "source"."provenance"'
        ).fetchone()[0]
        connection.rollback()
        if count != expected_rows:
            raise ValueError("provenance analyst SELECT count mismatch")
        for operation in operations:
            try:
                connection.execute(operation)
            except psycopg.errors.InsufficientPrivilege as error:
                connection.rollback()
                if error.sqlstate != "42501":
                    raise ValueError("provenance denial SQLSTATE mismatch") from error
                denied += 1
            else:
                connection.rollback()
                raise ValueError("provenance analyst operation unexpectedly allowed")
    return {
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
        "positive_selects": 1,
        "negative_operations": denied,
    }


def build_live_expected(
    settings: bootstrap_v11.Settings, *, require_provenance_zero: bool
) -> dict[str, Any]:
    """Run fresh source, manifest, schema, role, handoff, v1, and target checks."""
    rows = bootstrap_v11._read_dictionary(settings)
    paths = _source_paths(settings.config_path)
    pins, manifest_hash = fresh_manifest_evidence(settings, paths)
    source_counts = observe_source_counts(rows, paths)
    with _connect_target(settings) as connection:
        structure = (
            verify_pre_registration_schema(connection, rows)
            if require_provenance_zero
            else load_supplements_v11.verify_gate38_schema(connection, rows)
        )
        loaded_counts, xmins = _target_snapshot(connection)
        provenance_count = connection.execute(
            'SELECT count(*) FROM "source"."provenance"'
        ).fetchone()[0]
        comment = _provenance_comment(connection)
        role = bootstrap_v11._role_observation(connection)
        bootstrap_v11.validate_role_observation(role)
        acl = _verify_provenance_acl(connection)
        track_commit_timestamp = connection.execute(
            "SHOW track_commit_timestamp"
        ).fetchone()[0]
        connection.rollback()
    if source_counts != loaded_counts:
        raise ValueError("twelve-table source/live count mismatch")
    if require_provenance_zero:
        if provenance_count != 0:
            raise ValueError("provenance registration requires preflight-zero")
        if comment not in {
            PRE_AMENDMENT_COMMENT,
            generate_schema_v11.PROVENANCE_CONTRACT[7].comment,
        }:
            raise ValueError("pre-registration provenance comment mismatch")
    elif provenance_count != 12:
        raise ValueError("provenance row-count mismatch")
    if str(track_commit_timestamp).lower() not in {"off", "false"}:
        raise ValueError("track_commit_timestamp evidence changed")
    load_supplements_v11.validate_retained_handoff_security(settings)
    v1 = bootstrap_v11.capture_v1_fingerprint(settings)
    if v1.sha256 != EXPECTED_V1_FINGERPRINT:
        raise ValueError("v1 fingerprint mismatch")
    expected = build_expected_provenance(
        pins=pins,
        source_counts=source_counts,
        loaded_counts=loaded_counts,
        xmins=xmins,
        manifest_ref=settings.manifest_path,
        manifest_ref_sha256=manifest_hash,
    )
    return {
        "rows": rows,
        "expected": expected,
        "source_counts": source_counts,
        "xmins": xmins,
        "manifest_ref_sha256": manifest_hash,
        "structure": structure,
        "provenance_count": provenance_count,
        "comment": comment,
        "acl": acl,
        "v1_fingerprint": v1.sha256,
    }


def verify_persistent_provenance(
    settings: bootstrap_v11.Settings,
    expected: Sequence[ExpectedProvenance],
    *,
    expected_v1_fingerprint: str,
) -> dict[str, Any]:
    """Verify exact rows/comment/schema/security while preserving mirror data."""
    with _connect_target(settings) as connection:
        rows = bootstrap_v11._read_dictionary(settings)
        structure = load_supplements_v11.verify_gate38_schema(connection, rows)
        loaded_counts, xmins = _target_snapshot(connection)
        observed = _read_provenance(connection)
        timestamp = validate_provenance_observation(expected, observed)
        comment = _provenance_comment(connection)
        if comment != generate_schema_v11.PROVENANCE_CONTRACT[7].comment:
            raise ValueError("provenance timestamp comment mismatch")
        acl = _verify_provenance_acl(connection)
        role = bootstrap_v11._role_observation(connection)
        bootstrap_v11.validate_role_observation(role)
        connection.rollback()
    if loaded_counts != {row.table_name: row.loaded_rows for row in expected}:
        raise ValueError("provenance/live count mismatch")
    if xmins != {
        row.table_name: int(row.notes.split("=", 1)[1].split(";", 1)[0])
        for row in expected
    }:
        raise ValueError("provenance/live xmin mismatch")
    analyst = verify_provenance_analyst(settings)
    gate38_analyst = load_supplements_v11.verify_gate38_analyst(
        settings,
        {table: loaded_counts[table] for table in load_supplements_v11.GATE38_TABLES},
    )
    load_supplements_v11.validate_retained_handoff_security(settings)
    v1 = bootstrap_v11.capture_v1_fingerprint(settings)
    if v1.sha256 != expected_v1_fingerprint:
        raise ValueError("v1 fingerprint changed during Gate 3.9")
    return {
        "rows": len(observed),
        "table_set": list(PROVENANCE_TABLES),
        "registration_timestamp": timestamp.isoformat(),
        "manifest_ref_sha256": expected[0].manifest_ref_sha256,
        "source_loaded_counts": loaded_counts,
        "load_transaction_xmins": xmins,
        "supplement_versions": {
            row.table_name: row.supplement_version
            for row in expected
            if row.table_name in SUPPLEMENT_TABLES
        },
        "not_applicable_versions": sum(
            row.supplement_version == NOT_APPLICABLE for row in expected
        ),
        "structure": structure,
        "provenance_acl": acl,
        "provenance_analyst": analyst,
        "gate38_analyst": gate38_analyst,
        "v1_fingerprint": v1.sha256,
    }


def run_provenance_load(settings: bootstrap_v11.Settings) -> dict[str, Any]:
    """Run the guarded persistent Gate 3.9 registration."""
    stage = "preflight"
    retained = 0
    try:
        evidence = build_live_expected(settings, require_provenance_zero=True)
        print("gate39_stage=preflight status=passed provenance_rows=0", flush=True)
        expected = evidence["expected"]
        verification: dict[str, Any] = {}

        def verify_after_commit() -> None:
            nonlocal verification
            verification = verify_persistent_provenance(
                settings,
                expected,
                expected_v1_fingerprint=evidence["v1_fingerprint"],
            )

        timestamp = run_registration(
            expected,
            lambda: _connect_target(settings),
            verify_after_commit,
        )
        stage = "post_registration"
        retained = 12
        print(
            "gate39_stage=register status=committed rows=12 comment=amended",
            flush=True,
        )
        print("gate39_stage=verify_postcommit status=passed", flush=True)
        return {
            "gate": "3.9",
            "status": "passed",
            "mode": "load",
            "rows": 12,
            "registration_timestamp": timestamp.isoformat(),
            "verification": verification,
            "direct_analyst_network_auth_exercised": False,
            "pending_operator_action": "add direct analyst HBA coverage for ML01",
        }
    except ProvenanceFailure:
        raise
    except BaseException as error:
        raise _safe_failure(stage, error, retained=retained) from None


def run_provenance_verify_only(settings: bootstrap_v11.Settings) -> dict[str, Any]:
    """Verify an existing exact twelve-row registration without mutation."""
    retained: int | str = "unvalidated"
    try:
        evidence = build_live_expected(settings, require_provenance_zero=False)
        retained = 11
        verification = verify_persistent_provenance(
            settings,
            evidence["expected"],
            expected_v1_fingerprint=evidence["v1_fingerprint"],
        )
        return {
            "gate": "3.9",
            "status": "passed",
            "mode": "verify-only",
            "verification": verification,
            "direct_analyst_network_auth_exercised": False,
            "pending_operator_action": "add direct analyst HBA coverage for ML01",
        }
    except BaseException as error:
        raise _safe_failure("verify_only", error, retained=retained) from None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse mutually exclusive persistent registration/read-only modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--load", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Gate 3.9 while redacting all unexpected exception messages."""
    try:
        arguments = parse_args(argv)
        settings = resolve_settings(arguments.config)
        result = (
            run_provenance_load(settings)
            if arguments.load
            else run_provenance_verify_only(settings)
        )
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), default=str))
        return 0
    except ProvenanceFailure as error:
        print(str(error), file=sys.stderr)
        return 1
    except BaseException as error:
        error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
        print(f"stage=cli exception={error_class} sqlstate={sqlstate}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
