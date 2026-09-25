"""Gate 5.1 preflight: access verification, pin comparison, before-state.

Three verifications run before any expensive work:

1. ``--analyst`` — the fixed analyst handoff opens a direct connection to the
   configured database with connection-time read-only enforcement; database,
   principal, read-only settings, SELECT presence, and write-privilege
   absence are asserted against the 13 source relations; the ``analysis``
   schema's existence is recorded, not assumed.
2. ``--pins`` — manifest pins and ``source.provenance`` registrations are
   compared against freshly computed hashes of the consumed artifacts.
   Dictionaries and configuration bytes are hashed for the input identity.
3. ``--before-state`` — relation definitions, counts, and seeded content
   digests for every source relation are captured through the analyst path;
   protected v1 identity is captured through the admin transport under an
   enforced read-only transaction (requires the scoped Doppler runtime).

Evidence JSON lands under the configured staging directory; nothing here
writes to any database.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import yaml
from psycopg import sql

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402

SOURCE_TABLES = (
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
    "specz_compilation_unique",
    "specz_compilation_all",
)
EXPECTED_COUNTS = {
    "photometry_primary": 784_016,
    "specz_compilation_unique": 261_975,
    "specz_compilation_all": 482_579,
    "provenance": 12,
}
EXPECTED_ANALYST_ROLE = "cosmos2025_v11_ro"
EXPECTED_DATABASE = "cosmos2025_v11"
DIGEST_MODULUS = 977
DIGEST_OFFSET = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def verify_analyst_access(paths: ss_config.SpeczSciencePaths) -> dict[str, object]:
    """Assert the analyst contract on a fresh direct connection."""
    connection, identity = ss_config.connect_analyst(paths=paths)
    evidence: dict[str, object] = {
        "recorded_at": _utc_now(),
        "connection": {
            "host": identity.host,
            "port": identity.port,
            "database": identity.database,
            "session_user": connection.execute(
                "SELECT session_user"
            ).fetchone()[0],
            "current_user": connection.execute(
                "SELECT current_user"
            ).fetchone()[0],
        },
    }
    if identity.database != EXPECTED_DATABASE:
        raise SystemExit(
            f"preflight FAILED: connected database {identity.database!r} != {EXPECTED_DATABASE!r}"
        )
    for field in ("session_user", "current_user"):
        principal = evidence["connection"][field]
        if principal != EXPECTED_ANALYST_ROLE:
            raise SystemExit(
                f"preflight FAILED: {field} is {principal!r}, expected "
                f"{EXPECTED_ANALYST_ROLE!r}"
            )
    settings_row = connection.execute(
        "SELECT current_setting('default_transaction_read_only'), "
        "current_setting('transaction_read_only')"
    ).fetchone()
    evidence["read_only"] = {
        "default_transaction_read_only": settings_row[0],
        "transaction_read_only": settings_row[1],
    }
    if settings_row[0] != "on" or settings_row[1] != "on":
        raise SystemExit(
            f"preflight FAILED: read-only settings not enforced: {settings_row}"
        )
    attributes = connection.execute(
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, "
        "rolbypassrls FROM pg_roles WHERE rolname = current_user"
    ).fetchone()
    evidence["role_attributes"] = {
        "superuser": attributes[0],
        "createdb": attributes[1],
        "createrole": attributes[2],
        "replication": attributes[3],
        "bypassrls": attributes[4],
    }
    if any(attributes):
        raise SystemExit(f"preflight FAILED: analyst carries privileged attributes")
    db_privileges = connection.execute(
        "SELECT has_database_privilege(current_user, current_database(), 'CONNECT'), "
        "has_database_privilege(current_user, current_database(), 'CREATE')"
    ).fetchone()
    evidence["database_privileges"] = {
        "connect": db_privileges[0],
        "create": db_privileges[1],
    }
    if not db_privileges[0] or db_privileges[1]:
        raise SystemExit(
            f"preflight FAILED: unexpected database privileges {db_privileges}"
        )
    relations: dict[str, object] = {}
    failures: list[str] = []
    for table in (*SOURCE_TABLES, "provenance"):
        qualified = f'source."{table}"'
        count = connection.execute(
            sql.SQL("SELECT count(*) FROM source.{}").format(sql.Identifier(table))
        ).fetchone()[0]
        privileges = connection.execute(
            "SELECT has_table_privilege(current_user, %s, 'SELECT'), "
            "has_table_privilege(current_user, %s, 'INSERT'), "
            "has_table_privilege(current_user, %s, 'UPDATE'), "
            "has_table_privilege(current_user, %s, 'DELETE'), "
            "has_table_privilege(current_user, %s, 'TRUNCATE'), "
            "has_schema_privilege(current_user, 'source', 'USAGE'), "
            "has_schema_privilege(current_user, 'source', 'CREATE')",
            (qualified, qualified, qualified, qualified, qualified),
        ).fetchone()
        owner = connection.execute(
            "SELECT pg_get_userbyid(c.relowner) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'source' AND c.relname = %s",
            (table,),
        ).fetchone()[0]
        relations[table] = {
            "rows": count,
            "select": privileges[0],
            "insert": privileges[1],
            "update": privileges[2],
            "delete": privileges[3],
            "truncate": privileges[4],
            "source_schema_usage": privileges[5],
            "source_schema_create": privileges[6],
            "owner": owner,
        }
        if not privileges[0]:
            failures.append(f"{table}: analyst SELECT missing")
        if any(privileges[1:5]):
            failures.append(f"{table}: analyst carries write privilege")
        if not privileges[5] or privileges[6]:
            failures.append(f"{table}: unexpected source schema privileges")
        if owner == EXPECTED_ANALYST_ROLE:
            failures.append(f"{table}: analyst owns a source relation")
        if table in EXPECTED_COUNTS and count != EXPECTED_COUNTS[table]:
            failures.append(
                f"{table}: row count {count} != expected {EXPECTED_COUNTS[table]}"
            )
    evidence["relations"] = relations
    if failures:
        raise SystemExit(f"preflight FAILED: {failures}")
    analysis_state = connection.execute(
        "SELECT to_regnamespace('analysis'), "
        "(SELECT count(*) FROM pg_namespace WHERE nspname = 'analysis')"
    ).fetchone()
    evidence["analysis_schema"] = {
        "regnamespace": analysis_state[0],
        "present": int(analysis_state[1]) > 0,
        "expected_at_gate_5_1": False,
    }
    connection.rollback()
    connection.close()
    return evidence


def verify_input_pins(paths: ss_config.SpeczSciencePaths) -> dict[str, object]:
    """Compare manifest/provenance pins against freshly computed hashes."""
    repo_config = yaml.safe_load(
        (REPO_ROOT / "configs" / "data_paths.yaml").read_text(encoding="utf-8")
    )
    manifest_path = Path(repo_config["provenance"]["source_manifest_v11"])
    manifest_rows = {
        f"{row['root']}/{row['relative_path']}": row
        for row in csv.DictReader(manifest_path.open(encoding="utf-8"))
    }
    artifacts: dict[str, object] = {}
    for name in ("unique_fits", "all_fits"):
        path = Path(repo_config["specz"][name])
        observed, size = _sha256_file(path)
        manifest_row = manifest_rows.get(str(path))
        declared = manifest_row["sha256"] if manifest_row else None
        artifacts[name] = {
            "path": str(path),
            "bytes": size,
            "manifest_sha256": declared,
            "observed_sha256": observed,
            "agree": declared == observed,
        }
        if declared != observed:
            raise SystemExit(
                f"pins FAILED: {name} manifest {declared} != observed {observed}"
            )
    definitions = {}
    for label, path in (
        ("columns_v11_csv", repo_config["dictionary"]["columns_v11"]),
        ("data_paths_yaml", REPO_ROOT / "configs" / "data_paths.yaml"),
        ("policy_v1_yaml", paths.policy_path),
        ("approved_spec", Path(
            "/opt/agents/repos/spec/"
            "2026-09-21-cosmos2025-spec-p2r-05-specz-science-surface.md"
        )),
        ("dispositions_record",
         paths.evidence_dir.parent / "specz-science-dispositions.md"),
    ):
        digest, size = _sha256_file(Path(path))
        definitions[label] = {"path": str(path), "bytes": size, "sha256": digest}
    connection, identity = ss_config.connect_analyst(paths=paths)
    provenance_rows = connection.execute(
        "SELECT table_name, source_file, manifest_sha256, observed_sha256, "
        "source_rows, loaded_rows FROM source.provenance ORDER BY table_name"
    ).fetchall()
    connection.close()
    provenance = [
        {
            "table_name": row[0],
            "source_file": row[1],
            "manifest_sha256": row[2],
            "observed_sha256": row[3],
            "source_rows": int(row[4]),
            "loaded_rows": int(row[5]),
        }
        for row in provenance_rows
    ]
    if len(provenance) != 12:
        raise SystemExit(f"pins FAILED: expected 12 provenance rows, got {len(provenance)}")
    for row in provenance:
        if row["manifest_sha256"] != row["observed_sha256"]:
            raise SystemExit(
                f"pins FAILED: provenance row {row['table_name']} hash disagreement"
            )
        key = Path(row["source_file"])
        if row["table_name"] == "specz_compilation_unique":
            if key.name != Path(repo_config["specz"]["unique_fits"]).name:
                raise SystemExit("pins FAILED: unique provenance path drift")
        if row["table_name"] == "specz_compilation_all":
            if key.name != Path(repo_config["specz"]["all_fits"]).name:
                raise SystemExit("pins FAILED: all provenance path drift")
            declared = artifacts["all_fits"]["manifest_sha256"]
            if row["manifest_sha256"] != declared:
                raise SystemExit("pins FAILED: provenance/manifest all-FITS disagreement")
    return {
        "recorded_at": _utc_now(),
        "analyst_identity": {
            "database": identity.database,
            "user": identity.user,
        },
        "artifacts": artifacts,
        "definitions": definitions,
        "provenance_rows": provenance,
    }


def capture_before_state(paths: ss_config.SpeczSciencePaths) -> dict[str, object]:
    """Record source relation state and seeded content identities (analyst)."""
    connection, identity = ss_config.connect_analyst(paths=paths)
    state: dict[str, object] = {
        "recorded_at": _utc_now(),
        "connection": {
            "database": identity.database,
            "user": identity.user,
            "mode": "analyst_read_only",
        },
        "relations": {},
    }
    for table in (*SOURCE_TABLES, "provenance"):
        columns = [
            {"name": row[0], "type": row[1], "nullable": row[2]}
            for row in connection.execute(
                "SELECT a.attname, format_type(a.atttypid, a.atttypmod), "
                "NOT a.attnotnull FROM pg_attribute a "
                "JOIN pg_class c ON c.oid = a.attrelid "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'source' AND c.relname = %s "
                "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum",
                (table,),
            ).fetchall()
        ]
        constraints = [
            {"name": row[0], "definition": row[1]}
            for row in connection.execute(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = %s::regclass ORDER BY conname",
                (f'source."{table}"',),
            ).fetchall()
        ]
        comment = connection.execute(
            "SELECT obj_description(%s::regclass, 'pg_class')",
            (f'source."{table}"',),
        ).fetchone()[0]
        digest_row = connection.execute(
            sql.SQL(
                "SELECT count(*), md5(coalesce(string_agg(md5(s.txt), '' "
                "ORDER BY s.rn), '')) FROM (SELECT t::text AS txt, "
                "row_number() OVER (ORDER BY t.ctid) AS rn FROM source.{table} t) s "
                "WHERE s.rn %% %(modulus)s = %(offset)s"
            ).format(table=sql.Identifier(table)),
            {"modulus": DIGEST_MODULUS, "offset": DIGEST_OFFSET},
        ).fetchone()
        state["relations"][table] = {
            "columns": columns,
            "column_count": len(columns),
            "constraints": constraints,
            "comment": comment,
            "rows": None,
            "sampled_digest_rows": int(digest_row[0]),
            "seeded_content_digest": digest_row[1],
            "seed_modulus": DIGEST_MODULUS,
            "seed_offset": DIGEST_OFFSET,
        }
    counts = {
        table: connection.execute(
            sql.SQL("SELECT count(*) FROM source.{}").format(sql.Identifier(table))
        ).fetchone()[0]
        for table in (*SOURCE_TABLES, "provenance")
    }
    for table, entry in state["relations"].items():
        entry["rows"] = counts[table]
    connection.close()
    return state


def capture_v1_identity() -> dict[str, object]:
    """Capture protected v1 identity through the admin transport, read-only."""
    from src.etl import bootstrap_v11

    settings = bootstrap_v11.resolve_settings(bootstrap_v11.DEFAULT_CONFIG_PATH)
    fingerprint = bootstrap_v11.capture_v1_fingerprint(settings)
    return {
        "recorded_at": _utc_now(),
        "database": settings.baseline_database,
        "mode": "admin_transport_enforced_read_only_transaction",
        "fingerprint_sha256": fingerprint.sha256,
        "fingerprint_bytes": len(fingerprint.content),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analyst", action="store_true", help="verify direct analyst access"
    )
    parser.add_argument(
        "--pins", action="store_true", help="compare consumed-input pins"
    )
    parser.add_argument(
        "--before-state", action="store_true", help="capture source before-state"
    )
    parser.add_argument(
        "--v1-identity", action="store_true", help="capture protected v1 identity (admin)"
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    selected = [
        name
        for name in ("analyst", "pins", "before_state", "v1_identity")
        if getattr(args, name)
    ]
    if not selected:
        raise SystemExit("select at least one of --analyst/--pins/--before-state/--v1-identity")
    paths = ss_config.resolve_paths()
    evidence: dict[str, object] = {"preflight": selected}
    if "analyst" in selected:
        evidence["analyst_access"] = verify_analyst_access(paths)
    if "pins" in selected:
        evidence["input_pins"] = verify_input_pins(paths)
    if "before_state" in selected:
        evidence["source_before_state"] = capture_before_state(paths)
    if "v1_identity" in selected:
        evidence["v1_identity"] = capture_v1_identity()
    output = args.output if args.output is not None else (
        paths.staging_dir / "preflight-5-1.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"written": str(output), "preflight": selected}, indent=2))


if __name__ == "__main__":
    main()
