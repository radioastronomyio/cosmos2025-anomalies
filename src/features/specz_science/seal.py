"""Declare the gate 5.7 mechanical seal on the installed run record.

Writes ``mechanical_seal_at`` and the evidence document into the run row
through the bounded admin transport. The seal is mechanical only: it
records what was verified, with which commands, at what cost, and under
which identities. It asserts no scientific adoption — ``product_state``
stays ``pending_scientific_adoption`` — and contains no commit hash of any
file or commit carrying this record.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import install as ssi  # noqa: E402

RUN_ID = "1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c"

SEAL_EVIDENCE = {
    "verified_checks": [
        {
            "check": "python src/features/specz_science/check_installed_product.py",
            "result": "OK: analyst identity and read-only, SELECT on four tables, no write privileges, source counts unchanged, installed content digests equal staging artifacts",
        },
        {
            "check": "python src/features/specz_science/check_installed_independent.py",
            "result": "OK: 784,016 source rows and 482,579 measurement rows reproduced from the captured native input (preferred, conflicts, association, secure, splits, eligibility, reasons)",
        },
        {
            "check": "doppler run --project ml01 --config dev -- python src/features/specz_science/negative_controls.py",
            "result": "OK: six tampers each caught on the intended invariant (remove category, alter association, promote A entry, erase secure conflict, change tied preferred, move split)",
        },
        {
            "check": "python src/features/specz_science/check_splits_agreement.py",
            "result": "OK: independent tile-map recomputation and all 784,016 assignments agree; zero unassigned",
        },
        {
            "check": "python -m pytest tests/ -q (under doppler run --project ml01 --config dev)",
            "result": "563 passed in 2156.87 s, including dictionary byte-identity and full-manifest checks, scratch database tests, and all P2R-05 suites",
        },
        {
            "check": "python src/etl/generate_schema_v11.py --check (under doppler)",
            "result": "byte-identical: 12 mirrors, 1448 mirror columns, 166 array checks, 13 provenance columns",
        },
        {
            "check": "python src/etl/verify_conformance_v11.py --live (under doppler)",
            "result": "conformance passed; analyst capability matrix 78 denials / 13 selects; v1 fingerprint 82fb7e09... unchanged (v1_unchanged true)",
        },
        {
            "check": "python src/features/specz_science/preflight.py --before-state / --pins (5.7 rerun)",
            "result": "13 source relations identical to the 5.1 capture including seeded content digests; manifest/provenance pins agree with freshly observed hashes; policy, dictionary, data_paths, spec, dispositions bytes unchanged since 5.1",
        },
        {
            "check": "repeat install request",
            "result": "installed=false, unchanged=true: no rows, timestamps, grants, or adoption-state changes",
        },
    ],
    "identities": {
        "run_id": RUN_ID,
        "policy": "p2r05-specz-policy-v1",
        "approved_spec_sha256": "7f481111ad826dd80b01106eeec71bfdaf0f5c649c0cc79b8661a0087af2757b",
        "snapshot_manifest_sha256": "06b19654fc715106ba1f788b52e084df1e94043343517f2b8a49fd44abfff7a4",
        "tile_map_canonical_digest": "c6406d37e32e4b5cfeb89fc91cda0eb9ed4abf0a192d8c5ab7e56fb893635937",
    },
    "content_digests": {
        "measurements": "f1448edf939aeaa7d99f49a9b730c4eba5d6f4e9ded6230bbfdbf8705d416415",
        "sources": "5e4134af9d8e903179f6f56c24b401ce356a5824afcf292e22428dbfb22c8771",
        "splits": "945312724483046fe359b77bffb95f98a0ba1818519685bb0f96264bedffc725",
    },
    "runtime": {
        "build_finalize_wall_seconds": 54,
        "build_peak_rss_kbytes": 2448884,
        "install_wall_seconds": 44,
        "installed_verification_wall_seconds": 41,
        "full_suite_wall_seconds": 2157,
        "negative_controls_wall_seconds": 453,
    },
    "recovery_history": [
        {
            "event": "destructive rebuild 1 of the allowed budget of 2 (unsealed candidate)",
            "reason": "implementation-identity defect: the run identity hashed diagnostic modules (verify.py, coverage.py), so a gate 5.7 diagnostics edit moved the run id of already-built products; corrected to build-affecting modules only per the product contract",
            "discarded_validated_scope": "run 2bb71fb075cb5bd72a8f28908765bc8e0484c59f212a9e74ed26dbc06b333ae5, whose content was byte-identical to the resealed run after the embedded run-id field",
            "action": "down() of the superseded run (rows and newly created objects only), reinstall under the corrected identity, full re-verification",
        }
    ],
    "adoption": "mechanical seal only; product_state remains pending_scientific_adoption; S5-Q01..S5-Q05 unanswered",
}


def main() -> None:
    paths = ss_config.resolve_paths()
    finalize = json.loads(
        (paths.staging_dir / "products" / "finalize-summary.json").read_text(encoding="utf-8")
    )
    if finalize["run_id"] != RUN_ID:
        raise SystemExit(
            f"seal FAILED: staging run {finalize['run_id']} is not the verified run {RUN_ID}"
        )
    from src.etl import bootstrap_v11

    settings = bootstrap_v11.resolve_settings(bootstrap_v11.DEFAULT_CONFIG_PATH)
    with bootstrap_v11._connect(settings, settings.target_database) as connection:
        state = connection.execute(
            "SELECT product_state, mechanical_seal_at FROM analysis.specz_p2r05_runs "
            "WHERE run_id = %s",
            (RUN_ID,),
        ).fetchone()
        if state is None:
            raise SystemExit("seal FAILED: run row missing")
        if state[1] is not None:
            raise SystemExit(f"seal FAILED: already sealed at {state[1]}")
        sealed_at = datetime.now(timezone.utc).isoformat()
        connection.execute(
            "UPDATE analysis.specz_p2r05_runs SET mechanical_seal_at = %s, "
            "mechanical_seal_evidence = %s WHERE run_id = %s",
            (sealed_at, json.dumps(SEAL_EVIDENCE, sort_keys=True), RUN_ID),
        )
        after = connection.execute(
            "SELECT product_state, mechanical_seal_at FROM analysis.specz_p2r05_runs "
            "WHERE run_id = %s",
            (RUN_ID,),
        ).fetchone()
        connection.commit()
    if after[0] != "pending_scientific_adoption" or after[1] != sealed_at:
        raise SystemExit(f"seal FAILED: post-state {after}")
    evidence_path = paths.staging_dir / "mechanical-seal-5-7.json"
    evidence_path.write_text(
        json.dumps({"sealed_at": sealed_at, "evidence": SEAL_EVIDENCE}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"sealed_at": sealed_at, "product_state": after[0]}, indent=2))


if __name__ == "__main__":
    main()
