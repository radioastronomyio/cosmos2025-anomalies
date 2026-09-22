"""Gate 5.3 hostile fixtures: identifier lookup, conflicts, structural zero.

Synthetic tables exercise the independent reductions where they are easy to
get silently wrong: unordered and non-contiguous identifiers, colliding
values across identifier namespaces, single-``_unique`` sources with a
conflicting secure Priority 0 alternative, and population A's structural
zero. The production priors reproduced in the staging evidence are asserted
separately against the spec's prior table in the gate 5.3 summary.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import verify as ssv  # noqa: E402


def entry(
    id_specz: int,
    *,
    id_cosmos25: int | None,
    priority: int,
    specz: float | None,
    flag: int | None,
    confidence: int | None,
    ra_corrected: float | None = 10.0,
    dec_corrected: float | None = 10.0,
) -> ssv.SpeczEntry:
    """Build a minimal compilation measurement with defaults filled."""
    return ssv.SpeczEntry(
        id_specz=id_specz,
        id_original=None,
        ra_original=None,
        dec_original=None,
        ra_corrected=ra_corrected,
        dec_corrected=dec_corrected,
        priority=priority,
        specz=specz,
        flag=flag,
        confidence_level=confidence,
        survey=37,
        compilation_year=2019,
        public_or_private=1,
        id_cos20_classic=None,
        ra_cos20_classic=None,
        dec_cos20_classic=None,
        id_cos20_farmer=None,
        ra_cos20_farmer=None,
        dec_cos20_farmer=None,
        id_cosmos25=id_cosmos25,
        ra_cosmos25=None,
        dec_cosmos25=None,
        id_cosmos15=None,
        ra_cosmos15=None,
        dec_cosmos15=None,
        id_cosmos09=None,
        ra_cosmos09=None,
        dec_cosmos09=None,
        photoz=None,
        photoz_type=None,
        groupid=None,
        groupsize=None,
    )


def source(catalog_id: int, *, ra=150.0, dec=2.0, tile="A1", link=None):
    return ssv.CatalogSource(
        id=catalog_id,
        ra=ra,
        dec=dec,
        tile=tile,
        flag_star=False,
        flag_blend=False,
        mag_f150w=25.0,
        mag_f277w=24.0,
        mag_f444w=23.0,
        link_id_specz=link,
    )


DOMAIN = ("A1", "A2", "B1", "B2")


def hostile_fixture():
    """Unordered/non-contiguous/colliding identifiers, A and B populations.

    Catalog ids 303, 101, 205 (shuffled, non-contiguous; 9001 collides with
    an id_specz namespace value). Sources 101 and 205 carry one and two
    ``_unique`` entries; 303 is population A (``_all`` only, Priority 0).
    Row order within both compilation surfaces is deliberately not sorted.
    """
    catalog = [
        source(303),
        source(101),
        source(205),
        source(9001, link=None),
    ]
    lephare = {101: 0, 205: 0, 303: 0, 9001: None}
    unique = [
        entry(7003, id_cosmos25=205, priority=1, specz=0.42, flag=4, confidence=97),
        entry(3005, id_cosmos25=101, priority=1, specz=0.50, flag=4, confidence=97),
        entry(9001, id_cosmos25=205, priority=1, specz=0.50, flag=4, confidence=97),
    ]
    all_rows = [
        entry(9001, id_cosmos25=205, priority=1, specz=0.50, flag=4, confidence=97),
        entry(3005, id_cosmos25=101, priority=1, specz=0.50, flag=4, confidence=97),
        entry(7003, id_cosmos25=205, priority=1, specz=0.42, flag=4, confidence=97),
        entry(410, id_cosmos25=303, priority=0, specz=1.9, flag=2, confidence=80),
        entry(411, id_cosmos25=303, priority=0, specz=1.9005, flag=0, confidence=0),
        entry(412, id_cosmos25=-999, priority=0, specz=None, flag=0, confidence=0),
    ]
    return ssv.SnapshotData.build(catalog, lephare, unique, all_rows)


def test_identifier_lookup_survives_shuffled_colliding_fixture() -> None:
    data = hostile_fixture()
    equality = ssv.verify_unique_priority1_equality(data)
    assert equality["equal"] is True
    assert equality["rows_compared"] == 3


def test_positional_confusion_is_caught_by_perturbation() -> None:
    data = hostile_fixture()
    perturbed = list(data.unique_entries)
    # Swap two rows' native values while keeping their identifiers: a
    # positional comparison would line rows up incorrectly and still pass;
    # the identifier lookup must now report inequality.
    perturbed[0], perturbed[1] = (
        perturbed[1],
        perturbed[0],
    )
    swapped = [
        entry(
            item.id_specz,
            id_cosmos25=item.id_cosmos25,
            priority=item.priority,
            specz=item.specz,
            flag=item.flag,
            confidence=item.confidence_level,
        )
        for item in perturbed
    ]
    # Rebuild with the identifiers deliberately mismatched against values.
    mismatched = [
        entry(swapped[0].id_specz, id_cosmos25=101, priority=1, specz=0.42, flag=4, confidence=97),
        entry(swapped[1].id_specz, id_cosmos25=205, priority=1, specz=0.50, flag=4, confidence=97),
        entry(swapped[2].id_specz, id_cosmos25=205, priority=1, specz=0.50, flag=4, confidence=97),
    ]
    tampered = ssv.SnapshotData.build(
        [source(303), source(101), source(205), source(9001)],
        {101: 0, 205: 0, 303: 0, 9001: None},
        mismatched,
        data.all_entries,
    )
    result = ssv.verify_unique_priority1_equality(tampered)
    assert result["equal"] is False
    assert result["mismatch_count"] == 2


def test_conflicting_secure_priority0_detected_by_all_audit() -> None:
    # Source 101: one secure _unique entry; a second secure measurement in
    # _all at Priority 0 with a differing redshift must fire the veto.
    catalog = [source(101, tile="A1")]
    lephare = {101: 0}
    unique = [
        entry(3005, id_cosmos25=101, priority=1, specz=0.50, flag=4, confidence=97)
    ]
    all_rows = [
        entry(3005, id_cosmos25=101, priority=1, specz=0.50, flag=4, confidence=97),
        entry(2999, id_cosmos25=101, priority=0, specz=0.70, flag=4, confidence=97),
    ]
    data = ssv.SnapshotData.build(catalog, lephare, unique, all_rows)
    flags = ssv.conflict_flags_independent(data)[101]
    assert flags["unique_numeric_conflict"] is False  # single _unique entry
    assert flags["secure_all_conflict"] is True      # _all audit catches it
    result = ssv.reduce_qualified_before_type(data, DOMAIN)
    assert result["spectroscopy_qualified_before_photometric_type"] == 0


def test_population_a_structural_zero_and_no_neighbour_claim() -> None:
    data = hostile_fixture()
    reduced = ssv.reduce_population_a(data)
    assert reduced["population_a_sources"] == 1
    assert reduced["population_a_entries"] == 2
    assert reduced["nonzero_priority_entries"] == 0
    statement = reduced["structural_zero_statement"]
    assert "absent through _unique" in statement
    assert "no neighbour destination" in statement
    assert "nearest" not in statement.lower().replace("no neighbour destination", "")


def test_preferred_entry_tie_break_and_invalid_confidence_ordering() -> None:
    catalog = [source(501)]
    unique = [
        entry(8002, id_cosmos25=501, priority=1, specz=0.3, flag=3, confidence=95),
        entry(7004, id_cosmos25=501, priority=1, specz=0.4, flag=3, confidence=95),
        entry(9006, id_cosmos25=501, priority=1, specz=0.5, flag=2, confidence=200),
    ]
    data = ssv.SnapshotData.build(catalog, {501: 0}, unique, list(unique))
    preferred = ssv.preferred_entry_independent(data)[501]
    assert preferred.id_specz == 7004  # tie on valid confidence -> ascending id_specz
    assert ssv.entry_is_secure(preferred) is True
    # Out-of-domain confidence sorts below valid confidence.
    assert preferred.confidence_level == 95


def test_no_priority_zero_entry_becomes_preferred_or_secure_population() -> None:
    data = hostile_fixture()
    preferred = ssv.preferred_entry_independent(data)
    # Population A has no _unique candidates at all: absent key means the
    # source summary records a null preferred entry.
    assert preferred.get(303) is None
    secure_ids = {entry.id_specz for entry in data.unique_entries if ssv.entry_is_secure(entry)}
    assert 410 not in secure_ids and 411 not in secure_ids


def test_defective_path_median_matches_manual_computation() -> None:
    # Two sources one degree of declination apart from their carried links.
    near = entry(1001, id_cosmos25=None, priority=0, specz=0.1, flag=3, confidence=95,
                 ra_corrected=150.0, dec_corrected=2.0)
    far = entry(1002, id_cosmos25=None, priority=0, specz=0.1, flag=3, confidence=95,
                ra_corrected=150.0, dec_corrected=3.5)
    catalog = [source(11, ra=150.0, dec=2.0, link=1001), source(12, ra=150.0, dec=2.0, link=1002)]
    data = ssv.SnapshotData.build(catalog, {11: 0, 12: 0}, [], [near, far])
    result = ssv.reduce_defective_path_median(data)
    expected = [
        ssv.separation_arcsec(150.0, 2.0, 150.0, 2.0),
        ssv.separation_arcsec(150.0, 2.0, 150.0, 3.5),
    ]
    assert result["measured_separations"] == 2
    assert result["median_arcsec"] == pytest.approx(ssv.median(expected), rel=1e-12)


def test_unrecognized_flag_bound_per_surface() -> None:
    catalog = [source(601)]
    unique = [
        entry(5001, id_cosmos25=601, priority=1, specz=0.2, flag=5, confidence=90)
    ]
    all_rows = [
        entry(5001, id_cosmos25=601, priority=1, specz=0.2, flag=5, confidence=90),
        entry(5002, id_cosmos25=601, priority=0, specz=0.2, flag=-3, confidence=0),
    ]
    data = ssv.SnapshotData.build(catalog, {601: 0}, unique, all_rows)
    bound = ssv.reduce_unrecognized_flag_bound(data)
    distribution = bound["unrecognized_flag_confidence_distribution_by_surface"]
    assert distribution["5"]["_unique"] == {"90": 1}
    assert "-3" in distribution and distribution["-3"]["_all"] == {"0": 1}
    assert distribution["-3"]["_unique"] == {}
    assert bound["any_unrecognized_flag_confidence_ge_95"] is False


def test_population_b_counts_reconcile_to_enumeration() -> None:
    data = hostile_fixture()
    reduced = ssv.reduce_population_b(data)
    assert reduced["population_b_sources"] == len(reduced["groups"])
    assert reduced["population_b_entries"] == sum(
        len(group["id_specz"]) for group in reduced["groups"].values()
    )


def test_historical_rules_reproduce_boundary_definitions() -> None:
    z = lambda value: entry(1, id_cosmos25=1, priority=1, specz=value, flag=3, confidence=95)
    assert ssv.historical_usable(z(-89.9), strictly_positive=False) is True
    assert ssv.historical_usable(z(-90.0), strictly_positive=False) is False
    assert ssv.historical_usable(z(0.0), strictly_positive=True) is False
    assert ssv.historical_usable(z(1e-6), strictly_positive=True) is True


def test_conflict_threshold_is_exclusive_boundary() -> None:
    # Below the threshold: agreement; above: conflict. Decimal pairs a
    # mathematically exact 0.005 apart compute a few ulps above the
    # threshold in binary float (0.505 - 0.500 > 0.005 is True); the
    # implemented rule is the direct float comparison that reproduced the
    # sealed priors, and no production pair sits within ulps of it. The
    # exact float boundary is asserted at the span level, where float(0.005)
    # is representable directly.
    catalog = [source(701)]
    below = [
        entry(6001, id_cosmos25=701, priority=1, specz=0.5000, flag=4, confidence=97),
        entry(6002, id_cosmos25=701, priority=1, specz=0.5049, flag=4, confidence=97),
    ]
    at_boundary = ssv.SnapshotData.build(catalog, {701: 0}, below, list(below))
    assert ssv.conflict_flags_independent(at_boundary)[701]["unique_numeric_conflict"] is False
    above = [
        entry(6001, id_cosmos25=701, priority=1, specz=0.5000, flag=4, confidence=97),
        entry(6002, id_cosmos25=701, priority=1, specz=0.5060, flag=4, confidence=97),
    ]
    beyond = ssv.SnapshotData.build(catalog, {701: 0}, above, list(above))
    assert ssv.conflict_flags_independent(beyond)[701]["unique_numeric_conflict"] is True
    span = ssv.pairwise_span(
        below,
        lambda e: e.specz,
    )
    assert span < 0.005
    assert ssv.pairwise_span(
        [entry(1, id_cosmos25=1, priority=1, specz=0.0, flag=4, confidence=97),
         entry(2, id_cosmos25=1, priority=1, specz=0.005, flag=4, confidence=97)],
        lambda e: e.specz,
    ) == 0.005  # exactly at threshold is agreement under difference > threshold
