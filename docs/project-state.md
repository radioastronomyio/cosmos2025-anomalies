<!--
---
title: "Project State"
description: "Current phase, database inventory, data holdings, and environment for cosmos2025-anomalies"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: data-engineering
  - domain: documentation
  - tech: python
  - tech: postgresql
related_documents:
  - "[Unit Conventions](reference/unit-conventions.md)"
  - "[Science Opportunities](research/science-opportunities.md)"
  - "[v1.1 Readiness Review](research/v11-readiness-review.md)"
---
-->

# Project State

Operating state of `cosmos2025-anomalies`: phase, live database inventory, data holdings, and compute environment. AGENTS.md links here for everything time-sensitive; this document is the router target for current-state narrative and table inventories.

---

## 1. Phase and Posture

The project restarted on 2026-08-15. The v1 catalog is retired as the source of truth; the rebuild on v1.1 (ETL v2) is designed but not approved, and it dispatches only after the operator approves the readiness review produced by spec P2R-01 (`docs/research/v11-readiness-review.md`).

Until ETL v2 lands, the live v1 database objects below are the comparison baseline and are read-only by policy. No DDL or DML runs against psql01 outside an approved spec.

Open items the restart addresses, carried from the May/July diagnostic work as frozen inputs to the T_A v2 design unit (not facts to re-verify, not defects to fix in passing):

- The ~0.24 dex conditional mass offset between LePhare and CIGALE (unconditional `t_mass` mean -1.001 with `sigma_sys_mass = 0.1` dex, per the May report).
- The censoring-dominated SFR tension ranking: the analysis sample gates on `sfr_inst > 0 AND sfr_100myr > 0`, so `t_sfr_100` is **not** well calibrated as a ranking statistic despite its bulk pull statistics (mean 0.302, std 0.980) looking nominal: the top of the ranking is dominated by sources censored near the positivity floor. The phrase "well calibrated" does not apply to `t_sfr_100` without this qualification.
- The dimensionally incoherent `chi2_ratio` column in `catalog.tension_scalars` (a ratio of LePhare `chi2_best` to CIGALE `chi2_red_best_fit`, which are not commensurable quantities). It stays as recorded; its repair is a T_A v2 decision.

---

## 2. Live Database Inventory (psql01, v1 baseline)

Database `cosmos2025`, schema `catalog`, host psql01 (10.25.20.8). Credentials injected from Doppler `ml01/prd`; scripts read environment variables per the config contract in `configs/data_paths.yaml`. Read-only until ETL v2.

### Phase 1 tables (v1 ETL, complete)

| Table | Source | Rows | Notes |
|-------|--------|------:|-------|
| `catalog.photometry_core` | Master catalog ext 1 (Photometry) | 784,016 | 158 scalar columns. Array columns and band-repeated `flux_model` skipped. |
| `catalog.lephare` | Master catalog ext 2 (LePhare) | 784,016 | 44 columns. Values in **log10** space (see unit conventions). |
| `catalog.cigale` | Master catalog ext 4 (CIGALE) | 784,016 | 56 columns. Values in **linear** space. 24.9% NULL (unfittable). |
| `catalog.morphology` | Master catalog ext 5 (ML-Morpho) | 784,016 | 31 columns. 42.1% NULL morph_flags. |
| `catalog.lss_overdensity` | Hatamnia et al. | 164,155 | `density_excess` (1+delta). 20.9% coverage of full catalog. |
| `catalog.galaxy_groups` | Toni et al. | 1,678 | Groups to z=3.7. |
| `catalog.galaxy_group_memberships` | Toni et al. | 1,745,652 | 364,674 unique galaxies across 1,678 groups. |

Sentinel conversion (`-999`/`-99`/`999999` → NULL) happened at extraction. Column-name sanitization: hyphens → underscores.

### Phase 2 products (T_A v1, superseded by pending T_A v2)

| Object | Type | Rows | Notes |
|--------|------|------:|-------|
| `catalog.v_analysis_sample` | Materialized view | 553,830 | One-column `id` filter view. Four plausibility gates: catalog security, convergence, physical plausibility, information content (`nbfilt >= 5`). No chi2 threshold. |
| `catalog.tension_scalars` | Persistent table | 553,830 | 20 columns: raw cross-code deltas, propagated uncertainties, `t_mass` / `t_sfr_inst` / `t_sfr_100`, chi2 context (including the known-defective `chi2_ratio`), `has_f770w`, `is_quiescent_lp`. |

Diagnostics of record: `docs/phase2-tension-diagnostic-report.md` (2026-05-02 run).

---

## 3. Data Holdings (v1.1)

The v1 catalog file set is retired (path retirement recorded in the P2R-01 worklog). The project now runs on the v1.1 holdings downloaded 2026-08-14/15, pinned by the SHA-256 manifest at `docs/reference/data-manifest-v1.1.md` (machine layer: `data-manifest-v1.1.csv`). Structural characterization: `docs/reference/master-catalog-profile-v1.1.md`.

| Root | Contents |
|------|----------|
| `/mnt/nvme01/cosmos-web-dr1-catalog/` | v1.1 master catalog and per-extension FITS products (photom primary/secondary, LePhare, CIGALE, bulge-disk, galight/ML morphology, AGN-DESI cross-id), LePhare PDFz pickle and SEDs HDF5, detection images, star masks, column descriptions, arXiv paper source, supplements (`hatamnia-lss/`, `toni/`). Raw and immutable. |
| `reference-files/speczcompilation` (operator-stated) | Spec-z compilation checkout (Khostovan et al.), LFS-backed; absolute path and HEAD SHA pinned in the manifest. |
| `vps3557752:/opt/agents/repos/cosmosweb2025-data/CIGALE_SEDs_v1/` | Off-box CIGALE per-source SEDs (~175 GB). Not downloaded; deferred. Per-source lookups for candidate characterization, never bulk-loaded. |

The retired desktop holdings (`D:\...` SED archives) are no longer referenced; retirement recorded in the P2R-01 worklog.

---

## 4. Repository Layout

```
cosmos2025-anomalies/
├── assets/                       # Banner images, diagrams
├── configs/                      # data_paths.yaml: paths, DB env contract
├── docs/
│   ├── documentation-standards/  # Templates, tagging vocabulary, style guide
│   ├── reference/                # Column schemas, manifests, profiles, flags
│   └── research/                 # GDR results, ETL one-pager, reviews
├── internal-files/               # Human source materials (gitignored)
├── notebooks/                    # Exploration, EDA
├── recycle-bin/                  # Agent trash can (README tracked, contents ignored)
├── spec/                         # Active work specs; YYYY-MM/ archive
├── src/
│   ├── etl/                      # v1 FITS → parquet → psql pipeline
│   ├── features/                 # Derived feature computation
│   ├── inspection/               # v1.1 structural inspection utilities (P2R-01)
│   ├── detection/                # Anomaly detection methods (future)
│   └── utils/                    # Config loading, DB helpers
├── tests/
├── work-logs/                    # Date-based session logs
├── AGENTS.md                     # Agent instructions and work-spec contract
├── CLAUDE.md                     # Points at AGENTS.md
└── README.md
```

---

## 5. Compute Environment

| Environment | Role | Compute |
|-------------|------|---------|
| ML01 (primary) | Repo at `/opt/agents/repos/cosmos2025-anomalies`, v1.1 holdings, shared venv `/opt/agents/venv/` | 5950X / 128G / A4000 16GB |
| psql01 (10.25.20.8) | PostgreSQL, `cosmos2025` database, `catalog` schema | Read-only baseline until ETL v2 |
| vps3557752 (storage server) | Off-box SED archive root | Not an execution host |

---

## 6. Key Reference Files

| What | Where |
|------|-------|
| Data path configuration | `configs/data_paths.yaml` |
| v1.1 pinned data manifest | `docs/reference/data-manifest-v1.1.md` |
| v1.1 structural profile | `docs/reference/master-catalog-profile-v1.1.md` |
| v1 documented profile (historical) | `docs/reference/master-catalog-profile.md` |
| v1 column schemas (historical) | `docs/reference/columns-*.txt` |
| Unit conventions (log10 vs linear) | `docs/reference/unit-conventions.md` |
| Phase 2 tension diagnostics (May run) | `docs/phase2-tension-diagnostic-report.md` |
| ETL verification report (v1) | `docs/verification-report.md` |
| Codex pre-commit review (Phase 1) | `docs/research/phase1-precommit-codex-review.md` |
| ETL pipeline specification (v1) | `docs/research/etl-pipeline-one-pager.md` |
| Quality flag definitions | `docs/reference/quality-flags.txt` |
| LSS overdensity schema | `docs/reference/large-scale-structure-in-cosmos-web-readme.txt` |
