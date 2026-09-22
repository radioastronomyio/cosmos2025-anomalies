"""Canonical serialization, content digests, and deterministic run identity.

Canonical record form: JSON Lines, one object per line, keys in sorted
order, rows ordered by the product's declared key. JSON distinguishes null
from every finite sentinel and Python's shortest-repr floats are stable
for the same interpreter family. Operational timestamps never enter a
digest domain; the run identity covers approved policy identity, consumed
input content identities, and build-affecting implementation bytes only.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import psycopg

IMPLEMENTATION_MODULE_NAMES = (
    # Build-affecting modules only: these bytes change product content.
    # Verification and coverage modules are deliberately excluded so that
    # diagnostic edits cannot move the run identity of installed products.
    "policy",
    "config",
    "canonical",
    "build",
    "splits",
    "snapshot",
    "pipeline",
)


def canonical_line(record: Mapping[str, Any]) -> str:
    """Serialize one record canonically (sorted keys, no spaces)."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_bytes(records: Iterable[Mapping[str, Any]]) -> bytes:
    """Canonical byte form of a record sequence (newline-terminated)."""
    return "".join(canonical_line(record) + "\n" for record in records).encode("utf-8")


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_records(records: Iterable[Mapping[str, Any]]) -> str:
    """SHA-256 over the canonical serialization of a record sequence."""
    digest = hashlib.sha256()
    count = 0
    for record in records:
        digest.update((canonical_line(record) + "\n").encode("utf-8"))
        count += 1
    return digest.hexdigest()


def write_jsonl(
    path: Path, records: Iterable[Mapping[str, Any]]
) -> tuple[str, int]:
    """Stream records to a canonical JSONL artifact; return digest and count."""
    digest = hashlib.sha256()
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        for record in records:
            line = (canonical_line(record) + "\n").encode("utf-8")
            digest.update(line)
            handle.write(line)
            count += 1
    return digest.hexdigest(), count


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def implementation_digest(module_root: Path) -> dict[str, object]:
    """SHA-256 over the build-affecting code bytes and dependency identity.

    Names the modules whose bytes can change build output plus the Python
    and psycopg versions that govern execution behavior. A future closeout
    commit is deliberately outside this identity.
    """
    digests: dict[str, str] = {}
    for name in IMPLEMENTATION_MODULE_NAMES:
        path = module_root / f"{name}.py"
        if path.exists():
            digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "modules": digests,
        "python_version": platform.python_version(),
        "psycopg_version": psycopg.__version__,
        "platform": sys.platform,
    }


def build_run_identity(
    *,
    policy_digest: str,
    snapshot_manifest_digest: str,
    snapshot_file_digests: Mapping[str, str],
    implementation: Mapping[str, Any],
) -> dict[str, object]:
    """Assemble the run identity document (pre-image of the run ID)."""
    return {
        "policy_semantic_digest": policy_digest,
        "snapshot_manifest_digest": snapshot_manifest_digest,
        "snapshot_file_digests": dict(sorted(snapshot_file_digests.items())),
        "implementation": implementation,
    }


def run_id_from_identity(identity: Mapping[str, Any]) -> str:
    """Deterministic run identifier: sha256 of the canonical identity."""
    return digest_bytes(canonical_bytes([identity]))


def content_digest_document(
    *,
    measurements: str,
    sources: str,
    splits: str,
    measurement_rows: int,
    source_rows: int,
    split_rows: int,
) -> dict[str, object]:
    """The three product content digests, stored separately from file sums."""
    return {
        "measurements_content_sha256": measurements,
        "sources_content_sha256": sources,
        "splits_content_sha256": splits,
        "measurement_rows": measurement_rows,
        "source_rows": source_rows,
        "split_rows": split_rows,
    }
