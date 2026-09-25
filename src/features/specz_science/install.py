"""Bounded bootstrap and installation of the four P2R-05 analysis tables.

Administrative credentials (supplied only through the scoped Doppler
runtime) are authorized for exactly this: creating the ``analysis`` schema
if absent, the four named product relations with their constraints,
indexes, and comments, and bounded USAGE/SELECT grants to the existing
analyst role. Source rows are never touched: the installer consumes the
verified staging JSONL artifacts produced by the builder.

Installation is transactional and identity-aware: a repeat request with the
same run identity verifies equality and changes nothing; a conflicting
payload under the same run id fails before modifying existing rows. The
down operation removes only this unit's rows and only newly created
objects, and never runs after an uncertain commit.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from psycopg import sql  # noqa: E402

from src.features.specz_science import canonical as ss_canonical  # noqa: E402
from src.features.specz_science import config as ss_config  # noqa: E402

SCHEMA = "analysis"
RUNS = "specz_p2r05_runs"
MEASUREMENTS = "specz_p2r05_measurements"
SOURCES = "specz_p2r05_sources"
SPLITS = "specz_p2r05_splits"
PRODUCT_TABLES = (RUNS, MEASUREMENTS, SOURCES, SPLITS)
ANALYST_ROLE = "cosmos2025_v11_ro"

TYPE_MAP: dict[str, str] = {}

NATIVE_TYPES = {
    "id_original": "text",
    "ra_original": "double precision",
    "dec_original": "double precision",
    "ra_corrected": "double precision",
    "dec_corrected": "double precision",
    "priority": "bigint",
    "specz": "double precision",
    "flag": "bigint",
    "confidence_level": "bigint",
    "survey": "bigint",
    "compilation_year": "bigint",
    "public_or_private": "bigint",
    "id_cos20_classic": "bigint",
    "ra_cos20_classic": "double precision",
    "dec_cos20_classic": "double precision",
    "id_cos20_farmer": "bigint",
    "ra_cos20_farmer": "double precision",
    "dec_cos20_farmer": "double precision",
    "id_cosmos25": "bigint",
    "ra_cosmos25": "double precision",
    "dec_cosmos25": "double precision",
    "id_cosmos15": "bigint",
    "ra_cosmos15": "double precision",
    "dec_cosmos15": "double precision",
    "id_cosmos09": "bigint",
    "ra_cosmos09": "double precision",
    "dec_cosmos09": "double precision",
    "photoz": "double precision",
    "photoz_type": "bigint",
    "groupid": "bigint",
    "groupsize": "bigint",
}

MEASUREMENT_DERIVED_TYPES = {
    "association_status": "text",
    "resolved_catalog_id": "bigint",
    "is_unique_member": "boolean",
    "numeric_valid_z": "boolean",
    "z_invalid_reason": "text",
    "flag_category": "text",
    "confidence_in_domain": "boolean",
    "flag_confidence_mapping_consistent": "boolean",
    "secure_measurement": "boolean",
    "secure_block_reasons": "jsonb",
}

SOURCE_TYPES = {
    "association_resolved": "boolean",
    "population_a": "boolean",
    "population_b": "boolean",
    "unique_entry_count": "integer",
    "all_entry_count": "integer",
    "numeric_valid_all_count": "integer",
    "secure_all_count": "integer",
    "preferred_id_specz": "bigint",
    "preferred_reported_z": "double precision",
    "preferred_flag": "bigint",
    "preferred_confidence": "bigint",
    "preferred_tie": "boolean",
    "preferred_tied_ids": "jsonb",
    "preferred_entry_is_secure": "boolean",
    "unique_numeric_conflict": "boolean",
    "secure_all_conflict": "boolean",
    "other_measurement_disagreement": "boolean",
    "conflict_witnesses": "jsonb",
    "corroboration_status": "text",
    "lephare_type": "bigint",
    "classification_label": "text",
    "broad_line_reported": "boolean",
    "broad_line_entry_ids": "jsonb",
    "broad_line_confidences": "jsonb",
    "photometric_qso": "boolean",
    "flag_star_mask_overlap": "boolean",
    "flag_blend": "boolean",
    "native_tile": "text",
    "eligibility_primary_galaxy": "boolean",
    "eligibility_separate_validation": "boolean",
    "eligibility_basis_primary_pre_split": "boolean",
    "eligibility_basis_validation_pre_split": "boolean",
    "assigned_split": "text",
    "exclusion_reasons": "jsonb",
}

SPLIT_TYPES = {
    "native_tile": "text",
    "assigned_split": "text",
    "split_version": "text",
    "split_salt": "text",
    "valid_tile_domain_member": "boolean",
    "unassigned": "boolean",
}

RUNS_TYPES = {
    "policy_id": "text",
    "spec_version": "text",
    "spec_sha256": "text",
    "policy_semantic_digest": "text",
    "snapshot_manifest_digest": "text",
    "snapshot_file_digests": "jsonb",
    "implementation": "jsonb",
    "measurements_content_sha256": "text",
    "sources_content_sha256": "text",
    "splits_content_sha256": "text",
    "measurement_rows": "bigint",
    "source_rows": "bigint",
    "split_rows": "bigint",
    "tile_map_canonical_digest": "text",
    "tile_map": "jsonb",
    "product_state": "text",
    "mechanical_seal_at": "text",
    "mechanical_seal_evidence": "jsonb",
    "created_at": "text",
    "installed_by": "text",
}


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def ddl_statements() -> list[str]:
    """The complete tracked DDL for the four product relations."""
    measurement_columns = [
        ("run_id", "text", "NOT NULL"),
        ("id_specz", "bigint", "NOT NULL"),
        *[
            ("native_" + name, native_type, "")
            for name, native_type in NATIVE_TYPES.items()
        ],
        *[(name, dtype, "") for name, dtype in MEASUREMENT_DERIVED_TYPES.items()],
    ]
    source_columns = [
        ("run_id", "text", "NOT NULL"),
        ("catalog_id", "bigint", "NOT NULL"),
        *[(name, dtype, "") for name, dtype in SOURCE_TYPES.items()],
    ]
    split_columns = [
        ("run_id", "text", "NOT NULL"),
        ("catalog_id", "bigint", "NOT NULL"),
        *[(name, dtype, "") for name, dtype in SPLIT_TYPES.items()],
    ]
    runs_columns = [
        ("run_id", "text", ""),
        *[(name, dtype, "") for name, dtype in RUNS_TYPES.items()],
    ]
    statements: list[str] = []

    def create(table: str, columns: Sequence[tuple[str, str, str]], key: str) -> str:
        body = ",\n    ".join(
            f"{_quoted(name)} {dtype} {constraint}".strip()
            for name, dtype, constraint in columns
        )
        return (
            f'CREATE TABLE {_quoted(SCHEMA)}.{_quoted(table)} (\n    {body},\n'
            f"    PRIMARY KEY ({key}),\n"
            f"    FOREIGN KEY (run_id) REFERENCES {_quoted(SCHEMA)}.{_quoted(RUNS)} (run_id)\n"
            f")"
        )

    statements.append(f"CREATE SCHEMA IF NOT EXISTS {_quoted(SCHEMA)}")
    statements.append(create(RUNS, runs_columns, "run_id"))
    statements.append(create(MEASUREMENTS, measurement_columns, "run_id, id_specz"))
    statements.append(create(SOURCES, source_columns, "run_id, catalog_id"))
    statements.append(create(SPLITS, split_columns, "run_id, catalog_id"))
    statements.append(
        f"COMMENT ON TABLE {_quoted(SCHEMA)}.{_quoted(RUNS)} IS "
        "'P2R-05 run metadata: policy/input/implementation identities, "
        "canonical content digests, mechanical seal state, and "
        "pending_scientific_adoption product state. Outside the content "
        "digest domains.'"
    )
    statements.append(
        f"COMMENT ON TABLE {_quoted(SCHEMA)}.{_quoted(MEASUREMENTS)} IS "
        "'P2R-05 measurement audit: one row per (run_id, id_specz) over "
        "specz_compilation_all. native_* columns are unmodified copies "
        "including finite sentinels; remaining columns are derived "
        "predicates and reasons under policy p2r05-specz-policy-v1.'"
    )
    statements.append(
        f"COMMENT ON TABLE {_quoted(SCHEMA)}.{_quoted(SOURCES)} IS "
        "'P2R-05 source summary: one row per (run_id, catalog_id) over the "
        "full photometric catalog. Preferred entries, conflict flags with "
        "resolvable witnesses, classification evidence, finalized "
        "eligibility, and overlapping exclusion reasons.'"
    )
    statements.append(
        f"COMMENT ON TABLE {_quoted(SCHEMA)}.{_quoted(SPLITS)} IS "
        "'P2R-05 frozen partitions: one row per (run_id, catalog_id); tile "
        "assignment under p2r05-spatial-v1, assigned before any fitting or "
        "outcome analysis.'"
    )
    for table, column, comment in (
        (MEASUREMENTS, "native_specz", "Native redshift copy; -9 and other finite sentinels are values, not NULLs"),
        (MEASUREMENTS, "resolved_catalog_id", "Nullable resolved photometry_primary.id through id_cosmos25"),
        (SOURCES, "preferred_reported_z", "Copied from the selected _unique row, never averaged"),
        (SOURCES, "conflict_witnesses", "Pairwise witness records resolving to exact audited entries"),
        (SOURCES, "eligibility_primary_galaxy", "P-05 primary galaxy calibration eligibility, split-gated"),
        (SOURCES, "eligibility_separate_validation", "P-05 broad-line/photometric-QSO validation eligibility, split-gated"),
        (SPLITS, "assigned_split", "development | validation | holdout | unassigned"),
        (RUNS, "product_state", "pending_scientific_adoption until the operator answers S5-Q01..Q05"),
    ):
        statements.append(
            f"COMMENT ON COLUMN {_quoted(SCHEMA)}.{_quoted(table)}.{_quoted(column)} IS '{comment}'"
        )
    statements.append(
        f"CREATE INDEX {_quoted('specz_p2r05_measurements_source_idx')} ON "
        f"{_quoted(SCHEMA)}.{_quoted(MEASUREMENTS)} (run_id, resolved_catalog_id)"
    )
    statements.append(
        f"CREATE INDEX {_quoted('specz_p2r05_sources_primary_idx')} ON "
        f"{_quoted(SCHEMA)}.{_quoted(SOURCES)} (run_id) WHERE eligibility_primary_galaxy"
    )
    statements.append(
        f"CREATE INDEX {_quoted('specz_p2r05_sources_validation_idx')} ON "
        f"{_quoted(SCHEMA)}.{_quoted(SOURCES)} (run_id) WHERE eligibility_separate_validation"
    )
    statements.append(
        f"CREATE INDEX {_quoted('specz_p2r05_splits_split_idx')} ON "
        f"{_quoted(SCHEMA)}.{_quoted(SPLITS)} (run_id, assigned_split)"
    )
    statements.append(f"GRANT USAGE ON SCHEMA {_quoted(SCHEMA)} TO {_quoted(ANALYST_ROLE)}")
    for table in (RUNS, MEASUREMENTS, SOURCES, SPLITS):
        statements.append(
            f"GRANT SELECT ON {_quoted(SCHEMA)}.{_quoted(table)} TO {_quoted(ANALYST_ROLE)}"
        )
    return statements


def _jsonl_columns(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as handle:
        first = json.loads(handle.readline())
        return list(first)


def _records(path: Path) -> Iterator[dict[str, Any]]:
    for record in ss_canonical.read_jsonl(path):
        yield record


def _copy_batches(
    path: Path, columns: Sequence[str], batch_rows: int
) -> Iterator[tuple[str, io.StringIO]]:
    """Translate canonical JSONL into CSV COPY payloads batch by batch."""
    buffer: list[dict[str, Any]] = []
    for record in _records(path):
        buffer.append(record)
        if len(buffer) >= batch_rows:
            yield _render_csv(buffer, columns)
            buffer = []
    if buffer:
        yield _render_csv(buffer, columns)


def _render_csv(buffer: list[dict[str, Any]], columns: Sequence[str]) -> tuple[str, io.StringIO]:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for record in buffer:
        writer.writerow(
            [
                _csv_value(record.get(column))
                for column in columns
            ]
        )
    return "", output


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def install(
    connection: psycopg.Connection,
    *,
    products_dir: Path,
    run_metadata: Mapping[str, Any],
    batch_rows: int = 2000,
) -> dict[str, Any]:
    """Install the four tables from verified local artifacts, transactionally.

    Idempotent by run identity: an existing identical run verifies and
    returns without mutation; a conflicting same-id payload fails before
    modifying existing rows.
    """
    existing = _existing_state(connection)
    run_id = run_metadata["run_id"]
    if existing["runs_present"]:
        return _verify_repeat_install(
            connection, products_dir=products_dir, run_metadata=run_metadata
        )
    if existing["relations_present"] or existing["schema_has_other_objects"]:
        raise SystemExit(
            f"install FAILED: analysis schema state is not a clean bootstrap: {existing}"
        )
    statements = ddl_statements()
    ARTIFACT_NAMES = {
        MEASUREMENTS: "measurements.jsonl",
        SOURCES: "sources.jsonl",
        SPLITS: "splits.jsonl",
    }
    columns = {
        table: _jsonl_columns(products_dir / filename)
        for table, filename in ARTIFACT_NAMES.items()
    }
    for table, names in columns.items():
        expected = _expected_columns(table)
        if set(names) != set(expected):
            raise SystemExit(
                f"install FAILED: {table} artifact columns {sorted(set(names) ^ set(expected))} differ from DDL"
            )
    run_row = _run_row(run_metadata, connection)
    commit_attempted = False
    try:
        for statement in statements:
            connection.execute(statement)
        run_columns = list(run_row)
        with connection.cursor().copy(
            sql.SQL("COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv)").format(
                sql.Identifier(SCHEMA),
                sql.Identifier(RUNS),
                sql.SQL(", ").join(sql.Identifier(name) for name in run_columns),
            )
        ) as copy:
            _, payload = _render_csv([run_row], run_columns)
            copy.write(payload.getvalue().encode("utf-8"))
        for table in (MEASUREMENTS, SOURCES, SPLITS):
            names = columns[table]
            with connection.cursor().copy(
                sql.SQL("COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv)").format(
                    sql.Identifier(SCHEMA),
                    sql.Identifier(table),
                    sql.SQL(", ").join(sql.Identifier(name) for name in names),
                )
            ) as copy:
                for _, payload in _copy_batches(
                    products_dir / ARTIFACT_NAMES[table], names, batch_rows
                ):
                    copy.write(payload.getvalue().encode("utf-8"))
        counts = {
            table: connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{} WHERE run_id = %s").format(
                    sql.Identifier(SCHEMA), sql.Identifier(table)
                ),
                (run_id,),
            ).fetchone()[0]
            for table in (MEASUREMENTS, SOURCES, SPLITS)
        }
        expected_counts = {
            MEASUREMENTS: run_metadata["content_digests"]["measurement_rows"],
            SOURCES: run_metadata["content_digests"]["source_rows"],
            SPLITS: run_metadata["content_digests"]["split_rows"],
        }
        if counts != expected_counts:
            raise SystemExit(f"install FAILED: counts {counts} != {expected_counts}")
        commit_attempted = True
        connection.commit()
    except BaseException:
        if not commit_attempted:
            connection.rollback()
        # After an uncertain commit no destructive cleanup runs; the state
        # is classified read-only by an independent probe if needed.
        raise
    return {"installed": True, "run_id": run_id, "counts": counts}


def _expected_columns(table: str) -> list[str]:
    if table == MEASUREMENTS:
        return [
            "run_id",
            "id_specz",
            *("native_" + name for name in NATIVE_TYPES),
            *MEASUREMENT_DERIVED_TYPES,
        ]
    if table == SOURCES:
        return ["run_id", "catalog_id", *SOURCE_TYPES]
    if table == SPLITS:
        return ["run_id", "catalog_id", *SPLIT_TYPES]
    return ["run_id", *RUNS_TYPES]


def _run_row(run_metadata: Mapping[str, Any], connection: psycopg.Connection) -> dict[str, Any]:
    digests = run_metadata["content_digests"]
    return {
        "run_id": run_metadata["run_id"],
        "policy_id": run_metadata["policy_id"],
        "spec_version": run_metadata["spec_version"],
        "spec_sha256": run_metadata["spec_sha256"],
        "policy_semantic_digest": run_metadata["policy_semantic_digest"],
        "snapshot_manifest_digest": run_metadata["snapshot_manifest_digest"],
        "snapshot_file_digests": run_metadata["snapshot_file_digests"],
        "implementation": run_metadata["implementation"],
        "measurements_content_sha256": digests["measurements_content_sha256"],
        "sources_content_sha256": digests["sources_content_sha256"],
        "splits_content_sha256": digests["splits_content_sha256"],
        "measurement_rows": digests["measurement_rows"],
        "source_rows": digests["source_rows"],
        "split_rows": digests["split_rows"],
        "tile_map_canonical_digest": run_metadata["tile_map_canonical_digest"],
        "tile_map": run_metadata["tile_map"],
        "product_state": "pending_scientific_adoption",
        "mechanical_seal_at": None,
        "mechanical_seal_evidence": None,
        "created_at": run_metadata["created_at"],
        "installed_by": run_metadata["installed_by"],
    }


def _existing_state(connection: psycopg.Connection) -> dict[str, Any]:
    schema_exists = connection.execute(
        "SELECT to_regnamespace(%s) IS NOT NULL", (SCHEMA,)
    ).fetchone()[0]
    relations = [
        row[0]
        for row in connection.execute(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relkind = 'r' ORDER BY c.relname",
            (SCHEMA,),
        ).fetchall()
    ]
    return {
        "schema_exists": bool(schema_exists),
        "relations_present": [name for name in relations if name in PRODUCT_TABLES],
        "schema_has_other_objects": [name for name in relations if name not in PRODUCT_TABLES],
        "runs_present": RUNS in relations,
    }


def _verify_repeat_install(
    connection: psycopg.Connection, *, products_dir: Path, run_metadata: Mapping[str, Any]
) -> dict[str, Any]:
    run_id = run_metadata["run_id"]
    live_columns = [
        row[0]
        for row in connection.execute(
            "SELECT a.attname FROM pg_attribute a "
            "JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s "
            "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum",
            (SCHEMA, RUNS),
        ).fetchall()
    ]
    if set(live_columns) != set(_expected_columns(RUNS)):
        raise SystemExit(
            "install FAILED: pre-existing analysis.specz_p2r05_runs does not "
            "match this contract; refusing to modify it"
        )
    stored = connection.execute(
        sql.SQL("SELECT measurements_content_sha256, sources_content_sha256, "
                "splits_content_sha256, product_state FROM {}.{} WHERE run_id = %s").format(
            sql.Identifier(SCHEMA), sql.Identifier(RUNS)
        ),
        (run_id,),
    ).fetchone()
    if stored is None:
        raise SystemExit(
            f"install FAILED: runs table present without run id {run_id}; "
            "coexistence requires its own operator-reviewed installation"
        )
    digests = run_metadata["content_digests"]
    incoming = (
        digests["measurements_content_sha256"],
        digests["sources_content_sha256"],
        digests["splits_content_sha256"],
    )
    if tuple(stored[:3]) != incoming:
        raise SystemExit(
            f"install FAILED: run id {run_id} exists with different content "
            f"digests; refusing to modify existing rows"
        )
    counts = {
        table: connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{} WHERE run_id = %s").format(
                sql.Identifier(SCHEMA), sql.Identifier(table)
            ),
            (run_id,),
        ).fetchone()[0]
        for table in (MEASUREMENTS, SOURCES, SPLITS)
    }
    return {
        "installed": False,
        "run_id": run_id,
        "unchanged": True,
        "counts": counts,
        "product_state": stored[3],
    }


def installed_content_digest(
    connection: psycopg.Connection, table: str, run_id: str, order_by: str
) -> tuple[str, int]:
    """Recompute the canonical content digest from installed rows."""
    columns = _expected_columns(table)
    digest = ss_canonical.digest_records(
        _stream_installed(connection, table, run_id, order_by, columns)
    )
    return digest


def _stream_installed(
    connection: psycopg.Connection, table: str, run_id: str, order_by: str, columns: Sequence[str]
) -> Iterator[dict[str, Any]]:
    query = sql.SQL("SELECT {} FROM {}.{} WHERE run_id = %s ORDER BY {}").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in columns),
        sql.Identifier(SCHEMA),
        sql.Identifier(table),
        sql.SQL(order_by),
    )
    with connection.cursor(name=f"p2r05_verify_{table}") as cursor:
        cursor.itersize = 5000
        cursor.execute(query, (run_id,))
        while True:
            rows = cursor.fetchmany(5000)
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))


def down(connection: psycopg.Connection, *, run_id: str, created_objects: Sequence[str]) -> dict[str, Any]:
    """Remove only this unit's rows and only objects the ledger proves new.

    Deletes the named run's rows from all four relations, then drops each
    product relation only when it is in the startup ledger of newly created
    objects and now empty (no unrelated dependents or surviving runs). The
    schema drops only when empty and newly created. Grants this run added
    are revoked only when no retained product depends on them.
    """
    removed: dict[str, int] = {}
    for table in (MEASUREMENTS, SOURCES, SPLITS, RUNS):
        removed[table] = connection.execute(
            sql.SQL("WITH removed AS (DELETE FROM {}.{} WHERE run_id = %s RETURNING 1) "
                    "SELECT count(*) FROM removed").format(
                sql.Identifier(SCHEMA), sql.Identifier(table)
            ),
            (run_id,),
        ).fetchone()[0]
    dropped: list[str] = []
    for table in (MEASUREMENTS, SOURCES, SPLITS, RUNS):
        if table not in created_objects:
            continue
        survivors = connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier(SCHEMA), sql.Identifier(table)
            )
        ).fetchone()[0]
        if survivors == 0:
            connection.execute(
                sql.SQL("DROP TABLE {}.{}").format(
                    sql.Identifier(SCHEMA), sql.Identifier(table)
                )
            )
            dropped.append(table)
    remaining_relations = [
        row[0]
        for row in connection.execute(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relkind = 'r'",
            (SCHEMA,),
        ).fetchall()
    ]
    schema_dropped = False
    revoked_grants = False
    if not remaining_relations and SCHEMA in created_objects:
        connection.execute(
            sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(SCHEMA))
        )
        schema_dropped = True
        revoked_grants = True
    connection.commit()
    return {
        "removed_rows": removed,
        "dropped_tables": dropped,
        "schema_dropped": schema_dropped,
        "grants_revoked": revoked_grants,
    }


def run_metadata_from_staging(paths: ss_config.SpeczSciencePaths) -> dict[str, Any]:
    """Assemble the run metadata document from staging summaries."""
    from src.features.specz_science import policy as ss_policy
    from src.features.specz_science.pipeline import resolve_run_identity

    identity = resolve_run_identity(paths)
    finalize = json.loads(
        (paths.staging_dir / "products" / "finalize-summary.json").read_text(encoding="utf-8")
    )
    policy = ss_policy.load_frozen_policy(paths.policy_path)
    import datetime as dt

    return {
        "run_id": finalize["run_id"],
        "policy_id": policy["policy_id"],
        "spec_version": policy["spec_identity"]["version"],
        "spec_sha256": policy["spec_identity"]["sha256"],
        "policy_semantic_digest": identity["policy_semantic_digest"],
        "snapshot_manifest_digest": identity["snapshot_manifest_digest"],
        "snapshot_file_digests": identity["snapshot_file_digests"],
        "implementation": identity["implementation"],
        "content_digests": finalize["content_digests"],
        "tile_map_canonical_digest": finalize["tile_map_canonical_digest"],
        "tile_map": finalize["tile_map"],
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "installed_by": "p2r05-install",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=None, help="target database (default: configured target)")
    parser.add_argument("--batch-rows", type=int, default=None)
    args = parser.parse_args()
    from src.etl import bootstrap_v11

    paths = ss_config.resolve_paths()
    settings = bootstrap_v11.resolve_settings(bootstrap_v11.DEFAULT_CONFIG_PATH)
    database = args.database or settings.target_database
    if database != settings.target_database:
        from src.etl import verify_schema_v11_scratch as scratch

        scratch.validate_scratch_name(database)
    metadata = run_metadata_from_staging(paths)
    products = paths.staging_dir / "products"
    with bootstrap_v11._connect(settings, database) as connection:
        result = install(
            connection,
            products_dir=products,
            run_metadata=metadata,
            batch_rows=args.batch_rows or paths.install_batch_rows,
        )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
