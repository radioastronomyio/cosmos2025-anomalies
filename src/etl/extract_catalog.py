#!/usr/bin/env python3
"""
COSMOS-Web DR1 ETL Pipeline: FITS -> Parquet -> PostgreSQL

Purpose:
    Extract the COSMOS-Web DR1 master catalog (Shuntov et al. 2025) from a
    multi-extension FITS file into cleaned parquet files, then bulk-load them
    into PostgreSQL on psql01. Also loads two supplementary catalogs (LSS
    overdensity, galaxy groups + memberships).

    Extensions 3 (SE++ APER photometry) and 6 (Bulge+Disk decomposition) are
    intentionally skipped — see docs/research/etl-pipeline-one-pager.md for the
    rationale.

Usage:
    source /opt/agents/venv/bin/activate
    doppler run --project ml01 --config prd -- \
        python src/etl/extract_catalog.py
    (run from /opt/agents/repos/cosmos2025-anomalies)

Dependencies:
    astropy, numpy, pandas, psycopg2, pyarrow, pyyaml

Output:
    Parquet files written to the directory specified in configs/data_paths.yaml
    (default: staging/parquet under the repository root).
    Tables loaded into the ``catalog`` schema on psql01.

Unit conventions (critical for downstream analysis):
    LePhare columns: mass, SFR, sSFR are in LOG10 space.
    CIGALE columns: mass, SFR are in LINEAR space (M_sun, M_sun/yr).
    The derived sSFR (ssfr_cigale) is LINEAR (yr-1).
"""

import io
import logging
import os
import sys
import time

import numpy as np
import pandas as pd
import psycopg2
import yaml
from astropy.io import fits

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

REPO_ROOT = "/opt/agents/repos/cosmos2025-anomalies"

# Destructive-run fence. This script TRUNCATEs and reloads the ``cosmos2025``
# (v1) database, which upstream replaced in place and which therefore cannot be
# rebuilt from source. It is retained for provenance: it records how v1 was
# constructed, including the sentinel-to-NULL conversion in ``convert_sentinels``
# that the v1.1 mirror deliberately does not perform. Reading it is safe;
# running it is not. The v1.1 pipeline is src/etl/bootstrap_v11.py, which never
# imports or invokes this module.
DESTRUCTIVE_RUN_ENV = "COSMOS2025_ALLOW_V1_DESTRUCTIVE_RELOAD"
DESTRUCTIVE_RUN_TOKEN = "i-understand-v1-cannot-be-rebuilt"


def require_destructive_run_authorization(environment=os.environ):
    """Refuse to run unless the operator has explicitly authorized v1 destruction.

    The pipeline's first database action truncates every loaded table in the
    ``catalog`` schema of ``cosmos2025``. That database is an irreplaceable
    read-only baseline, so an accidental invocation is unrecoverable.
    Authorization is an exact environment token rather than a command-line flag
    so that it cannot arrive from shell history or a copied command line.

    Args:
        environment: Mapping consulted for the authorization token.

    Raises:
        SystemExit: If the exact token is absent.
    """
    if environment.get(DESTRUCTIVE_RUN_ENV) != DESTRUCTIVE_RUN_TOKEN:
        raise SystemExit(
            "refusing to run: this script TRUNCATEs and reloads the cosmos2025 "
            "(v1) database, which cannot be rebuilt because upstream replaced "
            "the source downloads in place. For the v1.1 mirror use "
            "src/etl/bootstrap_v11.py instead. To authorize destruction of v1 "
            f"anyway, set {DESTRUCTIVE_RUN_ENV}={DESTRUCTIVE_RUN_TOKEN}."
        )


def load_config():
    """Load data_paths.yaml from the repository configs directory.

    Returns:
        dict: Parsed YAML config with keys for catalogs, processed paths,
              database connection parameter names, and supplementary file paths.
    """
    with open(os.path.join(REPO_ROOT, "configs", "data_paths.yaml")) as f:
        return yaml.safe_load(f)


def get_db_connection(config):
    """Connect to PostgreSQL on psql01 using Doppler-injected credentials.

    The config stores *environment variable names* (not values) for each
    connection parameter.  This script reads the actual credentials from
    the environment via python-dotenv.

    Args:
        config: Parsed data_paths.yaml dict.

    Returns:
        psycopg2.connection: Open connection to the cosmos2025 database.
    """
    db = config["database"]
    return psycopg2.connect(
        host=os.environ[db["host_env"]],
        port=os.environ[db["port_env"]],
        user=os.environ[db["user_env"]],
        password=os.environ[db["password_env"]],
        dbname=db["database_name"],
    )


def is_array_column(col_format):
    """Determine whether a FITS binary table column is a vector (repeat count > 1).

    String columns ending in 'A' (e.g. '10A') are scalars, not arrays.

    Args:
        col_format: FITS column format string (e.g. '50A', '37E', '1J').

    Returns:
        bool: True if the column stores multiple values per row.
    """
    fmt = col_format.strip()
    if fmt.endswith("A"):
        return False
    if len(fmt) >= 2 and fmt[:-1].isdigit():
        return int(fmt[:-1]) > 1
    return False


def to_native(arr):
    """Convert a numpy array to native byte order.

    FITS data is big-endian; pandas and pyarrow expect native (little-endian
    on x86).  Columns left in non-native order cause cryptic parquet errors.

    Args:
        arr: numpy array, possibly non-native byte order.

    Returns:
        numpy array in native byte order (or the original if already native).
    """
    if (
        hasattr(arr, "dtype")
        and arr.dtype.byteorder not in ("=", "|")
        and arr.dtype.byteorder != ""
    ):
        return arr.astype(arr.dtype.newbyteorder("="))
    return arr


def convert_sentinels(arr, sentinels=(-999, -999.0, -99, -99.0)):
    """Replace FITS sentinel values with NaN in a float column.

    Sentinel values are arbitrary negative integers used by the catalog
    creators to mark missing or failed measurements:
        -999 / -999.0  —  general missing-value marker (most columns)
        -99  / -99.0   —  secondary marker used in some LePhare columns
        -999.9 / -99.9 —  variant markers (handled in LePhare extraction)
    All sentinels are converted to NaN so that downstream code never needs
    to know which sentinel a particular column used.

    Args:
        arr: numpy array to clean.
        sentinels: Tuple of sentinel values to replace with NaN.

    Returns:
        numpy float64 array with sentinels replaced by NaN.
    """
    if arr.dtype.kind == "f":
        result = to_native(arr).astype(np.float64).copy()
    elif arr.dtype.kind in ("i", "u"):
        result = to_native(arr).astype(np.float64)
    else:
        return arr
    mask = np.zeros(result.shape, dtype=bool)
    for s in sentinels:
        if not (isinstance(s, float) and np.isnan(s)):
            mask |= np.isclose(result, float(s))
    result[mask] = np.nan
    return result


def convert_sentinels_int(arr, sentinels=(-999,)):
    """Replace sentinel values with pd.NA in an integer column.

    Integer columns cannot hold NaN, so we use pandas nullable Int64 dtype.
    This is used for ID-like columns and flag columns where sentinel values
    indicate "no data" (e.g. id_specz_khostovan25 = -999 means no spec-z match).

    Args:
        arr: numpy integer array to clean.
        sentinels: Tuple of integer sentinel values to replace.

    Returns:
        pandas Int64 array with sentinels replaced by pd.NA.
    """
    arr = to_native(arr).copy()
    mask = np.zeros(arr.shape, dtype=bool)
    for s in sentinels:
        mask |= arr == s
    safe = arr.copy()
    safe[mask] = 0
    result = pd.array(safe, dtype=pd.Int64Dtype())
    result[mask] = pd.NA
    return result


def decode_str_column(raw_data):
    """Decode a FITS string column from bytes to stripped ASCII strings.

    Args:
        raw_data: FITS column data (bytes or mixed types).

    Returns:
        list of str: Decoded, whitespace-stripped strings.
    """
    vals = []
    for x in raw_data:
        if isinstance(x, bytes):
            vals.append(x.decode("ascii").strip())
        else:
            vals.append(str(x).strip())
    return vals


# Columns skipped in Extension 1 (Photometry) to keep parquet manageable:
#   - flux_model_*, flux_err-*_model_* : ~200 repeated model-fit fluxes per band
#   - flux_aper_*, flux_err_aper_*, mag_aper_* : aperture photometry arrays
# These are bulk photometry products not needed for catalog-level anomaly
# detection.  Total reduction: ~285 columns -> ~85 scalar columns.
PHOT_SKIP_PREFIXES = (
    "flux_model_",
    "flux_err-uncal_model_",
    "flux_err-cal_model_",
    "flux_aper_",
    "flux_err_aper_",
    "mag_aper_",
)


def extract_photometry_core(hdul, output_dir):
    """Extract Extension 1 (Photometry) to photometry_core.parquet.

    Selects ~85 scalar columns from Extension 1, skipping array columns and
    bulk model/aperature photometry (see PHOT_SKIP_PREFIXES).  Applies
    column-specific type handling and sentinel conversion.

    Args:
        hdul: Open astropy FITS HDUList (memmapped).
        output_dir: Directory for parquet output.

    Returns:
        pd.DataFrame: The extracted photometry dataframe.
    """
    log.info("Extracting Extension 1 (Photometry) -> photometry_core.parquet")
    ext = hdul[1]

    selected = []
    for col in ext.columns:
        if is_array_column(col.format):
            continue
        if any(col.name.startswith(p) for p in PHOT_SKIP_PREFIXES):
            continue
        selected.append(col.name)

    log.info(f"  Selected {len(selected)} scalar columns")

    data = {}
    for cn in selected:
        raw = ext.data[cn]
        san = cn.replace("-", "_")

        if cn in ("flag_star", "flag_blend"):
            data[san] = raw.astype(bool)
        elif cn in ("tile", "mode"):
            data[san] = decode_str_column(raw)
        elif cn == "flag_star_hsc":
            data[san] = raw.astype(np.int16)
        elif cn in ("id", "segment_id", "group_id", "warn_flag"):
            data[san] = to_native(raw)
        elif cn == "id_specz_khostovan25":
            data[san] = convert_sentinels_int(raw, sentinels=(-999,))
        elif cn.startswith("wht_"):
            data[san] = raw.astype(np.float64)
        elif cn.startswith("mag_err_model_"):
            data[san] = convert_sentinels(raw, sentinels=(-999, -999.0))
        elif raw.dtype.kind == "f":
            data[san] = convert_sentinels(raw, sentinels=(-999, -999.0))
        elif raw.dtype.kind in ("i", "u"):
            data[san] = raw
        else:
            data[san] = raw

    df = pd.DataFrame(data)
    log.info(f"  Shape: {df.shape}")
    path = os.path.join(output_dir, "photometry_core.parquet")
    df.to_parquet(path, index=False, engine="pyarrow")
    log.info(f"  Written: {path}")
    return df


def extract_lephare(hdul, id_array, output_dir):
    """Extract Extension 2 (LePhare SED fitting) to lephare.parquet.

    All 43 LePhare columns are extracted.  The 'id' column is injected from
    Extension 1 because LePhare, CIGALE, and Morphology extensions do not
    contain their own source ID column — they are row-aligned with Extension 1.

    LePhare uses a wider set of sentinel variants (-999, -999.9, -99, -99.9)
    and also marks some values as -inf (neginf), which are converted to NaN.

    Args:
        hdul: Open astropy FITS HDUList (memmapped).
        id_array: Source ID array from Extension 1 (injected as 'id' column).
        output_dir: Directory for parquet output.

    Returns:
        pd.DataFrame: The extracted LePhare dataframe.
    """
    log.info("Extracting Extension 2 (LePhare) -> lephare.parquet")
    ext = hdul[2]

    data = {"id": id_array}
    for col in ext.columns:
        raw = ext.data[col.name]
        san = col.name.replace("-", "_")

        if col.name == "zfinal":
            data[san] = convert_sentinels(raw, sentinels=(-99, -99.0))
        elif col.name == "mod_minchi2_phys":
            data[san] = convert_sentinels_int(raw, sentinels=(-99,))
        elif col.name == "law_minchi2":
            data[san] = convert_sentinels_int(raw, sentinels=(-999,))
        elif raw.dtype.kind == "i":
            data[san] = to_native(raw)
        elif raw.dtype.kind == "f":
            converted = convert_sentinels(
                raw, sentinels=(-999, -999.0, -999.9, -99, -99.0, -99.9)
            )
            converted[np.isneginf(converted)] = np.nan
            data[san] = converted
        else:
            data[san] = to_native(raw)

    df = pd.DataFrame(data)
    log.info(f"  Shape: {df.shape}")
    path = os.path.join(output_dir, "lephare.parquet")
    df.to_parquet(path, index=False, engine="pyarrow")
    log.info(f"  Written: {path}")
    return df


def extract_cigale(hdul, id_array, output_dir):
    """Extract Extension 4 (CIGALE SED fitting) to cigale.parquet.

    All 54 CIGALE columns are extracted plus the injected 'id' and a derived
    'ssfr_cigale' column.  CIGALE reports mass in linear M_sun and SFR in
    linear M_sun/yr, so sSFR is computed as sfr_inst / mass (linear yr-1).

    Note: ssfr_cigale is NOT in the original catalog — it is derived here
    during extraction so that downstream code has a consistent sSFR column
    for both SED fitters (LePhare provides ssfr_med natively in log10 space).

    Args:
        hdul: Open astropy FITS HDUList (memmapped).
        id_array: Source ID array from Extension 1 (injected as 'id' column).
        output_dir: Directory for parquet output.

    Returns:
        pd.DataFrame: The extracted CIGALE dataframe with derived ssfr_cigale.
    """
    log.info("Extracting Extension 4 (CIGALE) -> cigale.parquet")
    ext = hdul[4]

    data = {"id": id_array}
    for col in ext.columns:
        raw = ext.data[col.name]
        san = col.name.replace("-", "_")
        if raw.dtype.kind == "f":
            data[san] = convert_sentinels(raw, sentinels=(-999, -999.0))
        elif raw.dtype.kind in ("i", "u"):
            data[san] = convert_sentinels(raw, sentinels=(-999,))
        else:
            data[san] = raw

    df = pd.DataFrame(data)

    # ssfr_cigale = sfr_inst / mass  (linear yr-1, derived — not in original catalog)
    # Only computed where both mass and SFR are valid and mass != 0.
    sfr = df["sfr_inst"].values.astype(np.float64)
    mass = df["mass"].values.astype(np.float64)
    ssfr = np.full_like(sfr, np.nan)
    valid = (~np.isnan(mass)) & (mass != 0) & (~np.isnan(sfr))
    ssfr[valid] = sfr[valid] / mass[valid]
    df["ssfr_cigale"] = ssfr
    log.info(
        f"  Derived ssfr_cigale: {int(valid.sum())} valid, {int((~valid).sum())} NULL"
    )

    log.info(f"  Shape: {df.shape}")
    path = os.path.join(output_dir, "cigale.parquet")
    df.to_parquet(path, index=False, engine="pyarrow")
    log.info(f"  Written: {path}")
    return df


def extract_morphology(hdul, id_array, output_dir):
    """Extract Extension 5 (ML-Morpho) to morphology.parquet.

    Selects ~30 columns from the 150-column morphology extension:
    class probability means/stds (_mean, _std), morphological flags
    (morph_flag_*), and concentration indices (delta_*).  The remaining
    ~120 columns are per-epoch individual classifications not needed for
    catalog-level analysis.

    Args:
        hdul: Open astropy FITS HDUList (memmapped).
        id_array: Source ID array from Extension 1 (injected as 'id' column).
        output_dir: Directory for parquet output.

    Returns:
        pd.DataFrame: The extracted morphology dataframe.
    """
    log.info("Extracting Extension 5 (ML-Morpho) -> morphology.parquet")
    ext = hdul[5]

    selected = []
    for col in ext.columns:
        cn = col.name
        if cn.endswith("_mean") or cn.endswith("_std"):
            selected.append(cn)
        elif cn.startswith("morph_flag_"):
            selected.append(cn)
        elif cn.startswith("delta_"):
            selected.append(cn)

    log.info(f"  Selected {len(selected)} columns from 150")

    data = {"id": id_array}
    for cn in selected:
        raw = ext.data[cn]
        san = cn.replace("-", "_")
        if cn.startswith("morph_flag_"):
            data[san] = convert_sentinels_int(raw, sentinels=(999999,))
        elif raw.dtype.kind == "f":
            data[san] = raw.astype(np.float64)
        else:
            data[san] = raw

    df = pd.DataFrame(data)
    log.info(f"  Shape: {df.shape}")
    path = os.path.join(output_dir, "morphology.parquet")
    df.to_parquet(path, index=False, engine="pyarrow")
    log.info(f"  Written: {path}")
    return df


def load_parquet_to_psql(parquet_path, table_name, conn, schema="catalog"):
    """Load a parquet file into a PostgreSQL table using COPY FROM STDIN.

    Columns are reordered to match the database schema's ordinal positions
    (df = df[db_columns]).  This is necessary because the parquet column
    order may differ from the DDL column order — parquet preserves the
    extraction order while the DDL was written independently.  Without
    reordering, COPY FROM CSV with HEADER would fail on type mismatches.

    Boolean columns are mapped to 't'/'f' strings for PostgreSQL compatibility.

    Args:
        parquet_path: Path to the parquet file.
        table_name: Target table name in the catalog schema.
        conn: Open psycopg2 connection.
        schema: Database schema name (default: 'catalog').

    Side effects:
        Commits the transaction on success, rolls back on failure.
    """
    log.info(f"Loading {os.path.basename(parquet_path)} -> {schema}.{table_name}")
    df = pd.read_parquet(parquet_path)

    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
        (schema, table_name),
    )
    db_columns = [r[0] for r in cur.fetchall()]
    cur.close()

    # Reorder dataframe columns to match DDL ordinal positions.
    # The parquet column order follows the FITS extension layout;
    # the DDL was written with a different (more logical) ordering.
    df = df[db_columns]

    for col in df.select_dtypes(include=["bool"]).columns:
        df[col] = df[col].map({True: "t", False: "f"})

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)

    cur = conn.cursor()
    try:
        cur.copy_expert(
            f"COPY {schema}.{table_name} FROM STDIN WITH (FORMAT CSV, HEADER)", buf
        )
        conn.commit()
        log.info(f"  Loaded {len(df):,} rows into {schema}.{table_name}")
    except Exception as e:
        conn.rollback()
        log.error(f"  FAILED loading {schema}.{table_name}: {e}")
        raise
    finally:
        cur.close()


def load_lss_overdensity(config, conn):
    """Load the Hatamnia LSS overdensity supplementary catalog.

    Reads the OVERDENSITY extension from the LSS FITS file and loads
    id, RA, Dec, and density_excess into catalog.lss_overdensity.

    Args:
        config: Parsed data_paths.yaml dict (provides supplementary file paths).
        conn: Open psycopg2 connection.

    Side effects:
        Commits on success, rolls back on failure.
    """
    log.info("Loading LSS overdensity catalog")
    path = config["supplementary"]["lss_overdensity"]

    with fits.open(path, memmap=True) as hdul:
        d = hdul["OVERDENSITY"].data
        df = pd.DataFrame(
            {
                "id": d["id"].astype(np.int64),
                "ra": d["RA"].astype(np.float64),
                "dec": d["Dec"].astype(np.float64),
                "density_excess": d["density_excess"].astype(np.float64),
            }
        )

    log.info(f"  LSS rows: {len(df):,}")

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)

    cur = conn.cursor()
    try:
        cur.copy_expert(
            "COPY catalog.lss_overdensity FROM STDIN WITH (FORMAT CSV, HEADER)", buf
        )
        conn.commit()
        log.info(f"  Loaded {len(df):,} rows into catalog.lss_overdensity")
    except Exception as e:
        conn.rollback()
        log.error(f"  FAILED: {e}")
        raise
    finally:
        cur.close()


def load_galaxy_groups(config, conn):
    """Load the Toni group catalog (groups table) into catalog.galaxy_groups.

    The source file is whitespace-delimited with a header row.  Column names
    are mapped explicitly to match the DDL.  The n_spec column uses -99 as
    a sentinel for groups with no spectroscopic members.

    Args:
        config: Parsed data_paths.yaml dict.
        conn: Open psycopg2 connection.

    Side effects:
        Commits on success, rolls back on failure.
    """
    log.info("Loading galaxy group catalog")
    path = config["supplementary"]["group_catalog_groups"]

    col_map = [
        "group_id",
        "ra",
        "dec",
        "z",
        "sn",
        "sn_nocl",
        "amp",
        "mskfrc",
        "lambda",
        "lambda_star",
        "detection_flag",
        "n_spec",
        "zphys_sigm",
        "zphys_sigp",
    ]

    df = pd.read_csv(path, sep=r"\s+", names=col_map, skiprows=1)
    df.loc[df["n_spec"] == -99, "n_spec"] = pd.NA
    df["n_spec"] = df["n_spec"].astype(pd.Int64Dtype())

    log.info(f"  Groups: {len(df):,} rows")

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)

    cur = conn.cursor()
    try:
        cur.copy_expert(
            "COPY catalog.galaxy_groups FROM STDIN WITH (FORMAT CSV, HEADER)", buf
        )
        conn.commit()
        log.info(f"  Loaded {len(df):,} rows into catalog.galaxy_groups")
    except Exception as e:
        conn.rollback()
        log.error(f"  FAILED: {e}")
        raise
    finally:
        cur.close()


def load_group_memberships(config, conn):
    """Load galaxy-to-group membership associations into catalog.galaxy_group_memberships.

    Each row maps a galaxy ID (galid) to a group with an association probability.

    Args:
        config: Parsed data_paths.yaml dict.
        conn: Open psycopg2 connection.

    Side effects:
        Commits on success, rolls back on failure.
    """
    log.info("Loading galaxy group memberships")
    path = config["supplementary"]["group_catalog_memberships"]

    col_map = ["galid", "field_prob", "group_id", "assoc_prob"]
    df = pd.read_csv(path, sep=r"\s+", names=col_map, skiprows=1)

    log.info(f"  Memberships: {len(df):,} rows")

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)

    cur = conn.cursor()
    try:
        cur.copy_expert(
            "COPY catalog.galaxy_group_memberships FROM STDIN WITH (FORMAT CSV, HEADER)",
            buf,
        )
        conn.commit()
        log.info(f"  Loaded {len(df):,} rows into catalog.galaxy_group_memberships")
    except Exception as e:
        conn.rollback()
        log.error(f"  FAILED: {e}")
        raise
    finally:
        cur.close()


def run_verification(conn):
    """Run inline verification checks immediately after loading.

    Validates row counts (all 4 core tables must have exactly 784,016 rows),
    checks that sentinel values were properly converted to NULL, and performs
    a cross-code join spot check between LePhare and CIGALE.

    Args:
        conn: Open psycopg2 connection to the cosmos2025 database.
    """
    log.info("=" * 60)
    log.info("VERIFICATION")
    log.info("=" * 60)
    cur = conn.cursor()

    expected = 784016
    for t in ("photometry_core", "lephare", "cigale", "morphology"):
        cur.execute(f"SELECT COUNT(*) FROM catalog.{t}")
        cnt = cur.fetchone()[0]
        ok = "PASS" if cnt == expected else "FAIL"
        log.info(f"  [{ok}] catalog.{t}: {cnt:,} rows (expected {expected:,})")

    for t in ("lss_overdensity", "galaxy_groups", "galaxy_group_memberships"):
        cur.execute(f"SELECT COUNT(*) FROM catalog.{t}")
        cnt = cur.fetchone()[0]
        log.info(f"  [INFO] catalog.{t}: {cnt:,} rows")

    cur.execute("SELECT COUNT(*) FILTER (WHERE mass_med IS NULL) FROM catalog.lephare")
    nulls = cur.fetchone()[0]
    ok = "PASS" if nulls > 0 else "FAIL"
    log.info(f"  [{ok}] lephare.mass_med NULL count: {nulls:,} (should be > 0)")

    cur.execute(
        "SELECT l.id, l.mass_med, c.mass FROM catalog.lephare l "
        "JOIN catalog.cigale c ON l.id = c.id LIMIT 5"
    )
    rows = cur.fetchall()
    log.info(f"  [INFO] Cross-code join returned {len(rows)} rows:")
    for r in rows:
        log.info(f"         id={r[0]}, mass_med={r[1]}, mass={r[2]}")

    cur.execute("SELECT COUNT(*) FROM catalog.lephare WHERE zfinal = -99")
    bad = cur.fetchone()[0]
    ok = "PASS" if bad == 0 else "FAIL"
    log.info(f"  [{ok}] Remaining -99 in lephare.zfinal: {bad} (should be 0)")

    cur.execute(
        "SELECT COUNT(*) FROM catalog.morphology WHERE morph_flag_f444w = 999999"
    )
    bad = cur.fetchone()[0]
    ok = "PASS" if bad == 0 else "FAIL"
    log.info(
        f"  [{ok}] Remaining 999999 in morphology.morph_flag_f444w: {bad} (should be 0)"
    )

    cur.execute("SELECT COUNT(*) FROM catalog.lephare WHERE law_minchi2 = -999")
    bad = cur.fetchone()[0]
    ok = "PASS" if bad == 0 else "FAIL"
    log.info(f"  [{ok}] Remaining -999 in lephare.law_minchi2: {bad} (should be 0)")

    cur.close()
    log.info("=" * 60)


def main():
    """Execute the full ETL pipeline.

    Pipeline sequence:
        1. Load config and create output directories
        2. Open master catalog FITS (memmapped, 8.4GB)
        3. Extract ID array from Extension 1 (shared by ext 2, 4, 5)
        4. Extract 4 parquet files (photometry, lephare, cigale, morphology)
        5. Connect to PostgreSQL and truncate existing tables
        6. Bulk-load parquet files + supplementary catalogs
        7. Run inline verification checks
    """
    require_destructive_run_authorization()

    t0 = time.time()
    config = load_config()

    parquet_dir = config["processed"]["parquet_dir"]
    derived_dir = config["processed"]["derived_dir"]
    staging_dir = config["processed"]["staging_dir"]
    for d in (parquet_dir, derived_dir, staging_dir):
        os.makedirs(d, exist_ok=True)

    fits_path = config["catalogs"]["master_catalog"]
    log.info(f"Opening master catalog: {fits_path}")

    with fits.open(fits_path, memmap=True) as hdul:
        # Extensions 2, 4, 5 lack their own 'id' column — they are
        # row-aligned with Extension 1.  We copy the ID array here and
        # inject it into each extracted table so downstream joins work.
        id_array = to_native(hdul[1].data["id"].copy())
        log.info(f"Loaded ID array: {len(id_array):,} entries")

        extract_photometry_core(hdul, parquet_dir)
        extract_lephare(hdul, id_array, parquet_dir)
        extract_cigale(hdul, id_array, parquet_dir)
        extract_morphology(hdul, id_array, parquet_dir)

    log.info("Connecting to PostgreSQL (psql01)")
    conn = get_db_connection(config)

    try:
        cur = conn.cursor()
        cur.execute(
            "TRUNCATE catalog.photometry_core, catalog.lephare, "
            "catalog.cigale, catalog.morphology, "
            "catalog.lss_overdensity, catalog.galaxy_groups, "
            "catalog.galaxy_group_memberships CASCADE"
        )
        conn.commit()
        cur.close()
        log.info("Truncated all catalog tables")

        for pq_file, table in [
            ("photometry_core.parquet", "photometry_core"),
            ("lephare.parquet", "lephare"),
            ("cigale.parquet", "cigale"),
            ("morphology.parquet", "morphology"),
        ]:
            load_parquet_to_psql(os.path.join(parquet_dir, pq_file), table, conn)

        load_lss_overdensity(config, conn)
        load_galaxy_groups(config, conn)
        load_group_memberships(config, conn)

        run_verification(conn)
    finally:
        conn.close()

    elapsed = time.time() - t0
    log.info(f"ETL pipeline complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
