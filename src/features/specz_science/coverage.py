"""P-07 diagnostics and the three fixed sensitivity variants (gate 5.7).

Baseline coverage renders every figure with its predicate and denominator:
eligibility counts, mutually exclusive summary states, overlapping reason
counts, coverage against the full catalog, the pre-photometric-type
diagnostic cross-tabulated by observed LePHARE type and broad-line
reporting, survey/confidence distributions over audited entries, tile
coverage, mask/blend context, and magnitude/color diagnostics under the
policy's display-domain rule with explicit underflow/overflow and
not-evaluated bins.

The three sensitivity variants recompute secure status and conflict flags
consistently under their single changed dimension, retain the baseline
preferred-row ordering, share the frozen partitions, and report
source-level membership changes with reasons. Nothing here chooses a
winner, and no eligibility boolean in the installed product is touched.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import build as ssb  # noqa: E402
from src.features.specz_science import splits as ss_splits  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402
from src.features.specz_science.verify import SnapshotData, SpeczEntry  # noqa: E402

COLOR_DOMAIN = (-10.0, 50.0)
MAGNITUDE_BINS = (-math.inf, 15.0, 20.0, 24.0, 26.0, 28.0, 30.0, 35.0, math.inf)
COLOR_BINS = (-math.inf, -2.0, 0.0, 1.0, 2.0, 3.0, 4.0, 6.0, math.inf)


def bin_label(value: float, edges: tuple[float, ...]) -> str:
    for index in range(len(edges) - 1):
        if edges[index] <= value < edges[index + 1]:
            lower = edges[index]
            upper = edges[index + 1]
            return _edge_name(lower, upper)
    return "unbinned"


def _edge_name(lower: float, upper: float) -> str:
    def render(edge: float) -> str:
        if edge == -math.inf:
            return "underflow"
        if edge == math.inf:
            return "overflow"
        return f"{edge:g}"

    return f"[{render(lower)},{render(upper)})"


def magnitude_summary(values: Iterator[float | None], denominators: int) -> dict[str, Any]:
    """F444W magnitude distribution with native-missing and overflow bins."""
    counts: Counter[str] = Counter()
    for value in values:
        if value is None:
            counts["native_missing"] += 1
        elif not math.isfinite(value):
            counts["non_finite"] += 1
        else:
            counts[bin_label(value, MAGNITUDE_BINS)] += 1
    return {
        "denominator_sources": denominators,
        "bins": dict(sorted(counts.items())),
        "bin_edges": [None if math.isinf(edge) else edge for edge in MAGNITUDE_BINS],
    }


def color_summary(
    blue_values: list[float | None], red_values: list[float | None]
) -> dict[str, Any]:
    """F150W-F277W color only where both magnitudes are finite and inside
    the display domain; everything else lands in explicit categories."""
    counts: Counter[str] = Counter()
    for blue, red in zip(blue_values, red_values):
        if blue is None or red is None:
            counts["native_missing_input"] += 1
            continue
        if not (math.isfinite(blue) and math.isfinite(red)):
            counts["non_finite_input"] += 1
            continue
        if not (COLOR_DOMAIN[0] < blue < COLOR_DOMAIN[1]) or not (
            COLOR_DOMAIN[0] < red < COLOR_DOMAIN[1]
        ):
            counts["color_not_evaluated_display_domain"] += 1
            continue
        counts[bin_label(blue - red, COLOR_BINS)] += 1
    return {
        "denominator_sources": len(blue_values),
        "bins": dict(sorted(counts.items())),
        "display_domain": list(COLOR_DOMAIN),
        "bin_edges": [None if math.isinf(edge) else edge for edge in COLOR_BINS],
    }


def baseline_coverage(data: SnapshotData, tile_mapping, *, preferred=None, flags=None) -> dict[str, Any]:
    """Every P-07 baseline diagnostic over the captured snapshot."""
    secure_flags = (3, 4, 13, 14)
    qualified = ssv.reduce_qualified_before_type(
        data, list(tile_mapping)
    )
    sources = data.catalog
    full = len(sources)

    reason_counts: Counter[str] = Counter()
    eligibility_primary = 0
    eligibility_validation = 0
    mutually_exclusive_violations = 0
    state_counts: Counter[str] = Counter()
    preferred_secure = 0
    independent = preferred if preferred is not None else ssv.preferred_entry_independent(data)
    flags = flags if flags is not None else ssv.conflict_flags_independent(data)
    vetoed = 0
    for source_id in sources:
        entry = independent.get(source_id)
        is_secure = entry is not None and ssv.entry_is_secure(entry)
        flag = flags.get(source_id, {})
        veto = bool(flag.get("unique_numeric_conflict")) or bool(
            flag.get("secure_all_conflict")
        )
        if is_secure:
            preferred_secure += 1
        if veto:
            vetoed += 1
        tile = sources[source_id].tile
        valid_tile = tile in tile_mapping
        lephare = data.lephare_type.get(source_id)
        broad = any(
            e.numeric_valid_z and e.flag in (11, 12, 13, 14, 19)
            for e in data.all_groups.get(source_id, [])
        )
        label = (
            "unknown" if lephare is None else str(lephare) if lephare in (0, 1, 2) else f"other:{lephare}"
        )
        primary = is_secure and not veto and valid_tile and lephare == 0 and not broad
        validation = (
            is_secure
            and not veto
            and valid_tile
            and lephare in (0, 2)
            and (broad or lephare == 2)
        )
        eligibility_primary += primary
        eligibility_validation += validation
        mutually_exclusive_violations += primary and validation
        if primary:
            state_counts["primary_galaxy"] += 1
        elif validation:
            state_counts["separate_validation"] += 1
        elif veto:
            state_counts["conflict_vetoed"] += 1
        elif not is_secure:
            state_counts["no_secure_preferred"] += 1
        else:
            state_counts["classification_routed_out"] += 1
        # Reasons (overlapping).
        if not data.unique_groups.get(source_id) and not data.all_groups.get(source_id):
            reason_counts[ssb.REASON_NO_ASSOCIATION] += 1
        if data.all_groups.get(source_id) and not data.unique_groups.get(source_id):
            reason_counts[ssb.REASON_A_ONLY_NO_UNIQUE] += 1
        if data.unique_groups.get(source_id) and entry is None:
            reason_counts[ssb.REASON_NO_NUMERIC_VALID_UNIQUE] += 1
        if entry is not None and not is_secure:
            if entry.flag not in secure_flags:
                reason_counts[ssb.REASON_NOT_SECURE_FLAG] += 1
            elif entry.confidence_level is None or not (
                95 <= entry.confidence_level <= 100
            ):
                reason_counts[ssb.REASON_NOT_SECURE_CONFIDENCE_LOW] += 1
        if flag.get("unique_numeric_conflict"):
            reason_counts[ssb.REASON_UNIQUE_NUMERIC_CONFLICT] += 1
        if flag.get("secure_all_conflict"):
            reason_counts[ssb.REASON_SECURE_ALL_CONFLICT] += 1
        if lephare == 1:
            reason_counts[ssb.REASON_TYPE_STELLAR] += 1
        if lephare is None or lephare not in (0, 1, 2):
            reason_counts[ssb.REASON_TYPE_UNKNOWN] += 1
        if broad:
            reason_counts[ssb.REASON_BROAD_LINE_PRESENT] += 1
        if not broad and lephare != 2:
            reason_counts[ssb.REASON_NO_BROAD_LINE_OR_QSO] += 1

    survey_distribution = Counter(
        entry.survey
        for entry in data.all_entries
        if entry.numeric_valid_z
    )
    confidence_distribution = Counter(
        entry.confidence_level
        for entry in data.all_entries
        if entry.numeric_valid_z
    )
    flag_distribution = Counter(
        entry.flag for entry in data.all_entries if entry.numeric_valid_z
    )
    tile_counts = Counter(
        sources[source_id].tile for source_id in sources
    )
    tile_coverage = {
        tile: {
            "sources": tile_counts.get(tile, 0),
            "assigned": tile_mapping.get(tile, "unassigned"),
        }
        for tile in sorted(tile_mapping)
    }
    mask_blend = {
        "flag_star_true": sum(
            1 for s in sources.values() if s.flag_star is True
        ),
        "flag_star_false": sum(
            1 for s in sources.values() if s.flag_star is False
        ),
        "flag_star_missing": sum(
            1 for s in sources.values() if s.flag_star is None
        ),
        "flag_blend_true": sum(
            1 for s in sources.values() if s.flag_blend is True
        ),
        "flag_blend_false": sum(
            1 for s in sources.values() if s.flag_blend is False
        ),
        "flag_blend_missing": sum(
            1 for s in sources.values() if s.flag_blend is None
        ),
    }
    lephare_class = Counter(data.lephare_type.values())

    return {
        "denominators": {
            "full_catalog_sources": full,
            "unique_reached_sources": len(
                {s for s in data.unique_groups if s in sources}
            ),
            "all_reached_sources": len(
                {s for s in data.all_groups if s in sources}
            ),
            "audited_entries": len(data.all_entries),
            "numeric_valid_entries": sum(
                1 for e in data.all_entries if e.numeric_valid_z
            ),
        },
        "eligibility": {
            "primary_galaxy": eligibility_primary,
            "separate_validation": eligibility_validation,
            "mutually_exclusive_violations": mutually_exclusive_violations,
            "secure_preferred_sources": preferred_secure,
            "vetoed_sources": vetoed,
        },
        "summary_states_non_overlapping": dict(sorted(state_counts.items())),
        "overlapping_reason_counts": dict(sorted(reason_counts.items())),
        "qualified_before_photometric_type": qualified,
        "entry_survey_distribution_numeric_valid": {
            str(key): value for key, value in sorted(survey_distribution.items(), key=lambda kv: (kv[0] is None, kv[0]))
        },
        "entry_confidence_distribution_numeric_valid": {
            str(key): value for key, value in sorted(confidence_distribution.items(), key=lambda kv: (kv[0] is None, kv[0]))
        },
        "entry_flag_distribution_numeric_valid": {
            str(key): value for key, value in sorted(flag_distribution.items(), key=lambda kv: (kv[0] is None, kv[0]))
        },
        "tile_coverage": tile_coverage,
        "mask_blend_context": mask_blend,
        "lephare_type_distribution": {
            str(key): value for key, value in sorted(lephare_class.items(), key=lambda kv: (kv[0] is None, kv[0]))
        },
    }


def photometric_coverage(data: SnapshotData, population: set[int]) -> dict[str, Any]:
    """Magnitude and color diagnostics for a declared source population."""
    magnitudes = [
        data.catalog[source_id].mag_f444w for source_id in sorted(population)
    ]
    blue = [data.catalog[source_id].mag_f150w for source_id in sorted(population)]
    red = [data.catalog[source_id].mag_f277w for source_id in sorted(population)]
    return {
        "population_size": len(population),
        "f444w_magnitude": magnitude_summary(iter(magnitudes), len(population)),
        "f150w_minus_f277w_color": color_summary(blue, red),
    }


def sensitivity_variant(
    data: SnapshotData,
    tile_mapping,
    *,
    name: str,
    confidence_min: int | None = None,
    threshold: float | None = None,
    normalized_threshold: float | None = None,
) -> dict[str, Any]:
    """Recompute secure status and conflicts under one changed dimension.

    The baseline preferred-row ordering is retained: only secure status and
    conflict comparisons are recomputed under the variant parameters, and
    membership changes are reported with the changed-side reasons.
    """

    def secure(entry: SpeczEntry) -> bool:
        if not entry.numeric_valid_z:
            return False
        if entry.flag not in (3, 4, 13, 14):
            return False
        floor = confidence_min if confidence_min is not None else 95
        if entry.confidence_level is None or not floor <= entry.confidence_level <= 100:
            return False
        expected = ssv.flag_confidence(entry.flag)
        return expected is not None and entry.confidence_level == expected

    def differs(left: SpeczEntry, right: SpeczEntry) -> bool:
        if threshold is not None:
            return abs(left.specz - right.specz) > threshold  # type: ignore[operator]
        if normalized_threshold is not None:
            pair = min(left.specz, right.specz)  # type: ignore[operator]
            return (
                abs(left.specz - right.specz) / (1.0 + pair)  # type: ignore[operator]
                > normalized_threshold
            )
        return abs(left.specz - right.specz) > 0.005  # type: ignore[operator]

    baseline_preferred = ssv.preferred_entry_independent(data)
    changes: dict[str, Any] = {
        "variant": name,
        "changed_dimension": (
            "confidence_min"
            if confidence_min is not None
            else "conflict_threshold"
            if threshold is not None
            else "normalized_conflict_threshold"
        ),
        "primary_galaxy": 0,
        "separate_validation": 0,
        "gained_primary": [],
        "lost_primary": [],
        "gained_validation": [],
        "lost_validation": [],
    }
    baseline_flags = ssv.conflict_flags_independent(data)
    baseline_counts = {"primary": 0, "validation": 0}
    for source_id in data.catalog_ids:
        entry = baseline_preferred.get(source_id)
        tile = data.catalog[source_id].tile
        valid_tile = tile in tile_mapping
        secure_all = [e for e in data.all_groups.get(source_id, []) if secure(e)]
        numeric_unique = [
            e for e in data.unique_groups.get(source_id, []) if e.numeric_valid_z
        ]
        unique_conflict = any(
            differs(numeric_unique[i], numeric_unique[j])
            for i in range(len(numeric_unique))
            for j in range(i + 1, len(numeric_unique))
        )
        secure_conflict = any(
            differs(secure_all[i], secure_all[j])
            for i in range(len(secure_all))
            for j in range(i + 1, len(secure_all))
        )
        is_secure = entry is not None and secure(entry)
        veto = unique_conflict or secure_conflict
        lephare = data.lephare_type.get(source_id)
        broad = any(
            e.numeric_valid_z and e.flag in (11, 12, 13, 14, 19)
            for e in data.all_groups.get(source_id, [])
        )
        primary = is_secure and not veto and valid_tile and lephare == 0 and not broad
        validation = (
            is_secure and not veto and valid_tile and lephare in (0, 2) and (broad or lephare == 2)
        )
        changes["primary_galaxy"] += primary
        changes["separate_validation"] += validation
        baseline_flag = baseline_flags.get(source_id, {})
        baseline_veto = bool(
            baseline_flag.get("unique_numeric_conflict")
        ) or bool(baseline_flag.get("secure_all_conflict"))
        baseline_secure = (
            entry is not None and ssv.entry_is_secure(entry)
        )
        baseline_primary = (
            baseline_secure
            and not baseline_veto
            and valid_tile
            and lephare == 0
            and not broad
        )
        baseline_validation = (
            baseline_secure
            and not baseline_veto
            and valid_tile
            and lephare in (0, 2)
            and (broad or lephare == 2)
        )
        baseline_counts["primary"] += baseline_primary
        baseline_counts["validation"] += baseline_validation
        if primary and not baseline_primary:
            changes["gained_primary"].append(
                (source_id, _change_reason(veto, baseline_veto, is_secure, baseline_secure))
            )
        if baseline_primary and not primary:
            changes["lost_primary"].append(
                (source_id, _change_reason(veto, baseline_veto, is_secure, baseline_secure))
            )
        if validation and not baseline_validation:
            changes["gained_validation"].append(
                (source_id, _change_reason(veto, baseline_veto, is_secure, baseline_secure))
            )
        if baseline_validation and not validation:
            changes["lost_validation"].append(
                (source_id, _change_reason(veto, baseline_veto, is_secure, baseline_secure))
            )
    for key in ("gained_primary", "lost_primary", "gained_validation", "lost_validation"):
        entries = changes[key]
        changes[key] = {
            "count": len(entries),
            "reason_counts": dict(sorted(Counter(reason for _, reason in entries).items())),
            "examples": sorted(source for source, _ in entries[:10]),
        }
    changes["baseline_primary"] = baseline_counts["primary"]
    changes["baseline_validation"] = baseline_counts["validation"]
    return changes


def _change_reason(veto: bool, baseline_veto: bool, secure: bool, baseline_secure: bool) -> str:
    if baseline_secure and not secure:
        return "preferred_entry_left_secure_domain"
    if veto and not baseline_veto:
        return "new_conflict_veto"
    if baseline_veto and not veto:
        return "conflict_veto_resolved_under_variant"
    if secure and not baseline_secure:
        return "preferred_entry_became_secure"
    return "other_recombination"


def main() -> None:
    import argparse

    from src.features.specz_science import config as ss_config
    from src.features.specz_science import policy as ss_policy

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    paths = ss_config.resolve_paths()
    policy = ss_policy.load_frozen_policy(paths.policy_path)
    tile_mapping = ss_splits.tile_map(policy)
    data = ssv.load_snapshot_data(paths=paths)
    preferred = ssv.preferred_entry_independent(data)
    flags = ssv.conflict_flags_independent(data)
    coverage = baseline_coverage(data, tile_mapping, preferred=preferred, flags=flags)
    primary_population = {
        source_id
        for source_id in data.catalog_ids
        if _is_primary(data, tile_mapping, source_id, preferred, flags)
    }
    validation_population = {
        source_id
        for source_id in data.catalog_ids
        if _is_validation(data, tile_mapping, source_id, preferred, flags)
    }
    coverage["photometric_coverage_primary_galaxy"] = photometric_coverage(
        data, primary_population
    )
    coverage["photometric_coverage_separate_validation"] = photometric_coverage(
        data, validation_population
    )
    coverage["photometric_coverage_full_catalog"] = photometric_coverage(
        data, set(data.catalog_ids)
    )
    coverage["sensitivity_variants"] = {
        "min_confidence_97": sensitivity_variant(
            data, tile_mapping, name="min_confidence_97", confidence_min=97
        ),
        "abs_threshold_0p001": sensitivity_variant(
            data, tile_mapping, name="abs_threshold_0p001", threshold=0.001
        ),
        "normalized_0p005": sensitivity_variant(
            data, tile_mapping, name="normalized_0p005", normalized_threshold=0.005
        ),
    }
    output = args.output if args.output is not None else (
        paths.staging_dir / "coverage-5-7.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(coverage, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"written": str(output)}, indent=2))


def _is_primary(
    data: SnapshotData, tile_mapping, source_id: int, preferred, flags
) -> bool:
    entry = preferred.get(source_id)
    flag = flags.get(source_id, {})
    return bool(
        entry is not None
        and ssv.entry_is_secure(entry)
        and not flag.get("unique_numeric_conflict")
        and not flag.get("secure_all_conflict")
        and data.catalog[source_id].tile in tile_mapping
        and data.lephare_type.get(source_id) == 0
        and not any(
            e.numeric_valid_z and e.flag in (11, 12, 13, 14, 19)
            for e in data.all_groups.get(source_id, [])
        )
    )


def _is_validation(
    data: SnapshotData, tile_mapping, source_id: int, preferred, flags
) -> bool:
    entry = preferred.get(source_id)
    flag = flags.get(source_id, {})
    lephare = data.lephare_type.get(source_id)
    broad = any(
        e.numeric_valid_z and e.flag in (11, 12, 13, 14, 19)
        for e in data.all_groups.get(source_id, [])
    )
    return bool(
        entry is not None
        and ssv.entry_is_secure(entry)
        and not flag.get("unique_numeric_conflict")
        and not flag.get("secure_all_conflict")
        and data.catalog[source_id].tile in tile_mapping
        and lephare in (0, 2)
        and (broad or lephare == 2)
    )


if __name__ == "__main__":
    main()
