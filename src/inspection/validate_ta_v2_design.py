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
    "delta_ssfr_inst_dex": "(lephare.sfr_med - lephare.mass_med) - (log10(cigale.sfr_inst) - log10(cigale.mass))",
    "delta_ssfr_100_dex": "(lephare.sfr_med - lephare.mass_med) - (log10(cigale.sfr_100myr) - log10(cigale.mass))",
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
ALGEBRAIC_COUPLING_TOLERANCE = 1e-12
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


class _Symbol(str):
    """Dotless identifier that failed variable resolution; compares by name.

    Population predicates compare machine states to bare value tokens
    (``mass_point_state == point_valid``); those tokens are not record
    fields, so they resolve to symbols that compare equal to the state
    string instead of vanishing to NULL.
    """

    __slots__ = ()


def record_resolver(record, constants, states=None):
    """Resolve identifiers against a synthetic record plus declared constants.

    Computed states (e.g. ``mass_point_state``) overlay the record so that
    population predicates can reference them exactly as declared. Dotted
    record paths that are absent resolve to None (so ``is_null`` fires);
    dotless unknown identifiers resolve to comparison symbols.
    """

    def resolve(name):
        if states is not None and name in states:
            return states[name]
        if name in constants:
            return constants[name]
        if name in record:
            return record[name]
        if "." in name:
            return None
        return _Symbol(name)

    return resolve


def evaluate_population(contract, pop_id, record, constants, states):
    """Evaluate a declared population predicate; first declared eligibility wins."""
    population = next(p for p in contract["populations"] if p["id"] == pop_id)
    try:
        value = eval_node(
            parse_expression(population["predicate"]),
            record_resolver(record, constants, states),
        )
    except ExpressionError:
        value = False
    return bool(value)


def select_width(policy, residual, delta, lo, hi):
    """Select the LePhare half-width entering a normalized score (A1.3).

    Returns (width, zero_residual). The declared correct policy selects the
    side by the sign of the conditionally centered residual; scratch
    mutations of the declared policy (symmetric average, raw-delta side)
    flow through here so their behaviour differs and the fixtures catch it.
    """
    if policy == "symmetric_average":
        return (None if lo is None or hi is None else (lo + hi) / 2.0), False
    if policy == "directional_by_delta_sign":
        reference = delta
    else:
        reference = residual
    if reference is not None and reference == 0:
        return None, True
    if reference is None:
        return None, False
    return (lo if reference > 0 else hi), False


def evaluate_directional_score(residual, delta, lo, hi, cig, sys_sigma, guards, policy):
    """Compute a normalized score under the declared width policy (A1.3).

    Returns (score, state, reason). Guards evaluate in the contract's
    declared precedence; a zero residual never bypasses them. Missing,
    negative or non-finite widths never produce a score.
    """
    import math

    width, zero_residual = select_width(policy, residual, delta, lo, hi)
    if "directional_width" in guards:
        for candidate in (lo, hi):
            if candidate is not None and not math.isfinite(candidate):
                return None, "invalid_or_unsupported", "nonfinite_quantile_width"
        if zero_residual:
            if lo is None or hi is None or lo <= 0 or hi <= 0:
                return None, "degenerate_quantile_width", "degenerate_quantile_width"
            width = 0.0
        elif width is None or width <= 0 or not math.isfinite(width):
            return None, "degenerate_quantile_width", "degenerate_quantile_width"
    elif zero_residual:
        width = 0.0 if width is None else width
    if residual is None or cig is None or sys_sigma is None:
        return None, "unsupported_scale", "scale_component_unavailable"
    if width is None or not math.isfinite(width):
        return None, "unsupported_scale", "scale_component_unavailable"
    scale = math.sqrt(width * width + cig * cig + sys_sigma * sys_sigma)
    if "combined_scale_guard" in guards and scale < 1.0e-12:
        return None, "zero_combined_scale", "zero_combined_scale"
    return residual / scale, "point_valid", "none"


def solve_sigma_sys(residuals, scales, constants):
    """Deterministic robust-spread solve for sigma_sys (A1.3, declared policy).

    Solves g(sigma) = 1.4826 * median(|r_i / sqrt(s_i^2 + sigma^2)|) == 1 by
    bisection under the contract's declared tolerance/iteration policy.
    Returns a dict with state, value, reason. Pure; synthetic inputs only.
    """
    import math

    tolerance = float(constants.get("sigma_sys_solve_tolerance", 1e-10))
    max_iter = int(constants.get("sigma_sys_max_iterations", 200))
    upper = float(constants.get("sigma_sys_search_upper_dex", 10.0))
    interval_tol = float(constants.get("sigma_sys_interval_tolerance", 1e-12))

    pairs = [(r, s) for r, s in zip(residuals, scales) if r is not None and s is not None]
    if not pairs:
        return {"state": "invalid_or_unsupported", "value": None, "reason": "no_admissible_systematic_solution"}

    def median(values):
        ordered = sorted(values)
        n = len(ordered)
        mid = n // 2
        return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0

    def g(sigma):
        ratios = [r / math.sqrt(s * s + sigma * sigma) for r, s in pairs]
        center = median(ratios)
        return 1.4826 * median([abs(x - center) for x in ratios])

    def mad_zero():
        ratios = [r / s for r, s in pairs if s != 0]
        if not ratios:
            return True
        center = median(ratios)
        return median([abs(x - center) for x in ratios]) == 0

    if mad_zero():
        return {"state": "invalid_or_unsupported", "value": None, "reason": "zero_residual_spread"}
    g0 = g(0.0)
    if abs(g0 - 1.0) <= tolerance:
        return {"state": "point_valid", "value": 0.0, "reason": "none"}
    if g0 < 1.0:
        return {"state": "invalid_or_unsupported", "value": None, "reason": "no_admissible_systematic_solution"}
    low, high = 0.0, upper
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        if high - low <= interval_tol:
            break
        if g(mid) >= 1.0:
            low = mid
        else:
            high = mid
    sigma = (low + high) / 2.0
    if abs(g(sigma) - 1.0) > tolerance:
        return {"state": "invalid_or_unsupported", "value": None, "reason": "sigma_sys_solve_failed"}
    return {"state": "point_valid", "value": sigma, "reason": "none"}


def output_decl(contract, name):
    """Return the declared output block for ``name`` (or None)."""
    for output in contract["outputs"]:
        if output["name"] == name:
            return output
    return None


def evaluate_case(contract, case, scenarios):
    """Compute every declared output for one synthetic case record.

    Guard precedence follows contract.guard_precedence: population guards
    first, then point-domain guards, then scale/uncertainty guards, then
    arithmetic. A zero residual never bypasses an earlier guard. Population
    membership and output gating read the contract's declared predicates and
    ``population_gate``/``guards`` fields, so a scratch-copy mutation of those
    declarations changes behaviour and is caught by the fixtures (P2R-06a
    A1.2: the evaluator may not ignore the declared predicate).
    """
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
            state, reason = evaluate_rule(machine, record, constants, states)
        states[name] = state
        states[output_state] = state
        outputs[output_state] = state
        if output_reason:
            outputs[output_reason] = reason
        return state, reason

    def eval_formula(text):
        try:
            return eval_node(parse_expression(text), record_resolver(record, constants, states))
        except ExpressionError:
            return None

    def population_gate_ok(output_name):
        decl = output_decl(contract, output_name) or {}
        gate = decl.get("population_gate")
        if gate is None:
            return True, "none"
        member = evaluate_population(contract, gate, record, constants, states)
        return member, ("none" if member else "not_in_population")

    def guard_list(output_name):
        decl = output_decl(contract, output_name) or {}
        return decl.get("guards") or []

    # --- mass path -------------------------------------------------------
    run_machine("mass_point", "mass_point_state", "mass_point_reason")
    outputs["selection_type0"] = bool(
        eval_node(parse_expression("lephare.type == 0"), record_resolver(record, constants, states))
    )
    outputs["delta_mass_dex"] = (
        eval_formula(declared_formulas["delta_mass_dex"])
        if outputs["mass_point_state"] == "point_valid"
        else None
    )
    outputs["pop_mass"] = evaluate_population(contract, "POP-MASS", record, constants, states)
    outputs["pop_mass_reason"] = "none" if outputs["pop_mass"] else "not_in_population"

    requested_cell = None
    if scenario["model_kind"] == "S0-constant":
        # AI NOTE: S0 scenarios declare only the per-timescale SFR constants;
        # mass-center outputs stay absent rather than being fabricated.
        expected_delta, support = None, None
    else:
        expected_delta, support, requested_cell = evaluate_center(scenario, record, contract)
    outputs["expected_delta_mass_dex"] = (
        expected_delta if outputs["pop_mass"] else None
    )
    outputs["center_support"] = support if outputs["pop_mass"] else None
    outputs["center_requested_cell"] = requested_cell if outputs["pop_mass"] else None
    member_mass, mass_reason = population_gate_ok("residual_mass_dex")
    outputs["residual_mass_dex"] = (
        outputs["delta_mass_dex"] - expected_delta
        if member_mass
        and outputs["delta_mass_dex"] is not None
        and expected_delta is not None
        else None
    )

    scale_state, scale_reason = run_machine("mass_scale", "mass_scale_state", "mass_scale_reason")
    score_guards = guard_list("score_mass")
    mass_policy = contract["scales"]["mass_scale"]["width_selection"]["policy"]
    scale_ok_for_components = (
        scale_state == "point_valid" or "scale_state" not in score_guards
    )
    if scale_ok_for_components and outputs["mass_point_state"] == "point_valid":
        outputs["sigma_mass_lp_lo_dex"] = eval_formula("lephare.mass_med - lephare.mass_l68")
        outputs["sigma_mass_lp_hi_dex"] = eval_formula("lephare.mass_u68 - lephare.mass_med")
        outputs["sigma_mass_cig_dex"] = eval_formula("cigale.mass_err / (cigale.mass * ln10)")
    else:
        outputs["sigma_mass_lp_lo_dex"] = None
        outputs["sigma_mass_lp_hi_dex"] = None
        outputs["sigma_mass_cig_dex"] = None
    outputs["sigma_sys_mass_dex"] = scenario.get("sigma_sys_mass_dex")
    score_member, _ = population_gate_ok("score_mass")
    if not score_member:
        outputs["score_mass"], outputs["score_mass_state"] = None, "not_in_population"
        outputs["score_mass_reason"] = mass_reason
    elif (
        "scale_state" in score_guards
        and scale_state != "point_valid"
    ):
        outputs["score_mass"], outputs["score_mass_reason"] = None, scale_reason
        outputs["score_mass_state"] = scale_state
    elif outputs["mass_point_state"] != "point_valid":
        outputs["score_mass"], outputs["score_mass_reason"] = None, outputs["mass_point_reason"]
        outputs["score_mass_state"] = outputs["mass_point_state"]
    elif outputs["residual_mass_dex"] is None:
        outputs["score_mass"], outputs["score_mass_state"] = None, "unsupported_scale"
        outputs["score_mass_reason"] = "center_or_delta_unavailable"
    else:
        score_value, score_state, score_reason = evaluate_directional_score(
            outputs["residual_mass_dex"],
            outputs["delta_mass_dex"],
            outputs["sigma_mass_lp_lo_dex"],
            outputs["sigma_mass_lp_hi_dex"],
            outputs["sigma_mass_cig_dex"],
            outputs["sigma_sys_mass_dex"],
            score_guards,
            mass_policy,
        )
        outputs["score_mass"] = score_value
        outputs["score_mass_state"] = score_state
        outputs["score_mass_reason"] = score_reason

    # --- SFR paths (T in {inst, 100}; independent of POP-MASS) -----------
    for machine, state_name, reason_name, delta_name in [
        ("sfr_inst_point", "sfr_inst_state", "sfr_inst_reason", "delta_sfr_inst_dex"),
        ("sfr_100_point", "sfr_100_state", "sfr_100_reason", "delta_sfr_100_dex"),
    ]:
        state, _ = run_machine(machine, state_name, reason_name)
        outputs[delta_name] = (
            eval_formula(declared_formulas[delta_name]) if state == "point_comparable" else None
        )
    outputs["pop_sfr_inst"] = evaluate_population(contract, "POP-SFR-INST", record, constants, states)
    outputs["pop_sfr_inst_reason"] = "none" if outputs["pop_sfr_inst"] else "not_in_population"
    outputs["pop_sfr_100"] = evaluate_population(contract, "POP-SFR-100", record, constants, states)
    outputs["pop_sfr_100_reason"] = "none" if outputs["pop_sfr_100"] else "not_in_population"
    outputs["timescale_caveat_lephare"] = True

    s0 = scenarios.get("SYNTH-S0", scenario)
    outputs["expected_delta_sfr_inst_dex"] = (
        s0.get("constant_value_inst") if outputs["pop_sfr_inst"] else None
    )
    outputs["expected_delta_sfr_100_dex"] = (
        s0.get("constant_value_100") if outputs["pop_sfr_100"] else None
    )
    for suffix, delta_name, residual_name, expected_key, pop_flag in [
        ("inst", "delta_sfr_inst_dex", "residual_sfr_inst_dex", "constant_value_inst", "pop_sfr_inst"),
        ("100", "delta_sfr_100_dex", "residual_sfr_100_dex", "constant_value_100", "pop_sfr_100"),
    ]:
        member = outputs[pop_flag]
        outputs[residual_name] = (
            outputs[delta_name] - s0[expected_key]
            if member and outputs[delta_name] is not None and s0.get(expected_key) is not None
            else None
        )
    outputs["sigma_sfr_lp_lo_dex"] = eval_formula("lephare.sfr_med - lephare.sfr_l68")
    outputs["sigma_sfr_lp_hi_dex"] = eval_formula("lephare.sfr_u68 - lephare.sfr_med")
    sfr_policy = contract["scales"]["sfr_scale"]["width_selection"]["policy"]

    for suffix, point_state, scale_machine, cig_sigma, sys_sigma, cig_formula, delta_name in [
        ("inst", "sfr_inst_state", "sfr_inst_scale", "sigma_sfr_cig_inst_dex",
         "sigma_sys_sfr_inst_dex", "cigale.sfr_inst_err / (cigale.sfr_inst * ln10)", "delta_sfr_inst_dex"),
        ("100", "sfr_100_state", "sfr_100_scale", "sigma_sfr_cig_100_dex",
         "sigma_sys_sfr_100_dex", "cigale.sfr_100myr_err / (cigale.sfr_100myr * ln10)", "delta_sfr_100_dex"),
    ]:
        scale_state, scale_reason = run_machine(
            scale_machine, f"sfr_{suffix}_scale_state", f"sfr_{suffix}_scale_reason"
        )
        outputs[cig_sigma] = (
            eval_formula(cig_formula) if outputs[point_state] == "point_comparable" else None
        )
        outputs[sys_sigma] = scenario.get(sys_sigma)
        score_name = f"score_sfr_{suffix}"
        residual_name = f"residual_sfr_{suffix}_dex"
        score_guards = guard_list(score_name)
        member = outputs[f"pop_sfr_{suffix}"]
        if not member:
            outputs[score_name] = None
            outputs[f"{score_name}_state"] = "not_in_population"
            outputs[f"{score_name}_reason"] = "not_in_population"
        elif "scale_state" in score_guards and scale_state != "point_valid":
            outputs[score_name] = None
            outputs[f"{score_name}_state"] = scale_state
            outputs[f"{score_name}_reason"] = scale_reason
        elif outputs[point_state] != "point_comparable":
            outputs[score_name] = None
            outputs[f"{score_name}_state"] = outputs[point_state]
            outputs[f"{score_name}_reason"] = outputs[f"sfr_{suffix}_reason"]
        elif outputs[residual_name] is None:
            outputs[score_name] = None
            outputs[f"{score_name}_state"] = "unsupported_scale"
            outputs[f"{score_name}_reason"] = "scale_component_unavailable"
        else:
            score_value, score_state, score_reason = evaluate_directional_score(
                outputs[residual_name],
                outputs[delta_name],
                outputs["sigma_sfr_lp_lo_dex"],
                outputs["sigma_sfr_lp_hi_dex"],
                outputs[cig_sigma],
                outputs[sys_sigma],
                score_guards,
                sfr_policy,
            )
            outputs[score_name] = score_value
            outputs[f"{score_name}_state"] = score_state
            outputs[f"{score_name}_reason"] = score_reason

    for machine, state_name, reason_name, delta_name in [
        ("ssfr_inst_view", "ssfr_inst_state", "ssfr_inst_reason", "delta_ssfr_inst_dex"),
        ("ssfr_100_view", "ssfr_100_state", "ssfr_100_reason", "delta_ssfr_100_dex"),
    ]:
        state, _ = run_machine(machine, state_name, reason_name)
        outputs[delta_name] = (
            eval_formula(declared_formulas[delta_name]) if state == "point_valid" else None
        )
    outputs["pop_ssfr_inst"] = bool(outputs["selection_type0"] and outputs["ssfr_inst_state"] == "point_valid")
    outputs["pop_ssfr_100"] = bool(outputs["selection_type0"] and outputs["ssfr_100_state"] == "point_valid")
    outputs["not_independent_of_mass_and_sfr"] = True

    run_machine("ctx_lp_ssfr_point", "ctx_lp_ssfr_point_state", "ctx_lp_ssfr_point_reason")
    ctx_decl = output_decl(contract, "ctx_lp_ssfr_nonadditivity_dex") or {}
    outputs["ctx_lp_ssfr_nonadditivity_dex"] = (
        eval_formula(ctx_decl.get("formula", "lephare.ssfr_med - (lephare.sfr_med - lephare.mass_med)"))
        if outputs["ctx_lp_ssfr_point_state"] == "point_valid"
        else None
    )
    # AI NOTE: the sSFR score is unsupported by declared evidence (unknown
    # mass-SFR error correlation); it stays NULL rather than assuming
    # independence, per the contract's unsupported_correlated_errors state.
    outputs["score_ssfr_inst"] = None
    outputs["score_ssfr_100"] = None

    for output in contract["outputs"]:
        if output.get("kind") == "context_passthrough" and "source" in output:
            outputs[output["name"]] = record.get(output["source"])
    return outputs


def evaluate_rule(machine, record, constants, states=None):
    """Apply a state machine's ordered rules; the first match supplies state and reason."""
    for rule in machine["rules"]:
        predicate = str(rule.get("when", "true"))
        if predicate == "true":
            return rule["state"], rule.get("reason", "none")
        if predicate == "false":
            continue
        try:
            value = eval_node(parse_expression(predicate), record_resolver(record, constants, states))
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


def evaluate_center(scenario, record, contract=None):
    """Evaluate a synthetic center scenario; returns (expected_delta, support, requested).

    Declared C1 scenarios carry synthetic support counts; when the contract
    declares ``support_enforcement: center_min_cell_support`` the counts
    drive the cell/z_fallback/global_fallback hierarchy (A1.5). Scenarios
    of kind C1-fitted resolve through a model built from synthetic rows by
    ``build_center_from_rows`` under the same hierarchy.
    """
    kind = scenario["model_kind"]
    if kind == "C0-constant":
        return scenario["constant_value"], "global_fallback", None
    if kind == "S0-constant":
        raise ExpressionError("S0 scenarios are read per-timescale, not through this path")
    if kind in ("C1-conditional-binned-median", "C1-fitted"):
        z = record.get("lephare.zpdf_med")
        mag = record.get("photometry_primary.mag_auto_f444w")
        enforce = False
        min_support = 0
        if contract is not None:
            c1 = contract["centers"]["mass_center"]["comparison_set"][1]
            enforce = c1.get("support_enforcement") == "center_min_cell_support"
            min_support = int(
                {c["name"]: c["value"] for c in contract["declared_constants"]}[
                    "center_min_cell_support"
                ]
            )
        if kind == "C1-fitted":
            model = scenario["_built_model"]
            return resolve_center_model(model, z, mag, min_support)
        if z is None or mag is None:
            return scenario["global_constant"], "out_of_hull", None
        z_edges, mag_edges = scenario["z_bin_edges"], scenario["mag_bin_edges"]

        zi, mi = _bin_index(z, z_edges), _bin_index(mag, mag_edges)
        if zi is None or mi is None:
            return scenario["global_constant"], "out_of_hull", None
        requested = f"{zi}|{mi}"
        cell = scenario["cell_values"].get(requested)
        count = scenario.get("support_counts", {}).get(requested, 0)
        if cell is not None and ((enforce and count >= min_support) or not enforce):
            return cell, "cell", requested
        z_only = scenario["z_only_values"].get(str(zi))
        zc = scenario.get("z_only_support_counts", {}).get(str(zi), 0)
        if z_only is not None and ((enforce and zc >= min_support) or not enforce):
            return z_only, "z_fallback", requested
        return scenario["global_constant"], "global_fallback", requested
    raise ExpressionError(f"unknown scenario kind {kind!r}")


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


def _median(values):
    """Deterministic median: even counts average the two middle order statistics."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


def _quantile(sorted_values, q):
    """Deterministic linear-interpolation quantile on pre-sorted values."""
    import math

    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    h = (n - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, n - 1)
    frac = h - lo
    return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])


def _collapse_edges(edges):
    """Drop duplicate/non-increasing edges; record effective bins via length."""
    collapsed = []
    for edge in edges:
        if not collapsed or edge > collapsed[-1]:
            collapsed.append(edge)
    return collapsed


def _bin_index(value, edges):
    """Left-closed/right-open bin lookup; the final endpoint is included."""
    for index in range(len(edges) - 1):
        if edges[index] <= value < edges[index + 1]:
            return index
    if value == edges[-1]:
        return len(edges) - 2
    return None


def partition_guard(rows, assignment_rows):
    """Shared partition/duplicate guards for every synthetic fitter (A1.5/A1.6).

    Every fitted row needs an explicit, valid ``development`` assignment;
    missing assignments reject as unassigned_partition, unknown labels,
    conflicting assignments and duplicate training IDs reject, and any
    validation/holdout ID in the request rejects.
    """
    reasons = []
    assignment = {}
    for entry in assignment_rows:
        cid = entry["catalog_id"]
        if cid in assignment and assignment[cid] != entry["split"]:
            reasons.append(f"catalog_id {cid} appears in two partitions")
        assignment[cid] = entry["split"]
    for cid, split in sorted(assignment.items()):
        if split not in ("development", "validation", "holdout"):
            reasons.append(f"unknown partition label {split} for catalog_id {cid}")
    seen = set()
    for row in rows:
        cid = row["catalog_id"]
        if cid in seen:
            reasons.append(f"duplicate training rows for catalog_id {cid}")
        seen.add(cid)
    for cid in sorted(seen):
        if cid not in assignment:
            reasons.append(f"unassigned_partition catalog_id {cid}")
        elif assignment[cid] in ("validation", "holdout"):
            reasons.append(f"validation or holdout catalog_id {cid} in fit request")
    return reasons


def build_center_from_rows(construction, contract, force_no_edge=False):
    """Pure synthetic construction of a C1 center model (A1.5).

    Builds quantile edges (plus the forced high-redshift edge when strictly
    inside the development support), cell medians, z-only medians, global
    constant, and unique-source support counts from synthetic fixture rows
    only. Reads declared contract parameters (z/mag bin counts, forced
    edge, min support) rather than hardcoded mirrors; has no database
    path. Returns (model, guard_reasons).
    """
    import math

    constants = {c["name"]: c["value"] for c in contract["declared_constants"]}
    c1 = contract["centers"]["mass_center"]["comparison_set"][1]
    z_bins = int(c1["z_quantile_bins"])
    mag_bins = int(c1["mag_quantile_bins"])
    forced = constants.get("forced_highz_edge")
    if force_no_edge:
        forced = None

    rows = expand_construction_rows(construction)
    guard_reasons = partition_guard(rows, construction["partition_assignment"])

    points = []
    for row in rows:
        z = row.get("lephare.zpdf_med")
        mag = row.get("photometry_primary.mag_auto_f444w")
        if z is None or mag is None or not math.isfinite(z) or not math.isfinite(mag):
            return {"state": "invalid", "reason": "nonfinite_or_missing_covariate"}, guard_reasons
        points.append((z, mag, row["delta_mass_dex"], row["catalog_id"]))

    zs = sorted(p[0] for p in points)
    mags = sorted(p[1] for p in points)
    z_edges = _collapse_edges([_quantile(zs, k / z_bins) for k in range(z_bins + 1)])
    mag_edges = _collapse_edges([_quantile(mags, k / mag_bins) for k in range(mag_bins + 1)])
    forced_inserted = False
    if forced is not None and zs[0] < forced < zs[-1]:
        z_edges = _collapse_edges(sorted(z_edges + [float(forced)]))
        forced_inserted = True

    cells, z_only = {}, {}
    for z, mag, delta, cid in points:
        zi = _bin_index(z, z_edges)
        mi = _bin_index(mag, mag_edges)
        if zi is None or mi is None:
            return {"state": "invalid", "reason": "covariate_outside_support"}, guard_reasons
        cells.setdefault(f"{zi}|{mi}", {}).setdefault(cid, delta)
        z_only.setdefault(str(zi), {}).setdefault(cid, delta)

    model = {
        "state": "ok",
        "z_bin_edges": z_edges,
        "mag_bin_edges": mag_edges,
        "effective_z_bins": len(z_edges) - 1,
        "effective_mag_bins": len(mag_edges) - 1,
        "forced_edge_inserted": forced_inserted,
        "cell_values": {key: _median(list(members.values())) for key, members in cells.items()},
        "support_counts": {key: len(members) for key, members in cells.items()},
        "z_only_values": {key: _median(list(members.values())) for key, members in z_only.items()},
        "z_only_support_counts": {key: len(members) for key, members in z_only.items()},
        "global_constant": _median([p[2] for p in points]),
        "n_rows": len(points),
    }
    return model, guard_reasons


def expand_construction_rows(construction):
    """Expand the declared deterministic row blocks into concrete rows."""
    rule = construction.get("delta_rule", {})
    base_id = int(construction.get("base_catalog_id", 950000))
    rows = []
    next_id = base_id
    for block in construction["row_blocks"]:
        repeat = int(block.get("repeat", 1))
        z = block["lephare.zpdf_med"]
        mag = block["photometry_primary.mag_auto_f444w"]
        slope = rule.get("slope_below", 0.0) if z < rule.get("z_boundary", 5.5) else rule.get(
            "slope_above", 0.0
        )
        delta = rule.get("intercept", 0.0) + slope * (mag - rule.get("pivot_mag", 24.0))
        for _ in range(repeat):
            rows.append({
                "catalog_id": next_id,
                "lephare.zpdf_med": z,
                "photometry_primary.mag_auto_f444w": mag,
                "delta_mass_dex": delta,
            })
            next_id += 1
    assignment = [{"catalog_id": r["catalog_id"], "split": "development"} for r in rows]
    construction["partition_assignment"] = construction.get("partition_assignment", assignment)
    return rows


def resolve_center_model(model, z, mag, min_support):
    """Resolve a fitted center model with the support hierarchy (A1.5)."""
    if z is None or mag is None:
        return model["global_constant"], "out_of_hull", None
    zi = _bin_index(z, model["z_bin_edges"])
    mi = _bin_index(mag, model["mag_bin_edges"])
    if zi is None or mi is None:
        return model["global_constant"], "out_of_hull", None
    requested = f"{zi}|{mi}"
    count = model["support_counts"].get(requested, 0)
    if count >= min_support:
        return model["cell_values"][requested], "cell", requested
    zc = model["z_only_support_counts"].get(str(zi), 0)
    if zc >= min_support:
        return model["z_only_values"][str(zi)], "z_fallback", requested
    return model["global_constant"], "global_fallback", requested


def run_binning_demonstrations(fixtures, contract, built_models):
    """Slope-reversal demonstration: with vs without the forced edge (A1.5)."""
    import math

    results = []
    failures = []
    for demo in fixtures.get("binning_demonstrations", []):
        construction = fixtures["center_constructions"][demo["construction"]]
        model_with, _ = built_models[demo["construction"]], None
        model_without, _ = build_center_from_rows(construction, contract, force_no_edge=True)
        tolerance = float(demo["tolerance"])
        with_residuals, without_residuals = [], []
        for probe in demo["probes"]:
            min_support = int(
                {c["name"]: c["value"] for c in contract["declared_constants"]}[
                    "center_min_cell_support"
                ]
            )
            value_with, support_with, _ = resolve_center_model(
                model_with, probe["lephare.zpdf_med"], probe["photometry_primary.mag_auto_f444w"], min_support
            )
            value_without, _, _ = resolve_center_model(
                model_without, probe["lephare.zpdf_med"], probe["photometry_primary.mag_auto_f444w"], min_support
            )
            with_residuals.append(abs(probe["delta_mass_dex"] - value_with))
            without_residuals.append(abs(probe["delta_mass_dex"] - value_without))
        max_with = max(with_residuals)
        min_without = min(without_residuals)
        ok = max_with <= tolerance and min_without > tolerance
        if not ok:
            failures.append(f"binning_demonstration:{demo['id']}")
        results.append({
            "id": demo["id"], "tolerance": tolerance,
            "max_abs_residual_with_edge": max_with,
            "min_abs_residual_without_edge": min_without,
            "adequate_support_declared": demo.get("adequate_support_declared"),
            "pass": ok,
        })
    return failures, results


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


def run_math_counterexamples(fixtures):
    """Check the declared deterministic mathematical counterexamples (A1.4).

    MATH-1 solves the median of Y = X + Z for independent Exp(1) X, Z by
    bisection (exp(-m)(1+m) = 1/2) and verifies the median non-additivity
    2*ln2 - m against the declared expected value: a provably unimodal
    (log-concave) distribution with nonzero median non-additivity. No
    sampled data is involved; the check is analytic and deterministic.
    """
    import math

    results = []
    failures = []
    for check in fixtures.get("mathematical_counterexamples", []):
        if check["id"] != "MATH-1":
            continue
        low, high = 0.0, 5.0
        f = lambda m: math.exp(-m) * (1.0 + m) - 0.5  # noqa: E731
        for _ in range(200):
            mid = (low + high) / 2.0
            if f(mid) > 0:
                low = mid
            else:
                high = mid
        median_y = (low + high) / 2.0
        median_x = math.log(2.0)
        observed = 2.0 * median_x - median_y
        expected = check["expected_nonadditivity"]
        ok = (
            abs(observed - expected) <= 1e-9
            and median_y > median_x
            and abs(observed - check["checks"]["approx_value"]) < 1e-4
        )
        if not ok:
            failures.append(f"math_counterexample:{check['id']}")
        results.append({
            "id": check["id"], "description": check["description"],
            "expected_nonadditivity": expected, "observed_nonadditivity": observed,
            "median_y": median_y, "median_x": median_x, "pass": ok,
        })
    return failures, results


def check_algebraic_couplings(contract, outputs, case_id):
    """Numerically enforce every declared algebraic coupling (A1.4, R1).

    Each output carrying ``coupling_expr`` has that expression evaluated
    against the computed outputs; where both sides are defined the identity
    must hold to absolute tolerance 1e-12 on full-precision values. A
    declared identity that fails is a validation failure, never prose.
    """
    failures = []

    def resolver(name):
        return outputs.get(name)

    for output in contract["outputs"]:
        expression = output.get("coupling_expr")
        if not expression:
            continue
        try:
            tree = parse_expression(expression)
        except ExpressionError as exc:
            failures.append(f"coupling_unparsable:{output['name']}:{exc}")
            continue
        if not isinstance(tree, tuple) or tree[0] != "cmp" or tree[1] != "==":
            failures.append(f"coupling_malformed:{output['name']}")
            continue
        identifiers = collect_identifiers(tree, set())
        if any(outputs.get(name) is None for name in identifiers):
            continue  # checked only where both sides are defined
        try:
            left = eval_node(tree[2], resolver)
            right = eval_node(tree[3], resolver)
        except ExpressionError:
            left = right = None
        held = (
            left is not None
            and right is not None
            and (
                left == right
                or (
                    isinstance(left, (int, float))
                    and isinstance(right, (int, float))
                    and abs(left - right) <= ALGEBRAIC_COUPLING_TOLERANCE
                )
            )
        )
        if not held:
            failures.append(f"algebraic_coupling_violated:{output['name']}:{case_id}")
    return failures


def pop_mass_consistency(contract):
    """Compare the POP-MASS predicate and echo against input-contract.md (P2R-06a R3).

    The feature contract's predicate and its echo of the input contract's
    conditions must agree with the POP-MASS row actually present in
    input-contract.md section 6, so the two artefacts cannot drift apart.
    """
    failures = []
    population = next(
        (p for p in contract["populations"] if p["id"] == "POP-MASS"), None
    )
    if population is None:
        return ["pop_mass_missing"]
    predicate = population.get("predicate", "")
    echo = population.get("input_contract_echo", "")
    required_dsl = [
        "lephare.type == 0",
        "mass_point_state == point_valid",
        "is_null(cigale.mass_err) == false",
        "cigale.mass_err >= 0",
    ]
    for fragment in required_dsl:
        if fragment not in predicate:
            failures.append(f"pop_mass_predicate_condition_missing:{fragment}")
    if not INPUT_CONTRACT_MD.exists():
        failures.append("input_contract_absent")
        return failures
    text = INPUT_CONTRACT_MD.read_text()
    row = next(
        (line for line in text.splitlines() if line.strip().startswith("| `POP-MASS`")),
        "",
    )
    normalized_row = " ".join(row.split())
    required_shared = [
        "lephare.type = 0",
        "point_valid",
        "> 0",
        "error present and ≥ 0",
    ]
    for fragment in required_shared:
        if fragment not in normalized_row:
            failures.append(f"pop_mass_input_contract_condition_missing:{fragment}")
        if " ".join(fragment.split()) not in " ".join(echo.split()):
            failures.append(f"pop_mass_echo_drift:{fragment}")
    return failures


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

    # P2R-06a A1.2: every centered residual and normalized residual output
    # must declare the population gate that controls its emission, and every
    # normalized residual must declare the full guard list, so removing a
    # declared gate from a scratch copy is a structural failure before any
    # fixture runs.
    for output in contract["outputs"]:
        if output.get("kind") in ("centered_residual", "normalized_residual"):
            if not output.get("population_gate"):
                failures.append(f"population_gate_missing:{output['name']}")
        if output.get("kind") == "normalized_residual":
            guards = output.get("guards") or []
            for guard in (
                "population", "point_state", "scale_state", "directional_width",
                "combined_scale_guard",
            ):
                if guard not in guards:
                    failures.append(f"guard_missing:{output['name']}:{guard}")
        if output.get("kind") in ("uncertainty",) and output["name"].startswith("sigma_"):
            if "_lp_dex" in output["name"]:
                failures.append(f"symmetric_lp_output_present:{output['name']}")
        # P2R-06a A1.4: context outputs are never rankable, and native
        # lephare.ssfr_med appears in no rankable output and no
        # raw_disagreement/derived_view formula.
        if output.get("context_only") and output.get("rankable") is not False:
            failures.append(f"context_output_rankable:{output['name']}")
        if output.get("rankable") is True or output.get("rankable") in ("primary", "secondary"):
            identifiers = set()
            if output.get("formula"):
                try:
                    collect_identifiers(parse_expression(output["formula"]), identifiers)
                except ExpressionError:
                    identifiers = set()
            if "lephare.ssfr_med" in identifiers:
                failures.append(f"native_ssfr_in_rankable_formula:{output['name']}")
        if output.get("kind") in ("raw_disagreement", "derived_view") and output.get("formula"):
            identifiers = set()
            try:
                collect_identifiers(parse_expression(output["formula"]), identifiers)
            except ExpressionError:
                identifiers = set()
            if "lephare.ssfr_med" in identifiers:
                failures.append(f"native_ssfr_in_delta_formula:{output['name']}")

    failures.extend(pop_mass_consistency(contract))

    # P2R-06a A1.5: the C1 center must declare support enforcement against
    # center_min_cell_support and the forced high-redshift edge must exist
    # as a declared constant with its rationale.
    c1_entry = contract["centers"]["mass_center"]["comparison_set"][1]
    if c1_entry.get("support_enforcement") != "center_min_cell_support":
        failures.append("support_enforcement_missing")
    constant_names = {c["name"] for c in contract["declared_constants"]}
    if "forced_highz_edge" not in constant_names:
        failures.append("declared_constant_missing:forced_highz_edge")
    if not c1_entry.get("z_quantile_bins") or not c1_entry.get("mag_quantile_bins"):
        failures.append("binning_parameters_missing")

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
    elif kind == "drop_machine_rule_matching":
        machine = contract["state_machines"][action["machine"]]
        machine["rules"] = [
            r for r in machine["rules"] if action["match"] not in str(r.get("reason", ""))
        ]
    elif kind == "drop_partition_rule":
        rules = contract["partition_use"]["rules"]
        contract["partition_use"]["rules"] = [r for r in rules if action["match"] not in r]
    elif kind == "add_output":
        contract["outputs"].append(copy.deepcopy(action["output"]))
    elif kind == "change_identity_hash":
        identity["tracked_evidence_files"][0]["sha256"] = action["value"]
    elif kind == "add_center_covariate":
        contract["centers"][action["center"]]["comparison_set"][1]["covariates"].append(action["covariate"])
    elif kind == "edit_population_predicate":
        population = next(
            p for p in contract["populations"] if p["id"] == action["population"]
        )
        population["predicate"] = action["predicate"]
    elif kind == "edit_pop_mass_echo":
        population = next(p for p in contract["populations"] if p["id"] == "POP-MASS")
        population["input_contract_echo"] = action["echo"]
    elif kind == "remove_output_field":
        for output in contract["outputs"]:
            if output["name"] == action["output"]:
                output.pop(action["field"], None)
    elif kind == "edit_output_guards":
        for output in contract["outputs"]:
            if output["name"] == action["output"]:
                output["guards"] = list(action["guards"])
    elif kind == "edit_scales_policy":
        contract["scales"][action["scale"]]["width_selection"]["policy"] = action["policy"]
    elif kind == "set_output_coupling":
        for output in contract["outputs"]:
            if output["name"] == action["output"]:
                output["coupling_expr"] = action["coupling_expr"]
                output["algebraic_coupling"] = action.get(
                    "algebraic_coupling", output.get("algebraic_coupling")
                )
    elif kind == "set_output_field":
        for output in contract["outputs"]:
            if output["name"] == action["output"]:
                output[action["field"]] = action["value"]
    elif kind == "set_center_field":
        entry = contract["centers"][action["center"]]["comparison_set"][action["index"]]
        entry[action["field"]] = action["value"]
    elif kind == "remove_declared_constant":
        contract["declared_constants"] = [
            c for c in contract["declared_constants"] if c["name"] != action["name"]
        ]
    else:
        raise ValueError(f"unknown mutation kind {kind!r}")


def run_validation(contract, fixtures, identity, paths):
    """Run cases, fit requests, structural and identity checks; return failure codes and details."""
    failures = []
    scenarios = fixtures["declared_center_scenarios"]
    built_models = {}
    for name, construction in fixtures.get("center_constructions", {}).items():
        model, guard_reasons = build_center_from_rows(construction, contract)
        built_models[name] = model
        for reason in guard_reasons:
            failures.append(f"construction_partition:{name}:{reason}")
        if model.get("state") != "ok":
            failures.append(f"construction_invalid:{name}:{model.get('reason')}")
    for scenario in scenarios.values():
        if scenario.get("model_kind") == "C1-fitted":
            scenario["_built_model"] = built_models[scenario["construction"]]
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
        failures.extend(check_algebraic_couplings(contract, outputs, case["id"]))
        observed = {key: outputs.get(key) for key in case["expect"]}
        case_results.append(
            {"id": case["id"], "description": case["description"], "expected": case["expect"],
             "observed": observed, "pass": not mismatches}
        )
    fit_results = check_fit_requests(fixtures)
    for fit in fit_results:
        if not fit["pass"]:
            failures.append(f"fit_request:{fit['id']}")
    solve_results = []
    constants = {c["name"]: c["value"] for c in contract["declared_constants"]}
    for check in fixtures.get("sigma_sys_solve_checks", []):
        outcome = solve_sigma_sys(check["residuals"], check["scales"], constants)
        expected = check["expect"]
        ok = (
            outcome["state"] == expected.get("state")
            and outcome["reason"] == expected.get("reason", "none")
            and (
                expected.get("value") is None
                or (
                    outcome["value"] is not None
                    and abs(outcome["value"] - expected["value"])
                    <= NUMERIC_TOLERANCE * max(1.0, abs(expected["value"]))
                )
            )
        )
        if not ok:
            failures.append(f"sigma_sys_solve:{check['id']}")
        solve_results.append(
            {"id": check["id"], "description": check["description"],
             "expected": expected, "observed": outcome, "pass": ok}
        )
    math_failures, math_results = run_math_counterexamples(fixtures)
    failures.extend(math_failures)
    demo_failures, demo_results = run_binning_demonstrations(fixtures, contract, built_models)
    failures.extend(demo_failures)
    failures.extend(structural_checks(contract, fixtures))
    failures.extend(identity_checks(identity, *paths))
    return failures, case_results, fit_results, solve_results, math_results, demo_results


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
        failures, case_results, fit_results, solve_results, math_results, demo_results = run_validation(
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

    failures, case_results, fit_results, solve_results, math_results, demo_results = run_validation(
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
            "sigma_sys_checks_total": len(solve_results),
            "sigma_sys_checks_passed": sum(1 for s in solve_results if s["pass"]),
            "failures": sorted(set(failures)),
        },
        "cases": case_results,
        "fit_requests": fit_results,
        "sigma_sys_solve_checks": solve_results,
        "mathematical_counterexamples": math_results,
        "binning_demonstrations": demo_results,
        "mutations": mutation_records,
        "failures": sorted(set(failures)),
    }
    results_path = Path(args.results)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"cases {results['summary']['cases_passed']}/{results['summary']['cases_total']} passed; "
          f"fit requests {results['summary']['fit_requests_passed']}/{results['summary']['fit_requests_total']} passed; "
          f"sigma_sys checks {results['summary']['sigma_sys_checks_passed']}/{results['summary']['sigma_sys_checks_total']} passed; "
          f"mutations caught {results['summary']['mutations_caught']}/{results['summary']['mutations_total']}")
    if failures:
        print("failures:")
        for failure in sorted(set(failures)):
            print(f"  {failure}")
    print(f"results written to {results_path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
