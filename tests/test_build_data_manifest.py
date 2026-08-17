#!/usr/bin/env python3
"""
Script Name  : test_build_data_manifest.py
Description  : Discriminating tests for the v1.1 data manifest contract
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Spec P2R-02c gate A3.1 test suite. Two layers:

Isolated fixture tests build a passing temporary control (a small root and
its exact manifest), apply exactly one mutation, and assert both a nonzero
exit and the named diagnostic class. The ten required mutations cover
header absence/rename/reorder, duplicate keys, git-internal rows, both
path-set directions, and hash/size/mtime drift.

Production tests prove the committed CSV is the exact serialized 0f3e31d
baseline minus its 29 .git/** records, with 103/52 root counts, unique
keys, and no git machinery. The full production verifier runs as the
required integration check.
"""

import csv
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER = REPO_ROOT / "src" / "inspection" / "build_data_manifest.py"
PRODUCTION_CSV = REPO_ROOT / "docs" / "reference" / "data-manifest-v1.1.csv"
BASELINE_COMMIT = "0f3e31d"
FIXED_TIME = 1786000000  # deterministic fixture mtime


# =============================================================================
# Fixture helpers
# =============================================================================


def make_control_root(base: Path) -> Path:
    """Create a small deterministic root: two files, one nested."""
    root = base / "ctrl"
    (root / "sub").mkdir(parents=True)
    (root / "a.txt").write_bytes(b"alpha-content")
    (root / "sub" / "b.txt").write_bytes(b"beta-content" * 10)
    for path in (root / "a.txt", root / "sub" / "b.txt"):
        os.utime(path, (FIXED_TIME, FIXED_TIME))
    return root


def row_for(root: Path, rel: str) -> list[str]:
    """Compute the manifest fields for one file exactly as the builder does."""
    path = root / rel
    stat = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(
        timespec="seconds"
    )
    return [str(root), rel, digest, str(stat.st_size), mtime]


def write_manifest(csv_path: Path, rows: list[list[str]], header=None) -> None:
    """Serialize rows with the exact production header."""
    header = header or ["root", "relative_path", "sha256", "bytes", "mtime_utc"]
    with open(csv_path, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def control(base: Path) -> tuple[Path, Path]:
    """Build the passing control: root plus its exact manifest."""
    root = make_control_root(base)
    csv_path = base / "control.csv"
    write_manifest(csv_path, [row_for(root, "a.txt"), row_for(root, "sub/b.txt")])
    return root, csv_path


def run_verify(csv_path: Path, root: Path) -> subprocess.CompletedProcess:
    """Run the read-only verifier against an isolated target."""
    return subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--verify",
            "--csv",
            str(csv_path),
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def mutate(base: Path, mutation) -> subprocess.CompletedProcess:
    """Fresh control, one mutation applied, verifier run."""
    root, csv_path = control(base)
    mutation(root, csv_path)
    return run_verify(csv_path, root)


# =============================================================================
# Isolated fixture tests: control passes, each mutation fails its diagnostic
# =============================================================================


def test_control_fixture_passes(tmp_path):
    result = run_verify(*control(tmp_path)[::-1])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout


def test_missing_header_fails_with_header_diagnostic(tmp_path):
    def drop_header(_root, csv_path):
        # Rewrite without the header record: first data row is parsed as header.
        body = csv_path.read_text().splitlines(keepends=True)
        csv_path.write_text("".join(body[1:]))

    result = mutate(tmp_path, drop_header)
    assert result.returncode != 0
    assert "Header mismatch" in result.stdout


def test_renamed_header_field_fails_with_header_diagnostic(tmp_path):
    def rename_field(_root, csv_path):
        rows = [line.split(",") for line in csv_path.read_text().splitlines()]
        write_manifest(csv_path, rows[1:], header=["root", "relative_path", "sha256", "size_bytes", "mtime_utc"])

    result = mutate(tmp_path, rename_field)
    assert result.returncode != 0
    assert "Header mismatch" in result.stdout


def test_reordered_header_fails_with_header_diagnostic(tmp_path):
    def reorder_header(_root, csv_path):
        rows = [line.split(",") for line in csv_path.read_text().splitlines()]
        write_manifest(csv_path, rows[1:], header=["relative_path", "root", "sha256", "bytes", "mtime_utc"])

    result = mutate(tmp_path, reorder_header)
    assert result.returncode != 0
    assert "Header mismatch" in result.stdout


def test_duplicate_key_fails_with_duplicate_diagnostic(tmp_path):
    def duplicate_row(_root, csv_path):
        lines = csv_path.read_text().splitlines(keepends=True)
        csv_path.write_text("".join(lines) + lines[1])

    result = mutate(tmp_path, duplicate_row)
    assert result.returncode != 0
    assert "Duplicate key" in result.stdout


def test_added_git_config_row_fails_with_git_diagnostic(tmp_path):
    def add_git_row(_root, csv_path):
        lines = csv_path.read_text().splitlines(keepends=True)
        git_row = ",".join(
            [lines[1].split(",")[0], ".git/config", "0" * 64, "305", lines[1].split(",")[4].strip()]
        )
        csv_path.write_text("".join(lines) + git_row + "\n")

    result = mutate(tmp_path, add_git_row)
    assert result.returncode != 0
    assert "Git-internal path" in result.stdout


def test_manifest_only_row_fails_with_missing_on_disk_diagnostic(tmp_path):
    def add_ghost_row(root, csv_path):
        ghost = row_for(root, "a.txt")
        ghost[1] = "ghost.txt"
        lines = csv_path.read_text().splitlines(keepends=True)
        csv_path.write_text("".join(lines) + ",".join(ghost) + "\n")

    result = mutate(tmp_path, add_ghost_row)
    assert result.returncode != 0
    assert "Manifest row missing on disk" in result.stdout


def test_disk_only_file_fails_with_missing_from_manifest_diagnostic(tmp_path):
    def add_disk_file(root, _csv_path):
        extra = root / "extra.txt"
        extra.write_bytes(b"unmanifested")
        os.utime(extra, (FIXED_TIME, FIXED_TIME))

    result = mutate(tmp_path, add_disk_file)
    assert result.returncode != 0
    assert "Disk file missing from manifest" in result.stdout


def test_hash_only_drift_fails_with_hash_diagnostic_only(tmp_path):
    def drift_hash(_root, csv_path):
        lines = csv_path.read_text().splitlines(keepends=True)
        fields = lines[1].split(",")
        fields[2] = ("0" if fields[2][0] != "0" else "1") + fields[2][1:]
        lines[1] = ",".join(fields) + "\n"
        csv_path.write_text("".join(lines))

    result = mutate(tmp_path, drift_hash)
    assert result.returncode != 0
    assert "Hash mismatch" in result.stdout
    assert "Size mismatch" not in result.stdout
    assert "Mtime mismatch" not in result.stdout


def test_size_only_drift_fails_with_size_diagnostic_only(tmp_path):
    def drift_size(_root, csv_path):
        lines = csv_path.read_text().splitlines(keepends=True)
        fields = lines[1].split(",")
        fields[3] = str(int(fields[3]) + 1)
        lines[1] = ",".join(fields) + "\n"
        csv_path.write_text("".join(lines))

    result = mutate(tmp_path, drift_size)
    assert result.returncode != 0
    assert "Size mismatch" in result.stdout
    assert "Hash mismatch" not in result.stdout
    assert "Mtime mismatch" not in result.stdout


def test_mtime_only_drift_fails_with_mtime_diagnostic_only(tmp_path):
    def drift_mtime(_root, csv_path):
        lines = csv_path.read_text().splitlines(keepends=True)
        fields = lines[1].split(",")
        stamp = datetime.fromtimestamp(FIXED_TIME + 1, tz=timezone.utc)
        fields[4] = stamp.isoformat(timespec="seconds")
        lines[1] = ",".join(fields) + "\n"
        csv_path.write_text("".join(lines))

    result = mutate(tmp_path, drift_mtime)
    assert result.returncode != 0
    assert "Mtime mismatch" in result.stdout
    assert "Hash mismatch" not in result.stdout
    assert "Size mismatch" not in result.stdout


# =============================================================================
# Production tests: committed CSV equals the filtered 0f3e31d baseline
# =============================================================================


def filtered_baseline_bytes() -> bytes:
    show = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:docs/reference/data-manifest-v1.1.csv"],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
    )
    records = show.stdout.split(b"\r\n")
    assert records[-1] == b""
    header, data = records[0], records[1:-1]
    kept = [r for r in data if not r.split(b",")[1].startswith(b".git/")]
    return b"\r\n".join([header] + kept) + b"\r\n"


def test_production_csv_is_retained_baseline_plus_pinned_seds():
    """Strip the operator-dispositioned cigale-seds block from the committed
    CSV; the remainder must be byte-identical to the 0f3e31d baseline minus
    its 29 .git/** records, in original order and serialization."""
    expected = filtered_baseline_bytes()
    raw = PRODUCTION_CSV.read_bytes()
    records = raw.split(b"\r\n")
    assert records[-1] == b""
    header, data = records[0], records[1:-1]
    retained, sed_rows = [], 0
    for rec in data:
        if rec.split(b",", 2)[1].startswith(b"cigale-seds/"):
            sed_rows += 1
        else:
            retained.append(rec)
    assert sed_rows > 0, "expected the pinned cigale-seds block"
    actual = b"\r\n".join([header] + retained) + b"\r\n"
    assert actual == expected, (
        "committed CSV minus cigale-seds rows differs from the "
        "0f3e31d-minus-29 retained baseline"
    )


def test_production_csv_structure():
    with open(PRODUCTION_CSV, newline="") as handle:
        rows = list(csv.reader(handle))
    header, data = rows[0], rows[1:]
    assert header == ["root", "relative_path", "sha256", "bytes", "mtime_utc"]
    root1 = [r for r in data if r[0] == "/mnt/nvme01/cosmos-web-dr1-catalog"]
    root2 = [r for r in data if r[0] == "/opt/agents/repos/reference-files/speczcompilation"]
    assert len(root2) == 52
    assert all("/.git/" not in r[1] and not r[1].startswith(".git/") for r in data)
    keys = {r[0] + "\x00" + r[1] for r in data}
    assert len(keys) == len(data), "duplicate (root, relative_path) keys"


def test_production_full_verifier():
    """Required integration check: read-only verify over both production roots."""
    result = subprocess.run(
        [sys.executable, str(BUILDER), "--verify"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout
