"""
Tests for build_data_manifest.py.
Validates the manifest contract: header, keys, no git paths, full verification.
"""
import csv
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_csv_has_valid_header():
    """CSV must have exact ordered header."""
    csv_path = Path("docs/reference/data-manifest-v1.1.csv")
    with open(csv_path) as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["root", "relative_path", "sha256", "bytes", "mtime_utc"]


def test_csv_has_no_duplicate_keys():
    """(root, relative_path) must be unique."""
    csv_path = Path("docs/reference/data-manifest-v1.1.csv")
    keys = set()
    duplicates = set()
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["root"], row["relative_path"])
            if key in keys:
                duplicates.add(key)
            keys.add(key)
    assert len(duplicates) == 0, f"Duplicate keys: {duplicates}"


def test_csv_excludes_git_paths():
    """No path may contain /.git/ or start with .git/."""
    csv_path = Path("docs/reference/data-manifest-v1.1.csv")
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row["relative_path"]
            assert "/.git/" not in path, f"Git internal path: {row['root']}/{path}"
            assert not path.startswith(".git/"), f"Git internal path: {row['root']}/{path}"


def test_csv_row_counts_match_expected():
    """Exactly 103 root-1 rows and 52 root-2 worktree rows (155 total)."""
    csv_path = Path("docs/reference/data-manifest-v1.1.csv")
    root1_count = 0
    root2_count = 0
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["root"] == "/mnt/nvme01/cosmos-web-dr1-catalog":
                root1_count += 1
            elif row["root"] == "/opt/agents/repos/reference-files/speczcompilation":
                root2_count += 1
    assert root1_count == 103, f"Expected 103 root-1 rows, got {root1_count}"
    assert root2_count == 52, f"Expected 52 root-2 rows, got {root2_count}"


def test_csv_verify_passes():
    """The validator must succeed against the committed CSV."""
    result = subprocess.run(
        ["python", "src/inspection/build_data_manifest.py", "--verify"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Validator failed: {result.stderr}"


def test_csv_missing_header_fails():
    """Validator must reject headerless CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_csv = Path(tmpdir) / "bad.csv"
        with open(bad_csv, "w") as f:
            f.write("/root,path,hash,bytes,time\n")
        result = subprocess.run(
            ["python", "src/inspection/build_data_manifest.py", "--verify", str(bad_csv)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should reject wrong header"


def test_csv_reordered_header_fails():
    """Validator must reject header with reordered fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_csv = Path(tmpdir) / "bad.csv"
        with open(bad_csv, "w") as f:
            f.write("root,bytes,sha256,relative_path,mtime_utc\n")
        result = subprocess.run(
            ["python", "src/inspection/build_data_manifest.py", "--verify", str(bad_csv)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should reject reordered header"


def test_csv_git_config_row_fails():
    """Validator must reject a row with .git/config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_csv = Path(tmpdir) / "bad.csv"
        with open(bad_csv, "w") as f:
            f.write("root,relative_path,sha256,bytes,mtime_utc\n")
            f.write("/root,.git/config,abc123,100,2026-08-17T00:00:00+00:00\n")
        result = subprocess.run(
            ["python", "src/inspection/build_data_manifest.py", "--verify", str(bad_csv)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should reject .git/config"


def test_csv_omitted_worktree_file_fails():
    """Validator must reject manifest missing a worktree file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "root"
        root.mkdir()
        (root / "test.txt").write_text("content")
        bad_csv = Path(tmpdir) / "bad.csv"
        with open(bad_csv, "w") as f:
            f.write("root,relative_path,sha256,bytes,mtime_utc\n")
        result = subprocess.run(
            [
                "python",
                "src/inspection/build_data_manifest.py",
                "--verify",
                str(bad_csv),
                str(root),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should detect missing worktree file"


def test_csv_extra_disk_artifact_fails():
    """Validator must reject extra disk artifact not in manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "root"
        root.mkdir()
        (root / "extra.txt").write_text("extra content")
        bad_csv = Path(tmpdir) / "bad.csv"
        with open(bad_csv, "w") as f:
            f.write("root,relative_path,sha256,bytes,mtime_utc\n")
        result = subprocess.run(
            [
                "python",
                "src/inspection/build_data_manifest.py",
                "--verify",
                str(bad_csv),
                str(root),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should detect extra disk artifact"


def test_csv_hash_size_drift_fails():
    """Validator must reject changed hash or size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "root"
        root.mkdir()
        (root / "test.txt").write_text("different content")
        bad_csv = Path(tmpdir) / "bad.csv"
        with open(bad_csv, "w") as f:
            f.write("root,relative_path,sha256,bytes,mtime_utc\n")
            f.write(f"{root},test.txt,abc123,100,2026-08-17T00:00:00+00:00\n")
        result = subprocess.run(
            [
                "python",
                "src/inspection/build_data_manifest.py",
                "--verify",
                str(bad_csv),
                str(root),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should reject hash/size drift"