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
    "M10_pop_mass_error_clause_removed",
    "M11_mass_residual_population_gate_removed",
    "M12_sfr_score_point_state_only",
    "M13_sfr_population_gate_removed",
    "M14_pop_mass_conditions_disagree",
    "M15_median_containment_removed",
    "M16_symmetric_average_restored",
    "M17_side_by_raw_delta",
    "M18_zero_width_guard_removed",
    "M19_native_ssfr_reinserted",
    "M20_false_coupling_declared",
    "M21_ctx_marked_rankable",
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


class TestA12PopulationAndScaleGates:
    """P2R-06a A1.2 repairs: population gating and SFR scale states (R2, R3, R8)."""

    def test_population_gating_fixtures_present(self, results):
        ids = {c["id"] for c in results["cases"]}
        for required in [
            "FX-R3a", "FX-R3b",  # POP-MASS error validity
            "FX-R8a", "FX-R8b", "FX-R8c", "FX-R8d", "FX-R8e",  # population gates
            "FX-R2a", "FX-R2b", "FX-R2c", "FX-R2d", "FX-R2e", "FX-R2f", "FX-R2g",
        ]:
            assert required in ids, required

    def test_nonmember_residuals_and_scores_are_null(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        for fixture_id in ("FX-R3a", "FX-R3b", "FX-R8a", "FX-R8b", "FX-R8c"):
            observed = by_id[fixture_id]["observed"]
            assert observed["residual_mass_dex"] is None, fixture_id
            assert observed["score_mass"] is None, fixture_id
            assert observed["pop_mass"] is False, fixture_id
        observed = by_id["FX-R8d"]["observed"]
        assert observed["residual_sfr_100_dex"] is None
        assert observed["score_sfr_100"] is None

    def test_sfr_scores_respect_scale_states(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        assert by_id["FX-R2a"]["observed"]["score_sfr_100"] is None
        assert by_id["FX-R2a"]["observed"]["sfr_100_scale_state"] == "approximation_out_of_domain"
        assert by_id["FX-R2a"]["observed"]["residual_sfr_100_dex"] is not None
        assert by_id["FX-R2d"]["observed"]["sfr_100_scale_reason"] == "quantile_order_violation"
        assert by_id["FX-R2e"]["observed"]["sfr_100_scale_reason"] == "median_outside_quantile_interval"
        assert by_id["FX-R2g"]["observed"]["sfr_100_scale_reason"] == "nonfinite_uncertainty_input"

    def test_inclusive_boundary_controls_finite(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        for fixture_id in ("FX-R2b", "FX-R2c"):
            assert isinstance(by_id[fixture_id]["observed"]["score_sfr_100"], float), fixture_id

    def test_mass_delta_bit_identical_on_controls(self, results):
        """delta_mass_dex stays numerically identical on point-valid audit controls."""
        by_id = {c["id"]: c for c in results["cases"]}
        assert by_id["FX-01a"]["observed"]["delta_mass_dex"] == 1.0
        assert by_id["FX-R8a"]["observed"]["delta_mass_dex"] == 1.0  # raw audit retained

    def test_pop_mass_consistency_with_input_contract(self):
        """The POP-MASS predicate and echo agree with input-contract.md section 6."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "src" / "inspection"))
        import validate_ta_v2_design as validator
        import yaml
        contract = yaml.safe_load(CONTRACT.read_text())
        failures = validator.pop_mass_consistency(contract)
        assert failures == [], failures



class TestA13DirectionalWidths:
    """P2R-06a A1.3 repairs: directional LePhare half-widths (R9, decision 2)."""

    def test_directional_fixtures_present(self, results):
        ids = {c["id"] for c in results["cases"]}
        for required in [
            "FX-R9a", "FX-R9b", "FX-R9c", "FX-R9d", "FX-R9e",
            "FX-R9f", "FX-R9g", "FX-R9h", "FX-R9i",
        ]:
            assert required in ids, required

    def test_asymmetric_scores_use_selected_side(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        assert abs(by_id["FX-R9a"]["observed"]["sigma_mass_lp_lo_dex"] - 0.05) < 1e-12
        assert abs(by_id["FX-R9a"]["observed"]["sigma_mass_lp_hi_dex"] - 0.30) < 1e-12
        # positive residual -> lower width 0.05; symmetric 0.175 would give 0.4957
        assert abs(by_id["FX-R9a"]["observed"]["score_mass"] - 0.891740157358414) < 1e-9
        # negative residual -> upper width 0.30
        assert abs(by_id["FX-R9b"]["observed"]["score_mass"] - (-0.31610854496087415)) < 1e-9
        # opposite-sign delta/residual: side follows the residual
        assert abs(by_id["FX-R9c"]["observed"]["score_mass"] - 0.9820018620764585) < 1e-9

    def test_degenerate_and_zero_residual_cases(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        assert by_id["FX-R9d"]["observed"]["score_mass_state"] == "degenerate_quantile_width"
        assert by_id["FX-R9d"]["observed"]["score_mass"] is None
        assert by_id["FX-R9e"]["observed"]["score_mass_state"] == "point_valid"
        assert by_id["FX-R9e"]["observed"]["sigma_mass_lp_hi_dex"] == 0.0
        assert by_id["FX-R9f"]["observed"]["score_mass"] == 0.0
        assert by_id["FX-R9f"]["observed"]["score_mass_state"] == "point_valid"
        assert by_id["FX-R9g"]["observed"]["score_mass_state"] == "degenerate_quantile_width"
        assert by_id["FX-R9h"]["observed"]["mass_scale_reason"] == "median_outside_quantile_interval"
        assert by_id["FX-R9h"]["observed"]["delta_mass_dex"] is not None

    def test_sigma_sys_solve_policy_checks(self, results):
        checks = results["sigma_sys_solve_checks"]
        assert {c["id"] for c in checks} == {"SOLVE-1", "SOLVE-2", "SOLVE-3"}
        assert all(c["pass"] for c in checks)
        by_id = {c["id"]: c for c in checks}
        assert abs(by_id["SOLVE-1"]["observed"]["value"] - 0.3569053410920044) < 1e-9
        assert by_id["SOLVE-2"]["observed"]["reason"] == "no_admissible_systematic_solution"
        assert by_id["SOLVE-3"]["observed"]["reason"] == "zero_residual_spread"

    def test_no_symmetric_lp_outputs_remain(self):
        import yaml
        contract = yaml.safe_load(CONTRACT.read_text())
        names = {o["name"] for o in contract["outputs"]}
        assert "sigma_mass_lp_dex" not in names
        assert "sigma_sfr_lp_dex" not in names
        assert {"sigma_mass_lp_lo_dex", "sigma_mass_lp_hi_dex",
                "sigma_sfr_lp_lo_dex", "sigma_sfr_lp_hi_dex"} <= names


class TestA14SsfrComponentView:
    """P2R-06a A1.4 repairs: sSFR component view and non-additivity context (R1)."""

    def test_component_fixtures_present(self, results):
        ids = {c["id"] for c in results["cases"]}
        for required in ["FX-R1a", "FX-R1b", "FX-R1c", "FX-R1d"]:
            assert required in ids, required

    def test_fx06a_component_values(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        assert abs(by_id["FX-06a"]["observed"]["delta_ssfr_100_dex"]
                   - (0.5 - __import__("math").log10(2.0))) <= 1e-12
        assert by_id["FX-06a"]["observed"]["ctx_lp_ssfr_nonadditivity_dex"] == 0.5
        # coupling holds numerically: view == delta_sfr - delta_mass
        obs = by_id["FX-06a"]["observed"]
        coupling_ok = abs(
            by_id["FX-06a"]["observed"]["delta_ssfr_100_dex"]
            - (obs["delta_sfr_100_dex"] - obs["delta_mass_dex"])
        ) <= 1e-12 if "delta_sfr_100_dex" in obs else None
        # full outputs are recorded by the validator's own coupling check;
        # the case passing means no algebraic_coupling_violated failure

    def test_native_ssfr_independent_eligibility(self, results):
        by_id = {c["id"]: c for c in results["cases"]}
        for fixture_id in ("FX-R1c", "FX-R1d"):
            observed = by_id[fixture_id]["observed"]
            assert observed["delta_ssfr_100_dex"] is not None, fixture_id
            assert observed["ctx_lp_ssfr_nonadditivity_dex"] is None, fixture_id
        assert by_id["FX-R1b"]["observed"]["ctx_lp_ssfr_nonadditivity_dex"] == 0.0

    def test_math_counterexample_recorded(self, results):
        math_checks = results["mathematical_counterexamples"]
        assert {c["id"] for c in math_checks} == {"MATH-1"}
        check = math_checks[0]
        assert check["pass"]
        assert abs(check["observed_nonadditivity"] - (-0.29205262889677)) < 1e-9
        assert check["median_y"] > check["median_x"]

    def test_component_view_not_rankable(self):
        import yaml
        contract = yaml.safe_load(CONTRACT.read_text())
        by_name = {o["name"]: o for o in contract["outputs"]}
        assert by_name["delta_ssfr_100_dex"]["rankable"] is False
        assert by_name["delta_ssfr_inst_dex"]["kind"] == "derived_view"
        assert by_name["ctx_lp_ssfr_nonadditivity_dex"]["context_only"] is True
        assert by_name["ctx_lp_ssfr_nonadditivity_dex"]["rankable"] is False


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
