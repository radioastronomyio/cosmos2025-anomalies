<!--
---
title: "v1 to v1.1 Delta"
description: "Column-level, row-level, and ID-space classification between the v1 evidence base and the v1.1 holdings"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-16"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: cosmos-web
  - domain: data-engineering
  - tech: postgresql
related_documents:
  - "[v1.1 Structural Profile](master-catalog-profile-v1.1.md)"
  - "[v1 Profile (historical)](master-catalog-profile.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# v1 to v1.1 Delta

Classification of every column and every source ID between v1 (documented profile + live psql01 load) and v1.1 (local holdings). Generator: `src/inspection/diff_v1_v11.py` (run 2026-08-16 under `doppler run`); full machine record in the gate 1.9 worklog checkpoint and `staging/v1-v11-delta.json`.

Evidence sources: documented v1 inventories (`columns-*.txt`), live `information_schema` for the four loaded tables, v1.1 generated inventories (`columns-v1.1-*.txt`).

---

## 1. Column Classification per Extension

| Extension | v1 documented | v1.1 | Unchanged | Renamed | Removed | Added | Sum check (U+Rn+Rm = v1) |
|-----------|--------------:|-----:|----------:|--------:|--------:|------:|:------------------------:|
| PHOTOMETRY HOTCOLD AND SE++ | 287 | 287 | 287 | 0 | 0 | 0 | ✓ |
| LEPHARE | 43 | 43 | 43 | 0 | 0 | 0 | ✓ |
| SE++APER | 148 | 148 | 148 | 0 | 0 | 0 | ✓ |
| CIGALE | 54 | 56 | 54 | 0 | 0 | **2** | ✓ |
| ML-MORPHO | 150 | 150 | 150 | 0 | 0 | 0 | ✓ |
| B+D | 461 | 461 | 461 | 0 | 0 | 0 | ✓ |
| GALIGHT-MORPHO | — | 204 | — | — | — | 204 | (no v1 counterpart) |

**The only column-level change across the six shared extensions: CIGALE gains `ebv_stars` and `ebv_stars_err`.** Verified against the live load: neither column exists in `catalog.cigale` (information_schema), so these are genuine v1.1 additions, not a v1 documentation gap. No renames claimed (none needed: every non-added column matches by exact name). No dtype changes: every common column's v1.1 FITS format maps to its loaded PostgreSQL type (D→double precision, E→real, J/K→integer/bigint, A→text).

## 2. Row-Count Deltas

| Extension / table | v1 loaded rows | v1.1 rows | Delta |
|-------------------|---------------:|----------:|------:|
| PHOTOMETRY → `photometry_core` | 784,016 | 784,016 | 0 |
| LEPHARE → `lephare` | 784,016 | 784,016 | 0 |
| SE++APER (not loaded in v1) | — | 784,016 | — |
| CIGALE → `cigale` | 784,016 | 784,016 | 0 |
| ML-MORPHO → `morphology` | 784,016 | 784,016 | 0 |
| B+D (not loaded in v1) | — | 784,016 | — |
| GALIGHT-MORPHO (new) | — | 784,016 | — |
| AGNCAT / AUXDATA (new, reference file) | — | 17,995,599 | — |

## 3. ID-Space Delta (set operations, not assumption)

v1.1 PHOTOMETRY `id` column (read from `COSMOSWeb_mastercatalog_v1.1_photom_primary.fits`, memmap) set-compared against `SELECT id FROM catalog.photometry_core` via `numpy.intersect1d` / `setdiff1d`:

| Quantity | Count |
|----------|------:|
| v1 live IDs | 784,016 |
| v1.1 IDs | 784,016 |
| **Retained** (in both) | **784,016** |
| Dropped (v1 only, absent from v1.1) | 0 |
| New (v1.1 only, absent from v1) | 0 |

The source population is unchanged: v1.1 is a reprocessing of the same 784,016 detections, which is what makes the gate 1.10 value comparison a clean per-source join with zero ID reconciliation.

## 4. What the v1 Load Actually Carried (information_schema evidence)

| Table | DB columns | Composition vs FITS |
|-------|-----------:|---------------------|
| `photometry_core` | 158 | 158 of 287; band-repeated aperture/model flux triples skipped (129) |
| `lephare` | 44 | all 43 FITS columns + `id` |
| `cigale` | 56 | all 54 v1 FITS columns + `id` + derived `ssfr_cigale`; **no** `ebv_stars*` |
| `morphology` | 31 | 30 of 150; band-repeated morphology probabilities skipped (120) |

Loaded-name convention: FITS hyphens → underscores (`hst-f814w` → `hst_f814w`); `id` keys each table.
