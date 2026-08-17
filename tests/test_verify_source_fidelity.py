#!/usr/bin/env python3
"""
Script Name  : test_verify_source_fidelity.py
Description  : Test Gate 3.5 immutable-input and FITS fidelity contracts
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises the reusable Gate 3.5 verifier with isolated manifests and NumPy
arrays. Each mutation changes one source contract so the named diagnostic or
mismatch class proves that the live verifier would halt before extraction.

Usage
-----
    pytest tests/test_verify_source_fidelity.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import hashlib
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "verify_source_fidelity.py"
MANIFEST_HEADER = ["root", "relative_path", "sha256", "bytes", "mtime_utc"]
FIXED_TIME = 1_700_000_000

# =============================================================================
# Helpers
# =============================================================================


def _module():
    """Load the production module only when a test executes."""
    assert MODULE_PATH.exists(), "Gate 3.5 verifier module is missing"
    spec = importlib.util.spec_from_file_location("verify_source_fidelity", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _row(root: Path, relative_path: str) -> list[str]:
    """Build one independently derived manifest row."""
    path = root / relative_path
    stat = path.stat()
    return [
        str(root),
        relative_path,
        hashlib.sha256(path.read_bytes()).hexdigest(),
        str(stat.st_size),
        "2023-11-14T22:13:20+00:00",
    ]


def _manifest_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create two roots and an exact three-row manifest."""
    root_a = tmp_path / "catalog"
    root_b = tmp_path / "specz"
    root_a.mkdir()
    root_b.mkdir()
    (root_a / "master.fits").write_bytes(b"master-bytes")
    (root_a / "standalone.fits").write_bytes(b"standalone-bytes")
    (root_b / "unique.fits").write_bytes(b"specz-bytes")
    for path in (
        root_a / "master.fits",
        root_a / "standalone.fits",
        root_b / "unique.fits",
    ):
        os.utime(path, (FIXED_TIME, FIXED_TIME))
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(MANIFEST_HEADER)
        writer.writerows(
            [
                _row(root_a, "master.fits"),
                _row(root_a, "standalone.fits"),
                _row(root_b, "unique.fits"),
            ]
        )
    return root_a, root_b, manifest


def _contract(tmp_path: Path):
    """Return the production parser's passing synthetic contract."""
    root_a, root_b, manifest = _manifest_fixture(tmp_path)
    module = _module()
    contract = module.parse_manifest_contract(
        manifest,
        {str(root_a): 2, str(root_b): 1},
    )
    return module, root_a, root_b, manifest, contract


def _sed_pin_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Create a two-row CRLF SED listing and its exact aggregate sidecar."""
    listing = tmp_path / "full.csv"
    header = b"root,relative_path,sha256,bytes,mtime_utc\r\n"
    sed_b = b"/root,cigale-seds/P2/b.fits," + b"b" * 64 + b",7,t\r\n"
    other = b"/root,master.fits," + b"c" * 64 + b",11,t\r\n"
    sed_a = b"/root,cigale-seds/P1/a.fits," + b"a" * 64 + b",5,t\r\n"
    listing.write_bytes(header + sed_b + other + sed_a)
    row_block = b"".join(sorted([sed_a, sed_b]))
    sidecar = tmp_path / "sed-pin.csv"
    with sidecar.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "subtree",
                "root",
                "file_count",
                "total_bytes",
                "rows_sha256",
                "full_listing_path",
                "full_listing_sha256",
            ]
        )
        writer.writerow(
            [
                "cigale-seds",
                "/root",
                "2",
                "12",
                hashlib.sha256(row_block).hexdigest(),
                str(listing),
                hashlib.sha256(listing.read_bytes()).hexdigest(),
            ]
        )
    return listing, sidecar


# =============================================================================
# Manifest and consumed-input mutations
# =============================================================================


def test_manifest_contract_accepts_exact_header_counts_and_boundaries(tmp_path):
    module, root_a, root_b, _manifest, contract = _contract(tmp_path)
    assert contract.header == tuple(MANIFEST_HEADER)
    assert contract.row_count == 3
    assert contract.root_counts == {str(root_a): 2, str(root_b): 1}
    assert len(contract.entries) == 3
    assert module is not None


@pytest.mark.parametrize(
    ("mutation", "diagnostic"),
    [
        ("header", "Manifest header mismatch"),
        ("missing", "Manifest row-count boundary mismatch"),
        ("duplicate", "Duplicate manifest key"),
        ("extra_root", "Undeclared manifest root"),
        ("git", "Git-internal manifest row"),
        ("sed", "Out-of-boundary manifest row"),
    ],
)
def test_manifest_mutations_fail_named_contract(tmp_path, mutation, diagnostic):
    root_a, root_b, manifest = _manifest_fixture(tmp_path)
    rows = list(csv.reader(manifest.open(newline="")))
    if mutation == "header":
        rows[0][2] = "digest"
    elif mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows.append(rows[1])
    elif mutation == "extra_root":
        rows[1][0] = str(tmp_path / "undeclared")
    elif mutation == "git":
        rows[1][1] = ".git/config"
    elif mutation == "sed":
        rows[1][1] = "cigale-seds/P1/0.0_SFH.fits"
    with manifest.open("w", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)

    with pytest.raises(ValueError, match=diagnostic):
        _module().parse_manifest_contract(
            manifest,
            {str(root_a): 2, str(root_b): 1},
        )


def test_consumed_input_absent_from_manifest_halts(tmp_path):
    module, root_a, _root_b, _manifest, contract = _contract(tmp_path)
    absent = root_a / "future-extraction.fits"
    absent.write_bytes(b"present-but-unmanifested")

    with pytest.raises(ValueError, match="Consumed input absent from manifest"):
        module.pin_manifest_input("future_master_extraction", absent, contract)


@pytest.mark.parametrize(
    ("field_index", "replacement", "diagnostic"),
    [
        (2, "0" * 64, "SHA-256 mismatch"),
        (3, "999", "size mismatch"),
    ],
)
def test_manifest_declared_and_observed_mismatch_halts(
    tmp_path, field_index, replacement, diagnostic
):
    root_a, root_b, manifest = _manifest_fixture(tmp_path)
    rows = list(csv.reader(manifest.open(newline="")))
    rows[1][field_index] = replacement
    with manifest.open("w", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    module = _module()
    contract = module.parse_manifest_contract(
        manifest,
        {str(root_a): 2, str(root_b): 1},
    )

    with pytest.raises(ValueError, match=diagnostic) as error:
        module.pin_manifest_input("master", root_a / "master.fits", contract)
    message = str(error.value)
    assert "declared" in message and "observed" in message


def test_consumed_input_evidence_keeps_declared_and_observed_values(tmp_path):
    module, root_a, _root_b, _manifest, contract = _contract(tmp_path)
    evidence = module.pin_manifest_input("master", root_a / "master.fits", contract)
    assert evidence.declared_bytes == len(b"master-bytes")
    assert evidence.observed_bytes == len(b"master-bytes")
    assert evidence.declared_sha256 == hashlib.sha256(b"master-bytes").hexdigest()
    assert evidence.observed_sha256 == hashlib.sha256(b"master-bytes").hexdigest()
    assert evidence.boundary == "manifest"


def test_sed_aggregate_reproduces_crlf_row_block_without_reading_sed_files(tmp_path):
    _listing, sidecar = _sed_pin_fixture(tmp_path)
    expected_rows = list(csv.DictReader(sidecar.open(newline="")))[0]["rows_sha256"]

    evidence = _module().reproduce_sed_aggregate(sidecar)
    assert evidence.file_count == 2
    assert evidence.total_bytes == 12
    assert evidence.rows_sha256 == expected_rows


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("subtree", "other-seds", "SED pin subtree mismatch"),
        ("root", "/wrong-root", "SED pin root mismatch"),
    ],
)
def test_sed_sidecar_boundary_metadata_mutation_halts(
    tmp_path, field, value, diagnostic
):
    _listing, sidecar = _sed_pin_fixture(tmp_path)
    rows = list(csv.DictReader(sidecar.open(newline="")))
    rows[0][field] = value
    with sidecar.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match=diagnostic):
        _module().reproduce_sed_aggregate(sidecar)


def test_consumed_manifest_input_enumeration_is_exact_and_complete():
    module = _module()
    config = {
        "catalogs": {
            "master_catalog": "/data/master.fits",
            **{
                config_key: f"/data/{target}.fits"
                for config_key, target, _extname in module.MASTER_COMPARISONS
            },
        },
        "supplementary": {
            "lss_overdensity": "/data/lss.fits",
            "group_catalog_groups": "/data/groups.txt",
            "group_catalog_memberships": "/data/memberships.txt",
        },
        "specz": {"unique_fits": "/specz/unique.fits"},
        "semantic_sources": {
            "lss_readme": "/data/lss-readme.txt",
            "specz_root_readme": "/specz/README.md",
            "specz_schema_readme": "/specz/schema/README.md",
            "master_descriptions": "/data/descriptions.txt",
        },
    }
    inputs = module._consumed_manifest_inputs(config)
    assert set(inputs) == {
        "future_master_extraction",
        "hatamnia_lss_catalog",
        "hatamnia_lss_readme",
        "toni_groups",
        "toni_memberships",
        "specz_unique",
        "specz_root_readme",
        "specz_schema_readme",
        "master_descriptions",
        "standalone_photometry_primary",
        "standalone_lephare",
        "standalone_photometry_aper",
        "standalone_cigale",
        "standalone_ml_morpho",
        "standalone_bulge_disk",
        "standalone_galight_morph",
    }
    assert len(inputs) == 16
    assert len({str(path) for path in inputs.values()}) == 16


# =============================================================================
# Shared sample, structure, values, and identifier mutations
# =============================================================================


def test_shared_sample_is_seeded_sorted_distinct_and_exact_size():
    module = _module()
    first = module.generate_shared_sample(10_000, 5_000, 20_260_817)
    second = module.generate_shared_sample(10_000, 5_000, 20_260_817)
    assert np.array_equal(first, second)
    assert len(first) == 5_000
    assert len(np.unique(first)) == 5_000
    assert np.all(first[:-1] < first[1:])
    assert first[0] >= 0 and first[-1] < 10_000


def test_shared_sample_mutation_rejects_wrong_size_or_seed_sequence():
    module = _module()
    sample = module.generate_shared_sample(10_000, 5_000, 20_260_817)
    with pytest.raises(ValueError, match="Shared sample size mismatch"):
        module.validate_shared_sample(sample[:-1], 10_000, 5_000, 20_260_817)
    mutated = sample.copy()
    mutated[0] = sample[0] + 1
    mutated.sort()
    with pytest.raises(ValueError, match="Shared sample seed mismatch"):
        module.validate_shared_sample(mutated, 10_000, 5_000, 20_260_817)


@pytest.mark.parametrize(
    ("master_names", "master_types", "diagnostic"),
    [
        (("id", "flux_changed"), ("K", "D"), "column-name mismatch"),
        (("flux", "id"), ("D", "K"), "column-order mismatch"),
        (("id", "flux"), ("K", "E"), "column-type mismatch"),
    ],
)
def test_standalone_master_structure_drift_halts(
    master_names, master_types, diagnostic
):
    module = _module()
    standalone = module.TableStructure(4, ("id", "flux"), ("K", "D"))
    master = module.TableStructure(4, master_names, master_types)
    with pytest.raises(ValueError, match=diagnostic):
        module.verify_table_structure("PHOTOMETRY", standalone, master)


def test_sampled_scalar_mismatch_is_counted_exactly():
    counts = _module().compare_exact_arrays(
        np.array([1.0, 2.0, 3.0]),
        np.array([1.0, 9.0, 3.0]),
    )
    assert counts.scalar == 1
    assert counts.vector == 0
    assert counts.mask == 0
    assert counts.nan == 0


def test_sampled_vector_element_mismatch_is_counted_exactly():
    counts = _module().compare_exact_arrays(
        np.array([[1.0, 2.0], [3.0, 4.0]]),
        np.array([[1.0, 8.0], [3.0, 4.0]]),
    )
    assert counts.scalar == 0
    assert counts.vector == 1
    assert counts.mask == 0
    assert counts.nan == 0


def test_mask_position_mismatch_is_separate_from_values():
    standalone = np.ma.array([1.0, 2.0, 3.0], mask=[False, True, False])
    master = np.ma.array([1.0, 2.0, 3.0], mask=[True, False, False])
    counts = _module().compare_exact_arrays(standalone, master)
    assert counts.mask == 2
    assert counts.scalar == 0
    assert counts.nan == 0


def test_nan_position_mismatch_is_separate_from_values():
    standalone = np.array([1.0, np.nan, 3.0])
    master = np.array([np.nan, 2.0, 3.0])
    counts = _module().compare_exact_arrays(standalone, master)
    assert counts.nan == 2
    assert counts.scalar == 0
    assert counts.mask == 0


def test_differing_complete_primary_id_sequence_halts():
    module = _module()
    with pytest.raises(ValueError, match="Complete primary-ID sequence mismatch"):
        module.verify_primary_id_sequence(
            np.array([10, 11, 12], dtype=np.int64),
            np.array([10, 99, 12], dtype=np.int64),
        )


@pytest.mark.parametrize(
    ("names", "primary", "diagnostic"),
    [
        (("flux", "ra"), True, "missing native id"),
        (("flux", "ID"), False, "unexpected native id"),
    ],
)
def test_native_id_inventory_contract_halts(names, primary, diagnostic):
    with pytest.raises(ValueError, match=diagnostic):
        _module().verify_native_id_contract("table", names, primary=primary)


def test_source_row_and_injected_id_constructions_cover_complete_range():
    module = _module()
    primary_ids = np.array([41, 43, 47, 53], dtype=np.int64)
    source_rows = module.construct_source_rows(len(primary_ids))
    injected = module.construct_injected_ids(primary_ids, len(primary_ids))
    assert np.array_equal(source_rows, np.array([0, 1, 2, 3], dtype=np.int64))
    assert np.array_equal(injected, primary_ids)
    assert not np.shares_memory(injected, primary_ids)
