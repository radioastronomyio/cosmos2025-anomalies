# COSMOS-Web DR1 ETL Pipeline — Schema Design & AI-Assisted Execution

**Domain:** Astronomy / Data Engineering
**Status:** Ready for schema design → code generation
**Date:** 2026-03-01
**Version:** 1.0

---

## Vision

Design the PostgreSQL schema and FITS-to-parquet-to-psql ETL pipeline for the COSMOS-Web DR1 master catalog, then hand off code generation to GLM 4.7 via KiloCode with crystaldb Postgres MCP access. We define every decision; the model writes the code.

---

## Project Context

COSMOS-Web DR1 is the largest contiguous JWST imaging survey — 784,016 sources, 0.54 deg², 37-band photometry (JWST NIRCam + MIRI, HST, HSC, UltraVISTA, Subaru, Spitzer), with two independent SED fitting codes (LePhare, CIGALE), ML morphological classifications, and environmental context catalogs.

We are building an anomaly detection research pipeline targeting two primary science opportunities:

**O1 — Algorithmic Disagreement:** Mining residuals between LePhare and CIGALE physical parameter estimates (stellar mass, SFR) to find objects that "break" standard SED fitting. The dual-code framing is genuinely novel for COSMOS-Web. Δlog(M*) > 0.3 dex or Δlog(SFR) > 0.5 dex signal physically distinct objects — extreme emission line galaxies, obscured AGN, or decoupled UV/IR star formation.

**O5 — Contextual Anomalies:** Cross-referencing galaxy properties against large-scale structure density maps to find environmental outliers — massive starbursts in cluster cores, quenched dwarfs in voids. Uses the Hatamnia et al. (2025) LSS overdensity catalog and Toni et al. (2025) group catalog as environmental inputs.

The ETL pipeline exists to make the master catalog queryable in PostgreSQL for these analyses. Everything downstream (feature engineering, anomaly scoring, candidate characterization) depends on this being done correctly.

---

## Source Data

### Master Catalog

**File:** `COSMOSWeb_mastercatalog_v1.fits` (8.4 GB)
**Location:** `E:\repositories-data-folder\cosmos-web-dr1-2025\raw\catalogs\`

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
| LSS Overdensity | `hatamnia_lss_v1.fits` | `E:\...\raw\supplementary\` | ~164k sources | `density_excess` values for O5 environmental context |
| Galaxy Groups | Toni et al. group catalog | `E:\...\raw\supplementary\` | 1,678 groups | `group_id`, `prob_assoc` for O5 membership |

### Output Locations

| Product | Location |
|---------|----------|
| Parquet files | `E:\...\processed\parquet\` |
| PostgreSQL | psql01 (10.25.20.8), database `cosmos2025` |
| Staging/temp | `E:\...\staging\` |

---

## Sentinel Value Mapping

These sentinel patterns are consistent across the catalog. The ETL must convert all sentinels to NULL in both parquet and psql.

| Sentinel | Meaning | Found In |
|----------|---------|----------|
| `-999` / `-999.0` | No measurement | mag_err, model parameters across all extensions |
| `-99` / `-99.0` | No redshift solution | LePhare `zfinal`, `mod_minchi2_phys` |
| `999999` | No classification | ML-MORPHO `morph_flag` variants |
| `0.0` in `wht_*` columns | No coverage for that band | Photometry extension (55% of sources lack MIRI F770W) |
| NaN | Genuine missing (source couldn't be fit) | CIGALE has 16.1% NaN across all columns |

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

No array columns. Small extension — take everything.

### 3. `cigale.parquet`

Source: Extension 4 (CIGALE) — all 54 columns + `id` injected from Extension 1

Key columns for O1: `mass`, `sfr_inst`, `sfr_100myr`, `chi2_best_fit`, `chi2_red_best_fit`

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
| `lss_overdensity` | `id` PK; whatever spatial/redshift columns the catalog uses |
| `galaxy_groups` | `group_id`; `id` for member lookup |

Consider PostGIS for spatial indexing on (ra, dec) if cross-match queries become frequent.

### Bulk Load Strategy

Parquet → psql via `COPY FROM` with CSV intermediary, or direct psycopg2/psycopg3 bulk insert from pyarrow tables. The dataset is under 1M rows — either approach completes in minutes.

---

## ETL Pipeline Architecture

```
FITS (8.4GB, memmap)
  ├── Read Extension 1 → extract id array (kept in memory for injection)
  ├── Read Extension 1 → select scalar columns → sanitize names → convert sentinels → write photometry_core.parquet
  ├── Read Extension 2 → inject id → sanitize names → convert sentinels → write lephare.parquet
  ├── Read Extension 4 → inject id → sanitize names → convert sentinels → derive ssfr_cigale → write cigale.parquet
  └── Read Extension 5 → inject id → select columns → sanitize names → convert sentinels → write morphology.parquet

Parquet files (E:\...\processed\parquet\)
  ├── CREATE SCHEMA catalog; CREATE TABLEs with proper types
  ├── Load each parquet → psql table via COPY or bulk insert
  └── CREATE INDEXes

Supplementary FITS (LSS, Groups)
  ├── Read → convert → load to psql
  └── Index on id/group_id
```

### Technical Requirements

- Python 3.x with `astropy`, `numpy`, `pyarrow`, `psycopg2` (or `psycopg[binary]`)
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
SELECT l.id, l.mass_med AS mass_lephare, c.mass AS mass_cigale,
       ABS(LOG10(l.mass_med) - LOG10(c.mass)) AS delta_log_mass
FROM catalog.lephare l
JOIN catalog.cigale c ON l.id = c.id
WHERE l.mass_med > 0 AND c.mass > 0
ORDER BY delta_log_mass DESC
LIMIT 20;

-- O5 environmental check (once LSS loaded)
SELECT COUNT(*) FROM catalog.lss_overdensity;
```

---

## AI Execution Strategy

### Model Choice: GLM 4.7 (not GLM 5)

**Because:** The task is well-bounded code generation from a precise specification, not open-ended reasoning. GLM 4.7 excels at focused coding with tool use (SWE-bench verified #1 among open models, +16.5% Terminal Bench). GLM 5's advantages (deeper multi-step planning, 744B params) don't justify the 3× cost increase ($0.95 vs $0.30/M input tokens) for execution of a fully-specified plan.

### Tool Access: crystaldb Postgres MCP

Run locally as Docker container pointed at psql01:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URI=postgresql://user:pass@10.25.20.8:5432/cosmos2025 \
  crystaldba/postgres-mcp --access-mode=unrestricted --transport=sse
```

Configure KiloCode MCP client to connect at `http://localhost:8000/sse`. This gives GLM 4.7 ability to: create schemas/tables, execute SQL, run COPY commands, verify row counts, create indexes, and run spot-check queries — all through the MCP interface.

**Safety:** Scoped to the `cosmos2025` database only. Cannot touch any other databases on psql01.

### Division of Labor

| We Design (Human + Claude) | GLM 4.7 Executes |
|----------------------------|-------------------|
| This one-pager (complete ETL spec) | Python FITS → parquet conversion script |
| PostgreSQL DDL (table definitions, types, constraints) | SQL DDL execution via MCP |
| Column inclusion/exclusion lists | Parquet → psql bulk load script |
| Sentinel-to-NULL mapping rules | Verification queries |
| Verification query definitions | Index creation |
| Structured prompt packaging all of the above | Bug fixes if verification fails |

### Risk: Drift

The primary risk with AI-generated ETL is the model "improving" something we didn't ask for — different sentinel handling, creative column renaming, reordering that breaks row alignment. Mitigation: the structured prompt pins every decision, and the verification queries catch discrepancies. If row counts don't match or null patterns are wrong, we catch it immediately.

---

## Scope

**In scope:**
- PostgreSQL DDL for all 4 Phase 1 tables + 2 supplementary tables
- Python script: FITS → parquet (4 files)
- Python script or SQL: parquet → psql bulk load
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

**Deferred decisions:**
- PostGIS for spatial indexing (evaluate after initial queries reveal need)
- pgvector for embedding storage (Phase 2 if we vectorize SEDs)
- Partitioning strategy (784k rows doesn't need it, but revisit if derived tables grow)

---

## Next Steps

1. **Design DDL** — Write CREATE TABLE statements for all 6 tables with exact column names, types, constraints, and indexes
2. **Write structured prompt** — Package this one-pager + DDL into a kc-structured-prompt for GLM 4.7
3. **Spin up crystaldb MCP** — Docker container on local machine pointing at psql01
4. **Execute** — GLM 4.7 writes and runs the ETL scripts via KiloCode
5. **Verify** — Run verification queries, check row counts, spot-check values
6. **Load supplementary** — Hatamnia LSS + Toni groups into psql
7. **Begin O1 analysis** — First exploratory queries on LePhare vs CIGALE residuals

---

## Key Reference Files

| What | Where |
|------|-------|
| Master catalog profile | `docs/reference/master-catalog-profile.md` |
| Column schema (Photometry) | `docs/reference/columns-photometry-and-sepp-measurements.txt` |
| Column schema (LePhare) | `docs/reference/columns-lephare-physical-parameters.txt` |
| Column schema (CIGALE) | `docs/reference/columns-cigale-physical-parameters.txt` |
| Column schema (ML-Morpho) | `docs/reference/columns-ml-morphological-classification.txt` |
| Column schema (B+D) | `docs/reference/columns-bulge-disk-morphological-measurements.txt` |
| GDR opportunity landscape | `docs/research/COSMOS-Web_Anomaly_Detection_Opportunity.md` (to be placed) |
| Quality flag definitions | `docs/reference/quality-flags.txt` |
| Profiling script | `src/etl/profile_master_catalog.py` |
| AGENTS.md | Repository root |

---

## Document Info

| | |
|---|---|
| Author | CrainBramp + Claude (Opus 4.6) |
| Created | 2026-03-01 |
| Version | 1.0 |
| Status | Ready for schema design |

---

## Sources

- COSMOS-Web DR1 master catalog profiling (this session, 2026-03-01)
- GDR competitive landscape analysis (Gemini Deep Research, 2026-02-07)
- GLM 4.7 vs GLM 5 comparison research (WaveSpeedAI, CometAPI, Vertu reviews)
- crystaldb/postgres-mcp documentation (GitHub)
- Prior session: repo scaffolding, data organization, AGENTS.md creation (2026-02-07)
