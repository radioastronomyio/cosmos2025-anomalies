# Agent Instructions — COSMOS2025 Anomaly Detection

## Project Identity

Systematic anomaly detection on the COSMOS-Web DR1 photometric catalog (Shuntov et al. 2025). The catalog contains 784,016 sources across 0.54 deg² with 37-band photometry (JWST NIRCam + MIRI, HST, HSC, UltraVISTA, Subaru, Spitzer), two independent SED fitting codes (LePhare, CIGALE), ML morphological classifications, bulge-disk decomposition, and environmental context from supplementary group and large-scale structure catalogs. The goal is high-ROI scientific discoveries — objects or small populations that are novel and publishable — found through catalog-level feature analysis without proprietary data or spectroscopy.

## Current State

**Phase**: Phase 2 in progress. Plausibility filter and T_A tension scalars computed.
**Status**: All 7 Phase 1 catalog tables remain loaded and verified on psql01. Phase 2 feature engineering has started: materialized view `catalog.v_analysis_sample` defines the clean analysis sample with 553,830 sources from 784,016 total. The view applies four plausibility gates: catalog security (`warn_flag = 0`, `type = 0`, `flag_star_hsc = 0`), convergence (CIGALE mass and SFR not NULL), physical plausibility (CIGALE mass > 1e6, LePhare `mass_med > 6.0`, CIGALE SFR > 0), and information content (`nbfilt >= 5`). No chi2 threshold is applied; quality assessment is absorbed into the error-normalized tension metric. Persistent table `catalog.tension_scalars` stores per-source error-normalized tension metrics (`t_mass`, `t_sfr_inst`, `t_sfr_100` primary), raw deltas, propagated uncertainties, chi2 context, and quality metadata (`has_f770w`, `is_quiescent_lp`). Diagnostic report generated at `docs/phase2-tension-diagnostic-report.md`.
**Diagnostic findings**: `sigma_sys_mass = 0.1` dex and `sigma_sys_sfr = 0.2` dex are empirically adequate. `t_mass` has a systematic offset (mean = -1.0) reflecting known inter-code mass bias (CIGALE approximately 0.23 dex higher than LePhare). `t_sfr_100` is well calibrated (mean = 0.30, std = 0.98). `sfr_100myr` is confirmed as the primary SFR metric over `sfr_inst` because top-1000 ranking instability is 37.7%.
**Next**: Remaining tension components: T_z redshift, T_M morphological, and T_E environmental. Then Phase 3 anomaly detection.
**Blockers**: None.

**Critical unit note**: LePhare physical parameters (mass_med, sfr_med, ssfr_med) are in **log10** space. CIGALE parameters (mass, sfr_inst, ssfr_cigale) are in **linear** space. Cross-code comparison formula: `delta = lephare_log10_value - LOG10(cigale_linear_value)`. See `docs/verification-report.md` for full unit reference table.

## Science Opportunities

Two primary targets selected from five GDR-identified opportunities:

**O1 — Algorithmic Disagreement (Lead paper):** LePhare vs CIGALE residuals for stellar mass and SFR. Objects with Δlog(M*) > 0.3 dex or Δlog(SFR) > 0.5 dex signal physically distinct populations — extreme emission line galaxies ("Line Imposters"), obscured AGN, or decoupled UV/IR star formation ("Dusty Decoupling"). Pure catalog operations, least scoopable, dual-code framing genuinely novel for COSMOS-Web.

**O5 — Contextual Anomalies:** Environmental outliers found by cross-referencing galaxy properties against LSS density maps. Cluster starbursts (massive SF galaxies in highest-density peaks) and void quenched galaxies (low-mass passive in voids). Pairs naturally with O1 — objects anomalous in BOTH dimensions are "super-anomalies."

**Deprioritized:** O2 (Morphological Imposters — enrichment only, dust degeneracy trap), O3 (Low-Delta Uncertainty — secondary analysis), O4 (Green Peas — too close to dropout searches).

## Repository Structure

```
cosmos2025-anomalies/
├── assets/                       # Banner images, diagrams
├── configs/                      # data_paths.yaml, DB connection, parameters
├── docs/
│   ├── reference/                # Column schemas, quality flags, catalog profile
│   └── research/                 # GDR results, ETL one-pager, Codex review
├── notebooks/                    # Exploration, EDA, analysis
├── shared/                       # Cross-repo utilities (tree generator)
├── spec/                         # KC/OC structured prompts for agent execution
├── src/
│   ├── etl/                      # FITS → parquet → psql pipeline
│   ├── features/                 # Derived feature computation
│   │   └── compute_tension_scalars.py
│   ├── detection/                # Anomaly detection methods
│   └── utils/                    # Config loading, DB helpers
├── tests/
├── work-logs/                    # Date-based session logs
├── AGENTS.md                     # This file
└── README.md
```

## Data Location

Catalog data and repo both live on ML01. SED archives remain on the desktop (too large to migrate until NAS or fs02 capacity is addressed).

### ML01 — Primary execution environment

| Path | Contents |
|------|----------|
| `/opt/repos/cosmos2025-anomalies/` | Repository (cloned from GitHub) |
| `/mnt/nvme02/cosmosweb2025-dr1/` | Catalog data root |

```
/mnt/nvme02/cosmosweb2025-dr1/
├── catalogs/             # COSMOSWeb_mastercatalog_v1.fits (8.4GB), PDFz pickle (26GB)
├── images/               # Detection images, segmentation maps (not used Phase 1)
├── calibration/          # PSFs, star masks (not used Phase 1)
├── supplementary/        # Toni group catalog, Hatamnia LSS (hatamnia_lss_v1.fits)
└── reference-originals/  # Original download page HTML and docs (archived)
```

ETL output (populated by pipeline):

```
/mnt/nvme02/cosmosweb2025-dr1/
├── processed/
│   ├── parquet/          # 4 parquet files (photometry_core, lephare, cigale, morphology)
│   └── derived/          # Computed features, anomaly scores (Phase 2)
└── staging/              # ETL temp workspace, disposable
```

### Desktop — SED data only (Phase 2)

| Path | Contents |
|------|----------|
| `D:\repositories-data-folder\cosmos-web-dr1-2025\raw\seds\CIGALE_SEDs_v1\` | ~784k individual best-fit SED FITS files (~436GB) |
| `D:\repositories-data-folder\cosmos-web-dr1-2025\raw\seds\LePHARE_SEDs_v1\` | ~141GB tar, not extracted |

SED files are per-source lookups for Phase 2 candidate characterization, not bulk-loaded into psql.

### Environment Summary

| Environment | Data | Compute |
|-------------|------|---------|
| ML01 (primary) | Catalogs, supplementary, images, calibration at `/mnt/nvme02/cosmosweb2025-dr1/` | 5950X / 128G / A4000 16GB |
| Desktop (secondary) | SED archives only (`D:\`) | RTX 3080 12GB |
| Database | psql01 (10.25.20.8) | PostgreSQL, `cosmos2025` database, `catalog` schema |

### Credentials

Database credentials are loaded from `/opt/agents/.env` on ML01. Scripts should use `dotenv` or shell sourcing, never hardcode connection strings. See `configs/data_paths.yaml` for env var names and path configuration.

## ETL Pipeline (Phase 1 — Complete)

Master catalog → 4 parquet files → PostgreSQL tables. Extensions 3 (SE++APER) and 6 (B+D) skipped entirely.

| Table | Source Extension | Rows | Notes |
|-------|-----------------|------|-------|
| `catalog.photometry_core` | 1 (Photometry) | 784,016 | 158 scalar columns. Array cols and band-repeated flux_model skipped. |
| `catalog.lephare` | 2 (LePhare) | 784,016 | 44 columns. id injected from ext 1. Values in **log10** space. |
| `catalog.cigale` | 4 (CIGALE) | 784,016 | 56 columns. id injected, ssfr_cigale derived. Values in **linear** space. 24.9% NULL (unfittable). |
| `catalog.morphology` | 5 (ML-Morpho) | 784,016 | 31 columns. Mean/std probs + flags + deltas. 42.1% NULL morph_flags. |
| `catalog.lss_overdensity` | Hatamnia et al. | 164,155 | density_excess (1+delta). 20.9% coverage of full catalog. |
| `catalog.galaxy_groups` | Toni et al. | 1,678 | Groups to z=3.7. |
| `catalog.galaxy_group_memberships` | Toni et al. | 1,745,652 | 364,674 unique galaxies across 1,678 groups. |

Sentinel conversion: `-999`/`-99`/`999999` → NULL. Column name sanitization: hyphens → underscores for PostgreSQL compatibility. Verification report: `docs/verification-report.md`.

Full ETL specification: `docs/research/etl-pipeline-one-pager.md`

## Feature Engineering (Phase 2)

The first Phase 2 data products are live on psql01. They define the plausibility-filtered analysis sample and the first Analysis Ready Dataset scalar layer for algorithmic disagreement.

| Object | Type | Rows | Notes |
|--------|------|------|-------|
| `catalog.v_analysis_sample` | Materialized view | 553,830 | One-column `id` filter view. Four plausibility gates applied; no chi2 threshold. Refreshable after view redefinition. |
| `catalog.tension_scalars` | Persistent table | 553,830 | 20 columns. Stores raw cross-code deltas, propagated uncertainties, `t_mass`, `t_sfr_inst`, `t_sfr_100`, chi2 context, F770W coverage, and LePhare quiescent flag. |

Diagnostic report: `docs/phase2-tension-diagnostic-report.md`. Script: `src/features/compute_tension_scalars.py`.

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Language | Python 3.x | All ETL, analysis, and pipeline code |
| Catalog I/O | astropy, pyarrow | FITS reading, parquet conversion |
| Database | PostgreSQL on psql01 (10.25.20.8) | `cosmos2025` database, `catalog` schema, 7 tables |
| DB access | psycopg2 | Direct connection, credentials from `/opt/agents/.env` |
| ML/Stats | scikit-learn, scipy | Isolation Forest, SOM, statistical tests |
| GPU compute | ML01 A4000 16GB (primary), desktop RTX 3080 12GB (secondary) | |
| Notebooks | Jupyter | Exploration and EDA |
| AI execution | Claude Code / KiloCode / OpenCode on ML01 | Pipeline code generation from structured prompts |

## Conventions

- Interior READMEs in every directory — the repo should speak for itself
- Column schemas and data documentation live in `docs/reference/`, not inline
- Raw data is immutable — never modify files under `raw/`
- Config-driven paths — no hardcoded data paths in source code
- Sentinel values converted to NULL at extraction time, not downstream

## Key Reference Files

| What | Where |
|------|-------|
| Data path configuration | `configs/data_paths.yaml` |
| ETL verification report | `docs/verification-report.md` |
| Phase 1 verification (HTML with charts) | `docs/phase1-verification-report.html` |
| Phase 2 tension diagnostic report | `docs/phase2-tension-diagnostic-report.md` |
| Codex pre-commit review | `docs/research/phase1-precommit-codex-review.md` |
| ETL pipeline specification | `docs/research/etl-pipeline-one-pager.md` |
| Master catalog structural profile | `docs/reference/master-catalog-profile.md` |
| Catalog column schemas (6 extensions) | `docs/reference/columns-*.txt` |
| Quality flag definitions | `docs/reference/quality-flags.txt` |
| LSS overdensity catalog schema | `docs/reference/large-scale-structure-in-cosmos-web-readme.txt` |
| COSMOS-Web primary catalog readme | `docs/reference/cosmos-web-primary-readme.pdf` |
