#!/usr/bin/env python3
"""
Script Name  : profile_v11.py
Description  : Profile the COSMOS-Web v1.1 FITS products to HDU, row, and column level
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-16
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Spec P2R-01 gate 1.8 utility. For each catalog-family FITS product in
configs/data_paths.yaml (master, per-extension products, AGN-DESI
cross-id): enumerate the HDU list with EXTNAME, record per-extension row
counts from headers, and emit machine-generated column name/format
inventories to docs/reference/columns-v1.1-*.txt (mirroring the v1
columns-*.txt pattern). Star masks and detection images are summarized at
the header level only. Deterministic output: re-running regenerates
byte-identical inventory files (the gate validation diffs them). Read-only
against the holdings; uses memmap and never loads full tables.

Usage
-----
    python src/inspection/profile_v11.py [--check]

Examples
--------
    python src/inspection/profile_v11.py
        Writes inventory files under docs/reference/ and a structural
        JSON summary to staging/profile-v11-summary.json.

    python src/inspection/profile_v11.py --check
        Regenerates inventories into a temp directory and diffs them
        against the committed files; exits nonzero on any difference.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import filecmp
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml
from astropy.io import fits

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
REFERENCE_DIR = REPO_ROOT / "docs" / "reference"
SUMMARY_JSON = REPO_ROOT / "staging" / "profile-v11-summary.json"

# Catalog-family keys profiled to the column level; masks and detection
# images are header-level only.
COLUMN_LEVEL_KEYS = [
    "master_catalog",
    "photom_primary",
    "photom_secondary",
    "lephare",
    "cigale",
    "bulgedisk",
    "galight_morph",
    "ml_morph",
    "agngal_desi",
]

HEADER_LEVEL_KEYS = ["detection_images_dir"]

# =============================================================================
# Functions
# =============================================================================


def inventory_filename(key: str, extname: str) -> str:
    """Map a config key plus EXTNAME to the v1-mirroring inventory filename."""
    slug = extname.strip().lower().replace(" ", "-").replace("+", "plus").replace("/", "-")
    return f"columns-v1.1-{slug}.txt"


def profile_bintable(hdu) -> dict:
    """Extract row/column facts from one binary table HDU."""
    return {
        "extname": hdu.header.get("EXTNAME", ""),
        "rows": int(hdu.header.get("NAXIS2", 0)),
        "columns": int(hdu.header.get("TFIELDS", 0)),
        "column_list": [
            {
                "name": name,
                "format": hdu.columns.formats[i],
                "unit": hdu.columns.units[i] or "",
            }
            for i, name in enumerate(hdu.columns.names)
        ],
    }


def profile_fits(path: Path) -> dict:
    """HDU-level facts for one FITS file, column detail for tables."""
    record = {"file": path.name, "bytes": path.stat().st_size, "hdus": []}
    with fits.open(path, memmap=True) as hdul:
        for index, hdu in enumerate(hdul):
            entry = {"index": index, "class": type(hdu).__name__, "extname": hdu.header.get("EXTNAME", "")}
            if hasattr(hdu, "columns") and hdu.columns is not None:
                entry.update(profile_bintable(hdu))
            else:
                entry["naxis1"] = hdu.header.get("NAXIS1")
                entry["naxis2"] = hdu.header.get("NAXIS2")
            record["hdus"].append(entry)
    return record


def write_inventory(record: dict, target_dir: Path) -> list[Path]:
    """Write one deterministic column inventory file per table HDU."""
    written = []
    for hdu in record["hdus"]:
        if "column_list" not in hdu:
            continue
        title = hdu["extname"] or f"HDU{hdu['index']}"
        lines = [f"{title} (v1.1, from {record['file']}, {hdu['rows']} rows)", "Column Name\tFormat\tUnit"]
        for col in hdu["column_list"]:
            lines.append(f"{col['name']}\t{col['format']}\t{col['unit']}")
        out = target_dir / inventory_filename(record["key"], hdu["extname"] or f"hdu{hdu['index']}")
        out.write_text("\n".join(lines) + "\n")
        written.append(out)
    return written


def header_level_files(paths: list[Path]) -> list[dict]:
    """Header-level summary for a list of FITS files (masks/images)."""
    entries = []
    for path in sorted(paths, key=lambda p: p.name):
        with fits.open(path, memmap=True) as hdul:
            header = hdul[0].header
            entries.append(
                {
                    "file": path.name,
                    "hdu_count": len(hdul),
                    "naxis1": header.get("NAXIS1"),
                    "naxis2": header.get("NAXIS2"),
                    "bitpix": header.get("BITPIX"),
                    "imagetyp": header.get("IMAGETYP", ""),
                }
            )
    return entries


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Profile the v1.1 catalog family and emit inventories plus summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="diff regenerated inventories against committed files")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG_PATH.read_text())
    catalogs = config["catalogs"]

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) if args.check else REFERENCE_DIR
        profiled = []
        all_inventory_paths = []
        for key in COLUMN_LEVEL_KEYS:
            path = Path(catalogs[key])
            record = profile_fits(path)
            record["key"] = key
            profiled.append(record)
            all_inventory_paths.extend(write_inventory(record, target))

        if args.check:
            mismatches = [
                regenerated.name
                for regenerated in all_inventory_paths
                if not (REFERENCE_DIR / regenerated.name).exists()
                or not filecmp.cmp(regenerated, REFERENCE_DIR / regenerated.name, shallow=False)
            ]
            if mismatches:
                print(f"inventory check: {len(mismatches)} file(s) differ or missing")
                for name in mismatches:
                    print(f"  {name}")
                raise SystemExit(1)
            print(f"inventory check: {len(all_inventory_paths)} inventories regenerate byte-identical")
            return

    data_root = Path(config["data_root"])
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "catalog_family": profiled,
        "detection_images": header_level_files(
            list(Path(catalogs["detection_images_dir"]).glob("*.fits"))
        ),
        "star_masks": header_level_files(
            list(data_root.glob("cosmos_web_starmask_jwst_*.fits"))
        ),
    }
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
