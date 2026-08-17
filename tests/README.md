# Manifest Validator Tests

Tests for `src/inspection/build_data_manifest.py` validate the manifest contract:

## Quick Tests (no filesystem access)
- `test_csv_has_valid_header`: CSV must have exact ordered header
- `test_csv_has_no_duplicate_keys`: (root, relative_path) must be unique
- `test_csv_excludes_git_paths`: No path may contain /.git/ or start with .git/
- `test_csv_row_counts_match_expected`: Exactly 103 root-1 + 52 root-2 rows

## Full Verification Tests (require filesystem access)
- `test_csv_verify_passes`: The validator must succeed against the committed CSV
- `test_csv_missing_header_fails`: Validator must reject headerless CSV
- `test_csv_reordered_header_fails`: Validator must reject header with reordered fields
- `test_csv_git_config_row_fails`: Validator must reject .git/config row
- `test_csv_omitted_worktree_file_fails`: Validator must detect missing worktree file
- `test_csv_extra_disk_artifact_fails`: Validator must detect extra disk artifact
- `test_csv_hash_size_drift_fails`: Validator must reject changed hash/size

## Running Tests

```bash
# Quick tests (run in ~0.1s)
pytest tests/test_build_data_manifest.py::test_csv_has_valid_header -v
pytest tests/test_build_data_manifest.py::test_csv_has_no_duplicate_keys -v
pytest tests/test_build_data_manifest.py::test_csv_excludes_git_paths -v
pytest tests/test_build_data_manifest.py::test_csv_row_counts_match_expected -v

# All tests (full verification takes several minutes to hash all files)
pytest tests/test_build_data_manifest.py -v

# Run the validator directly
python src/inspection/build_data_manifest.py --verify
```