<!--
---
title: "COSMOS2025 Project Roadmap"
description: "Consolidated opportunity landscape, phased execution plan, and ARD output track"
author: "CrainBramp"
date: "2026-04-05"
version: "0.2"
status: "Active"
tags:
  - type: roadmap
  - domain: [astronomy, anomaly-detection, data-science]
related_documents:
  - "[README.md](README.md)"
  - "[AGENTS.md](AGENTS.md)"
  - "[ARD Framework](https://github.com/radioastronomyio/analysis-ready-dataset)"
  - "[Gemini Deep Research — Opportunity Landscape](staging/gemini-deep-research-cosmosweb-dr1-opportunities.md)"
  - "[GPT Deep Research — Opportunity Landscape](staging/gpt-deep-research-cosmosweb-dr1-opportunities.md)"
---
-->

# COSMOS2025 Project Roadmap

> Anomaly detection on the COSMOS-Web DR1 catalog, with a parallel output track producing an Analysis Ready Dataset for the community.

This document synthesizes competitive landscape research from two independent deep research surveys (Gemini, GPT — February 2026) into a consolidated opportunity map, defines the phased execution plan, and frames the ARD as a natural byproduct of the anomaly detection pipeline.

---

## 1. Consolidated Opportunity Landscape

Two independent deep research agents surveyed the COSMOS-Web DR1 publication landscape and converged on the same core finding: the highest-ROI anomaly detection strategy exploits **tension between independent measurements** already present in the catalog. Both ranked cross-code disagreement mining as the #1 opportunity and produced nearly identical "avoid" lists.

### 1.1 Claimed Territory — Do Not Enter

These science cases are saturated or owned by active teams working the same public data products. Entering these spaces without a clearly differentiated selection axis risks producing unpublishable work.

| Territory | Claimed By | Why It's Closed |
|-----------|-----------|-----------------|
| Little Red Dots — discovery, abundance, basic properties | Akins et al. 2025 | Large COSMOS-Web LRD sample with AGN vs stellar interpretation; multiple follow-on papers including stacked mid-IR/ALMA evidence |
| F150W-dropout / dust-obscured galaxies | Manning et al. 2025 (SCUBADive II) | Systematic candidate search already published |
| Population-level morphology evolution | Huertas-Company et al. 2025 | "Emergence of the Hubble Sequence" — occupies the broad morphology novelty space |
| Morphology-dependent stellar mass functions | Shuntov et al. 2025b | SMF evolution split by star-forming/quiescent and morphology |
| Galaxy size/compactness evolution | Ono et al. 2025 | Claims structural scaling relation space across wide redshift range |
| Galaxy group finding (z < 3.7) | Toni et al. 2025 | AMICO group catalog is a published product — the "group catalog slot" is filled |
| Large-scale structure density mapping | Hatamnia et al. 2025 | Density maps to z ~ 7 are released products |
| Dual AGN identification | Li et al. 2025 | Catalog of dual AGN candidates exists; requires PSF subtraction beyond catalog-only scope |

**Implication:** Broad population papers ("we found rare dusty galaxies / rare compacts / rare LRD-like objects") are not viable unless the novelty is in the *selection axis* itself — i.e., multi-product disagreement intersections that are methodologically distinct from what these papers do.

### 1.2 Opportunity Matrix — Selected and Ranked

The combined research surface identifies 7–8 distinct anomaly axes. We select a primary target (O1), a complementary conditioning axis (O5), and two additional feature dimensions that integrate into the same pipeline without expanding scope.

#### Primary: O1 — Cross-Code Algorithmic Disagreement

**What:** Systematic mining of LePhare vs CIGALE residuals for stellar mass, SFR, and sSFR. Objects where the codes disagree catastrophically (Δlog M★ > 0.3 dex, Δlog SFR > 0.5 dex) while photometry quality is high and morphology is "real" (not uncertain/noisy).

**Why it works:** The core team's publications emphasize *consistency* between codes for the bulk population. The disagreement tails are explicitly discarded or averaged out. No published work systematically mines these tails into a ranked candidate list with physical interpretation.

**Physics targets:**

- "Line Imposters" — extreme [OIII] boosting F444W flux; LePhare reads massive old stellar continuum while CIGALE identifies the line excess. Result: Δlog M★ >> 0, candidate EELGs.
- "Dusty Decoupling" — heavily obscured starbursts invisible in optical but bright in MIRI F770W; LePhare (optical-driven) fits low SFR while CIGALE (energy balance) forces high SFR. Result: Δlog SFR >> 0, candidate obscured AGN or starbursts.
- Template failure modes — objects where *both* codes produce high χ² but disagree on *why* the templates fail.

**Key columns:** `mass_med` vs `mass` (CIGALE), `sfr_med` vs `sfr_inst`, `chi2_best` vs `chi2_best_fit`, `chi2_agn`, `nbfilt`, quality flags.

**Competitive assessment:** High novelty. "Disagreement tail mining" is methodologically distinct from SMFs, morphology evolution, and LRD searches. Produces both a science paper and a community-useful "warning list."

#### Complementary: O5 — Environmental Context as Conditioning Axis

**What:** Cross-referencing per-source tension metrics against LSS density maps (`density_excess` from Hatamnia et al.) and group membership probabilities (Toni et al.) to find objects that are anomalous in *both* intrinsic properties and environmental context.

**Why it works:** Environment papers establish average trends (quiescent fraction increases with density). We're not claiming a trend — we're finding the *exceptions*: massive starbursts in cluster cores, quenched dwarfs in cosmic voids. Objects anomalous on O1 metrics AND environmental metrics are "super-anomalies."

**Key columns:** `density_excess` (join by COSMOS2025 `id`), group `prob_assoc`, combined with O1 tension features.

**Competitive assessment:** Moderate. Pure environment claims are crowded, but "context + multi-product contradiction" is underexploited and differentiated.

#### Additional Tension Dimensions (Same Pipeline, More Columns)

These are not separate opportunities — they are additional feature engineering targets that enrich the tension vector without requiring new pipelines.

**Photo-z PDF Pathology:** Sources with broad/multimodal PDF(z), strong zpdf_med vs zchi2 disagreement, or space-only vs full photo-z inconsistencies. The full PDF(z) pickle is already downloaded (26 GB). Most published work discards ambiguous photo-z objects to get "clean" samples — that discarded space is the signal. Features: PDF width (`zpdf_u68 - zpdf_l68`), multimodality metrics from the pickle, space-vs-all divergence. An object where codes disagree on mass AND the photo-z is multimodal is a much stronger anomaly candidate than either signal alone.

**Morphology-SED Contradiction (Delta-Filtered):** Confident spheroids (low `delta_f444w`) that are strongly star-forming, or confident disks with quiescent SEDs. The `delta` metric (difference between top two ML class probabilities) is a uniquely valuable feature of this catalog that almost nobody exploits — standard analyses filter out low-confidence objects. Here we filter *in* high-confidence objects whose SED type contradicts their morphology. These are the Blue Nuggets (compaction events) and Passive Disks (evidence for strangulation/halo quenching) that test formation physics. Risk mitigation: use `Av_best` and MIRI F770W to distinguish "old red" from "dusty red."

#### Deprioritized (Known but Deferred)

| Opportunity | Disposition | Reason |
|-------------|-------------|--------|
| Structural decomposition anomalies (`fmf_b+d_chi2`) | Phase 2 | Data is in the bulge-disk extension we're already loading; interesting but separate analysis |
| AGN-template tension beyond LRDs | Phase 2 | `chi2_agn` vs `chi2_best` catalog available; risk of adjacency to LRD territory |
| Photometric Green Peas at z > 5 | Not pursued | Targeted population search rather than general anomaly hunt; needs precise filter transmission modeling |

### 1.3 The Tension Vector Architecture

Following the Gemini research framing, each source in the quality-filtered catalog receives a multi-dimensional tension score:

| Component | Symbol | Source Features |
|-----------|--------|-----------------|
| Algorithmic tension | T_A | Δlog M★, ΔSFR, ΔsSFR, χ² ratios (LePhare vs CIGALE) |
| Redshift tension | T_z | PDF width, multimodality index, zpdf_med vs zchi2, space-vs-all divergence |
| Morphological tension | T_M | High-confidence morphology-SED contradiction (delta-filtered) |
| Environmental tension | T_E | Density excess extremes, group membership context |

Objects with high values across *multiple* components are "super-anomalies" — the primary target for the candidate list. The component decomposition also enables independent analysis of each tension axis and interpretation of *why* an object is anomalous.

### 1.4 Methodological Precedents

| Method | Precedent | Application Here |
|--------|-----------|------------------|
| Isolation Forest | Baron & Poznanski 2017 (SDSS); Broadbelt et al. 2025 (GAMA E+A) | Universal outlier scoring on tension feature space |
| Self-Organizing Maps | Abedini et al. 2025 (COSMOS-Web parameter estimation) | Density estimation — empty/high-QE nodes as anomaly signal. Distinct from Abedini's regression use. |
| UMAP candidate pooling | Euclid/JADES high-z quiescent search 2025 | Manifold learning to isolate rare classes, then SED validation |
| Active Anomaly Discovery | SNAD PineForest; O'Ryan & Gomez AnomalyMatch 2025 | Active learning loop: rank → inspect via FitsMap → label → re-rank |

---

## 2. Phased Execution Plan

### Phase 1: Foundation (Complete)

**Objective:** Quality-filtered COSMOS2025 catalog queryable in PostgreSQL with all extensions joined.

| Task | Status | Detail |
|------|--------|--------|
| Data acquisition | ✅ Complete | All DR1 catalog products downloaded |
| Catalog profiling | ✅ Complete | 6 extensions characterized, sentinel patterns mapped |
| ETL schema design | ✅ Complete | 4-file parquet schema + PostgreSQL DDL |
| ETL execution | ✅ Complete | FITS → Parquet → psql via OpenCode/KC on ML01. 784,016 rows across 4 core tables. |
| Supplementary catalog ingest | ✅ Complete | 164,155 LSS sources, 1,678 groups, 1,745,652 memberships loaded |
| Data integrity verification | ✅ Complete | 93 checks (47 pass, 0 fail). Sentinels, joins, units, ranges verified. |

**Exit criteria (met):** `SELECT count(*) FROM catalog.photometry_core WHERE warn_flag = 0` returns 694,341 rows; all 4 core tables join on `id` with zero orphans; supplementary catalogs linked; sentinel residuals eliminated; unit validation passed (LePhare log10, CIGALE linear).

**Known issue for Phase 2:** CIGALE returned non-NULL but astrophysically impossible values (mass < 10⁻¹⁰ M_sun) for some sources. These "zombie fits" contaminate O1 disagreement counts. A CIGALE plausibility filter is the first Phase 2 task.

### Phase 2: Feature Engineering (Tension Scalars)

**Objective:** Per-source tension metrics computed and materialized as queryable columns.

| Task | Detail |
|------|--------|
| CIGALE plausibility filter | Exclude zombie fits: mass floor (~10³ M_sun), chi2_red_best_fit threshold, photometric coverage requirements |
| Quality cuts | Apply DR1 tutorial recipe: `type=0`, `warn_flag=0`, `|mag_model_f444w|<30`, `flag_star_hsc=0` |
| T_A: Algorithmic tension | Δlog M★, Δlog SFR, Δlog sSFR, χ² ratio features, AGN-galaxy χ² comparison |
| T_z: Redshift tension | Load PDF(z) pickle; compute PDF width, multimodality index, zpdf_med vs zchi2 offset, space-vs-all divergence |
| T_M: Morphological tension | Delta-filtered morphology-SED contradiction scores; cross-check parametric vs ML classifications |
| T_E: Environmental tension | Join LSS `density_excess`; compute percentile ranks; flag group membership extremes |
| Combined tension magnitude | Per-component ranks + multi-axis "super-anomaly" flag |

**Exit criteria:** Tension scalar table materialized in PostgreSQL; summary statistics and distributions documented; obvious artifacts (flag leakage, photometric edge effects) identified and excluded; zombie fits excluded from all tension metrics.

### Phase 3: Anomaly Detection (Vectors + Ranking)

**Objective:** Ranked candidate lists from multiple detection methods, triaged via visual inspection.

| Task | Detail |
|------|--------|
| Isolation Forest | Run on tension feature space; calibrate contamination parameter; extract anomaly scores |
| SOM density estimation | Train on photometric + tension features; identify low-density/high-QE nodes; map anomaly populations |
| Tension vector ranking | Rank by combined tension magnitude; identify "super-anomalies" (high on 3+ components) |
| Cross-method consensus | Intersect candidate lists from IF, SOM, and tension ranking; prioritize objects flagged by multiple methods |
| Visual triage | Top 100–200 candidates inspected via COSMOS-Web FitsMap viewer; classify as artifact, merger, genuine anomaly, etc. |
| Candidate catalog | Publish ranked list with tension decomposition, physical interpretation hypotheses, and triage classifications |

**Exit criteria:** Candidate catalog with ≥50 high-confidence anomalies carrying interpretable tension signatures; methods reproducible from published code.

### Phase 4: Characterization + Publication

**Objective:** Science paper + ARD release.

| Task | Detail |
|------|--------|
| SED-level analysis | For top candidates: inspect CIGALE best-fit SEDs (436 GB extracted), compare model components, identify failure modes |
| Physical interpretation | Classify candidates into physics categories (Line Imposters, Dusty Decoupling, Blue Nuggets, Passive Disks, environmental outliers) |
| Science paper | Target: "Tension Catalog" — objects that break standard SED fitting, with environmental context |
| ARD packaging | Release tension scalar table as community data product (see Section 3) |

---

## 3. Analysis Ready Dataset — Parallel Output Track

The anomaly detection pipeline naturally produces a reusable community data product. Every tension metric computed for our science goals is independently valuable to any researcher working with COSMOS2025. Rather than treating this as a side effect, we frame it explicitly as an ARD following the [Analysis Ready Dataset methodology](https://github.com/radioastronomyio/analysis-ready-dataset).

### 3.1 Layer Mapping

| ARD Layer | COSMOS2025 Content | Pipeline Phase |
|-----------|-------------------|----------------|
| **0: Raw** | Master catalog (6 extensions) + supplementary catalogs in PostgreSQL, quality-filtered, cross-extension joins materialized | Phase 1 |
| **1: Scalars** | Tension metrics (T_A, T_z, T_M, T_E), derived quality indicators, combined tension magnitude, percentile ranks | Phase 2 |
| **2: Vectors** | Isolation Forest anomaly scores, SOM node assignments + quantization errors, tension vector embeddings | Phase 3 |
| **3: Graphs** | Environmental context joins (group membership, LSS density), k-NN graphs in tension feature space | Phase 3 |

### 3.2 Scope

The ARD covers the quality-filtered subset of COSMOS2025 — approximately 694K sources with `warn_flag=0`, further refined by the DR1 tutorial quality recipe. Layer 1 scalars are materialized for the full clean sample. Layer 2 vectors are computed for the subset with sufficient photometric coverage and valid fits from both SED codes (the "dual-code clean" sample, expected ~500–600K sources).

This is not a full catalog reprocessing. It is a targeted materialization of the tension metrics that the anomaly detection pipeline computes anyway, packaged for reuse.

### 3.3 Community Value Proposition

Every researcher working with COSMOS2025 who wants to assess cross-code consistency must independently compute Δlog M★, ΔSFR, χ² ratios, photo-z PDF metrics, and morphology-SED contradiction scores. This ARD front-loads that compute cost once with documented methodology, converting processor time into storage space. The tension scalars also serve as a "catalog QA layer" — a pre-computed map of where the catalog's internal products disagree, useful for any science case that depends on parameter reliability.

### 3.4 Distinction from Science Paper

The science paper interprets the anomalies — classifying candidates, proposing physical scenarios, recommending spectroscopic follow-up targets. The ARD is the *data product* underneath: the tension scalars, anomaly scores, and ranked lists without interpretation. The two outputs serve different audiences (science community vs data users) and have different publication venues.

---

## 4. Key References

### Data Anchors

- Shuntov et al. 2025a — COSMOS2025 catalog paper (photometry, morphology, photo-z, physical parameters, non-parametric SFHs)
- Shuntov et al. 2025b — Stellar mass function (quiescent/star-forming split)
- Toni et al. 2025 — Galaxy group catalog (AMICO, z < 3.7)
- Hatamnia et al. 2025 — Large-scale structure density maps (z ~ 7)

### Methodological Precedents

- Baron & Poznanski 2017 — Isolation Forest outlier detection in SDSS
- Broadbelt et al. 2025 — Anomalous E+A galaxies in GAMA via Isolation Forest
- Abedini et al. 2025 — SOMs for parameter estimation in COSMOS-Web
- O'Ryan & Gomez 2025 — AnomalyMatch on HST Legacy Archive

### Anti-Portfolio (Claimed Territory)

- Akins et al. 2025 — Little Red Dots in COSMOS-Web
- Manning et al. 2025 — SCUBADive II, dust-obscured galaxies
- Huertas-Company et al. 2025 — Emergence of the Hubble Sequence
- Li et al. 2025 — Dual AGN identification

---

*Last Updated: April 5, 2026 | v0.2*
