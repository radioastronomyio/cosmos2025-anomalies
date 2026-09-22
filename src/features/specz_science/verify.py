"""Independent reductions over the captured snapshot (gates 5.3 and 5.7).

Everything here re-derives quantities from the captured input identity
without calling the builders in ``build.py`` and without reusing the P2R-04
generators: each reduction names its surface, predicate, unit, and
denominator so a reviewer can restate it independently. Fixture-driven
tests exercise the same functions on synthetic tables with unordered,
non-contiguous, and colliding identifiers to catch source/row-position
confusion.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402

ARCSEC_PER_RADIAN = 180.0 / math.pi * 3600.0


# =============================================================================
# Parsing helpers
# =============================================================================


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    parsed = float(value)
    if math.isnan(parsed):
        return None
    return parsed


def _optional_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    if value in ("t", "true", "True"):
        return True
    if value in ("f", "false", "False"):
        return False
    return None


@dataclass(frozen=True)
class CatalogSource:
    """The photometry fields this product consumes, as captured."""

    id: int
    ra: float | None
    dec: float | None
    tile: str | None
    flag_star: bool | None
    flag_blend: bool | None
    mag_f150w: float | None
    mag_f277w: float | None
    mag_f444w: float | None
    link_id_specz: int | None


@dataclass(frozen=True)
class SpeczEntry:
    """One compilation measurement, all 32 native fields as captured."""

    id_specz: int
    id_original: str | None
    ra_original: float | None
    dec_original: float | None
    ra_corrected: float | None
    dec_corrected: float | None
    priority: int | None
    specz: float | None
    flag: int | None
    confidence_level: int | None
    survey: int | None
    compilation_year: int | None
    public_or_private: int | None
    id_cos20_classic: int | None
    ra_cos20_classic: float | None
    dec_cos20_classic: float | None
    id_cos20_farmer: int | None
    ra_cos20_farmer: float | None
    dec_cos20_farmer: float | None
    id_cosmos25: int | None
    ra_cosmos25: float | None
    dec_cosmos25: float | None
    id_cosmos15: int | None
    ra_cosmos15: float | None
    dec_cosmos15: float | None
    id_cosmos09: int | None
    ra_cosmos09: float | None
    dec_cosmos09: float | None
    photoz: float | None
    photoz_type: int | None
    groupid: int | None
    groupsize: int | None

    @property
    def numeric_valid_z(self) -> bool:
        """P-02: non-null, finite, strictly positive."""
        return self.specz is not None and math.isfinite(self.specz) and self.specz > 0.0


def _parse_specz_row(row: Mapping[str, str]) -> SpeczEntry:
    return SpeczEntry(
        id_specz=int(row["id_specz"]),
        id_original=row["id_original"] or None,
        ra_original=_optional_float(row["ra_original"]),
        dec_original=_optional_float(row["dec_original"]),
        ra_corrected=_optional_float(row["ra_corrected"]),
        dec_corrected=_optional_float(row["dec_corrected"]),
        priority=_optional_int(row["priority"]),
        specz=_optional_float(row["specz"]),
        flag=_optional_int(row["flag"]),
        confidence_level=_optional_int(row["confidence_level"]),
        survey=_optional_int(row["survey"]),
        compilation_year=_optional_int(row["compilation_year"]),
        public_or_private=_optional_int(row["public_or_private"]),
        id_cos20_classic=_optional_int(row["id_cos20_classic"]),
        ra_cos20_classic=_optional_float(row["ra_cos20_classic"]),
        dec_cos20_classic=_optional_float(row["dec_cos20_classic"]),
        id_cos20_farmer=_optional_int(row["id_cos20_farmer"]),
        ra_cos20_farmer=_optional_float(row["ra_cos20_farmer"]),
        dec_cos20_farmer=_optional_float(row["dec_cos20_farmer"]),
        id_cosmos25=_optional_int(row["id_cosmos25"]),
        ra_cosmos25=_optional_float(row["ra_cosmos25"]),
        dec_cosmos25=_optional_float(row["dec_cosmos25"]),
        id_cosmos15=_optional_int(row["id_cosmos15"]),
        ra_cosmos15=_optional_float(row["ra_cosmos15"]),
        dec_cosmos15=_optional_float(row["dec_cosmos15"]),
        id_cosmos09=_optional_int(row["id_cosmos09"]),
        ra_cosmos09=_optional_float(row["ra_cosmos09"]),
        dec_cosmos09=_optional_float(row["dec_cosmos09"]),
        photoz=_optional_float(row["photoz"]),
        photoz_type=_optional_int(row["photoz_type"]),
        groupid=_optional_int(row["groupid"]),
        groupsize=_optional_int(row["groupsize"]),
    )


@dataclass
class SnapshotData:
    """Parsed captured inputs and the lookup structures reductions need."""

    catalog_ids: set[int]
    catalog: dict[int, CatalogSource]
    lephare_type: dict[int, int | None]
    unique_entries: list[SpeczEntry]
    all_entries: list[SpeczEntry]
    unique_by_id: dict[int, SpeczEntry] = field(default_factory=dict)
    all_by_id: dict[int, SpeczEntry] = field(default_factory=dict)
    unique_groups: dict[int, list[SpeczEntry]] = field(default_factory=dict)
    all_groups: dict[int, list[SpeczEntry]] = field(default_factory=dict)

    @staticmethod
    def build(
        catalog_sources: Iterable[CatalogSource],
        lephare_type: Mapping[int, int | None],
        unique_entries: Iterable[SpeczEntry],
        all_entries: Iterable[SpeczEntry],
        *,
        no_association_sentinel: int = -999,
    ) -> "SnapshotData":
        data = SnapshotData(
            catalog_ids={item.id for item in catalog_sources},
            catalog={item.id: item for item in catalog_sources},
            lephare_type=dict(lephare_type),
            unique_entries=list(unique_entries),
            all_entries=list(all_entries),
        )
        for entry in data.unique_entries:
            if entry.id_specz in data.unique_by_id:
                raise ValueError(f"duplicate id_specz in _unique: {entry.id_specz}")
            data.unique_by_id[entry.id_specz] = entry
            if (
                entry.id_cosmos25 is not None
                and entry.id_cosmos25 != no_association_sentinel
            ):
                data.unique_groups.setdefault(entry.id_cosmos25, []).append(entry)
        for entry in data.all_entries:
            if entry.id_specz in data.all_by_id:
                raise ValueError(f"duplicate id_specz in _all: {entry.id_specz}")
            data.all_by_id[entry.id_specz] = entry
            if (
                entry.id_cosmos25 is not None
                and entry.id_cosmos25 != no_association_sentinel
            ):
                data.all_groups.setdefault(entry.id_cosmos25, []).append(entry)
        return data


def load_snapshot_data(
    snapshot_dir: Path | None = None,
    paths: ss_config.SpeczSciencePaths | None = None,
) -> SnapshotData:
    """Parse the four captured CSV artifacts into ``SnapshotData``."""
    if snapshot_dir is None:
        resolved = paths if paths is not None else ss_config.resolve_paths()
        snapshot_dir = resolved.snapshot_dir
    catalog: list[CatalogSource] = []
    with (snapshot_dir / "photometry_primary.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            catalog.append(
                CatalogSource(
                    id=int(row["id"]),
                    ra=_optional_float(row["ra"]),
                    dec=_optional_float(row["dec"]),
                    tile=row["tile"] or None,
                    flag_star=_optional_bool(row["flag_star"]),
                    flag_blend=_optional_bool(row["flag_blend"]),
                    mag_f150w=_optional_float(row["mag_auto_f150w"]),
                    mag_f277w=_optional_float(row["mag_auto_f277w"]),
                    mag_f444w=_optional_float(row["mag_auto_f444w"]),
                    link_id_specz=_optional_int(row["id_specz_khostovan25"]),
                )
            )
    lephare_type: dict[int, int | None] = {}
    with (snapshot_dir / "lephare.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            lephare_type[int(row["id"])] = _optional_int(row["type"])
    unique_entries = _read_specz_csv(snapshot_dir / "specz_compilation_unique.csv")
    all_entries = _read_specz_csv(snapshot_dir / "specz_compilation_all.csv")
    return SnapshotData.build(catalog, lephare_type, unique_entries, all_entries)


def _read_specz_csv(path: Path) -> list[SpeczEntry]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [_parse_specz_row(row) for row in csv.DictReader(handle)]


# =============================================================================
# Shared predicates (restated here independently of the builder)
# =============================================================================


def historical_usable(entry: SpeczEntry, *, strictly_positive: bool) -> bool:
    """The historical rule: finite specz greater than the stated floor."""
    if entry.specz is None or not math.isfinite(entry.specz):
        return False
    return entry.specz > 0.0 if strictly_positive else entry.specz > -90.0


def flag_confidence(flag: int) -> int | None:
    """Documented base-flag confidence; broad-line flags subtract ten."""
    base = {1: 50, 2: 80, 3: 95, 4: 97, 9: 85}
    return base.get(flag, base.get(flag - 10))


def entry_is_secure(entry: SpeczEntry) -> bool:
    """P-02 secure predicate, restated: flag {3,4,13,14}, confidence in
    [95,100] consistent with the documented mapping, numeric-valid z."""
    if not entry.numeric_valid_z:
        return False
    if entry.flag not in (3, 4, 13, 14):
        return False
    if entry.confidence_level is None or not 95 <= entry.confidence_level <= 100:
        return False
    expected = flag_confidence(entry.flag)
    return expected is not None and entry.confidence_level == expected


def pairwise_span(
    entries: Sequence[SpeczEntry], value_of: Callable[[SpeczEntry], float | None]
) -> float:
    """Maximum pairwise absolute difference over the valued entries."""
    values = [value_of(entry) for entry in entries if value_of(entry) is not None]
    if len(values) < 2:
        return 0.0
    return max(values) - min(values)


def separation_arcsec(
    ra1: float, dec1: float, ra2: float, dec2: float
) -> float:
    """Great-circle separation in arcsec (haversine)."""
    ra1, dec1, ra2, dec2 = (
        math.radians(value) for value in (ra1, dec1, ra2, dec2)
    )
    hav = (
        math.sin((dec2 - dec1) / 2.0) ** 2
        + math.cos(dec1) * math.cos(dec2) * math.sin((ra2 - ra1) / 2.0) ** 2
    )
    return 2.0 * math.asin(min(1.0, math.sqrt(hav))) * ARCSEC_PER_RADIAN


def median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        raise ValueError("median of empty sequence")
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


# =============================================================================
# Prior reductions
# =============================================================================


def reduce_row_counts(data: SnapshotData) -> dict[str, int]:
    return {
        "catalog_rows": len(data.catalog),
        "unique_rows": len(data.unique_entries),
        "all_rows": len(data.all_entries),
    }


def reduce_tiles(data: SnapshotData, valid_domain: Sequence[str]) -> dict[str, object]:
    domain = set(valid_domain)
    observed: set[str] = set()
    null_or_out = 0
    for source in data.catalog.values():
        if source.tile is None or source.tile not in domain:
            null_or_out += 1
        else:
            observed.add(source.tile)
    return {
        "distinct_documented_labels": len(observed),
        "null_or_out_of_domain_sources": null_or_out,
        "observed_labels": sorted(observed),
    }


def reduce_reached_sources(data: SnapshotData) -> dict[str, int]:
    unique_reached = {
        source_id
        for source_id, entries in data.unique_groups.items()
        if source_id in data.catalog_ids and entries
    }
    all_reached = {
        source_id
        for source_id, entries in data.all_groups.items()
        if source_id in data.catalog_ids and entries
    }
    return {
        "unique_reached_sources": len(unique_reached),
        "all_reached_sources": len(all_reached),
    }


def reduce_population_a(data: SnapshotData) -> dict[str, object]:
    unique_reached = {
        source_id
        for source_id in data.unique_groups
        if source_id in data.catalog_ids
    }
    all_reached = {
        source_id for source_id in data.all_groups if source_id in data.catalog_ids
    }
    population_a = all_reached - unique_reached
    entries = [
        entry
        for source_id in population_a
        for entry in data.all_groups[source_id]
    ]
    nonzero_priority = [entry for entry in entries if (entry.priority or 0) != 0]
    return {
        "population_a_sources": len(population_a),
        "population_a_entries": len(entries),
        "nonzero_priority_entries": len(nonzero_priority),
        "structural_zero_statement": (
            "Population A is present through _all and absent through _unique; "
            "searching _unique can never return an A source, and this zero "
            "establishes no neighbour destination or upstream deduplication "
            "component."
        ),
    }


def reduce_population_b(data: SnapshotData) -> dict[str, object]:
    groups = {
        source_id: entries
        for source_id, entries in data.unique_groups.items()
        if source_id in data.catalog_ids and len(entries) > 1
    }
    entries = [entry for rows in groups.values() for entry in rows]
    return {
        "population_b_sources": len(groups),
        "population_b_entries": len(entries),
        "groups": {
            str(source_id): {
                "id_specz": [entry.id_specz for entry in rows],
                "specz": [entry.specz for entry in rows],
                "confidence": [entry.confidence_level for entry in rows],
            }
            for source_id, rows in groups.items()
        },
    }


def _group_classification(
    entries: Sequence[SpeczEntry], *, strictly_positive: bool, tolerance: float = 0.005
) -> str:
    usable = [entry for entry in entries if historical_usable(entry, strictly_positive=strictly_positive)]
    if len(usable) < 2:
        return "zero_usable" if not usable else "one_usable"
    return "agreeing" if pairwise_span(usable, lambda e: e.specz) <= tolerance else "disagreeing"


def reduce_population_b_rules(data: SnapshotData) -> dict[str, object]:
    groups = {
        source_id: entries
        for source_id, entries in data.unique_groups.items()
        if source_id in data.catalog_ids and len(entries) > 1
    }
    result: dict[str, object] = {}
    tied_disagreeing: set[int] = set()
    for rule, strictly_positive in (("finite_gt_-90", False), ("positive", True)):
        counts = {"agreeing": 0, "disagreeing": 0, "one_usable": 0, "zero_usable": 0}
        for source_id, entries in groups.items():
            label = _group_classification(entries, strictly_positive=strictly_positive)
            counts[label] += 1
            if label == "disagreeing":
                usable = [
                    entry
                    for entry in entries
                    if historical_usable(entry, strictly_positive=strictly_positive)
                ]
                top = max(entry.confidence_level or -1 for entry in usable)
                if sum(1 for entry in usable if entry.confidence_level == top) >= 2:
                    tied_disagreeing.add(source_id)
        result[rule] = counts
    result["disagreeing_groups_with_tied_highest_confidence_either_rule"] = len(
        tied_disagreeing
    )
    return result


def reduce_unique_usable_sources(data: SnapshotData) -> dict[str, int]:
    def count(predicate: Callable[[SpeczEntry], bool]) -> int:
        return len(
            {
                source_id
                for source_id, entries in data.unique_groups.items()
                if source_id in data.catalog_ids
                and any(predicate(entry) for entry in entries)
            }
        )

    return {
        "unique_sources_z_gt_-90": count(
            lambda e: historical_usable(e, strictly_positive=False)
        ),
        "unique_sources_positive_z": count(
            lambda e: historical_usable(e, strictly_positive=True)
        ),
        "unique_sources_positive_z_conf_ge_95": count(
            lambda e: historical_usable(e, strictly_positive=True)
            and (e.confidence_level is not None and e.confidence_level >= 95)
        ),
    }


def reduce_broadline_high_confidence_entries(data: SnapshotData) -> dict[str, int]:
    corrected_path = [
        entry
        for entry in data.unique_entries
        if entry.id_cosmos25 is not None
        and entry.id_cosmos25 != -999
        and entry.id_cosmos25 in data.catalog_ids
    ]
    hits = [
        entry
        for entry in corrected_path
        if entry.flag in (13, 14)
        and entry.confidence_level is not None
        and entry.confidence_level >= 95
    ]
    return {"unique_entries_conf_ge_95_flags_13_14_no_z_filter": len(hits)}


def reduce_high_confidence_all_disagreement(data: SnapshotData) -> dict[str, object]:
    """The exploratory confidence-only counts (priors P12-P15)."""
    unique_reached = {
        source_id
        for source_id in data.unique_groups
        if source_id in data.catalog_ids
    }
    qualifying: dict[int, list[SpeczEntry]] = {}
    for source_id in unique_reached:
        entries = [
            entry
            for entry in data.all_groups.get(source_id, [])
            if historical_usable(entry, strictly_positive=True)
            and entry.confidence_level is not None
            and entry.confidence_level >= 95
        ]
        if len(entries) >= 2:
            qualifying[source_id] = entries
    spanning = {
        source_id: entries
        for source_id, entries in qualifying.items()
        if pairwise_span(entries, lambda e: e.specz) > 0.005
    }
    single_unique = {
        source_id: entries
        for source_id, entries in spanning.items()
        if len(data.unique_groups.get(source_id, [])) == 1
    }
    priority1_meets = {
        source_id: entries
        for source_id, entries in single_unique.items()
        if any(
            historical_usable(entry, strictly_positive=True)
            and entry.confidence_level is not None
            and entry.confidence_level >= 95
            for entry in data.unique_groups[source_id]
        )
    }
    return {
        "unique_reachable_sources_ge2_positive_conf95_all": len(qualifying),
        "spanning_abs_z_diff_gt_0p005": len(spanning),
        "of_those_exactly_one_unique_entry": len(single_unique),
        "of_those_priority1_meets_positive_conf95": len(priority1_meets),
        "population": "distinct sources; entries from _all restricted to _unique-reachable sources",
    }


def reduce_defective_path_median(data: SnapshotData) -> dict[str, object]:
    """All-links defective-path separation median on its documented basis.

    Population: every catalog source carrying a non-sentinel
    id_specz_khostovan25 link. Pairing: photometry_primary.ra/dec against
    the carried link's measurement-level _all ra_corrected/dec_corrected at
    that link value's id_specz. The basis is unchanged from the corrected
    P2R-04 evidence; this reduction is independent of their code.
    """
    separations: list[float] = []
    unmatched_links = 0
    invalid_coordinates = 0
    for source in data.catalog.values():
        link = source.link_id_specz
        if link is None or link == -999:
            continue
        entry = data.all_by_id.get(link)
        if entry is None:
            unmatched_links += 1
            continue
        if (
            source.ra is None
            or source.dec is None
            or entry.ra_corrected is None
            or entry.dec_corrected is None
        ):
            invalid_coordinates += 1
            continue
        separations.append(
            separation_arcsec(
                source.ra, source.dec, entry.ra_corrected, entry.dec_corrected
            )
        )
    return {
        "all_links_sources": len(separations) + unmatched_links + invalid_coordinates,
        "measured_separations": len(separations),
        "median_arcsec": median(separations),
        "unmatched_links": unmatched_links,
        "invalid_coordinates": invalid_coordinates,
    }


def verify_unique_priority1_equality(data: SnapshotData) -> dict[str, object]:
    """Full positional per-column equality between _unique and _all@Priority=1.

    The comparison joins by ``id_specz`` lookup (never row position) and
    compares every native field including the None/mask distinction.
    """
    priority_one = [entry for entry in data.all_entries if (entry.priority or 0) == 1]
    priority_by_id = {entry.id_specz: entry for entry in priority_one}
    if len(priority_by_id) != len(priority_one):
        return {
            "equal": False,
            "reason": "id_specz not unique within _all Priority=1 rows",
        }
    if set(priority_by_id) != set(data.unique_by_id):
        return {
            "equal": False,
            "reason": "identifier sets differ",
            "unique_only": sorted(set(data.unique_by_id) - set(priority_by_id))[:5],
            "priority_only": sorted(set(priority_by_id) - set(data.unique_by_id))[:5],
        }
    mismatches: list[int] = []
    fields = [
        field_name
        for field_name in SpeczEntry.__dataclass_fields__
        if field_name != "id_specz"
    ]
    for id_specz, unique_entry in data.unique_by_id.items():
        priority_entry = priority_by_id[id_specz]
        if any(
            getattr(unique_entry, name) != getattr(priority_entry, name)
            for name in fields
        ):
            mismatches.append(id_specz)
    return {
        "equal": not mismatches,
        "compared_fields": len(fields),
        "rows_compared": len(data.unique_by_id),
        "mismatched_ids": mismatches[:5],
        "mismatch_count": len(mismatches),
    }


def reduce_unrecognized_flag_bound(data: SnapshotData) -> dict[str, object]:
    """Empirical bound: which unrecognized flags carry which confidences.

    Tracked per surface so a flag present only in ``_all`` (for example -3)
    is distinguishable from one present in both compilation surfaces.
    """
    recognized = {1, 2, 3, 4, 9, 11, 12, 13, 14, 19}
    observed: dict[int, dict[str, dict[int, int]]] = {}
    for scope, entries in (
        ("_unique", data.unique_entries),
        ("_all", data.all_entries),
    ):
        for entry in entries:
            if entry.flag in recognized:
                continue
            key = (
                entry.confidence_level
                if entry.confidence_level is not None
                else "null"
            )
            per_flag = observed.setdefault(entry.flag, {"_unique": {}, "_all": {}})
            per_flag[scope][key] = per_flag[scope].get(key, 0) + 1
    any_ge_95 = any(
        isinstance(confidence, int) and confidence >= 95
        for per_flag in observed.values()
        for scope in per_flag.values()
        for confidence in scope
    )
    serialized = {
        str(flag): {
            scope: {str(k): v for k, v in sorted(counts.items(), key=lambda kv: str(kv[0]))}
            for scope, counts in per_flag.items()
        }
        for flag, per_flag in sorted(observed.items())
    }
    return {
        "unrecognized_flag_confidence_distribution_by_surface": serialized,
        "any_unrecognized_flag_confidence_ge_95": any_ge_95,
    }


def preferred_entry_independent(data: SnapshotData) -> dict[int, SpeczEntry | None]:
    """P-03 selection, restated: numeric-valid _unique candidates, highest
    valid confidence in [0,100], ties to ascending id_specz."""
    resolved: dict[int, SpeczEntry | None] = {}
    for source_id, entries in data.unique_groups.items():
        candidates = [entry for entry in entries if entry.numeric_valid_z]
        if not candidates:
            resolved[source_id] = None
            continue

        def sort_key(entry: SpeczEntry) -> tuple[int, int, int]:
            confidence = entry.confidence_level
            valid = confidence is not None and 0 <= confidence <= 100
            return (
                0 if valid else 1,
                -(confidence if valid else -1),
                entry.id_specz,
            )

        resolved[source_id] = sorted(candidates, key=sort_key)[0]
    return resolved


def conflict_flags_independent(
    data: SnapshotData, tolerance: float = 0.005
) -> dict[int, dict[str, Any]]:
    """P-04 flags, restated independently of the builder."""
    preferred = preferred_entry_independent(data)
    secure_by_source: dict[int, list[SpeczEntry]] = {}
    numeric_all_by_source: dict[int, list[SpeczEntry]] = {}
    for source_id in data.all_groups:
        secure_by_source[source_id] = [
            entry for entry in data.all_groups[source_id] if entry_is_secure(entry)
        ]
        numeric_all_by_source[source_id] = [
            entry for entry in data.all_groups[source_id] if entry.numeric_valid_z
        ]
    flags: dict[int, dict[str, Any]] = {}
    for source_id, entries in data.unique_groups.items():
        numeric_unique = [entry for entry in entries if entry.numeric_valid_z]
        unique_conflict = pairwise_span(numeric_unique, lambda e: e.specz) > tolerance
        secure_conflict = (
            pairwise_span(secure_by_source.get(source_id, []), lambda e: e.specz)
            > tolerance
        )
        other = False
        secure_ids = {entry.id_specz for entry in secure_by_source.get(source_id, [])}
        numeric_all = numeric_all_by_source.get(source_id, [])
        for i in range(len(numeric_all)):
            for j in range(i + 1, len(numeric_all)):
                left, right = numeric_all[i], numeric_all[j]
                if abs(left.specz - right.specz) > tolerance:  # type: ignore[operator]
                    if left.id_specz not in secure_ids or right.id_specz not in secure_ids:
                        other = True
        flags[source_id] = {
            "unique_numeric_conflict": unique_conflict,
            "secure_all_conflict": secure_conflict,
            "other_measurement_disagreement": other,
            "assessable": len(numeric_unique) >= 2 or len(secure_by_source.get(source_id, [])) >= 2,
        }
    return flags


def reduce_qualified_before_type(
    data: SnapshotData, valid_domain: Sequence[str]
) -> dict[str, object]:
    """The pre-photometric-type diagnostic mask under the proposed baseline.

    Resolved association, secure preferred _unique entry, neither P-04 veto,
    valid native tile. Cross-tabulated by observed LePHARE type (including
    missing/unknown) and broad-line reporting. Distinct sources are the
    denominator throughout.
    """
    preferred = preferred_entry_independent(data)
    flags = conflict_flags_independent(data)
    domain = set(valid_domain)
    qualified: list[int] = []
    for source_id, entries in data.unique_groups.items():
        if source_id not in data.catalog_ids:
            continue
        entry = preferred.get(source_id)
        if entry is None or not entry_is_secure(entry):
            continue
        source_flags = flags.get(source_id, {})
        if source_flags.get("unique_numeric_conflict") or source_flags.get(
            "secure_all_conflict"
        ):
            continue
        tile = data.catalog[source_id].tile
        if tile is None or tile not in domain:
            continue
        qualified.append(source_id)
    crosstab: dict[str, dict[str, int]] = {}
    broad_line_flags = {11, 12, 13, 14, 19}
    for source_id in qualified:
        lephare = data.lephare_type.get(source_id)
        if lephare is None:
            type_label = "missing"
        elif lephare in (0, 1, 2):
            type_label = str(lephare)
        else:
            type_label = f"other:{lephare}"
        broad = any(
            entry.numeric_valid_z and entry.flag in broad_line_flags
            for entry in data.all_groups.get(source_id, [])
        )
        broad_label = "broad_line_reported" if broad else "no_broad_line_report"
        crosstab.setdefault(type_label, {}).setdefault(broad_label, 0)
        crosstab[type_label][broad_label] += 1
    return {
        "spectroscopy_qualified_before_photometric_type": len(qualified),
        "crosstab_lephare_type_x_broad_line": crosstab,
    }


def reduce_secure_quality_inconsistencies(data: SnapshotData) -> dict[str, object]:
    """Entries meeting every secure criterion except flag/confidence mapping."""
    candidates = [
        entry
        for entry in data.all_entries
        if entry.numeric_valid_z
        and entry.flag in (3, 4, 13, 14)
        and entry.confidence_level is not None
        and 95 <= entry.confidence_level <= 100
    ]
    inconsistent = [
        entry
        for entry in candidates
        if flag_confidence(entry.flag) != entry.confidence_level
    ]
    secure = [entry for entry in candidates if entry not in inconsistent]
    return {
        "secure_measurement_entries_all": len(secure),
        "flag_domain_conf_range_but_mapping_inconsistent": len(inconsistent),
        "inconsistent_examples": [
            {
                "id_specz": entry.id_specz,
                "flag": entry.flag,
                "confidence": entry.confidence_level,
                "expected": flag_confidence(entry.flag),
            }
            for entry in inconsistent[:10]
        ],
    }


def reduce_secure_population(data: SnapshotData) -> dict[str, object]:
    """Secure preferred-entry population and veto accounting, baseline."""
    preferred = preferred_entry_independent(data)
    flags = conflict_flags_independent(data)
    secure_preferred = 0
    vetoed = 0
    for source_id, entry in preferred.items():
        if source_id not in data.catalog_ids:
            continue
        if entry is None or not entry_is_secure(entry):
            continue
        secure_preferred += 1
        source_flags = flags.get(source_id, {})
        if source_flags.get("unique_numeric_conflict") or source_flags.get(
            "secure_all_conflict"
        ):
            vetoed += 1
    return {
        "resolved_sources_with_secure_preferred_unique_entry": secure_preferred,
        "of_those_vetoed_by_either_p04_flag": vetoed,
    }


def build_prior_evidence(data: SnapshotData, valid_domain: Sequence[str]) -> dict[str, Any]:
    """Assemble the full gate 5.3 evidence document."""
    priors: dict[str, Any] = {
        "row_counts": reduce_row_counts(data),
        "tiles": reduce_tiles(data, valid_domain),
        "reached_sources": reduce_reached_sources(data),
        "population_a": reduce_population_a(data),
        "population_b": reduce_population_b(data),
        "population_b_rules": reduce_population_b_rules(data),
        "unique_usable_sources": reduce_unique_usable_sources(data),
        "broadline_high_confidence_entries": reduce_broadline_high_confidence_entries(data),
        "high_confidence_all_disagreement": reduce_high_confidence_all_disagreement(data),
        "defective_path": reduce_defective_path_median(data),
        "unique_priority1_equality": verify_unique_priority1_equality(data),
        "unrecognized_flag_bound": reduce_unrecognized_flag_bound(data),
        "qualified_before_type": reduce_qualified_before_type(data, valid_domain),
        "secure_quality_inconsistencies": reduce_secure_quality_inconsistencies(data),
        "secure_population": reduce_secure_population(data),
    }
    return priors


def main() -> None:
    import argparse

    from src.features.specz_science import policy as ss_policy

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    paths = ss_config.resolve_paths()
    data = load_snapshot_data(paths=paths)
    evidence = build_prior_evidence(data, ss_policy.VALID_TILE_DOMAIN)
    output = args.output if args.output is not None else (
        paths.staging_dir / "priors-5-3.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"written": str(output)}, indent=2))


if __name__ == "__main__":
    main()
