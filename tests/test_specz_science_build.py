"""Gate 5.4 builder tests: predicates, selections, conflicts, routing.

Fixture-driven discriminators for the measurement audit and source summary
builders: zero/one/multiple usable representatives, ties and invalid
confidence ordering, flags 0/10 and unrecognized flags, every z failure
mode, exact conflict boundaries, veto asymmetry between shipped
representatives and demoted alternatives, and the distinctness of
broad-line, photometric-QSO, stellar, and mask-overlap evidence. The
full-data agreement check against the independent verifier runs separately
as ``check_build_agreement.py``.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import build as ssb  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402
from tests.test_specz_science_verify import entry, source  # noqa: E402


def make_data(
    unique: list[ssv.SpeczEntry],
    all_rows: list[ssv.SpeczEntry],
    catalog=None,
    lephare=None,
    catalog_ids: tuple[int, ...] = (1,),
) -> ssv.SnapshotData:
    return ssv.SnapshotData.build(
        catalog if catalog is not None else [source(i) for i in catalog_ids],
        lephare if lephare is not None else {i: 0 for i in catalog_ids},
        unique,
        all_rows,
    )


def z_failure_matrix():
    return [
        (None, "z_missing"),
        (float("nan"), "z_non_finite"),
        (float("inf"), "z_non_finite"),
        (-9.0, "z_non_positive"),
        (0.0, "z_non_positive"),
        (-0.0001, "z_non_positive"),
    ]


@pytest.mark.parametrize("specz,expected_reason", z_failure_matrix())
def test_z_failure_modes_and_reasons(specz, expected_reason) -> None:
    item = entry(1, id_cosmos25=1, priority=1, specz=specz, flag=3, confidence=95)
    assert ssb.z_invalid_reason(item) == expected_reason
    assert item.numeric_valid_z is (expected_reason is None)


def test_positive_finite_z_is_numeric_valid() -> None:
    item = entry(1, id_cosmos25=1, priority=1, specz=1e-4, flag=3, confidence=95)
    assert ssb.z_invalid_reason(item) is None


@pytest.mark.parametrize(
    "flag,expected",
    [
        (0, "non_measured"),
        (10, "non_measured"),
        (1, "recognized_measured"),
        (19, "recognized_measured"),
        (5, "unrecognized"),
        (-3, "unrecognized"),
        (None, "flag_missing"),
    ],
)
def test_flag_categories(flag, expected) -> None:
    assert ssb.flag_category(flag) == expected


def test_flags_0_10_and_unknown_are_never_secure() -> None:
    for flag, conf in ((0, 0), (10, -99), (5, 90), (-3, 0), (None, None)):
        item = entry(1, id_cosmos25=1, priority=1, specz=0.1, flag=flag, confidence=conf)
        assert ssb.measurement_is_secure(item) is False


def test_secure_requires_full_conjunction() -> None:
    good = entry(1, id_cosmos25=1, priority=1, specz=0.1, flag=4, confidence=97)
    assert ssb.measurement_is_secure(good) is True
    broad = entry(2, id_cosmos25=1, priority=1, specz=0.1, flag=13, confidence=95)
    assert ssb.measurement_is_secure(broad) is True
    for mutated in (
        entry(3, id_cosmos25=1, priority=1, specz=None, flag=4, confidence=97),
        entry(4, id_cosmos25=1, priority=1, specz=0.1, flag=2, confidence=97),
        entry(5, id_cosmos25=1, priority=1, specz=0.1, flag=4, confidence=94),
        entry(6, id_cosmos25=1, priority=1, specz=0.1, flag=4, confidence=101),
        entry(7, id_cosmos25=1, priority=1, specz=0.1, flag=4, confidence=95),
    ):
        assert ssb.measurement_is_secure(mutated) is False


def test_secure_block_reasons_name_every_failed_conjunct() -> None:
    item = entry(1, id_cosmos25=1, priority=1, specz=None, flag=9, confidence=200)
    reasons = ssb.secure_block_reasons(item)
    assert ssb.REASON_NOT_SECURE_Z in reasons
    assert ssb.REASON_NOT_SECURE_FLAG in reasons
    assert ssb.REASON_NOT_SECURE_CONFIDENCE_INVALID in reasons


def test_measurement_record_preserves_native_and_separates_derived() -> None:
    item = entry(42, id_cosmos25=7, priority=0, specz=-9.0, flag=5, confidence=90)
    data = make_data([], [item], catalog=[source(7)], lephare={7: 0}, catalog_ids=(7,))
    record = next(
        ssb.build_measurement_records(data, run_id="r", no_association_sentinel=-999)
    )
    assert record["native_specz"] == -9.0  # finite sentinel preserved as value
    assert record["native_flag"] == 5
    assert record["numeric_valid_z"] is False  # derived rejection, separate field
    assert record["association_status"] == ssb.ASSOCIATED
    assert record["resolved_catalog_id"] == 7
    assert record["flag_category"] == "unrecognized"


def test_measurement_association_statuses() -> None:
    sentinel = entry(1, id_cosmos25=-999, priority=0, specz=0.1, flag=3, confidence=95)
    null_id = entry(2, id_cosmos25=None, priority=0, specz=0.1, flag=3, confidence=95)
    unknown = entry(3, id_cosmos25=999999, priority=0, specz=0.1, flag=3, confidence=95)
    data = make_data([], [sentinel, null_id, unknown])
    records = {
        record["id_specz"]: record
        for record in ssb.build_measurement_records(data, run_id="r")
    }
    assert records[1]["association_status"] == ssb.NO_ASSOCIATION
    assert records[1]["resolved_catalog_id"] is None
    assert records[2]["association_status"] == ssb.NO_ASSOCIATION
    assert records[3]["association_status"] == ssb.UNRESOLVED_IDENTIFIER
    assert records[3]["resolved_catalog_id"] is None


def test_zero_one_multiple_usable_representatives() -> None:
    # Zero: no numeric-valid _unique candidate.
    data = make_data(
        [entry(1, id_cosmos25=1, priority=1, specz=-9.0, flag=3, confidence=95)],
        [entry(1, id_cosmos25=1, priority=1, specz=-9.0, flag=3, confidence=95)],
    )
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["preferred_id_specz"] is None
    assert ssb.REASON_NO_NUMERIC_VALID_UNIQUE in record["exclusion_reasons"]
    # One: usable, secure.
    data = make_data(
        [entry(2, id_cosmos25=1, priority=1, specz=0.5, flag=4, confidence=97)],
        [entry(2, id_cosmos25=1, priority=1, specz=0.5, flag=4, confidence=97)],
    )
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["preferred_id_specz"] == 2
    assert record["preferred_reported_z"] == 0.5
    assert record["corroboration_status"] == ssb.CORROBORATION_SINGLY
    # Multiple agreeing.
    rows = [
        entry(3, id_cosmos25=1, priority=1, specz=0.5, flag=4, confidence=97),
        entry(4, id_cosmos25=1, priority=0, specz=0.5001, flag=3, confidence=95),
    ]
    data = make_data(rows[:1], rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["corroboration_status"] == ssb.CORROBORATION_MULTIPLY
    assert record["preferred_id_specz"] == 3  # higher valid confidence wins


def test_preferred_tie_break_and_provenance() -> None:
    rows = [
        entry(80, id_cosmos25=1, priority=1, specz=0.4, flag=3, confidence=95),
        entry(70, id_cosmos25=1, priority=1, specz=0.5, flag=4, confidence=95),
        entry(90, id_cosmos25=1, priority=1, specz=0.6, flag=2, confidence=80),
        entry(95, id_cosmos25=1, priority=1, specz=0.7, flag=3, confidence=None),
    ]
    data = make_data(rows, rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["preferred_id_specz"] == 70  # tie at 95 -> ascending id_specz
    assert record["preferred_tie"] is True
    assert record["preferred_tied_ids"] == [70, 80]
    assert record["preferred_reported_z"] == 0.5  # copied, never averaged


def test_invalid_confidence_sorts_below_valid() -> None:
    rows = [
        entry(10, id_cosmos25=1, priority=1, specz=0.3, flag=2, confidence=120),
        entry(11, id_cosmos25=1, priority=1, specz=0.4, flag=1, confidence=50),
    ]
    data = make_data(rows, rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["preferred_id_specz"] == 11


def test_preferred_value_copied_not_averaged() -> None:
    rows = [
        entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97),
        entry(2, id_cosmos25=1, priority=1, specz=0.6, flag=4, confidence=95),
    ]
    data = make_data(rows, rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["preferred_reported_z"] == 0.4


def test_unique_numeric_conflict_ignores_confidence() -> None:
    rows = [
        entry(1, id_cosmos25=1, priority=1, specz=0.40, flag=4, confidence=97),
        entry(2, id_cosmos25=1, priority=1, specz=0.42, flag=1, confidence=50),
    ]
    data = make_data(rows, rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["unique_numeric_conflict"] is True
    assert record["eligibility_basis_primary_pre_split"] is False


def test_secure_conflict_between_shipped_representatives_vetoes() -> None:
    rows = [
        entry(1, id_cosmos25=1, priority=1, specz=0.40, flag=4, confidence=97),
        entry(2, id_cosmos25=1, priority=1, specz=0.50, flag=3, confidence=95),
    ]
    data = make_data(rows, rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["secure_all_conflict"] is True
    assert record["unique_numeric_conflict"] is True  # both numeric-valid _unique rows


def test_low_quality_demoted_disagreement_alone_does_not_veto() -> None:
    unique_row = entry(1, id_cosmos25=1, priority=1, specz=0.40, flag=4, confidence=97)
    demoted = entry(2, id_cosmos25=1, priority=0, specz=9.9, flag=1, confidence=50)
    data = make_data([unique_row], [unique_row, demoted])
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["secure_all_conflict"] is False
    assert record["unique_numeric_conflict"] is False
    assert record["other_measurement_disagreement"] is True  # audited, not vetoing
    assert record["eligibility_basis_primary_pre_split"] is True


def test_conflicting_secure_alternative_vetoes_despite_deterministic_preferred() -> None:
    unique_row = entry(1, id_cosmos25=1, priority=1, specz=0.40, flag=4, confidence=97)
    alternative = entry(2, id_cosmos25=1, priority=0, specz=0.41, flag=13, confidence=95)
    data = make_data([unique_row], [unique_row, alternative])
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["preferred_id_specz"] == 1
    assert record["secure_all_conflict"] is True
    assert record["eligibility_basis_primary_pre_split"] is False


def test_conflict_witnesses_resolve_to_audited_entries() -> None:
    rows = [
        entry(5, id_cosmos25=1, priority=1, specz=0.40, flag=4, confidence=97),
        entry(6, id_cosmos25=1, priority=1, specz=0.51, flag=3, confidence=95),
    ]
    data = make_data(rows, rows)
    record = next(ssb.build_source_records(data, run_id="r"))
    witnesses = record["conflict_witnesses"]["unique_numeric"]
    assert witnesses == [
        {
            "left_id_specz": 5,
            "right_id_specz": 6,
            "left_z": 0.40,
            "right_z": 0.51,
            "left_flag": 4,
            "right_flag": 3,
            "left_confidence": 97,
            "right_confidence": 95,
            "abs_difference": pytest.approx(0.11, abs=1e-12),
        }
    ]


def test_classification_routing_and_reasons() -> None:
    secure = [entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)]

    def record_for(lephare_type, all_rows=None, unique_rows=None):
        data = make_data(
            unique_rows or secure, all_rows or (unique_rows or secure), lephare={1: lephare_type}
        )
        return next(ssb.build_source_records(data, run_id="r"))

    galaxy = record_for(0)
    assert galaxy["classification_label"] == "galaxy"
    assert galaxy["eligibility_basis_primary_pre_split"] is True
    assert galaxy["eligibility_basis_validation_pre_split"] is False
    assert ssb.REASON_NO_BROAD_LINE_OR_QSO in galaxy["exclusion_reasons"]

    star = record_for(1)
    assert star["eligibility_basis_primary_pre_split"] is False
    assert star["eligibility_basis_validation_pre_split"] is False
    assert ssb.REASON_TYPE_STELLAR in star["exclusion_reasons"]

    qso = record_for(2)
    assert qso["photometric_qso"] is True
    assert qso["eligibility_basis_validation_pre_split"] is True
    assert qso["eligibility_basis_primary_pre_split"] is False

    unknown = record_for(None)
    assert unknown["classification_label"] == "unknown_missing"
    assert ssb.REASON_TYPE_UNKNOWN in unknown["exclusion_reasons"]
    assert unknown["eligibility_basis_primary_pre_split"] is False

    unrecognized = record_for(7)
    assert unrecognized["classification_label"] == "unknown_unrecognized"
    assert unrecognized["eligibility_basis_primary_pre_split"] is False


def test_broad_line_evidence_blocks_primary_and_routes_validation() -> None:
    unique_row = entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)
    broad = entry(2, id_cosmos25=1, priority=0, specz=0.4002, flag=13, confidence=95)
    data = make_data([unique_row], [unique_row, broad], lephare={1: 0})
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["broad_line_reported"] is True
    assert record["broad_line_entry_ids"] == [2]
    assert record["broad_line_confidences"] == [95]
    assert record["eligibility_basis_primary_pre_split"] is False
    assert record["eligibility_basis_validation_pre_split"] is True
    assert ssb.REASON_BROAD_LINE_PRESENT in record["exclusion_reasons"]


def test_broad_line_requires_numeric_valid_measurement() -> None:
    unique_row = entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)
    broad_invalid_z = entry(2, id_cosmos25=1, priority=0, specz=-9.0, flag=19, confidence=85)
    data = make_data([unique_row], [unique_row, broad_invalid_z], lephare={1: 0})
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["broad_line_reported"] is False
    assert record["eligibility_basis_primary_pre_split"] is True


def test_flag_star_cannot_change_classification_or_eligibility() -> None:
    secure = [entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)]
    masked = source(1)
    masked = ssv.CatalogSource(
        id=1, ra=masked.ra, dec=masked.dec, tile="A1",
        flag_star=True, flag_blend=False,
        mag_f150w=25.0, mag_f277w=24.0, mag_f444w=23.0,
        link_id_specz=None,
    )
    data = ssv.SnapshotData.build([masked], {1: 0}, secure, secure)
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["classification_label"] == "galaxy"
    assert record["eligibility_basis_primary_pre_split"] is True
    assert record["flag_star_mask_overlap"] is True  # carried as context only


def test_population_a_source_reasons_and_null_preferred() -> None:
    a_entry = entry(9, id_cosmos25=1, priority=0, specz=0.3, flag=3, confidence=95)
    data = make_data([], [a_entry])
    record = next(ssb.build_source_records(data, run_id="r"))
    assert record["population_a"] is True
    assert record["preferred_id_specz"] is None
    assert ssb.REASON_A_ONLY_NO_UNIQUE in record["exclusion_reasons"]
    assert record["eligibility_basis_primary_pre_split"] is False


def test_no_association_source_reason() -> None:
    data = make_data([], [])
    record = next(ssb.build_source_records(data, run_id="r"))
    assert ssb.REASON_NO_ASSOCIATION in record["exclusion_reasons"]
    assert record["association_resolved"] is False


def test_mutual_exclusivity_holds_on_fixture_zoo() -> None:
    cases = []
    base_secure = entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)
    broad = entry(2, id_cosmos25=1, priority=0, specz=0.4001, flag=12, confidence=80)
    for lephare_type in (0, 1, 2, None, 9):
        for extra in ([], [broad]):
            all_rows = [base_secure, *extra]
            data = make_data([base_secure], all_rows, lephare={1: lephare_type})
            cases.append(next(ssb.build_source_records(data, run_id="r")))
    for record in cases:
        assert not (
            record["eligibility_basis_primary_pre_split"]
            and record["eligibility_basis_validation_pre_split"]
        )


def test_finalize_eligibility_applies_split_gate() -> None:
    secure = [entry(1, id_cosmos25=1, priority=1, specz=0.4, flag=4, confidence=97)]
    data = make_data(secure, secure)
    record = next(ssb.build_source_records(data, run_id="r"))
    assigned = ssb.finalize_eligibility(record, "development", "unassigned")
    assert assigned["eligibility_primary_galaxy"] is True
    assert assigned["assigned_split"] == "development"
    blocked = ssb.finalize_eligibility(record, "unassigned", "unassigned")
    assert blocked["eligibility_primary_galaxy"] is False
    assert ssb.REASON_SPLIT_UNASSIGNED in blocked["exclusion_reasons"]
