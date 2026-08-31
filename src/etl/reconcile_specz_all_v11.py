#!/usr/bin/env python3
"""
Script Name  : reconcile_specz_all_v11.py
Description  : Reconciles loaded specz_compilation_all values against the source
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
P2R-04 gate 4.5 value reconciliation for `source.specz_compilation_all`,
independent of the load path. Re-opens the pinned measurement-level FITS fresh,
samples rows (not columns) deterministically under a recorded seed, fetches
every generated column from one repeatable-read read-only snapshot, and
compares exact target-cast tokens: IEEE bytes for floats, integer edges,
arrays with order and cardinality, NULLs only against FITS masks and NaN.

This reuses the P2R-03 reconciliation core and streaming readers; only the
single-table scope and the recorded seed are new.

Usage
-----
    doppler run --project ml01 --config dev -- \
        python src/etl/reconcile_specz_all_v11.py

Examples
--------
    Default invocation reconciles the configured 20,000-row seeded sample
    across all 32 columns and writes a JSONL mismatch ledger if any cell
    differs.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import bootstrap_v11, reconcile_values_v11  # noqa: E402
from src.etl.conformance_cases_v11 import CASES  # noqa: E402
from src.etl.reconciliation_core_v11 import MismatchLedger  # noqa: E402
from src.etl.reconcile_values_v11 import (  # noqa: E402
    TableContract,
    fetch_target_rows,
    reconcile_expected_batch,
    stream_source_batches,
)
from src.etl import reconciliation_core_v11 as core  # noqa: E402

TABLE = "specz_compilation_all"
EXPECTED_COLUMNS = 32
# Frozen P2R-04 sampling seed, recorded in the worklog and distinct from every
# Gate 3.11 seed so the two samples are independent evidence.
SPECZ_ALL_SAMPLE_SEED = 12_006_315_477_097_142_501
SAMPLING_DERIVATION = "sha256_uint64_seed_plus_zero_based_ordinal_lowest_rank_v1"


# =============================================================================
# Functions
# =============================================================================


def build_contract() -> TableContract:
    """Build the single-table contract from the generated case surface."""
    selected = tuple(case for case in CASES if case["table"] == TABLE)
    if len(selected) != EXPECTED_COLUMNS:
        raise SystemExit(
            f"cases FAILED: {TABLE} has {len(selected)} cases, "
            f"expected {EXPECTED_COLUMNS}"
        )
    paths = {str(case["source_file"]) for case in selected}
    locators = {str(case["source_locator"]) for case in selected}
    populations = {int(case["expected_source_rows"]) for case in selected}
    if len(paths) != 1 or len(locators) != 1 or len(populations) != 1:
        raise SystemExit(f"cases FAILED: {TABLE} source contract is not singular")
    if any(case["column_origin"] != "source_native" for case in selected):
        raise SystemExit(f"cases FAILED: {TABLE} carries a metadata case")
    return TableContract(
        table=TABLE,
        cases=selected,
        source_path=Path(paths.pop()),
        source_locator=locators.pop(),
        expected_rows=populations.pop(),
        match_source_columns=("Id_specz",),
        match_target_columns=("id_specz",),
        historical_target_key=None,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=bootstrap_v11.DEFAULT_CONFIG_PATH)
    args = parser.parse_args()

    settings = bootstrap_v11.resolve_settings(args.config)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    sample_rows = int(config["reconciliation"]["sample_rows"])
    batch_rows = int(config["reconciliation"]["batch_rows"])
    contract = build_contract()
    sample_size = min(sample_rows, contract.expected_rows)
    ordinals = core.ranked_sample(
        contract.expected_rows, sample_size, SPECZ_ALL_SAMPLE_SEED
    )
    plan = reconcile_values_v11.SamplePlan(
        seed=SPECZ_ALL_SAMPLE_SEED,
        population=contract.expected_rows,
        sample_size=sample_size,
        ordinals=ordinals,
        digest=core.sample_digest(ordinals),
    )
    ledger_root = (
        settings.repo_root
        / ".superpowers"
        / "sdd"
        / "2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction"
    )
    ledger_root.mkdir(parents=True, exist_ok=True)
    ledger = MismatchLedger.create(
        ledger_root / "gate-4-5-mismatches.jsonl", allowed_root=ledger_root
    )
    mismatch_count = 0
    batch_count = 0
    compared_rows = 0

    with bootstrap_v11._connect(settings, settings.target_database) as connection:
        reconcile_values_v11.begin_read_only_snapshot(connection)
        live = connection.execute(
            'SELECT count(*) FROM "source"."{}"'.format(TABLE)
        ).fetchone()[0]
        if live != contract.expected_rows:
            raise SystemExit(
                f"count FAILED: live {live} != source {contract.expected_rows}"
            )

        def consume(rows, matching_method, multiplicities, tuple_locators):
            nonlocal mismatch_count, batch_count, compared_rows
            target = fetch_target_rows(connection, contract, rows)
            evidence = reconcile_expected_batch(
                contract,
                rows,
                target,
                matching_method=matching_method,
                native_tuple_multiplicities=multiplicities,
                ledger=ledger,
                native_tuple_locators=tuple_locators,
            )
            mismatch_count += evidence.mismatch_count
            compared_rows += len(rows)
            batch_count += 1

        try:
            streamed, _ = stream_source_batches(
                contract,
                plan,
                primary_ids=None,
                batch_rows=batch_rows,
                consume=consume,
            )
            if mismatch_count:
                summary = ledger.seal()
                raise SystemExit(
                    f"reconciliation FAILED: {mismatch_count} mismatches; ledger at "
                    f"{ledger.final_path}; {summary}"
                )
            # A zero-mismatch run publishes no ledger; clean the empty temp file.
            ledger.abort()
        except BaseException:
            try:
                ledger.abort()
            except (FileNotFoundError, RuntimeError, ValueError):
                pass
            raise
        connection.rollback()

    evidence = {
        "table": TABLE,
        "live_rows": live,
        "source_rows": streamed.total_rows,
        "distinct_key_rows": streamed.distinct_key_rows,
        "matching_method": streamed.matching_method,
        "sample_seed": SPECZ_ALL_SAMPLE_SEED,
        "sampling_derivation": SAMPLING_DERIVATION,
        "sample_size": plan.sample_size,
        "sample_digest": plan.digest,
        "rows_compared": compared_rows,
        "columns_compared": len(contract.cases),
        "row_column_comparisons": compared_rows * len(contract.cases),
        "database_batches": batch_count,
        "source_reads": streamed.source_reads,
        "mismatch_count": mismatch_count,
        "ledger_created": mismatch_count > 0,
    }
    print(json.dumps(evidence, indent=2, default=str))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
