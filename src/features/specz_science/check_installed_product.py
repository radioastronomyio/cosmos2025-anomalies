#!/usr/bin/env python3
"""
Script Name  : check_installed_product.py
Description  : Verify pre-seal or post-seal P2R-05 installed product identity.
Repository   : cosmos2025-anomalies
Author       : Codex (https://github.com/openai/codex)
Created      : 2026-09-22
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Use the connection-time read-only analyst contract and SELECT statements only.
Pre-seal compares an unsealed candidate to finalize-summary artifact digests.
Post-seal checks the recorded seal and recomputes installed content against
sealed metadata, without depending on the mutable staging summary. Run identity
uses freshly hashed implementation bytes and recorded native input identities;
this verifier does not rehash the raw inputs or repeat scientific verification.

Usage / Examples
----------------
    python check_installed_product.py --mode pre-seal
        Check an installed candidate before mechanical sealing.
    python check_installed_product.py --mode post-seal --run-id RUN_ID
        Check the sealed run, read-only, printing JSON to standard output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import canonical  # noqa: E402
from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import install as ssi  # noqa: E402
from src.features.specz_science import splits  # noqa: E402

ORDER_BY = {
    ssi.MEASUREMENTS: "run_id, id_specz",
    ssi.SOURCES: "run_id, catalog_id",
    ssi.SPLITS: "run_id, catalog_id",
}
DIGEST_NAMES = {
    ssi.MEASUREMENTS: "measurements",
    ssi.SOURCES: "sources",
    ssi.SPLITS: "splits",
}


# The nine historical check/result records for run 1e604a81, sealed 2026-09-22.
# Pin complete free-text results, sorted by check name and canonically encoded.
# These are evidence labels, not commands to rerun; unknown wording fails closed.
SEALED_VERIFIED_CHECKS_SHA256 = (
    "5a8c39f8b128ec3c9812630526ca34a08bedb22a2d33f3191350bc18f25c20a4"
)
SEAL_FAILURE_MARKERS = re.compile(
    r"\b(?:fail(?:ed|ure|ures|ing|s)?|errors?|exceptions?|traceback|not[\s_-]+ok)\b",
    re.IGNORECASE,
)


def check_run_contract(
    *, run: Mapping[str, Any] | None, run_id: str, mode: str,
    implementation: Mapping[str, Any], installed_digests: Mapping[str, str],
    staging_digests: Mapping[str, str] | None = None,
) -> list[str]:
    """Check identity and the mode-specific digest oracle without side effects."""
    if mode not in ("pre-seal", "post-seal"):
        raise ValueError(f"unknown verification mode: {mode}")
    if run is None:
        return [f"run not found: {run_id}"]
    failures: list[str] = []
    try:
        if run["run_id"] != run_id:
            failures.append("requested run identity differs from run metadata")
        if run["product_state"] != "pending_scientific_adoption":
            failures.append("product is not pending scientific adoption")
        if set(implementation["modules"]) != set(canonical.IMPLEMENTATION_MODULE_NAMES):
            failures.append("build-affecting implementation module set differs")
        if implementation != run["implementation"]:
            failures.append("current implementation differs from recorded implementation")
        identity = canonical.build_run_identity(
            policy_digest=run["policy_semantic_digest"],
            snapshot_manifest_digest=run["snapshot_manifest_digest"],
            snapshot_file_digests=run["snapshot_file_digests"],
            implementation=implementation,
        )
        if canonical.run_id_from_identity(identity) != run_id:
            failures.append("recomputed run identity differs from requested run")
        if splits.canonical_tile_map_digest(run["tile_map"]) != run["tile_map_canonical_digest"]:
            failures.append("tile map differs from its recorded digest")

        seal = run["mechanical_seal_evidence"]
        if mode == "pre-seal":
            if run["mechanical_seal_at"] is not None or seal is not None:
                failures.append("pre-seal mode requires an unsealed run")
            if staging_digests is None:
                failures.append("pre-seal mode requires staging artifact digests")
        else:
            # A timestamp alone is not a seal: identity and content evidence
            # must agree with the run and freshly observed installed rows.
            if not run["mechanical_seal_at"]:
                failures.append("post-seal mode requires a mechanical seal timestamp")
            else:
                timestamp = datetime.fromisoformat(run["mechanical_seal_at"])
                if timestamp.tzinfo is None:
                    failures.append("mechanical seal timestamp lacks a timezone")
            if not isinstance(seal, dict) or not seal:
                failures.append("post-seal mode requires recorded seal evidence")
                seal = {}
            expected_identities = {
                "run_id": run_id,
                "policy": run["policy_id"],
                "approved_spec_sha256": run["spec_sha256"],
                "snapshot_manifest_sha256": run["snapshot_manifest_digest"],
                "tile_map_canonical_digest": run["tile_map_canonical_digest"],
            }
            if seal.get("identities") != expected_identities:
                failures.append("seal identities differ from run metadata")
            checks = seal.get("verified_checks")
            if not isinstance(checks, list) or not checks or not all(
                isinstance(item, dict)
                and isinstance(item.get("check"), str) and item["check"].strip()
                and isinstance(item.get("result"), str) and item["result"].strip()
                for item in checks
            ):
                failures.append("seal lacks valid recorded verification evidence")
            else:
                checks_digest = canonical.digest_records(
                    sorted(checks, key=lambda item: item["check"])
                )
                if checks_digest != SEALED_VERIFIED_CHECKS_SHA256:
                    failures.append("seal verification records differ from the pinned nine checks")
                for item in checks:
                    if SEAL_FAILURE_MARKERS.search(item["result"]):
                        failures.append(f"seal recorded check indicates failure: {item['check']}")

        for table, name in DIGEST_NAMES.items():
            field = f"{name}_content_sha256"
            installed = installed_digests[table]
            if installed != run[field]:
                failures.append(f"{table}: installed digest differs from run metadata")
            if mode == "pre-seal":
                if staging_digests is not None and installed != staging_digests[field]:
                    failures.append(f"{table}: installed digest differs from staging artifact")
            elif installed != seal.get("content_digests", {}).get(name):
                failures.append(f"{table}: installed digest differs from mechanical seal")
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        failures.append(f"invalid or incomplete run/seal metadata: {error}")
    return failures


def verify_product(
    connection, *, run_id: str, mode: str, implementation: Mapping[str, Any],
    staging_digests: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Run the SELECT-only capability, source-count and full content checks."""
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

    row = connection.execute(
        "SELECT to_jsonb(r) FROM analysis.specz_p2r05_runs r WHERE run_id = %s",
        (run_id,),
    ).fetchone()
    run = row[0] if row else None
    digests = {
        table: ssi.installed_content_digest(connection, table, run_id, order)
        for table, order in ORDER_BY.items()
    } if run is not None else {}
    failures.extend(check_run_contract(
        run=run, run_id=run_id, mode=mode, implementation=implementation,
        installed_digests=digests, staging_digests=staging_digests,
    ))
    return {
        "status": "FAILED" if failures else "OK", "failures": failures,
        "mode": mode, "run_id": run_id,
        "analyst_identity": {"database": database, "user": principal[0]},
        "read_only": list(ro), "installed_content_digests": digests,
        "digest_reference": "mechanical_seal_evidence" if mode == "post-seal" else "staging_artifacts",
        "product_state": run.get("product_state") if run else None,
        "mechanical_seal_at": run.get("mechanical_seal_at") if run else None,
    }


def main(argv: list[str] | None = None) -> None:
    """Select an explicit verification contract; never change a product."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("pre-seal", "post-seal"), default="pre-seal",
                        help="default preserves the original pre-seal invocation")
    parser.add_argument("--run-id", help="required for post-seal; optional pre-seal identity assertion")
    args = parser.parse_args(argv)
    if args.mode == "post-seal" and not args.run_id:
        parser.error("--run-id is required for post-seal verification")
    paths = ss_config.resolve_paths()
    staging_digests = None
    run_id = args.run_id
    if args.mode == "pre-seal":
        finalize = json.loads(
            (paths.staging_dir / "products" / "finalize-summary.json").read_text(encoding="utf-8")
        )
        if run_id is not None and run_id != finalize["run_id"]:
            parser.error("--run-id differs from the pre-seal finalize summary")
        run_id = finalize["run_id"]
        staging_digests = finalize["content_digests"]
    implementation = canonical.implementation_digest(Path(__file__).resolve().parent)
    connection, _ = ss_config.connect_analyst(paths=paths)
    try:
        report = verify_product(connection, run_id=run_id, mode=args.mode,
                                implementation=implementation, staging_digests=staging_digests)
    finally:
        connection.close()
    print(json.dumps(report, indent=2))
    if report["status"] != "OK":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
