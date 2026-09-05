#!/usr/bin/env python3
"""
Script Name  : reconcile_values_v11.py
Description  : Source-fresh exact value reconciliation for ETL v2
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Re-reads the eleven configured source artifacts independently of the load path
and compares dictionary-generated, target-cast values with a read-only
PostgreSQL snapshot.
"""

from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================

import argparse
import json
import os
import re
import stat
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import yaml
from astropy.io import fits

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import (  # noqa: E402
    bootstrap_v11,
    generate_conformance_v11,
    reconciliation_core_v11 as core,
    verify_conformance_v11,
    verify_source_fidelity,
)
from src.etl.conformance_cases_v11 import CASES  # noqa: E402

DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"


# =============================================================================
# Fixed table and native-key candidate boundary
# =============================================================================

GATE311_TABLES = (
    "photometry_primary",
    "lephare",
    "photometry_aper",
    "cigale",
    "ml_morpho",
    "bulge_disk",
    "galight_morph",
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
    "specz_compilation_unique",
)
MASTER_TABLES = GATE311_TABLES[:7]

MATCH_SOURCE_CANDIDATES = {
    "lss_overdensity": ("id",),
    "galaxy_groups": ("ID",),
    "galaxy_group_memberships": ("GALID", "ID"),
    "specz_compilation_unique": ("Id_specz",),
}

HISTORICAL_TARGET_KEYS = {
    "galaxy_groups": ("group_id",),
    "galaxy_group_memberships": ("galid", "group_id"),
}

EXPECTED_SUCCESS_TOTALS = {
    "tables": 11,
    "columns": 1_416,
    "native_columns": 1_403,
    "metadata_columns": 13,
    "sampled_table_records": 201_678,
    "row_column_comparisons": 28_063_492,
    "metadata_comparisons": 260_000,
    "array_cells": 3_320_000,
    "array_element_comparisons": 16_600_000,
}
SAMPLING_DERIVATION = "sha256_uint64_seed_plus_zero_based_ordinal_lowest_rank_v1"


# =============================================================================
# Evidence types
# =============================================================================


@dataclass(frozen=True)
class FileIdentity:
    """Stable no-symlink metadata around one immutable source extraction."""

    device: int
    inode: int
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class TableContract:
    """Generated value contract and exact source/key mapping for one mirror."""

    table: str
    cases: tuple[Mapping[str, Any], ...]
    source_path: Path
    source_locator: str
    expected_rows: int
    match_source_columns: tuple[str, ...]
    match_target_columns: tuple[str, ...]
    historical_target_key: tuple[str, ...] | None


@dataclass(frozen=True)
class ExpectedSourceRow:
    """One sampled source row after independent exact target casting."""

    ordinal: int
    source_locator: str
    match_key: tuple[core.CanonicalCell, ...]
    values: Mapping[str, core.CanonicalCell]


@dataclass(frozen=True)
class TableSourceEvidence:
    """Complete source uniqueness plus sampled exact rows from one read."""

    table: str
    total_rows: int
    distinct_key_rows: int
    matching_method: str
    source_reads: int
    sample_rows: tuple[ExpectedSourceRow, ...]
    native_tuple_multiplicities: Mapping[tuple[Any, ...], int]
    native_tuple_locators: Mapping[tuple[Any, ...], str]
    identity: FileIdentity


@dataclass(frozen=True)
class SamplePlan:
    """One recorded deterministic source-ordinal sample."""

    seed: int
    population: int
    sample_size: int
    ordinals: tuple[int, ...]
    digest: str


@dataclass(frozen=True)
class ReconciliationSettings:
    """Config-resolved read-only target and bounded reconciliation settings."""

    base: bootstrap_v11.Settings
    cases_path: Path
    mismatch_ledger_path: Path
    sample_rows: int
    wide_batch_rows: int
    batch_rows: int


@dataclass(frozen=True)
class StreamedTableEvidence:
    """Bounded extraction/batch facts retained after sampled rows are discarded."""

    table: str
    total_rows: int
    distinct_key_rows: int
    matching_method: str
    source_reads: int
    sample_size: int
    database_batches: int
    identity: FileIdentity


@dataclass(frozen=True)
class TableRunEvidence:
    """One streamed source observation plus all bounded comparison metrics."""

    stream: StreamedTableEvidence
    metrics: Mapping[str, int]


@dataclass(frozen=True)
class BatchReconciliationEvidence:
    """Exact comparison counts and mismatch total for one bounded row batch."""

    sampled_rows: int
    row_column_comparisons: int
    metadata_comparisons: int
    array_cells: int
    array_element_comparisons: int
    mismatch_count: int


@dataclass(frozen=True)
class Gate311ProtectedIdentity:
    """Persistent identity and per-table row/XID facts around read-only work."""

    base: verify_conformance_v11.ProtectedIdentity
    row_xids: tuple[tuple[str, int, tuple[str, ...]], ...]


class ReconciliationMismatch(RuntimeError):
    """A complete value-mismatch ledger was sealed without database mutation."""

    def __init__(self, mismatch_count: int, ledger_path: Path) -> None:
        super().__init__("Gate 3.11 value mismatches detected")
        self.mismatch_count = mismatch_count
        self.ledger_path = ledger_path


class RecordedMismatch(ValueError):
    """A mismatch was already written and must be sealed by orchestration."""

    def __init__(self, mismatch_count: int, message: str) -> None:
        super().__init__(message)
        self.mismatch_count = mismatch_count


@dataclass(frozen=True)
class ScratchFixture:
    """Synthetic complete source/target rows for disposable PostgreSQL proof."""

    cases: tuple[Mapping[str, Any], ...]
    contracts: Mapping[str, TableContract]
    target_rows: Mapping[str, tuple[Mapping[str, Any], ...]]


# =============================================================================
# Generated contracts
# =============================================================================


def _derive_match_columns(
    table: str, cases: Sequence[Mapping[str, Any]]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Map exact source-header candidates through sealed generated rows."""
    if table not in MATCH_SOURCE_CANDIDATES:
        return (), ("source_row",)
    sources = MATCH_SOURCE_CANDIDATES[table]
    targets: list[str] = []
    for source in sources:
        matches = [
            case
            for case in cases
            if case["column_origin"] == "source_native"
            and case["source_column"] == source
        ]
        if len(matches) != 1:
            raise ValueError(f"native key dictionary mismatch: {table}")
        targets.append(str(matches[0]["column"]))
    return sources, tuple(targets)


def build_table_contracts(
    cases: Sequence[Mapping[str, Any]],
) -> dict[str, TableContract]:
    """Build all eleven source contracts solely from generated case fields."""
    historical = [
        case for case in cases if case["table"] in set(GATE311_TABLES)
    ]
    cases = historical
    if len(cases) != 1_416 or tuple(dict.fromkeys(case["table"] for case in cases)) != (
        GATE311_TABLES
    ):
        raise ValueError("Gate 3.11 generated case boundary mismatch")
    contracts: dict[str, TableContract] = {}
    for table in GATE311_TABLES:
        selected = tuple(case for case in cases if case["table"] == table)
        native = tuple(
            case for case in selected if case["column_origin"] == "source_native"
        )
        paths = {str(case["source_file"]) for case in native}
        locators = {str(case["source_locator"]) for case in native}
        populations = {int(case["expected_source_rows"]) for case in selected}
        if not native or len(paths) != 1 or len(locators) != 1 or len(populations) != 1:
            raise ValueError(f"Gate 3.11 source contract mismatch: {table}")
        match_sources, match_targets = _derive_match_columns(table, selected)
        contracts[table] = TableContract(
            table=table,
            cases=selected,
            source_path=Path(paths.pop()),
            source_locator=locators.pop(),
            expected_rows=populations.pop(),
            match_source_columns=match_sources,
            match_target_columns=match_targets,
            historical_target_key=HISTORICAL_TARGET_KEYS.get(table),
        )
    return contracts


def resolve_settings(
    config_path: Path, environment: Mapping[str, str]
) -> ReconciliationSettings:
    """Resolve all Gate 3.11 paths and positive bounds from configuration."""
    base = bootstrap_v11.resolve_settings(config_path, environment)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        cases_path = Path(config["dictionary"]["conformance_cases_v11"])
        values = config["reconciliation"]
        mismatch = Path(values["mismatch_ledger"])
        sample_rows = int(values["sample_rows"])
        wide_batch_rows = int(values["wide_batch_rows"])
        batch_rows = int(values["batch_rows"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("missing Gate 3.11 reconciliation configuration") from exc
    expected_cases = base.repo_root / "src" / "etl" / "conformance_cases_v11.py"
    task_root = base.repo_root / ".superpowers" / "sdd"
    if cases_path != expected_cases:
        raise ValueError("generated cases path mismatch")
    if (
        mismatch.parent.resolve(strict=True)
        not in task_root.resolve(strict=True).glob("*")
        or mismatch.name != "gate-3-11-mismatches.jsonl"
    ):
        raise ValueError("mismatch ledger path boundary mismatch")
    if sample_rows < 1 or wide_batch_rows < 1 or batch_rows < 1:
        raise ValueError("positive reconciliation bounds required")
    return ReconciliationSettings(
        base=base,
        cases_path=cases_path,
        mismatch_ledger_path=mismatch,
        sample_rows=sample_rows,
        wide_batch_rows=wide_batch_rows,
        batch_rows=batch_rows,
    )


def build_sample_plan(
    contract: TableContract, *, sample_limit: int = 20_000
) -> SamplePlan:
    """Build the shared-master or separate-table deterministic sample."""
    if not isinstance(sample_limit, int) or sample_limit < 1:
        raise ValueError("sample limit mismatch")
    if contract.table in MASTER_TABLES:
        seed = core.MASTER_SAMPLE_SEED
    else:
        try:
            seed = core.TABLE_SAMPLE_SEEDS[contract.table]
        except KeyError as exc:
            raise ValueError("table sample seed mismatch") from exc
    sample_size = min(sample_limit, contract.expected_rows)
    ordinals = core.ranked_sample(contract.expected_rows, sample_size, seed)
    return SamplePlan(
        seed=seed,
        population=contract.expected_rows,
        sample_size=sample_size,
        ordinals=ordinals,
        digest=core.sample_digest(ordinals),
    )


# =============================================================================
# Immutable source helpers
# =============================================================================


def _file_identity(path: Path) -> FileIdentity:
    """Require one exact regular, non-symlink source path."""
    observed = path.lstat()
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError("source path is not a regular file")
    return FileIdentity(
        device=observed.st_dev,
        inode=observed.st_ino,
        size=observed.st_size,
        mtime_ns=observed.st_mtime_ns,
    )


def _validate_sample(sample: Sequence[int], population: int) -> tuple[int, ...]:
    """Require sorted unique source ordinals inside the physical population."""
    observed = tuple(sample)
    if (
        not observed
        or tuple(sorted(set(observed))) != observed
        or observed[0] < 0
        or observed[-1] >= population
    ):
        raise ValueError("source sample boundary mismatch")
    return observed


def _native_cases(contract: TableContract) -> tuple[Mapping[str, Any], ...]:
    """Return generated native cases in exact target-column order."""
    return tuple(
        case for case in contract.cases if case["column_origin"] == "source_native"
    )


def _case_by_source(contract: TableContract, source_column: str) -> Mapping[str, Any]:
    """Resolve one native source name through the generated table contract."""
    matches = [
        case
        for case in contract.cases
        if case["column_origin"] == "source_native"
        and case["source_column"] == source_column
    ]
    if len(matches) != 1:
        raise ValueError("source column contract mismatch")
    return matches[0]


def _fits_hdu_index(locator: str) -> int:
    """Parse the exact generated FITS HDU ordinal without filename inference."""
    match = re.fullmatch(r"HDU (\d+)(?: \[.*\])?", locator)
    if match is None:
        raise ValueError("FITS source locator mismatch")
    return int(match.group(1))


def _fits_nulls(hdu: fits.BinTableHDU) -> dict[str, Any]:
    """Read only declared FITS TNULL values from the selected table."""
    return {
        column.name: column.null for column in hdu.columns if column.null is not None
    }


def _canonical_fits_value(
    case: Mapping[str, Any], value: Any, *, fits_null: Any | None
) -> core.CanonicalCell:
    """Apply actual FITS masks and the independent target cast to one value."""
    if str(case["target_type"]).endswith("[]"):
        array = np.asarray(value)
        mask: bool | Sequence[bool]
        mask = False if fits_null is None else np.equal(array, fits_null)
        return core.cast_source_cell(case, array, masked=mask)
    masked = bool(fits_null is not None and value == fits_null)
    return core.cast_source_cell(case, value, masked=masked)


def _row_from_fits(
    contract: TableContract,
    data: fits.FITS_rec,
    nulls: Mapping[str, Any],
    ordinal: int,
    primary_ids: Mapping[int, int] | None,
) -> ExpectedSourceRow:
    """Build one complete generated row from a sampled FITS ordinal."""
    values: dict[str, core.CanonicalCell] = {}
    for case in contract.cases:
        origin = case["column_origin"]
        if origin == "source_native":
            source = str(case["source_column"])
            values[str(case["column"])] = _canonical_fits_value(
                case, data[source][ordinal], fits_null=nulls.get(source)
            )
        elif origin == "source_row_metadata":
            values[str(case["column"])] = core.cast_source_cell(case, ordinal)
        elif origin == "id_injected":
            if primary_ids is None or ordinal not in primary_ids:
                raise ValueError("sampled primary ID boundary mismatch")
            values[str(case["column"])] = core.cast_source_cell(
                case, primary_ids[ordinal]
            )
        else:
            raise ValueError("unsupported generated column origin")
    key = tuple(values[column] for column in contract.match_target_columns)
    return ExpectedSourceRow(
        ordinal=ordinal,
        source_locator=f"{contract.source_locator} row {ordinal}",
        match_key=key,
        values=values,
    )


def _native_tuple(row: ExpectedSourceRow, contract: TableContract) -> tuple[Any, ...]:
    """Return the complete target-cast native tuple for fallback multiplicity."""
    return tuple(
        row.values[str(case["column"])].token for case in _native_cases(contract)
    )


def read_fits_sample(
    contract: TableContract,
    sample: Sequence[int],
    primary_ids: Mapping[int, int] | None,
) -> TableSourceEvidence:
    """Observe full key uniqueness and sampled values in one FITS open."""
    before = _file_identity(contract.source_path)
    with fits.open(contract.source_path, memmap=True) as hdul:
        index = _fits_hdu_index(contract.source_locator)
        if index >= len(hdul) or not isinstance(hdul[index], fits.BinTableHDU):
            raise ValueError("FITS source HDU mismatch")
        hdu = hdul[index]
        expected_columns = tuple(
            str(case["source_column"]) for case in _native_cases(contract)
        )
        if tuple(hdu.columns.names) != expected_columns:
            raise ValueError("FITS source column boundary mismatch")
        data = hdu.data
        total = len(data)
        if total != contract.expected_rows:
            raise ValueError("FITS source row-count mismatch")
        ordinals = _validate_sample(sample, total)
        nulls = _fits_nulls(hdu)
        key_cases = tuple(
            _case_by_source(contract, column)
            for column in contract.match_source_columns
        )
        keys = (
            {
                tuple(
                    _canonical_fits_value(
                        case,
                        data[str(case["source_column"])][ordinal],
                        fits_null=nulls.get(str(case["source_column"])),
                    ).token
                    for case in key_cases
                )
                for ordinal in range(total)
            }
            if key_cases
            else set()
        )
        sample_rows = tuple(
            _row_from_fits(contract, data, nulls, ordinal, primary_ids)
            for ordinal in ordinals
        )
        distinct_key_rows = len(keys) if key_cases else total
        if distinct_key_rows == total:
            method = "unique_key"
            multiplicities: Mapping[tuple[Any, ...], int] = {}
            tuple_locators: Mapping[tuple[Any, ...], str] = {}
        else:
            method = "native_tuple_multiplicity"
            observed_counts: Counter[tuple[Any, ...]] = Counter()
            observed_locators: dict[tuple[Any, ...], str] = {}
            for ordinal in range(total):
                row = _row_from_fits(contract, data, nulls, ordinal, primary_ids)
                native_tuple = _native_tuple(row, contract)
                observed_counts[native_tuple] += 1
                observed_locators.setdefault(native_tuple, row.source_locator)
            multiplicities = observed_counts
            tuple_locators = observed_locators
    after = _file_identity(contract.source_path)
    if after != before:
        raise ValueError("source file identity changed during read")
    return TableSourceEvidence(
        table=contract.table,
        total_rows=total,
        distinct_key_rows=distinct_key_rows,
        matching_method=method,
        source_reads=1,
        sample_rows=sample_rows,
        native_tuple_multiplicities=multiplicities,
        native_tuple_locators=tuple_locators,
        identity=before,
    )


def _parse_text_value(case: Mapping[str, Any], token: str) -> Any:
    """Parse one whitespace token for the independent declared target cast."""
    target_type = str(case["target_type"])
    if target_type in {"smallint", "integer", "bigint"}:
        return int(token)
    if target_type in {"real", "double precision"}:
        return float(token)
    if target_type == "boolean":
        if token not in {"t", "f", "true", "false", "True", "False"}:
            raise ValueError("text boolean token mismatch")
        return token.lower() in {"t", "true"}
    if target_type == "text":
        return token
    raise ValueError("unsupported text target type")


def read_text_sample(
    contract: TableContract, sample: Sequence[int]
) -> TableSourceEvidence:
    """Observe text key uniqueness and fallback tuples in one sequential scan."""
    before = _file_identity(contract.source_path)
    expected_columns = tuple(
        str(case["source_column"]) for case in _native_cases(contract)
    )
    ordinals = _validate_sample(sample, contract.expected_rows)
    selected = set(ordinals)
    sample_rows: list[ExpectedSourceRow] = []
    keys: set[tuple[Any, ...]] = set()
    multiplicities: Counter[tuple[Any, ...]] = Counter()
    tuple_locators: dict[tuple[Any, ...], str] = {}
    total = 0
    with contract.source_path.open(encoding="utf-8") as handle:
        header = handle.readline().split()
        if tuple(header) != expected_columns:
            raise ValueError("text source column boundary mismatch")
        for line in handle:
            if not line.strip():
                continue
            tokens = line.split()
            if len(tokens) != len(contract.cases):
                raise ValueError("text source row width mismatch")
            values = {
                str(case["column"]): core.cast_source_cell(
                    case, _parse_text_value(case, token)
                )
                for case, token in zip(contract.cases, tokens, strict=True)
            }
            key = tuple(values[column] for column in contract.match_target_columns)
            keys.add(tuple(cell.token for cell in key))
            row = ExpectedSourceRow(
                ordinal=total,
                source_locator=f"{contract.source_locator} row {total}",
                match_key=key,
                values=values,
            )
            native_tuple = _native_tuple(row, contract)
            multiplicities[native_tuple] += 1
            tuple_locators.setdefault(native_tuple, row.source_locator)
            if total in selected:
                sample_rows.append(row)
            total += 1
    if total != contract.expected_rows:
        raise ValueError("text source row-count mismatch")
    after = _file_identity(contract.source_path)
    if after != before:
        raise ValueError("source file identity changed during read")
    unique = len(keys) == total
    return TableSourceEvidence(
        table=contract.table,
        total_rows=total,
        distinct_key_rows=len(keys),
        matching_method="unique_key" if unique else "native_tuple_multiplicity",
        source_reads=1,
        sample_rows=tuple(sample_rows),
        native_tuple_multiplicities={} if unique else multiplicities,
        native_tuple_locators={} if unique else tuple_locators,
        identity=before,
    )


# =============================================================================
# Exact bounded target comparison
# =============================================================================


def _case_by_target(contract: TableContract, column: str) -> Mapping[str, Any]:
    """Resolve one target column from the generated ordered contract."""
    matches = [case for case in contract.cases if case["column"] == column]
    if len(matches) != 1:
        raise ValueError("target column contract mismatch")
    return matches[0]


def _target_key(
    contract: TableContract, row: Mapping[str, Any]
) -> tuple[tuple[Any, ...], ...]:
    """Canonicalize the generated match key from one target result row."""
    return tuple(
        core.canonicalize_database_cell(
            _case_by_target(contract, column), row[column]
        ).token
        for column in contract.match_target_columns
    )


def _expected_key(row: ExpectedSourceRow) -> tuple[tuple[Any, ...], ...]:
    """Return the already canonical source match key."""
    return tuple(cell.token for cell in row.match_key)


def _target_native_tuple(
    contract: TableContract, row: Mapping[str, Any]
) -> tuple[Any, ...]:
    """Canonicalize the complete generated native target tuple."""
    return tuple(
        core.canonicalize_database_cell(case, row[str(case["column"])]).token
        for case in _native_cases(contract)
    )


def _write_mismatch(
    ledger: core.MismatchLedger | None,
    *,
    source_locator: str,
    table: str,
    column: str,
    source_value: tuple[Any, ...],
    database_value: tuple[Any, ...],
    matching_method: str,
    sample_locator: int | str | tuple[Any, ...],
    element_index: int | None,
) -> None:
    """Write one complete mismatch when a protected ledger is active."""
    if ledger is not None:
        ledger.write(
            core.Mismatch(
                source_locator=source_locator,
                table=table,
                column=column,
                source_value=source_value,
                database_value=database_value,
                matching_method=matching_method,
                sample_locator=sample_locator,
                element_index=element_index,
            )
        )


def _write_cell_mismatches(
    ledger: core.MismatchLedger | None,
    *,
    contract: TableContract,
    case: Mapping[str, Any],
    source_row: ExpectedSourceRow,
    source_cell: core.CanonicalCell,
    database_cell: core.CanonicalCell,
    matching_method: str,
) -> int:
    """Write one scalar/whole-cell mismatch or every differing array element."""
    if source_cell.token == database_cell.token:
        return 0
    target_type = str(case["target_type"])
    if (
        target_type.endswith("[]")
        and source_cell.token[0] == target_type
        and database_cell.token[0] == target_type
    ):
        count = 0
        for index, (source_element, database_element) in enumerate(
            zip(source_cell.token[1], database_cell.token[1], strict=True)
        ):
            if source_element == database_element:
                continue
            _write_mismatch(
                ledger,
                source_locator=source_row.source_locator,
                table=contract.table,
                column=str(case["column"]),
                source_value=source_element,
                database_value=database_element,
                matching_method=matching_method,
                sample_locator=source_row.ordinal,
                element_index=index,
            )
            count += 1
        return count
    _write_mismatch(
        ledger,
        source_locator=source_row.source_locator,
        table=contract.table,
        column=str(case["column"]),
        source_value=source_cell.token,
        database_value=database_cell.token,
        matching_method=matching_method,
        sample_locator=source_row.ordinal,
        element_index=None,
    )
    return 1


def _batch_counts(
    contract: TableContract, sampled_rows: int, mismatch_count: int
) -> BatchReconciliationEvidence:
    """Derive coverage totals only from generated cases and sampled rows."""
    metadata = sum(case["column_origin"] != "source_native" for case in contract.cases)
    arrays = tuple(
        case for case in contract.cases if str(case["target_type"]).endswith("[]")
    )
    return BatchReconciliationEvidence(
        sampled_rows=sampled_rows,
        row_column_comparisons=sampled_rows * len(contract.cases),
        metadata_comparisons=sampled_rows * metadata,
        array_cells=sampled_rows * len(arrays),
        array_element_comparisons=sampled_rows
        * sum(int(case["element_count"]) for case in arrays),
        mismatch_count=mismatch_count,
    )


def reconcile_expected_batch(
    contract: TableContract,
    expected_rows: Sequence[ExpectedSourceRow],
    target_rows: Sequence[Mapping[str, Any]],
    *,
    matching_method: str,
    native_tuple_multiplicities: Mapping[tuple[Any, ...], int],
    ledger: core.MismatchLedger | None,
    native_tuple_locators: Mapping[tuple[Any, ...], str] | None = None,
) -> BatchReconciliationEvidence:
    """Compare one bounded target result against independently cast source rows."""
    expected = tuple(expected_rows)
    target = tuple(target_rows)
    columns = {str(case["column"]) for case in contract.cases}
    if not expected:
        raise ValueError("empty reconciliation batch")
    if any(set(row) != columns for row in target):
        raise ValueError("target column boundary mismatch")
    expected_keys = {_expected_key(row) for row in expected}
    target_keys = [_target_key(contract, row) for row in target]
    if matching_method == "unique_key":
        if len(expected_keys) != len(expected):
            raise ValueError("unique source key contract mismatch")
        expected_by_key = {_expected_key(row): row for row in expected}
        target_by_key: dict[tuple[tuple[Any, ...], ...], list[Mapping[str, Any]]] = {}
        for key, row in zip(target_keys, target, strict=True):
            target_by_key.setdefault(key, []).append(row)
        mismatch_count = 0
        for key in sorted(expected_keys - set(target_by_key), key=repr):
            source_row = expected_by_key[key]
            _write_mismatch(
                ledger,
                source_locator=source_row.source_locator,
                table=contract.table,
                column="[match_key_presence]",
                source_value=("match_key", key),
                database_value=("absent",),
                matching_method=matching_method,
                sample_locator=source_row.ordinal,
                element_index=None,
            )
            mismatch_count += 1
        for key in sorted(set(target_by_key) - expected_keys, key=repr):
            _write_mismatch(
                ledger,
                source_locator="[absent from source]",
                table=contract.table,
                column="[match_key_presence]",
                source_value=("absent",),
                database_value=("match_key", key),
                matching_method=matching_method,
                sample_locator=key,
                element_index=None,
            )
            mismatch_count += 1
        for source_row in expected:
            key = _expected_key(source_row)
            matches = target_by_key.get(key, [])
            if not matches:
                continue
            if len(matches) != 1:
                _write_mismatch(
                    ledger,
                    source_locator=source_row.source_locator,
                    table=contract.table,
                    column="[match_key_multiplicity]",
                    source_value=("multiplicity", 1, key),
                    database_value=("multiplicity", len(matches), key),
                    matching_method=matching_method,
                    sample_locator=source_row.ordinal,
                    element_index=None,
                )
                mismatch_count += 1
                continue
            database_row = matches[0]
            for case in contract.cases:
                column = str(case["column"])
                source_cell = source_row.values[column]
                database_cell = core.canonicalize_database_cell(
                    case, database_row[column]
                )
                mismatch_count += _write_cell_mismatches(
                    ledger,
                    contract=contract,
                    case=case,
                    source_row=source_row,
                    source_cell=source_cell,
                    database_cell=database_cell,
                    matching_method=matching_method,
                )
        return _batch_counts(contract, len(expected), mismatch_count)
    if matching_method != "native_tuple_multiplicity":
        raise ValueError("unsupported source matching method")
    native_cases = _native_cases(contract)
    key_positions = tuple(
        next(
            index for index, case in enumerate(native_cases) if case["column"] == column
        )
        for column in contract.match_target_columns
    )
    relevant_source = {
        row_tuple: count
        for row_tuple, count in native_tuple_multiplicities.items()
        if tuple(row_tuple[index] for index in key_positions) in expected_keys
    }
    observed_target = Counter(_target_native_tuple(contract, row) for row in target)
    tuple_locators = native_tuple_locators or {}
    mismatch_count = 0
    for row_tuple in sorted(set(relevant_source) | set(observed_target), key=repr):
        source_count = relevant_source.get(row_tuple, 0)
        database_count = observed_target.get(row_tuple, 0)
        if source_count == database_count:
            continue
        mismatch_count += 1
        _write_mismatch(
            ledger,
            source_locator=tuple_locators.get(row_tuple, "[absent from source]"),
            table=contract.table,
            column="[native_row_tuple_multiplicity]",
            source_value=("multiplicity", source_count, row_tuple),
            database_value=("multiplicity", database_count, row_tuple),
            matching_method=matching_method,
            sample_locator=tuple(sorted(expected_keys, key=repr)),
            element_index=None,
        )
    return _batch_counts(contract, len(expected), mismatch_count)


def batched(values: Sequence[Any], size: int) -> tuple[tuple[Any, ...], ...]:
    """Split one in-memory sample into explicit positive bounded batches."""
    if not isinstance(size, int) or size < 1:
        raise ValueError("database batch size mismatch")
    observed = tuple(values)
    return tuple(
        observed[start : start + size] for start in range(0, len(observed), size)
    )


def begin_read_only_snapshot(connection: Any) -> None:
    """Start and positively assert the sole target transaction is read-only."""
    connection.execute("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    observed = connection.execute("SHOW transaction_read_only").fetchone()
    value = (
        observed.get("transaction_read_only")
        if isinstance(observed, Mapping)
        else observed[0]
        if isinstance(observed, Sequence) and len(observed) == 1
        else None
    )
    if value != "on":
        raise ValueError("read-only transaction mismatch")


def _parameter_from_cell(cell: core.CanonicalCell) -> Any:
    """Recover a typed query key from a canonical scalar token."""
    kind = cell.token[0]
    if kind in {"smallint", "integer", "bigint", "boolean", "text"}:
        return cell.token[1]
    raise ValueError("unsupported target query-key type")


def fetch_target_rows(
    connection: Any,
    contract: TableContract,
    expected_rows: Sequence[ExpectedSourceRow],
) -> tuple[Mapping[str, Any], ...]:
    """Fetch all generated columns for one bounded exact match-key batch."""
    expected = tuple(expected_rows)
    if not expected:
        raise ValueError("empty target fetch batch")
    columns = tuple(str(case["column"]) for case in contract.cases)
    selected = sql.SQL(", ").join(sql.Identifier(column) for column in columns)
    table = sql.SQL("{}.{}").format(
        sql.Identifier("source"), sql.Identifier(contract.table)
    )
    unique_keys: list[tuple[core.CanonicalCell, ...]] = []
    seen: set[tuple[tuple[Any, ...], ...]] = set()
    for row in expected:
        key = tuple(cell.token for cell in row.match_key)
        if key not in seen:
            seen.add(key)
            unique_keys.append(row.match_key)
    if len(contract.match_target_columns) == 1:
        key_column = contract.match_target_columns[0]
        statement = sql.SQL("SELECT {} FROM {} WHERE {} = ANY(%s)").format(
            selected, table, sql.Identifier(key_column)
        )
        parameters: tuple[Any, ...] = (
            [_parameter_from_cell(key[0]) for key in unique_keys],
        )
    else:
        key_columns = sql.SQL(", ").join(
            sql.Identifier(column) for column in contract.match_target_columns
        )
        one_key = (
            sql.SQL("(")
            + sql.SQL(", ").join(
                sql.Placeholder() for _ in contract.match_target_columns
            )
            + sql.SQL(")")
        )
        key_values = sql.SQL(", ").join(one_key for _ in unique_keys)
        statement = sql.SQL("SELECT {} FROM {} WHERE ({}) IN ({})").format(
            selected, table, key_columns, key_values
        )
        parameters = tuple(
            _parameter_from_cell(cell) for key in unique_keys for cell in key
        )
    return tuple(connection.execute(statement, parameters).fetchall())


def stream_source_batches(
    contract: TableContract,
    plan: SamplePlan,
    *,
    primary_ids: Mapping[int, int] | None,
    batch_rows: int,
    consume: Callable[
        [
            tuple[ExpectedSourceRow, ...],
            str,
            Mapping[tuple[Any, ...], int],
            Mapping[tuple[Any, ...], str],
        ],
        Any,
    ],
) -> tuple[StreamedTableEvidence, dict[int, int]]:
    """Read one source once and discard every sample batch after consumption."""
    if (
        plan.population != contract.expected_rows
        or plan.sample_size != len(plan.ordinals)
        or plan.digest != core.sample_digest(plan.ordinals)
    ):
        raise ValueError("source sample plan mismatch")
    if contract.source_locator.startswith("text table"):
        observed = read_text_sample(contract, plan.ordinals)
        batch_count = 0
        for rows in batched(observed.sample_rows, batch_rows):
            consume(
                rows,
                observed.matching_method,
                observed.native_tuple_multiplicities,
                observed.native_tuple_locators,
            )
            batch_count += 1
        return (
            StreamedTableEvidence(
                table=contract.table,
                total_rows=observed.total_rows,
                distinct_key_rows=observed.distinct_key_rows,
                matching_method=observed.matching_method,
                source_reads=observed.source_reads,
                sample_size=len(observed.sample_rows),
                database_batches=batch_count,
                identity=observed.identity,
            ),
            dict(primary_ids or {}),
        )
    before = _file_identity(contract.source_path)
    sampled_primary_ids = dict(primary_ids or {})
    with fits.open(contract.source_path, memmap=True) as hdul:
        index = _fits_hdu_index(contract.source_locator)
        if index >= len(hdul) or not isinstance(hdul[index], fits.BinTableHDU):
            raise ValueError("FITS source HDU mismatch")
        hdu = hdul[index]
        expected_columns = tuple(
            str(case["source_column"]) for case in _native_cases(contract)
        )
        if tuple(hdu.columns.names) != expected_columns:
            raise ValueError("FITS source column boundary mismatch")
        data = hdu.data
        total = len(data)
        if total != contract.expected_rows:
            raise ValueError("FITS source row-count mismatch")
        _validate_sample(plan.ordinals, total)
        nulls = _fits_nulls(hdu)
        key_cases = tuple(
            _case_by_source(contract, column)
            for column in contract.match_source_columns
        )
        keys = (
            {
                tuple(
                    _canonical_fits_value(
                        case,
                        data[str(case["source_column"])][ordinal],
                        fits_null=nulls.get(str(case["source_column"])),
                    ).token
                    for case in key_cases
                )
                for ordinal in range(total)
            }
            if key_cases
            else set()
        )
        distinct = len(keys) if key_cases else total
        if distinct == total:
            method = "unique_key"
            multiplicities: Mapping[tuple[Any, ...], int] = {}
            tuple_locators: Mapping[tuple[Any, ...], str] = {}
        else:
            method = "native_tuple_multiplicity"
            observed_counts: Counter[tuple[Any, ...]] = Counter()
            observed_locators: dict[tuple[Any, ...], str] = {}
            for ordinal in range(total):
                row = _row_from_fits(contract, data, nulls, ordinal, primary_ids)
                native_tuple = _native_tuple(row, contract)
                observed_counts[native_tuple] += 1
                observed_locators.setdefault(native_tuple, row.source_locator)
            multiplicities = observed_counts
            tuple_locators = observed_locators
        batch_count = 0
        for ordinal_batch in batched(plan.ordinals, batch_rows):
            rows = tuple(
                _row_from_fits(contract, data, nulls, ordinal, primary_ids)
                for ordinal in ordinal_batch
            )
            if contract.table == "photometry_primary":
                for row in rows:
                    token = row.values["id"].token
                    if token[0] != "bigint":
                        raise ValueError("sampled primary ID type mismatch")
                    sampled_primary_ids[row.ordinal] = int(token[1])
            consume(rows, method, multiplicities, tuple_locators)
            batch_count += 1
    after = _file_identity(contract.source_path)
    if after != before:
        raise ValueError("source file identity changed during read")
    return (
        StreamedTableEvidence(
            table=contract.table,
            total_rows=total,
            distinct_key_rows=distinct,
            matching_method=method,
            source_reads=1,
            sample_size=plan.sample_size,
            database_batches=batch_count,
            identity=before,
        ),
        sampled_primary_ids,
    )


def derive_success_totals(
    contracts: Mapping[str, TableContract], sample_sizes: Mapping[str, int]
) -> dict[str, int]:
    """Compute the complete success boundary from cases and actual sample sizes."""
    if set(contracts) != set(GATE311_TABLES) or set(sample_sizes) != set(contracts):
        raise ValueError("Gate 3.11 table total boundary mismatch")
    columns = tuple(case for contract in contracts.values() for case in contract.cases)
    return {
        "tables": len(contracts),
        "columns": len(columns),
        "native_columns": sum(
            case["column_origin"] == "source_native" for case in columns
        ),
        "metadata_columns": sum(
            case["column_origin"] != "source_native" for case in columns
        ),
        "sampled_table_records": sum(sample_sizes.values()),
        "row_column_comparisons": sum(
            len(contract.cases) * sample_sizes[table]
            for table, contract in contracts.items()
        ),
        "metadata_comparisons": sum(
            sum(case["column_origin"] != "source_native" for case in contract.cases)
            * sample_sizes[table]
            for table, contract in contracts.items()
        ),
        "array_cells": sum(
            sum(str(case["target_type"]).endswith("[]") for case in contract.cases)
            * sample_sizes[table]
            for table, contract in contracts.items()
        ),
        "array_element_comparisons": sum(
            sum(
                int(case["element_count"])
                for case in contract.cases
                if str(case["target_type"]).endswith("[]")
            )
            * sample_sizes[table]
            for table, contract in contracts.items()
        ),
    }


def validate_success_totals(observed: Mapping[str, int]) -> None:
    """Require runtime-derived totals equal the approved Gate 3.11 boundary."""
    if dict(observed) != EXPECTED_SUCCESS_TOTALS:
        raise ValueError("Gate 3.11 success total mismatch")


def build_table_success_evidence(
    contract: TableContract,
    plan: SamplePlan,
    stream: StreamedTableEvidence,
    metrics: Mapping[str, int],
) -> dict[str, Any]:
    """Render the complete value-free reproducibility boundary for one table."""
    target_columns = tuple(str(case["column"]) for case in contract.cases)
    source_columns = tuple(
        str(case["source_column"])
        for case in contract.cases
        if case["column_origin"] == "source_native"
    )
    return {
        "source_path": str(contract.source_path),
        "source_locator": contract.source_locator,
        "sampling_derivation": SAMPLING_DERIVATION,
        "seed": plan.seed,
        "eligible_population": plan.population,
        "sample_size": plan.sample_size,
        "sample_digest": plan.digest,
        "source_reads": stream.source_reads,
        "database_batches": stream.database_batches,
        "source_key_total": stream.total_rows,
        "source_key_distinct": stream.distinct_key_rows,
        "matching_method": stream.matching_method,
        "match_source_columns": contract.match_source_columns,
        "match_target_columns": contract.match_target_columns,
        "historical_target_key": contract.historical_target_key,
        "source_columns": source_columns,
        "target_columns": target_columns,
        "reconciled_columns": target_columns,
        "columns_reconciled": len(target_columns),
        "cell_null_state_comparisons": metrics["row_column_comparisons"],
        "array_element_null_state_comparisons": metrics["array_element_comparisons"],
        "null_states_exact": metrics["mismatch_count"] == 0,
        **metrics,
    }


# =============================================================================
# Disposable complete source fixtures
# =============================================================================


def _fixture_native_value(case: Mapping[str, Any], row: int, column_index: int) -> Any:
    """Return one deterministic raw source value independent of reconciliation."""
    table = str(case["table"])
    source = str(case["source_column"])
    effective_row = 0 if table == "galaxy_group_memberships" and row == 1 else row
    special_integer = {
        ("photometry_primary", "id"): 1_000 + effective_row,
        ("lss_overdensity", "id"): 2_000 + effective_row,
        ("galaxy_groups", "ID"): 3_000 + effective_row,
        ("galaxy_group_memberships", "GALID"): 4_000 + effective_row,
        ("galaxy_group_memberships", "ID"): 5_000 + effective_row,
        ("specz_compilation_unique", "Id_specz"): 6_000 + effective_row,
    }
    if (table, source) in special_integer:
        return special_integer[(table, source)]
    target_type = str(case["target_type"])
    element_count = int(case["element_count"])
    scratch_null = case.get("scratch_fits_null")
    if scratch_null is not None and row == 0:
        return int(scratch_null)
    if target_type.endswith("[]"):
        base = target_type.removesuffix("[]")
        values = np.array(
            [-0.0, np.inf, -np.inf, np.nan, -999.0],
            dtype=np.float32 if base == "real" else np.float64,
        )
        if case.get("scratch_finite_rounding"):
            values[0] = 1.1
        if len(values) != element_count:
            raise ValueError("scratch array edge cardinality mismatch")
        return values
    if target_type in core.INTEGER_RANGES:
        lower, upper = core.INTEGER_RANGES[target_type]
        if target_type == "smallint":
            return (0, upper, lower + 1)[effective_row]
        return (lower + 1, upper, 0)[effective_row]
    if target_type == "boolean":
        return effective_row % 2 == 0
    if target_type == "text":
        width = max(1, element_count)
        return f"A{effective_row}"[:width]
    if target_type in {"real", "double precision"}:
        if case.get("scratch_finite_rounding"):
            return np.float32(1.1) if target_type == "real" else 1.1
        if table == "lss_overdensity" and source == "density_excess":
            return (-999.0, -0.0, np.inf)[effective_row]
        value = (-0.0, np.inf, -np.inf)[effective_row]
        return np.float32(value) if target_type == "real" else float(value)
    raise ValueError("unsupported scratch fixture target type")


def _fixture_database_value(case: Mapping[str, Any], value: Any) -> Any:
    """Independently construct a psycopg value accepted by the declared target."""
    target_type = str(case["target_type"])
    scratch_null = case.get("scratch_fits_null")
    if scratch_null is not None and int(value) == int(scratch_null):
        return None
    if target_type.endswith("[]"):
        base = target_type.removesuffix("[]")
        output: list[Any] = []
        for element in np.asarray(value):
            if np.isnan(element):
                output.append(None)
            elif base == "real":
                output.append(float(np.float32(element)))
            else:
                output.append(float(element))
        return output
    if target_type in {"real", "double precision"}:
        converted = float(value)
        if np.isnan(converted):
            return None
        return float(np.float32(converted)) if target_type == "real" else converted
    if target_type in {"smallint", "integer", "bigint"}:
        return int(value)
    if target_type == "boolean":
        return bool(value)
    if target_type == "text":
        return bytes(value).decode("utf-8") if isinstance(value, bytes) else str(value)
    raise ValueError("unsupported scratch database target type")


def build_scratch_fixture(root: Path, *, rows_per_table: int) -> ScratchFixture:
    """Write eleven small complete sources and independent target row values."""
    if not root.is_dir() or rows_per_table < 2:
        raise ValueError("scratch fixture boundary mismatch")
    rewritten: list[dict[str, Any]] = []
    raw_tables: dict[str, list[dict[str, Any]]] = {}
    rounding_widths: set[str] = set()
    for table in GATE311_TABLES:
        original = [case for case in CASES if case["table"] == table]
        is_text = table in {"galaxy_groups", "galaxy_group_memberships"}
        path = root / f"{table}.{'txt' if is_text else 'fits'}"
        table_cases = []
        for case in original:
            changed = dict(case)
            changed["source_file"] = str(path)
            changed["source_locator"] = (
                "text table, header line 1" if is_text else "HDU 1"
            )
            changed["expected_source_rows"] = rows_per_table
            if (
                not is_text
                and changed["column_origin"] == "source_native"
                and changed["target_type"] == "smallint"
            ):
                changed["scratch_fits_null"] = core.INTEGER_RANGES["smallint"][0]
            rounding_width = (
                "real"
                if changed["target_type"] == "real[]"
                else "double precision"
                if changed["target_type"] == "double precision"
                else None
            )
            if (
                changed["column_origin"] == "source_native"
                and rounding_width is not None
                and rounding_width not in rounding_widths
            ):
                changed["scratch_finite_rounding"] = True
                rounding_widths.add(rounding_width)
            table_cases.append(changed)
            rewritten.append(changed)
        scratch_native = [
            case for case in table_cases if case["column_origin"] == "source_native"
        ]
        raw_rows: list[dict[str, Any]] = []
        for row in range(rows_per_table):
            raw_rows.append(
                {
                    str(case["source_column"]): _fixture_native_value(
                        case, row, column_index
                    )
                    for column_index, case in enumerate(scratch_native)
                }
            )
        raw_tables[table] = raw_rows
        if is_text:
            lines = [" ".join(str(case["source_column"]) for case in scratch_native)]
            for raw in raw_rows:
                lines.append(
                    " ".join(
                        str(raw[str(case["source_column"])]) for case in scratch_native
                    )
                )
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            columns = []
            for case in scratch_native:
                source = str(case["source_column"])
                columns.append(
                    fits.Column(
                        name=source,
                        format=str(case["source_type"]),
                        array=np.asarray([raw[source] for raw in raw_rows]),
                        null=case.get("scratch_fits_null"),
                    )
                )
            fits.BinTableHDU.from_columns(columns).writeto(path)
    contracts = build_table_contracts(tuple(rewritten))
    primary_ids = {
        row: int(raw_tables["photometry_primary"][row]["id"])
        for row in range(rows_per_table)
    }
    target_rows: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for table, contract in contracts.items():
        output: list[dict[str, Any]] = []
        for ordinal, raw in enumerate(raw_tables[table]):
            values: dict[str, Any] = {}
            for case in contract.cases:
                origin = case["column_origin"]
                if origin == "source_native":
                    source_value = raw[str(case["source_column"])]
                elif origin == "source_row_metadata":
                    source_value = ordinal
                elif origin == "id_injected":
                    source_value = primary_ids[ordinal]
                else:
                    raise ValueError("scratch generated origin mismatch")
                values[str(case["column"])] = _fixture_database_value(
                    case, source_value
                )
            output.append(values)
        target_rows[table] = tuple(output)
    return ScratchFixture(
        cases=tuple(rewritten), contracts=contracts, target_rows=target_rows
    )


def scratch_cast_parity_evidence(fixture: ScratchFixture) -> dict[str, int]:
    """Require the complete synthetic edge set later round-trips through PostgreSQL."""
    mask_case = next(case for case in fixture.cases if "scratch_fits_null" in case)
    mask_table = str(mask_case["table"])
    mask_column = str(mask_case["column"])
    mask_contract = fixture.contracts[mask_table]
    with fits.open(mask_contract.source_path, memmap=True) as hdul:
        hdu = hdul[_fits_hdu_index(mask_contract.source_locator)]
        source_column = str(mask_case["source_column"])
        if (
            hdu.columns[source_column].null != mask_case["scratch_fits_null"]
            or int(hdu.data[source_column][0]) != mask_case["scratch_fits_null"]
            or fixture.target_rows[mask_table][0][mask_column] is not None
        ):
            raise ValueError("scratch FITS mask parity boundary mismatch")
    if [fixture.target_rows[mask_table][row][mask_column] for row in (1, 2)] != [
        core.INTEGER_RANGES["smallint"][1],
        core.INTEGER_RANGES["smallint"][0] + 1,
    ]:
        raise ValueError("scratch smallint edge boundary mismatch")
    bigint_case = next(
        case
        for case in fixture.cases
        if case["target_type"] == "bigint"
        and (case["table"], case["source_column"])
        not in {
            ("photometry_primary", "id"),
            ("lss_overdensity", "id"),
            ("galaxy_groups", "ID"),
            ("galaxy_group_memberships", "GALID"),
            ("galaxy_group_memberships", "ID"),
            ("specz_compilation_unique", "Id_specz"),
        }
    )
    bigint_values = [
        fixture.target_rows[str(bigint_case["table"])][row][str(bigint_case["column"])]
        for row in (0, 1)
    ]
    if bigint_values != [
        core.INTEGER_RANGES["bigint"][0] + 1,
        core.INTEGER_RANGES["bigint"][1],
    ]:
        raise ValueError("scratch bigint edge boundary mismatch")
    real_case = next(case for case in fixture.cases if case["target_type"] == "real")
    double_case = next(
        case
        for case in fixture.cases
        if case["target_type"] == "double precision"
        and not case.get("scratch_finite_rounding")
    )
    real_values = fixture.target_rows[str(real_case["table"])]
    real_column = str(real_case["column"])
    double_values = fixture.target_rows[str(double_case["table"])]
    double_column = str(double_case["column"])
    if (
        real_values[0][real_column] != -999.0
        or not np.signbit(real_values[1][real_column])
        or real_values[1][real_column] != 0.0
        or not np.isposinf(real_values[2][real_column])
        or not np.signbit(double_values[0][double_column])
        or double_values[0][double_column] != 0.0
        or not np.isposinf(double_values[1][double_column])
        or not np.isneginf(double_values[2][double_column])
    ):
        raise ValueError("scratch scalar IEEE parity boundary mismatch")
    array_widths = set()
    for target_type in ("real[]", "double precision[]"):
        case = next(
            case
            for case in fixture.cases
            if case["target_type"] == target_type
            and not case.get("scratch_finite_rounding")
        )
        values = fixture.target_rows[str(case["table"])][0][str(case["column"])]
        if not (
            len(values) == 5
            and values[0] == 0.0
            and np.signbit(values[0])
            and np.isposinf(values[1])
            and np.isneginf(values[2])
            and values[3] is None
            and values[4] == -999.0
        ):
            raise ValueError("scratch array IEEE/null parity boundary mismatch")
        array_widths.add(target_type)
    if array_widths != {"real[]", "double precision[]"}:
        raise ValueError("scratch array width boundary mismatch")
    rounding_cases = {
        (
            "real"
            if str(case["target_type"]).startswith("real")
            else "double precision"
        ): case
        for case in fixture.cases
        if case.get("scratch_finite_rounding")
    }
    if set(rounding_cases) != {"real", "double precision"}:
        raise ValueError("scratch finite rounding width boundary mismatch")
    real_rounding = rounding_cases["real"]
    real_rounding_value = fixture.target_rows[str(real_rounding["table"])][0][
        str(real_rounding["column"])
    ][0]
    double_rounding = rounding_cases["double precision"]
    double_rounding_value = fixture.target_rows[str(double_rounding["table"])][0][
        str(double_rounding["column"])
    ]
    if real_rounding_value != float(np.float32(1.1)) or double_rounding_value != 1.1:
        raise ValueError("scratch finite rounding value mismatch")
    return {
        "smallint_fits_mask_nulls": 1,
        "smallint_edges": 2,
        "bigint_edges": 2,
        "signed_zero_widths": 2,
        "positive_infinity_widths": 2,
        "negative_infinity_widths": 2,
        "finite_rounding_widths": len(rounding_cases),
        "finite_sentinel_values": 1,
        "array_edge_kinds": 5,
    }


def run_guarded_scratch_lifecycle(
    *, create: Callable[[], Any], proof: Callable[[], Any], drop: Callable[[], Any]
) -> Any:
    """Run proof after creation and always perform the exact supplied cleanup."""
    cleanup_candidate = False
    try:
        cleanup_candidate = True
        create()
        return proof()
    finally:
        if cleanup_candidate:
            drop()


def _connect_scratch_dict(
    settings: ReconciliationSettings, database: str
) -> psycopg.Connection:
    """Connect with mapping rows only to one prefix-validated scratch database."""
    config = yaml.safe_load(settings.base.config_path.read_text(encoding="utf-8"))
    prefix = str(config["database"]["scratch_prefix"])
    verify_conformance_v11.validate_scratch_name(prefix, database)
    base = settings.base
    return psycopg.connect(
        host=base.host,
        port=base.port,
        user=base.user,
        password=base.password,
        dbname=database,
        row_factory=dict_row,
    )


def _drop_scratch_candidate(settings: ReconciliationSettings, database: str) -> None:
    """Drop the exact random candidate if present and otherwise prove absence."""
    config = yaml.safe_load(settings.base.config_path.read_text(encoding="utf-8"))
    prefix = str(config["database"]["scratch_prefix"])
    verify_conformance_v11.validate_scratch_name(prefix, database)
    with verify_conformance_v11._connect_database(
        settings.base, settings.base.maintenance_database
    ) as admin:
        exists = admin.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname=%s)",
            (database,),
        ).fetchone()[0]
    if exists:
        verify_conformance_v11._drop_scratch_database(settings.base, database)


def _insert_scratch_fixture(
    connection: psycopg.Connection,
    fixture: ScratchFixture,
    settings: ReconciliationSettings,
) -> None:
    """Create reviewed schema and insert independent synthetic target values."""
    connection.execute(verify_conformance_v11._reviewed_ddl(settings.base))
    connection.execute(
        sql.SQL("GRANT USAGE ON SCHEMA source TO {}").format(
            sql.Identifier(settings.base.analyst_role)
        )
    )
    connection.execute(
        sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA source TO {}").format(
            sql.Identifier(settings.base.analyst_role)
        )
    )
    for table in GATE311_TABLES:
        contract = fixture.contracts[table]
        columns = tuple(str(case["column"]) for case in contract.cases)
        statement = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier("source"),
            sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        parameters = [
            tuple(row[column] for column in columns)
            for row in fixture.target_rows[table]
        ]
        with connection.cursor() as cursor:
            cursor.executemany(statement, parameters)
    verify_conformance_v11._insert_scratch_provenance(connection)
    connection.commit()


def _reconcile_fixture(
    connection: psycopg.Connection,
    fixture: ScratchFixture,
    ledger: core.MismatchLedger,
    *,
    begin_snapshot: bool,
) -> tuple[dict[str, TableRunEvidence], dict[int, int]]:
    """Call the production per-table pipeline over all eleven scratch sources."""
    if begin_snapshot:
        begin_read_only_snapshot(connection)
    primary_ids: dict[int, int] = {}
    output: dict[str, TableRunEvidence] = {}
    for table, contract in fixture.contracts.items():
        plan = build_sample_plan(contract, sample_limit=contract.expected_rows)
        output[table], primary_ids = reconcile_one_table(
            connection,
            contract,
            plan,
            primary_ids=primary_ids or None,
            batch_rows=2,
            ledger=ledger,
        )
    if begin_snapshot:
        connection.rollback()
    return output, primary_ids


def _detect_scratch_mutation(
    settings: ReconciliationSettings,
    scratch: str,
    fixture: ScratchFixture,
    *,
    table: str,
    statements: Sequence[Any],
    primary_ids: Mapping[int, int],
    ledger_root: Path,
    label: str,
) -> None:
    """Require one intended scratch mismatch, rollback, then re-establish GREEN."""
    contract = fixture.contracts[table]
    plan = build_sample_plan(contract, sample_limit=contract.expected_rows)
    ledger = core.MismatchLedger.create(
        ledger_root / f"{label}.jsonl", allowed_root=ledger_root
    )
    detected = False
    with _connect_scratch_dict(settings, scratch) as connection:
        try:
            for statement in statements:
                connection.execute(statement)
            try:
                result, _ = reconcile_one_table(
                    connection,
                    contract,
                    plan,
                    primary_ids=primary_ids or None,
                    batch_rows=2,
                    ledger=ledger,
                )
            except ValueError as exc:
                detected = any(
                    text in str(exc)
                    for text in (
                        "target/source table count mismatch",
                        "target sampled key boundary mismatch",
                        "target key multiplicity mismatch",
                    )
                )
                if not detected:
                    raise
            else:
                detected = result.metrics["mismatch_count"] > 0
            if not detected:
                raise ValueError("scratch value mutation was not detected")
        finally:
            connection.rollback()
            ledger.abort()
    clean_ledger = core.MismatchLedger.create(
        ledger_root / f"{label}-clean.jsonl", allowed_root=ledger_root
    )
    with _connect_scratch_dict(settings, scratch) as connection:
        begin_read_only_snapshot(connection)
        result, _ = reconcile_one_table(
            connection,
            contract,
            plan,
            primary_ids=primary_ids or None,
            batch_rows=2,
            ledger=clean_ledger,
        )
        connection.rollback()
    if result.metrics["mismatch_count"] != 0:
        raise ValueError("scratch rollback did not restore reconciliation")
    clean_ledger.abort()


def _run_scratch_body(settings: ReconciliationSettings) -> dict[str, Any]:
    """Execute the disposable proof inside an external identity bracket."""
    config = yaml.safe_load(settings.base.config_path.read_text(encoding="utf-8"))
    prefix = str(config["database"]["scratch_prefix"])
    scratch = verify_conformance_v11.validate_scratch_name(
        prefix, prefix + __import__("uuid").uuid4().hex
    )
    result: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="cosmos_gate311_") as directory:
        root = Path(directory)
        fixture = build_scratch_fixture(root, rows_per_table=3)
        cast_parity = scratch_cast_parity_evidence(fixture)

        def create() -> None:
            verify_conformance_v11._create_scratch_database(settings.base, scratch)

        def proof() -> dict[str, Any]:
            with _connect_scratch_dict(settings, scratch) as connection:
                _insert_scratch_fixture(connection, fixture, settings)
            with verify_conformance_v11._connect_scratch(
                settings.base, scratch
            ) as connection:
                conformance = verify_conformance_v11._validate_scratch_snapshot(
                    connection
                )
                connection.rollback()
            baseline_ledger = core.MismatchLedger.create(
                root / "baseline.jsonl", allowed_root=root
            )
            with _connect_scratch_dict(settings, scratch) as connection:
                baseline, primary_ids = _reconcile_fixture(
                    connection, fixture, baseline_ledger, begin_snapshot=True
                )
            if any(table.metrics["mismatch_count"] != 0 for table in baseline.values()):
                raise ValueError("scratch baseline value mismatch")
            baseline_ledger.abort()
            mutations: list[tuple[str, str, tuple[Any, ...]]] = []
            mutations.append(
                (
                    "scalar",
                    "photometry_primary",
                    (
                        'UPDATE "source"."photometry_primary" '
                        'SET "segment_id"="segment_id"+1 WHERE "source_row"=0',
                    ),
                )
            )
            array_case = next(
                case
                for case in fixture.contracts["photometry_primary"].cases
                if str(case["target_type"]).endswith("[]")
            )
            mutations.append(
                (
                    "array_element",
                    "photometry_primary",
                    (
                        sql.SQL("UPDATE {}.{} SET {}[1]=12345 WHERE {}=0").format(
                            sql.Identifier("source"),
                            sql.Identifier("photometry_primary"),
                            sql.Identifier(str(array_case["column"])),
                            sql.Identifier("source_row"),
                        ),
                    ),
                )
            )
            mutations.extend(
                [
                    (
                        "finite_sentinel_null",
                        "lss_overdensity",
                        (
                            'UPDATE "source"."lss_overdensity" '
                            'SET "density_excess"=NULL WHERE "id"=2000',
                        ),
                    ),
                    (
                        "source_row",
                        "lephare",
                        (
                            'UPDATE "source"."lephare" '
                            'SET "source_row"=999 WHERE "source_row"=0',
                        ),
                    ),
                    (
                        "missing_row",
                        "specz_compilation_unique",
                        (
                            'DELETE FROM "source"."specz_compilation_unique" '
                            'WHERE "id_specz"=6000',
                        ),
                    ),
                    (
                        "extra_row",
                        "specz_compilation_unique",
                        (
                            'INSERT INTO "source"."specz_compilation_unique" '
                            'SELECT * FROM "source"."specz_compilation_unique" LIMIT 1',
                        ),
                    ),
                    (
                        "tuple_multiplicity",
                        "galaxy_group_memberships",
                        (
                            'UPDATE "source"."galaxy_group_memberships" '
                            'SET "assoc_prob"="assoc_prob"+1 '
                            "WHERE ctid IN (SELECT ctid FROM "
                            '"source"."galaxy_group_memberships" '
                            'WHERE "galid"=4000 AND "id"=5000 LIMIT 1)',
                        ),
                    ),
                ]
            )
            with _connect_scratch_dict(settings, scratch) as connection:
                foreign_key = connection.execute(
                    """
                    SELECT con.conname
                    FROM pg_constraint AS con
                    JOIN pg_class AS c ON c.oid=con.conrelid
                    JOIN pg_namespace AS n ON n.oid=c.relnamespace
                    WHERE n.nspname='source' AND c.relname='lephare'
                      AND con.contype='f'
                    """
                ).fetchone()["conname"]
                connection.rollback()
            mutations.append(
                (
                    "injected_id",
                    "lephare",
                    (
                        sql.SQL("ALTER TABLE {}.{} DROP CONSTRAINT {}").format(
                            sql.Identifier("source"),
                            sql.Identifier("lephare"),
                            sql.Identifier(foreign_key),
                        ),
                        'UPDATE "source"."lephare" SET "id"=-1 WHERE "source_row"=0',
                    ),
                )
            )
            for label, table, statements in mutations:
                _detect_scratch_mutation(
                    settings,
                    scratch,
                    fixture,
                    table=table,
                    statements=statements,
                    primary_ids=primary_ids,
                    ledger_root=root,
                    label=label,
                )
            return {
                "conformance_cases": conformance["case_assertions"],
                "baseline_tables": len(baseline),
                "baseline_source_reads": sum(
                    table.stream.source_reads for table in baseline.values()
                ),
                "mutations_detected": len(mutations),
                "postgresql_cast_parity": cast_parity,
            }

        def drop() -> None:
            _drop_scratch_candidate(settings, scratch)

        result = run_guarded_scratch_lifecycle(create=create, proof=proof, drop=drop)
    return {
        **result,
        "scratch_absent": True,
        "direct_network_auth_exercised": False,
    }


def run_scratch_proof(settings: ReconciliationSettings) -> dict[str, Any]:
    """Prove scratch behavior while checking protected identity on every exit."""
    before = capture_protected_identity(settings)
    try:
        result = _run_scratch_body(settings)
    finally:
        after = capture_protected_identity(settings)
        if after != before:
            raise ValueError(
                "protected identity changed during Gate 3.11 scratch proof"
            )
    return {**result, "protected_identity_unchanged": True}


# =============================================================================
# Persistent read-only orchestration
# =============================================================================


def _connect_target(settings: ReconciliationSettings) -> psycopg.Connection:
    """Connect only to the fixed target with credentials kept in keyword args."""
    base = settings.base
    return psycopg.connect(
        host=base.host,
        port=base.port,
        user=base.user,
        password=base.password,
        dbname=base.target_database,
        row_factory=dict_row,
    )


def capture_protected_identity(
    settings: ReconciliationSettings,
) -> Gate311ProtectedIdentity:
    """Capture schema/security plus exact row and transaction-ID observations."""
    base_identity = verify_conformance_v11._protected_identity(settings.base)
    rows: list[tuple[str, int, tuple[str, ...]]] = []
    with _connect_target(settings) as connection:
        begin_read_only_snapshot(connection)
        for table in GATE311_TABLES:
            statement = sql.SQL(
                "SELECT count(*) AS row_count, "
                "array_agg(DISTINCT xmin::text ORDER BY xmin::text) AS xids "
                "FROM {}.{}"
            ).format(sql.Identifier("source"), sql.Identifier(table))
            observed = connection.execute(statement).fetchone()
            if observed is None or not isinstance(observed["row_count"], int):
                raise ValueError("protected target row/XID observation mismatch")
            xids = tuple(observed["xids"] or ())
            if not xids or any(not isinstance(value, str) for value in xids):
                raise ValueError("protected target XID boundary mismatch")
            rows.append((table, observed["row_count"], xids))
        connection.rollback()
    return Gate311ProtectedIdentity(base=base_identity, row_xids=tuple(rows))


def _sum_batch_evidence(
    batches: Sequence[BatchReconciliationEvidence],
) -> dict[str, int]:
    """Sum only runtime-observed batch metrics for one table."""
    return {
        "sampled_rows": sum(item.sampled_rows for item in batches),
        "row_column_comparisons": sum(item.row_column_comparisons for item in batches),
        "metadata_comparisons": sum(item.metadata_comparisons for item in batches),
        "array_cells": sum(item.array_cells for item in batches),
        "array_element_comparisons": sum(
            item.array_element_comparisons for item in batches
        ),
        "mismatch_count": sum(item.mismatch_count for item in batches),
    }


def _fresh_generated_contract(settings: ReconciliationSettings) -> None:
    """Prove the configured generated cases still equal sealed dictionary bytes."""
    dictionary_path, output_path = generate_conformance_v11.configured_paths(
        settings.base.config_path
    )
    if output_path != settings.cases_path:
        raise ValueError("configured generated case identity mismatch")
    generate_conformance_v11.write_or_check(
        generate_conformance_v11._read_dictionary(dictionary_path),
        output_path,
        check=True,
    )


def fresh_gate311_pins(
    settings: ReconciliationSettings,
    contracts: Mapping[str, TableContract],
) -> dict[str, Any]:
    """Freshly hash only the eleven source bytes bound by one stable manifest."""
    if tuple(contracts) != GATE311_TABLES:
        raise ValueError("Gate 3.11 pin table boundary mismatch")
    manifest_path = settings.base.manifest_path
    digest_before = verify_source_fidelity.sha256_of(manifest_path)
    manifest = bootstrap_v11._manifest_contract(settings.base)
    pins = {
        table: verify_source_fidelity.pin_manifest_input(
            table, contracts[table].source_path, manifest
        )
        for table in GATE311_TABLES
    }
    digest_after = verify_source_fidelity.sha256_of(manifest_path)
    if digest_after != digest_before:
        raise ValueError("source manifest changed during Gate 3.11 pin reads")
    if any(pin.declared_sha256 != pin.observed_sha256 for pin in pins.values()):
        raise ValueError("Gate 3.11 source pin mismatch")
    return pins


def reconcile_one_table(
    connection: Any,
    contract: TableContract,
    plan: SamplePlan,
    *,
    primary_ids: Mapping[int, int] | None,
    batch_rows: int,
    ledger: core.MismatchLedger | None,
) -> tuple[TableRunEvidence, dict[int, int]]:
    """Count, stream, fetch, compare, and discard one complete table sample."""
    count_statement = sql.SQL("SELECT count(*) AS row_count FROM {}.{}").format(
        sql.Identifier("source"), sql.Identifier(contract.table)
    )
    count_row = connection.execute(count_statement).fetchone()
    if count_row is None or not isinstance(count_row.get("row_count"), int):
        raise ValueError("target table count observation mismatch")
    if count_row["row_count"] != contract.expected_rows:
        _write_mismatch(
            ledger,
            source_locator=contract.source_locator,
            table=contract.table,
            column="[table_row_count]",
            source_value=("row_count", contract.expected_rows),
            database_value=("row_count", count_row["row_count"]),
            matching_method="table_count",
            sample_locator="[table]",
            element_index=None,
        )
        raise RecordedMismatch(1, "target/source table count mismatch")
    batch_metrics: list[BatchReconciliationEvidence] = []

    def consume(
        rows: tuple[ExpectedSourceRow, ...],
        matching_method: str,
        multiplicities: Mapping[tuple[Any, ...], int],
        tuple_locators: Mapping[tuple[Any, ...], str],
    ) -> None:
        target = fetch_target_rows(connection, contract, rows)
        batch_metrics.append(
            reconcile_expected_batch(
                contract,
                rows,
                target,
                matching_method=matching_method,
                native_tuple_multiplicities=multiplicities,
                ledger=ledger,
                native_tuple_locators=tuple_locators,
            )
        )

    stream, sampled_primary_ids = stream_source_batches(
        contract,
        plan,
        primary_ids=primary_ids,
        batch_rows=batch_rows,
        consume=consume,
    )
    metrics = _sum_batch_evidence(batch_metrics)
    if metrics["sampled_rows"] != plan.sample_size:
        raise ValueError("table sampled-row comparison mismatch")
    return TableRunEvidence(stream=stream, metrics=metrics), sampled_primary_ids


def _run_live_body(
    settings: ReconciliationSettings, before: Gate311ProtectedIdentity
) -> dict[str, Any]:
    """Run source and target comparison inside an external identity bracket."""
    _fresh_generated_contract(settings)
    contracts = build_table_contracts(CASES)
    source_pins = fresh_gate311_pins(settings, contracts)
    conformance = verify_conformance_v11.run_live(settings.base)
    plans = {
        table: build_sample_plan(contract, sample_limit=settings.sample_rows)
        for table, contract in contracts.items()
    }
    derived_totals = derive_success_totals(
        contracts, {table: plan.sample_size for table, plan in plans.items()}
    )
    validate_success_totals(derived_totals)
    ledger = core.MismatchLedger.create(
        settings.mismatch_ledger_path,
        allowed_root=settings.mismatch_ledger_path.parent,
    )
    primary_ids: dict[int, int] = {}
    table_output: dict[str, Any] = {}
    total_mismatches = 0
    try:
        with _connect_target(settings) as connection:
            begin_read_only_snapshot(connection)
            for table, contract in contracts.items():
                plan = plans[table]
                table_run, primary_ids = reconcile_one_table(
                    connection,
                    contract,
                    plan,
                    primary_ids=primary_ids or None,
                    batch_rows=(
                        settings.wide_batch_rows
                        if table in MASTER_TABLES
                        else settings.batch_rows
                    ),
                    ledger=ledger,
                )
                stream = table_run.stream
                metrics = table_run.metrics
                total_mismatches += metrics["mismatch_count"]
                table_output[table] = build_table_success_evidence(
                    contract, plan, stream, metrics
                )
            connection.rollback()
        if sum(item["source_reads"] for item in table_output.values()) != 11:
            raise ValueError("logical source-read boundary mismatch")
        observed_totals = {
            "tables": len(table_output),
            "columns": sum(
                item["columns_reconciled"] for item in table_output.values()
            ),
            "native_columns": derived_totals["native_columns"],
            "metadata_columns": derived_totals["metadata_columns"],
            "sampled_table_records": sum(
                item["sampled_rows"] for item in table_output.values()
            ),
            "row_column_comparisons": sum(
                item["row_column_comparisons"] for item in table_output.values()
            ),
            "metadata_comparisons": sum(
                item["metadata_comparisons"] for item in table_output.values()
            ),
            "array_cells": sum(item["array_cells"] for item in table_output.values()),
            "array_element_comparisons": sum(
                item["array_element_comparisons"] for item in table_output.values()
            ),
        }
        validate_success_totals(observed_totals)
        if total_mismatches:
            ledger.seal()
            raise ReconciliationMismatch(
                total_mismatches, settings.mismatch_ledger_path
            )
        ledger.abort()
    except RecordedMismatch as exc:
        if not ledger._closed:
            ledger.seal()
        raise ReconciliationMismatch(
            exc.mismatch_count, settings.mismatch_ledger_path
        ) from None
    except Exception:
        if not ledger._closed:
            ledger.abort()
        raise
    return {
        "status": "passed",
        "source_integrity": "passed",
        "source_pin_count": len(source_pins),
        "conformance_case_assertions": conformance["conformance"]["case_assertions"],
        "totals": observed_totals,
        "tables": table_output,
        "mismatch_count": 0,
        "mismatch_ledger_created": False,
        "protected_identity_unchanged": True,
        "v1_fingerprint": before.base.v1_fingerprint,
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
    }


def run_live_reconciliation(settings: ReconciliationSettings) -> dict[str, Any]:
    """Run the sole live proof while checking protected identity on every exit."""
    before = capture_protected_identity(settings)
    try:
        result = _run_live_body(settings, before)
    finally:
        after = capture_protected_identity(settings)
        if after != before:
            raise ValueError("protected identity changed during reconciliation")
    return result


# =============================================================================
# Redacted CLI
# =============================================================================


def _safe_failure(stage: str, error: BaseException) -> dict[str, Any]:
    """Return only allowlisted diagnostic metadata, never exception text."""
    error_class = type(error).__name__
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", error_class) is None:
        error_class = "Exception"
    sqlstate = getattr(error, "sqlstate", None)
    if not isinstance(sqlstate, str) or re.fullmatch(r"[0-9A-Z]{5}", sqlstate) is None:
        sqlstate = None
    diagnostic = {
        "error_class": error_class,
        "sqlstate": sqlstate,
        "stage": stage,
        "status": "failed",
    }
    if isinstance(error, ReconciliationMismatch):
        diagnostic["mismatch_count"] = error.mismatch_count
        diagnostic["ledger_path"] = str(error.ledger_path)
    return diagnostic


def main() -> None:
    """Run exactly one selected Gate 3.11 read-only or scratch proof mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--live", action="store_true")
    modes.add_argument("--scratch-proof", action="store_true")
    args = parser.parse_args()
    stage = "live_reconciliation" if args.live else "scratch_proof"
    try:
        settings = resolve_settings(args.config, os.environ)
        result = (
            run_live_reconciliation(settings)
            if args.live
            else run_scratch_proof(settings)
        )
        stage = "success_output"
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except Exception as exc:
        raise SystemExit(
            json.dumps(_safe_failure(stage, exc), sort_keys=True)
        ) from None


if __name__ == "__main__":
    main()
