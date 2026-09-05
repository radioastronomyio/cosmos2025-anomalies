<!--
---
title: "COSMOS2025 Anomaly Detection"
description: "Systematic anomaly detection on the COSMOS-Web DR1 photometric catalog — exploiting tension between independent measurements to find scientifically valuable outliers"
author: "VintageDon"
date: "2026-08-18"
version: "1.0"
status: "ETL v2 Verified; Operator Cutover Pending"
tags:
  - type: project-root
  - domain: [astronomy, anomaly-detection, data-science]
  - tech: [python, postgresql, astropy, scikit-learn, jwst]
related_documents:
  - "[COSMOS-Web DR1 Catalog](https://cosmos-web.astro.caltech.edu/)"
  - "[RadioAstronomy.io Organization](https://github.com/radioastronomyio)"
  - "[Project Roadmap](ROADMAP.md)"
  - "[ARD Framework](https://github.com/radioastronomyio/analysis-ready-dataset)"
---
-->

# 🔭 COSMOS2025 Anomaly Detection

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql)](https://postgresql.org)
[![JWST](https://img.shields.io/badge/Data-JWST_COSMOS--Web_DR1-orange)](https://cosmos-web.astro.caltech.edu/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

![COSMOS2025 anomaly detection](assets/icon.svg)

> Systematic anomaly detection on the COSMOS-Web DR1 galaxy catalog — hunting for high-value scientific discoveries in the largest contiguous JWST survey to date.

This project applies outlier detection methods to the COSMOS-Web v1.1
photometric catalog (Shuntov et al. 2025), a 784,016-source dataset spanning
37 photometric bands from UV through mid-infrared. The verified
`cosmos2025_v11.source` mirror preserves all twelve release and supplement
tables. The next science stage exploits *tension between independent
measurements* after operator approval of MetaMCP cutover and T_A v2.

Each source receives a multi-component **tension vector** quantifying disagreement across four axes:

- **T_A — Algorithmic Tension:** LePhare vs CIGALE residuals in stellar mass, SFR, and sSFR. Catastrophic disagreements (Δlog M* > 0.3 dex, Δlog SFR > 0.5 dex) signal extreme emission line galaxies, obscured AGN, or decoupled UV/IR star formation.
- **T_z — Redshift Tension:** Photo-z PDF pathology — multimodal distributions, zpdf vs zchi2 divergence, space-only vs full photo-z inconsistencies — exploiting the 26 GB PDF(z) pickle that most published work discards for "clean" samples.
- **T_M — Morphological Tension:** High-confidence ML classifications that contradict SED type — confident spheroids that are strongly star-forming (Blue Nugget candidates), confident disks that are quenched (Passive Disk candidates) — filtered by the catalog's `delta` uncertainty metric.
- **T_E — Environmental Tension:** Galaxy properties cross-referenced against LSS density maps and group membership to find contextual outliers — massive starbursts in cluster cores, quenched dwarfs in cosmic voids.

Objects with high tension across *multiple* axes are "super-anomalies" — the primary targets for the ranked candidate list. The pipeline also produces a parallel community data product: an **Analysis Ready Dataset** (ARD) that materializes the tension metrics for reuse by other researchers. See the [Project Roadmap](ROADMAP.md) for the full opportunity landscape, phased execution plan, and ARD output track.

The project is catalog-only — no image-level analysis, no spectroscopy, no proprietary data. Everything is derived from publicly available COSMOS-Web DR1 data products.

---

## 📊 Project Status

| Area | Status | Description |
|------|--------|-------------|
| Data acquisition | ✅ Complete | v1.1 holdings pinned by the repository SHA-256 manifest; raw sources remain immutable |
| Literature landscape | ✅ Complete | Independent deep research surveys (Gemini, GPT) converged on tension-first strategy; four-axis tension vector defined |
| Catalog profiling | ✅ Complete | Seven master extensions plus five supplement/spec-z products sealed in a 1,448-row dictionary |
| ETL execution | ✅ Complete | Twelve lossless mirrors plus provenance loaded into `cosmos2025_v11.source` |
| ETL verification | ✅ Complete | Source pins, schema, values, provenance, analyst permissions, and v1 identity passed Gates 3.5–3.11; P2R-04 spec-z linkage unit passed Gates 4.1–4.6 |
| Runtime cutover | ⏳ Pending approval | MetaMCP cutover and direct analyst HBA validation remain operator actions |
| Feature engineering | ⏳ Pending approval | T_A v2 design follows cutover; v1 Phase 2 products remain historical evidence only |
| Anomaly detection | 🔲 Planned | Isolation Forest, SOM-based density estimation on tension features |
| Characterization | 🔲 Planned | Phase 2 — SED-level analysis of top candidates |
| ARD release | 🔲 Planned | Tension scalars + anomaly scores packaged as community data product |

---

## 🏗️ Architecture

### Current data boundary

The release-driven ETL reads immutable v1.1 artifacts into seven master
mirrors, three environmental supplement tables, and the two-table Khostovan
spec-z compilation (galaxy-level `specz_compilation_unique` and
measurement-level `specz_compilation_all`). `source.provenance` records the
twelve source registrations separately. The
read-only `cosmos2025_v11_ro` role is the runtime boundary; cleaned or derived
science products belong in a future `analysis` schema.

The retained architecture and dataset infographics under `assets/` describe
the retired v1 pipeline and are intentionally not presented as current.

### Compute Environment

| Stage | Environment | Hardware |
|-------|-------------|----------|
| ETL, exploration, feature engineering | ML01 bare metal | 5950X / 128G / A4000 16GB |
| Catalog queries | psql01 (cluster VM) | `cosmos2025_v11.source` read-only mirror; `cosmos2025.catalog` v1 baseline |
| SED characterization (Phase 2) | Desktop workstation | RTX 3080 12GB |

---

## 📁 Repository Structure

```
cosmos2025-anomalies/
├── assets/                       # Banner images, diagrams
├── configs/                      # Data paths, DB connection, parameters
├── docs/
│   ├── reference/                # Column schemas, quality flags, catalog profile
│   └── research/                 # GDR results, ETL one-pager, Codex review
├── notebooks/                    # Exploration, EDA, analysis
├── shared/                       # Cross-repo utilities (tree generator)
├── spec/                         # Repository-local completed-spec archive/index
├── src/
│   ├── etl/                      # FITS → parquet → psql pipeline
│   ├── features/                 # Derived feature computation
│   ├── detection/                # Anomaly detection methods
│   └── utils/                    # Config loading, DB helpers
├── tests/
├── work-logs/                    # Date-based session logs
├── AGENTS.md                     # Agent instructions and project context
├── ROADMAP.md                    # Opportunity landscape, execution plan, ARD track
└── README.md                     # This file
```

Data is stored outside the repository — see [AGENTS.md](AGENTS.md) for path conventions and the data layout on ML01.

---

## 🔬 Dataset: COSMOS-Web DR1 v1.1

The master catalog provides seven aligned extensions per source: primary
photometry, non-PSF-homogenized aperture photometry, LePhare, CIGALE, machine-
learning morphology, bulge/disk morphology, and Galight morphology.
Supplementary catalogs add Hatamnia overdensity, Toni groups and memberships,
and the Khostovan spec-z compilation. See
[`schema-v11.md`](docs/reference/schema-v11.md) for the complete generated
1,416-column source-mirror reference.

### Data Products

| Data Product | Source | Size | Phase 1 Use |
|--------------|--------|------|-------------|
| Master catalog (7 extensions) | Shuntov et al. 2025 | 8.4 GB | Seven lossless source mirrors |
| Galaxy group catalog | Toni et al. 2025 | ~1 MB | O5 environmental context |
| LSS overdensity catalog | Hatamnia et al. 2025 | 289 MB | O5 environmental context |
| Spec-z compilation | Khostovan et al. | 261,975 galaxy / 482,579 measurement rows | Calibration/validation evidence; sample definition deferred to operator disposition of the linkage review surface |
| CIGALE best-fit SEDs | Shuntov et al. 2025 | 436 GB (extracted) | Phase 2 characterization |
| LePhare best-fit SEDs | Shuntov et al. 2025 | 141 GB (compressed) | Phase 2 characterization |
| LePhare PDFz distributions | Shuntov et al. 2025 | 26 GB | Phase 2 — T_z tension metrics |
| Detection images (20 tiles) | COSMOS-Web DR1 | 31 GB | Not used — catalog-only project |

---

## 📦 Dual Output: Science Paper + Analysis Ready Dataset

The anomaly detection pipeline produces two outputs serving different audiences:

**Science paper** — A "Tension Catalog" interpreting the top anomaly candidates: classifying them into physical categories (Line Imposters, Dusty Decoupling, Blue Nuggets, Passive Disks, environmental outliers), proposing formation scenarios, and recommending spectroscopic follow-up targets.

**Analysis Ready Dataset** — The tension scalars, anomaly scores, and ranked lists *without* interpretation, packaged as a reusable community data product following the [ARD methodology](https://github.com/radioastronomyio/analysis-ready-dataset). Every researcher working with COSMOS2025 who wants to assess cross-code consistency must independently compute Δlog M★, ΔSFR, χ² ratios, photo-z PDF metrics, and morphology-SED contradiction scores. This ARD front-loads that compute cost once with documented methodology.

The ARD layers map directly to pipeline phases: the verified v1.1 source mirror
in PostgreSQL (Layer 0), future T_A v2 tension scalars (Layer 1), anomaly scores
and SOM embeddings (Layer 2), and environmental context joins (Layer 3). See
the [Project Roadmap](ROADMAP.md) for the historical layer framing; execution
of T_A v2 remains pending operator approval.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ with astropy, pyarrow, numpy, psycopg2
- PostgreSQL access to psql01 (see [AGENTS.md](AGENTS.md) for connection details)
- COSMOS-Web DR1 data products (login-gated at [cosmos-web.astro.caltech.edu](https://cosmos-web.astro.caltech.edu/))

### Setup

```bash
git clone https://github.com/radioastronomyio/cosmos2025-anomalies.git
cd cosmos2025-anomalies

# Install dependencies
pip install astropy pyarrow numpy psycopg2-binary scipy scikit-learn jupyter pyyaml python-dotenv

# Configure data paths (see AGENTS.md for expected data layout)
# Edit configs/data_paths.yaml with your data root paths
```

### Data Access

The COSMOS-Web DR1 catalog is publicly available but requires a login. Download all catalog products and organize per the data layout documented in [AGENTS.md](AGENTS.md).

---

## 🌟 Open Science Philosophy

We practice open science and open methodology — our version of "showing your work":

- Research methodologies are fully documented and repeatable
- All analysis is performed on publicly available data products
- Scripts and pipelines are published so others can reproduce, verify, or extend results
- Anomaly candidate lists will be published with full provenance

---

## 📄 License

- **Code**: [MIT License](LICENSE)
- **Data/Content**: [CC-BY-4.0](LICENSE-DATA)

---

## 🙏 Acknowledgments

- **COSMOS-Web Team** — Shuntov, Casey, Kartaltepe, Koekemoer et al. for the DR1 catalog
- **Toni et al.** — Galaxy group catalog
- **Hatamnia et al.** — Large-scale structure overdensity maps
- [RadioAstronomy.io](https://github.com/radioastronomyio) — Research infrastructure
- **ARD Methodology** — [Analysis Ready Dataset framework](https://github.com/radioastronomyio/analysis-ready-dataset)

---

Last Updated: August 18, 2026 | ETL v2 Verified; Operator Cutover Pending
