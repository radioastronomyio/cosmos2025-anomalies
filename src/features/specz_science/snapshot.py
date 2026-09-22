"""Read-only capture of the build's consumed input identity (gate 5.1).

One REPEATABLE READ, READ ONLY transaction on the analyst connection exports
every field the build and its evidence consume, ordered by primary key, into
CSV artifacts under the configured snapshot directory, then records a
manifest with per-file SHA-256 digests, row counts, column lists, and the
captured principal identity. All later passes read this captured identity;
nothing re-reads the live mirror mid-build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from psycopg import sql

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402

SNAPSHOT_TABLES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "photometry_primary",
        (
            "id",
            "ra",
            "dec",
            "tile",
            "flag_star",
            "flag_blend",
            "mag_auto_f150w",
            "mag_auto_f277w",
            "mag_auto_f444w",
            "id_specz_khostovan25",
        ),
        "id",
    ),
    ("lephare", ("id", "type"), "id"),
    (
        "specz_compilation_unique",
        (
            "id_specz",
            "id_original",
            "ra_original",
            "dec_original",
            "ra_corrected",
            "dec_corrected",
            "priority",
            "specz",
            "flag",
            "confidence_level",
            "survey",
            "compilation_year",
            "public_or_private",
            "id_cos20_classic",
            "ra_cos20_classic",
            "dec_cos20_classic",
            "id_cos20_farmer",
            "ra_cos20_farmer",
            "dec_cos20_farmer",
            "id_cosmos25",
            "ra_cosmos25",
            "dec_cosmos25",
            "id_cosmos15",
            "ra_cosmos15",
            "dec_cosmos15",
            "id_cosmos09",
            "ra_cosmos09",
            "dec_cosmos09",
            "photoz",
            "photoz_type",
            "groupid",
            "groupsize",
        ),
        "id_specz",
    ),
    (
        "specz_compilation_all",
        (
            "id_specz",
            "id_original",
            "ra_original",
            "dec_original",
            "ra_corrected",
            "dec_corrected",
            "priority",
            "specz",
            "flag",
            "confidence_level",
            "survey",
            "compilation_year",
            "public_or_private",
            "id_cos20_classic",
            "ra_cos20_classic",
            "dec_cos20_classic",
            "id_cos20_farmer",
            "ra_cos20_farmer",
            "dec_cos20_farmer",
            "id_cosmos25",
            "ra_cosmos25",
            "dec_cosmos25",
            "id_cosmos15",
            "ra_cosmos15",
            "dec_cosmos15",
            "id_cosmos09",
            "ra_cosmos09",
            "dec_cosmos09",
            "photoz",
            "photoz_type",
            "groupid",
            "groupsize",
        ),
        "id_specz",
    ),
)


@dataclass(frozen=True)
class SnapshotFile:
    """One exported snapshot artifact and its identity."""

    table: str
    path: Path
    sha256: str
    bytes: int
    rows: int


def _copy_to_file(connection, table: str, columns: tuple[str, ...], order_by: str, path: Path) -> int:
    """Export one ordered table slice as deterministic CSV."""
    query = sql.SQL("COPY (SELECT {} FROM source.{} ORDER BY {}) TO STDOUT WITH (FORMAT csv, HEADER true)").format(
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.Identifier(table),
        sql.Identifier(order_by),
    )
    digest = hashlib.sha256()
    size = 0
    rows = connection.execute(
        sql.SQL("SELECT count(*) FROM source.{}").format(sql.Identifier(table))
    ).fetchone()[0]
    with path.open("wb") as handle:
        with connection.cursor().copy(query) as copy:
            for chunk in copy:
                data = bytes(chunk)
                digest.update(data)
                size += len(data)
                handle.write(data)
    return SnapshotFile(table, path, digest.hexdigest(), size, int(rows))


def capture_snapshot(
    paths: ss_config.SpeczSciencePaths | None = None,
) -> dict[str, object]:
    """Capture the consistent read-only input snapshot and its manifest."""
    if paths is None:
        paths = ss_config.resolve_paths()
    paths.snapshot_dir.mkdir(parents=True, exist_ok=True)
    connection, identity = ss_config.connect_analyst(paths=paths)
    connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    connection.execute("SET TRANSACTION READ ONLY")
    snapshot_at = datetime.now(timezone.utc).isoformat()
    transaction_snapshot = connection.execute(
        "SELECT txid_current_snapshot()::text"
    ).fetchone()[0]
    files: list[SnapshotFile] = []
    try:
        for table, columns, order_by in SNAPSHOT_TABLES:
            path = paths.snapshot_dir / f"{table}.csv"
            files.append(
                _copy_to_file(connection, table, columns, order_by, path)
            )
        connection.rollback()
    finally:
        connection.close()
    manifest = {
        "captured_at": snapshot_at,
        "mode": "analyst_read_only_repeatable_read",
        "transaction_snapshot": transaction_snapshot,
        "connection": {
            "database": identity.database,
            "user": identity.user,
        },
        "files": [
            {
                "table": item.table,
                "path": str(item.path),
                "sha256": item.sha256,
                "bytes": item.bytes,
                "data_rows": item.rows,
                "order_by": order_by,
                "columns": list(columns),
            }
            for item, (_, columns, order_by) in zip(files, SNAPSHOT_TABLES)
        ],
    }
    manifest_path = paths.snapshot_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return {**manifest, "manifest_path": str(manifest_path), "manifest_sha256": manifest_digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    manifest = capture_snapshot()
    print(
        json.dumps(
            {
                "manifest_path": manifest["manifest_path"],
                "manifest_sha256": manifest["manifest_sha256"],
                "files": [
                    {"table": f["table"], "rows": f["data_rows"], "sha256": f["sha256"]}
                    for f in manifest["files"]
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
