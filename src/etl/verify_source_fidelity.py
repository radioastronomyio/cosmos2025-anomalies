#!/usr/bin/env python3
"""
Script Name  : verify_source_fidelity.py
Description  : Verify immutable inputs and standalone/master FITS fidelity
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Implements the read-only ETL v2 Gate 3.5 preflight. The verifier validates the
sealed two-root manifest before it reads any catalog for comparison, freshly
pins every consumed immutable input, reproduces the aggregate CIGALE-SED pin,
and compares all seven standalone tables to their master-catalog HDUs.

Usage
-----
    python src/etl/verify_source_fidelity.py

Examples
--------
    /usr/bin/time -v python src/etl/verify_source_fidelity.py
        Runs the complete live read-only Gate 3.5 verification and emits JSON.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from astropy.io import fits

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.inspection.build_data_manifest import (  # noqa: E402
    EXPECTED_HEADER,
    sha256_of,
    validate_manifest,
)

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
EXPECTED_MANIFEST_ROOT_COUNTS = (103, 52)
EXPECTED_MANIFEST_ROWS = 155
EXPECTED_LIVE_ROWS = 784_016
EXPECTED_NATIVE_FIELDS = 1_349
SHARED_SAMPLE_SIZE = 5_000
SHARED_SAMPLE_SEED = 20_260_817
YANG_REFERENCE = "Yang et al. 2026, arXiv:2606.14869v1"
YANG_ARXIV_ID = "arXiv:2606.14869v1"
YANG_BYTES = 5_310_696
YANG_SHA256 = "f4d369c1f3c093dc5990895ac7f95ceecead318339e9fe1b8b823fb51675f0bc"
ORDINAL_LIMITATION = (
    "The six keyless extensions cannot independently prove cross-HDU object "
    "identity. Their source_row and injected-ID alignment relies on the "
    "upstream catalog's cross-HDU ordinal contract."
)

MASTER_COMPARISONS = (
    ("photom_primary", "photometry_primary", "PHOTOMETRY HOTCOLD AND SE++"),
    ("lephare", "lephare", "LEPHARE"),
    ("photom_secondary", "photometry_aper", "SE++APER"),
    ("cigale", "cigale", "CIGALE"),
    ("ml_morph", "ml_morpho", "ML-MORPHO"),
    ("bulgedisk", "bulge_disk", "B+D"),
    ("galight_morph", "galight_morph", "GALIGHT-MORPHO"),
)

# =============================================================================
# Evidence types
# =============================================================================


@dataclass(frozen=True)
class ManifestEntry:
    """One declared immutable-source row."""

    root: str
    relative_path: str
    sha256: str
    bytes: int
    mtime_utc: str


@dataclass(frozen=True)
class ManifestContract:
    """Parsed manifest boundary and exact key inventory."""

    header: tuple[str, ...]
    row_count: int
    root_counts: dict[str, int]
    entries: dict[tuple[str, str], ManifestEntry]


@dataclass(frozen=True)
class InputEvidence:
    """Separate declared and freshly observed evidence for one input."""

    name: str
    path: str
    boundary: str
    root: str
    relative_path: str
    declared_bytes: int
    observed_bytes: int
    declared_sha256: str
    observed_sha256: str


@dataclass(frozen=True)
class BoundaryEvidence:
    """Fresh evidence for an authorized input outside the local manifest."""

    name: str
    path: str
    boundary: str
    reference: str
    declared_bytes: int | None
    observed_bytes: int
    declared_sha256: str
    observed_sha256: str


@dataclass(frozen=True)
class SedAggregateEvidence:
    """Declared and reproduced CIGALE-SED aggregate pin."""

    subtree: str
    root: str
    full_listing_path: str
    declared_full_listing_sha256: str
    observed_full_listing_sha256: str
    declared_file_count: int
    file_count: int
    declared_total_bytes: int
    total_bytes: int
    declared_rows_sha256: str
    rows_sha256: str


@dataclass(frozen=True)
class TableStructure:
    """Row count plus exact ordered FITS name/TFORM inventory."""

    row_count: int
    names: tuple[str, ...]
    formats: tuple[str, ...]


@dataclass
class MismatchCounts:
    """Independent exact mismatch-position totals."""

    scalar: int = 0
    vector: int = 0
    mask: int = 0
    nan: int = 0

    def add(self, other: "MismatchCounts") -> None:
        """Add another column's mismatch positions in place."""
        self.scalar += other.scalar
        self.vector += other.vector
        self.mask += other.mask
        self.nan += other.nan

    def total(self) -> int:
        """Return the total mismatch positions across independent classes."""
        return self.scalar + self.vector + self.mask + self.nan


# =============================================================================
# Manifest and hash verification
# =============================================================================


def parse_manifest_contract(
    manifest_path: Path,
    expected_root_counts: dict[str, int],
) -> ManifestContract:
    """Parse and enforce the exact manifest header, roots, counts, and boundary."""
    with manifest_path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != EXPECTED_HEADER:
            raise ValueError(
                "Manifest header mismatch: expected "
                f"{EXPECTED_HEADER}, observed {header}"
            )
        entries: dict[tuple[str, str], ManifestEntry] = {}
        counts: Counter[str] = Counter()
        for line_number, row in enumerate(reader, start=2):
            if len(row) != 5:
                raise ValueError(
                    f"Malformed manifest row {line_number}: expected 5 fields, "
                    f"observed {len(row)}"
                )
            root, relative_path, sha256, byte_text, mtime_utc = row
            if root not in expected_root_counts:
                raise ValueError(f"Undeclared manifest root: {root}")
            parts = Path(relative_path).parts
            if relative_path.startswith(".git/") or "/.git/" in relative_path:
                raise ValueError(f"Git-internal manifest row: {root}/{relative_path}")
            if parts and parts[0] == "cigale-seds":
                raise ValueError(
                    f"Out-of-boundary manifest row: {root}/{relative_path}"
                )
            key = (root, relative_path)
            if key in entries:
                raise ValueError(f"Duplicate manifest key: {root}/{relative_path}")
            if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
                raise ValueError(
                    f"Malformed manifest SHA-256 at row {line_number}: {sha256!r}"
                )
            try:
                byte_count = int(byte_text)
            except ValueError as exc:
                raise ValueError(
                    f"Malformed manifest byte count at row {line_number}: {byte_text!r}"
                ) from exc
            entries[key] = ManifestEntry(
                root=root,
                relative_path=relative_path,
                sha256=sha256,
                bytes=byte_count,
                mtime_utc=mtime_utc,
            )
            counts[root] += 1

    expected_rows = sum(expected_root_counts.values())
    if len(entries) != expected_rows:
        raise ValueError(
            "Manifest row-count boundary mismatch: "
            f"expected {expected_rows}, observed {len(entries)}"
        )
    observed_counts = dict(counts)
    if observed_counts != expected_root_counts:
        raise ValueError(
            "Manifest root-count boundary mismatch: "
            f"expected {expected_root_counts}, observed {observed_counts}"
        )
    return ManifestContract(
        header=tuple(header),
        row_count=len(entries),
        root_counts=observed_counts,
        entries=entries,
    )


def pin_manifest_input(
    name: str,
    path: Path,
    contract: ManifestContract,
) -> InputEvidence:
    """Resolve one exact manifest row and freshly verify its size and SHA-256."""
    candidates: list[tuple[str, str]] = []
    for root_text in contract.root_counts:
        root = Path(root_text)
        try:
            relative_path = path.relative_to(root)
        except ValueError:
            continue
        candidates.append((root_text, str(relative_path)))
    if len(candidates) != 1:
        raise ValueError(
            f"Consumed input is outside or ambiguous across manifest roots: "
            f"{name} {path}"
        )
    key = candidates[0]
    declared = contract.entries.get(key)
    if declared is None:
        raise ValueError(f"Consumed input absent from manifest: {name} {path}")
    if not path.is_file():
        raise ValueError(f"Consumed input missing on disk: {name} {path}")

    observed_bytes = path.stat().st_size
    observed_sha256 = sha256_of(path)
    evidence = InputEvidence(
        name=name,
        path=str(path),
        boundary="manifest",
        root=declared.root,
        relative_path=declared.relative_path,
        declared_bytes=declared.bytes,
        observed_bytes=observed_bytes,
        declared_sha256=declared.sha256,
        observed_sha256=observed_sha256,
    )
    if declared.bytes != observed_bytes:
        raise ValueError(
            f"Consumed input size mismatch for {name} {path}: "
            f"declared {declared.bytes}, observed {observed_bytes}; "
            f"declared SHA-256 {declared.sha256}, observed SHA-256 "
            f"{observed_sha256}"
        )
    if declared.sha256 != observed_sha256:
        raise ValueError(
            f"Consumed input SHA-256 mismatch for {name} {path}: "
            f"declared {declared.sha256}, observed {observed_sha256}; "
            f"declared bytes {declared.bytes}, observed bytes {observed_bytes}"
        )
    return evidence


def pin_boundary_input(
    name: str,
    path: Path,
    *,
    boundary: str,
    reference: str,
    declared_sha256: str,
    declared_bytes: int | None = None,
) -> BoundaryEvidence:
    """Freshly verify one authorized non-manifest artifact."""
    if not path.is_file():
        raise ValueError(f"Boundary input missing on disk: {name} {path}")
    observed_bytes = path.stat().st_size
    observed_sha256 = sha256_of(path)
    if declared_bytes is not None and observed_bytes != declared_bytes:
        raise ValueError(
            f"Boundary input size mismatch for {name}: declared "
            f"{declared_bytes}, observed {observed_bytes}"
        )
    if observed_sha256 != declared_sha256:
        raise ValueError(
            f"Boundary input SHA-256 mismatch for {name}: declared "
            f"{declared_sha256}, observed {observed_sha256}"
        )
    return BoundaryEvidence(
        name=name,
        path=str(path),
        boundary=boundary,
        reference=reference,
        declared_bytes=declared_bytes,
        observed_bytes=observed_bytes,
        declared_sha256=declared_sha256,
        observed_sha256=observed_sha256,
    )


def reproduce_sed_aggregate(sidecar_path: Path) -> SedAggregateEvidence:
    """Reproduce the CRLF-preserving SED row-block pin from its full listing."""
    expected_header = [
        "subtree",
        "root",
        "file_count",
        "total_bytes",
        "rows_sha256",
        "full_listing_path",
        "full_listing_sha256",
    ]
    with sidecar_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_header:
            raise ValueError(
                f"SED pin header mismatch: expected {expected_header}, "
                f"observed {reader.fieldnames}"
            )
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError(
            f"SED pin row-count mismatch: expected 1, observed {len(rows)}"
        )
    pin = rows[0]
    if pin["subtree"] != "cigale-seds":
        raise ValueError(
            "SED pin subtree mismatch: expected 'cigale-seds', "
            f"observed {pin['subtree']!r}"
        )
    full_listing = Path(pin["full_listing_path"])
    raw = full_listing.read_bytes()
    observed_full_sha = hashlib.sha256(raw).hexdigest()
    if observed_full_sha != pin["full_listing_sha256"]:
        raise ValueError(
            "SED full-listing SHA-256 mismatch: declared "
            f"{pin['full_listing_sha256']}, observed {observed_full_sha}"
        )

    records = raw.split(b"\n")[1:]
    sed_records = []
    for record in records:
        fields = record.split(b",", 4)
        if len(fields) == 5 and fields[1].startswith(b"cigale-seds/"):
            sed_records.append(record)
    observed_rows_sha = hashlib.sha256(
        b"".join(record + b"\n" for record in sorted(sed_records))
    ).hexdigest()
    observed_roots = {
        record.split(b",", 1)[0].decode("utf-8") for record in sed_records
    }
    if observed_roots != {pin["root"]}:
        raise ValueError(
            f"SED pin root mismatch: declared {pin['root']!r}, "
            f"observed {sorted(observed_roots)}"
        )
    observed_bytes = sum(int(record.split(b",", 4)[3]) for record in sed_records)
    observed_count = len(sed_records)
    declared_count = int(pin["file_count"])
    declared_bytes = int(pin["total_bytes"])
    if observed_count != declared_count:
        raise ValueError(
            f"SED file-count mismatch: declared {declared_count}, "
            f"observed {observed_count}"
        )
    if observed_bytes != declared_bytes:
        raise ValueError(
            f"SED total-bytes mismatch: declared {declared_bytes}, "
            f"observed {observed_bytes}"
        )
    if observed_rows_sha != pin["rows_sha256"]:
        raise ValueError(
            f"SED row-block SHA-256 mismatch: declared {pin['rows_sha256']}, "
            f"observed {observed_rows_sha}"
        )
    return SedAggregateEvidence(
        subtree=pin["subtree"],
        root=pin["root"],
        full_listing_path=str(full_listing),
        declared_full_listing_sha256=pin["full_listing_sha256"],
        observed_full_listing_sha256=observed_full_sha,
        declared_file_count=declared_count,
        file_count=observed_count,
        declared_total_bytes=declared_bytes,
        total_bytes=observed_bytes,
        declared_rows_sha256=pin["rows_sha256"],
        rows_sha256=observed_rows_sha,
    )


# =============================================================================
# Sample, structure, and value equality
# =============================================================================


def generate_shared_sample(population: int, size: int, seed: int) -> np.ndarray:
    """Return the seeded, sorted, distinct zero-based ordinal sample."""
    if population < 0 or size < 0:
        raise ValueError("Sample population and size must be non-negative")
    actual_size = min(population, size)
    generator = np.random.default_rng(seed)
    sample = generator.choice(population, size=actual_size, replace=False)
    sample.sort()
    return sample.astype(np.int64, copy=False)


def validate_shared_sample(
    sample: np.ndarray,
    population: int,
    size: int,
    seed: int,
) -> None:
    """Prove size, range, uniqueness, sort order, and recorded-seed sequence."""
    array = np.asarray(sample)
    expected_size = min(population, size)
    if array.ndim != 1 or len(array) != expected_size:
        raise ValueError(
            f"Shared sample size mismatch: expected {expected_size}, "
            f"observed shape {array.shape}"
        )
    if len(np.unique(array)) != expected_size:
        raise ValueError("Shared sample contains duplicate ordinals")
    if expected_size and (int(array[0]) < 0 or int(array[-1]) >= population):
        raise ValueError("Shared sample ordinal outside eligible population")
    if expected_size > 1 and not bool(np.all(array[:-1] < array[1:])):
        raise ValueError("Shared sample is not strictly sorted")
    expected = generate_shared_sample(population, size, seed)
    if not np.array_equal(array, expected):
        raise ValueError("Shared sample seed mismatch")


def verify_table_structure(
    label: str,
    standalone: TableStructure,
    master: TableStructure,
) -> None:
    """Require exact row count, column count, ordered names, and TFORMs."""
    if standalone.row_count != master.row_count:
        raise ValueError(
            f"{label} row-count mismatch: standalone {standalone.row_count}, "
            f"master {master.row_count}"
        )
    if len(standalone.names) != len(master.names):
        raise ValueError(
            f"{label} column-count mismatch: standalone {len(standalone.names)}, "
            f"master {len(master.names)}"
        )
    if standalone.names != master.names:
        if Counter(standalone.names) == Counter(master.names):
            diagnostic = "column-order mismatch"
        else:
            diagnostic = "column-name mismatch"
        raise ValueError(
            f"{label} {diagnostic}: standalone {standalone.names}, "
            f"master {master.names}"
        )
    if standalone.formats != master.formats:
        raise ValueError(
            f"{label} column-type mismatch: standalone {standalone.formats}, "
            f"master {master.formats}"
        )


def _nan_positions(array: np.ndarray) -> np.ndarray:
    """Return NaN positions for float/complex arrays and false elsewhere."""
    if array.dtype.kind in {"f", "c"}:
        return np.isnan(array)
    return np.zeros(array.shape, dtype=bool)


def compare_exact_arrays(
    standalone: np.ndarray,
    master: np.ndarray,
) -> MismatchCounts:
    """Count exact scalar/vector, FITS-mask, and NaN-position differences."""
    left = np.ma.asarray(standalone)
    right = np.ma.asarray(master)
    left_data = np.asarray(left.data)
    right_data = np.asarray(right.data)
    if left_data.shape != right_data.shape:
        raise ValueError(
            f"Compared array shape mismatch: standalone {left_data.shape}, "
            f"master {right_data.shape}"
        )
    left_mask = np.ma.getmaskarray(left)
    right_mask = np.ma.getmaskarray(right)
    mask_difference = np.logical_xor(left_mask, right_mask)
    common_unmasked = ~(left_mask | right_mask)
    left_nan = _nan_positions(left_data) & common_unmasked
    right_nan = _nan_positions(right_data) & common_unmasked
    nan_difference = np.logical_xor(left_nan, right_nan)
    comparable = common_unmasked & ~(left_nan | right_nan)
    value_difference = np.not_equal(left_data, right_data) & comparable
    value_count = int(np.count_nonzero(value_difference))
    vector = left_data.ndim > 1
    return MismatchCounts(
        scalar=0 if vector else value_count,
        vector=value_count if vector else 0,
        mask=int(np.count_nonzero(mask_difference)),
        nan=int(np.count_nonzero(nan_difference)),
    )


def verify_primary_id_sequence(
    standalone_ids: np.ndarray,
    master_ids: np.ndarray,
) -> None:
    """Require exact equality of every native primary-photometry ID."""
    counts = compare_exact_arrays(standalone_ids, master_ids)
    if counts.total():
        raise ValueError(f"Complete primary-ID sequence mismatch: {asdict(counts)}")


def verify_native_id_contract(
    label: str,
    names: tuple[str, ...],
    *,
    primary: bool,
) -> None:
    """Require one native ID in primary and none in the six keyless tables."""
    id_count = sum(name.lower() == "id" for name in names)
    if primary and id_count != 1:
        raise ValueError(f"{label} missing native id: observed {id_count}")
    if not primary and id_count != 0:
        raise ValueError(f"{label} unexpected native id: observed {id_count}")


def construct_source_rows(row_count: int) -> np.ndarray:
    """Construct the complete zero-based source-row ordinal."""
    if row_count < 0:
        raise ValueError("Source-row population must be non-negative")
    return np.arange(row_count, dtype=np.int64)


def construct_injected_ids(primary_ids: np.ndarray, row_count: int) -> np.ndarray:
    """Copy primary native IDs for one keyless extension's complete range."""
    ids = np.asarray(primary_ids)
    if ids.ndim != 1 or len(ids) != row_count:
        raise ValueError(
            f"Injected-ID population mismatch: expected {row_count}, "
            f"observed shape {ids.shape}"
        )
    return np.array(ids, copy=True)


# =============================================================================
# Live orchestration
# =============================================================================


def _dictionary_recorded_hash(
    dictionary_path: Path,
    source_value: str,
) -> str:
    """Return the one SHA-256 recorded for a semantic evidence source."""
    source_fields = (
        ("description_source", "description_source_sha256"),
        ("unit_source", "unit_source_sha256"),
        ("semantic_note_source", "semantic_note_source_sha256"),
    )
    hashes: set[str] = set()
    with dictionary_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            for source_field, hash_field in source_fields:
                if row[source_field] == source_value and row[hash_field]:
                    hashes.add(row[hash_field])
    if len(hashes) != 1:
        raise ValueError(
            f"Dictionary-recorded SHA-256 set mismatch for {source_value}: "
            f"{sorted(hashes)}"
        )
    return next(iter(hashes))


def _consumed_manifest_inputs(config: dict[str, Any]) -> dict[str, Path]:
    """Enumerate every unique manifest-bounded artifact consumed by ETL v2."""
    inputs: dict[str, Path] = {
        "future_master_extraction": Path(config["catalogs"]["master_catalog"]),
        "hatamnia_lss_catalog": Path(config["supplementary"]["lss_overdensity"]),
        "hatamnia_lss_readme": Path(config["semantic_sources"]["lss_readme"]),
        "toni_groups": Path(config["supplementary"]["group_catalog_groups"]),
        "toni_memberships": Path(config["supplementary"]["group_catalog_memberships"]),
        "specz_unique": Path(config["specz"]["unique_fits"]),
        "specz_root_readme": Path(config["semantic_sources"]["specz_root_readme"]),
        "specz_schema_readme": Path(config["semantic_sources"]["specz_schema_readme"]),
        "master_descriptions": Path(config["semantic_sources"]["master_descriptions"]),
    }
    for config_key, target_table, _extname in MASTER_COMPARISONS:
        inputs[f"standalone_{target_table}"] = Path(config["catalogs"][config_key])
    unique_paths = {str(path) for path in inputs.values()}
    if len(unique_paths) != len(inputs):
        raise ValueError("Consumed manifest input enumeration contains duplicate paths")
    return inputs


def _hdu_structure(hdu: fits.BinTableHDU) -> TableStructure:
    """Extract the live row/name/TFORM structure without value conversion."""
    return TableStructure(
        row_count=int(len(hdu.data)),
        names=tuple(str(column.name) for column in hdu.columns),
        formats=tuple(str(column.format) for column in hdu.columns),
    )


def _single_table(hdul: fits.HDUList) -> fits.BinTableHDU:
    """Return the only table HDU in a standalone FITS product."""
    tables = [hdu for hdu in hdul if getattr(hdu, "columns", None) is not None]
    if len(tables) != 1:
        raise ValueError(
            f"Standalone FITS table-count mismatch: observed {len(tables)}"
        )
    return tables[0]


def _column_values(
    hdu: fits.BinTableHDU,
    name: str,
    ordinals: np.ndarray | None,
) -> np.ndarray:
    """Read native values and apply only the FITS-declared TNULL mask."""
    values = hdu.data[name]
    if ordinals is not None:
        values = values[ordinals]
    column = hdu.columns[name]
    if column.null is None:
        return np.asarray(values)
    return np.ma.array(values, mask=np.equal(values, column.null), copy=False)


def _compare_live_tables(config: dict[str, Any]) -> dict[str, Any]:
    """Compare all seven standalone tables against one open master catalog."""
    master_path = Path(config["catalogs"]["master_catalog"])
    table_evidence: list[dict[str, Any]] = []
    total_mismatches = MismatchCounts()
    total_fields = 0
    scalar_fields = 0
    vector_fields = 0
    primary_ids: np.ndarray | None = None
    sample: np.ndarray | None = None
    population: int | None = None
    primary_id_count = 0
    keyless_absences = 0
    injected_checks = 0

    with fits.open(master_path, memmap=True, lazy_load_hdus=True) as master_hdul:
        for config_key, target_table, extname in MASTER_COMPARISONS:
            standalone_path = Path(config["catalogs"][config_key])
            with fits.open(
                standalone_path, memmap=True, lazy_load_hdus=True
            ) as standalone_hdul:
                standalone_hdu = _single_table(standalone_hdul)
                master_hdu = master_hdul[extname]
                standalone_structure = _hdu_structure(standalone_hdu)
                master_structure = _hdu_structure(master_hdu)
                verify_table_structure(
                    target_table, standalone_structure, master_structure
                )
                if population is None:
                    population = standalone_structure.row_count
                    if population != EXPECTED_LIVE_ROWS:
                        raise ValueError(
                            "Observed live population mismatch: expected "
                            f"{EXPECTED_LIVE_ROWS}, observed {population}"
                        )
                    sample = generate_shared_sample(
                        population, SHARED_SAMPLE_SIZE, SHARED_SAMPLE_SEED
                    )
                if standalone_structure.row_count != population:
                    raise ValueError(
                        f"Shared eligible population mismatch for {target_table}: "
                        f"expected {population}, observed "
                        f"{standalone_structure.row_count}"
                    )
                assert sample is not None
                validate_shared_sample(
                    sample, population, SHARED_SAMPLE_SIZE, SHARED_SAMPLE_SEED
                )

                primary = target_table == "photometry_primary"
                verify_native_id_contract(
                    target_table, standalone_structure.names, primary=primary
                )
                if primary:
                    primary_id_count = 1
                else:
                    keyless_absences += 1

                table_mismatches = MismatchCounts()
                table_scalar_fields = 0
                table_vector_fields = 0
                for name in standalone_structure.names:
                    standalone_values = _column_values(standalone_hdu, name, sample)
                    master_values = _column_values(master_hdu, name, sample)
                    counts = compare_exact_arrays(standalone_values, master_values)
                    if np.asarray(standalone_values).ndim > 1:
                        table_vector_fields += 1
                    else:
                        table_scalar_fields += 1
                    if counts.total():
                        raise ValueError(
                            f"Sampled value mismatch for {target_table}.{name}: "
                            f"{asdict(counts)}"
                        )
                    table_mismatches.add(counts)

                source_rows = construct_source_rows(population)
                source_row_exact = bool(
                    len(source_rows) == population
                    and (population == 0 or int(source_rows[0]) == 0)
                    and (population == 0 or int(source_rows[-1]) == population - 1)
                    and np.array_equal(source_rows, np.arange(population))
                )
                if not source_row_exact:
                    raise ValueError(
                        f"source_row construction mismatch: {target_table}"
                    )

                if primary:
                    standalone_ids = _column_values(standalone_hdu, "id", None)
                    master_ids = _column_values(master_hdu, "id", None)
                    verify_primary_id_sequence(standalone_ids, master_ids)
                    primary_ids = np.array(master_ids, copy=True)
                else:
                    if primary_ids is None:
                        raise ValueError("Primary IDs unavailable before keyless table")
                    injected = construct_injected_ids(primary_ids, population)
                    if not np.array_equal(injected, primary_ids):
                        raise ValueError(
                            f"Injected-ID construction mismatch: {target_table}"
                        )
                    injected_checks += 1

                total_fields += len(standalone_structure.names)
                scalar_fields += table_scalar_fields
                vector_fields += table_vector_fields
                total_mismatches.add(table_mismatches)
                table_evidence.append(
                    {
                        "target_table": target_table,
                        "extname": extname,
                        "standalone_path": str(standalone_path),
                        "master_hdu": int(master_hdul.index_of(master_hdu)),
                        "row_count": standalone_structure.row_count,
                        "column_count": len(standalone_structure.names),
                        "ordered_names_equal": True,
                        "tforms_equal": True,
                        "sampled_native_fields": len(standalone_structure.names),
                        "sampled_scalar_fields": table_scalar_fields,
                        "sampled_vector_fields": table_vector_fields,
                        "mismatches": asdict(table_mismatches),
                        "native_id_present": primary,
                        "source_row_complete_zero_based": source_row_exact,
                        "injected_id_complete_primary_ordinal_copy": not primary,
                    }
                )

    if population is None or sample is None or primary_ids is None:
        raise ValueError("No live master comparison evidence was produced")
    if total_fields != EXPECTED_NATIVE_FIELDS:
        raise ValueError(
            f"Sampled native-field total mismatch: expected {EXPECTED_NATIVE_FIELDS}, "
            f"observed {total_fields}"
        )
    if primary_id_count != 1 or keyless_absences != 6 or injected_checks != 6:
        raise ValueError(
            "Native/injected ID contract count mismatch: "
            f"primary={primary_id_count}, keyless={keyless_absences}, "
            f"injected={injected_checks}"
        )
    return {
        "seed": SHARED_SAMPLE_SEED,
        "eligible_population": population,
        "requested_sample_size": SHARED_SAMPLE_SIZE,
        "actual_sample_size": len(sample),
        "sample_sha256": hashlib.sha256(
            sample.astype("<i8", copy=False).tobytes()
        ).hexdigest(),
        "sampled_native_fields": total_fields,
        "sampled_scalar_fields": scalar_fields,
        "sampled_vector_fields": vector_fields,
        "mismatches": asdict(total_mismatches),
        "primary_id_values_compared": len(primary_ids),
        "primary_id_sequences_equal": True,
        "primary_native_id_count": primary_id_count,
        "keyless_native_id_absences": keyless_absences,
        "complete_source_row_constructions": len(table_evidence),
        "complete_injected_id_constructions": injected_checks,
        "tables": table_evidence,
        "inherited_ordinal_alignment_limitation": ORDINAL_LIMITATION,
    }


def run_gate_3_5(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Run the complete Gate 3.5 preflight and return structured evidence."""
    config = yaml.safe_load(config_path.read_text())
    provenance = config.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("Missing provenance path configuration")
    manifest_path = Path(provenance["source_manifest_v11"])
    sed_sidecar_path = Path(provenance["cigale_seds_aggregate_pin"])
    nvme_root = str(Path(config["data_root"]))
    specz_root = str(Path(config["specz"]["compilation_root"]))
    expected_counts = {
        nvme_root: EXPECTED_MANIFEST_ROOT_COUNTS[0],
        specz_root: EXPECTED_MANIFEST_ROOT_COUNTS[1],
    }

    # AI NOTE: no catalog or semantic source may be opened above this point.
    # The complete repaired-manifest preflight is the first source-data read.
    contract = parse_manifest_contract(manifest_path, expected_counts)
    live_manifest_errors = validate_manifest(
        manifest_path,
        [(Path(nvme_root), False), (Path(specz_root), True)],
    )
    if live_manifest_errors:
        raise ValueError(
            "Production manifest verification failed:\n"
            + "\n".join(live_manifest_errors)
        )
    if contract.row_count != EXPECTED_MANIFEST_ROWS:
        raise ValueError(f"Production manifest row mismatch: {contract.row_count}")

    sed_evidence = reproduce_sed_aggregate(sed_sidecar_path)
    manifest_inputs = _consumed_manifest_inputs(config)
    input_evidence = [
        pin_manifest_input(name, path, contract)
        for name, path in manifest_inputs.items()
    ]

    dictionary_path = Path(config["dictionary"]["columns_v11"])
    unit_path = Path(config["semantic_sources"]["unit_conventions"])
    unit_hash = _dictionary_recorded_hash(dictionary_path, str(unit_path))
    spec_path = Path(config["semantic_sources"]["etl_v2_spec"])
    spec_hash = _dictionary_recorded_hash(dictionary_path, str(spec_path))
    yang_path = Path(config["semantic_sources"]["yang_v1_pdf"])
    dictionary_yang_hash = _dictionary_recorded_hash(dictionary_path, YANG_REFERENCE)
    if dictionary_yang_hash != YANG_SHA256:
        raise ValueError(
            "Dictionary Yang SHA-256 mismatch: expected "
            f"{YANG_SHA256}, observed {dictionary_yang_hash}"
        )
    boundary_evidence = [
        pin_boundary_input(
            "unit_conventions",
            unit_path,
            boundary="git-controlled-project-input",
            reference="dictionary-recorded semantic evidence",
            declared_sha256=unit_hash,
        ),
        pin_boundary_input(
            "etl_v2_spec",
            spec_path,
            boundary="operator-controlled-project-spec",
            reference="dictionary-recorded project-derived evidence",
            declared_sha256=spec_hash,
        ),
        pin_boundary_input(
            "yang_v1_pdf",
            yang_path,
            boundary="authorized-external-reference",
            reference=YANG_ARXIV_ID,
            declared_sha256=YANG_SHA256,
            declared_bytes=YANG_BYTES,
        ),
    ]

    comparison_evidence = _compare_live_tables(config)
    return {
        "gate": "3.5",
        "status": "passed",
        "manifest": {
            "path": str(manifest_path),
            "header": list(contract.header),
            "row_count": contract.row_count,
            "root_counts": contract.root_counts,
            "unique_keys": len(contract.entries),
            "git_rows": 0,
            "cigale_sed_rows": 0,
            "live_filesystem_verified": True,
        },
        "cigale_sed_aggregate": asdict(sed_evidence),
        "consumed_manifest_input_count": len(input_evidence),
        "consumed_manifest_inputs": [asdict(item) for item in input_evidence],
        "nonmanifest_boundaries": [asdict(item) for item in boundary_evidence],
        "standalone_master_fidelity": comparison_evidence,
    }


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Run Gate 3.5 and print deterministic machine-readable evidence."""
    parser = argparse.ArgumentParser(
        description="Verify Gate 3.5 source integrity and FITS fidelity"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to data_paths.yaml",
    )
    args = parser.parse_args()
    try:
        evidence = run_gate_3_5(args.config)
    except Exception as exc:  # noqa: BLE001 - CLI must emit the halt reason
        print(f"Gate 3.5 verification FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
