"""Measurement audit and source summary construction (P-01 through P-05).

Builds the two record products over the captured snapshot under the frozen
policy. Native values ride along untouched in the measurement audit; every
derived predicate is a visibly separate field with machine-readable
reasons. Split-dependent eligibility stays unfinalized here (P-06 runs in
gate 5.5 and then finalizes both secure-use booleans).

The builders restate the policy predicates locally instead of calling the
independent verifier in ``verify.py``: the verifier's value is being a
second implementation, so sharing code would destroy the discrimination
the gate 5.7 checks rely on.
"""

from __future__ import annotations

import math
from typing import Any, Iterator, Mapping

from src.features.specz_science import splits as ss_splits
from src.features.specz_science import verify as ssv
from src.features.specz_science.verify import SnapshotData, SpeczEntry

CONFLICT_THRESHOLD = 0.005
SECURE_FLAGS = (3, 4, 13, 14)
SECURE_CONFIDENCE_MIN = 95
SECURE_CONFIDENCE_MAX = 100
CONFIDENCE_DOMAIN = (0, 100)
BROAD_LINE_FLAGS = (11, 12, 13, 14, 19)
GALAXY_TYPE = 0
STELLAR_TYPE = 1
QSO_TYPE = 2

ASSOCIATED = "associated"
NO_ASSOCIATION = "no_association_sentinel"
UNRESOLVED_IDENTIFIER = "unresolved_identifier"

# Mutually overlapping exclusion reasons (never collapsed into additive
# counts; a source may carry several).
REASON_NO_ASSOCIATION = "no_association"
REASON_A_ONLY_NO_UNIQUE = "population_a_no_unique_entries"
REASON_NO_NUMERIC_VALID_UNIQUE = "no_numeric_valid_unique_candidate"
REASON_NOT_SECURE_FLAG = "preferred_flag_not_in_secure_domain"
REASON_NOT_SECURE_CONFIDENCE_LOW = "preferred_confidence_below_95"
REASON_NOT_SECURE_CONFIDENCE_INVALID = "preferred_confidence_out_of_domain"
REASON_NOT_SECURE_MAPPING = "preferred_flag_confidence_mapping_inconsistent"
REASON_NOT_SECURE_Z = "preferred_z_not_numeric_valid"
REASON_UNIQUE_NUMERIC_CONFLICT = "unique_numeric_conflict"
REASON_SECURE_ALL_CONFLICT = "secure_all_conflict"
REASON_TYPE_STELLAR = "photometric_type_stellar"
REASON_TYPE_UNKNOWN = "photometric_type_unknown_or_missing"
REASON_BROAD_LINE_PRESENT = "broad_line_evidence_present"
REASON_NO_BROAD_LINE_OR_QSO = "no_broad_line_or_photometric_qso_evidence"
REASON_SPLIT_UNASSIGNED = "split_unassigned"
REASON_TYPE_NOT_ALLOWED_VALIDATION = "photometric_type_not_allowed_for_validation"

CORROBORATION_CONFLICTING = "conflicting"
CORROBORATION_MULTIPLY = "multiply_supported"
CORROBORATION_SINGLY = "singly_supported"
CORROBORATION_NOT_ASSESSABLE = "not_assessable"


# =============================================================================
# Measurement predicates (P-02)
# =============================================================================


def z_invalid_reason(entry: SpeczEntry) -> str | None:
    """Reason a measurement's redshift fails numeric validity, else None."""
    if entry.specz is None:
        return "z_missing"
    if not math.isfinite(entry.specz):
        return "z_non_finite"
    if not entry.specz > 0.0:
        return "z_non_positive"
    return None


def flag_category(flag: int | None) -> str:
    if flag is None:
        return "flag_missing"
    if flag in (0, 10):
        return "non_measured"
    if flag in (1, 2, 3, 4, 9, 11, 12, 13, 14, 19):
        return "recognized_measured"
    return "unrecognized"


def confidence_in_domain(confidence: int | None) -> bool:
    return confidence is not None and CONFIDENCE_DOMAIN[0] <= confidence <= CONFIDENCE_DOMAIN[1]


def mapping_consistency(entry: SpeczEntry) -> bool | None:
    """None when the flag admits no documented mapping; else agreement."""
    expected = ssv.flag_confidence(entry.flag) if entry.flag is not None else None
    if expected is None:
        return None
    return entry.confidence_level == expected


def measurement_is_secure(entry: SpeczEntry) -> bool:
    """P-02 secure predicate (builder's own restatement)."""
    if z_invalid_reason(entry) is not None:
        return False
    if entry.flag not in SECURE_FLAGS:
        return False
    if not confidence_in_domain(entry.confidence_level):
        return False
    if not SECURE_CONFIDENCE_MIN <= entry.confidence_level <= SECURE_CONFIDENCE_MAX:
        return False
    return mapping_consistency(entry) is True


def secure_block_reasons(entry: SpeczEntry) -> list[str]:
    """Every failed secure conjunct for this measurement, possibly several."""
    reasons: list[str] = []
    if z_invalid_reason(entry) is not None:
        reasons.append(REASON_NOT_SECURE_Z)
    if entry.flag not in SECURE_FLAGS:
        reasons.append(REASON_NOT_SECURE_FLAG)
    if entry.confidence_level is None or not confidence_in_domain(entry.confidence_level):
        reasons.append(REASON_NOT_SECURE_CONFIDENCE_INVALID)
    elif not SECURE_CONFIDENCE_MIN <= entry.confidence_level <= SECURE_CONFIDENCE_MAX:
        reasons.append(REASON_NOT_SECURE_CONFIDENCE_LOW)
    if mapping_consistency(entry) is False:
        reasons.append(REASON_NOT_SECURE_MAPPING)
    return reasons


# =============================================================================
# Measurement audit records (P-01, P-02)
# =============================================================================


def association_fields(
    entry: SpeczEntry, catalog_ids: set[int], no_association_sentinel: int
) -> tuple[str, int | None]:
    """Association status and nullable resolved catalog id for one entry."""
    identifier = entry.id_cosmos25
    if identifier is None or identifier == no_association_sentinel:
        return NO_ASSOCIATION, None
    if identifier in catalog_ids:
        return ASSOCIATED, identifier
    return UNRESOLVED_IDENTIFIER, None


def measurement_record(
    entry: SpeczEntry,
    *,
    run_id: str,
    catalog_ids: set[int],
    unique_ids: set[int],
    no_association_sentinel: int,
) -> dict[str, Any]:
    """One measurement audit row: 32 native fields plus derived predicates."""
    status, resolved = association_fields(entry, catalog_ids, no_association_sentinel)
    native = {
        "native_" + name: getattr(entry, name)
        for name in SpeczEntry.__dataclass_fields__
        if name != "id_specz"
    }
    return {
        "run_id": run_id,
        "id_specz": entry.id_specz,
        **native,
        "association_status": status,
        "resolved_catalog_id": resolved,
        "is_unique_member": entry.id_specz in unique_ids,
        "numeric_valid_z": z_invalid_reason(entry) is None,
        "z_invalid_reason": z_invalid_reason(entry),
        "flag_category": flag_category(entry.flag),
        "confidence_in_domain": confidence_in_domain(entry.confidence_level),
        "flag_confidence_mapping_consistent": mapping_consistency(entry),
        "secure_measurement": measurement_is_secure(entry),
        "secure_block_reasons": secure_block_reasons(entry),
    }


def build_measurement_records(
    data: SnapshotData,
    *,
    run_id: str,
    no_association_sentinel: int = -999,
) -> Iterator[dict[str, Any]]:
    """All `_all` entries in `id_specz` order (the table's declared key)."""
    unique_ids = set(data.unique_by_id)
    for entry in sorted(data.all_entries, key=lambda item: item.id_specz):
        yield measurement_record(
            entry,
            run_id=run_id,
            catalog_ids=data.catalog_ids,
            unique_ids=unique_ids,
            no_association_sentinel=no_association_sentinel,
        )


# =============================================================================
# Source-level policy (P-03, P-04, P-05)
# =============================================================================


def preferred_selection(
    entries: list[SpeczEntry],
) -> tuple[SpeczEntry | None, list[int], bool]:
    """P-03: highest valid confidence in [0,100]; ties to ascending id_specz.

    Returns the selected entry, the full tie list at the winning confidence,
    and whether the selection was tied. Missing or out-of-domain confidence
    sorts below any valid confidence.
    """

    def rank(entry: SpeczEntry) -> tuple[int, int, int]:
        confidence = entry.confidence_level
        valid = confidence_in_domain(confidence)
        return (
            0 if valid else 1,
            -(confidence if valid else -1),
            entry.id_specz,
        )

    candidates = sorted(
        (entry for entry in entries if entry.numeric_valid_z), key=rank
    )
    if not candidates:
        return None, [], False
    winner = candidates[0]
    winner_valid = confidence_in_domain(winner.confidence_level)
    tied = sorted(
        entry.id_specz
        for entry in candidates
        if entry.confidence_level == winner.confidence_level
        and confidence_in_domain(entry.confidence_level) == winner_valid
    )
    return winner, tied, len(tied) > 1


def pairwise_witnesses(
    entries: list[SpeczEntry], *, threshold: float, both_secure: bool | None
) -> list[dict[str, Any]]:
    """Witness records for pairs exceeding the threshold.

    ``both_secure`` filters the pair class: True keeps secure-secure pairs,
    False keeps pairs that are not both secure, None keeps all.
    """
    witnesses: list[dict[str, Any]] = []
    qualifying = [entry for entry in entries if entry.numeric_valid_z]
    for i in range(len(qualifying)):
        for j in range(i + 1, len(qualifying)):
            left, right = qualifying[i], qualifying[j]
            difference = abs(left.specz - right.specz)  # type: ignore[operator]
            if difference <= threshold:
                continue
            if both_secure is True and not (
                measurement_is_secure(left) and measurement_is_secure(right)
            ):
                continue
            if both_secure is False and (
                measurement_is_secure(left) and measurement_is_secure(right)
            ):
                continue
            witnesses.append(
                {
                    "left_id_specz": left.id_specz,
                    "right_id_specz": right.id_specz,
                    "left_z": left.specz,
                    "right_z": right.specz,
                    "left_flag": left.flag,
                    "right_flag": right.flag,
                    "left_confidence": left.confidence_level,
                    "right_confidence": right.confidence_level,
                    "abs_difference": difference,
                }
            )
    return witnesses


def classification_label(lephare_type: int | None) -> str:
    if lephare_type is None:
        return "unknown_missing"
    if lephare_type == GALAXY_TYPE:
        return "galaxy"
    if lephare_type == STELLAR_TYPE:
        return "star"
    if lephare_type == QSO_TYPE:
        return "qso"
    return "unknown_unrecognized"


def source_record(
    source_id: int,
    data: SnapshotData,
    *,
    run_id: str,
    threshold: float = CONFLICT_THRESHOLD,
) -> dict[str, Any]:
    """One catalog source's summary under the frozen policy (pre-split)."""
    catalog_source = data.catalog[source_id]
    unique_entries = data.unique_groups.get(source_id, [])
    all_entries = data.all_groups.get(source_id, [])
    lephare_type = data.lephare_type.get(source_id)
    label = classification_label(lephare_type)

    preferred, tied_ids, tied = preferred_selection(unique_entries)
    numeric_valid_unique = [e for e in unique_entries if e.numeric_valid_z]
    secure_all = [e for e in all_entries if measurement_is_secure(e)]
    broad_entries = [
        e for e in all_entries if e.numeric_valid_z and e.flag in BROAD_LINE_FLAGS
    ]
    broad_line_reported = bool(broad_entries)
    photometric_qso = lephare_type == QSO_TYPE

    unique_witnesses = pairwise_witnesses(
        unique_entries, threshold=threshold, both_secure=None
    )
    unique_conflict = any(
        witness for witness in unique_witnesses
    ) if len(numeric_valid_unique) >= 2 else False
    secure_witnesses = pairwise_witnesses(
        all_entries, threshold=threshold, both_secure=True
    )
    secure_conflict = len(secure_witnesses) > 0
    other_witnesses = pairwise_witnesses(
        all_entries, threshold=threshold, both_secure=False
    )
    other_disagreement = len(other_witnesses) > 0

    if len(secure_all) < 2:
        corroboration = CORROBORATION_NOT_ASSESSABLE if len(secure_all) == 0 else CORROBORATION_SINGLY
        if len(secure_all) == 1 and secure_conflict:
            corroboration = CORROBORATION_CONFLICTING
    else:
        corroboration = (
            CORROBORATION_CONFLICTING if secure_conflict else CORROBORATION_MULTIPLY
        )

    reasons: list[str] = []
    if not unique_entries and not all_entries:
        reasons.append(REASON_NO_ASSOCIATION)
    if all_entries and not unique_entries:
        reasons.append(REASON_A_ONLY_NO_UNIQUE)
    preferred_secure = False
    if preferred is None:
        if unique_entries:
            reasons.append(REASON_NO_NUMERIC_VALID_UNIQUE)
    else:
        preferred_secure = measurement_is_secure(preferred)
        if not preferred_secure:
            for reason in secure_block_reasons(preferred):
                reasons.append(reason)
    if unique_conflict:
        reasons.append(REASON_UNIQUE_NUMERIC_CONFLICT)
    if secure_conflict:
        reasons.append(REASON_SECURE_ALL_CONFLICT)
    if label == "star":
        reasons.append(REASON_TYPE_STELLAR)
    if label in ("unknown_missing", "unknown_unrecognized"):
        reasons.append(REASON_TYPE_UNKNOWN)
    if broad_line_reported:
        reasons.append(REASON_BROAD_LINE_PRESENT)
    if not broad_line_reported and not photometric_qso:
        reasons.append(REASON_NO_BROAD_LINE_OR_QSO)

    eligible_basis = (
        source_id in data.catalog_ids
        and preferred is not None
        and preferred_secure
        and not unique_conflict
        and not secure_conflict
        and label == "galaxy"
        and not broad_line_reported
    )
    validation_basis = (
        source_id in data.catalog_ids
        and preferred is not None
        and preferred_secure
        and not unique_conflict
        and not secure_conflict
        and label in ("galaxy", "qso")
        and (broad_line_reported or photometric_qso)
    )

    return {
        "run_id": run_id,
        "catalog_id": source_id,
        "association_resolved": bool(unique_entries or all_entries),
        "population_a": bool(all_entries and not unique_entries),
        "population_b": len(unique_entries) > 1,
        "unique_entry_count": len(unique_entries),
        "all_entry_count": len(all_entries),
        "numeric_valid_all_count": sum(
            1 for e in all_entries if e.numeric_valid_z
        ),
        "secure_all_count": len(secure_all),
        "preferred_id_specz": preferred.id_specz if preferred else None,
        "preferred_reported_z": preferred.specz if preferred else None,
        "preferred_flag": preferred.flag if preferred else None,
        "preferred_confidence": preferred.confidence_level if preferred else None,
        "preferred_tie": tied,
        "preferred_tied_ids": tied_ids if preferred else [],
        "preferred_entry_is_secure": preferred_secure,
        "unique_numeric_conflict": unique_conflict,
        "secure_all_conflict": secure_conflict,
        "other_measurement_disagreement": other_disagreement,
        "conflict_witnesses": {
            "threshold": threshold,
            "unique_numeric": unique_witnesses,
            "secure_all": secure_witnesses,
            "other_measurement": other_witnesses,
        },
        "corroboration_status": corroboration,
        "lephare_type": lephare_type,
        "classification_label": label,
        "broad_line_reported": broad_line_reported,
        "broad_line_entry_ids": [e.id_specz for e in broad_entries],
        "broad_line_confidences": [
            e.confidence_level for e in broad_entries
        ],
        "photometric_qso": photometric_qso,
        "flag_star_mask_overlap": catalog_source.flag_star,
        "flag_blend": catalog_source.flag_blend,
        "native_tile": catalog_source.tile,
        "eligibility_primary_galaxy": None,
        "eligibility_separate_validation": None,
        "eligibility_basis_primary_pre_split": eligible_basis,
        "eligibility_basis_validation_pre_split": validation_basis,
        "exclusion_reasons": sorted(set(reasons)),
    }


def build_source_records(
    data: SnapshotData,
    *,
    run_id: str,
    threshold: float = CONFLICT_THRESHOLD,
) -> Iterator[dict[str, Any]]:
    """One summary per catalog source, in `catalog_id` order."""
    for source_id in sorted(data.catalog_ids):
        yield source_record(source_id, data, run_id=run_id, threshold=threshold)


def finalize_eligibility(
    record: dict[str, Any], assigned_split: str, unassigned_label: str
) -> dict[str, Any]:
    """Apply P-06 to a source record: split gate plus final booleans.

    Gate 5.5 calls this after the tile map exists; the split-dependent
    fields written here are exactly the ones left null in gate 5.4.
    """
    valid_split = assigned_split != unassigned_label
    reasons = list(record["exclusion_reasons"])
    if not valid_split:
        reasons.append(REASON_SPLIT_UNASSIGNED)
    primary = (
        record["eligibility_basis_primary_pre_split"] and valid_split
    )
    separate = (
        record["eligibility_basis_validation_pre_split"] and valid_split
    )
    finalized = dict(record)
    finalized["assigned_split"] = assigned_split
    finalized["eligibility_primary_galaxy"] = primary
    finalized["eligibility_separate_validation"] = separate
    finalized["exclusion_reasons"] = sorted(set(reasons))
    return finalized


def build_split_records(
    data: SnapshotData, *, run_id: str, tile_mapping: Mapping[str, str],
    unassigned_label: str = ss_splits.UNASSIGNED, salt: str = "cosmos2025-p2r05-spatial-v1",
) -> Iterator[dict[str, Any]]:
    """One split record per catalog source, in `catalog_id` order."""
    for source_id in sorted(data.catalog_ids):
        tile = data.catalog[source_id].tile
        yield {
            "run_id": run_id,
            "catalog_id": source_id,
            "native_tile": tile,
            "assigned_split": ss_splits.assign_tile(tile_mapping, tile),
            "split_version": "p2r05-spatial-v1",
            "split_salt": salt,
            "valid_tile_domain_member": tile in tile_mapping,
            "unassigned": ss_splits.assign_tile(tile_mapping, tile) == unassigned_label,
        }
