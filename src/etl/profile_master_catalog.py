"""
COSMOS-Web DR1 Master Catalog Profiler
======================================
Profiles the COSMOSWeb_mastercatalog_v1.fits file to characterize each
extension's structure, column types, row counts, null/sentinel patterns,
and basic statistics. Outputs a markdown report for ETL planning.

Usage:
    python profile_master_catalog.py

Output:
    ../../../docs/reference/master-catalog-profile.md

Requirements:
    pip install astropy numpy
"""

import sys
import time
from pathlib import Path

import numpy as np
from astropy.io import fits

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Primary data root on E:, adjust if your layout differs
CATALOG_PATH = Path(r"E:\repositories-data-folder\cosmos-web-dr1-2025\raw\catalogs\COSMOSWeb_mastercatalog_v1.fits")

# Output report location (relative to this script inside src/etl/)
REPORT_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "reference" / "master-catalog-profile.md"

# How many rows to sample for null/range analysis (full scan is slow on 8.4GB)
SAMPLE_SIZE = 50_000

# Common sentinel values used in astronomical catalogs
SENTINELS = {
    "int": [-999, -99, -1, 0, 99, 999],
    "float": [-999.0, -99.0, -9999.0, -1.0, 0.0, np.nan, np.inf, -np.inf],
}


def format_bytes(nbytes: int) -> str:
    """Human-readable byte size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def fits_dtype_label(fmt: str) -> str:
    """Convert FITS format code to human-readable type."""
    mapping = {
        "L": "bool",
        "B": "uint8",
        "I": "int16",
        "J": "int32",
        "K": "int64",
        "E": "float32",
        "D": "float64",
        "C": "complex64",
        "M": "complex128",
        "A": "string",
    }
    # Strip repeat count for scalar columns; keep for arrays
    count = ""
    base = fmt
    if len(fmt) > 1 and fmt[-1].isalpha():
        count = fmt[:-1]
        base = fmt[-1]
    
    label = mapping.get(base, fmt)
    if count and count != "1":
        label = f"{label}[{count}]"
    return label


def profile_extension(hdu, ext_idx: int, sample_size: int) -> dict:
    """Profile a single BINTABLE extension."""
    header = hdu.header
    ext_name = header.get("EXTNAME", f"EXT_{ext_idx}")
    nrows = header.get("NAXIS2", 0)
    ncols = header.get("TFIELDS", 0)

    # Column metadata
    columns = []
    for i in range(1, ncols + 1):
        col_name = header.get(f"TTYPE{i}", f"col_{i}")
        col_fmt = header.get(f"TFORM{i}", "?")
        col_unit = header.get(f"TUNIT{i}", "")
        columns.append({
            "name": col_name,
            "fits_format": col_fmt,
            "dtype": fits_dtype_label(col_fmt),
            "unit": col_unit,
        })

    # Sample data for statistics
    n_sample = min(sample_size, nrows)
    if n_sample > 0 and nrows > 0:
        # Read the first n_sample rows (avoids random access on large files)
        data = hdu.data[:n_sample]
        col_stats = []
        for col_info in columns:
            cname = col_info["name"]
            try:
                vals = data[cname]
            except (KeyError, IndexError):
                col_stats.append({"name": cname, "error": "read_failed"})
                continue

            stat = {"name": cname}

            # Handle array columns (e.g., flux_aper with 5 apertures)
            if vals.ndim > 1:
                stat["array_shape"] = str(vals.shape[1:])
                vals_flat = vals.ravel()
            else:
                vals_flat = vals

            # Numeric stats
            if np.issubdtype(vals_flat.dtype, np.floating):
                finite = vals_flat[np.isfinite(vals_flat)]
                stat["n_nan"] = int(np.sum(np.isnan(vals_flat)))
                stat["n_inf"] = int(np.sum(np.isinf(vals_flat)))
                if len(finite) > 0:
                    stat["min"] = float(np.min(finite))
                    stat["max"] = float(np.max(finite))
                    stat["median"] = float(np.median(finite))
                    stat["mean"] = float(np.mean(finite))
                # Check sentinel values
                sentinel_hits = {}
                for sv in SENTINELS["float"]:
                    if not (np.isnan(sv) or np.isinf(sv)):
                        count = int(np.sum(vals_flat == sv))
                        if count > 0:
                            sentinel_hits[str(sv)] = count
                if sentinel_hits:
                    stat["sentinels"] = sentinel_hits

            elif np.issubdtype(vals_flat.dtype, np.integer):
                stat["min"] = int(np.min(vals_flat))
                stat["max"] = int(np.max(vals_flat))
                # Check sentinel values
                sentinel_hits = {}
                for sv in SENTINELS["int"]:
                    count = int(np.sum(vals_flat == sv))
                    if count > 0:
                        sentinel_hits[str(sv)] = count
                if sentinel_hits:
                    stat["sentinels"] = sentinel_hits
                # Unique count for low-cardinality columns
                uniques = np.unique(vals_flat)
                if len(uniques) <= 20:
                    stat["unique_values"] = [int(u) for u in uniques]

            elif vals_flat.dtype.kind in ("U", "S", "O"):
                # String columns
                uniques = np.unique(vals_flat)
                stat["n_unique"] = len(uniques)
                if len(uniques) <= 20:
                    stat["unique_values"] = [str(u).strip() for u in uniques]

            col_stats.append(stat)
    else:
        col_stats = []

    return {
        "ext_idx": ext_idx,
        "ext_name": ext_name,
        "nrows": nrows,
        "ncols": ncols,
        "columns": columns,
        "col_stats": col_stats,
        "n_sampled": n_sample,
    }


def generate_report(profiles: list, file_size: int, elapsed: float) -> str:
    """Generate markdown report from extension profiles."""
    lines = []
    lines.append("# COSMOS-Web DR1 Master Catalog Profile")
    lines.append("")
    lines.append(f"**File:** `COSMOSWeb_mastercatalog_v1.fits`")
    lines.append(f"**Size:** {format_bytes(file_size)}")
    lines.append(f"**Extensions:** {len(profiles)}")
    lines.append(f"**Profile time:** {elapsed:.1f}s")
    lines.append(f"**Sample size per extension:** {profiles[0]['n_sampled']:,} rows")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## Extension Summary")
    lines.append("")
    lines.append("| # | Extension | Rows | Columns |")
    lines.append("|---|-----------|------|---------|")
    for p in profiles:
        lines.append(f"| {p['ext_idx']} | {p['ext_name']} | {p['nrows']:,} | {p['ncols']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-extension detail
    for p in profiles:
        lines.append(f"## Extension {p['ext_idx']}: {p['ext_name']}")
        lines.append("")
        lines.append(f"**Rows:** {p['nrows']:,} | **Columns:** {p['ncols']}")
        lines.append("")

        # Column inventory table
        lines.append("### Column Inventory")
        lines.append("")
        lines.append("| Column | FITS Format | Type | Unit |")
        lines.append("|--------|-------------|------|------|")
        for col in p["columns"]:
            lines.append(f"| `{col['name']}` | {col['fits_format']} | {col['dtype']} | {col['unit']} |")
        lines.append("")

        # Statistics for sampled columns
        if p["col_stats"]:
            lines.append("### Sample Statistics")
            lines.append("")
            lines.append(f"Based on first {p['n_sampled']:,} of {p['nrows']:,} rows.")
            lines.append("")

            # Group stats into notable findings
            sentinel_cols = []
            nan_cols = []
            low_card_cols = []
            array_cols = []

            for s in p["col_stats"]:
                if "error" in s:
                    continue
                if s.get("n_nan", 0) > 0:
                    nan_cols.append(s)
                if "sentinels" in s:
                    sentinel_cols.append(s)
                if "unique_values" in s and "array_shape" not in s:
                    low_card_cols.append(s)
                if "array_shape" in s:
                    array_cols.append(s)

            if array_cols:
                lines.append("**Array columns (multi-value per row):**")
                lines.append("")
                for s in array_cols:
                    lines.append(f"- `{s['name']}`: shape {s['array_shape']}")
                lines.append("")

            if nan_cols:
                lines.append("**Columns with NaN values:**")
                lines.append("")
                lines.append("| Column | NaN count | Inf count | Min | Max |")
                lines.append("|--------|-----------|-----------|-----|-----|")
                for s in sorted(nan_cols, key=lambda x: x.get("n_nan", 0), reverse=True)[:30]:
                    pct = 100 * s["n_nan"] / p["n_sampled"] if p["n_sampled"] > 0 else 0
                    mn = f"{s.get('min', 'N/A'):.4g}" if isinstance(s.get('min'), float) else "N/A"
                    mx = f"{s.get('max', 'N/A'):.4g}" if isinstance(s.get('max'), float) else "N/A"
                    lines.append(f"| `{s['name']}` | {s['n_nan']:,} ({pct:.1f}%) | {s.get('n_inf', 0):,} | {mn} | {mx} |")
                if len(nan_cols) > 30:
                    lines.append(f"| ... | ({len(nan_cols) - 30} more columns with NaNs) | | | |")
                lines.append("")

            if sentinel_cols:
                lines.append("**Columns with potential sentinel values:**")
                lines.append("")
                lines.append("| Column | Sentinel | Count |")
                lines.append("|--------|----------|-------|")
                for s in sentinel_cols[:30]:
                    for sv, cnt in s["sentinels"].items():
                        pct = 100 * cnt / p["n_sampled"] if p["n_sampled"] > 0 else 0
                        if pct > 1.0:  # Only report if >1% of sample
                            lines.append(f"| `{s['name']}` | {sv} | {cnt:,} ({pct:.1f}%) |")
                lines.append("")

            if low_card_cols:
                lines.append("**Low-cardinality columns (categorical/flag):**")
                lines.append("")
                for s in low_card_cols:
                    vals_str = ", ".join(str(v) for v in s["unique_values"])
                    lines.append(f"- `{s['name']}`: [{vals_str}]")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines.append(f"*Generated by profile_master_catalog.py*")
    return "\n".join(lines)


def main():
    if not CATALOG_PATH.exists():
        print(f"ERROR: Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    file_size = CATALOG_PATH.stat().st_size
    print(f"Profiling {CATALOG_PATH}")
    print(f"File size: {format_bytes(file_size)}")
    print(f"Sample size: {SAMPLE_SIZE:,} rows per extension")
    print()

    t0 = time.time()

    with fits.open(str(CATALOG_PATH), memmap=True) as hdul:
        print(f"HDU list: {len(hdul)} entries")
        for i, hdu in enumerate(hdul):
            print(f"  [{i}] {type(hdu).__name__}: {hdu.name}")
        print()

        profiles = []
        for i, hdu in enumerate(hdul):
            if isinstance(hdu, fits.BinTableHDU):
                print(f"Profiling extension {i}: {hdu.name} ...", end=" ", flush=True)
                t1 = time.time()
                profile = profile_extension(hdu, i, SAMPLE_SIZE)
                print(f"done ({time.time() - t1:.1f}s, {profile['ncols']} cols)")
                profiles.append(profile)

    elapsed = time.time() - t0
    print(f"\nTotal profiling time: {elapsed:.1f}s")

    # Generate and write report
    report = generate_report(profiles, file_size, elapsed)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
