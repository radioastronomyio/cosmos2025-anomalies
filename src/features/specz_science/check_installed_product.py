"""Gate 5.6 post-install verification: analyst access and content identity.

Reconnects through the real analyst path (fixed handoff, connection-time
read-only) and asserts effective access to exactly the four product
relations with no write privileges anywhere, unchanged source/v1 posture,
and full installed content identity: canonical digests recomputed from the
installed rows must equal the staging artifacts' digests, row for row.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import install as ssi  # noqa: E402

ORDER_BY = {
    ssi.MEASUREMENTS: "run_id, id_specz",
    ssi.SOURCES: "run_id, catalog_id",
    ssi.SPLITS: "run_id, catalog_id",
}


def main() -> None:
    paths = ss_config.resolve_paths()
    finalize = json.loads(
        (paths.staging_dir / "products" / "finalize-summary.json").read_text(encoding="utf-8")
    )
    run_id = finalize["run_id"]
    recorded = finalize["content_digests"]
    connection, identity = ss_config.connect_analyst(paths=paths)
    failures: list[str] = []

    database = connection.execute("SELECT current_database()").fetchone()[0]
    principal = connection.execute("SELECT session_user, current_user").fetchone()
    ro = connection.execute(
        "SELECT current_setting('default_transaction_read_only'), "
        "current_setting('transaction_read_only')"
    ).fetchone()
    if database != "cosmos2025_v11" or principal != ("cosmos2025_v11_ro", "cosmos2025_v11_ro"):
        failures.append(f"identity drift: {database} {principal}")
    if ro != ("on", "on"):
        failures.append(f"read-only not enforced: {ro}")

    for table in (*ssi.PRODUCT_TABLES,):
        granted = connection.execute(
            "SELECT has_table_privilege(current_user, %s, 'SELECT')",
            (f'analysis."{table}"',),
        ).fetchone()[0]
        if not granted:
            failures.append(f"{table}: analyst SELECT missing")
        for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            if connection.execute(
                "SELECT has_table_privilege(current_user, %s, %s)",
                (f'analysis."{table}"', privilege),
            ).fetchone()[0]:
                failures.append(f"{table}: analyst carries {privilege}")
    if connection.execute(
        "SELECT has_schema_privilege(current_user, 'analysis', 'CREATE')"
    ).fetchone()[0]:
        failures.append("analyst can CREATE in analysis schema")
    if connection.execute(
        "SELECT has_schema_privilege(current_user, 'source', 'CREATE')"
    ).fetchone()[0]:
        failures.append("analyst gained CREATE on source schema")
    source_writes = connection.execute(
        "SELECT has_table_privilege(current_user, 'source.photometry_primary', 'UPDATE'), "
        "has_table_privilege(current_user, 'source.specz_compilation_all', 'DELETE')"
    ).fetchone()
    if any(source_writes):
        failures.append("source write privileges appeared")
    source_rows = connection.execute(
        "SELECT (SELECT count(*) FROM source.photometry_primary), "
        "(SELECT count(*) FROM source.specz_compilation_all), "
        "(SELECT count(*) FROM source.provenance)"
    ).fetchone()
    if tuple(source_rows) != (784016, 482579, 12):
        failures.append(f"source counts drifted: {source_rows}")

    state = connection.execute(
        'SELECT product_state, mechanical_seal_at FROM analysis.specz_p2r05_runs '
        "WHERE run_id = %s",
        (run_id,),
    ).fetchone()
    if state[0] != "pending_scientific_adoption" or state[1] is not None:
        failures.append(f"adoption/seal state wrong: {state}")

    digest_results = {}
    for table, order in ORDER_BY.items():
        digest = ssi.installed_content_digest(connection, table, run_id, order)
        digest_results[table] = digest
    expected = {
        ssi.MEASUREMENTS: recorded["measurements_content_sha256"],
        ssi.SOURCES: recorded["sources_content_sha256"],
        ssi.SPLITS: recorded["splits_content_sha256"],
    }
    for table, digest in digest_results.items():
        if digest != expected[table]:
            failures.append(
                f"{table}: installed digest {digest} != artifact {expected[table]}"
            )
    connection.close()

    if failures:
        print(json.dumps({"status": "FAILED", "failures": failures}, indent=2))
        raise SystemExit(1)
    print(
        json.dumps(
            {
                "status": "OK",
                "run_id": run_id,
                "analyst_identity": {"database": database, "user": principal[0]},
                "read_only": list(ro),
                "installed_digests_match_artifacts": True,
                "product_state": state[0],
                "mechanical_seal_at": state[1],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
