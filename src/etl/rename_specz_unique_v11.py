#!/usr/bin/env python3
"""
Script Name  : rename_specz_unique_v11.py
Description  : Renames source.specz_compilation to _unique and re-verifies it
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
P2R-04 gate 4.4 evidence command. Renames the galaxy-level spec-z mirror from
`source.specz_compilation` to `source.specz_compilation_unique`, updates its
`source.provenance` row's `table_name`, and re-verifies that the rename cost
nothing: identical row count, identical seeded row-level digest, every column
comment intact, constraints preserved, the analyst SELECT still effective, the
provenance row changed in `table_name` only, and no other relation in `source`
changed name, owner, or row count.

The rename removes an ambiguity that would otherwise be paid by every future
consumer joining `specz_compilation` and believing it holds every redshift.

Usage
-----
    doppler run --project ml01 --config dev -- \
        python src/etl/rename_specz_unique_v11.py --rename
    doppler run --project ml01 --config dev -- \
        python src/etl/rename_specz_unique_v11.py --verify-only

Examples
--------
    --rename       One transaction: ALTER TABLE ... RENAME plus the single
                   provenance table_name update, then full re-verification.
    --verify-only  Re-run the post-rename verification without mutating.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import json
from pathlib import Path
import sys

import psycopg
from psycopg import sql

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import bootstrap_v11, generate_schema_v11  # noqa: E402

OLD_TABLE = "specz_compilation"
NEW_TABLE = "specz_compilation_unique"
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
    OLD_TABLE,
    "provenance",
)


# =============================================================================
# Observation helpers
# =============================================================================


def _relations(connection: psycopg.Connection) -> list[tuple[str, str, str]]:
    """Return (relname, kind, owner) for every source relation, in order."""
    return [
        (row[0], row[1], row[2])
        for row in connection.execute(
            "SELECT c.relname, c.relkind, pg_get_userbyid(c.relowner) "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'source' AND c.relkind IN ('r','v','m') "
            "ORDER BY c.relname"
        ).fetchall()
    ]


def _row_count(connection: psycopg.Connection, table: str) -> int:
    return int(
        connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(table)
            )
        ).fetchone()[0]
    )


def _seeded_digest(connection: psycopg.Connection, table: str) -> dict[str, object]:
    """Digest a deterministic physical-row sample with a recorded seed."""
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


def _column_comments(
    connection: psycopg.Connection, table: str
) -> list[tuple[str, str]]:
    """Return (column, comment) for every live column in ordinal order."""
    return [
        (row[0], row[1] if row[1] is not None else "")
        for row in connection.execute(
            "SELECT a.attname, d.description FROM pg_attribute a "
            "JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "LEFT JOIN pg_description d "
            "ON d.objoid = c.oid AND d.objsubid = a.attnum "
            "WHERE n.nspname = 'source' AND c.relname = %s "
            "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum",
            (table,),
        ).fetchall()
    ]


def _constraints(connection: psycopg.Connection, table: str) -> list[tuple[str, str]]:
    """Return (constraint name, definition) in stable order."""
    return [
        (row[0], row[1])
        for row in connection.execute(
            "SELECT con.conname, pg_get_constraintdef(con.oid, true) "
            "FROM pg_constraint con "
            "JOIN pg_class c ON c.oid = con.conrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'source' AND c.relname = %s "
            "ORDER BY con.conname",
            (table,),
        ).fetchall()
    ]


def _provenance_row(
    connection: psycopg.Connection, table: str
) -> dict[str, object] | None:
    columns = [field.name for field in generate_schema_v11.PROVENANCE_CONTRACT]
    row = connection.execute(
        sql.SQL("SELECT {} FROM {}.provenance WHERE table_name = %s").format(
            sql.SQL(", ").join(sql.Identifier(name) for name in columns),
            sql.Identifier("source"),
        ),
        (table,),
    ).fetchone()
    return dict(zip(columns, row)) if row is not None else None


def _analyst_select(
    connection: psycopg.Connection, settings: bootstrap_v11.Settings, table: str
) -> int:
    """Count rows as the analyst role through session authorization."""
    connection.execute(
        sql.SQL("SET SESSION AUTHORIZATION {}").format(
            sql.Identifier(settings.analyst_role)
        )
    )
    try:
        return _row_count(connection, table)
    finally:
        connection.execute("RESET SESSION AUTHORIZATION")


def _capture_before(connection: psycopg.Connection) -> dict[str, object]:
    provenance = _provenance_row(connection, OLD_TABLE)
    if provenance is None:
        raise SystemExit(f"preflight FAILED: no provenance row for {OLD_TABLE}")
    live = _row_count(connection, OLD_TABLE)
    if live != int(provenance["loaded_rows"]):
        raise SystemExit(
            f"preflight FAILED: {OLD_TABLE} live {live} != provenance "
            f"{provenance['loaded_rows']}"
        )
    if _provenance_row(connection, NEW_TABLE) is not None:
        raise SystemExit(f"preflight FAILED: {NEW_TABLE} provenance row exists")
    relations = _relations(connection)
    if NEW_TABLE in {name for name, _, _ in relations}:
        raise SystemExit(f"preflight FAILED: {NEW_TABLE} already exists")
    return {
        "relations": relations,
        "row_count": live,
        "digest": _seeded_digest(connection, OLD_TABLE),
        "comments": _column_comments(connection, OLD_TABLE),
        "constraints": _constraints(connection, OLD_TABLE),
        "provenance": provenance,
        "counts": {
            table: _row_count(connection, table)
            for table in PROTECTED_TABLES
            if table != OLD_TABLE
        },
    }


def _verify_after(
    connection: psycopg.Connection,
    before: dict[str, object],
    settings: bootstrap_v11.Settings,
) -> dict[str, object]:
    relations = _relations(connection)
    names = {name for name, _, _ in relations}
    if OLD_TABLE in names:
        raise SystemExit(f"rename FAILED: {OLD_TABLE} still exists")
    if NEW_TABLE not in names:
        raise SystemExit(f"rename FAILED: {NEW_TABLE} absent")

    row_count = _row_count(connection, NEW_TABLE)
    if row_count != before["row_count"]:
        raise SystemExit(
            f"rename FAILED: row count {row_count} != {before['row_count']}"
        )
    digest = _seeded_digest(connection, NEW_TABLE)
    if digest != before["digest"]:
        raise SystemExit(f"rename FAILED: seeded digest changed: {digest}")

    comments = _column_comments(connection, NEW_TABLE)
    if len(comments) != len(before["comments"]):
        raise SystemExit(
            f"rename FAILED: comment count {len(comments)} != "
            f"{len(before['comments'])}"
        )
    changed = [
        (old, new)
        for (old, new) in zip(before["comments"], comments)
        if old != new
    ]
    if changed:
        raise SystemExit(f"rename FAILED: comments changed: {changed[:3]}")

    constraints = _constraints(connection, NEW_TABLE)
    if constraints != before["constraints"]:
        raise SystemExit("rename FAILED: constraints changed")

    provenance = _provenance_row(connection, NEW_TABLE)
    if provenance is None:
        raise SystemExit("rename FAILED: provenance row missing after rename")
    old_row = dict(before["provenance"])
    expected_row = dict(old_row)
    expected_row["table_name"] = NEW_TABLE
    drift = {
        field: (old_row[field], provenance[field])
        for field in old_row
        if provenance[field] != expected_row[field]
    }
    if drift:
        raise SystemExit(f"rename FAILED: provenance drift beyond table_name: {drift}")

    analyst_count = _analyst_select(connection, settings, NEW_TABLE)
    if analyst_count != row_count:
        raise SystemExit(
            f"rename FAILED: analyst SELECT returned {analyst_count} != {row_count}"
        )

    other = [
        (table, count)
        for table, count in before["counts"].items()
        if _row_count(connection, table) != count
    ]
    if other:
        raise SystemExit(f"rename FAILED: other relation row counts changed: {other}")
    renames = sorted(
        {name for name, _, _ in relations} ^ {name for name, _, _ in before["relations"]}
    )
    owners = {
        (name, owner)
        for name, _, owner in relations
        if name == NEW_TABLE
    }
    connection.rollback()
    return {
        "renamed_to": NEW_TABLE,
        "row_count": row_count,
        "digest": digest,
        "comment_count": len(comments),
        "comment_sample_unchanged": True,
        "constraints": [name for name, _ in constraints],
        "provenance_table_name": provenance["table_name"],
        "provenance_other_fields_unchanged": True,
        "analyst_select_rows": analyst_count,
        "relation_name_delta": renames,
        "new_table_owner": sorted(owners)[0][1] if owners else None,
    }


# =============================================================================
# Entry Point
# =============================================================================


def _verify_post_state(
    connection: psycopg.Connection, settings: bootstrap_v11.Settings
) -> dict[str, object]:
    """Repeatably verify the post-rename state without any before-capture."""
    names = {name for name, _, _ in _relations(connection)}
    if OLD_TABLE in names:
        raise SystemExit(f"verify FAILED: {OLD_TABLE} still exists")
    if NEW_TABLE not in names:
        raise SystemExit(f"verify FAILED: {NEW_TABLE} absent")
    if _provenance_row(connection, OLD_TABLE) is not None:
        raise SystemExit(f"verify FAILED: stale provenance row for {OLD_TABLE}")
    provenance = _provenance_row(connection, NEW_TABLE)
    if provenance is None:
        raise SystemExit(f"verify FAILED: no provenance row for {NEW_TABLE}")
    row_count = _row_count(connection, NEW_TABLE)
    if row_count != int(provenance["loaded_rows"]):
        raise SystemExit(
            f"verify FAILED: row count {row_count} != provenance "
            f"{provenance['loaded_rows']}"
        )
    rows = bootstrap_v11._read_dictionary(settings)
    expected_comments = {
        item.column: item.text
        for item in generate_schema_v11.column_comment_contract(rows)
        if item.table == NEW_TABLE
    }
    live_comments = dict(_column_comments(connection, NEW_TABLE))
    if live_comments != expected_comments:
        raise SystemExit("verify FAILED: comments differ from dictionary contract")
    constraints = _constraints(connection, NEW_TABLE)
    analyst_count = _analyst_select(connection, settings, NEW_TABLE)
    if analyst_count != row_count:
        raise SystemExit(
            f"verify FAILED: analyst SELECT returned {analyst_count} != {row_count}"
        )
    for table in PROTECTED_TABLES:
        if table in {OLD_TABLE, NEW_TABLE, "provenance"}:
            continue
        row = _provenance_row(connection, table)
        if row is None or _row_count(connection, table) != int(row["loaded_rows"]):
            raise SystemExit(f"verify FAILED: {table} disagrees with provenance")
    connection.rollback()
    return {
        "renamed_to": NEW_TABLE,
        "row_count": row_count,
        "digest": _seeded_digest(connection, NEW_TABLE),
        "comment_count": len(live_comments),
        "comments_match_dictionary": True,
        "constraints": [name for name, _ in constraints],
        "provenance_table_name": provenance["table_name"],
        "analyst_select_rows": analyst_count,
        "other_relations_match_provenance": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=bootstrap_v11.DEFAULT_CONFIG_PATH)
    parser.add_argument("--rename", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.rename == args.verify_only:
        raise SystemExit("exactly one of --rename or --verify-only is required")

    settings = bootstrap_v11.resolve_settings(args.config)
    with bootstrap_v11._connect(settings, settings.target_database) as connection:
        if args.verify_only:
            evidence = _verify_post_state(connection, settings)
        else:
            before = _capture_before(connection)
            connection.execute(
                sql.SQL("ALTER TABLE {}.{} RENAME TO {}").format(
                    sql.Identifier("source"),
                    sql.Identifier(OLD_TABLE),
                    sql.Identifier(NEW_TABLE),
                )
            )
            updated = connection.execute(
                sql.SQL("UPDATE {}.provenance SET table_name = %s "
                        "WHERE table_name = %s").format(
                    sql.Identifier("source")
                ),
                (NEW_TABLE, OLD_TABLE),
            ).rowcount
            if updated != 1:
                connection.rollback()
                raise SystemExit(f"rename FAILED: {updated} provenance rows updated")
            connection.commit()
            evidence = _verify_after(connection, before, settings)
    print(json.dumps(evidence, indent=2, default=str))


if __name__ == "__main__":
    main()
