# Agent Instructions — COSMOS2025 Anomaly Detection

## Project Identity

Systematic anomaly detection on the COSMOS-Web DR1 photometric catalog (Shuntov et al. 2025). The catalog contains 784,016 sources across 0.54 deg² with 37-band photometry (JWST NIRCam + MIRI, HST, HSC, UltraVISTA, Subaru, Spitzer), two independent SED fitting codes (LePhare, CIGALE), ML morphological classifications, bulge-disk decomposition, and environmental context from supplementary group and large-scale structure catalogs. The goal is high-ROI scientific discoveries — objects or small populations that are novel and publishable — found through catalog-level feature analysis without proprietary data or spectroscopy.

## Current State

**Phase**: Phase 1 complete. Phase 2 (feature engineering) ready to begin.
**Status**: All 7 catalog tables loaded and verified on psql01. ETL pipeline (`src/etl/extract_catalog.py`) executed successfully: 784,016 rows across 4 core tables, 164,155 LSS sources, 1,678 galaxy groups, 1,745,652 group memberships. Verification report generated (`docs/verification-report.md`) with 47 passed, 0 failed across 93 checks covering row counts, sentinel residuals, NULL distributions, cross-table join integrity, unit validation, value ranges, and O1 readiness. Codex pre-commit review completed (`docs/research/phase1-precommit-codex-review.md`).
**Next**: Phase 2 feature engineering. Define CIGALE plausibility filter (mass > 1e3, chi2 thresholds) to exclude zombie fits. Compute T_A tension scalars (Δlog M★, Δlog SFR, Δlog sSFR) for the dual-code clean sample. Begin O1 exploratory analysis.
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
| Codex pre-commit review | `docs/research/phase1-precommit-codex-review.md` |
| ETL pipeline specification | `docs/research/etl-pipeline-one-pager.md` |
| Master catalog structural profile | `docs/reference/master-catalog-profile.md` |
| Catalog column schemas (6 extensions) | `docs/reference/columns-*.txt` |
| Quality flag definitions | `docs/reference/quality-flags.txt` |
| LSS overdensity catalog schema | `docs/reference/large-scale-structure-in-cosmos-web-readme.txt` |
| COSMOS-Web primary catalog readme | `docs/reference/cosmos-web-primary-readme.pdf` |
