<!--
---
title: "Data Manifest v1.1"
description: "SHA-256 pin of the COSMOS-Web v1.1 holdings and the spec-z compilation checkout"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-16"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Project State](../project-state.md)"
  - "[v1.1 Structural Profile](master-catalog-profile-v1.1.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# Data Manifest v1.1

Provenance anchor for the v1.1 rebuild. Machine layer: [data-manifest-v1.1.csv](data-manifest-v1.1.csv) (184 rows: SHA-256, bytes, mtime UTC per file). Builder: `src/inspection/build_data_manifest.py` (read-only against the roots). Generated 2026-08-16T03:32:50Z. **Nothing under either hashed root may change after this point; a single modified byte unpins every downstream artifact.**

---

## 1. Provenance Roots

| # | Root | Location | Files | Bytes | Role |
|---|------|----------|------:|------:|------|
| 1 | NVMe v1.1 holdings | `/mnt/nvme01/cosmos-web-dr1-catalog` | 103 | 130,197,210,900 | Hashed here; raw and immutable |
| 2 | speczcompilation checkout | `/opt/agents/repos/reference-files/speczcompilation` | 81 | 245,107,236 | Hashed here; git HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0` |
| 3 | CIGALE SEDs (external) | host `vps3557752`, path `/opt/agents/repos/cosmosweb2025-data/CIGALE_SEDs_v1/` | — | ~175 GB | **Off-box; recorded by name only, not hashed** |

Row-count verification (manifest vs filesystem, run 2026-08-16):

```
find /mnt/nvme01/cosmos-web-dr1-catalog -type f | wc -l   → 103
find /opt/agents/repos/reference-files/speczcompilation -type f | wc -l → 81
manifest rows: 184 = 103 + 81
```

Re-hash verification: three randomly chosen files (seed 20260815) re-hashed and compared against the manifest — `cosmos_web_starmask_jwst_B1.fits`, `COSMOSWeb_mastercatalog_v1.1_ml_morph.fits`, `logo/cosmos-logo-light.png` — all three reproduce the recorded SHA-256 and byte size exactly.

---

## 2. LFS Materialization Status (finding F-LFS)

The speczcompilation checkout's `.gitattributes` LFS-tracks `*.fits` and `*.pkl`. **All seven LFS-pattern files are unmaterialized pointer files (133–134 bytes each), not data.** `git-lfs` is not installed on ML01 and no materialized copy of any of these files exists elsewhere on-box (searched `/mnt/nvme01` and `/opt/agents`). Materialization requires operator action (git-lfs install + network fetch from `github.com/cosmosastro/speczcompilation`), outside executor authority.

Expected content per pointer (oid and true size from the pointer text):

| File | Expected SHA-256 (from pointer) | Expected bytes |
|------|--------------------------------|---------------:|
| `specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | `6ffd1145...336e99` | 70,223,040 |
| `specz_compilation/specz_compilation_COSMOS_DR1.1_all.fits` | `30675493...68fd3` | 129,343,680 |
| `sed_fitting/cigale/cigale_results_specz_compilation_DR1.1.fits` | `43bd6bb6...e37710` | 309,882,240 |
| `sed_fitting/lephare/lephare_results_specz_compilation_DR1.1.fits` | `555487d5...dd1b3` | 49,271,040 |
| `soms/trained_som_lowz_i_band_26.0_magnitude_limit.pkl` | `2784dd9a...f12b28` | 359,235,918 |
| `soms/trained_som_midz_i_band_26.0_magnitude_limit.pkl` | `4e3f9c03...62296` | 359,533,902 |
| `soms/trained_som_highz_i_band_26.0_magnitude_limit.pkl` | `c1ded80b...6b052` | 24,265,414 |

The manifest hashes the pointer files as they exist on disk; after operator materialization the seven rows must be regenerated and the summary updated.

**`*_unique.fits` row count: not obtainable on-box.** astropy open attempt fails with `No SIMPLE card found, this file does not appear to be a valid FITS file` — the file is the 133-byte pointer, not the 70 MB catalog its pointer describes. Spec-z join readiness (gate 1.11) and readiness-review finding F6 inherit this blocker; see the readiness review for the closed question.

---

## 3. Holdings Shape (top-level)

103 files: 10 master/per-extension catalog FITS + AGN-DESI cross-id FITS, PDFz pickle, LePhare SEDs HDF5, 25 JWST star-mask FITS + 1 DS9 region file, 20 detection images + README, arXiv paper source (LaTeX + 29 figures), column-description text, flag-construction PNG, flowchart PNG, LSS supplement (catalog + readme), group supplements (groups, memberships).

Disk-hygiene observations recorded for the operator (no action taken; raw root is immutable): none — the holdings directory contains no redundant archives or stray downloads at manifest time.
