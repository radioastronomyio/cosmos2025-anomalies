#!/usr/bin/env python3
"""
Script Name  : test_specz_linkage_evidence_regressions.py
Description  : Reproduce P2R-04 evidence-layer identifier and confidence defects
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-31

Description
-----------
Runs the two evidence generators against small in-memory source-mirror
fixtures. The fixtures intentionally separate catalog row order from catalog
identifiers and include a confidence category outside the defective-column
subset, so the assertions catch association and completeness regressions.

Usage
-----
    pytest tests/test_specz_linkage_evidence_regressions.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from astropy.table import Table

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import characterize_specz_linkage_v11 as characterize
from src.etl import verify_specz_linkage_v11 as verify


class _Connection:
    """Minimal read-only connection surface required by the evidence commands."""

    def cursor(self):
        return _Cursor()

    def close(self):
        pass


class _Cursor:
    """Return post-state counts without introducing a database dependency."""

    def execute(self, _statement):
        pass

    def fetchone(self):
        return (0,)


def _specz_table() -> Table:
    """Build two galaxy and measurement rows, including Id_specz 20."""
    return Table(
        {
            "Id_specz": [20, 21],
            "Id_COSMOS25": [1, 1],
            "ra_corrected": [0.0, 0.0],
            "dec_corrected": [0.0, 0.0],
            "ra_COSMOS25": [0.0, 0.0],
            "dec_COSMOS25": [0.0, 0.0],
            "specz": [1.0, 1.0],
            "Priority": [1, 1],
            "Flag": [4, 4],
            "Confidence_level": [97, 97],
            "Survey": [1, 1],
        }
    )


def _run_verifier(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, catalog_rows):
    """Run the real Gate 4.1 pairing path against an ordered catalog fixture."""
    evidence_path = tmp_path / "gate-4-1.json"
    table = _specz_table()
    monkeypatch.setattr(
        verify,
        "load_config",
        lambda: {
            "specz": {"all_fits": "/fixture/all.fits", "unique_fits": "/fixture/unique.fits"},
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


def test_defective_path_pairs_link_with_its_stored_catalog_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D1: a stored link must select its carrier, never the catalog row whose id equals it."""
    catalog_rows = [
        {"id": 30, "ra": 30.0, "dec": 0.0, "link": -999},
        {"id": 10, "ra": 0.0, "dec": 0.0, "link": 20},
        {"id": 20, "ra": 10.0, "dec": 0.0, "link": -999},
    ]
    evidence = _run_verifier(monkeypatch, tmp_path, catalog_rows)

    # Direct lookup independently establishes that link 20 is carried by
    # catalog source 10. Catalog source 20 is a different source and must not
    # become the pairing merely because its catalog id equals the link value.
    carrier = next(row for row in catalog_rows if row["link"] == 20)
    identifier_coincidence = next(row for row in catalog_rows if row["id"] == 20)
    assert evidence["geometry"]["defective_path"]["median"] == 0.0, (
        "link 20 must pair with stored-link carrier catalog source 10 "
        f"(ra={carrier['ra']}), not catalog source 20 (ra={identifier_coincidence['ra']})"
    )


def test_defective_path_pairing_is_invariant_under_catalog_row_permutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D1: pairing by stored link must survive a catalog-row permutation."""
    catalog_rows = [
        {"id": 30, "ra": 30.0, "dec": 0.0, "link": -999},
        {"id": 10, "ra": 0.0, "dec": 0.0, "link": 20},
        {"id": 20, "ra": 10.0, "dec": 0.0, "link": -999},
    ]
    original = _run_verifier(monkeypatch, tmp_path / "original", catalog_rows)
    permuted = _run_verifier(
        monkeypatch,
        tmp_path / "permuted",
        [catalog_rows[2], catalog_rows[1], catalog_rows[0]],
    )

    assert original["geometry"]["defective_path"] == permuted["geometry"]["defective_path"], (
        "link 20 pairing changed after row permutation; it must remain attached "
        "to stored-link carrier catalog source 10, not catalog source 20"
    )


def _run_characterization(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[dict, tuple]:
    """Run the real Gate 4.7 rendering path against a three-category fixture."""
    evidence_dir = tmp_path / "evidence"
    catalog = (
        [10, 20, 30], [0.0, 1.0, 2.0], [0.0, 0.0, 0.0], [100, -999, 101]
    )
    columns = (
        "id_specz", "ra_corrected", "dec_corrected", "priority", "specz",
        "flag", "confidence_level", "survey", "id_cosmos25",
    )
    unique = (
        [100, 101, 102], [0.0, 2.0, 1.0], [0.0, 0.0, 0.0], [1, 1, 1],
        [1.0, 1.1, 1.2], [4, 4, 4], [97, 50, 85], [1, 1, 1], [10, 30, 20],
    )
    monkeypatch.setattr(
        characterize,
        "load_config",
        lambda: {"specz_linkage": {"evidence_dir": str(evidence_dir)}},
    )
    monkeypatch.setattr(characterize, "connect_readonly", lambda _config: _Connection())

    def fetch(_cursor, table, requested_columns):
        assert requested_columns == columns or table == "photometry_primary"
        return catalog if table == "photometry_primary" else unique

    monkeypatch.setattr(characterize, "fetch_table", fetch)
    characterize.main()
    return (
        json.loads(
            (evidence_dir / "specz-linkage-g47-characterization.json").read_text(
                encoding="utf-8"
            )
        ),
        unique,
    )


def _rendered_confidence_distribution(evidence: dict) -> dict:
    """Read the rendered buckets and their stated galaxy-level total."""
    selection = evidence["selection_function"]
    return {
        "buckets": selection[
            "corrected_path_attached_galaxy_entries_confidence_distribution"
        ]["resolve"],
        "stated_total": selection["precision_recall"]["against_galaxy_level"][
            "denominator_positive"
        ],
    }


def test_confidence_distribution_renders_every_observed_category(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D2: an observed Confidence_level category cannot disappear from the rendering."""
    evidence, unique = _run_characterization(monkeypatch, tmp_path)
    observed_categories = {str(value) for value in unique[6]}
    rendered = _rendered_confidence_distribution(evidence)["buckets"]

    assert observed_categories <= set(rendered), (
        "rendered confidence distribution omitted observed category 85"
    )


def test_confidence_distribution_total_reconciles_to_its_population(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D2: rendered bucket counts must reconcile to the independent population count."""
    evidence, unique = _run_characterization(monkeypatch, tmp_path)
    rendered = _rendered_confidence_distribution(evidence)
    independently_counted_population = len(unique[0])

    assert sum(rendered["buckets"].values()) == rendered["stated_total"], (
        "rendered confidence buckets do not reconcile to their stated total"
    )
    assert rendered["stated_total"] == independently_counted_population, (
        "rendered stated total does not reconcile to the independently counted population"
    )
