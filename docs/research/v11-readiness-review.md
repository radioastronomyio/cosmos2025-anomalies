<!--
---
title: "v1.1 Readiness Review"
description: "Evidence-backed findings and closed questions constituting the ETL v2 approval surface"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-16"
version: "1.0"
status: "Active"
tags:
  - type: report
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Data Manifest v1.1](../reference/data-manifest-v1.1.md)"
  - "[v1.1 Structural Profile](../reference/master-catalog-profile-v1.1.md)"
  - "[v1 to v1.1 Delta](../reference/v1-to-v11-delta.md)"
  - "[Parameter Migration Evidence](../reference/parameter-migration-evidence-v1.1.md)"
---
-->

# v1.1 Readiness Review

The approval surface for ETL v2. Every finding below carries an ID, a statement, evidence with exact numbers, and a closed question. The evidence comes from gates 1.7 through 1.11 of spec P2R-01; nothing here cites the spec's own assertions. Task 2 does not dispatch until the operator answers these questions.

---

## Findings

### F1. The v1.1 master catalog carries seven extensions; the seventh is GALIGHT-MORPHO

**Evidence:** `COSMOSWeb_mastercatalog_v1.1.fits` enumerated by EXTNAME (`docs/reference/master-catalog-profile-v1.1.md` §1, generator `src/inspection/profile_v11.py`): PHOTOMETRY HOTCOLD AND SE++ (287 cols), LEPHARE (43), SE++APER (148), CIGALE (56), ML-MORPHO (150), B+D (461), GALIGHT-MORPHO (204), all 784,016 rows. The v1 documented profile records six extensions; GALIGHT-MORPHO is absent from v1 (`docs/reference/columns-bulge-disk-morphological-measurements.txt` era) and ships both in the master and as `COSMOSWeb_mastercatalog_v1.1_galight_morph.fits`. The v1.1 column-description file lists it as extension 7.

**Closed question:** Load GALIGHT-MORPHO as a new `catalog` table in ETL v2 (204 columns, id-keyed, same column-skip policy as ML-MORPHO)? Yes/No.

### F2. CIGALE physical parameters were fully recomputed for v1.1

**Evidence:** 60,000-source sampled join, exact-match fraction 0.000000 on mass, sfr_inst, sfr_100myr, and chi2_red_best_fit in both tile groups (5,112 + 37,074 valid rows; not one bitwise match). Median relative shifts: mass −6%, sfr_inst +30%, chi2 +95%. The extension also gains two columns (`ebv_stars`, `ebv_stars_err`) absent from both the v1 documentation and the live `catalog.cigale` schema. Full tables: `docs/reference/parameter-migration-evidence-v1.1.md` §1; delta classification: `docs/reference/v1-to-v11-delta.md` §1.

**Closed question:** Confirm ETL v2 loads CIGALE values as the new baseline (no v1 carry-over anywhere, tension products recomputed from scratch)? Yes/No.

### F3. LePhare changes are field-wide, not concentrated in tiles B5/B9/B10

**Evidence:** Same 60,000-source join, split by tile from the master PHOTOMETRY extension (B5/B9/B10: 8,479 rows; others: 51,521). Tail fractions agree within ~0.5 percentage points on every column: |Δzfinal| > 0.1 in 7.97% of hot-tile vs 8.17% of other-tile sources; |Δmass_med| > 0.1 dex in 11.96% vs 11.44%; |Δsfr_med| > 0.1 dex in 18.56% vs 18.69%. Medians are ~0 in both groups.

**Closed question:** Confirm ETL v2 treats the photo-z change as field-wide (no per-tile special casing in extraction or verification)? Yes/No.

### F4. The LSS and group supplements are the v1 release, unchanged; skew against the v1.1 photo-z recompute is unresolved (OPEN)

**Evidence:** On-disk files compared at value level against the live tables (`src/inspection/supplement_evidence.py`, seed 20260815): row counts from the files are 164,155 LSS (OVERDENSITY HDU), 1,678 groups, 1,745,652 memberships, each equal to its live table count; sampled value checks are bitwise exact throughout (2,000/2,000 LSS on (id, density_excess); 1,678/1,678 groups on (ID, LAMBDA); 5,000/5,000 memberships on (galid, group_id, assoc_prob)). The local files are therefore the same release that was loaded, not a refresh. The on-disk v1.1 documentation says nothing about updated supplements: the arXiv paper source (arXiv-2506.03243v1) predates v1.1 and mentions no supplement reissue; the v1.1 column-description file covers only the master catalog; the LSS readme describes Hatamnia et al. 2025 KDE built on "robust photometric redshifts" (the v1 photo-z that v1.1 reran per F2/F3). Whether upstream ships refreshed supplements is not determinable on-box.

**Closed question:** Accept the v1 supplements into ETL v2 with their skew against the v1.1 photo-z documented as a known limitation (O5 contextual-anomaly work proceeds with that caveat), or hold supplement ingest pending an upstream refresh? Accept / Hold.

### F5. ETL v2 should feed from the primary photometry product; the two products are structurally distinct

**Evidence:** `photom_primary` = EXTNAME "PHOTOMETRY HOTCOLD AND SE++", 287 columns, hot+cold SE++ model photometry on PSF-homogenized mosaics; this is the v1 lineage loaded as `catalog.photometry_core` (158 scalar columns; band-repeated aperture triples skipped). `photom_secondary` = EXTNAME "SE++APER", 148 columns, non-PSF-homogenized aperture photometry (v1 documentation: `docs/reference/columns-non-psf-homogenized-aperture-photometry.txt`). Both carry the identical 784,016-source ID set (`docs/reference/v1-to-v11-delta.md` §3). The standalone per-extension files are column-identical to their master HDUs (verified name-by-name, gate 1.8), so the choice of source file does not change content, only I/O weight.

**Closed question:** Adopt photom_primary as the ETL v2 photometry source (secondary either skipped or loaded as a reference table)? Primary / Primary+secondary.

### F6. The spec-z join cannot be verified on-box: the compilation's data files are LFS pointers (OPEN)

**Evidence:** All seven LFS-pattern files in `/opt/agents/repos/reference-files/speczcompilation` (`.gitattributes`: `*.fits`, `*.pkl`) are 133–134 byte pointer files; `git-lfs` is not installed on ML01; no materialized copy exists anywhere on-box (searched `/mnt/nvme01`, `/opt/agents`, home). The `_unique.fits` pointer declares its true content as SHA-256 `6ffd1145...336e99`, 70,223,040 bytes; the astropy open attempt fails with "No SIMPLE card found". Live side verified by query: 37,219 sources carry a non-sentinel `id_specz_khostovan25` and 26,323 of them sit in `catalog.v_analysis_sample`; the compilation-side count (compilation `Id_specz` values matching live links) is therefore uncomputable on-box, and any discrepancy against 37,219 remains unstated rather than reconciled. Manifest: `docs/reference/data-manifest-v1.1.md` §2.

**Closed question:** Operator materializes the checkout (git-lfs install on ML01 plus `git lfs pull`, an operator action by the no-network rule), after which the gate 1.11 join runs as a zero-gate verification; or supplies the compilation by another channel. Materialize / Alternate channel?

### F7. No v1 master FITS survives on-box

**Evidence:** Filesystem search over `/mnt/nvme01`, `/opt/agents`, and the home directory for any `*mastercatalog*` file outside the v1.1 holdings returns nothing; the NVMe root holds only the v1.1 directory and unrelated DESI data. After Task 2's schema drop, the only v1 primary sources will be the Task 2 pg_dump (not yet taken) and the git-tracked v1 records (`docs/reference/columns-*.txt`, `master-catalog-profile.md`, `verification-report.md`). This is a report-and-locate finding; disposition is the operator's.

**Closed question:** Proceed with Task 2 on the strength of the pg_dump plus tracked v1 records as the v1 baseline (no re-download of the v1 FITS)? Yes / No, obtain v1 FITS first.

### F8. LePhare match fractions are intermediate (1.0–2.9%) and are reported as their own finding, per the rule stated in advance

**Evidence:** Exact-match fractions from the gate 1.10 sample: zfinal 0.029122 (hot) / 0.026480 (others); mass_med 0.009694 / 0.009619; sfr_med 0.013359 / 0.013065. Each is neither approximately 0 nor approximately 1. Reading: the rerun leaves 1–3% of sources bitwise identical while the remainder move, mostly by small amounts (medians ~0; 92% of photo-z within 0.1), with heavy tails (p1/p99 reaching −1.8/+0.7). This fraction is never averaged into a summary; it bounds how many sources could silently inherit identical parameters under a "carried" hypothesis and refutes that hypothesis for the other 97–99%.

**Closed question:** None required beyond F2/F3 confirmation; recorded because the spec's stated rule makes any intermediate fraction a standalone finding.

### F9. `agngal_desi.fits` is a 17,995,599-row reference product, not a per-source catalog table

**Evidence:** Two binary tables (AGNCAT, 36 cols; AUXDATA, 58 cols), both 17,995,599 rows, about 23× the 784,016 COSMOS-Web source count (`docs/reference/master-catalog-profile-v1.1.md` §3). The file is an AGN/DESI cross-identification reference; loading it whole into the `catalog` schema would multiply the database row count by an order of magnitude with no analysis consumer named.

**Closed question:** ETL v2 treats agngal_desi as a deferred reference file (hashed and pinned by the gate 1.7 manifest, loaded only if a spec later needs it), or loads it as reference tables now? Defer / Load.

---

## ETL v2 Design Questions

Each question is closed, with the recommendation the evidence supports.

**Q1. Extension-to-table mapping.** Load the seven master extensions as id-keyed tables (photometry lineage per F5's answer, lephare, cigale including `ebv_stars*`, ml_morpho subset policy as v1, b+d, galight_morpho new per F1), with agngal_desi deferred per F9? Recommendation: yes, seven tables plus existing supplement tables per F4's answer. Proceed / amend?

**Q2. Per-extension file strategy.** Extract from the standalone per-extension FITS products rather than the 10 GB master, since gate 1.8 verified them column-identical to the master HDUs; the master remains pinned by the manifest as the reference artifact. Recommendation: standalone files. Proceed / amend?

**Q3. Supplement handling.** Per F4: reload the identical v1-content files (accept documented skew), or hold for an upstream refresh. Recommendation: reload now, mark `supplement_version = v1-content-on-v1.1-holdings` in the provenance table, revisit if upstream refreshes. Proceed / hold?

**Q4. Spec-z ingest as an ETL v2 gate.** Per F6: the operator materializes the compilation before ETL v2 dispatch (it is a precondition for the spec-z ingest gate and for recomputing the 37,219-link join), and ETL v2 ingests `_unique.fits` with the join rebuilt and reported against 37,219 / 26,323. Recommendation: yes, spec-z ingest is an ETL v2 gate contingent on F6 materialization. Proceed / defer spec-z?

---

## Approval

Operator signature on the nine closed questions and four design questions authorizes Task 2 (ETL v2) to dispatch. Until then the v1 database stays untouched and the v1.1 holdings stay pinned at manifest `data-manifest-v1.1.csv`.
