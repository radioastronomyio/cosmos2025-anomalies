#!/usr/bin/env python3
"""
Script Name  : test_reconciliation_core_v11.py
Description  : Test deterministic Gate 3.11 sampling and exact values
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises the pure, loader-independent value contract used by the live
reconciler. Expectations are hand-derived rather than built by production
helpers.

Usage
-----
    pytest tests/test_reconciliation_core_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import importlib.util
import json
import math
import os
import stat
import sys
from pathlib import Path

import pytest


# =============================================================================
# Configuration and loader
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "reconciliation_core_v11.py"


def _module():
    """Load production after test start so the absent core is an honest RED."""
    assert MODULE_PATH.exists(), "Gate 3.11 reconciliation core is missing"
    spec = importlib.util.spec_from_file_location(
        "reconciliation_core_v11", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# =============================================================================
# Deterministic sampling
# =============================================================================


def test_ranked_sample_uses_stable_sha256_order_and_sorted_output() -> None:
    """Changing hash input, replacement, or output ordering must fail."""
    module = _module()

    assert module.ranked_sample(10, 3, 1) == (3, 8, 9)
    assert module.sample_digest((3, 8, 9)) == (
        "b098535e51620edc9419bb94f9d2e940c573f0a8c7d3de116d0eede7ccf5689f"
    )
    assert module.ranked_sample(4, 4, 7) == (0, 1, 2, 3)


def test_ranked_sample_rejects_invalid_population_size_and_seed() -> None:
    """Invalid sampling bounds must fail before silently changing coverage."""
    module = _module()

    for arguments in ((0, 1, 1), (10, 0, 1), (10, 11, 1), (10, 2, -1)):
        with pytest.raises(ValueError, match="sample boundary"):
            module.ranked_sample(*arguments)
    with pytest.raises(ValueError, match="sample boundary"):
        module.ranked_sample(10, 2, 2**64)


def test_recorded_seed_boundary_is_exact() -> None:
    """Using one seed for separate source families must fail the evidence split."""
    module = _module()

    assert module.MASTER_SAMPLE_SEED == 1_380_376_179_526_893_666
    assert module.TABLE_SAMPLE_SEEDS == {
        "lss_overdensity": 4_976_263_942_886_350_198,
        "galaxy_groups": 4_652_599_078_883_424_958,
        "galaxy_group_memberships": 15_583_989_488_859_696_288,
        "specz_compilation": 9_076_022_164_977_561_485,
    }


# =============================================================================
# Exact target-cast values
# =============================================================================


def _case(target_type: str, *, element_count: int = 1) -> dict[str, object]:
    """Return a complete literal case surface for one pure-value behavior."""
    return {
        "table": "fixture_table",
        "column": "fixture_column",
        "target_type": target_type,
        "element_count": element_count,
    }


@pytest.mark.parametrize(
    ("target_type", "source", "expected"),
    [
        ("smallint", 12, ("smallint", 12)),
        ("bigint", -999, ("bigint", -999)),
        ("boolean", True, ("boolean", True)),
        ("text", b"A1", ("text", "A1")),
        ("real", 1.1, ("real", "3f8ccccd")),
        ("double precision", 1.1, ("double precision", "3ff199999999999a")),
        ("real", -0.0, ("real", "80000000")),
        ("double precision", -0.0, ("double precision", "8000000000000000")),
        ("real", math.inf, ("real", "7f800000")),
        ("double precision", -math.inf, ("double precision", "fff0000000000000")),
    ],
)
def test_source_values_cast_to_exact_target_tokens(
    target_type: str, source: object, expected: tuple[object, ...]
) -> None:
    """Changing a target cast, finite sentinel, or IEEE representation must fail."""
    module = _module()

    observed = module.cast_source_cell(_case(target_type), source, masked=False)

    assert observed.token == expected


def test_source_nulls_only_masks_and_nan() -> None:
    """Nulling finite sentinels or retaining masks/NaN must fail."""
    module = _module()

    assert module.cast_source_cell(_case("bigint"), -999, masked=False).token == (
        "bigint",
        -999,
    )
    assert module.cast_source_cell(_case("bigint"), -999, masked=True).token == (
        "null",
    )
    assert module.cast_source_cell(_case("double precision"), math.nan).token == (
        "null",
    )


def test_arrays_cast_each_ordered_element_and_null_state() -> None:
    """Flattening, reordering, tolerating, or whole-array nulling must fail."""
    module = _module()
    case = _case("real[]", element_count=5)

    observed = module.cast_source_cell(
        case,
        [1.1, -0.0, math.nan, -999.0, math.inf],
        masked=[False, False, False, True, False],
    )

    assert observed.token == (
        "real[]",
        (
            ("real", "3f8ccccd"),
            ("real", "80000000"),
            ("null",),
            ("null",),
            ("real", "7f800000"),
        ),
    )
    with pytest.raises(ValueError, match="array cardinality mismatch"):
        module.cast_source_cell(case, [1.0, 2.0], masked=False)


def test_database_values_use_same_tokens_without_source_null_inference() -> None:
    """Database NaN must not be silently treated as the source NULL contract."""
    module = _module()

    assert module.canonicalize_database_cell(_case("real"), -0.0).token == (
        "real",
        "80000000",
    )
    assert module.canonicalize_database_cell(_case("real"), None).token == ("null",)
    database_nan = module.canonicalize_database_cell(_case("real"), math.nan)
    assert database_nan.token[0] == "real"
    assert database_nan.token != ("null",)


def test_cast_rejects_overflow_wrong_shapes_and_unsupported_types() -> None:
    """Python coercion must not accept values PostgreSQL target casts reject."""
    module = _module()

    with pytest.raises(ValueError, match="integer target range"):
        module.cast_source_cell(_case("smallint"), 40_000)
    with pytest.raises(ValueError, match="boolean source type"):
        module.cast_source_cell(_case("boolean"), 1)
    with pytest.raises(ValueError, match="unsupported target type"):
        module.cast_source_cell(_case("numeric"), 1)


# =============================================================================
# Protected complete mismatch ledger
# =============================================================================


def _mismatch(module):
    """Return one literal mismatch whose values must survive the ledger."""
    return module.Mismatch(
        source_locator="HDU 1 row 7",
        table="photometry_primary",
        column="flux_aper_hst_f814w",
        source_value=("real[]", (("real", "3f800000"), ("null",))),
        database_value=("real[]", (("real", "40000000"), ("null",))),
        matching_method="source_row",
        sample_locator=7,
        element_index=0,
    )


def test_mismatch_ledger_seals_complete_mode_0600_jsonl(tmp_path: Path) -> None:
    """Dropping details, weakening mode, or leaving a temporary must fail."""
    module = _module()
    final = tmp_path / "mismatches.jsonl"
    ledger = module.MismatchLedger.create(final, allowed_root=tmp_path)

    ledger.write(_mismatch(module))
    observed = ledger.seal()

    assert observed == {"mismatch_count": 1, "ledger_created": True}
    assert stat.S_IMODE(final.lstat().st_mode) == 0o600
    assert stat.S_ISREG(final.lstat().st_mode)
    assert list(tmp_path.iterdir()) == [final]
    assert json.loads(final.read_text(encoding="utf-8")) == {
        "column": "flux_aper_hst_f814w",
        "database_value": ["real[]", [["real", "40000000"], ["null"]]],
        "element_index": 0,
        "matching_method": "source_row",
        "sample_locator": 7,
        "source_locator": "HDU 1 row 7",
        "source_value": ["real[]", [["real", "3f800000"], ["null"]]],
        "table": "photometry_primary",
    }


def test_mismatch_ledger_refuses_existing_symlink_and_outside_path(
    tmp_path: Path,
) -> None:
    """Following a final path or escaping the ignored root must fail."""
    module = _module()
    target = tmp_path / "target"
    target.write_text("protected", encoding="utf-8")
    symlink = tmp_path / "mismatches.jsonl"
    symlink.symlink_to(target)

    with pytest.raises(ValueError, match="ledger final path exists"):
        module.MismatchLedger.create(symlink, allowed_root=tmp_path)
    symlink.unlink()
    symlink.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="ledger final path exists"):
        module.MismatchLedger.create(symlink, allowed_root=tmp_path)
    with pytest.raises(ValueError, match="ledger containment"):
        module.MismatchLedger.create(
            tmp_path.parent / "outside.jsonl", allowed_root=tmp_path
        )
    assert target.read_text(encoding="utf-8") == "protected"


def test_mismatch_ledger_abort_removes_only_its_exact_inode(tmp_path: Path) -> None:
    """Interrupted writes must remove the run-owned temporary and no other file."""
    module = _module()
    final = tmp_path / "mismatches.jsonl"
    protected = tmp_path / "protected"
    protected.write_text("keep", encoding="utf-8")
    ledger = module.MismatchLedger.create(final, allowed_root=tmp_path)
    temporary = ledger.temporary_path
    ledger.write(_mismatch(module))

    ledger.abort()

    assert not final.exists()
    assert not temporary.exists()
    assert protected.read_text(encoding="utf-8") == "keep"


def test_mismatch_ledger_detects_temporary_inode_replacement(tmp_path: Path) -> None:
    """Cleanup must stop instead of unlinking a path replaced after creation."""
    module = _module()
    ledger = module.MismatchLedger.create(
        tmp_path / "mismatches.jsonl", allowed_root=tmp_path
    )
    temporary = ledger.temporary_path
    replacement = tmp_path / "replacement"
    replacement.write_text("do not delete", encoding="utf-8")
    os.unlink(temporary)
    os.link(replacement, temporary)

    with pytest.raises(RuntimeError, match="ledger cleanup identity"):
        ledger.abort()
    assert temporary.read_text(encoding="utf-8") == "do not delete"
