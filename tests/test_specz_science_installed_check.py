#!/usr/bin/env python3
"""
Script Name  : test_specz_science_installed_check.py
Description  : Test pre-seal and post-seal verification without database writes.
Repository   : cosmos2025-anomalies
Author       : Codex (https://github.com/openai/codex)
Created      : 2026-10-04
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Synthetic metadata isolates seal, content and implementation identity failures.
A recording connection proves the verifier issues only SELECT statements.

Usage / Examples
----------------
    python -m pytest tests/test_specz_science_installed_check.py
        Run all verifier contract checks in memory.
"""

from copy import deepcopy

import pytest

from src.features.specz_science import canonical, install, splits
from src.features.specz_science import check_installed_product as check


# Nine unmodified seal records from run 1e604a81, sealed 2026-09-22.
SEALED_VERIFIED_CHECKS = [
    {
        "check": "python src/features/specz_science/check_installed_product.py",
        "result": (
            "OK: analyst identity and read-only, SELECT on four tables, no write "
            "privileges, source counts unchanged, installed content digests equal staging "
            "artifacts"
        ),
    },
    {
        "check": "python src/features/specz_science/check_installed_independent.py",
        "result": (
            "OK: 784,016 source rows and 482,579 measurement rows reproduced from the "
            "captured native input (preferred, conflicts, association, secure, splits, "
            "eligibility, reasons)"
        ),
    },
    {
        "check": (
            "doppler run --project ml01 --config dev -- python "
            "src/features/specz_science/negative_controls.py"
        ),
        "result": (
            "OK: six tampers each caught on the intended invariant (remove category, alter "
            "association, promote A entry, erase secure conflict, change tied preferred, "
            "move split)"
        ),
    },
    {
        "check": "python src/features/specz_science/check_splits_agreement.py",
        "result": (
            "OK: independent tile-map recomputation and all 784,016 assignments agree; zero"
            " unassigned"
        ),
    },
    {
        "check": (
            "python -m pytest tests/ -q (under doppler run --project ml01 --config dev)"
        ),
        "result": (
            "563 passed in 2156.87 s, including dictionary byte-identity and full-manifest "
            "checks, scratch database tests, and all P2R-05 suites"
        ),
    },
    {
        "check": "python src/etl/generate_schema_v11.py --check (under doppler)",
        "result": (
            "byte-identical: 12 mirrors, 1448 mirror columns, 166 array checks, 13 "
            "provenance columns"
        ),
    },
    {
        "check": "python src/etl/verify_conformance_v11.py --live (under doppler)",
        "result": (
            "conformance passed; analyst capability matrix 78 denials / 13 selects; v1 "
            "fingerprint 82fb7e09... unchanged (v1_unchanged true)"
        ),
    },
    {
        "check": (
            "python src/features/specz_science/preflight.py --before-state / --pins (5.7 "
            "rerun)"
        ),
        "result": (
            "13 source relations identical to the 5.1 capture including seeded content "
            "digests; manifest/provenance pins agree with freshly observed hashes; policy, "
            "dictionary, data_paths, spec, dispositions bytes unchanged since 5.1"
        ),
    },
    {
        "check": "repeat install request",
        "result": (
            "installed=false, unchanged=true: no rows, timestamps, grants, or "
            "adoption-state changes"
        ),
    },
]


@pytest.fixture
def contract():
    implementation = {
        "modules": {name: "1" * 64 for name in canonical.IMPLEMENTATION_MODULE_NAMES},
        "python_version": "test", "psycopg_version": "test", "platform": "test",
    }
    run = {
        "policy_id": "p2r05-specz-policy-v1", "spec_sha256": "a" * 64,
        "policy_semantic_digest": "b" * 64, "snapshot_manifest_digest": "c" * 64,
        "snapshot_file_digests": {"native": "d" * 64},
        "implementation": deepcopy(implementation),
        "product_state": "pending_scientific_adoption",
        "tile_map": {"A1": "development"},
        "tile_map_canonical_digest": splits.canonical_tile_map_digest({"A1": "development"}),
        "mechanical_seal_at": "2026-09-22T10:21:25+00:00",
    }
    run_id = canonical.run_id_from_identity(canonical.build_run_identity(
        policy_digest=run["policy_semantic_digest"],
        snapshot_manifest_digest=run["snapshot_manifest_digest"],
        snapshot_file_digests=run["snapshot_file_digests"], implementation=implementation,
    ))
    run["run_id"] = run_id
    digests, recorded, sealed = {}, {}, {}
    for table, name, digest in (
        (install.MEASUREMENTS, "measurements", "e" * 64),
        (install.SOURCES, "sources", "f" * 64),
        (install.SPLITS, "splits", "0" * 64),
    ):
        digests[table] = digest
        recorded[f"{name}_content_sha256"] = digest
        run[f"{name}_content_sha256"] = digest
        sealed[name] = digest
    run["mechanical_seal_evidence"] = {
        "content_digests": sealed,
        "identities": {
            "run_id": run_id, "policy": run["policy_id"],
            "approved_spec_sha256": run["spec_sha256"],
            "snapshot_manifest_sha256": run["snapshot_manifest_digest"],
            "tile_map_canonical_digest": run["tile_map_canonical_digest"],
        },
        "verified_checks": deepcopy(SEALED_VERIFIED_CHECKS),
    }
    return dict(run=run, run_id=run_id, implementation=implementation,
                installed_digests=digests, staging_digests=recorded)


def failures(contract, mode="post-seal"):
    return check.check_run_contract(mode=mode, **contract)


def unseal(contract):
    contract["run"]["mechanical_seal_at"] = None
    contract["run"]["mechanical_seal_evidence"] = None


def test_post_seal_accepts_sealed_metadata_without_staging(contract):
    contract["staging_digests"] = None
    assert failures(contract) == []


def test_pre_seal_accepts_unsealed_staging_contract(contract):
    unseal(contract)
    assert failures(contract, "pre-seal") == []


@pytest.mark.parametrize("mode", ["pre-seal", "post-seal"])
def test_modes_reject_opposite_seal_state(contract, mode):
    if mode == "post-seal":
        unseal(contract)
    assert failures(contract, mode)


def test_pre_seal_requires_staging_digests(contract):
    unseal(contract)
    contract["staging_digests"] = None
    assert failures(contract, "pre-seal")


def test_post_seal_ignores_mutable_staging_digest_oracle(contract):
    contract["staging_digests"]["sources_content_sha256"] = "changed staging"
    assert failures(contract) == []


@pytest.mark.parametrize("mode", ["pre-seal", "post-seal"])
def test_both_modes_reject_changed_installed_content(contract, mode):
    if mode == "pre-seal":
        unseal(contract)
    contract["installed_digests"][install.SOURCES] = "wrong"
    assert failures(contract, mode)


@pytest.mark.parametrize("field", ["run_id", "policy", "approved_spec_sha256",
                                    "snapshot_manifest_sha256", "tile_map_canonical_digest"])
def test_post_seal_rejects_each_seal_identity_mismatch(contract, field):
    contract["run"]["mechanical_seal_evidence"]["identities"][field] = "wrong"
    assert failures(contract)


@pytest.mark.parametrize("name", ["measurements", "sources", "splits"])
def test_post_seal_rejects_each_seal_content_mismatch(contract, name):
    contract["run"]["mechanical_seal_evidence"]["content_digests"][name] = "wrong"
    assert failures(contract)


@pytest.mark.parametrize("mutation", ["missing_run", "missing_seal", "empty_seal",
                                      "seal_time", "checks", "state", "module", "tile",
                                      "input", "requested_run", "run_digest"])
def test_post_seal_fails_closed_on_drift(contract, mutation):
    run = contract["run"]
    if mutation == "missing_run":
        contract["run"] = None
    elif mutation == "missing_seal":
        run["mechanical_seal_evidence"] = None
    elif mutation == "empty_seal":
        run["mechanical_seal_evidence"] = {}
    elif mutation == "seal_time":
        run["mechanical_seal_at"] = "not a timestamp"
    elif mutation == "checks":
        run["mechanical_seal_evidence"]["verified_checks"] = []
    elif mutation == "state":
        run["product_state"] = "adopted"
    elif mutation == "module":
        contract["implementation"]["modules"]["build"] = "changed"
    elif mutation == "tile":
        run["tile_map"]["A1"] = "holdout"
    elif mutation == "input":
        run["snapshot_file_digests"]["native"] = "changed"
    elif mutation == "requested_run":
        contract["run_id"] = "wrong"
    elif mutation == "run_digest":
        run["sources_content_sha256"] = "wrong"
    assert failures(contract)


class SelectOnlyConnection:
    """Record every statement and reject a non-SELECT before it could run."""

    def __init__(self, run):
        self.run = run
        self.queries = []
        self.closed = False

    def execute(self, query, parameters=None):
        from types import SimpleNamespace

        assert query.lstrip().upper().startswith("SELECT ")
        self.queries.append((query, parameters))
        if "to_jsonb" in query:
            result = (self.run,) if self.run is not None else None
        elif "current_database" in query:
            result = ("cosmos2025_v11",)
        elif "session_user" in query:
            result = ("cosmos2025_v11_ro", "cosmos2025_v11_ro")
        elif "current_setting" in query:
            result = ("on", "on")
        elif "has_schema_privilege" in query:
            result = (False,)
        elif "source.photometry_primary', 'UPDATE'" in query:
            result = (False, False)
        elif "has_table_privilege" in query:
            result = ("'SELECT'" in query,)
        elif "count(*)" in query:
            result = (784016, 482579, 12)
        else:
            raise AssertionError(f"unexpected query: {query}")
        return SimpleNamespace(fetchone=lambda: result)

    def close(self):
        self.closed = True


@pytest.mark.parametrize("mode", ["pre-seal", "post-seal"])
def test_verifier_issues_only_select_and_checks_all_products(contract, monkeypatch, mode):
    if mode == "pre-seal":
        unseal(contract)
    connection = SelectOnlyConnection(contract["run"])
    scanned = []

    def digest(conn, table, run_id, order):
        assert conn is connection and run_id == contract["run_id"]
        scanned.append(table)
        return contract["installed_digests"][table]

    monkeypatch.setattr(check.ssi, "installed_content_digest", digest)
    report = check.verify_product(
        connection, run_id=contract["run_id"], mode=mode,
        implementation=contract["implementation"], staging_digests=contract["staging_digests"],
    )
    assert report["status"] == "OK"
    assert set(scanned) == set(check.ORDER_BY)
    assert len(connection.queries) == 28


def test_missing_run_reports_failure_without_scanning_tables(contract, monkeypatch):
    def unexpected(*args):
        raise AssertionError("must not scan product tables for an absent run")

    monkeypatch.setattr(check.ssi, "installed_content_digest", unexpected)
    report = check.verify_product(SelectOnlyConnection(None), run_id=contract["run_id"],
                                  mode="post-seal", implementation=contract["implementation"])
    assert report["status"] == "FAILED"
    assert report["failures"] == [f"run not found: {contract['run_id']}"]


def test_post_seal_cli_never_reads_finalize_summary(contract, monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace

    connection = SelectOnlyConnection(contract["run"])
    monkeypatch.setattr(check.ss_config, "resolve_paths", lambda: SimpleNamespace())
    monkeypatch.setattr(check.ss_config, "connect_analyst", lambda **kwargs: (connection, None))
    monkeypatch.setattr(check.canonical, "implementation_digest", lambda _: contract["implementation"])
    monkeypatch.setattr(check.ssi, "installed_content_digest",
                        lambda conn, table, run_id, order: contract["installed_digests"][table])

    def forbidden_read(*args, **kwargs):
        raise AssertionError("post-seal CLI must not read the finalize summary")

    monkeypatch.setattr(Path, "read_text", forbidden_read)
    check.main(["--mode", "post-seal", "--run-id", contract["run_id"]])
    assert connection.closed


def test_pre_seal_rejects_staging_digest_mismatch(contract):
    unseal(contract)
    contract["staging_digests"]["sources_content_sha256"] = "wrong"
    assert any("staging artifact" in failure for failure in failures(contract, "pre-seal"))


def test_post_seal_cli_requires_explicit_run_id():
    with pytest.raises(SystemExit) as caught:
        check.main(["--mode", "post-seal"])
    assert caught.value.code == 2


@pytest.mark.parametrize("result", [
    "FAILED: installed digest mismatch",
    "failure: incomplete native verification",
    "ERROR: read failed",
    "not OK: changed tile assignment",
    "OK: checks started; one check failed",
])
def test_post_seal_rejects_failed_recorded_check(contract, result):
    contract["run"]["mechanical_seal_evidence"]["verified_checks"][0]["result"] = result
    assert any("indicates failure" in failure for failure in failures(contract))


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "renamed"])
def test_post_seal_rejects_changed_recorded_check_set(contract, mutation):
    checks = contract["run"]["mechanical_seal_evidence"]["verified_checks"]
    if mutation == "missing":
        checks.pop()
    elif mutation == "extra":
        checks.append({"check": "unexpected check", "result": "completed"})
    elif mutation == "duplicate":
        checks[-1] = deepcopy(checks[0])
    else:
        checks[-1]["check"] = "renamed check"
    assert failures(contract)


def test_post_seal_accepts_all_nine_original_free_text_results(contract):
    checks = contract["run"]["mechanical_seal_evidence"]["verified_checks"]
    assert len(checks) == 9
    assert sum(not item["result"].startswith("OK") for item in checks) == 5
    assert failures(contract) == []


def test_post_seal_pin_is_independent_of_check_order(contract):
    contract["run"]["mechanical_seal_evidence"]["verified_checks"].reverse()
    assert failures(contract) == []


def test_post_seal_rejects_unrecognized_result_text(contract):
    checks = contract["run"]["mechanical_seal_evidence"]["verified_checks"]
    checks[0]["result"] = "native verification never completed"
    assert failures(contract)


@pytest.mark.parametrize("item", [
    {"check": "name", "result": "   "},
    {"check": "name", "result": True},
    {"check": ["name"], "result": "OK"},
    {"check": "name"},
])
def test_post_seal_rejects_malformed_recorded_check(contract, item):
    contract["run"]["mechanical_seal_evidence"]["verified_checks"][0] = item
    assert failures(contract)
