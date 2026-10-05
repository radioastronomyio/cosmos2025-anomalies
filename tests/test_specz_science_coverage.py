#!/usr/bin/env python3
"""
Script Name  : test_specz_science_coverage.py
Description  : Test fixed sensitivity population totals with synthetic sources.
Repository   : cosmos2025-anomalies
Author       : Codex (https://github.com/openai/codex)
Created      : 2026-10-04
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Usage / Examples
----------------
    python -m pytest tests/test_specz_science_coverage.py
        Exercise each fixed sensitivity dimension in memory.

Description
-----------

Hand-counted sources exercise retained, lost and gained members in both
populations. Stricter confidence can add members by dissolving a veto;
headline totals must count membership, rather than just record net changes.
"""

from __future__ import annotations

import pytest

from src.features.specz_science import coverage, verify
from test_specz_science_verify import entry, source


@pytest.mark.parametrize(
    "options, expected, gained, lost",
    [
        ({"confidence_min": 97}, 3, 1, 1),
        ({"threshold": 0.001}, 2, 0, 1),
        ({"normalized_threshold": 0.005}, 4, 1, 0),
    ],
)
def test_sensitivity_totals_count_primary_and_separate_members(
    options, expected, gained, lost
):
    catalog, kinds, unique, all_rows = [], {}, [], []
    for offset, lephare_type in ((0, 0), (10, 2)):
        # Baseline members are 1, 3, 5. At confidence 97, 2 replaces 1.
        # Tight absolute conflicts lose 3; normalized conflicts gain 4.
        for number, z, flag, confidence, other in (
            (1, 1.0, 3, 95, None),
            (2, 1.0, 4, 97, (1.1, 3, 95)),
            (3, 1.0, 4, 97, (1.002, 4, 97)),
            (4, 2.0, 4, 97, (2.006, 4, 97)),
            (5, 1.0, 4, 97, None),
        ):
            sid = number + offset
            catalog.append(source(sid))
            kinds[sid] = lephare_type
            preferred = entry(
                sid * 10, id_cosmos25=sid, priority=1, specz=z,
                flag=flag, confidence=confidence,
            )
            unique.append(preferred)
            all_rows.append(preferred)
            if other:
                all_rows.append(entry(
                    sid * 10 + 1, id_cosmos25=sid, priority=0,
                    specz=other[0], flag=other[1], confidence=other[2],
                ))
    # An extra retained QSO keeps the population totals distinguishable.
    catalog.append(source(21))
    kinds[21] = 2
    qso = entry(210, id_cosmos25=21, priority=1, specz=1.0, flag=4, confidence=97)
    unique.append(qso)
    all_rows.append(qso)
    # Neither the excluded stellar type nor the unmatched source is eligible.
    catalog.extend([source(30), source(31)])
    kinds.update({30: 1, 31: 0})
    star = entry(300, id_cosmos25=30, priority=1, specz=1.0, flag=4, confidence=97)
    unique.append(star)
    all_rows.append(star)
    data = verify.SnapshotData.build(catalog, kinds, unique, all_rows)
    result = coverage.sensitivity_variant(data, {"A1": "development"}, name="test", **options)
    assert result["baseline_primary"] == 3
    assert result["baseline_validation"] == 4
    assert result["primary_galaxy"] == expected
    assert result["separate_validation"] == expected + 1
    for population in ("primary", "validation"):
        assert result[f"gained_{population}"]["count"] == gained
        assert result[f"lost_{population}"]["count"] == lost
