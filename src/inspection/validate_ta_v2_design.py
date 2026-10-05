#!/usr/bin/env python3
"""
Script Name  : validate_ta_v2_design.py
Description  : Pure synthetic-contract validator for the proposed T_A v2 design (P2R-06 gate 6.3)
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-10-05
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Validates the proposed T_A v2 feature contract in
docs/research/ta-v2-design/feature-contract.yaml against the synthetic-only
fixture corpus in fixtures.json and the identity record input-identity.json.
It evaluates the declared algebra (state machines, formulas, center
scenarios, scales, partition-use rules) on synthetic records, checks the
declared dependency prohibitions (chi-square quotients, dof recovery,
invented photo-z, truth labels, forbidden covariates), compares recorded
identities by content, and applies each named scratch-copy mutation to
prove it fails its intended invariant. The validator never connects to a
database, never imports an installer, and has no catalog feature-generation
mode: every number it touches is a labelled synthetic fixture value.

Usage
-----
    python src/inspection/validate_ta_v2_design.py [options]

Examples
--------
    python src/inspection/validate_ta_v2_design.py
        Validate the tracked contract, fixtures, and identity record; write
        docs/research/ta-v2-design/validation-results.json; exit 0 on a
        complete pass, 1 on any failure.

    python src/inspection/validate_ta_v2_design.py --mutation M4_chi2_quotient
        Apply the named mutation to an in-memory scratch copy and exit
        nonzero with the intended failure reason (demonstrates the guard).
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = REPO_ROOT / "docs" / "research" / "ta-v2-design" / "feature-contract.yaml"
DEFAULT_FIXTURES = REPO_ROOT / "docs" / "research" / "ta-v2-design" / "fixtures.json"
DEFAULT_IDENTITY = REPO_ROOT / "docs" / "research" / "ta-v2-design" / "input-identity.json"
DEFAULT_RESULTS = REPO_ROOT / "docs" / "research" / "ta-v2-design" / "validation-results.json"
INPUT_CONTRACT_MD = REPO_ROOT / "docs" / "research" / "ta-v2-design" / "input-contract.md"

# Canonical raw-formula identity of the gate 6.2 proposal. A scratch copy
# whose delta formulas drift from these bytes is rejected; the fixtures
# independently check the numeric behaviour, so this guard is not circular.
# AI NOTE: keep in sync with feature-contract.yaml (whitespace normalized).
CANONICAL_DELTA_FORMULAS = {
    "delta_mass_dex": "lephare.mass_med - log10(cigale.mass)",
    "delta_sfr_inst_dex": "lephare.sfr_med - log10(cigale.sfr_inst)",
    "delta_sfr_100_dex": "lephare.sfr_med - log10(cigale.sfr_100myr)",
    "delta_ssfr_inst_dex": "lephare.ssfr_med - (log10(cigale.sfr_inst) - log10(cigale.mass))",
    "delta_ssfr_100_dex": "lephare.ssfr_med - (log10(cigale.sfr_100myr) - log10(cigale.mass))",
}

CHI2_IDENTIFIERS = {"lephare.chi2_best", "cigale.chi2_best_fit", "cigale.chi2_red_best_fit"}
REQUIRED_SFR_STATES = {
    "point_comparable",
    "upper_limit_supported",
    "floor_or_censoring_suspected",
    "nonpositive_log_undefined",
    "missing",
    "invalid_or_unsupported",
}
FIT_REQUEST_RULE_SUBSTRING = "validation or holdout catalog_id is rejected"
NUMERIC_TOLERANCE = 1e-9

# =============================================================================
# Safe expression evaluation (no eval; whitelist-only)
# =============================================================================


class ExpressionError(ValueError):
    """Raised when an expression uses anything outside the whitelist."""


_TOKEN_RE = re.compile(
    r"\s*(?:(?P<num>\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)"
    r"|(?P<id>[A-Za-z_][A-Za-z0-9_.]*)"
    r"|(?P<op>\*\*|<=|>=|==|!=|[-+*/^()<>,]))"
)
_ALLOWED_FUNCTIONS = {"log10", "sqrt", "abs", "min", "max", "is_null", "is_nan"}
_COMPARISONS = {"<", "<=", ">", ">=", "==", "!="}


def tokenize(text):
    """Split an expression string into (kind, value) tokens."""
    tokens, pos = [], 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        match = _TOKEN_RE.match(text, pos)
        if not match or match.end() == pos:
            raise ExpressionError(f"unparsable expression near: {text[pos:pos+24]!r}")
        pos = match.end()
        kind = match.lastgroup
        tokens.append((kind, match.group(kind)))
    return tokens


class _Parser:
    """Recursive-descent parser for the whitelisted arithmetic/predicate grammar."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def next(self):
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, value):
        kind, val = self.next()
        if val != value:
            raise ExpressionError(f"expected {value!r}, found {val!r}")

    def parse(self):
        node = self.parse_or()
        if self.pos != len(self.tokens):
            raise ExpressionError(f"trailing tokens at {self.peek()!r}")
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == ("op", "OR") or self.peek() == ("id", "OR"):
            self.next()
            node = ("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_comparison()
        while self.peek() == ("op", "AND") or self.peek() == ("id", "AND"):
            self.next()
            node = ("and", node, self.parse_comparison())
        return node

    def parse_comparison(self):
        node = self.parse_sum()
        if self.peek()[1] in _COMPARISONS:
            op = self.next()[1]
            node = ("cmp", op, node, self.parse_sum())
        return node

    def parse_sum(self):
        node = self.parse_product()
        while self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            node = ("bin", op, node, self.parse_product())
        return node

    def parse_product(self):
        node = self.parse_power()
        while self.peek()[1] in ("*", "/"):
            op = self.next()[1]
            node = ("bin", op, node, self.parse_power())
        return node

    def parse_power(self):
        node = self.parse_unary()
        if self.peek()[1] in ("^", "**"):
            self.next()
            node = ("bin", "**", node, self.parse_power())
        return node

    def parse_unary(self):
        kind, val = self.peek()
        if val == "-":
            self.next()
            return ("neg", self.parse_unary())
        if val == "+":
            self.next()
            return self.parse_unary()
        return self.parse_atom()

    def parse_atom(self):
        kind, val = self.next()
        if kind == "num":
            return ("num", float(val))
        if kind == "id":
            if val in ("true", "True"):
                return ("bool", True)
            if val in ("false", "False"):
                return ("bool", False)
            if self.peek() == ("op", "("):
                if val not in _ALLOWED_FUNCTIONS:
                    raise ExpressionError(f"function {val!r} is not whitelisted")
                self.next()
                args = [self.parse_or()]
                while self.peek()[1] == ",":
                    self.next()
                    args.append(self.parse_or())
                self.expect(")")
                return ("call", val, args)
            return ("id", val)
        if val == "(":
            node = self.parse_or()
            self.expect(")")
            return node
        raise ExpressionError(f"unexpected token {val!r}")


def parse_expression(text):
    """Parse an expression string into an AST node."""
    return _Parser(tokenize(text)).parse()


def eval_node(node, resolver):
    """Evaluate an AST node; identifiers resolve through ``resolver``."""
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "bool":
        return node[1]
    if kind == "id":
        return resolver(node[1])
    if kind == "neg":
        value = eval_node(node[1], resolver)
        return None if value is None else -value
    if kind == "bin":
        left = eval_node(node[2], resolver)
        right = eval_node(node[3], resolver)
        if left is None or right is None:
            return None
        if node[1] == "+":
            return left + right
        if node[1] == "-":
            return left - right
        if node[1] == "*":
            return left * right
        if node[1] == "/":
            return None if right == 0 else left / right
        if node[1] == "**":
            try:
                return left ** right
            except (OverflowError, ZeroDivisionError):
                return None
        raise ExpressionError(f"operator {node[1]!r} not supported")
    if kind == "cmp":
        left = eval_node(node[2], resolver)
        right = eval_node(node[3], resolver)
        if left is None or right is None:
            return False
        op = node[1]
        return {
            "<": lambda: left < right, "<=": lambda: left <= right,
            ">": lambda: left > right, ">=": lambda: left >= right,
            "==": lambda: left == right, "!=": lambda: left != right,
        }[op]()
    if kind == "and":
        left = eval_node(node[1], resolver)
        right = eval_node(node[2], resolver)
        return bool(left) and bool(right)
    if kind == "or":
        left = eval_node(node[1], resolver)
        right = eval_node(node[2], resolver)
        return bool(left) or bool(right)
    if kind == "call":
        name, args = node[1], [eval_node(a, resolver) for a in node[2]]
        if name == "is_null":
            return args[0] is None
        if name == "is_nan":
            import math
            return args[0] is not None and not isinstance(args[0], bool) and math.isnan(args[0])
        if args and any(a is None for a in args):
            return None
        import math
        if name == "log10":
            return None if args[0] <= 0 else math.log10(args[0])
        if name == "sqrt":
            return None if args[0] < 0 else math.sqrt(args[0])
        if name == "abs":
            return abs(args[0])
        if name == "min":
            return min(args)
        if name == "max":
            return max(args)
    raise ExpressionError(f"node kind {kind!r} not supported")


def collect_identifiers(node, into):
    """Collect every identifier name referenced by an AST node."""
    kind = node[0]
    if kind == "id":
        into.add(node[1])
    elif kind == "num" or kind == "bool":
        pass
    elif kind == "neg":
        collect_identifiers(node[1], into)
    elif kind in ("bin",):
        collect_identifiers(node[2], into)
        collect_identifiers(node[3], into)
    elif kind == "cmp":
        collect_identifiers(node[2], into)
        collect_identifiers(node[3], into)
    elif kind in ("and", "or"):
        collect_identifiers(node[1], into)
        collect_identifiers(node[2], into)
    elif kind == "call":
        for arg in node[2]:
            collect_identifiers(arg, into)
    return into


def normalize_formula(text):
    """Collapse whitespace for byte-identity comparisons of declared formulas."""
    return re.sub(r"\s+", "", str(text))


# =============================================================================
# Contract evaluation on synthetic records
# =============================================================================


def record_resolver(record, constants):
    """Resolve identifiers against a synthetic record plus declared constants."""

    def resolve(name):
        if name in constants:
            return constants[name]
        if name in record:
            return record[name]
        # AI NOTE: identifiers absent from the record resolve to None so that
        # is_null(...) predicates fire; arithmetic with None yields None
        # instead of an exception, keeping evaluation pure and total.
        return None

    return resolve


def evaluate_rule(machine, record, constants):
    """Apply a state machine's ordered rules; the first match supplies state and reason."""
    for rule in machine["rules"]:
        predicate = str(rule.get("when", "true"))
        if predicate == "true":
            return rule["state"], rule.get("reason", "none")
        if predicate == "false":
            continue
        try:
            value = eval_node(parse_expression(predicate), record_resolver(record, constants))
        except ExpressionError:
            value = False
        if value:
            return rule["state"], rule.get("reason", "none")
    return None, "no_rule_matched"


def precondition_ok(text, states):
    """Evaluate a machine precondition of the form 'X == y AND ...' against computed states."""
    for clause in re.split(r"\s+AND\s+", str(text)):
        match = re.fullmatch(r"\s*([A-Za-z0-9_]+)\s*==\s*([A-Za-z0-9_]+)\s*", clause)
        if not match:
            return False
        name, expected = match.groups()
        if states.get(name) != expected:
            return False
    return True


def evaluate_center(scenario, record):
    """Evaluate a synthetic center scenario; returns (expected_delta, support)."""
    kind = scenario["model_kind"]
    if kind == "C0-constant":
        return scenario["constant_value"], "global_fallback"
    if kind == "S0-constant":
        raise ExpressionError("S0 scenarios are read per-timescale, not through this path")
    if kind == "C1-conditional-binned-median":
        z = record.get("lephare.zpdf_med")
        mag = record.get("photometry_primary.mag_auto_f444w")
        if z is None or mag is None:
            return scenario["global_constant"], "out_of_hull"
        z_edges, mag_edges = scenario["z_bin_edges"], scenario["mag_bin_edges"]

        def bin_index(value, edges):
            for index in range(len(edges) - 1):
                if edges[index] <= value < edges[index + 1]:
                    return index
            return None

        zi, mi = bin_index(z, z_edges), bin_index(mag, mag_edges)
        if zi is None or mi is None:
            return scenario["global_constant"], "out_of_hull"
        cell = scenario["cell_values"].get(f"{zi}|{mi}")
        if cell is not None:
            return cell, "cell"
        z_only = scenario["z_only_values"].get(str(zi))
        if z_only is not None:
            return z_only, "z_fallback"
        return scenario["global_constant"], "global_fallback"
    raise ExpressionError(f"unknown scenario kind {kind!r}")


def evaluate_case(contract, case, scenarios):
    """Compute every declared output for one synthetic case record."""
    constants = {c["name"]: c["value"] for c in contract["declared_constants"]}
    record = case["record"]
    scenario = scenarios[case["scenario"]]
    machines = contract["state_machines"]
    # AI NOTE: delta outputs are evaluated through the contract's own declared
    # formulas, so a mutated scratch formula yields mutated values that the
    # fixtures catch; the canonical-identity guard is a separate structural
    # check and does not mask value mismatches.
    declared_formulas = {o["name"]: o["formula"] for o in contract["outputs"] if o.get("formula")}
    outputs = {}
    states = {}

    def run_machine(name, output_state, output_reason):
        machine = machines[name]
        precondition = machine.get("precondition")
        if precondition and not precondition_ok(precondition, states):
            state, reason = "invalid_or_unsupported", "parent_state_not_permitted"
        else:
            state, reason = evaluate_rule(machine, record, constants)
        states[name] = state
        states[output_state] = state
        outputs[output_state] = state
        if output_reason:
            outputs[output_reason] = reason
        return state, reason

    def eval_formula(text):
        try:
            return eval_node(parse_expression(text), record_resolver(record, constants))
        except ExpressionError:
            return None

    run_machine("mass_point", "mass_point_state", "mass_point_reason")
    outputs["selection_type0"] = bool(
        eval_node(parse_expression("lephare.type == 0"), record_resolver(record, constants))
    )
    outputs["delta_mass_dex"] = (
        eval_formula(declared_formulas["delta_mass_dex"])
        if outputs["mass_point_state"] == "point_valid"
        else None
    )
    outputs["pop_mass"] = bool(outputs["selection_type0"] and outputs["mass_point_state"] == "point_valid")

    if scenario["model_kind"] == "S0-constant":
        # AI NOTE: S0 scenarios declare only the per-timescale SFR constants;
        # mass-center outputs stay absent rather than being fabricated.
        expected_delta, support = None, None
    else:
        expected_delta, support = evaluate_center(scenario, record)
    outputs["expected_delta_mass_dex"] = expected_delta
    outputs["center_support"] = support
    outputs["residual_mass_dex"] = (
        outputs["delta_mass_dex"] - expected_delta
        if outputs["delta_mass_dex"] is not None and expected_delta is not None
        else None
    )

    scale_state, _ = run_machine("mass_scale", "mass_scale_state", "mass_scale_reason")
    if scale_state == "point_valid":
        outputs["sigma_mass_lp_dex"] = eval_formula("(lephare.mass_u68 - lephare.mass_l68) / 2.0")
        outputs["sigma_mass_cig_dex"] = eval_formula("cigale.mass_err / (cigale.mass * ln10)")
    else:
        outputs["sigma_mass_lp_dex"] = None
        outputs["sigma_mass_cig_dex"] = None
    outputs["sigma_sys_mass_dex"] = scenario.get("sigma_sys_mass_dex")
    components = [outputs["sigma_mass_lp_dex"], outputs["sigma_mass_cig_dex"], outputs["sigma_sys_mass_dex"]]
    if scale_state == "point_valid" and all(c is not None for c in components):
        scale = sum(c * c for c in components) ** 0.5
        if scale < 1.0e-12:
            outputs["score_mass_state"] = "zero_combined_scale"
            outputs["score_mass"] = None
        elif outputs["residual_mass_dex"] is not None:
            outputs["score_mass"] = outputs["residual_mass_dex"] / scale
            outputs["score_mass_state"] = "point_valid"
        else:
            outputs["score_mass"] = None
            outputs["score_mass_state"] = "unsupported_scale"
    else:
        outputs["score_mass"] = None
        outputs["score_mass_state"] = "unsupported_scale" if scale_state == "point_valid" else scale_state

    for machine, state_name, reason_name, delta_name, formula_key in [
        ("sfr_inst_point", "sfr_inst_state", "sfr_inst_reason", "delta_sfr_inst_dex", "delta_sfr_inst_dex"),
        ("sfr_100_point", "sfr_100_state", "sfr_100_reason", "delta_sfr_100_dex", "delta_sfr_100_dex"),
    ]:
        state, _ = run_machine(machine, state_name, reason_name)
        outputs[delta_name] = (
            eval_formula(declared_formulas[formula_key]) if state == "point_comparable" else None
        )
    outputs["pop_sfr_inst"] = bool(outputs["selection_type0"] and outputs["sfr_inst_state"] == "point_comparable")
    outputs["pop_sfr_100"] = bool(outputs["selection_type0"] and outputs["sfr_100_state"] == "point_comparable")
    outputs["timescale_caveat_lephare"] = True

    s0 = scenarios.get("SYNTH-S0", scenario)
    outputs["expected_delta_sfr_inst_dex"] = s0.get("constant_value_inst")
    outputs["expected_delta_sfr_100_dex"] = s0.get("constant_value_100")
    outputs["residual_sfr_inst_dex"] = (
        outputs["delta_sfr_inst_dex"] - s0["constant_value_inst"]
        if outputs["delta_sfr_inst_dex"] is not None and s0.get("constant_value_inst") is not None
        else None
    )
    outputs["residual_sfr_100_dex"] = (
        outputs["delta_sfr_100_dex"] - s0["constant_value_100"]
        if outputs["delta_sfr_100_dex"] is not None and s0.get("constant_value_100") is not None
        else None
    )
    outputs["sigma_sfr_lp_dex"] = eval_formula("(lephare.sfr_u68 - lephare.sfr_l68) / 2.0")
    outputs["sigma_sfr_cig_inst_dex"] = (
        eval_formula("cigale.sfr_inst_err / (cigale.sfr_inst * ln10)")
        if outputs["sfr_inst_state"] == "point_comparable"
        else None
    )
    outputs["sigma_sfr_cig_100_dex"] = (
        eval_formula("cigale.sfr_100myr_err / (cigale.sfr_100myr * ln10)")
        if outputs["sfr_100_state"] == "point_comparable"
        else None
    )
    outputs["sigma_sys_sfr_inst_dex"] = scenario.get("sigma_sys_sfr_inst_dex")
    outputs["sigma_sys_sfr_100_dex"] = scenario.get("sigma_sys_sfr_100_dex")
    for suffix, delta_name, residual_name, cig_sigma, sys_sigma in [
        ("inst", "delta_sfr_inst_dex", "residual_sfr_inst_dex", "sigma_sfr_cig_inst_dex", "sigma_sys_sfr_inst_dex"),
        ("100", "delta_sfr_100_dex", "residual_sfr_100_dex", "sigma_sfr_cig_100_dex", "sigma_sys_sfr_100_dex"),
    ]:
        parts = [outputs["sigma_sfr_lp_dex"], outputs[cig_sigma], outputs[sys_sigma]]
        if outputs[f"sfr_{suffix}_state"] == "point_comparable" and all(p is not None for p in parts):
            scale = sum(p * p for p in parts) ** 0.5
            outputs[f"score_sfr_{suffix}"] = (
                outputs[residual_name] / scale if scale >= 1.0e-12 and outputs[residual_name] is not None else None
            )
        else:
            outputs[f"score_sfr_{suffix}"] = None

    for machine, state_name, reason_name, delta_name, formula_key in [
        ("ssfr_inst_point", "ssfr_inst_state", "ssfr_inst_reason", "delta_ssfr_inst_dex", "delta_ssfr_inst_dex"),
        ("ssfr_100_point", "ssfr_100_state", "ssfr_100_reason", "delta_ssfr_100_dex", "delta_ssfr_100_dex"),
    ]:
        state, _ = run_machine(machine, state_name, reason_name)
        outputs[delta_name] = (
            eval_formula(declared_formulas[formula_key]) if state == "point_valid" else None
        )
    outputs["pop_ssfr_inst"] = bool(outputs["selection_type0"] and outputs["ssfr_inst_state"] == "point_valid")
    outputs["pop_ssfr_100"] = bool(outputs["selection_type0"] and outputs["ssfr_100_state"] == "point_valid")
    outputs["not_independent_of_mass_and_sfr"] = True
    # AI NOTE: the sSFR score is unsupported by declared evidence (unknown
    # mass-SFR error correlation); it stays NULL rather than assuming
    # independence, per the contract's unsupported_correlated_errors state.
    outputs["score_ssfr_inst"] = None
    outputs["score_ssfr_100"] = None

    for output in contract["outputs"]:
        if output.get("kind") == "context_passthrough" and "source" in output:
            outputs[output["name"]] = record.get(output["source"])
    return outputs


def compare_expected(case, outputs):
    """Compare a case's expected values against computed outputs."""
    mismatches = []
    for key, expected in case["expect"].items():
        observed = outputs.get(key)
        if isinstance(expected, bool) or isinstance(observed, bool):
            if bool(expected) != bool(observed):
                mismatches.append(key)
        elif expected is None:
            if observed is not None:
                mismatches.append(key)
        elif isinstance(expected, (int, float)):
            if not isinstance(observed, (int, float)) or abs(observed - expected) > NUMERIC_TOLERANCE * max(
                1.0, abs(expected)
            ):
                mismatches.append(key)
        elif observed != expected:
            mismatches.append(key)
    return mismatches


def check_fit_requests(fixtures):
    """Enforce the partition-use rules on the synthetic fit requests."""
    results = []
    for request in fixtures.get("fit_requests", []):
        reasons = []
        assignment = {}
        for entry in request["partition_assignment"]:
            cid = entry["catalog_id"]
            if cid in assignment and assignment[cid] != entry["split"]:
                reasons.append(f"catalog_id {cid} appears in two partitions")
            assignment[cid] = entry["split"]
        seen = set()
        for row in request["training_rows"]:
            cid = row["catalog_id"]
            if cid in seen:
                reasons.append(f"duplicate training rows for catalog_id {cid}")
            seen.add(cid)
        for cid in seen:
            if assignment.get(cid) in ("validation", "holdout"):
                reasons.append(f"validation or holdout catalog_id {cid} in fit request")
        expected = request["expect"]
        ok = (not reasons) if expected == "accepted" else bool(reasons)
        if expected == "rejected" and request.get("intended_reason") and not any(
            request["intended_reason"] in r for r in reasons
        ):
            ok = False
            reasons.append(f"intended reason absent: {request['intended_reason']}")
        results.append(
            {
                "id": request["id"],
                "description": request["description"],
                "expected": expected,
                "observed": reasons or ["accepted"],
                "pass": ok,
            }
        )
    return results


# =============================================================================
# Structural contract checks and mutation controls
# =============================================================================


def structural_checks(contract, fixtures):
    """Declare-and-verify the contract's own invariants; return failure codes."""
    failures = []
    machines = contract["state_machines"]

    for machine_name in ("sfr_inst_point", "sfr_100_point"):
        states = {rule["state"] for rule in machines[machine_name]["rules"]}
        for required in sorted(REQUIRED_SFR_STATES - states):
            failures.append(f"required_state_missing:{required}")
        for rule in machines[machine_name]["rules"]:
            if rule["state"] == "upper_limit_supported" and not rule.get("unreachable_on_current_sources"):
                failures.append("reachable_upper_limit_declared")

    for output in contract["outputs"]:
        formula = output.get("formula")
        if not formula:
            continue
        name = output["name"]
        if name in CANONICAL_DELTA_FORMULAS and normalize_formula(formula) != normalize_formula(
            CANONICAL_DELTA_FORMULAS[name]
        ):
            failures.append(f"delta_formula_identity:{name}")
        try:
            tree = parse_expression(formula)
        except ExpressionError as exc:
            failures.append(f"unparsable_formula:{name}:{exc}")
            continue
        identifiers = collect_identifiers(tree, set())
        chi2_refs = identifiers & CHI2_IDENTIFIERS
        if len(chi2_refs) >= 2 and ("/" in re.sub(r"\s+", "", formula)):
            failures.append("chi2_quotient")
        if chi2_refs and output.get("kind") != "context_passthrough":
            failures.append(f"chi2_predictor:{name}")
        if "lephare.nbfilt" in identifiers and output.get("kind") != "context_passthrough":
            failures.append(f"dof_from_nbfilt:{name}")
        for identifier in identifiers:
            if re.match(r"^cigale\.(z|photoz)", identifier):
                failures.append(f"independent_cigale_photoz:{identifier}")
        if "true_" in name or name.endswith("_truth"):
            failures.append(f"mass_truth_label:{name}")

    rules_text = " ".join(contract["partition_use"]["rules"])
    if FIT_REQUEST_RULE_SUBSTRING not in rules_text:
        failures.append("fit_request_rule_missing")

    forbidden_covariates = contract["centers"]["mass_center"]["forbidden_covariates"]
    for covariate in contract["centers"]["mass_center"]["comparison_set"][1]["covariates"]:
        if covariate in forbidden_covariates:
            failures.append(f"forbidden_covariate:{covariate}")
        elif "specz" in covariate:
            failures.append(f"forbidden_covariate:{covariate}")
        elif "tile" in covariate or "survey" in covariate:
            failures.append(f"forbidden_covariate:{covariate}")

    if fixtures.get("provenance") != "synthetic":
        failures.append("fixtures_not_synthetic")
    ids = [case["id"] for case in fixtures.get("cases", [])]
    if len(ids) != len(set(ids)) or not all(i.startswith("FX-") for i in ids):
        failures.append("fixture_ids_unstable")

    for case in fixtures.get("cases", []):
        field = case.get("asserts_no_rule_references")
        if not field:
            continue
        referenced = set()
        for machine in machines.values():
            for rule in machine["rules"]:
                try:
                    collect_identifiers(parse_expression(str(rule.get("when", "true"))), referenced)
                except ExpressionError:
                    continue
        for output in contract["outputs"]:
            if output.get("formula"):
                try:
                    collect_identifiers(parse_expression(output["formula"]), referenced)
                except ExpressionError:
                    continue
        if field in referenced:
            failures.append(f"undeclared_bound_field_referenced:{case['id']}")
    return failures


def identity_checks(identity, contract_path, fixtures_path, identity_path):
    """Compare recorded identities by content; never regenerate or overwrite."""
    failures = []

    def sha256_file(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    for entry in identity.get("tracked_evidence_files", []):
        path = REPO_ROOT / entry["path"]
        if not path.exists():
            failures.append(f"identity_file_absent:{entry['path']}")
        elif sha256_file(path) != entry["sha256"]:
            failures.append("identity_content_mismatch")
    spec = identity.get("authorizing_spec", {})
    spec_path = Path(spec.get("path", ""))
    if spec_path.exists() and sha256_file(spec_path) != spec.get("sha256"):
        failures.append("identity_mismatch:authorizing_spec")
    if INPUT_CONTRACT_MD.exists():
        text = INPUT_CONTRACT_MD.read_text()
        product = identity.get("p2r05_product", {})
        for key in ("run_id", "spec_sha256", "snapshot_manifest_sha256", "tile_map_canonical_digest"):
            if product.get(key) and product[key] not in text:
                failures.append(f"identity_mismatch:{key}")
    return failures


def apply_mutation(contract, identity, action):
    """Apply one named scratch-copy mutation in memory."""
    kind = action["kind"]
    if kind == "set_output_formula":
        for output in contract["outputs"]:
            if output["name"] == action["output"]:
                output["formula"] = action["formula"]
    elif kind == "drop_state_rule":
        machine = contract["state_machines"][action["machine"]]
        machine["rules"] = [r for r in machine["rules"] if r["state"] != action["state"]]
    elif kind == "drop_partition_rule":
        rules = contract["partition_use"]["rules"]
        contract["partition_use"]["rules"] = [r for r in rules if action["match"] not in r]
    elif kind == "add_output":
        contract["outputs"].append(copy.deepcopy(action["output"]))
    elif kind == "change_identity_hash":
        identity["tracked_evidence_files"][0]["sha256"] = action["value"]
    elif kind == "add_center_covariate":
        contract["centers"][action["center"]]["comparison_set"][1]["covariates"].append(action["covariate"])
    else:
        raise ValueError(f"unknown mutation kind {kind!r}")


def run_validation(contract, fixtures, identity, paths):
    """Run cases, fit requests, structural and identity checks; return failure codes and details."""
    failures = []
    scenarios = fixtures["declared_center_scenarios"]
    case_results = []
    for case in fixtures.get("cases", []):
        try:
            outputs = evaluate_case(contract, case, scenarios)
        except (ExpressionError, KeyError, TypeError) as exc:
            failures.append(f"case_error:{case['id']}:{exc}")
            case_results.append(
                {"id": case["id"], "description": case["description"], "expected": case["expect"],
                 "observed": {"error": str(exc)}, "pass": False}
            )
            continue
        mismatches = compare_expected(case, outputs)
        for key in mismatches:
            failures.append(f"case_mismatch:{case['id']}:{key}")
        observed = {key: outputs.get(key) for key in case["expect"]}
        case_results.append(
            {"id": case["id"], "description": case["description"], "expected": case["expect"],
             "observed": observed, "pass": not mismatches}
        )
    fit_results = check_fit_requests(fixtures)
    for fit in fit_results:
        if not fit["pass"]:
            failures.append(f"fit_request:{fit['id']}")
    failures.extend(structural_checks(contract, fixtures))
    failures.extend(identity_checks(identity, *paths))
    return failures, case_results, fit_results


# =============================================================================
# Entry point
# =============================================================================


def build_arg_parser():
    """Declare the complete CLI surface (no database, installer, or generation modes)."""
    parser = argparse.ArgumentParser(description="Validate the proposed T_A v2 design contract (synthetic only)")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    parser.add_argument("--identity", default=str(DEFAULT_IDENTITY))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument(
        "--mutation",
        default=None,
        help="apply one named scratch-copy mutation (or NONE for the no-op control)",
    )
    parser.add_argument("--list-mutations", action="store_true", help="list named mutations and exit")
    return parser


def main(argv=None):
    """Validate, write results, and exit 0 on a complete pass."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    contract_path, fixtures_path, identity_path = Path(args.contract), Path(args.fixtures), Path(args.identity)
    contract = yaml.safe_load(contract_path.read_text())
    fixtures = json.loads(fixtures_path.read_text())
    identity = json.loads(identity_path.read_text())

    if args.list_mutations:
        for name, record in fixtures.get("mutations", {}).items():
            print(f"{name}: {record['description']}")
        return 0

    selected = [args.mutation] if args.mutation else list(fixtures.get("mutations", {}))
    mutation_records = {}
    for name in selected:
        if name == "NONE":
            mutated_contract, mutated_identity = copy.deepcopy(contract), copy.deepcopy(identity)
            action, description, intended = {"kind": "none"}, "no-op control", None
        else:
            record = fixtures["mutations"][name]
            mutated_contract = copy.deepcopy(contract)
            mutated_identity = copy.deepcopy(identity)
            apply_mutation(mutated_contract, mutated_identity, record["action"])
            action, description, intended = record["action"], record["description"], record["intended_reason"]
        failures, case_results, fit_results = run_validation(
            mutated_contract, fixtures, mutated_identity,
            (contract_path, fixtures_path, identity_path),
        )
        exit_code = 1 if failures else 0
        if name != "NONE":
            mutation_records[name] = {
                "applied": True,
                "description": description,
                "action": action,
                "intended_reason": intended,
                "observed_reasons": sorted(set(failures)),
                "exit_code": exit_code,
                "caught": bool(intended and any(f.startswith(intended) or intended in f for f in failures)),
            }
        if args.mutation:
            # Single-mutation demonstration run: exit with the mutation's own
            # code so a caught mutation is visibly nonzero.
            print(f"mutation {name}: exit {exit_code}")
            for failure in sorted(set(failures)):
                print(f"  reason: {failure}")
            if not failures:
                print("  no invariant failed (mutation not caught)")
            return exit_code

    failures, case_results, fit_results = run_validation(
        contract, fixtures, identity, (contract_path, fixtures_path, identity_path)
    )
    exit_code = 1 if failures else 0
    caught = [m["caught"] for m in mutation_records.values()]
    if not all(caught):
        exit_code = 1

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(["python", str(contract_path.parent.parent.parent / "src" / "inspection" / "validate_ta_v2_design.py")] + sys.argv[1:]),
        "mode": args.mutation or "full",
        "validator": "src/inspection/validate_ta_v2_design.py",
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "fixtures_sha256": hashlib.sha256(fixtures_path.read_bytes()).hexdigest(),
        "identity_sha256": hashlib.sha256(identity_path.read_bytes()).hexdigest(),
        "fixtures_provenance": fixtures.get("provenance"),
        "exit_code": exit_code,
        "summary": {
            "cases_total": len(case_results),
            "cases_passed": sum(1 for c in case_results if c["pass"]),
            "fit_requests_total": len(fit_results),
            "fit_requests_passed": sum(1 for f in fit_results if f["pass"]),
            "mutations_total": len(mutation_records),
            "mutations_caught": sum(1 for m in mutation_records.values() if m["caught"]),
            "failures": sorted(set(failures)),
        },
        "cases": case_results,
        "fit_requests": fit_results,
        "mutations": mutation_records,
        "failures": sorted(set(failures)),
    }
    results_path = Path(args.results)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"cases {results['summary']['cases_passed']}/{results['summary']['cases_total']} passed; "
          f"fit requests {results['summary']['fit_requests_passed']}/{results['summary']['fit_requests_total']} passed; "
          f"mutations caught {results['summary']['mutations_caught']}/{results['summary']['mutations_total']}")
    if failures:
        print("failures:")
        for failure in sorted(set(failures)):
            print(f"  {failure}")
    print(f"results written to {results_path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
