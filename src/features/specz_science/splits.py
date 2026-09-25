"""P-06 frozen tile partitions: deterministic, policy-driven, rebalance-free.

The assignment depends only on each source's native tile and the fixed
algorithm: SHA-256 over UTF-8 ``cosmos2025-p2r05-spatial-v1|<tile>`` without
a trailing newline, labels sorted by full hexadecimal digest (ties broken by
tile string), first four holdout, next four validation, remaining twelve
development. Null or out-of-domain tiles are ``unassigned`` and fail
secure-use eligibility. Nothing about spectroscopy, quality, or counts may
enter the assignment, and no re-rolling for balance is permitted.
"""

from __future__ import annotations

import hashlib
from typing import Mapping

from src.features.specz_science import policy as ss_policy

DEVELOPMENT = "development"
VALIDATION = "validation"
HOLDOUT = "holdout"
UNASSIGNED = "unassigned"
ASSIGNMENT_VALUES = (DEVELOPMENT, VALIDATION, HOLDOUT, UNASSIGNED)


def tile_map(policy: Mapping[str, object]) -> dict[str, str]:
    """Compute the frozen tile map exactly as P-06 specifies.

    Raises ``ss_policy.PolicyError`` if the policy's tile domain or counts
    are inconsistent (sum of partitions must equal the domain size).
    """
    splits = policy["splits"]
    domain = tuple(splits["valid_tile_domain"])
    if len(set(domain)) != len(domain):
        raise ss_policy.PolicyError("splits.valid_tile_domain: duplicate labels")
    holdout = int(splits["holdout_count"])
    validation = int(splits["validation_count"])
    development = int(splits["development_count"])
    if holdout + validation + development != len(domain):
        raise ss_policy.PolicyError(
            "splits: partition counts do not sum to the tile domain size"
        )
    salt = str(splits["salt"])
    encoding = str(splits["encoding"])
    algorithm = str(splits["hash_algorithm"])
    if algorithm != "sha256":
        raise ss_policy.PolicyError(f"splits.hash_algorithm: unsupported {algorithm!r}")
    if splits["trailing_newline"]:
        raise ss_policy.PolicyError("splits.trailing_newline: P-06 forbids a newline")
    ranked = sorted(
        (
            hashlib.new(
                algorithm, f"{salt}|{tile}".encode(encoding)
            ).hexdigest(),
            tile,
        )
        for tile in domain
    )
    assignment: dict[str, str] = {}
    for index, (_, tile) in enumerate(ranked):
        if index < holdout:
            assignment[tile] = HOLDOUT
        elif index < holdout + validation:
            assignment[tile] = VALIDATION
        else:
            assignment[tile] = DEVELOPMENT
    return assignment


def assign_tile(tile_map: Mapping[str, str], tile: str | None) -> str:
    """Assign one native tile; null or out-of-domain yields ``unassigned``."""
    if tile is None:
        return UNASSIGNED
    return tile_map.get(tile, UNASSIGNED)


def canonical_tile_map_digest(mapping: Mapping[str, str]) -> str:
    """SHA-256 over the canonical ``tile=assignment`` serialization."""
    payload = "\n".join(
        f"{tile}={mapping[tile]}" for tile in sorted(mapping)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
