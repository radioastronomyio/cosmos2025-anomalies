# Agent Instructions — COSMOS2025 Anomaly Detection

## Project Identity

Systematic anomaly detection on the COSMOS-Web DR1 photometric catalog (Shuntov et al. 2025). The catalog contains 784,016 sources across 0.54 deg² with 37-band photometry (JWST NIRCam + MIRI, HST, HSC, UltraVISTA, Subaru, Spitzer), two independent SED fitting codes (LePhare, CIGALE), ML morphological classifications, bulge-disk decomposition, and environmental context from supplementary group and large-scale structure catalogs. The goal is high-ROI scientific discoveries — objects or small populations that are novel and publishable — found through catalog-level feature analysis without proprietary data or spectroscopy.

## Current State

**Phase**: ETL execution
**Status**: Repository scaffolded, data organized and migrated to ML01, competitive landscape surveyed, opportunities selected (O1 + O5), master catalog profiled, ETL schema designed (DDL complete at `src/etl/create_schema.sql`), one-pager written for AI-assisted execution handoff.
**Next**: Create `cosmos2025` database on psql01 → execute DDL → write KC structured prompt for ETL script → execute ETL (FITS → parquet → psql) via CC/KC on ML01 → verify data integrity → begin O1/O5 exploratory analysis.
**Blockers**: None. CIGALE SED extraction complete (436GB, 784k files on desktop). LePhare SEDs archived as tar (not extracted, Phase 2).

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
│   └── research/                 # GDR results, ETL one-pager, opportunity analysis
├── notebooks/                    # Exploration, EDA, analysis
├── shared/                       # Cross-repo utilities (tree generator)
├── src/
│   ├── etl/                      # FITS → parquet → psql pipeline
│   ├── features/                 # Derived feature computation
│   ├── detection/                # Anomaly detection methods
│   └── utils/                    # Config loading, DB helpers
├── tests/
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

ETL output targets (created during pipeline execution):

```
/mnt/nvme02/cosmosweb2025-dr1/
├── processed/
│   ├── parquet/          # 4 parquet files (ETL output)
│   └── derived/          # Computed features, anomaly scores
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
| Database | psql01 (10.25.20.8) | PostgreSQL, `cosmos2025` database |

### Credentials

Database credentials are loaded from `/opt/agents/.env` on ML01. Scripts should use `dotenv` or shell sourcing, never hardcode connection strings. See `configs/data_paths.yaml` for env var names and path configuration.

## ETL Pipeline (Phase 1)

Master catalog → 4 parquet files → PostgreSQL tables. Extensions 3 (SE++APER) and 6 (B+D) skipped entirely.

| Parquet File | Source Extension | Columns | Notes |
|--------------|-----------------|---------|-------|
| `photometry_core.parquet` | 1 (Photometry) | ~85 scalar | Skip 18 array cols, ~200 band-repeated model fluxes |
| `lephare.parquet` | 2 (LePhare) | 43 + id | All columns, id injected from ext 1 |
| `cigale.parquet` | 4 (CIGALE) | 54 + id + ssfr_cigale | All columns, id injected, ssfr derived |
| `morphology.parquet` | 5 (ML-Morpho) | ~30 + id | Mean/std probs + flags + deltas only |

Sentinel conversion: `-999`/`-99`/`999999` → NULL. Column name sanitization: hyphens → underscores for PostgreSQL compatibility.

Full ETL specification: `docs/research/etl-pipeline-one-pager.md`

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Language | Python 3.x | All ETL, analysis, and pipeline code |
| Catalog I/O | astropy, pyarrow | FITS reading, parquet conversion |
| Database | PostgreSQL on psql01 (10.25.20.8) | `cosmos2025` database, catalog tables |
| DB access | psycopg2 | Direct connection, credentials from `/opt/agents/.env` |
| ML/Stats | scikit-learn, scipy | Isolation Forest, SOM, statistical tests |
| GPU compute | ML01 A4000 16GB (primary), desktop RTX 3080 12GB (secondary) | |
| Notebooks | Jupyter | Phase 1 exploration |
| AI execution | Claude Code / KiloCode on ML01 | ETL and pipeline code generation from structured prompts |

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
| ETL pipeline specification | `docs/research/etl-pipeline-one-pager.md` |
| Master catalog structural profile | `docs/reference/master-catalog-profile.md` |
| Catalog column schemas (6 extensions) | `docs/reference/columns-*.txt` |
| Quality flag definitions | `docs/reference/quality-flags.txt` |
| LSS overdensity catalog schema | `docs/reference/large-scale-structure-in-cosmos-web-readme.txt` |
| COSMOS-Web primary catalog readme | `docs/reference/cosmos-web-primary-readme.pdf` |
