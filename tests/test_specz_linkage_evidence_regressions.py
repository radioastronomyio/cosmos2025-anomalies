#!/usr/bin/env python3
"""
Script Name  : test_specz_linkage_evidence_regressions.py
Description  : Discriminating regressions for the P2R-04 evidence-layer defects
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31

Description
-----------
Two defect families are covered.

D1 is identifier-space conflation in the gate 4.1 verifier. The tests assert
the *association* the pairing produces, meaning which catalog source each
stored link value is attached to, established by direct lookup in the fixture
rather than by any arithmetic the code under test also performs. A test that
asserted only a separation statistic would survive a future off-by-one, so no
D1 assertion is written against a distance.

D2 is silent category loss in the gate 4.7 characterizer. Every expected
bucket and every expected total is derived here, from the fixture, by a plain
Python reduction. No D2 assertion compares two fields that both originate
from the generator under test, because two fields the generator computed from
the same intermediate agree whether or not either is right.

Both families carry negative controls: the defective pairings and the
mutilated distributions are run through the same assertion helpers the
positive tests use, and are required to be rejected. A check that cannot be
made to fail is not a check.

Usage
-----
    pytest tests/test_specz_linkage_evidence_regressions.py -v
"""

# =============================================================================
# Imports
# =============================================================================

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from astropy.table import Table

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import characterize_specz_linkage_v11 as characterize  # noqa: E402
from src.etl import verify_specz_linkage_v11 as verify  # noqa: E402

# =============================================================================
# Fixtures
# =============================================================================

LINK_SENTINEL = -999

# D1 association fixture. Catalog identifiers are deliberately unordered and
# non-contiguous, and link value 20 collides with catalog identifier 20 while
# link value 21 matches no catalog identifier at all. The collision catches a
# pairing that selects by identifier; the absence catches one that silently
# drops what it cannot address that way.
D1_CATALOG: tuple[dict[str, float], ...] = (
    {"id": 30, "ra": 30.0, "dec": 0.0, "link": 21},
    {"id": 10, "ra": 0.0, "dec": 0.0, "link": 20},
    {"id": 20, "ra": 10.0, "dec": 0.0, "link": LINK_SENTINEL},
    {"id": 41, "ra": 41.0, "dec": 0.0, "link": LINK_SENTINEL},
)
D1_SPECZ_IDS: tuple[int, ...] = (20, 21)

# End-to-end fixture for the whole gate 4.1 command. Catalog identifiers are a
# permutation of 0..3 so that `Id_COSMOS25` values are real catalog
# identifiers whose positions differ from their values.
E2E_CATALOG: tuple[dict[str, float], ...] = (
    {"id": 3, "ra": 30.0, "dec": 0.0, "link": 21},
    {"id": 0, "ra": 0.0, "dec": 0.0, "link": 20},
    {"id": 2, "ra": 10.0, "dec": 0.0, "link": LINK_SENTINEL},
    {"id": 1, "ra": 41.0, "dec": 0.0, "link": LINK_SENTINEL},
)

# Gate 4.7 characterizer fixture, held at module scope so the tests can reduce
# it independently instead of restating hand-counted literals.
C_CATALOG_ID = (10, 20, 30, 40, 50)
C_CATALOG_RA = (0.0, 1.0, 2.0, 3.0, 4.0)
C_CATALOG_DEC = (0.0, 0.0, 0.0, 0.0, 0.0)
C_CATALOG_LINK = (100, LINK_SENTINEL, 101, 999, 103)
C_COLUMNS = (
    "id_specz", "ra_corrected", "dec_corrected", "priority", "specz",
    "flag", "confidence_level", "survey", "id_cosmos25",
)
C_UNIQUE = {
    "id_specz": (100, 101, 102, 103),
    "ra_corrected": (0.0, 2.0, 3.0, 4.0),
    "dec_corrected": (0.0, 0.0, 0.0, 0.0),
    "priority": (1, 1, 1, 1),
    "specz": (1.0, 1.1, 1.2, 1.3),
    "flag": (4, 4, 7, 4),
    "confidence_level": (97, 50, 85, 85),
    "survey": (1, 1, 1, 1),
    "id_cosmos25": (10, 30, 40, 50),
}
C_ALL = {
    "id_specz": (100, 101, 102, 103, 104),
    "ra_corrected": (0.0, 2.0, 3.0, 4.0, 4.0 / 3600.0),
    "dec_corrected": (0.0, 0.0, 0.0, 0.0, 0.0),
    "priority": (1, 1, 1, 1, 0),
    "specz": (1.0, 1.1, 1.2, 1.3, 1.4),
    "flag": (4, 4, 7, 4, 9),
    "confidence_level": (97, 50, 85, 85, 85),
    "survey": (1, 1, 1, 1, 1),
    "id_cosmos25": (10, 30, 40, 50, 20),
}


class _Connection:
    """Minimal read-only connection surface required by the evidence commands."""

    def cursor(self):
        return _Cursor()

    def close(self):
        pass


class _Cursor:
    """Return post-state counts without introducing a database dependency."""

    def execute(self, statement):
        self.statement = statement

    def fetchone(self):
        if "current_database" in self.statement:
            return ("fixture", "fixture_ro", "fixture_ro", "on", "on")
        return (0,)


def _specz_table(specz_ids, cosmos_ids, ra_corrected, ra_cosmos) -> Table:
    """Build a compilation table whose crossmatch names real catalog sources."""
    size = len(specz_ids)
    return Table(
        {
            "Id_specz": list(specz_ids),
            "Id_COSMOS25": list(cosmos_ids),
            "ra_corrected": list(ra_corrected),
            "dec_corrected": [0.0] * size,
            "ra_COSMOS25": list(ra_cosmos),
            "dec_COSMOS25": [0.0] * size,
            "specz": [1.0] * size,
            "Priority": [1] * size,
            "Flag": [4] * size,
            "Confidence_level": [97] * size,
            "Survey": [1] * size,
        }
    )


def _run_verifier(monkeypatch, tmp_path: Path, catalog_rows, table: Table) -> dict:
    """Run the real gate 4.1 command against an in-memory catalog fixture."""
    evidence_path = tmp_path / "gate-4-1.json"
    monkeypatch.setattr(
        verify,
        "load_config",
        lambda: {
            "specz": {
                "all_fits": "/fixture/all.fits",
                "unique_fits": "/fixture/unique.fits",
            },
            "provenance": {"source_manifest_v11": "/fixture/manifest.csv"},
            "specz_linkage": {"gate_4_1_evidence": str(evidence_path)},
        },
    )
    monkeypatch.setattr(
        verify,
        "pin_against_manifest",
        lambda *_args: {"sha_match": True, "bytes_match": True},
    )
    monkeypatch.setattr(verify, "sha256_file", lambda _path: ("fixture", 0))
    monkeypatch.setattr(verify.Table, "read", lambda *_args, **_kwargs: table.copy())
    monkeypatch.setattr(verify, "connect_readonly", lambda _config: _Connection())
    monkeypatch.setattr(
        verify,
        "load_catalog",
        lambda _conn: {
            "id": np.asarray([row["id"] for row in catalog_rows], dtype=np.int64),
            "ra": np.asarray([row["ra"] for row in catalog_rows], dtype=float),
            "dec": np.asarray([row["dec"] for row in catalog_rows], dtype=float),
            "link": np.asarray([row["link"] for row in catalog_rows], dtype=np.int64),
        },
    )
    verify.main()
    return json.loads(evidence_path.read_text(encoding="utf-8"))


def _e2e_table() -> Table:
    """The compilation table paired with `E2E_CATALOG`."""
    return _specz_table(
        specz_ids=(20, 21),
        cosmos_ids=(0, 3),
        ra_corrected=(0.0, 41.0),
        ra_cosmos=(0.0, 30.0),
    )


# =============================================================================
# D1: association, not distance
# =============================================================================


def carriers_from_fixture(catalog_rows, specz_ids) -> dict[int, int]:
    """Derive the correct link-to-catalog-source association from the fixture.

    This reduction is a plain loop over the fixture rows. It shares no code
    with the pairing under test, so agreement between the two is evidence
    rather than a restatement.
    """
    known = {int(value) for value in specz_ids}
    expected: dict[int, int] = {}
    for row in catalog_rows:
        link = int(row["link"])
        if link == LINK_SENTINEL or link not in known:
            continue
        assert link not in expected, "fixture gives one link two carriers"
        expected[link] = int(row["id"])
    return expected


def association_from_pairing(catalog_rows, specz_ids, pairing) -> dict[int, int]:
    """Render a pairing implementation's output as link value to catalog id."""
    catalog_id = np.asarray([row["id"] for row in catalog_rows], dtype=np.int64)
    catalog_link = np.asarray([row["link"] for row in catalog_rows], dtype=np.int64)
    target_ids = np.asarray(specz_ids, dtype=np.int64)
    carrier_rows, _target_rows, carried_links = pairing(catalog_link, target_ids)
    return {
        int(link): int(catalog_id[row])
        for row, link in zip(carrier_rows, carried_links, strict=True)
    }


def _name_source(catalog_rows, catalog_id) -> str:
    """Name one catalog source by identifier and position, never by distance."""
    if catalog_id is None:
        return "no catalog source"
    for index, row in enumerate(catalog_rows):
        if int(row["id"]) == int(catalog_id):
            return f"catalog source {catalog_id} (row {index}, ra={row['ra']})"
    return f"catalog source {catalog_id} (absent from the fixture)"


def assert_links_pair_with_their_carriers(observed, expected, catalog_rows) -> None:
    """Require every stored link to be attached to the source that carries it.

    A failure names the link value and both candidate sources. It never
    reports a separation, because the defect is a wrong association and a
    distance is only its symptom.
    """
    problems = []
    for link in sorted(set(expected) | set(observed)):
        want = expected.get(link)
        got = observed.get(link)
        if want == got:
            continue
        problems.append(
            f"link {link} paired with {_name_source(catalog_rows, got)} "
            f"but is carried by {_name_source(catalog_rows, want)}"
        )
    assert not problems, "; ".join(problems)


def index_arithmetic_pairing(catalog_rows):
    """Rebuild the P2R-04 defect: treat a stored link as a catalog identifier."""
    catalog_id = np.asarray([row["id"] for row in catalog_rows], dtype=np.int64)

    def pairing(catalog_link, target_ids):
        distinct = np.unique(catalog_link[catalog_link != LINK_SENTINEL])
        order = np.argsort(catalog_id, kind="stable")
        sorted_ids = catalog_id[order]
        positions = np.clip(
            np.searchsorted(sorted_ids, distinct), 0, sorted_ids.size - 1
        )
        hit = sorted_ids[positions] == distinct
        target_order = np.argsort(target_ids, kind="stable")
        sorted_targets = target_ids[target_order]
        target_positions = np.searchsorted(sorted_targets, distinct[hit])
        in_bounds = target_positions < sorted_targets.size
        return (
            order[positions[hit]][in_bounds],
            target_order[target_positions[in_bounds]],
            distinct[hit][in_bounds],
        )

    return pairing


def position_dependent_pairing(catalog_link, target_ids):
    """Pair by catalog row order rather than by the stored link each row holds."""
    carrier_rows = np.flatnonzero(catalog_link != LINK_SENTINEL)
    carried_links = catalog_link[carrier_rows]
    shifted = np.roll(carrier_rows, 1)
    target_order = np.argsort(target_ids, kind="stable")
    sorted_targets = target_ids[target_order]
    positions = np.searchsorted(sorted_targets, carried_links)
    in_bounds = positions < sorted_targets.size
    matched = np.zeros(carried_links.size, dtype=bool)
    matched[in_bounds] = sorted_targets[positions[in_bounds]] == carried_links[in_bounds]
    return (
        shifted[matched],
        target_order[positions[matched]],
        carried_links[matched],
    )


def test_d1_each_link_is_paired_with_the_catalog_source_that_carries_it() -> None:
    """D1: the production pairing must reproduce the fixture's own association."""
    observed = association_from_pairing(
        D1_CATALOG, D1_SPECZ_IDS, verify.pair_catalog_link_carriers
    )
    expected = carriers_from_fixture(D1_CATALOG, D1_SPECZ_IDS)

    assert expected == {20: 10, 21: 30}, "fixture derivation changed unexpectedly"
    assert_links_pair_with_their_carriers(observed, expected, D1_CATALOG)


def test_d1_association_survives_a_catalog_row_permutation() -> None:
    """D1: association is by stored link value, so row order cannot matter."""
    permuted = tuple(reversed(D1_CATALOG))
    observed = association_from_pairing(
        permuted, D1_SPECZ_IDS, verify.pair_catalog_link_carriers
    )

    assert_links_pair_with_their_carriers(
        observed, carriers_from_fixture(permuted, D1_SPECZ_IDS), permuted
    )


def test_d1_check_rejects_a_pairing_reverted_to_index_arithmetic() -> None:
    """D1 negative control: the original defect must fail this assertion."""
    observed = association_from_pairing(
        D1_CATALOG, D1_SPECZ_IDS, index_arithmetic_pairing(D1_CATALOG)
    )
    expected = carriers_from_fixture(D1_CATALOG, D1_SPECZ_IDS)

    with pytest.raises(AssertionError) as raised:
        assert_links_pair_with_their_carriers(observed, expected, D1_CATALOG)

    message = str(raised.value)
    assert "link 20 paired with catalog source 20" in message
    assert "carried by catalog source 10" in message
    assert "link 21 paired with no catalog source" in message
    assert "carried by catalog source 30" in message
    assert "arcsec" not in message


def test_d1_check_rejects_a_position_dependent_pairing() -> None:
    """D1 negative control: pairing by row order must fail this assertion."""
    observed = association_from_pairing(
        D1_CATALOG, D1_SPECZ_IDS, position_dependent_pairing
    )
    expected = carriers_from_fixture(D1_CATALOG, D1_SPECZ_IDS)

    with pytest.raises(AssertionError) as raised:
        assert_links_pair_with_their_carriers(observed, expected, D1_CATALOG)

    assert "carried by catalog source" in str(raised.value)


def test_d1_gate_41_geometry_is_invariant_under_catalog_row_permutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D1 end-to-end: the whole command inherits the association's invariance."""
    original = _run_verifier(
        monkeypatch, tmp_path / "original", E2E_CATALOG, _e2e_table()
    )
    permuted = _run_verifier(
        monkeypatch, tmp_path / "permuted", tuple(reversed(E2E_CATALOG)), _e2e_table()
    )

    assert (
        original["geometry"]["defective_path"]
        == permuted["geometry"]["defective_path"]
    ), "defective-path geometry moved when only catalog row order changed"
    assert original["geometry"]["defective_path"]["n"] == len(
        carriers_from_fixture(E2E_CATALOG, (20, 21))
    )


def test_defective_median_guard_rejects_drift_past_two_decimals(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D1: the all-links median guard must retain two decimal places."""
    monkeypatch.setitem(verify.PRIORS, "defective_median", 4054.34)
    evidence = _run_verifier(
        monkeypatch,
        tmp_path,
        (
            {"id": 3, "ra": 30.0, "dec": 0.0, "link": LINK_SENTINEL},
            {"id": 0, "ra": 4054.346 / 3600.0, "dec": 0.0, "link": 20},
            {"id": 2, "ra": 10.0, "dec": 0.0, "link": LINK_SENTINEL},
        ),
        _specz_table(
            specz_ids=(20, 21),
            cosmos_ids=(0, 2),
            ra_corrected=(0.0, 30.0),
            ra_cosmos=(4054.346 / 3600.0, 10.0),
        ),
    )
    defective_check = next(
        check
        for check in evidence["prior_checks"]
        if check["observation"] == "defective_median"
    )

    assert defective_check == {
        "observation": "defective_median",
        "prior": 4054.34,
        "observed": 4054.35,
        "agreement": False,
    }


# =============================================================================
# A1.2 repair: catalog identifiers are resolved, never used as row positions
# =============================================================================


def identifier_as_position_lookup(catalog_id, wanted):
    """The unguarded shortcut: treat an identifier as though it were a row."""
    return np.asarray(wanted, dtype=np.int64)


def test_a12_identifier_lookup_holds_on_a_non_contiguous_catalog(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The crossmatch must name the source `Id_COSMOS25` says, not row N.

    `E2E_CATALOG` carries identifiers 0..3 in the row order 3, 0, 2, 1, so a
    catalog identifier and its row position are never the same thing. The
    compilation's stored `ra_COSMOS25`/`dec_COSMOS25` are the coordinates of
    the sources its `Id_COSMOS25` names, so the namespace separation is zero
    exactly when identifiers are resolved and non-zero when they are used as
    positions.
    """
    evidence = _run_verifier(
        monkeypatch, tmp_path, E2E_CATALOG, _e2e_table()
    )
    measurement = evidence["namespace_validity"][0]

    assert measurement["exclusions"]["compared"] == 2
    assert measurement["separation"]["max"] == pytest.approx(0.0, abs=1e-9)


def test_a12_test_fails_when_identifier_lookup_is_reverted_to_positions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Negative control: removing the lookup must turn the check above red."""
    monkeypatch.setattr(verify, "catalog_rows_for_ids", identifier_as_position_lookup)
    evidence = _run_verifier(
        monkeypatch, tmp_path, E2E_CATALOG, _e2e_table()
    )
    measurement = evidence["namespace_validity"][0]

    assert measurement["separation"]["max"] > 1.0, (
        "a non-contiguous catalog indexed by identifier must report a "
        "non-zero namespace separation; if it does not, this control has "
        "stopped discriminating"
    )


def test_a12_an_unknown_catalog_identifier_halts_rather_than_pairing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An identifier the catalog does not carry is an error, not a silent row."""
    table = _specz_table(
        specz_ids=(20, 21),
        cosmos_ids=(0, 7),
        ra_corrected=(0.0, 41.0),
        ra_cosmos=(0.0, 30.0),
    )

    with pytest.raises(SystemExit) as raised:
        _run_verifier(monkeypatch, tmp_path, E2E_CATALOG, table)

    assert "catalog identifier absent from photometry_primary.id" in str(raised.value)
    assert "[7]" in str(raised.value)


# =============================================================================
# D2: derived categories and independently counted totals
# =============================================================================


def _run_characterization(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict:
    """Run the real gate 4.7 rendering path against both selection buckets."""
    evidence_dir = tmp_path / "evidence"
    catalog = (C_CATALOG_ID, C_CATALOG_RA, C_CATALOG_DEC, C_CATALOG_LINK)
    unique = tuple(C_UNIQUE[name] for name in C_COLUMNS)
    all_rows = tuple(C_ALL[name] for name in C_COLUMNS)
    monkeypatch.setattr(
        characterize,
        "load_config",
        lambda: {"specz_linkage": {"evidence_dir": str(evidence_dir)}},
    )
    monkeypatch.setattr(characterize, "connect_readonly", lambda _config: _Connection())

    def fetch(_cursor, table, requested_columns):
        assert requested_columns == C_COLUMNS or table == "photometry_primary"
        if table == "photometry_primary":
            return catalog
        return unique if table == "specz_compilation_unique" else all_rows

    monkeypatch.setattr(characterize, "fetch_table", fetch)
    characterize.main()
    return json.loads(
        (evidence_dir / "specz-linkage-g47-characterization.json").read_text(
            encoding="utf-8"
        )
    )


def expected_attached(quantity: str) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """Reduce the fixture to the buckets and totals the generator must produce.

    Independent of the characterizer: the resolution rule, the bucket split,
    and the entry counts are all recomputed here from the fixture tuples.
    """
    link_by_source = dict(zip(C_CATALOG_ID, C_CATALOG_LINK, strict=True))
    galaxy_ids = set(C_UNIQUE["id_specz"])
    resolves = {
        source: link in galaxy_ids
        for source, link in link_by_source.items()
        if link != LINK_SENTINEL
    }
    buckets: dict[str, Counter] = {"resolve": Counter(), "no_resolve": Counter()}
    totals = {"resolve": 0, "no_resolve": 0}
    for index, source in enumerate(C_UNIQUE["id_cosmos25"]):
        if source < 0 or source not in resolves:
            continue
        name = "resolve" if resolves[source] else "no_resolve"
        buckets[name][C_UNIQUE[quantity][index]] += 1
        totals[name] += 1
    rendered = {
        name: {str(key): count for key, count in sorted(counter.items())}
        for name, counter in buckets.items()
    }
    return rendered, totals


def rendered_distribution(evidence: dict, quantity: str, bucket: str) -> dict:
    """Read one fully scoped, reconciled distribution from the evidence."""
    selection = evidence["selection_function"]
    return selection[f"corrected_path_attached_galaxy_entries_{quantity}_distribution"][
        bucket
    ]


def check_rendered_distribution(rendered, expected_buckets, expected_total) -> None:
    """Compare a rendered distribution against fixture-derived expectations.

    Every comparison has one side derived here and one side from the
    generator. Nothing on the left and right of an equality both came out of
    the code under test.
    """
    missing = set(expected_buckets) - set(rendered["buckets"])
    extra = set(rendered["buckets"]) - set(expected_buckets)
    assert not missing, f"rendered distribution dropped categories {sorted(missing)}"
    assert not extra, f"rendered distribution invented categories {sorted(extra)}"
    assert rendered["buckets"] == expected_buckets, (
        f"rendered buckets {rendered['buckets']} do not match the fixture "
        f"reduction {expected_buckets}"
    )
    counted = sum(int(count) for count in rendered["buckets"].values())
    assert counted == expected_total, (
        f"rendered bucket counts sum to {counted}, fixture population is "
        f"{expected_total}"
    )
    assert rendered["bucket_sum"] == expected_total, (
        f"stated bucket_sum {rendered['bucket_sum']} is not the fixture "
        f"population {expected_total}"
    )
    assert rendered["attached_entry_total"] == expected_total, (
        f"stated attached_entry_total {rendered['attached_entry_total']} is "
        f"not the fixture population {expected_total}"
    )
    assert rendered["independent_entry_count"] == expected_total, (
        f"stated independent_entry_count {rendered['independent_entry_count']} "
        f"is not the fixture population {expected_total}"
    )
    assert rendered["reconciled"] is True, "generator reported an unreconciled bucket"
    assert rendered["population_scope"], "rendered distribution states no population scope"


@pytest.mark.parametrize("quantity", ["confidence", "flag"])
def test_d2_rendered_distributions_match_the_fixture_reduction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, quantity: str
) -> None:
    """D2: every observed category and every total is checked against the fixture."""
    evidence = _run_characterization(monkeypatch, tmp_path)
    expected_buckets, expected_totals = expected_attached(
        "confidence_level" if quantity == "confidence" else "flag"
    )

    for bucket in ("resolve", "no_resolve"):
        check_rendered_distribution(
            rendered_distribution(evidence, quantity, bucket),
            expected_buckets[bucket],
            expected_totals[bucket],
        )


def test_d2_check_fails_when_a_rendered_category_is_dropped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D2 negative control: silent category loss is the original defect."""
    evidence = _run_characterization(monkeypatch, tmp_path)
    expected_buckets, expected_totals = expected_attached("confidence_level")
    mutilated = dict(rendered_distribution(evidence, "confidence", "resolve"))
    mutilated["buckets"] = {
        key: value for key, value in mutilated["buckets"].items() if key != "85"
    }

    with pytest.raises(AssertionError) as raised:
        check_rendered_distribution(
            mutilated, expected_buckets["resolve"], expected_totals["resolve"]
        )

    assert "dropped categories ['85']" in str(raised.value)


def test_d2_check_fails_when_a_stated_total_is_perturbed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D2 negative control: a total that no longer counts the population fails."""
    evidence = _run_characterization(monkeypatch, tmp_path)
    expected_buckets, expected_totals = expected_attached("confidence_level")
    mutilated = dict(rendered_distribution(evidence, "confidence", "resolve"))
    mutilated["attached_entry_total"] = int(mutilated["attached_entry_total"]) + 1

    with pytest.raises(AssertionError):
        check_rendered_distribution(
            mutilated, expected_buckets["resolve"], expected_totals["resolve"]
        )


def test_population_a_reports_radius_sensitivity_and_pairwise_matching(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A1.3: population A classifies one nearest candidate at all three radii."""
    evidence = _run_characterization(monkeypatch, tmp_path)
    population_a = evidence["population_a"]

    classifications = population_a["representative_classification_by_radius_arcsec"]
    for result in classifications.values():
        assert result["names_same_catalog_source"] == 0
        assert result["classification_total"] == population_a["sources"]

    assert classifications["3"]["names_other_catalog_source"] == 0
    assert classifications["3"]["none_within_radius"] == 1
    assert classifications["5"]["names_other_catalog_source"] == 1
    assert classifications["5"]["none_within_radius"] == 0
    assert classifications["10"] == classifications["5"] | {"radius_arcsec": 10.0}
    assert classifications["3"] != classifications["5"]
    assert population_a["five_arcsec_split_stable_across_tested_radii"] is False

    topology = population_a["matching_topology"]
    assert topology["constructs_connected_components"] is False
    assert topology["multi_member_component_count"] is None
    assert topology["interpretation"] == (
        "pairwise nearest-candidate classification only; no A-B/B-C "
        "transitive connected components are constructed"
    )
