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


EXPECTED_HEADER = ["root", "relative_path", "sha256", "bytes", "mtime_utc"]


def validate_manifest(csv_path: Path, roots: list[tuple[Path, bool]]) -> list[str]:
    """
    Validate an existing manifest CSV against the live filesystem (read-only).

    Machine contract enforced, each with a condition-specific diagnostic:
    exact ordered five-field header; one row per (root, relative_path) key
    with duplicates rejected before any overwrite; zero .git/** relative
    paths; rows only under declared roots; complete path-set equality in
    both directions; and exact SHA-256, integer byte count, and normalized
    second-resolution UTC mtime agreement for every row.

    Returns a list of diagnostic strings. An empty list means valid.
    """
    errors: list[str] = []

    # Header: exact, ordered, nothing renamed/reordered/missing/extra.
    with csv_path.open("rb") as handle:
        first_line = handle.readline()
    header_text = first_line.decode("utf-8").rstrip("\r\n")
    if header_text.split(",") != EXPECTED_HEADER:
        errors.append(
            f"Header mismatch: expected exactly '{','.join(EXPECTED_HEADER)}', got '{header_text}'"
        )
        return errors

    # Rows: field count, git-internal paths, duplicate keys (before assignment).
    manifest_rows: dict[tuple[str, str], dict] = {}
    with csv_path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for lineno, fields in enumerate(reader, start=2):
            if not fields:
                continue
            if len(fields) != 5:
                errors.append(
                    f"Row {lineno}: expected 5 fields, got {len(fields)}"
                )
                continue
            root, rel, sha, bytes_str, mtime = fields
            if "/.git/" in rel or rel.startswith(".git/"):
                errors.append(f"Git-internal path in manifest: {root}/{rel}")
                continue
            key = (root, rel)
            if key in manifest_rows:
                errors.append(f"Duplicate key: {root}/{rel}")
                continue
            manifest_rows[key] = {
                "sha256": sha,
                "bytes": bytes_str,
                "mtime_utc": mtime,
            }

    # Declared roots: manifest rows may not name an undeclared root.
    declared_roots = {str(root) for root, _ in roots}
    for root, rel in manifest_rows:
        if root not in declared_roots:
            errors.append(f"Undeclared root in manifest: {root}")

    # Disk inventory (excluding .git machinery for git-checkout roots).
    disk_files: dict[tuple[str, str], Path] = {}
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

    # Field agreement: manifest -> disk.
    for key, row in sorted(manifest_rows.items()):
        if key not in disk_files:
            errors.append(f"Manifest row missing on disk: {key[0]}/{key[1]}")
            continue
        path = disk_files[key]
        stat = path.stat()
        try:
            declared_bytes = int(row["bytes"])
        except ValueError:
            errors.append(
                f"Non-integer byte count {key[0]}/{key[1]}: {row['bytes']!r}"
            )
            continue
        if stat.st_size != declared_bytes:
            errors.append(
                f"Size mismatch {key[0]}/{key[1]}: manifest {declared_bytes} vs disk {stat.st_size}"
            )
        disk_mtime = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat(timespec="seconds")
        if disk_mtime != row["mtime_utc"]:
            errors.append(
                f"Mtime mismatch {key[0]}/{key[1]}: manifest {row['mtime_utc']} vs disk {disk_mtime}"
            )
        disk_hash = sha256_of(path)
        if disk_hash != row["sha256"]:
            errors.append(
                f"Hash mismatch {key[0]}/{key[1]}: manifest {row['sha256']} vs disk {disk_hash}"
            )

    # Path-set equality: disk -> manifest.
    for key in sorted(disk_files):
        if key not in manifest_rows:
            errors.append(f"Disk file missing from manifest: {key[0]}/{key[1]}")

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
    parser.add_argument("--verify", action="store_true", help="Validate existing manifest without rewriting (read-only).")
    parser.add_argument("--csv", type=Path, default=None, help="Manifest CSV to verify (default: production path from config).")
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        default=None,
        metavar="PATH[:git]",
        help="Root to verify against (repeatable). Suffix ':git' marks a git checkout whose .git is excluded. Defaults to the two configured production roots.",
    )
    args = parser.parse_args()

    if args.verify:
        if args.csv is not None and args.root is not None:
            verify_csv = args.csv
            verify_roots: list[tuple[Path, bool]] = []
            for spec in args.root:
                if str(spec).endswith(":git"):
                    verify_roots.append((Path(str(spec)[:-len(":git")]), True))
                else:
                    verify_roots.append((Path(spec), False))
        elif args.csv is None and args.root is None:
            config = yaml.safe_load(CONFIG_PATH.read_text())
            verify_csv = CSV_PATH
            verify_roots = [
                (Path(config["data_root"]), False),
                (Path(config["specz"]["compilation_root"]), True),
            ]
        else:
            parser.error("--csv and --root must be used together when overriding the verification target.")
        errors = validate_manifest(verify_csv, verify_roots)
        if errors:
            print("Manifest validation FAILED:")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)
        print("Manifest validation PASSED: all rows match live filesystem.")
        sys.exit(0)

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
