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

P2R-02d additions: one further mutation asserts that a `cigale-seds/` row
in the manifest fails with the out-of-boundary diagnostic, and one
production test recomputes the SED aggregate digest from the NVMe full
listing and compares it to the tracked sidecar. Together they keep the
exclusion honest in both directions: the subtree may not creep back into
the per-file pin, and the aggregate that replaced it must reproduce.
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
SED_DIGEST_CSV = REPO_ROOT / "docs" / "reference" / "data-manifest-v1.1-cigale-seds.csv"
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


def test_out_of_boundary_subtree_row_fails_with_subtree_diagnostic(tmp_path):
    """A cigale-seds/ row may not re-enter the per-file pin. The subtree is
    pinned by aggregate digest; a per-file row for it is a contract violation
    even when the file exists on disk."""

    def add_sed_row(root, csv_path):
        sed_dir = root / "cigale-seds" / "P1"
        sed_dir.mkdir(parents=True)
        sed = sed_dir / "0.0_SFH.fits"
        sed.write_bytes(b"sed-content")
        os.utime(sed, (FIXED_TIME, FIXED_TIME))
        lines = csv_path.read_text().splitlines(keepends=True)
        row = row_for(root, "cigale-seds/P1/0.0_SFH.fits")
        csv_path.write_text("".join(lines) + ",".join(row) + "\n")

    result = mutate(tmp_path, add_sed_row)
    assert result.returncode != 0
    assert "Out-of-boundary subtree path" in result.stdout


def test_excluded_subtree_on_disk_does_not_trip_path_set_equality(tmp_path):
    """The mirror of the test above: SED files present on disk and absent from
    the manifest are correct, not a finding. This is the assertion that would
    have caught the A3.1 verify failure as a boundary question rather than a
    missing-rows question."""

    def add_sed_file_only(root, _csv_path):
        sed_dir = root / "cigale-seds" / "P2"
        sed_dir.mkdir(parents=True)
        sed = sed_dir / "9.9_SFH.fits"
        sed.write_bytes(b"unmanifested-by-design")
        os.utime(sed, (FIXED_TIME, FIXED_TIME))

    result = mutate(tmp_path, add_sed_file_only)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout


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


def test_production_csv_equals_filtered_baseline():
    """The committed CSV must be byte-identical to the 0f3e31d baseline minus
    its 29 .git/** records, in original order and serialization. P2R-02C
    added 1,185,322 cigale-seds rows here; P2R-02D lifted them back out to an
    aggregate digest, so the tracked file is once again exactly the reviewed
    pin and carries no SED row at all."""
    assert PRODUCTION_CSV.read_bytes() == filtered_baseline_bytes()


def test_production_csv_structure():
    with open(PRODUCTION_CSV, newline="") as handle:
        rows = list(csv.reader(handle))
    header, data = rows[0], rows[1:]
    assert header == ["root", "relative_path", "sha256", "bytes", "mtime_utc"]
    root1 = [r for r in data if r[0] == "/mnt/nvme01/cosmos-web-dr1-catalog"]
    root2 = [r for r in data if r[0] == "/opt/agents/repos/reference-files/speczcompilation"]
    assert len(root1) == 103
    assert len(root2) == 52
    assert len(data) == 155
    assert all(not r[1].startswith("cigale-seds/") for r in data), (
        "cigale-seds rows belong in the aggregate digest, not the per-file pin"
    )
    assert all("/.git/" not in r[1] and not r[1].startswith(".git/") for r in data)
    keys = {r[0] + "\x00" + r[1] for r in data}
    assert len(keys) == len(data), "duplicate (root, relative_path) keys"


def test_sed_digest_sidecar_reproduces_from_full_listing():
    """Recompute the aggregate from the NVMe full listing and compare it to the
    tracked sidecar. This is what makes the digest a pin rather than an
    assertion: the per-file rows still exist and still hash to the recorded
    value."""
    with open(SED_DIGEST_CSV, newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1, "digest sidecar carries exactly one row"
    pin = rows[0]

    full = Path(pin["full_listing_path"])
    if not full.exists():
        pytest.skip(f"full listing not present at {full}")

    raw = full.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin["full_listing_sha256"], (
        "full listing on NVMe does not match its recorded SHA-256"
    )

    # Mirror `awk -F, 'NR>1 && $2 ~ /^cigale-seds\//' | LC_ALL=C sort | sha256sum`:
    # records keep their trailing CR, sort is bytewise, each line re-terminated \n.
    records = raw.split(b"\n")[1:]
    sed = [r for r in records if r.split(b",", 2)[1:2] and r.split(b",", 2)[1].startswith(b"cigale-seds/")]
    digest = hashlib.sha256(b"".join(r + b"\n" for r in sorted(sed))).hexdigest()

    assert len(sed) == int(pin["file_count"])
    assert sum(int(r.split(b",")[3]) for r in sed) == int(pin["total_bytes"])
    assert digest == pin["rows_sha256"]


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
