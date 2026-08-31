#!/usr/bin/env python3
"""
Script Name  : reconciliation_core_v11.py
Description  : Pure sampling and exact-value core for ETL v2 reconciliation
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Provides loader-independent, deterministic primitives for Gate 3.11. This
module performs no filesystem or PostgreSQL mutation.
"""

from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================

import hashlib
import heapq
import json
import math
import numbers
import os
import stat
import struct
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import IO
from typing import Any, Mapping, Sequence

import numpy as np


# =============================================================================
# Frozen sampling contract
# =============================================================================

MASTER_SAMPLE_SEED = 1_380_376_179_526_893_666
TABLE_SAMPLE_SEEDS = {
    "lss_overdensity": 4_976_263_942_886_350_198,
    "galaxy_groups": 4_652_599_078_883_424_958,
    "galaxy_group_memberships": 15_583_989_488_859_696_288,
    "specz_compilation_unique": 9_076_022_164_977_561_485,
}

INTEGER_RANGES = {
    "smallint": (-(2**15), 2**15 - 1),
    "integer": (-(2**31), 2**31 - 1),
    "bigint": (-(2**63), 2**63 - 1),
}


@dataclass(frozen=True)
class CanonicalCell:
    """One exact target-typed value represented without numeric tolerance."""

    token: tuple[Any, ...]


@dataclass(frozen=True)
class Mismatch:
    """Complete source/target evidence for one exact value mismatch."""

    source_locator: str
    table: str
    column: str
    source_value: tuple[Any, ...]
    database_value: tuple[Any, ...]
    matching_method: str
    sample_locator: int | str | tuple[Any, ...]
    element_index: int | None


class MismatchLedger:
    """Stream complete mismatch JSONL to one exact protected local file."""

    def __init__(
        self,
        *,
        final_path: Path,
        temporary_path: Path,
        handle: IO[str],
        identity: tuple[int, int],
    ) -> None:
        self.final_path = final_path
        self.temporary_path = temporary_path
        self._handle = handle
        self._identity = identity
        self._count = 0
        self._closed = False

    @classmethod
    def create(cls, path: Path, *, allowed_root: Path) -> MismatchLedger:
        """Exclusively create one no-follow mode-0600 temporary ledger."""
        root = allowed_root.resolve(strict=True)
        parent = path.parent.resolve(strict=True)
        if not root.is_dir() or (parent != root and root not in parent.parents):
            raise ValueError("ledger containment mismatch")
        try:
            path.lstat()
        except FileNotFoundError:
            pass
        else:
            raise ValueError("ledger final path exists")
        temporary = parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(temporary, flags, 0o600)
        try:
            observed = os.fstat(descriptor)
            if (
                not stat.S_ISREG(observed.st_mode)
                or stat.S_IMODE(observed.st_mode) != 0o600
            ):
                raise RuntimeError("ledger temporary metadata mismatch")
            handle = os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")
        except Exception:
            os.close(descriptor)
            temporary.unlink(missing_ok=True)
            raise
        return cls(
            final_path=path,
            temporary_path=temporary,
            handle=handle,
            identity=(observed.st_dev, observed.st_ino),
        )

    def write(self, mismatch: Mismatch) -> None:
        """Append one complete mismatch without truncation or value omission."""
        if self._closed or not isinstance(mismatch, Mismatch):
            raise ValueError("ledger write state mismatch")
        payload = {
            "source_locator": mismatch.source_locator,
            "table": mismatch.table,
            "column": mismatch.column,
            "source_value": mismatch.source_value,
            "database_value": mismatch.database_value,
            "matching_method": mismatch.matching_method,
            "sample_locator": mismatch.sample_locator,
            "element_index": mismatch.element_index,
        }
        self._handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        self._handle.write("\n")
        self._count += 1

    def _close(self, *, durable: bool) -> None:
        """Close the run-owned descriptor, optionally flushing durable bytes."""
        if self._closed:
            return
        if durable:
            self._handle.flush()
            os.fsync(self._handle.fileno())
        self._handle.close()
        self._closed = True

    def _temporary_stat(self) -> os.stat_result:
        """Require the temporary path still names the exact created inode."""
        observed = self.temporary_path.lstat()
        if (
            (observed.st_dev, observed.st_ino) != self._identity
            or not stat.S_ISREG(observed.st_mode)
            or stat.S_IMODE(observed.st_mode) != 0o600
        ):
            raise RuntimeError("ledger cleanup identity mismatch")
        return observed

    def _fsync_parent(self) -> None:
        """Durably record link/unlink directory operations."""
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(self.final_path.parent, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def seal(self) -> dict[str, int | bool]:
        """Publish the exact complete ledger without overwriting any path."""
        if self._count < 1:
            raise ValueError("ledger cannot seal empty evidence")
        self._close(durable=True)
        self._temporary_stat()
        try:
            os.link(self.temporary_path, self.final_path, follow_symlinks=False)
            final = self.final_path.lstat()
            if (final.st_dev, final.st_ino) != self._identity:
                raise RuntimeError("ledger final identity mismatch")
            self._temporary_stat()
            self.temporary_path.unlink()
            self._fsync_parent()
        except Exception:
            try:
                self._temporary_stat()
            except (FileNotFoundError, RuntimeError):
                pass
            else:
                self.temporary_path.unlink()
            raise
        return {"mismatch_count": self._count, "ledger_created": True}

    def abort(self) -> None:
        """Remove only the exact run-owned temporary after an interrupted write."""
        self._close(durable=False)
        self._temporary_stat()
        self.temporary_path.unlink()
        self._fsync_parent()


# =============================================================================
# Deterministic sampling
# =============================================================================


def ranked_sample(population: int, sample_size: int, seed: int) -> tuple[int, ...]:
    """Select the lowest seeded SHA-256 ranks with bounded memory."""
    if (
        not isinstance(population, int)
        or not isinstance(sample_size, int)
        or not isinstance(seed, int)
        or population < 1
        or sample_size < 1
        or sample_size > population
        or seed < 0
        or seed >= 2**64
    ):
        raise ValueError("sample boundary mismatch")
    if sample_size == population:
        return tuple(range(population))
    seed_bytes = seed.to_bytes(8, "big")
    retained: list[tuple[int, int, int]] = []
    for ordinal in range(population):
        digest = hashlib.sha256(seed_bytes + ordinal.to_bytes(8, "big")).digest()
        rank = int.from_bytes(digest, "big")
        entry = (-rank, -ordinal, ordinal)
        if len(retained) < sample_size:
            heapq.heappush(retained, entry)
            continue
        largest = (-retained[0][0], -retained[0][1])
        if (rank, ordinal) < largest:
            heapq.heapreplace(retained, entry)
    return tuple(sorted(entry[2] for entry in retained))


def sample_digest(ordinals: tuple[int, ...]) -> str:
    """Hash the exact newline-delimited sorted sample for evidence."""
    if not ordinals or tuple(sorted(set(ordinals))) != ordinals:
        raise ValueError("sample digest boundary mismatch")
    payload = "".join(f"{ordinal}\n" for ordinal in ordinals).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


# =============================================================================
# Exact target-cast values
# =============================================================================


def _canonical_scalar(target_type: str, value: Any, *, source: bool) -> CanonicalCell:
    """Cast and tokenize one scalar using the declared PostgreSQL target type."""
    if value is None:
        return CanonicalCell(("null",))
    if source and isinstance(value, numbers.Real) and math.isnan(float(value)):
        return CanonicalCell(("null",))
    if target_type in INTEGER_RANGES:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, numbers.Integral
        ):
            raise ValueError("integer source type mismatch")
        converted = int(value)
        lower, upper = INTEGER_RANGES[target_type]
        if converted < lower or converted > upper:
            raise ValueError("integer target range mismatch")
        return CanonicalCell((target_type, converted))
    if target_type == "boolean":
        if not isinstance(value, (bool, np.bool_)):
            raise ValueError("boolean source type mismatch")
        return CanonicalCell((target_type, bool(value)))
    if target_type == "text":
        if isinstance(value, (bytes, np.bytes_)):
            converted = bytes(value).decode("utf-8")
        elif isinstance(value, (str, np.str_)):
            converted = str(value)
        else:
            raise ValueError("text source type mismatch")
        return CanonicalCell((target_type, converted))
    if target_type in {"real", "double precision"}:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
            raise ValueError("float source type mismatch")
        converted = float(value)
        if target_type == "real":
            token = struct.pack("!f", np.float32(converted)).hex()
        else:
            token = struct.pack("!d", converted).hex()
        return CanonicalCell((target_type, token))
    raise ValueError(f"unsupported target type: {target_type}")


def _mask_elements(masked: bool | Sequence[bool], size: int) -> tuple[bool, ...]:
    """Normalize one scalar/element mask without truthy shape coercion."""
    if isinstance(masked, (bool, np.bool_)):
        return (bool(masked),) * size
    observed = tuple(bool(value) for value in masked)
    if len(observed) != size:
        raise ValueError("array mask cardinality mismatch")
    return observed


def cast_source_cell(
    case: Mapping[str, Any],
    value: Any,
    *,
    masked: bool | Sequence[bool] = False,
) -> CanonicalCell:
    """Apply the frozen source NULL rule and exact declared target cast."""
    target_type = str(case["target_type"])
    if not target_type.endswith("[]"):
        if not isinstance(masked, (bool, np.bool_)):
            raise ValueError("scalar mask shape mismatch")
        if bool(masked):
            return CanonicalCell(("null",))
        return _canonical_scalar(target_type, value, source=True)
    if value is None:
        return CanonicalCell(("null",))
    array = np.asarray(value, dtype=object)
    expected = int(case["element_count"])
    if array.ndim != 1 or len(array) != expected:
        raise ValueError("array cardinality mismatch")
    masks = _mask_elements(masked, expected)
    base_type = target_type.removesuffix("[]")
    elements = tuple(
        CanonicalCell(("null",)).token
        if element_masked
        else _canonical_scalar(base_type, element, source=True).token
        for element, element_masked in zip(array, masks, strict=True)
    )
    return CanonicalCell((target_type, elements))


def canonicalize_database_cell(case: Mapping[str, Any], value: Any) -> CanonicalCell:
    """Tokenize an already target-typed database value without source nulling."""
    target_type = str(case["target_type"])
    if not target_type.endswith("[]"):
        return _canonical_scalar(target_type, value, source=False)
    if value is None:
        return CanonicalCell(("null",))
    if isinstance(value, (str, bytes)):
        raise ValueError("database array shape mismatch")
    elements = tuple(value)
    if len(elements) != int(case["element_count"]):
        raise ValueError("array cardinality mismatch")
    base_type = target_type.removesuffix("[]")
    return CanonicalCell(
        (
            target_type,
            tuple(
                _canonical_scalar(base_type, element, source=False).token
                for element in elements
            ),
        )
    )
