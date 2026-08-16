<!--
---
title: "COSMOS-Web DR1 ETL Pipeline One-Pager"
description: "v1 ETL schema design and execution record"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Archived"
tags:
  - type: one-pager
  - domain: etl
  - domain: data-engineering
---
-->

# COSMOS-Web DR1 ETL Pipeline — Schema Design & AI-Assisted Execution

**Domain:** Astronomy / Data Engineering
**Status:** Complete (executed 2026-04-05)
**Date:** 2026-03-01
**Version:** 1.1

---

## Vision

Design the PostgreSQL schema and FITS-to-parquet-to-psql ETL pipeline for the COSMOS-Web DR1 master catalog, then hand off code generation to AI coding agents on ML01. We define every decision; the model writes the code.

---

## Project Context

COSMOS-Web DR1 is the largest contiguous JWST imaging survey — 784,016 sources, 0.54 deg², 37-band photometry (JWST NIRCam + MIRI, HST, HSC, UltraVISTA, Subaru, Spitzer), with two independent SED fitting codes (LePhare, CIGALE), ML morphological classifications, and environmental context catalogs.

We are building an anomaly detection research pipeline targeting two primary science opportunities:

**O1 — Algorithmic Disagreement:** Mining residuals between LePhare and CIGALE physical parameter estimates (stellar mass, SFR) to find objects that "break" standard SED fitting. The dual-code framing is genuinely novel for COSMOS-Web. Δlog(M*) > 0.3 dex or Δlog(SFR) > 0.5 dex signal physically distinct objects — extreme emission line galaxies, obscured AGN, or decoupled UV/IR star formation.

**O5 — Contextual Anomalies:** Cross-referencing galaxy properties against large-scale structure density maps to find environmental outliers — massive starbursts in cluster cores, quenched dwarfs in voids. Uses the Hatamnia et al. (2025) LSS overdensity catalog and Toni et al. (2025) group catalog as environmental inputs.

The ETL pipeline exists to make the master catalog queryable in PostgreSQL for these analyses. Everything downstream (feature engineering, anomaly scoring, candidate characterization) depends on this being done correctly.

**Critical unit note (added post-execution):** LePhare physical parameters (mass_med, sfr_med, ssfr_med) are stored in **log10** space. CIGALE parameters (mass, sfr_inst) are in **linear** space. Cross-code comparison formula: `delta = lephare_log10_value - LOG10(cigale_linear_value)`. An earlier draft of this document contained a double-log bug in the verification query; it has been corrected below.

---

## Source Data

### Master Catalog

**File:** `COSMOSWeb_mastercatalog_v1.fits` (8.4 GB)
**Location:** `/mnt/nvme02/cosmosweb2025-dr1/catalogs/` (ML01)

Six BINTABLE extensions, all sharing 784,016 rows in positional lockstep (join by row index, not shared key column). Only Extension 1 has an `id` column — all other extensions are implicitly aligned by row order.

| # | Extension Name | Rows | Columns | Phase 1 Action |
|---|----------------|------|---------|----------------|
| 1 | PHOTOMETRY HOTCOLD AND SE++ | 784,016 | 287 | Extract core columns (skip ~200 band-repeated model mags, skip 18 array columns) |
| 2 | LEPHARE | 784,016 | 43 | Take all columns |
| 3 | SE++APER | 784,016 | 148 | **SKIP entirely** — all 148 columns are float32[5] arrays (5 aperture sizes × 37 bands) |
| 4 | CIGALE | 784,016 | 54 | Take all columns |
| 5 | ML-MORPHO | 784,016 | 150 | Extract mean/std probabilities + morph_flags + deltas (~30 cols, skip 120 per-run probabilities) |
| 6 | B+D (Bulge-Disk) | 784,016 | 461 | **SKIP entirely** — defer to Phase 2 |

### Supplementary Catalogs

| Catalog | File | Location | Rows | Purpose |
|---------|------|----------|------|---------|
| LSS Overdensity | `hatamnia_lss_v1.fits` | `/mnt/nvme02/.../supplementary/` | ~164k sources | `density_excess` values for O5 environmental context |
| Galaxy Groups | `deep-galaxy-group-catalog-groups.txt` | `/mnt/nvme02/.../supplementary/` | 1,678 groups | `group_id`, `prob_assoc` for O5 membership |
| Galaxy Memberships | `deep-galaxy-group-catalog-memberships.txt` | `/mnt/nvme02/.../supplementary/` | ~1.7M rows | Galaxy-group associations |

### Output Locations

| Product | Location |
|---------|----------|
| Parquet files | `/mnt/nvme02/cosmosweb2025-dr1/processed/parquet/` |
| PostgreSQL | psql01 (10.25.20.8), database `cosmos2025`, schema `catalog` |

---

## Sentinel Value Mapping

These sentinel patterns are consistent across the catalog. The ETL must convert all sentinels to NULL in both parquet and psql.

| Sentinel | Meaning | Found In |
|----------|---------|----------|
| `-999` / `-999.0` | No measurement | mag_err, model parameters across all extensions |
| `-99` / `-99.0` | No redshift solution | LePhare `zfinal`, `mod_minchi2_phys` |
| `999999` | No classification | ML-MORPHO `morph_flag` variants |
| `0.0` in `wht_*` columns | No coverage for that band | Photometry extension (66% of sources lack MIRI F770W) |
| NaN | Genuine missing (source couldn't be fit) | CIGALE has 24.9% fully-NULL rows (unfittable sources) |

**Decision:** Convert `-999`, `-999.0`, `-99`, `-99.0`, and `999999` to NULL/NaN during extraction. Preserve `0.0` in weight columns as-is (it's informative, not missing). NaN passes through naturally.

**Justification:** Sentinels in numeric columns corrupt any statistical operation (means, medians, correlations). Converting to NULL ensures correct behavior in both pandas/pyarrow and PostgreSQL aggregations. The weight-zero pattern needs to stay because it distinguishes "measured but faint" from "not observed."

---

## Phase 1 Parquet Schema (4 Files)

### 1. `photometry_core.parquet`

Source: Extension 1 (PHOTOMETRY HOTCOLD AND SE++)

**Include (~85 scalar columns):**
- Identity & position: `id`, `segment_id`, `tile`, `ra`, `dec`, `x_image`, `y_image`
- Detection stats: `chi2_max`, `mode`, `fwhm`, `seg_area`
- Per-band scalar photometry (6 JWST+HST bands, 5 quantities each = 30 cols): `snr_*`, `wht_*`, `flux_auto_*`, `flux_err_auto_*`, `mag_auto_*`
- Compactness & surface brightness: `c_f444w`, `mu_max_*`
- Kron aperture params: `kron_rad`, `kron1_a`, `kron1_b`, `kron1_area`, `kron2_a`, `kron2_b`, `kron2_area`, `kron_corr`, `kron_f444w_psf_corr`, `kron_f770w_psf_corr`, `kron_f770w_ap_corr`
- Sérsic model params: `ra_model`, `dec_model`, `radius_sersic`, `radius_sersic_err`, `axratio_sersic`, `axratio_sersic_err`, `sersic`, `sersic_err`, `angle_sersic`, `angle_sersic_err`, `e1`, `e1_err`, `e2`, `e2_err`, `fmf_chi2`, `group_id`
- Flags: `flag_star`, `flag_star_hsc`, `flag_blend`, `warn_flag`
- Spec-z cross-match: `id_specz_khostovan25`
- Sérsic model magnitudes (37 bands): `mag_model_*` — keep these as they're scalar, useful for color computation

**Skip:**
- 18 array columns: `flux_aper_*`, `flux_err_aper_*`, `mag_aper_*` (each is float32[5] for 5 aperture diameters)
- Band-repeated `flux_model_*`, `flux_err-uncal_model_*`, `flux_err-cal_model_*` (redundant with mag_model when both are present; if needed later, Phase 2 can add them)

**Column name sanitization:** FITS column names contain hyphens (e.g., `mag_model_hst-f814w`). PostgreSQL doesn't allow hyphens in unquoted identifiers. Replace `-` with `_` in all column names during extraction (e.g., `mag_model_hst_f814w`). Apply this globally.

### 2. `lephare.parquet`

Source: Extension 2 (LEPHARE) — all 43 columns + `id` injected from Extension 1

Key columns for O1: `mass_med`, `sfr_med`, `ssfr_med`, `chi2_best`, `zfinal`, `zpdf_med`, `zpdf_l68`, `zpdf_u68`, `nbfilt`, `mod_minchi2_phys`

**Unit note:** All mass, SFR, sSFR, and age columns are in **log10** space (e.g., `mass_med` = log10(M/M_sun)).

No array columns. Small extension — take everything.

### 3. `cigale.parquet`

Source: Extension 4 (CIGALE) — all 54 columns + `id` injected from Extension 1

Key columns for O1: `mass`, `sfr_inst`, `sfr_100myr`, `chi2_best_fit`, `chi2_red_best_fit`

**Unit note:** All mass and SFR columns are in **linear** space (e.g., `mass` = M_sun, `sfr_inst` = M_sun/yr).

**Derived column:** Compute `ssfr_cigale = sfr_inst / mass` during extraction (CIGALE has no native sSFR column). Handle division by zero/NaN → NaN.

Missing `id` column in source extension — inject from Extension 1 by row position.

### 4. `morphology.parquet`

Source: Extension 5 (ML-MORPHO) — subset of 150 columns + `id` from Extension 1

**Include (~30 columns):**
- Mean class probabilities (3 bands × 4 classes = 12): `sph_f150w_mean`, `disk_f150w_mean`, `irr_f150w_mean`, `bd_f150w_mean`, and same for `_f277w_*` and `_f444w_*`
- Std deviations (same 12): `sph_f150w_std`, etc.
- Morphological flags: `morph_flag_f150w`, `morph_flag_f277w`, `morph_flag_f444w`
- Delta metrics: `delta_f150w`, `delta_f277w`, `delta_f444w`

**Skip:** 120 per-model-run probability columns (`sph_f444w_0`, `sph_f444w_1`, ..., `sph_f444w_9`, etc.) — these are individual CNN run outputs that the mean/std already summarize.

---

## PostgreSQL Schema

**Database:** `cosmos2025` on psql01 (10.25.20.8)
**Schema:** `catalog` (isolates our tables from any other databases on this server)

One table per parquet file, plus supplementary tables. All joined on `id` (BIGINT, PRIMARY KEY).

### Index Strategy

| Table | Indexes |
|-------|---------|
| All tables | PRIMARY KEY on `id` |
| `photometry_core` | `(ra, dec)` for spatial queries; `warn_flag` for quality filtering; `flag_star` for star exclusion |
| `lephare` | `zfinal` for redshift slicing; `mass_med` for mass binning |
| `cigale` | `mass` for cross-code comparison |
| `morphology` | `morph_flag_f444w` for class selection; `delta_f444w` for uncertainty filtering |
| `lss_overdensity` | `id` PK; `(ra, dec)` spatial; `density_excess` for range queries |
| `galaxy_groups` | `group_id`; `z` for redshift slicing |
| `galaxy_group_memberships` | `(galid, group_id)` composite PK; `galid`; `group_id` |

### Bulk Load Strategy

Parquet → psql via `COPY FROM` with CSV intermediary, or direct psycopg2 bulk insert from pyarrow tables. The dataset is under 1M rows — either approach completes in minutes.

---

## ETL Pipeline Architecture

```
FITS (8.4GB, memmap)
  ├── Read Extension 1 → extract id array (kept in memory for injection)
  ├── Read Extension 1 → select scalar columns → sanitize names → convert sentinels → write photometry_core.parquet
  ├── Read Extension 2 → inject id → sanitize names → convert sentinels → write lephare.parquet
  ├── Read Extension 4 → inject id → sanitize names → convert sentinels → derive ssfr_cigale → write cigale.parquet
  └── Read Extension 5 → inject id → select columns → sanitize names → convert sentinels → write morphology.parquet

Parquet files
  ├── CREATE SCHEMA catalog; CREATE TABLEs with proper types
  ├── Load each parquet → psql table via COPY or bulk insert
  └── CREATE INDEXes

Supplementary (LSS FITS + Group text files)
  ├── Read → convert → load to psql
  └── Index on id/group_id
```

### Technical Requirements

- Python 3.x with `astropy`, `numpy`, `pyarrow`, `psycopg2` (or `psycopg[binary]`), `pyyaml`, `python-dotenv`
- FITS reading via `astropy.io.fits` with `memmap=True` (critical — 8.4GB file)
- Parquet writing via `pyarrow.parquet`
- Chunk processing not strictly required (784k rows fits in memory once column-selected) but good practice

### Verification Queries (Run After Load)

```sql
-- Row counts must match
SELECT 'photometry_core' AS tbl, COUNT(*) FROM catalog.photometry_core
UNION ALL SELECT 'lephare', COUNT(*) FROM catalog.lephare
UNION ALL SELECT 'cigale', COUNT(*) FROM catalog.cigale
UNION ALL SELECT 'morphology', COUNT(*) FROM catalog.morphology;
-- All should return 784016

-- Null counts for sentinel columns (should be > 0, confirming conversion worked)
SELECT COUNT(*) FILTER (WHERE mass_med IS NULL) AS lephare_mass_null,
       COUNT(*) FILTER (WHERE chi2_best IS NULL) AS lephare_chi2_null
FROM catalog.lephare;

-- Cross-code join sanity check
-- NOTE: mass_med is already log10(M/M_sun); mass is linear M_sun
SELECT l.id, l.mass_med AS log_mass_lephare, LOG10(c.mass) AS log_mass_cigale,
       ABS(l.mass_med - LOG10(c.mass)) AS delta_log_mass
FROM catalog.lephare l
JOIN catalog.cigale c ON l.id = c.id
WHERE l.mass_med IS NOT NULL AND c.mass > 0
ORDER BY delta_log_mass DESC
LIMIT 20;

-- O5 environmental check (once LSS loaded)
SELECT COUNT(*) FROM catalog.lss_overdensity;
```

---

## Scope

**In scope:**
- PostgreSQL DDL for all 4 Phase 1 tables + 3 supplementary tables
- Python script: FITS → parquet (4 files)
- Python script: parquet → psql bulk load
- Sentinel-to-NULL conversion during extraction
- Column name sanitization (hyphens → underscores)
- `ssfr_cigale` derived column computation
- `id` injection into extensions that lack it
- Verification queries
- Index creation

**Out of scope (Phase 2+):**
- SE++APER extension (aperture photometry arrays)
- B+D extension (bulge-disk decomposition, 461 columns)
- SED file ingestion (784k individual FITS files, ~580GB total)
- Detection image extraction
- PDFz pickle processing (photo-z probability distributions)
- Feature engineering for anomaly detection
- Any analysis or science

---

## Key Reference Files

| What | Where |
|------|-------|
| Master catalog profile | `docs/reference/master-catalog-profile.md` |
| Column schema (Photometry) | `docs/reference/columns-photometry.txt` |
| Column schema (LePhare) | `docs/reference/columns-lephare-photometrric-redshifts.txt` |
| Column schema (CIGALE) | `docs/reference/columns-cigale-physical-parameters.txt` |
| Column schema (ML-Morpho) | `docs/reference/columns-machine-learning-morphological-classifications.txt` |
| Column schema (B+D) | `docs/reference/columns-bulge-disk-morphological-measurements.txt` |
| Quality flag definitions | `docs/reference/quality-flags.txt` |
| Profiling script | `src/etl/profile_master_catalog.py` |
| ETL script | `src/etl/extract_catalog.py` |
| Verification script | `src/etl/verify_catalog.py` |
| Verification report | `docs/verification-report.md` |
| AGENTS.md | Repository root |

---

## Document Info

| | |
|---|---|
| Author | CrainBramp + Claude (Opus 4.6) |
| Created | 2026-03-01 |
| Updated | 2026-04-05 (v1.1: fixed unit bug in verification query, updated paths and file references, added unit notes) |
| Status | Complete (ETL executed and verified) |
