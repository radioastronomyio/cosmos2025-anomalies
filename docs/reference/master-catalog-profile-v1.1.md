<!--
---
title: "COSMOS-Web Master Catalog Structural Profile (v1.1)"
description: "HDU, row-count, and column-level structure of the local v1.1 FITS holdings"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-16"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: cosmos-web
  - tech: astropy
related_documents:
  - "[Data Manifest v1.1](data-manifest-v1.1.md)"
  - "[v1 Profile (historical)](master-catalog-profile.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# COSMOS-Web Master Catalog Structural Profile (v1.1)

Machine-derived structure of the v1.1 holdings at `/mnt/nvme01/cosmos-web-dr1-catalog` (pinned by [data-manifest-v1.1.md](data-manifest-v1.1.md)). Generator: `src/inspection/profile_v11.py`; run 2026-08-16. Every count below is read from the FITS headers, not from release notes.

---

## 1. Master Catalog Extension Count: 7

`COSMOSWeb_mastercatalog_v1.1.fits` carries **seven table extensions** (plus the empty primary), enumerated by EXTNAME:

| # | EXTNAME | Rows | Columns |
|---|---------|------:|--------:|
| 1 | PHOTOMETRY HOTCOLD AND SE++ | 784,016 | 287 |
| 2 | LEPHARE | 784,016 | 43 |
| 3 | SE++APER | 784,016 | 148 |
| 4 | CIGALE | 784,016 | 56 |
| 5 | ML-MORPHO | 784,016 | 150 |
| 6 | B+D | 784,016 | 461 |
| 7 | GALIGHT-MORPHO | 784,016 | 204 |

The v1 documented profile records six extensions (PHOTOMETRY, LEPHARE, SE++APER, CIGALE, ML-MORPHO, B+D). The seventh v1.1 extension is **GALIGHT-MORPHO**, also shipped as a standalone per-extension product (`COSMOSWeb_mastercatalog_v1.1_galight_morph.fits`). Readiness-review finding F1 consumes this evidence.

---

## 2. Per-Extension Products

Each standalone product mirrors its master-catalog HDU **exactly**, same EXTNAME, row count, and column list, verified name-by-name identical to the master HDU:

| File | EXTNAME | Rows | Columns | Master HDU |
|------|---------|------:|--------:|:----------:|
| `..._photom_primary.fits` | PHOTOMETRY HOTCOLD AND SE++ | 784,016 | 287 | 1 |
| `..._photom_secondary.fits` | SE++APER | 784,016 | 148 | 3 |
| `..._lephare.fits` | LEPHARE | 784,016 | 43 | 2 |
| `..._cigale.fits` | CIGALE | 784,016 | 56 | 4 |
| `..._ml_morph.fits` | ML-MORPHO | 784,016 | 150 | 5 |
| `..._bulgedisk.fits` | B+D | 784,016 | 461 | 6 |
| `..._galight_morph.fits` | GALIGHT-MORPHO | 784,016 | 204 | 7 |

Structural distinction between the photometry products (readiness finding F5): **primary = hot+cold SE++ model photometry** (EXTNAME "PHOTOMETRY HOTCOLD AND SE++", 287 columns, the v1 lineage loaded as `photometry_core`); **secondary = SE++ aperture photometry** ("SE++APER", 148 columns, non-PSF-homogenized apertures per the v1 documentation).

## 3. AGN/DESI Cross-Identification File

`agngal_desi.fits` carries two tables, both 17,995,599 rows:

| # | EXTNAME | Rows | Columns |
|---|---------|------:|--------:|
| 1 | AGNCAT | 17,995,599 | 36 |
| 2 | AUXDATA | 17,995,599 | 58 |

Row count is ~23× the COSMOS-Web source count: this is an all-sky (or wide-field) AGN/DESI reference cross-identification product, not a per-COSMOS-source table. ETL v2 mapping treats it accordingly (readiness review).

## 4. Other Holdings (header level only)

| Family | Files | Shape | BITPIX |
|--------|------:|-------|--------|
| JWST star masks (`cosmos_web_starmask_jwst_*.fits`) | 20 | 19200 × 24910 | 8 |
| Detection images (`detection_images/detection_chi2pos_SWLW_*.fits`) | 20 | 19200 × 24910 | -32 |

Plus: `cosmos2020_starmask_hsc.reg` (DS9 region file), LePhare PDFz pickle and SEDs HDF5 (not FITS), arXiv paper source, column-description text, and the two supplement directories (profiled at the value level in the readiness review).

---

## 5. Column Inventories

Machine-generated inventories (name, FITS format, unit), regeneration-diffed byte-identical against the committed files (`python src/inspection/profile_v11.py --check`):

| Inventory | Source |
|-----------|--------|
| [columns-v1.1-photometry-hotcold-and-seplusplus.txt](columns-v1.1-photometry-hotcold-and-seplusplus.txt) | ext 1 |
| [columns-v1.1-lephare.txt](columns-v1.1-lephare.txt) | ext 2 |
| [columns-v1.1-seplusplusaper.txt](columns-v1.1-seplusplusaper.txt) | ext 3 |
| [columns-v1.1-cigale.txt](columns-v1.1-cigale.txt) | ext 4 |
| [columns-v1.1-ml-morpho.txt](columns-v1.1-ml-morpho.txt) | ext 5 |
| [columns-v1.1-bplusd.txt](columns-v1.1-bplusd.txt) | ext 6 |
| [columns-v1.1-galight-morpho.txt](columns-v1.1-galight-morpho.txt) | ext 7 (new) |
| [columns-v1.1-agncat.txt](columns-v1.1-agncat.txt) | agngal_desi ext 1 |
| [columns-v1.1-auxdata.txt](columns-v1.1-auxdata.txt) | agngal_desi ext 2 |

The v1 `columns-*.txt` files remain untouched as the historical baseline for the gate 1.9 delta.
