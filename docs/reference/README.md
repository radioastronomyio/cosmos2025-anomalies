<!--
---
title: "Reference"
description: "Catalog column schemas, structural profiles, pinned manifests, and unit conventions"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: cosmos-web
related_documents:
  - "[Project State](../project-state.md)"
---
-->

# Reference

Lookup material for the catalog data: column schemas, structural profiles, the pinned data manifest, unit conventions, and upstream documentation. The v1 documents are the historical record for the retired v1 load; the v1.1 documents are the live evidence base for ETL v2.

---

## 1. Contents

```
reference/
├── columns-*.txt                                  # v1 column inventories (historical)
├── master-catalog-profile.md                      # v1 structural profile (historical)
├── master-catalog-profile-v1.1.md                 # v1.1 structural profile (live)
├── data-manifest-v1.1.md / data-manifest-v1.1.csv # SHA-256 pin of the v1.1 holdings
├── sentinel-candidates-v11.md                     # Gate 3.3 generated observations
├── unit-conventions.md                            # log10 vs linear cross-code rules
├── quality-flags.txt                              # flag definitions
├── large-scale-structure-in-cosmos-web-readme.txt # LSS supplement readme
├── cosmos-web-primary-readme.pdf                  # upstream catalog readme
└── README.md                                      # This file
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [unit-conventions.md](unit-conventions.md) | Verbatim cross-code delta formula and error-propagation rules | ✅ Active |
| [master-catalog-profile.md](master-catalog-profile.md) | Documented v1 profile; historical baseline for the v1→v1.1 delta | 🗄️ Archived |
| [master-catalog-profile-v1.1.md](master-catalog-profile-v1.1.md) | v1.1 extension/column structural profile | ✅ Active |
| [data-manifest-v1.1.md](data-manifest-v1.1.md) | SHA-256 manifest summary for the v1.1 holdings | ✅ Active |
| [v1-to-v11-delta.md](v1-to-v11-delta.md) | Column, row, and ID-space classification, v1 to v1.1 | ✅ Active |
| [parameter-migration-evidence-v1.1.md](parameter-migration-evidence-v1.1.md) | CIGALE/LePhare value comparison against the live v1 tables | ✅ Active |
| [sentinel-candidates-v11.md](sentinel-candidates-v11.md) | Generated FITS-mask, NaN, documented-sentinel, and conservative candidate observations | ✅ Active |
| [quality-flags.txt](quality-flags.txt) | Upstream quality flag definitions | ✅ Active |
| [columns-photometry.txt](columns-photometry.txt) | v1 photometry column inventory | 🗄️ Archived |
| [columns-lephare-photometrric-redshifts.txt](columns-lephare-photometrric-redshifts.txt) | v1 LePhare column inventory | 🗄️ Archived |
| [columns-cigale-physical-parameters.txt](columns-cigale-physical-parameters.txt) | v1 CIGALE column inventory | 🗄️ Archived |
| [columns-machine-learning-morphological-classifications.txt](columns-machine-learning-morphological-classifications.txt) | v1 ML morphology column inventory | 🗄️ Archived |
| [columns-bulge-disk-morphological-measurements.txt](columns-bulge-disk-morphological-measurements.txt) | v1 bulge-disk column inventory | 🗄️ Archived |
| [columns-non-psf-homogenized-aperture-photometry.txt](columns-non-psf-homogenized-aperture-photometry.txt) | v1 non-PSF-homogenized photometry inventory | 🗄️ Archived |
| [large-scale-structure-in-cosmos-web-readme.txt](large-scale-structure-in-cosmos-web-readme.txt) | LSS overdensity supplement readme | ✅ Active |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Documentation](../README.md) | Parent directory |
| [Unit Conventions](unit-conventions.md) | Read before computing any cross-code quantity |
