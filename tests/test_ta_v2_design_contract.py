#!/usr/bin/env python3
"""
Script Name  : test_ta_v2_design_contract.py
Description  : Synthetic-only contract tests for the proposed T_A v2 design validator
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-10-05
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Proves the P2R-06 gate 6.3 contract for src/inspection/validate_ta_v2_design.py:
the validator exits 0 on the complete proposed contract with every synthetic
fixture within tolerance, exits nonzero with the intended named reason on
each declared scratch-copy mutation, records stable case IDs with
expected/observed behaviour and hashes, and has no database connection, no
installer import, and no catalog feature-generation mode. Nothing here is
astrophysical validation, measured calibration, a power estimate, or a
real-data ranking; every fixture is labelled synthetic.

Usage
-----
    pytest tests/test_ta_v2_design_contract.py -v

Examples
--------
    pytest tests/test_ta_v2_design_contract.py -v
        Run the full gate 6.3 suite against the tracked contract, fixtures,
        and identity record.
"""

# =============================================================================
# Imports
# =============================================================================

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "src" / "inspection" / "validate_ta_v2_design.py"
DESIGN_DIR = REPO_ROOT / "docs" / "research" / "ta-v2-design"
CONTRACT = DESIGN_DIR / "feature-contract.yaml"
FIXTURES = DESIGN_DIR / "fixtures.json"
IDENTITY = DESIGN_DIR / "input-identity.json"
RESULTS = DESIGN_DIR / "validation-results.json"

MUTATIONS = [
    "M1_swap_representation",
    "M2_drop_censoring_state",
    "M3_allow_heldout_fit",
    "M4_chi2_quotient",
    "M5_identity_digest_change",
    "M6_hidden_shift",
    "M7_reverse_definition",
    "M8_forbidden_covariate",
    "M9_specz_covariate",
]


def run_validator(*args, tmp_path=None):
    """Run the validator as a subprocess and return the CompletedProcess."""
    cmd = [sys.executable, str(VALIDATOR)]
    if tmp_path is not None:
        cmd += ["--results", str(tmp_path / "results.json")]
    cmd += list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


@pytest.fixture(scope="module")
def clean_run(tmp_path_factory):
    """One clean validator run shared by the read-only assertions."""
    out = tmp_path_factory.mktemp("clean")
    proc = run_validator(tmp_path=out)
    return proc, out / "results.json"


@pytest.fixture(scope="module")
def results(clean_run):
    """Parsed validation-results.json from the clean run."""
    proc, results_path = clean_run
    assert proc.returncode == 0, f"clean run failed:\n{proc.stdout}\n{proc.stderr}"
    return json.loads(results_path.read_text())


class TestCleanContract:
    """The validator accepts the complete proposed contract."""

    def test_exits_zero(self, clean_run):
        proc, _ = clean_run
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_all_cases_pass(self, results):
        cases = results["cases"]
        assert cases, "no cases recorded"
        failed = [c for c in cases if not c["pass"]]
        assert not failed, failed

    def test_fit_request_controls_present(self, results):
        fit = results["fit_requests"]
        assert {f["id"] for f in fit} >= {"FX-P1", "FX-P2", "FX-P3", "FX-P4"}
        assert all(f["pass"] for f in fit)

    def test_stable_case_ids(self, results):
        ids = [c["id"] for c in results["cases"]]
        assert len(ids) == len(set(ids))
        assert all(i.startswith("FX-") for i in ids)

    def test_expected_and_observed_recorded(self, results):
        for case in results["cases"]:
            assert "expected" in case and "observed" in case

    def test_hashes_and_command_recorded(self, results):
        for key in ("contract_sha256", "fixtures_sha256", "identity_sha256"):
            assert len(results[key]) == 64
        assert "command" in results and "exit_code" in results

    def test_required_discriminators_covered(self, results):
        ids = {c["id"] for c in results["cases"]}
        for required in [
            "FX-01a",  # log-vs-linear unit and sign
            "FX-01c",  # equal physical masses
            "FX-02a", "FX-02b",  # cell-dependent residual, unchanged raw
            "FX-02c1", "FX-02c2",  # bias centers, isolated deviation survives
            "FX-03a", "FX-03b", "FX-03c", "FX-03d",  # four SFR paths
            "FX-04a", "FX-04b", "FX-04c", "FX-04d",  # mass/SFR independence
        ]:
            assert required in ids, required

    def test_synthetic_labelling(self, results):
        assert results["fixtures_provenance"] == "synthetic"
        blob = json.dumps(results).lower()
        for banned in ("astrophysical validation", "measured calibration", "power estimate", "real-data ranking"):
            assert banned not in blob, banned


class TestMutationControls:
    """Each named scratch-copy mutation fails its intended invariant."""

    @pytest.mark.parametrize("name", MUTATIONS)
    def test_mutation_fails_with_intended_reason(self, name, tmp_path):
        proc = run_validator("--mutation", name, tmp_path=tmp_path)
        assert proc.returncode != 0, f"{name} was not caught"
        out = proc.stdout + proc.stderr
        assert name in out

    def test_intended_reasons_recorded(self, clean_run):
        _, results_path = clean_run
        data = json.loads(results_path.read_text())
        muts = data["mutations"]
        assert set(muts) == set(MUTATIONS)
        for name, record in muts.items():
            assert record["applied"], name
            assert record["exit_code"] != 0, name
            assert record["intended_reason"] in record["observed_reasons"], (name, record)

    def test_null_mutation_still_passes(self, tmp_path):
        """Negative control for the harness: no-op mutation must not fail."""
        proc = run_validator("--mutation", "NONE", tmp_path=tmp_path)
        assert proc.returncode == 0, proc.stdout + proc.stderr


class TestValidatorBoundaries:
    """The validator is pure: no database, no installer, no feature mode."""

    def test_no_database_or_network_imports(self):
        source = VALIDATOR.read_text()
        for banned in ("psycopg", "socket", "create_connection", "MySQLdb", "sqlite3"):
            assert banned not in source, banned

    def test_no_installer_import(self):
        source = VALIDATOR.read_text()
        assert "src.etl" not in source
        assert "etl import" not in source

    def test_cli_has_no_feature_generation_mode(self, clean_run):
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), "--help"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert "--mutation" in proc.stdout
        assert "--mode" not in proc.stdout  # no pre-seal/post-seal style modes; no generation mode

    def test_fixtures_file_declared_synthetic(self):
        data = json.loads(FIXTURES.read_text())
        assert data["provenance"] == "synthetic"

    def test_contract_states_required(self):
        import yaml
        contract = yaml.safe_load(CONTRACT.read_text())
        required = {
            "point_comparable", "upper_limit_supported", "floor_or_censoring_suspected",
            "nonpositive_log_undefined", "missing", "invalid_or_unsupported",
        }
        for machine in ("sfr_inst_point", "sfr_100_point"):
            states = {r["state"] for r in contract["state_machines"][machine]["rules"]}
            assert required <= states, machine
        for rule in contract["state_machines"]["sfr_100_point"]["rules"]:
            if rule["state"] == "upper_limit_supported":
                assert rule.get("unreachable_on_current_sources") is True


class TestIdentityIntegrity:
    """Identity records are compared by content, never overwritten."""

    def test_identity_json_matches_tracked_files(self):
        data = json.loads(IDENTITY.read_text())
        import hashlib
        for entry in data["tracked_evidence_files"]:
            path = REPO_ROOT / entry["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == entry["sha256"], entry["path"]

    def test_scratch_identity_mutation_rejected(self, tmp_path):
        scratch = tmp_path / "input-identity.json"
        data = json.loads(IDENTITY.read_text())
        data["p2r05_product"]["run_id"] = "0" * 64
        scratch.write_text(json.dumps(data))
        proc = run_validator("--identity", str(scratch), tmp_path=tmp_path)
        assert proc.returncode != 0
        assert "identity_mismatch" in proc.stdout + proc.stderr
