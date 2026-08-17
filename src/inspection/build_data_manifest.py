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

Amendment P2R-02a: Git-checkout roots now exclude the `.git` directory from
the manifest boundary. The `.git` directory is mutable transport machinery,
not a data artifact. The manifest records worktree artifacts and the Git
commit SHA, not repository internals. The validator rejects any row with
`/.git/` in its path or starting `.git/`, and raises if a declared row does
not match on-disk in full verification mode.

Usage
-----
    python src/inspection/build_data_manifest.py [--verify]

Examples
--------
    python src/inspection/build_data_manifest.py
        Writes docs/reference/data-manifest-v1.1.csv and a summary JSON to
        stdout capture for the markdown summary.

    python src/inspection/build_data_manifest.py --verify
        Validates the existing CSV against the live filesystem without
        rewriting. Raises on mismatch or missing/extra files.
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


def manifest_root(root: Path, git_checkout: bool = False) -> list[dict]:
    """
    Hash every regular file under root.

    For git_checkout roots, exclude the .git directory entirely.
    The manifest records worktree artifacts, not mutable repository machinery.
    """
    rows = []
    excluded_dirs = {".git"} if git_checkout else set()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirpath_path = Path(dirpath)
        if excluded_dirs & set(dirpath_path.parts):
            dirnames.clear()
            filenames.clear()
            continue
        for name in sorted(filenames):
            path = dirpath_path / name
            stat = path.stat()
            relative = path.relative_to(root)
            rows.append(
                {
                    "root": str(root),
                    "relative_path": str(relative),
                    "sha256": sha256_of(path),
                    "bytes": stat.st_size,
                    "mtime_utc": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(timespec="seconds"),
                }
            )
    return rows


def validate_manifest(csv_path: Path, roots: list[tuple[Path, bool]]) -> list[str]:
    """
    Validate an existing manifest CSV against live filesystem.

    Returns list of error messages. Empty list means valid.
    Raises if any row has .git/ in its path (violation of durable boundary).
    """
    errors = []
    manifest_rows = {}
    for r in csv.DictReader(csv_path.open()):
        path = r["relative_path"]
        if "/.git/" in path or path.startswith(".git/"):
            raise AssertionError(f"Manifest contains .git/ path: {r['root']}/{path}")
        manifest_rows[(r["root"], path)] = r

    disk_files = {}
    for root, is_git_checkout in roots:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirpath_path = Path(dirpath)
            if is_git_checkout and ".git" in dirpath_path.parts:
                dirnames.clear()
                filenames.clear()
                continue
            for name in filenames:
                path = dirpath_path / name
                relative = path.relative_to(root)
                disk_files[(str(root), str(relative))] = path

    for key, row in manifest_rows.items():
        if key not in disk_files:
            errors.append(f"Missing on disk: {key[0]}/{key[1]}")
            continue
        path = disk_files[key]
        h = sha256_of(path)
        sz = path.stat().st_size
        if h != row["sha256"]:
            errors.append(f"Hash mismatch {key[0]}/{key[1]}: manifest {row['sha256'][:16]}... vs disk {h[:16]}...")
        if sz != int(row["bytes"]):
            errors.append(f"Size mismatch {key[0]}/{key[1]}: manifest {row['bytes']} vs disk {sz}")

    for key in disk_files:
        if key not in manifest_rows:
            errors.append(f"Extra file on disk not in manifest: {key[0]}/{key[1]}")

    return errors


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
    """Build the pinned manifest for both local provenance roots, or validate existing."""
    import argparse

    parser = argparse.ArgumentParser(description="Build or validate the COSMOS-Web v1.1 data manifest.")
    parser.add_argument("--verify", action="store_true", help="Validate existing manifest without rewriting.")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG_PATH.read_text())
    data_root = Path(config["data_root"])
    specz_root = Path(config["specz"]["compilation_root"])
    unique_fits = Path(config["specz"]["unique_fits"])

    roots_spec = [(data_root, False), (specz_root, True)]

    if args.verify:
        errors = validate_manifest(CSV_PATH, roots_spec)
        if errors:
            print("Manifest validation FAILED:")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)
        print("Manifest validation PASSED: all rows match live filesystem.")
        sys.exit(0)

    rows = manifest_root(data_root, git_checkout=False)
    specz_rows = manifest_root(specz_root, git_checkout=True)
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
