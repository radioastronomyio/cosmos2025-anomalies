#!/usr/bin/env python3
"""
Script Name  : test_reconcile_values_v11.py
Description  : Test Gate 3.11 source-fresh value reconciliation
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises real generated contracts and small FITS/text sources before the
authenticated disposable and live reconciliation proofs.

Usage
-----
    pytest tests/test_reconcile_values_v11.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.io import fits


# =============================================================================
# Configuration and loader
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "reconcile_values_v11.py"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl.conformance_cases_v11 import CASES  # noqa: E402


def _module():
    """Load production after test start so the absent reconciler is an honest RED."""
    assert MODULE_PATH.exists(), "Gate 3.11 value reconciler is missing"
    spec = importlib.util.spec_from_file_location("reconcile_values_v11", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _case(
    *,
    table: str,
    source_file: Path,
    source_column: str,
    target_column: str,
    target_type: str,
    element_count: int = 1,
) -> dict[str, object]:
    """Build a complete literal native case for a controlled source fixture."""
    return {
        "case_id": f"fixture:{table}.{target_column}",
        "case_group": "supplement_native",
        "table": table,
        "column": target_column,
        "target_type": target_type,
        "column_origin": "source_native",
        "comment": "fixture",
        "element_count": element_count,
        "array_constraint_name": None,
        "array_constraint_expression": None,
        "source_family": "fixture",
        "source_file": str(source_file),
        "source_locator": "HDU 1",
        "source_column": source_column,
        "source_type": "fixture",
        "has_fits_mask": False,
        "has_nan": False,
        "expected_source_rows": 3,
    }


def test_direct_file_entry_resolves_repo_package_outside_checkout(
    tmp_path: Path,
) -> None:
    """The documented direct-file CLI must import ``src`` independent of cwd."""
    completed = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--scratch-proof" in completed.stdout


# =============================================================================
# Generated source/key boundary
# =============================================================================


def test_generated_table_contracts_derive_live_keys_and_historical_evidence() -> None:
    """Querying historical aliases or losing a generated column must fail."""
    module = _module()
    contracts = module.build_table_contracts(CASES)

    assert tuple(contracts) == module.GATE311_TABLES
    assert sum(len(contract.cases) for contract in contracts.values()) == 1_416
    assert contracts["lss_overdensity"].match_source_columns == ("id",)
    assert contracts["lss_overdensity"].match_target_columns == ("id",)
    assert contracts["galaxy_groups"].match_source_columns == ("ID",)
    assert contracts["galaxy_groups"].match_target_columns == ("id",)
    assert contracts["galaxy_groups"].historical_target_key == ("group_id",)
    assert contracts["galaxy_group_memberships"].match_source_columns == (
        "GALID",
        "ID",
    )
    assert contracts["galaxy_group_memberships"].match_target_columns == (
        "galid",
        "id",
    )
    assert contracts["galaxy_group_memberships"].historical_target_key == (
        "galid",
        "group_id",
    )
    assert contracts["specz_compilation"].match_source_columns == ("Id_specz",)
    assert contracts["specz_compilation"].match_target_columns == ("id_specz",)


# =============================================================================
# Real source readers
# =============================================================================


def test_fits_reader_observes_unique_key_and_exact_sample_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reopening, sampling wrong rows, or changing an exact cast must fail."""
    module = _module()
    source = tmp_path / "fixture.fits"
    fits.BinTableHDU.from_columns(
        [
            fits.Column(name="ID", format="K", array=np.array([10, 20, 30])),
            fits.Column(name="VALUE", format="D", array=np.array([1.5, -999.0, 3.5])),
            fits.Column(
                name="VECTOR",
                format="2E",
                array=np.array([[1.0, 2.0], [-0.0, np.nan], [5.0, 6.0]]),
            ),
        ]
    ).writeto(source)
    cases = (
        _case(
            table="fixture_fits",
            source_file=source,
            source_column="ID",
            target_column="id",
            target_type="bigint",
        ),
        _case(
            table="fixture_fits",
            source_file=source,
            source_column="VALUE",
            target_column="value",
            target_type="double precision",
        ),
        _case(
            table="fixture_fits",
            source_file=source,
            source_column="VECTOR",
            target_column="vector",
            target_type="real[]",
            element_count=2,
        ),
    )
    contract = module.TableContract(
        table="fixture_fits",
        cases=cases,
        source_path=source,
        source_locator="HDU 1",
        expected_rows=3,
        match_source_columns=("ID",),
        match_target_columns=("id",),
        historical_target_key=None,
    )
    real_open = module.fits.open
    open_count = 0

    def counted_open(*args, **kwargs):
        nonlocal open_count
        open_count += 1
        return real_open(*args, **kwargs)

    monkeypatch.setattr(module.fits, "open", counted_open)

    observed = module.read_fits_sample(contract, (0, 1, 2), primary_ids=None)

    assert observed.total_rows == 3
    assert observed.distinct_key_rows == 3
    assert observed.matching_method == "unique_key"
    assert observed.source_reads == 1
    assert open_count == 1
    assert [row.match_key[0].token for row in observed.sample_rows] == [
        ("bigint", 10),
        ("bigint", 20),
        ("bigint", 30),
    ]
    assert observed.sample_rows[1].values["value"].token == (
        "double precision",
        "c08f380000000000",
    )
    assert observed.sample_rows[1].values["vector"].token == (
        "real[]",
        (("real", "80000000"), ("null",)),
    )


def test_text_reader_switches_to_full_tuple_multiplicity_after_duplicate_key(
    tmp_path: Path,
) -> None:
    """Trusting a duplicate key or rereading text for fallback must fail."""
    module = _module()
    source = tmp_path / "memberships.txt"
    source.write_text(
        "GALID FIELD_PROB ID ASSOC_PROB\n"
        "1 0.25 10 0.75\n"
        "1 0.25 10 0.75\n"
        "2 0.5 11 0.5\n",
        encoding="utf-8",
    )
    definitions = (
        ("GALID", "galid", "bigint"),
        ("FIELD_PROB", "field_prob", "double precision"),
        ("ID", "id", "bigint"),
        ("ASSOC_PROB", "assoc_prob", "double precision"),
    )
    cases = tuple(
        {
            **_case(
                table="fixture_text",
                source_file=source,
                source_column=source_column,
                target_column=target_column,
                target_type=target_type,
            ),
            "source_locator": "text table, header line 1",
        }
        for source_column, target_column, target_type in definitions
    )
    contract = module.TableContract(
        table="fixture_text",
        cases=cases,
        source_path=source,
        source_locator="text table, header line 1",
        expected_rows=3,
        match_source_columns=("GALID", "ID"),
        match_target_columns=("galid", "id"),
        historical_target_key=("galid", "group_id"),
    )

    observed = module.read_text_sample(contract, (0, 1, 2))

    assert observed.total_rows == 3
    assert observed.distinct_key_rows == 2
    assert observed.matching_method == "native_tuple_multiplicity"
    assert observed.source_reads == 1
    assert sorted(observed.native_tuple_multiplicities.values()) == [1, 2]
    assert len(observed.sample_rows) == 3


def test_master_reader_uses_ordinal_key_and_constructs_source_row(
    tmp_path: Path,
) -> None:
    """Treating the generated source_row key as an empty native key must fail."""
    module = _module()
    source = tmp_path / "master.fits"
    fits.BinTableHDU.from_columns(
        [fits.Column(name="ID", format="K", array=np.array([10, 20, 30]))]
    ).writeto(source)
    native = _case(
        table="fixture_master",
        source_file=source,
        source_column="ID",
        target_column="id",
        target_type="bigint",
    )
    metadata = {
        **native,
        "case_id": "fixture:fixture_master.source_row",
        "column": "source_row",
        "column_origin": "source_row_metadata",
        "source_column": "",
    }
    contract = module.TableContract(
        table="fixture_master",
        cases=(native, metadata),
        source_path=source,
        source_locator="HDU 1",
        expected_rows=3,
        match_source_columns=(),
        match_target_columns=("source_row",),
        historical_target_key=None,
    )

    observed = module.read_fits_sample(contract, (0, 2), primary_ids=None)

    assert observed.distinct_key_rows == 3
    assert observed.matching_method == "unique_key"
    assert [row.match_key[0].token for row in observed.sample_rows] == [
        ("bigint", 0),
        ("bigint", 2),
    ]


def test_sample_plan_uses_shared_master_and_separate_table_seeds(
    tmp_path: Path,
) -> None:
    """A per-master sample or shared supplement seed must fail reproducibility."""
    module = _module()
    master = module.TableContract(
        table="photometry_primary",
        cases=(),
        source_path=tmp_path / "master.fits",
        source_locator="HDU 1",
        expected_rows=10,
        match_source_columns=(),
        match_target_columns=("source_row",),
        historical_target_key=None,
    )
    supplement = module.TableContract(
        table="galaxy_groups",
        cases=(),
        source_path=tmp_path / "groups.txt",
        source_locator="text table, header line 1",
        expected_rows=10,
        match_source_columns=("ID",),
        match_target_columns=("id",),
        historical_target_key=("group_id",),
    )

    master_plan = module.build_sample_plan(master, sample_limit=3)
    supplement_plan = module.build_sample_plan(supplement, sample_limit=3)

    assert master_plan.seed == 1_380_376_179_526_893_666
    assert master_plan.ordinals == (0, 1, 7)
    assert supplement_plan.seed == 4_652_599_078_883_424_958
    assert supplement_plan.population == 10
    assert supplement_plan.sample_size == 3
    assert supplement_plan.ordinals == (2, 4, 8)


def test_settings_resolve_all_reconciliation_paths_and_positive_bounds() -> None:
    """Hardcoded evidence paths or unbounded sample/query sizes must fail."""
    module = _module()
    environment = {
        "PGSQL01_HOST": "127.0.0.1",
        "PGSQL01_PORT": "5432",
        "PGSQL01_ADMIN_USER": "fixture_admin",
        "PGSQL01_ADMIN_PASSWORD": "fixture-password",
    }

    settings = module.resolve_settings(
        REPO_ROOT / "configs" / "data_paths.yaml", environment
    )

    assert settings.base.target_database == "cosmos2025_v11"
    assert settings.cases_path == REPO_ROOT / "src/etl/conformance_cases_v11.py"
    assert settings.mismatch_ledger_path == (
        REPO_ROOT
        / ".superpowers/sdd/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror"
        / "gate-3-11-mismatches.jsonl"
    )
    assert settings.sample_rows == 20_000
    assert settings.wide_batch_rows == 500
    assert settings.batch_rows == 2_000
    assert os.path.commonpath(
        [settings.mismatch_ledger_path, settings.base.repo_root]
    ) == str(settings.base.repo_root)


# =============================================================================
# Exact batched comparison
# =============================================================================


def _comparison_fixture(module, tmp_path: Path):
    """Return a two-column contract and independently literal expected rows."""
    id_case = _case(
        table="fixture_compare",
        source_file=tmp_path / "fixture.fits",
        source_column="ID",
        target_column="id",
        target_type="bigint",
    )
    array_case = _case(
        table="fixture_compare",
        source_file=tmp_path / "fixture.fits",
        source_column="VECTOR",
        target_column="vector",
        target_type="real[]",
        element_count=2,
    )
    contract = module.TableContract(
        table="fixture_compare",
        cases=(id_case, array_case),
        source_path=tmp_path / "fixture.fits",
        source_locator="HDU 1",
        expected_rows=2,
        match_source_columns=("ID",),
        match_target_columns=("id",),
        historical_target_key=None,
    )
    rows = (
        module.ExpectedSourceRow(
            ordinal=0,
            source_locator="HDU 1 row 0",
            match_key=(module.core.CanonicalCell(("bigint", 10)),),
            values={
                "id": module.core.CanonicalCell(("bigint", 10)),
                "vector": module.core.CanonicalCell(
                    ("real[]", (("real", "3f800000"), ("null",)))
                ),
            },
        ),
        module.ExpectedSourceRow(
            ordinal=1,
            source_locator="HDU 1 row 1",
            match_key=(module.core.CanonicalCell(("bigint", 20)),),
            values={
                "id": module.core.CanonicalCell(("bigint", 20)),
                "vector": module.core.CanonicalCell(
                    ("real[]", (("real", "40000000"), ("real", "40400000")))
                ),
            },
        ),
    )
    return contract, rows


def test_reconcile_batch_matches_reordered_exact_target_rows(tmp_path: Path) -> None:
    """Comparing by result order or skipping an array element must fail."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)
    target = (
        {"id": 20, "vector": [2.0, 3.0]},
        {"id": 10, "vector": [1.0, None]},
    )

    observed = module.reconcile_expected_batch(
        contract,
        expected,
        target,
        matching_method="unique_key",
        native_tuple_multiplicities={},
        ledger=None,
    )

    assert observed.sampled_rows == 2
    assert observed.row_column_comparisons == 4
    assert observed.array_cells == 2
    assert observed.array_element_comparisons == 4
    assert observed.metadata_comparisons == 0
    assert observed.mismatch_count == 0


def test_reconcile_batch_logs_every_value_mismatch(tmp_path: Path) -> None:
    """Stopping at the first column or omitting exact values must fail."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)
    ledger_path = tmp_path / "mismatches.jsonl"
    ledger = module.core.MismatchLedger.create(ledger_path, allowed_root=tmp_path)
    target = (
        {"id": 10, "vector": [9.0, None]},
        {"id": 20, "vector": [2.0, 9.0]},
    )

    observed = module.reconcile_expected_batch(
        contract,
        expected,
        target,
        matching_method="unique_key",
        native_tuple_multiplicities={},
        ledger=ledger,
    )
    ledger.seal()
    records = [
        __import__("json").loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]

    assert observed.mismatch_count == 2
    assert [(record["sample_locator"], record["column"]) for record in records] == [
        (0, "vector"),
        (1, "vector"),
    ]
    assert [record["element_index"] for record in records] == [0, 1]
    assert all(record["source_value"] != record["database_value"] for record in records)


@pytest.mark.parametrize(
    ("target", "message"),
    [
        (
            (
                {"id": 10, "vector": [1.0, None]},
                {"id": 20, "vector": [2.0, 3.0], "extra": 1},
            ),
            "target column boundary",
        ),
    ],
)
def test_reconcile_batch_rejects_missing_duplicate_and_extra_target_boundary(
    tmp_path: Path, target: tuple[dict[str, object], ...], message: str
) -> None:
    """A structurally impossible target column batch must fail immediately."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)

    with pytest.raises(ValueError, match=message):
        module.reconcile_expected_batch(
            contract,
            expected,
            target,
            matching_method="unique_key",
            native_tuple_multiplicities={},
            ledger=None,
        )


@pytest.mark.parametrize(
    ("target", "column", "database_value"),
    [
        (
            ({"id": 10, "vector": [1.0, None]},),
            "[match_key_presence]",
            ["absent"],
        ),
        (
            (
                {"id": 10, "vector": [1.0, None]},
                {"id": 10, "vector": [1.0, None]},
                {"id": 20, "vector": [2.0, 3.0]},
            ),
            "[match_key_multiplicity]",
            None,
        ),
    ],
)
def test_missing_and_duplicate_matches_write_complete_ledger_evidence(
    tmp_path: Path,
    target: tuple[dict[str, object], ...],
    column: str,
    database_value: list[str] | None,
) -> None:
    """Key-boundary mismatches must survive in the protected ledger."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)
    ledger_path = tmp_path / "keys.jsonl"
    ledger = module.core.MismatchLedger.create(ledger_path, allowed_root=tmp_path)

    observed = module.reconcile_expected_batch(
        contract,
        expected,
        target,
        matching_method="unique_key",
        native_tuple_multiplicities={},
        ledger=ledger,
    )
    ledger.seal()
    records = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]

    assert observed.mismatch_count == 1
    assert records[0]["column"] == column
    assert records[0]["source_locator"] in {
        expected[0].source_locator,
        expected[1].source_locator,
    }
    if database_value is not None:
        assert records[0]["database_value"] == database_value


def test_reconcile_batch_compares_complete_native_tuple_multiplicity(
    tmp_path: Path,
) -> None:
    """Falling back to candidate-key row order instead of tuple counts must fail."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)
    duplicate_expected = (expected[0], expected[0])
    source_tuple = (
        ("bigint", 10),
        ("real[]", (("real", "3f800000"), ("null",))),
    )

    passed = module.reconcile_expected_batch(
        contract,
        duplicate_expected,
        (
            {"id": 10, "vector": [1.0, None]},
            {"id": 10, "vector": [1.0, None]},
        ),
        matching_method="native_tuple_multiplicity",
        native_tuple_multiplicities={source_tuple: 2},
        ledger=None,
    )

    assert passed.mismatch_count == 0
    assert passed.row_column_comparisons == 4


def test_fallback_ledger_uses_exact_tuple_locator_or_explicit_absence(
    tmp_path: Path,
) -> None:
    """Fallback evidence must never attribute a tuple to an unrelated sample row."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)
    source_tuples = {
        (
            row.values["id"].token,
            row.values["vector"].token,
        ): row.source_locator
        for row in expected
    }
    ledger_path = tmp_path / "fallback.jsonl"
    ledger = module.core.MismatchLedger.create(ledger_path, allowed_root=tmp_path)

    observed = module.reconcile_expected_batch(
        contract,
        expected,
        (
            {"id": 10, "vector": [1.0, None]},
            {"id": 20, "vector": [2.0, 9.0]},
        ),
        matching_method="native_tuple_multiplicity",
        native_tuple_multiplicities={key: 1 for key in source_tuples},
        native_tuple_locators=source_tuples,
        ledger=ledger,
    )
    ledger.seal()
    records = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]

    assert observed.mismatch_count == 2
    assert expected[1].source_locator in {
        record["source_locator"] for record in records
    }
    assert "[absent from source]" in {record["source_locator"] for record in records}
    assert expected[0].source_locator not in {
        record["source_locator"] for record in records if record["source_value"][1] == 0
    }


class _Result:
    """Specific external-DB result double with complete used surface."""

    def __init__(self, rows=(), one=None):
        self._rows = tuple(rows)
        self._one = one

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._one


class _RecordingConnection:
    """Exercise production SQL composition while replacing only PostgreSQL I/O."""

    def __init__(self, rows=(), *, read_only="on"):
        self.rows = tuple(rows)
        self.read_only = read_only
        self.calls: list[tuple[str, object]] = []

    def execute(self, statement, parameters=None):
        rendered = (
            statement.as_string() if hasattr(statement, "as_string") else statement
        )
        self.calls.append((rendered, parameters))
        if rendered == "SHOW transaction_read_only":
            return _Result(one=(self.read_only,))
        return _Result(rows=self.rows)


class _KeyedConnection(_RecordingConnection):
    """Return exact generated rows selected by one scalar ANY parameter."""

    def execute(self, statement, parameters=None):
        rendered = (
            statement.as_string() if hasattr(statement, "as_string") else statement
        )
        self.calls.append((rendered, parameters))
        if rendered.startswith("SELECT count(*)"):
            return _Result(one={"row_count": len(self.rows)})
        if rendered == "SHOW transaction_read_only":
            return _Result(one=(self.read_only,))
        selected = set(parameters[0])
        return _Result(rows=(row for row in self.rows if row["id"] in selected))


class _DictReadOnlyConnection(_RecordingConnection):
    """Match the configured psycopg ``dict_row`` result for SHOW."""

    def execute(self, statement, parameters=None):
        rendered = (
            statement.as_string() if hasattr(statement, "as_string") else statement
        )
        self.calls.append((rendered, parameters))
        if rendered == "SHOW transaction_read_only":
            return _Result(one={"transaction_read_only": self.read_only})
        return _Result(rows=self.rows)


def test_target_fetch_uses_one_generated_scalar_key_query(tmp_path: Path) -> None:
    """Per-column queries or a historical alias must fail the batched boundary."""
    module = _module()
    contract, expected = _comparison_fixture(module, tmp_path)
    connection = _RecordingConnection(
        rows=({"id": 10, "vector": [1.0, None]}, {"id": 20, "vector": [2.0, 3.0]})
    )

    rows = module.fetch_target_rows(connection, contract, expected)

    assert len(rows) == 2
    assert len(connection.calls) == 1
    statement, parameters = connection.calls[0]
    assert statement == (
        'SELECT "id", "vector" FROM "source"."fixture_compare" WHERE "id" = ANY(%s)'
    )
    assert parameters == ([10, 20],)
    assert "group_id" not in statement


def test_target_fetch_batches_composite_key_without_alias(tmp_path: Path) -> None:
    """Flattening or renaming the exact native composite key must fail."""
    module = _module()
    source = tmp_path / "memberships.txt"
    cases = tuple(
        _case(
            table="fixture_memberships",
            source_file=source,
            source_column=source_column,
            target_column=target_column,
            target_type="bigint",
        )
        for source_column, target_column in (("GALID", "galid"), ("ID", "id"))
    )
    contract = module.TableContract(
        table="fixture_memberships",
        cases=cases,
        source_path=source,
        source_locator="text table, header line 1",
        expected_rows=2,
        match_source_columns=("GALID", "ID"),
        match_target_columns=("galid", "id"),
        historical_target_key=("galid", "group_id"),
    )
    expected = (
        module.ExpectedSourceRow(
            0,
            "row 0",
            (
                module.core.CanonicalCell(("bigint", 1)),
                module.core.CanonicalCell(("bigint", 10)),
            ),
            {},
        ),
        module.ExpectedSourceRow(
            1,
            "row 1",
            (
                module.core.CanonicalCell(("bigint", 2)),
                module.core.CanonicalCell(("bigint", 11)),
            ),
            {},
        ),
    )
    connection = _RecordingConnection(rows=())

    module.fetch_target_rows(connection, contract, expected)

    statement, parameters = connection.calls[0]
    assert statement == (
        'SELECT "galid", "id" FROM "source"."fixture_memberships" '
        'WHERE ("galid", "id") IN ((%s, %s), (%s, %s))'
    )
    assert parameters == (1, 10, 2, 11)
    assert "group_id" not in statement


def test_read_only_snapshot_is_asserted_and_batch_sizes_are_bounded() -> None:
    """A writable transaction or unbounded row fetch must fail before comparison."""
    module = _module()
    connection = _RecordingConnection()

    module.begin_read_only_snapshot(connection)

    assert connection.calls == [
        ("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY", None),
        ("SHOW transaction_read_only", None),
    ]
    assert [len(batch) for batch in module.batched(tuple(range(1_201)), 500)] == [
        500,
        500,
        201,
    ]
    with pytest.raises(ValueError, match="read-only transaction mismatch"):
        module.begin_read_only_snapshot(_RecordingConnection(read_only="off"))


def test_read_only_snapshot_accepts_configured_dict_row_shape() -> None:
    """The production ``dict_row`` connection must pass the positive assertion."""
    module = _module()

    module.begin_read_only_snapshot(_DictReadOnlyConnection())

    with pytest.raises(ValueError, match="read-only transaction mismatch"):
        module.begin_read_only_snapshot(_DictReadOnlyConnection(read_only="off"))


def test_fits_stream_delivers_bounded_batches_from_one_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Materializing a wide 20k sample or reopening per DB batch must fail."""
    module = _module()
    source = tmp_path / "master.fits"
    fits.BinTableHDU.from_columns(
        [fits.Column(name="ID", format="K", array=np.arange(1_201, dtype=np.int64))]
    ).writeto(source)
    native = {
        **_case(
            table="photometry_primary",
            source_file=source,
            source_column="ID",
            target_column="id",
            target_type="bigint",
        ),
        "expected_source_rows": 1_201,
    }
    metadata = {
        **native,
        "case_id": "fixture:photometry_primary.source_row",
        "column": "source_row",
        "column_origin": "source_row_metadata",
        "source_column": "",
    }
    contract = module.TableContract(
        table="photometry_primary",
        cases=(native, metadata),
        source_path=source,
        source_locator="HDU 1",
        expected_rows=1_201,
        match_source_columns=(),
        match_target_columns=("source_row",),
        historical_target_key=None,
    )
    plan = module.SamplePlan(
        seed=module.core.MASTER_SAMPLE_SEED,
        population=1_201,
        sample_size=1_201,
        ordinals=tuple(range(1_201)),
        digest=module.core.sample_digest(tuple(range(1_201))),
    )
    real_open = module.fits.open
    open_count = 0
    batch_sizes: list[int] = []

    def counted_open(*args, **kwargs):
        nonlocal open_count
        open_count += 1
        return real_open(*args, **kwargs)

    def consume(rows, matching_method, multiplicities, tuple_locators):
        batch_sizes.append(len(rows))
        assert matching_method == "unique_key"
        assert multiplicities == {}
        assert tuple_locators == {}

    monkeypatch.setattr(module.fits, "open", counted_open)

    evidence, primary_ids = module.stream_source_batches(
        contract,
        plan,
        primary_ids=None,
        batch_rows=500,
        consume=consume,
    )

    assert batch_sizes == [500, 500, 201]
    assert open_count == 1
    assert evidence.source_reads == 1
    assert evidence.database_batches == 3
    assert evidence.sample_size == 1_201
    assert len(primary_ids) == 1_201
    assert primary_ids[0] == 0
    assert primary_ids[1_200] == 1_200


def test_success_totals_are_derived_from_generated_cases_and_samples() -> None:
    """Returning frozen totals without consuming cases/sample sizes must fail."""
    module = _module()
    contracts = module.build_table_contracts(CASES)
    sample_sizes = {
        table: min(20_000, contract.expected_rows)
        for table, contract in contracts.items()
    }

    observed = module.derive_success_totals(contracts, sample_sizes)

    assert observed == {
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
    module.validate_success_totals(observed)
    changed = dict(observed)
    changed["columns"] -= 1
    with pytest.raises(ValueError, match="Gate 3.11 success total mismatch"):
        module.validate_success_totals(changed)


def test_table_success_evidence_records_sampling_columns_and_null_states() -> None:
    """Success evidence must expose every approved reproducibility boundary."""
    module = _module()
    contract = module.build_table_contracts(CASES)["specz_compilation"]
    plan = module.build_sample_plan(contract, sample_limit=3)
    stream = SimpleNamespace(
        source_reads=1,
        database_batches=2,
        total_rows=contract.expected_rows,
        distinct_key_rows=contract.expected_rows,
        matching_method="unique_key",
    )
    metrics = {
        "sampled_rows": 3,
        "row_column_comparisons": 87,
        "metadata_comparisons": 0,
        "array_cells": 0,
        "array_element_comparisons": 0,
        "mismatch_count": 0,
    }

    observed = module.build_table_success_evidence(contract, plan, stream, metrics)

    assert observed["sampling_derivation"] == module.SAMPLING_DERIVATION
    assert observed["source_columns"] == tuple(
        case["source_column"]
        for case in contract.cases
        if case["column_origin"] == "source_native"
    )
    assert observed["target_columns"] == tuple(
        case["column"] for case in contract.cases
    )
    assert observed["reconciled_columns"] == observed["target_columns"]
    assert observed["cell_null_state_comparisons"] == 87
    assert observed["array_element_null_state_comparisons"] == 0
    assert observed["null_states_exact"] is True


def test_fresh_preflight_hashes_exact_eleven_without_record_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fresh integrity must pin bytes without invoking Gate 3.5 record sampling."""
    module = _module()
    contracts = module.build_table_contracts(CASES)
    manifest_path = tmp_path / "manifest.csv"
    manifest_path.write_text("sealed\n", encoding="utf-8")
    settings = SimpleNamespace(base=SimpleNamespace(manifest_path=manifest_path))
    calls: list[tuple[str, Path]] = []

    monkeypatch.setattr(
        module.verify_source_fidelity,
        "run_gate_3_5",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("record extraction is forbidden")
        ),
    )
    monkeypatch.setattr(
        module.verify_source_fidelity,
        "sha256_of",
        lambda path: "a" * 64,
    )
    monkeypatch.setattr(
        module.bootstrap_v11,
        "_manifest_contract",
        lambda _settings: object(),
    )

    def pin(name, path, _manifest):
        calls.append((name, path))
        return SimpleNamespace(
            declared_sha256="b" * 64,
            observed_sha256="b" * 64,
        )

    monkeypatch.setattr(module.verify_source_fidelity, "pin_manifest_input", pin)

    observed = module.fresh_gate311_pins(settings, contracts)

    assert tuple(observed) == module.GATE311_TABLES
    assert calls == [
        (table, contracts[table].source_path) for table in module.GATE311_TABLES
    ]


def test_fresh_generated_contract_executes_byte_identity_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hash-only pin helper must not bypass generated-case byte identity."""
    module = _module()
    dictionary = tmp_path / "columns.csv"
    output = tmp_path / "cases.py"
    calls: list[tuple[object, Path, bool]] = []
    settings = SimpleNamespace(
        base=SimpleNamespace(config_path=tmp_path / "config.yaml"),
        cases_path=output,
    )
    monkeypatch.setattr(
        module.generate_conformance_v11,
        "configured_paths",
        lambda _path: (dictionary, output),
    )
    monkeypatch.setattr(
        module.generate_conformance_v11,
        "_read_dictionary",
        lambda _path: ["sealed-row"],
    )
    monkeypatch.setattr(
        module.generate_conformance_v11,
        "write_or_check",
        lambda rows, path, *, check: calls.append((rows, path, check)),
    )

    module._fresh_generated_contract(settings)

    assert calls == [(["sealed-row"], output, True)]


def test_cli_redacts_unexpected_exception_text(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A source path, database value, or credential in an exception must not print."""
    module = _module()
    monkeypatch.setattr(
        module,
        "run_live_reconciliation",
        lambda settings: (_ for _ in ()).throw(
            RuntimeError("analyst-secret /immutable/source.fits row-value")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [str(MODULE_PATH), "--live"],
    )
    monkeypatch.setattr(
        module,
        "resolve_settings",
        lambda config, environment: object(),
    )

    with pytest.raises(SystemExit) as failure:
        module.main()

    rendered = str(failure.value) + capsys.readouterr().out
    assert "analyst-secret" not in rendered
    assert "/immutable/source.fits" not in rendered
    assert "row-value" not in rendered
    diagnostic = json.loads(str(failure.value))
    assert diagnostic == {
        "error_class": "RuntimeError",
        "sqlstate": None,
        "stage": "live_reconciliation",
        "status": "failed",
    }


def test_cli_redacts_success_rendering_and_broken_pipe_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Success serialization/output failures must not escape the safe boundary."""
    module = _module()
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--live"])
    monkeypatch.setattr(module, "resolve_settings", lambda *_args: object())
    monkeypatch.setattr(
        module,
        "run_live_reconciliation",
        lambda _settings: {"status": "passed", "unsafe": "row-value"},
    )
    monkeypatch.setattr(
        "builtins.print",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            BrokenPipeError("row-value analyst-secret")
        ),
    )

    with pytest.raises(SystemExit) as failure:
        module.main()

    diagnostic = json.loads(str(failure.value))
    assert diagnostic == {
        "error_class": "BrokenPipeError",
        "sqlstate": None,
        "stage": "success_output",
        "status": "failed",
    }


def test_expected_mismatch_diagnostic_reports_only_count_and_protected_path(
    tmp_path: Path,
) -> None:
    """Mismatch failures need actionable ledger metadata without row values."""
    module = _module()
    ledger = tmp_path / "mismatches.jsonl"

    diagnostic = module._safe_failure(
        "live_reconciliation", module.ReconciliationMismatch(7, ledger)
    )

    assert diagnostic == {
        "error_class": "ReconciliationMismatch",
        "ledger_path": str(ledger),
        "mismatch_count": 7,
        "sqlstate": None,
        "stage": "live_reconciliation",
        "status": "failed",
    }


# =============================================================================
# Disposable production-pipeline fixtures
# =============================================================================


def test_scratch_fixture_rewrites_all_sources_without_touching_sealed_cases(
    tmp_path: Path,
) -> None:
    """A partial table/column fixture or tracked-case mutation must fail scratch parity."""
    module = _module()
    original_first = dict(CASES[0])

    fixture = module.build_scratch_fixture(tmp_path, rows_per_table=3)

    assert len(fixture.cases) == 1_416
    assert tuple(fixture.contracts) == module.GATE311_TABLES
    assert set(fixture.target_rows) == set(module.GATE311_TABLES)
    assert all(len(rows) == 3 for rows in fixture.target_rows.values())
    assert len({contract.source_path for contract in fixture.contracts.values()}) == 11
    assert all(
        contract.source_path.is_file() for contract in fixture.contracts.values()
    )
    assert sum(len(contract.cases) for contract in fixture.contracts.values()) == 1_416
    assert dict(CASES[0]) == original_first
    memberships = fixture.contracts["galaxy_group_memberships"]
    observed = module.read_text_sample(memberships, (0, 1, 2))
    assert observed.matching_method == "native_tuple_multiplicity"
    assert observed.distinct_key_rows == 2
    assert module.scratch_cast_parity_evidence(fixture) == {
        "smallint_fits_mask_nulls": 1,
        "smallint_edges": 2,
        "bigint_edges": 2,
        "signed_zero_widths": 2,
        "positive_infinity_widths": 2,
        "negative_infinity_widths": 2,
        "finite_rounding_widths": 2,
        "finite_sentinel_values": 1,
        "array_edge_kinds": 5,
    }


def test_reconcile_one_table_streams_source_and_validates_full_target_count(
    tmp_path: Path,
) -> None:
    """Skipping target count or retaining all sampled source rows must fail."""
    module = _module()
    source = tmp_path / "lss.fits"
    fits.BinTableHDU.from_columns(
        [
            fits.Column(name="id", format="K", array=np.array([10, 20, 30])),
            fits.Column(name="VALUE", format="D", array=np.array([1.0, 2.0, 3.0])),
        ]
    ).writeto(source)
    cases = (
        _case(
            table="lss_overdensity",
            source_file=source,
            source_column="id",
            target_column="id",
            target_type="bigint",
        ),
        _case(
            table="lss_overdensity",
            source_file=source,
            source_column="VALUE",
            target_column="value",
            target_type="double precision",
        ),
    )
    contract = module.TableContract(
        table="lss_overdensity",
        cases=cases,
        source_path=source,
        source_locator="HDU 1",
        expected_rows=3,
        match_source_columns=("id",),
        match_target_columns=("id",),
        historical_target_key=None,
    )
    plan = module.SamplePlan(
        seed=module.core.TABLE_SAMPLE_SEEDS["lss_overdensity"],
        population=3,
        sample_size=3,
        ordinals=(0, 1, 2),
        digest=module.core.sample_digest((0, 1, 2)),
    )
    connection = _KeyedConnection(
        rows=(
            {"id": 10, "value": 1.0},
            {"id": 20, "value": 2.0},
            {"id": 30, "value": 3.0},
        )
    )
    ledger = module.core.MismatchLedger.create(
        tmp_path / "mismatches.jsonl", allowed_root=tmp_path
    )

    observed, primary_ids = module.reconcile_one_table(
        connection,
        contract,
        plan,
        primary_ids=None,
        batch_rows=2,
        ledger=ledger,
    )
    ledger.abort()

    assert primary_ids == {}
    assert observed.stream.sample_size == 3
    assert observed.stream.database_batches == 2
    assert observed.metrics == {
        "sampled_rows": 3,
        "row_column_comparisons": 6,
        "metadata_comparisons": 0,
        "array_cells": 0,
        "array_element_comparisons": 0,
        "mismatch_count": 0,
    }
    assert connection.calls[0][0].startswith("SELECT count(*)")
    connection.rows += ({"id": 40, "value": 4.0},)
    with pytest.raises(ValueError, match="target/source table count mismatch"):
        module.reconcile_one_table(
            connection,
            contract,
            plan,
            primary_ids=None,
            batch_rows=2,
            ledger=None,
        )


def test_guarded_scratch_lifecycle_drops_after_failure_and_surfaces_cleanup() -> None:
    """A proof failure must not skip exact cleanup or hide cleanup failure."""
    module = _module()
    events: list[str] = []

    def create():
        events.append("create")

    def proof():
        events.append("proof")
        raise ValueError("intended proof failure")

    def drop():
        events.append("drop")

    with pytest.raises(ValueError, match="intended proof failure"):
        module.run_guarded_scratch_lifecycle(create=create, proof=proof, drop=drop)
    assert events == ["create", "proof", "drop"]

    def failed_drop():
        raise RuntimeError("cleanup failed")

    with pytest.raises(RuntimeError, match="cleanup failed"):
        module.run_guarded_scratch_lifecycle(
            create=lambda: None, proof=lambda: None, drop=failed_drop
        )

    events.clear()

    def create_then_interrupt():
        events.append("create")
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        module.run_guarded_scratch_lifecycle(
            create=create_then_interrupt,
            proof=lambda: None,
            drop=lambda: events.append("drop"),
        )
    assert events == ["create", "drop"]


def test_scratch_orchestration_rechecks_identity_after_source_open_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pre-create source failure must still close the protected identity bracket."""
    module = _module()
    config = tmp_path / "config.yaml"
    config.write_text(
        "database:\n  scratch_prefix: cosmos2025_v11_scratch_\n",
        encoding="utf-8",
    )
    settings = SimpleNamespace(base=SimpleNamespace(config_path=config))
    captures: list[str] = []

    def capture(_settings):
        captures.append("capture")
        return "unchanged"

    monkeypatch.setattr(module, "capture_protected_identity", capture)
    monkeypatch.setattr(
        module,
        "build_scratch_fixture",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("source-open")),
    )

    with pytest.raises(OSError, match="source-open"):
        module.run_scratch_proof(settings)
    assert captures == ["capture", "capture"]


def test_live_orchestration_rechecks_identity_after_target_open_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A post-preflight DB failure must still reobserve persistent identity."""
    module = _module()
    settings = SimpleNamespace(
        base=object(),
        mismatch_ledger_path=tmp_path / "mismatches.jsonl",
        sample_rows=3,
        wide_batch_rows=2,
        batch_rows=2,
    )
    contract = SimpleNamespace(table="fixture", expected_rows=3)
    captures: list[str] = []

    monkeypatch.setattr(module, "_fresh_generated_contract", lambda _settings: None)
    monkeypatch.setattr(
        module, "build_table_contracts", lambda _cases: {"fixture": contract}
    )
    monkeypatch.setattr(
        module, "fresh_gate311_pins", lambda *_args: {"fixture": object()}
    )
    monkeypatch.setattr(
        module.verify_conformance_v11,
        "run_live",
        lambda _settings: {"conformance": {"case_assertions": 1_416}},
    )
    monkeypatch.setattr(
        module,
        "build_sample_plan",
        lambda *_args, **_kwargs: SimpleNamespace(sample_size=3),
    )
    monkeypatch.setattr(
        module,
        "derive_success_totals",
        lambda *_args: dict(module.EXPECTED_SUCCESS_TOTALS),
    )
    monkeypatch.setattr(module, "validate_success_totals", lambda _totals: None)
    monkeypatch.setattr(
        module,
        "build_sample_plan",
        lambda *_args, **_kwargs: module.SamplePlan(
            seed=1,
            population=2,
            sample_size=2,
            ordinals=(0, 1),
            digest=module.core.sample_digest((0, 1)),
        ),
    )

    def capture(_settings):
        captures.append("capture")
        return "unchanged"

    monkeypatch.setattr(module, "capture_protected_identity", capture)
    monkeypatch.setattr(
        module,
        "_connect_target",
        lambda _settings: (_ for _ in ()).throw(ConnectionError("target-open")),
    )

    class Ledger:
        _closed = False

        def abort(self):
            self._closed = True

    monkeypatch.setattr(
        module.core.MismatchLedger,
        "create",
        lambda *_args, **_kwargs: Ledger(),
    )

    with pytest.raises(ConnectionError, match="target-open"):
        module.run_live_reconciliation(settings)
    assert captures == ["capture", "capture"]


def test_live_table_count_drift_seals_protected_boundary_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A normal missing/extra-row count failure must retain exact safe evidence."""
    module = _module()
    contract, _expected = _comparison_fixture(module, tmp_path)
    ledger_path = tmp_path / "mismatches.jsonl"
    settings = SimpleNamespace(
        base=object(),
        mismatch_ledger_path=ledger_path,
        sample_rows=2,
        wide_batch_rows=2,
        batch_rows=2,
    )
    captures: list[str] = []

    monkeypatch.setattr(module, "_fresh_generated_contract", lambda _settings: None)
    monkeypatch.setattr(
        module, "build_table_contracts", lambda _cases: {contract.table: contract}
    )
    monkeypatch.setattr(
        module, "fresh_gate311_pins", lambda *_args: {contract.table: object()}
    )
    monkeypatch.setattr(
        module.verify_conformance_v11,
        "run_live",
        lambda _settings: {"conformance": {"case_assertions": 1_416}},
    )
    monkeypatch.setattr(
        module,
        "derive_success_totals",
        lambda *_args: dict(module.EXPECTED_SUCCESS_TOTALS),
    )
    monkeypatch.setattr(module, "validate_success_totals", lambda _totals: None)
    monkeypatch.setattr(
        module,
        "build_sample_plan",
        lambda *_args, **_kwargs: module.SamplePlan(
            seed=1,
            population=2,
            sample_size=2,
            ordinals=(0, 1),
            digest=module.core.sample_digest((0, 1)),
        ),
    )

    def capture(_settings):
        captures.append("capture")
        return "unchanged"

    monkeypatch.setattr(module, "capture_protected_identity", capture)

    class Connection(_KeyedConnection):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def rollback(self):
            return None

        def execute(self, statement, parameters=None):
            if (
                statement
                == "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
            ):
                self.calls.append((statement, parameters))
                return _Result()
            return super().execute(statement, parameters)

    connection = Connection(rows=({"id": 10, "vector": [1.0, None]},))
    monkeypatch.setattr(module, "_connect_target", lambda _settings: connection)

    with pytest.raises(module.ReconciliationMismatch) as failure:
        module.run_live_reconciliation(settings)

    assert failure.value.mismatch_count == 1
    assert failure.value.ledger_path == ledger_path
    assert captures == ["capture", "capture"]
    assert stat.S_IMODE(ledger_path.lstat().st_mode) == 0o600
    record = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert record["column"] == "[table_row_count]"
    assert record["source_value"] == ["row_count", 2]
    assert record["database_value"] == ["row_count", 1]


def _prepare_live_failure_fixture(
    module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    rows: tuple[dict[str, object], ...],
    exit_error: BaseException | None = None,
):
    """Install one complete tiny live orchestration boundary for failure injection."""
    contract, _expected = _comparison_fixture(module, tmp_path)
    fits.BinTableHDU.from_columns(
        [
            fits.Column(name="ID", format="K", array=np.array([10, 20])),
            fits.Column(
                name="VECTOR",
                format="2E",
                array=np.array([[1.0, np.nan], [2.0, 3.0]], dtype=np.float32),
            ),
        ]
    ).writeto(contract.source_path)
    settings = SimpleNamespace(
        base=object(),
        mismatch_ledger_path=tmp_path / "mismatches.jsonl",
        sample_rows=2,
        wide_batch_rows=2,
        batch_rows=2,
    )
    captures: list[str] = []
    monkeypatch.setattr(module, "_fresh_generated_contract", lambda _settings: None)
    monkeypatch.setattr(
        module, "build_table_contracts", lambda _cases: {contract.table: contract}
    )
    monkeypatch.setattr(
        module, "fresh_gate311_pins", lambda *_args: {contract.table: object()}
    )
    monkeypatch.setattr(
        module.verify_conformance_v11,
        "run_live",
        lambda _settings: {"conformance": {"case_assertions": 1_416}},
    )
    monkeypatch.setattr(
        module,
        "build_sample_plan",
        lambda *_args, **_kwargs: module.SamplePlan(
            seed=1,
            population=2,
            sample_size=2,
            ordinals=(0, 1),
            digest=module.core.sample_digest((0, 1)),
        ),
    )
    monkeypatch.setattr(
        module,
        "derive_success_totals",
        lambda *_args: dict(module.EXPECTED_SUCCESS_TOTALS),
    )
    monkeypatch.setattr(module, "validate_success_totals", lambda _totals: None)

    def capture(_settings):
        captures.append("capture")
        return "unchanged"

    monkeypatch.setattr(module, "capture_protected_identity", capture)

    class Connection(_KeyedConnection):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            if exit_error is not None:
                raise exit_error
            return False

        def rollback(self):
            return None

        def execute(self, statement, parameters=None):
            if (
                statement
                == "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
            ):
                self.calls.append((statement, parameters))
                return _Result()
            return super().execute(statement, parameters)

    monkeypatch.setattr(module, "_connect_target", lambda _settings: Connection(rows))
    return settings, captures


def test_live_fetch_failure_aborts_ledger_and_rechecks_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A target-fetch failure must remove only its temporary and close identity."""
    module = _module()
    settings, captures = _prepare_live_failure_fixture(
        module,
        tmp_path,
        monkeypatch,
        rows=(
            {"id": 10, "vector": [1.0, None]},
            {"id": 20, "vector": [2.0, 3.0]},
        ),
    )
    monkeypatch.setattr(
        module,
        "fetch_target_rows",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ConnectionError("fetch")),
    )

    with pytest.raises(ConnectionError, match="fetch"):
        module.run_live_reconciliation(settings)

    assert captures == ["capture", "capture"]
    assert not settings.mismatch_ledger_path.exists()
    assert not tuple(tmp_path.glob(".*mismatches*.tmp"))


def test_live_ledger_write_failure_aborts_and_rechecks_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ledger-write failure must remove the exact temporary and close identity."""
    module = _module()
    settings, captures = _prepare_live_failure_fixture(
        module,
        tmp_path,
        monkeypatch,
        rows=(
            {"id": 10, "vector": [9.0, None]},
            {"id": 20, "vector": [2.0, 3.0]},
        ),
    )
    monkeypatch.setattr(
        module.core.MismatchLedger,
        "write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("ledger-write")),
    )

    with pytest.raises(OSError, match="ledger-write"):
        module.run_live_reconciliation(settings)

    assert captures == ["capture", "capture"]
    assert not settings.mismatch_ledger_path.exists()
    assert not tuple(tmp_path.glob(".*mismatches*.tmp"))


def test_live_transaction_close_failure_aborts_and_rechecks_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A context-close failure must not leave a ledger or skip identity."""
    module = _module()
    settings, captures = _prepare_live_failure_fixture(
        module,
        tmp_path,
        monkeypatch,
        rows=(
            {"id": 10, "vector": [1.0, None]},
            {"id": 20, "vector": [2.0, 3.0]},
        ),
        exit_error=OSError("transaction-close"),
    )

    with pytest.raises(OSError, match="transaction-close"):
        module.run_live_reconciliation(settings)

    assert captures == ["capture", "capture"]
    assert not settings.mismatch_ledger_path.exists()
    assert not tuple(tmp_path.glob(".*mismatches*.tmp"))


def test_live_identity_drift_overrides_success() -> None:
    """A changed after-observation must prevent any success return."""
    module = _module()
    captures = iter(("before", "after"))
    original_capture = module.capture_protected_identity
    original_body = module._run_live_body
    module.capture_protected_identity = lambda _settings: next(captures)
    module._run_live_body = lambda *_args: {"status": "passed"}
    try:
        with pytest.raises(ValueError, match="protected identity changed"):
            module.run_live_reconciliation(object())
    finally:
        module.capture_protected_identity = original_capture
        module._run_live_body = original_body
