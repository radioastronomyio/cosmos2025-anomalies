#!/usr/bin/env python3
"""
Script Name  : build_data_manifest.py
Description  : Pin the COSMOS-Web v1.1 holdings and spec-z compilation with SHA-256 manifests
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-15
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Spec P2R-01 gate 1.7 utility. Walks the two local provenance roots named in
configs/data_paths.yaml (the NVMe v1.1 catalog holdings and the spec-z
compilation git checkout), records SHA-256, byte size, and mtime for every
file, captures the checkout's git HEAD, and verifies LFS materialization for
every LFS-tracked file (a pointer is a ~130-byte text file; data is not).
Attempts to open the compilation's *_unique.fits under astropy and record
its row count. Read-only against the roots: it opens files for hashing and
nothing else. The off-box CIGALE SED root is recorded in the summary by
host and path only, never hashed.

Usage
-----
    python src/inspection/build_data_manifest.py

Examples
--------
    python src/inspection/build_data_manifest.py
        Writes docs/reference/data-manifest-v1.1.csv and a summary JSON to
        stdout capture for the markdown summary.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
CSV_PATH = REPO_ROOT / "docs" / "reference" / "data-manifest-v1.1.csv"
SUMMARY_JSON = REPO_ROOT / "staging" / "manifest-summary-v1.1.json"

# HUMAN NOTE: LFS patterns mirror the checkout's .gitattributes (fitted
# dynamically at runtime; this constant is only the pointer-detection size
# threshold, anything smaller than this cannot be the data).
POINTER_MAX_BYTES = 1024

# =============================================================================
# Functions
# =============================================================================


def sha256_of(path: Path) -> str:
    """Stream a file through SHA-256 without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_root(root: Path) -> list[dict]:
    """Hash every regular file under root, newest-stable order (walk order)."""
    rows = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            path = Path(dirpath) / name
            stat = path.stat()
            rows.append(
                {
                    "root": str(root),
                    "relative_path": str(path.relative_to(root)),
                    "sha256": sha256_of(path),
                    "bytes": stat.st_size,
                    "mtime_utc": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(timespec="seconds"),
                }
            )
    return rows


def git_head(root: Path) -> str:
    """Return the checkout's HEAD commit SHA."""
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def lfs_patterns(root: Path) -> list[str]:
    """Extract LFS-tracked filename patterns from the checkout's .gitattributes."""
    attrs = root / ".gitattributes"
    patterns = []
    if attrs.exists():
        for line in attrs.read_text().splitlines():
            fields = line.split()
            if len(fields) >= 2 and any(f == "filter=lfs" for f in fields[1:]):
                patterns.append(fields[0])
    return patterns


def check_lfs_materialization(root: Path, patterns: list[str]) -> list[dict]:
    """
    Verify every LFS-pattern file under root is data, not a pointer.

    A materialized file is larger than POINTER_MAX_BYTES; a pointer is a
    short text file starting with the LFS spec header. FITS files that are
    materialized are additionally opened under astropy.
    """
    results = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            path = Path(dirpath) / name
            matched = any(Path(name).match(p) for p in patterns)
            if not matched:
                continue
            size = path.stat().st_size
            is_pointer = False
            if size <= POINTER_MAX_BYTES:
                with path.open("rb") as handle:
                    is_pointer = handle.read(64).startswith(b"version https://git-lfs")
            entry = {
                "file": str(path.relative_to(root)),
                "bytes": size,
                "state": "pointer" if is_pointer else "materialized",
            }
            if not is_pointer and path.suffix == ".fits" and size > POINTER_MAX_BYTES:
                try:
                    from astropy.io import fits

                    with fits.open(path, memmap=True) as hdul:
                        entry["astropy_opens"] = True
                        entry["hdu_count"] = len(hdul)
                except Exception as exc:  # noqa: BLE001 - record, never crash the manifest
                    entry["astropy_opens"] = False
                    entry["astropy_error"] = str(exc)[:200]
            results.append(entry)
    return results


def try_unique_fits(path: Path) -> dict:
    """Attempt to open the compilation's unique.fits and count rows."""
    record = {"path": str(path), "bytes": path.stat().st_size if path.exists() else None}
    try:
        from astropy.io import fits

        with fits.open(path, memmap=True) as hdul:
            data = hdul[1].data
            record["opens"] = True
            record["row_count"] = int(len(data))
    except Exception as exc:  # noqa: BLE001 - failure is itself the finding
        record["opens"] = False
        record["error"] = str(exc)[:200]
    return record


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Build the pinned manifest for both local provenance roots."""
    config = yaml.safe_load(CONFIG_PATH.read_text())
    data_root = Path(config["data_root"])
    specz_root = Path(config["specz"]["compilation_root"])
    unique_fits = Path(config["specz"]["unique_fits"])

    rows = manifest_root(data_root)
    specz_rows = manifest_root(specz_root)
    all_rows = rows + specz_rows

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    patterns = lfs_patterns(specz_root)
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "roots": {
            "nvme_holdings": {
                "path": str(data_root),
                "file_count": len(rows),
                "total_bytes": sum(r["bytes"] for r in rows),
            },
            "speczcompilation": {
                "path": str(specz_root),
                "git_head": git_head(specz_root),
                "file_count": len(specz_rows),
                "total_bytes": sum(r["bytes"] for r in specz_rows),
            },
            "external_cigale_seds": config["external_holdings"]["cigale_seds_root"],
        },
        "lfs_patterns": patterns,
        "lfs_materialization": check_lfs_materialization(specz_root, patterns),
        "unique_fits": try_unique_fits(unique_fits),
        "csv_path": str(CSV_PATH),
        "csv_row_count": len(all_rows),
    }
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
