<!--
---
title: "v1.1 Readiness Review"
description: "Evidence-backed findings and closed questions constituting the ETL v2 approval surface"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.1"
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

**Amendment 2026-08-17 (spec P2R-02).** F6 is closed with materialization evidence, and F1, F5, F7, F9, and Q1 carry resolution blocks reconciling them with the subsequently approved lossless-mirror architecture. Resolutions are append-only: original finding text, evidence, and closed questions are unchanged so that every finding remains legible as it stood when written. The Approval section is now a record with an operator-confirmation table and signature line; the executor prepared the structure and disposition summaries and left every confirmation cell and the signature empty.

---

## Findings

### F1. The v1.1 master catalog carries seven extensions; the seventh is GALIGHT-MORPHO

**Evidence:** `COSMOSWeb_mastercatalog_v1.1.fits` enumerated by EXTNAME (`docs/reference/master-catalog-profile-v1.1.md` §1, generator `src/inspection/profile_v11.py`): PHOTOMETRY HOTCOLD AND SE++ (287 cols), LEPHARE (43), SE++APER (148), CIGALE (56), ML-MORPHO (150), B+D (461), GALIGHT-MORPHO (204), all 784,016 rows. The v1 documented profile records six extensions; GALIGHT-MORPHO is absent from v1 (`docs/reference/columns-bulge-disk-morphological-measurements.txt` era) and ships both in the master and as `COSMOSWeb_mastercatalog_v1.1_galight_morph.fits`. The v1.1 column-description file lists it as extension 7.

**Closed question:** Load GALIGHT-MORPHO as a new `catalog` table in ETL v2 (204 columns, id-keyed, same column-skip policy as ML-MORPHO)? Yes/No.

**Resolution (2026-08-17, spec P2R-02, per the approved lossless-mirror architecture):** All 204 GALIGHT-MORPHO source columns are in scope; no ML-MORPHO subset policy carries forward. The mirror is complete per extension, and the column-skip question this finding posed is superseded by that completeness rule.

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

**Resolution (2026-08-17, spec P2R-02, per the approved lossless-mirror architecture):** Both primary photometry (PHOTOMETRY HOTCOLD AND SE++) and SE++APER are loaded completely; vector-valued columns remain arrays in the source mirror. The either/or framing of the closed question is superseded: the mirror does not choose products.

### F6. The spec-z join cannot be verified on-box: the compilation's data files are LFS pointers (CLOSED 2026-08-17)

**Evidence:** All seven LFS-pattern files in `/opt/agents/repos/reference-files/speczcompilation` (`.gitattributes`: `*.fits`, `*.pkl`) are 133–134 byte pointer files; `git-lfs` is not installed on ML01; no materialized copy exists anywhere on-box (searched `/mnt/nvme01`, `/opt/agents`, home). The `_unique.fits` pointer declares its true content as SHA-256 `6ffd1145...336e99`, 70,223,040 bytes; the astropy open attempt fails with "No SIMPLE card found". Live side verified by query: 37,219 sources carry a non-sentinel `id_specz_khostovan25` and 26,323 of them sit in `catalog.v_analysis_sample`; the compilation-side count (compilation `Id_specz` values matching live links) is therefore uncomputable on-box, and any discrepancy against 37,219 remains unstated rather than reconciled. Manifest: `docs/reference/data-manifest-v1.1.md` §2.

**Closed question:** Operator materializes the checkout (git-lfs install on ML01 plus `git lfs pull`, an operator action by the no-network rule), after which the gate 1.11 join runs as a zero-gate verification; or supplies the compilation by another channel. Materialize / Alternate channel?

**Resolution (2026-08-17, spec P2R-02):** CLOSED. The operator chose materialization by action: git-lfs 3.4.1 installed on ML01 and the checkout materialized 2026-08-17T01:38–01:42Z at pinned HEAD `1924f5d0` (checkout clean, HEAD unmoved). Gate 2.2 reconciliation: for all seven LFS files the SHA-256 of the materialized content equals the `oid sha256:` declared by the pointer blob at the pinned commit, and byte counts equal the declared sizes — 7/7 on both; `astropy.io.fits.open` succeeds on `_unique.fits` (261,975 rows) and `_all.fits` (482,579 rows). The manifest's seven rows are re-pinned to content hashes (`data-manifest-v1.1.md` §2). Live-side counts stand as recorded above: 37,219 linked sources, 26,323 within `catalog.v_analysis_sample`. Compilation side: `_unique.fits` carries 261,975 rows; the link-level join of compilation `Id_specz` against the live 37,219 is recomputed and reported as a P2R-03 gate, which this closure unblocks.

### F7. No v1 master FITS survives on-box

**Evidence:** Filesystem search over `/mnt/nvme01`, `/opt/agents`, and the home directory for any `*mastercatalog*` file outside the v1.1 holdings returns nothing; the NVMe root holds only the v1.1 directory and unrelated DESI data. After Task 2's schema drop, the only v1 primary sources will be the Task 2 pg_dump (not yet taken) and the git-tracked v1 records (`docs/reference/columns-*.txt`, `master-catalog-profile.md`, `verification-report.md`). This is a report-and-locate finding; disposition is the operator's.

**Closed question:** Proceed with Task 2 on the strength of the pg_dump plus tracked v1 records as the v1 baseline (no re-download of the v1 FITS)? Yes / No, obtain v1 FITS first.

**Resolution (2026-08-17, spec P2R-02, per the approved lossless-mirror architecture):** Superseded as an execution concern. `cosmos2025` remains untouched and `cosmos2025_v11` is built alongside it; no v1 schema drop and no v1 archive are part of P2R-03. The no-v1-FITS risk this finding weighed is retired for the rebuild because nothing v1 is destroyed by it.

### F8. LePhare match fractions are intermediate (1.0–2.9%) and are reported as their own finding, per the rule stated in advance

**Evidence:** Exact-match fractions from the gate 1.10 sample: zfinal 0.029122 (hot) / 0.026480 (others); mass_med 0.009694 / 0.009619; sfr_med 0.013359 / 0.013065. Each is neither approximately 0 nor approximately 1. Reading: the rerun leaves 1–3% of sources bitwise identical while the remainder move, mostly by small amounts (medians ~0; 92% of photo-z within 0.1), with heavy tails (p1/p99 reaching −1.8/+0.7). This fraction is never averaged into a summary; it bounds how many sources could silently inherit identical parameters under a "carried" hypothesis and refutes that hypothesis for the other 97–99%.

**Closed question:** None required beyond F2/F3 confirmation; recorded because the spec's stated rule makes any intermediate fraction a standalone finding.

### F9. `agngal_desi.fits` is a 17,995,599-row reference product, not a per-source catalog table

**Evidence:** Two binary tables (AGNCAT, 36 cols; AUXDATA, 58 cols), both 17,995,599 rows, about 23× the 784,016 COSMOS-Web source count (`docs/reference/master-catalog-profile-v1.1.md` §3). The file is an AGN/DESI cross-identification reference; loading it whole into the `catalog` schema would multiply the database row count by an order of magnitude with no analysis consumer named.

**Closed question:** ETL v2 treats agngal_desi as a deferred reference file (hashed and pinned by the gate 1.7 manifest, loaded only if a spec later needs it), or loads it as reference tables now? Defer / Load.

**Resolution (2026-08-17, spec P2R-02, per the approved lossless-mirror architecture):** AGN/DESI remains deferred because it is a separate 18-million-row reference product outside the declared catalog-mirror boundary, not because it lacks a current research consumer. The boundary rationale, not consumer demand, is the basis; a future spec that brings it inside a declared boundary reopens the load decision on its own terms.

---

## ETL v2 Design Questions

Each question is closed, with the recommendation the evidence supports.

**Q1. Extension-to-table mapping.** Load the seven master extensions as id-keyed tables (photometry lineage per F5's answer, lephare, cigale including `ebv_stars*`, ml_morpho subset policy as v1, b+d, galight_morpho new per F1), with agngal_desi deferred per F9? Recommendation: yes, seven tables plus existing supplement tables per F4's answer. Proceed / amend?

**Resolution (2026-08-17, spec P2R-02, per the approved lossless-mirror architecture):** The frozen mapping is all seven complete master extensions, three complete supplements, and the spec-z compilation, with no science-driven column projection. The v1 ML-MORPHO subset policy referenced in the question does not carry into the mirror.

**Q2. Per-extension file strategy.** Extract from the standalone per-extension FITS products rather than the 10 GB master, since gate 1.8 verified them column-identical to the master HDUs; the master remains pinned by the manifest as the reference artifact. Recommendation: standalone files. Proceed / amend?

**Q3. Supplement handling.** Per F4: reload the identical v1-content files (accept documented skew), or hold for an upstream refresh. Recommendation: reload now, mark `supplement_version = v1-content-on-v1.1-holdings` in the provenance table, revisit if upstream refreshes. Proceed / hold?

**Q4. Spec-z ingest as an ETL v2 gate.** Per F6: the operator materializes the compilation before ETL v2 dispatch (it is a precondition for the spec-z ingest gate and for recomputing the 37,219-link join), and ETL v2 ingests `_unique.fits` with the join rebuilt and reported against 37,219 / 26,323. Recommendation: yes, spec-z ingest is an ETL v2 gate contingent on F6 materialization. Proceed / defer spec-z?

---

## Approval

Operator signature on the nine closed questions and four design questions authorizes Task 2 (ETL v2) to dispatch. Until then the v1 database stays untouched and the v1.1 holdings stay pinned at manifest `data-manifest-v1.1.csv`.

**Record of operator confirmation (structure prepared by spec P2R-02, 2026-08-17).** Each row carries a disposition summary of the evidence and any resolution above. The confirmation column is the operator's alone; it is empty until filled by hand, and nothing in this record infers or presumes an answer.

| ID | Disposition summary | Operator confirmation |
|----|---------------------|-----------------------|
| F1 | Seventh extension GALIGHT-MORPHO confirmed in v1.1 (204 cols, 784,016 rows); resolved: all 204 columns in scope, no subset policy carries forward | |
| F2 | CIGALE fully recomputed for v1.1 (0.000000 exact-match; mass −6%, sfr_inst +30%, chi2 +95%; `ebv_stars*` new); v1.1 loads as new baseline, tension products recomputed from scratch | |
| F3 | LePhare change is field-wide, not tile-concentrated (tail fractions agree within ~0.5 pp); no per-tile special casing | |
| F4 | Supplements are v1 release, bitwise identical to live tables; skew against v1.1 photo-z unresolved upstream; accept-with-documented-skew or hold is the operator's call | |
| F5 | Photometry products structurally distinct, same 784,016-source ID set; resolved: both loaded completely, vector columns remain arrays | |
| F6 | CLOSED 2026-08-17: checkout materialized, 7/7 pointer-content reconciliation, `_unique.fits` 261,975 rows / `_all.fits` 482,579 rows open cleanly; live side 37,219 / 26,323 stands | |
| F7 | No v1 master FITS on-box; resolved: superseded — `cosmos2025` untouched, `cosmos2025_v11` built alongside, no v1 drop or archive in P2R-03 | |
| F8 | LePhare intermediate match fractions 1.0–2.9% recorded as bounding finding per the stated rule; no action beyond F2/F3 | |
| F9 | AGN/DESI is a 17,995,599-row reference product (~23× source count); resolved: deferred by mirror-boundary and scale, not by absence of a consumer | |
| Q1 | Resolved: frozen mapping is all seven complete master extensions, three complete supplements, and the spec-z compilation, no science-driven column projection | |
| Q2 | Standalone per-extension FITS verified column-identical to master HDUs; extract from standalone, master stays manifest-pinned as reference artifact | |
| Q3 | Supplements reload now marked `supplement_version = v1-content-on-v1.1-holdings`, skew documented; revisit on upstream refresh | |
| Q4 | Spec-z ingest is an ETL v2 gate, unblocked by F6 closure; join recomputed and reported against 37,219 / 26,323 and compilation 261,975 | |

Operator signature: ______________________  Name: ______________________  Date: ____________
