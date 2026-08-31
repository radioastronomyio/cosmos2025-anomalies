#!/usr/bin/env python3
"""
Script Name  : load_specz_all_v11.py
Description  : Loads and verifies the measurement-level spec-z compilation mirror
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
P2R-04 gate 4.5/4.6 evidence command. Loads the measurement-level spec-z
compilation artifact (`specz_compilation_COSMOS_DR1.1_all.fits`) into
`source.specz_compilation_all` under the P2R-03 load contract: only FITS masks
and NaN become SQL NULL, every finite value including sentinels is stored
unchanged, and no transformation occurs. The table is created from the tracked,
byte-checked generated DDL slice; comments come from the same artifact; the
analyst grant is verified after creation rather than assumed.

`--register-provenance` (gate 4.6) adds the single provenance row under the
existing fixed field contract, carrying manifest-declared and freshly observed
source SHA-256 values as separate evidence, and verifies the eleven
pre-existing rows did not change.

Usage
-----
    doppler run --project ml01 --config dev -- \
        python src/etl/load_specz_all_v11.py --load
    doppler run --project ml01 --config dev -- \
        python src/etl/load_specz_all_v11.py --verify-only
    doppler run --project ml01 --config dev -- \
        python src/etl/load_specz_all_v11.py --register-provenance

Examples
--------
    --load                Preflight pins, guarded CREATE/COPY transaction,
                          post-load verification, and invariance digests.
    --verify-only         All read-only post-load checks.
    --register-provenance Verify, insert one provenance row, verify twelve.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

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
    verify_source_fidelity,
)

TABLE = "specz_compilation_all"
OLD_UNIQUE_TABLE = "specz_compilation_unique"
EXPECTED_NATIVE_COLUMNS = 32
DIGEST_MODULUS = 977
DIGEST_OFFSET = 3
PROTECTED_TABLES = (
    "photometry_primary",
    "photometry_aper",
    "lephare",
    "cigale",
    "ml_morpho",
    "bulge_disk",
    "galight_morph",
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
    OLD_UNIQUE_TABLE,
)
COPY_NULL_MARKER = bootstrap_v11.COPY_NULL_MARKER


# =============================================================================
# Dictionary and DDL contract helpers
# =============================================================================


def _table_rows(rows: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    """Select the new table's native rows and enforce the field contract."""
    selected = tuple(
        row for row in rows if row["target_table"] == TABLE
    )
    if len(selected) != EXPECTED_NATIVE_COLUMNS:
        raise SystemExit(
            f"dictionary FAILED: {TABLE} has {len(selected)} rows, "
            f"expected {EXPECTED_NATIVE_COLUMNS}"
        )
    if any(row["column_origin"] != "source_native" for row in selected):
        raise SystemExit(f"dictionary FAILED: {TABLE} carries a metadata column")
    identifiers = [row["target_identifier"] for row in selected]
    if len(set(identifiers)) != len(identifiers):
        raise SystemExit(f"dictionary FAILED: {TABLE} duplicate identifiers")
    return selected


def _ddl_statements(ddl_path: Path, rows: tuple[dict[str, str], ...]) -> list[str]:
    """Extract this table's CREATE and COMMENT statements from tracked DDL."""
    text = ddl_path.read_text(encoding="utf-8")
    statements: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if current:
            current.append(line)
            if line.rstrip().endswith(";"):
                statements.append("\n".join(current))
                current = []
        elif line.startswith(f'CREATE TABLE "source"."{TABLE}"'):
            current.append(line)
        elif line.startswith(f'COMMENT ON COLUMN "source"."{TABLE}".'):
            statements.append(line)
    if current:
        raise SystemExit("DDL FAILED: unterminated statement slice")
    create = [s for s in statements if s.startswith("CREATE TABLE")]
    comments = [s for s in statements if s.startswith("COMMENT ON COLUMN")]
    if len(create) != 1 or len(comments) != len(rows):
        raise SystemExit(
            f"DDL FAILED: extracted {len(create)} CREATE and {len(comments)} "
            f"COMMENT statements for {len(rows)} columns"
        )
    return statements


def _copy_statement(rows: tuple[dict[str, str], ...]) -> str:
    columns = ", ".join(
        generate_schema_v11.quote_identifier(row["target_identifier"])
        for row in rows
    )
    return (
        f'COPY "source"."{TABLE}" ({columns}) FROM STDIN WITH '
        f"(FORMAT csv, DELIMITER E'\\t', NULL '{COPY_NULL_MARKER}')"
    )


# =============================================================================
# Observation helpers
# =============================================================================


def _row_count(connection: psycopg.Connection, table: str) -> int:
    return int(
        connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(table)
            )
        ).fetchone()[0]
    )


def _seeded_digest(connection: psycopg.Connection, table: str) -> dict[str, object]:
    result = connection.execute(
        sql.SQL(
            "SELECT count(*), md5(coalesce(string_agg(md5(s.txt), '' "
            "ORDER BY s.rn), '')) FROM (SELECT t::text AS txt, "
            "row_number() OVER (ORDER BY t.ctid) AS rn FROM {}.{} t) s "
            "WHERE s.rn %% %(modulus)s = %(offset)s"
        ).format(sql.Identifier("source"), sql.Identifier(table)),
        {"modulus": DIGEST_MODULUS, "offset": DIGEST_OFFSET},
    ).fetchone()
    return {
        "seed_modulus": DIGEST_MODULUS,
        "seed_offset": DIGEST_OFFSET,
        "sampled_rows": int(result[0]),
        "digest": result[1],
    }


def _analyst_select_count(
    connection: psycopg.Connection, settings: bootstrap_v11.Settings
) -> int:
    connection.execute(
        sql.SQL("SET SESSION AUTHORIZATION {}").format(
            sql.Identifier(settings.analyst_role)
        )
    )
    try:
        return _row_count(connection, TABLE)
    finally:
        connection.execute("RESET SESSION AUTHORIZATION")


def _default_privilege_owner(connection: psycopg.Connection) -> str:
    owners = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT pg_get_userbyid(defaclrole) FROM pg_default_acl dac "
            "JOIN pg_namespace n ON n.oid = dac.defaclnamespace "
            "WHERE n.nspname = 'source' AND dac.defaclobjtype = 'r'"
        ).fetchall()
    }
    if len(owners) != 1:
        raise SystemExit(f"principal FAILED: ambiguous default-privilege owners {owners}")
    return owners.pop()


def _assert_principal(connection: psycopg.Connection) -> str:
    current = connection.execute("SELECT current_user").fetchone()[0]
    owner = _default_privilege_owner(connection)
    if current != owner:
        raise SystemExit(
            f"principal FAILED: connecting identity {current!r} is not the "
            f"default-privilege owner {owner!r}"
        )
    return current


def _grants(connection: psycopg.Connection, settings: bootstrap_v11.Settings) -> dict:
    has_grant = connection.execute(
        "SELECT has_table_privilege(%s, %s, 'SELECT')",
        (settings.analyst_role, f'source."{TABLE}"'),
    ).fetchone()[0]
    return {"analyst_role": settings.analyst_role, "select_granted": bool(has_grant)}


def _invariance(connection: psycopg.Connection) -> dict[str, object]:
    return {
        table: {
            "count": _row_count(connection, table),
            "digest": _seeded_digest(connection, table),
        }
        for table in PROTECTED_TABLES
    }


def _pin(settings: bootstrap_v11.Settings, rows: tuple[dict[str, str], ...]):
    config = yaml.safe_load(settings.config_path.read_text(encoding="utf-8"))
    path = Path(config["specz"]["all_fits"])
    if {Path(row["source_file"]) for row in rows} != {path}:
        raise SystemExit("dictionary FAILED: source_file does not match configured artifact")
    contract = bootstrap_v11._manifest_contract(settings)
    return verify_source_fidelity.pin_manifest_input(TABLE, path, contract)


# =============================================================================
# Verification
# =============================================================================


def _verify_loaded(
    connection: psycopg.Connection,
    settings: bootstrap_v11.Settings,
    rows: tuple[dict[str, str], ...],
    pin,
) -> dict[str, object]:
    if pin.declared_sha256 != pin.observed_sha256 or (
        pin.declared_bytes != pin.observed_bytes
    ):
        raise SystemExit("pin FAILED: manifest and observed hashes differ")
    live = _row_count(connection, TABLE)
    observation = load_supplements_v11.inspect_fits_source(Path(pin.path), rows)
    if live != observation.row_count:
        raise SystemExit(
            f"count FAILED: live {live} != source {observation.row_count}"
        )
    uniqueness = connection.execute(
        sql.SQL("SELECT count({id}), count(DISTINCT {id}) FROM {}.{}").format(
            sql.Identifier("source"),
            sql.Identifier(TABLE),
            id=sql.Identifier("id_specz"),
        )
    ).fetchone()
    if uniqueness[0] != live or uniqueness[1] != live:
        raise SystemExit(
            f"key FAILED: id_specz not unique/non-null: {uniqueness} of {live}"
        )
    live_columns = [
        row[0]
        for row in connection.execute(
            "SELECT a.attname FROM pg_attribute a "
            "JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'source' AND c.relname = %s "
            "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum",
            (TABLE,),
        ).fetchall()
    ]
    expected_columns = [row["target_identifier"] for row in rows]
    if live_columns != expected_columns:
        raise SystemExit(
            f"columns FAILED: live/dictionary column sets differ: "
            f"{live_columns} vs {expected_columns}"
        )
    expected_comments = {
        item.column: item.text
        for item in generate_schema_v11.column_comment_contract(
            bootstrap_v11._read_dictionary(settings)
        )
        if item.table == TABLE
    }
    live_comments = _column_comment_map(connection)
    if live_comments != expected_comments:
        differing = [
            key
            for key in expected_comments
            if live_comments.get(key) != expected_comments[key]
        ]
        raise SystemExit(f"comments FAILED: {len(differing)} differ: {differing[:5]}")
    grants = _grants(connection, settings)
    if not grants["select_granted"]:
        raise SystemExit("grant FAILED: analyst SELECT absent after creation")
    analyst_rows = _analyst_select_count(connection, settings)
    if analyst_rows != live:
        raise SystemExit(
            f"grant FAILED: analyst SELECT returned {analyst_rows} != {live}"
        )
    connection.rollback()
    return {
        "source_rows": observation.row_count,
        "loaded_rows": live,
        "id_specz_distinct": int(uniqueness[1]),
        "column_count": len(live_columns),
        "comment_count": len(live_comments),
        "grants": grants,
        "analyst_select_rows": analyst_rows,
        "pin": {
            "manifest_sha256": pin.declared_sha256,
            "observed_sha256": pin.observed_sha256,
            "manifest_bytes": pin.declared_bytes,
            "observed_bytes": pin.observed_bytes,
        },
    }


def _column_comment_map(connection: psycopg.Connection) -> dict[str, str]:
    rows = connection.execute(
        "SELECT a.attname, d.description FROM pg_attribute a "
        "JOIN pg_class c ON c.oid = a.attrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = a.attnum "
        "WHERE n.nspname = 'source' AND c.relname = %s "
        "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum",
        (TABLE,),
    ).fetchall()
    return {name: (comment or "") for name, comment in rows}


# =============================================================================
# Provenance registration (gate 4.6)
# =============================================================================


def _read_provenance_rows(connection: psycopg.Connection) -> list[dict]:
    columns = [field.name for field in generate_schema_v11.PROVENANCE_CONTRACT]
    return [
        dict(zip(columns, row))
        for row in connection.execute(
            sql.SQL("SELECT {} FROM {}.provenance ORDER BY table_name").format(
                sql.SQL(", ").join(sql.Identifier(name) for name in columns),
                sql.Identifier("source"),
            )
        ).fetchall()
    ]


def _register_provenance(
    connection: psycopg.Connection,
    settings: bootstrap_v11.Settings,
    rows: tuple[dict[str, str], ...],
    pin,
) -> dict[str, object]:
    manifest_hash = hashlib.sha256(settings.manifest_path.read_bytes()).hexdigest()
    before = _read_provenance_rows(connection)
    if len(before) != 11:
        raise SystemExit(f"provenance FAILED: expected 11 rows, found {len(before)}")
    live = _row_count(connection, TABLE)
    observation = load_supplements_v11.inspect_fits_source(Path(pin.path), rows)
    if live != observation.row_count:
        raise SystemExit("provenance FAILED: live/source count mismatch")
    xmins = {
        row[0]
        for row in connection.execute(
            sql.SQL("SELECT DISTINCT xmin::text FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(TABLE)
            )
        ).fetchall()
    }
    if len(xmins) != 1:
        raise SystemExit(f"provenance FAILED: table spans multiple xmins: {xmins}")
    xmin = int(xmins.pop())
    notes = (
        f"load_transaction_xmin={xmin}; actual commit timestamp is unavailable "
        "because track_commit_timestamp was off; measurement-level compilation "
        "mirror added by spec P2R-04 gate 4.5"
    )
    row = load_provenance_v11.ExpectedProvenance(
        table_name=TABLE,
        source_file=Path(pin.path).name,
        source_path=str(pin.path),
        manifest_sha256=pin.declared_sha256,
        observed_sha256=pin.observed_sha256,
        source_rows=observation.row_count,
        loaded_rows=live,
        manifest_ref=str(settings.manifest_path),
        manifest_ref_sha256=manifest_hash,
        catalog_version=load_provenance_v11.CATALOG_VERSION,
        supplement_version=load_provenance_v11.NOT_APPLICABLE,
        notes=notes,
    )
    connection.execute(
        load_provenance_v11.INSERT_PROVENANCE_SQL,
        load_provenance_v11._insert_parameters(row),
    )
    after = _read_provenance_rows(connection)
    if len(after) != 12:
        connection.rollback()
        raise SystemExit(f"provenance FAILED: 12 rows expected, found {len(after)}")
    added = next(item for item in after if item["table_name"] == TABLE)
    if added["manifest_sha256"] != added["observed_sha256"]:
        connection.rollback()
        raise SystemExit("provenance FAILED: manifest and observed hashes differ")
    changed_preexisting = sorted(
        item["table_name"]
        for item in before
        if item not in after
    )
    if changed_preexisting:
        connection.rollback()
        raise SystemExit(
            f"provenance FAILED: pre-existing rows changed: {changed_preexisting}"
        )
    connection.commit()
    live_tables = {
        row[0]
        for row in connection.execute(
            "SELECT c.relname FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'source' AND c.relkind = 'r' AND c.relname <> 'provenance'"
        ).fetchall()
    }
    if live_tables != {item["table_name"] for item in after}:
        raise SystemExit("provenance FAILED: provenance/table-name set mismatch")
    return {
        "rows": len(after),
        "table_set": sorted(live_tables),
        "added_row": {
            "table_name": added["table_name"],
            "manifest_sha256": added["manifest_sha256"],
            "observed_sha256": added["observed_sha256"],
            "manifest_ref_sha256": added["manifest_ref_sha256"],
            "loaded_rows": int(added["loaded_rows"]),
            "load_transaction_xmin": xmin,
        },
        "preexisting_rows_unchanged": True,
    }


# =============================================================================
# Entry Point
# =============================================================================
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=bootstrap_v11.DEFAULT_CONFIG_PATH)
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--register-provenance", action="store_true")
    args = parser.parse_args()
    selected = [name for name in ("load", "verify_only", "register_provenance") if getattr(args, name)]
    if len(selected) != 1:
        raise SystemExit("exactly one of --load, --verify-only, --register-provenance")

    settings = bootstrap_v11.resolve_settings(args.config)
    rows = bootstrap_v11._read_dictionary(settings)
    table_rows = _table_rows(rows)
    generate_schema_v11.write_or_check(
        rows, settings.ddl_path, check=True
    )
    statements = _ddl_statements(settings.ddl_path, table_rows)
    pin = _pin(settings, table_rows)

    with bootstrap_v11._connect(settings, settings.target_database) as connection:
        principal = _assert_principal(connection)
        if args.load:
            existing = connection.execute(
                "SELECT to_regclass(%s) IS NOT NULL", (f'source."{TABLE}"',)
            ).fetchone()[0]
            if existing:
                raise SystemExit(f"load FAILED: {TABLE} already exists")
            baseline = _invariance(connection)
            provenance_counts = {
                row[0]: row[1]
                for row in connection.execute(
                    "SELECT table_name, loaded_rows FROM source.provenance"
                ).fetchall()
            }
            for table, count in baseline.items():
                if table == "provenance":
                    continue
                if provenance_counts.get(table) != count["count"]:
                    raise SystemExit(
                        f"invariance FAILED: {table} count disagrees with provenance"
                    )
            try:
                for statement in statements:
                    connection.execute(statement)
                with connection.cursor().copy(_copy_statement(table_rows)) as copy:
                    for frame in load_supplements_v11.iter_fits_copy_frames(
                        Path(pin.path),
                        table_rows,
                        batch_rows=settings.copy_batch_rows,
                    ):
                        copy.write(frame)
                loaded = _row_count(connection, TABLE)
                keys = connection.execute(
                    sql.SQL("SELECT count({id}), count(DISTINCT {id}) FROM {}.{}").format(
                        sql.Identifier("source"),
                        sql.Identifier(TABLE),
                        id=sql.Identifier("id_specz"),
                    )
                ).fetchone()
                observation = load_supplements_v11.inspect_fits_source(
                    Path(pin.path), table_rows
                )
                if loaded != observation.row_count:
                    raise SystemExit(
                        f"load FAILED: {loaded} rows != source {observation.row_count}"
                    )
                if keys[0] != loaded or keys[1] != loaded:
                    raise SystemExit(f"load FAILED: id_specz key violation: {keys}")
                connection.commit()
            except BaseException:
                connection.rollback()
                for statement in statements:
                    if statement.startswith("CREATE TABLE"):
                        connection.execute(
                            sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                                sql.Identifier("source"), sql.Identifier(TABLE)
                            )
                        )
                        connection.commit()
                raise
        evidence = _verify_loaded(connection, settings, table_rows, pin)
        evidence["principal_identity"] = principal
        evidence["ddl_statements_executed"] = len(statements) if args.load else None
        if args.load:
            after = _invariance(connection)
            drift = {
                table: after[table] != baseline[table]
                for table in PROTECTED_TABLES
            }
            if any(drift.values()):
                raise SystemExit(f"invariance FAILED: protected tables changed: {drift}")
            evidence["protected_tables_unchanged"] = True
        if args.register_provenance:
            evidence["provenance"] = _register_provenance(
                connection, settings, table_rows, pin
            )
    print(json.dumps(evidence, indent=2, default=str))


if __name__ == "__main__":
    main()
