<!--
---
title: "COSMOS2025 ETL v2 Verification Surface"
description: "Evidence-generated approval surface for the lossless v1.1 mirror"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-18"
version: "1.0"
status: "Draft"
tags:
  - type: report
  - domain: astronomy
related_documents:
  - "[Schema v1.1](../reference/schema-v11.md)"
  - "[Science Opportunities](science-opportunities.md)"
---
-->

# ETL v2 Verification Surface

The tracked evidence supports operator review; it does not itself authorize cutover or analysis dispatch.

## Verification findings

<!-- finding:V13-01 -->
### V13-01

All 11 mirrors map 1,403 native and 13 metadata fields in 1,416 rows, including 1,349 master-native fields.

| Evidence | Value | Tracked source |
|---|---:|---|
| mirror tables | 11 | `data/dictionary/columns-v11.csv:rows 2-1417 field=target_table` |
| dictionary rows | 1,416 | `data/dictionary/columns-v11.csv:rows 2-1417` |
| native fields | 1,403 | `data/dictionary/columns-v11.csv:rows 2-1417 field=column_origin` |
| metadata fields | 13 | `data/dictionary/columns-v11.csv:rows 2-1417 field=column_origin` |
| master fidelity | 1,349 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L524` |

Question: Accept the 11-source, 1,416-field lossless mirror boundary? Yes/No.

Recommendation: Accept the sealed dictionary coverage boundary.

<!-- finding:V13-02 -->
### V13-02

Across 1,416 rows, descriptions are 1,150/204/49/13, units 586/830, semantics 15/1,401, NULL states 1,108/305/3, documented sentinels 1/1, and candidates 476/793.

| Evidence | Value | Tracked source |
|---|---:|---|
| dictionary rows | 1,416 | `data/dictionary/columns-v11.csv:rows 2-1417` |
| description verified | 1,150 | `data/dictionary/columns-v11.csv:rows 2-1417 field=description_status` |
| description undocumented_upstream | 49 | `data/dictionary/columns-v11.csv:rows 2-1417 field=description_status` |
| description pattern_expanded | 204 | `data/dictionary/columns-v11.csv:rows 2-1417 field=description_status` |
| description project_derived | 13 | `data/dictionary/columns-v11.csv:rows 2-1417 field=description_status` |
| unit unknown | 830 | `data/dictionary/columns-v11.csv:rows 2-1417 field=unit/unit_source` |
| unit provenanced | 586 | `data/dictionary/columns-v11.csv:rows 2-1417 field=unit/unit_source` |
| semantic absent | 1,401 | `data/dictionary/columns-v11.csv:rows 2-1417 field=semantic_note` |
| semantic provenanced | 15 | `data/dictionary/columns-v11.csv:rows 2-1417 field=semantic_note` |
| NULL none | 1,108 | `data/dictionary/columns-v11.csv:rows 2-1417 field=has_fits_mask,has_nan` |
| NULL nan | 305 | `data/dictionary/columns-v11.csv:rows 2-1417 field=has_fits_mask,has_nan` |
| NULL fits_mask | 3 | `data/dictionary/columns-v11.csv:rows 2-1417 field=has_fits_mask,has_nan` |
| documented sentinel fields | 1 | `data/dictionary/columns-v11.csv:rows 2-1417 field=documented_sentinel_values_json` |
| documented sentinel values | 1 | `data/dictionary/columns-v11.csv:rows 2-1417 field=documented_sentinel_values_json` |
| candidate fields | 476 | `data/dictionary/columns-v11.csv:rows 2-1417 field=candidate_sentinel_values_json` |
| candidate observations | 793 | `data/dictionary/columns-v11.csv:rows 2-1417 field=candidate_sentinel_values_json` |

Question: Accept the complete computed evidence-state distributions as the review baseline? Yes/No.

Recommendation: Accept the computed evidence distributions without relabeling upstream facts.

<!-- finding:V13-03 -->
### V13-03

Review 49 upstream gaps and 793 finite candidates across 476 fields.

| Evidence | Value | Tracked source |
|---|---:|---|
| upstream gaps | 49 | `data/dictionary/columns-v11.csv:rows 2-1417 field=description_status=undocumented_upstream` |
| candidate observations | 793 | `data/dictionary/columns-v11.csv:rows 2-1417 field=candidate_sentinel_values_json` |
| candidate fields | 476 | `data/dictionary/columns-v11.csv:rows 2-1417 field=candidate_sentinel_values_json` |

Question: Defer all 793 candidate-to-cleaning-rule decisions to scientific review? Yes/No.

Recommendation: Keep candidates finite and unchanged until a separately approved scientific review.

<!-- finding:V13-04 -->
### V13-04

The 155-row manifest bounded 16 inputs; 7 master products each had 784,016 rows, and 1,349 fields passed 5,000 sampled ordinals with 0 mismatches.

| Evidence | Value | Tracked source |
|---|---:|---|
| manifest rows | 155 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L483` |
| consumed inputs | 16 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L497` |
| master products | 7 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L513-L519` |
| rows per master | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L522` |
| master native fields | 1,349 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L524` |
| sample ordinals | 5,000 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L521` |
| fidelity mismatches | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L525` |

Question: Accept the 16-pin and 1,349-field fidelity evidence with its ordinal limitation? Yes/No.

Recommendation: Accept the result while retaining the inherited cross-HDU ordinal contract caveat.

<!-- finding:V13-05 -->
### V13-05

The target has 11 exact load counts, 1,429 columns, 192 constraints, 166 arrays, 11 provenance rows carrying 22 declared/observed digests, and 1 pinned manifest identity.

| Evidence | Value | Tracked source |
|---|---:|---|
| mirror tables | 11 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1201-L1204` |
| columns | 1,429 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1201-L1204` |
| constraints | 192 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1201-L1204` |
| arrays | 166 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1201-L1204` |
| provenance rows | 11 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L943-L953` |
| declared and observed digests | 22 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L943-L953` |
| load count photometry_primary | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L943` |
| load count photometry_aper | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L944` |
| load count lephare | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L945` |
| load count cigale | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L946` |
| load count ml_morpho | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L947` |
| load count bulge_disk | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L948` |
| load count galight_morph | 784,016 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L949` |
| load count lss_overdensity | 164,155 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L950` |
| load count galaxy_groups | 1,678 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L951` |
| load count galaxy_group_memberships | 1,745,652 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L952` |
| load count specz_compilation | 261,975 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L953` |
| manifest identity 5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L957-L959` |

Question: Accept the exact 11-mirror, 1,429-column persisted schema and provenance boundary? Yes/No.

Recommendation: Accept the generated schema and dual-hash provenance contract.

<!-- finding:V13-06 -->
### V13-06

All 1,416 cases passed 201,678 samples, 28,063,492 row-column and 16,600,000 array comparisons with 0 mismatches.

| Evidence | Value | Tracked source |
|---|---:|---|
| value reconciliation | 28,063,492 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1145` |
| cases | 1,416 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1144-L1147` |
| sampled records | 201,678 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1144-L1147` |
| array elements | 16,600,000 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1144-L1147` |
| mismatches | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1144-L1147` |

Question: Accept the 1,416-case value reconciliation as complete for the declared sample? Yes/No.

Recommendation: Accept the zero-mismatch bounded reconciliation evidence.

<!-- finding:V13-07 -->
### V13-07

All 261,975 spec-z rows span 17 flags; flags 3+4 total 183,221, flag 9 totals 2,326, and the nonmaterialized join is 24,364 versus 37,219, a -12,855 difference.

| Evidence | Value | Tracked source |
|---|---:|---|
| spec-z rows | 261,975 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| observed flags | 17 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| flag identifier | 3 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| flag identifier | 4 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| flags 3+4 rows | 183,221 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| flag identifier | 9 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| flag 9 rows | 2,326 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
| join rows | 24,364 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L853-L854` |
| prior rows | 37,219 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L853-L854` |
| difference | -12,855 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L853-L854` |

Question: Accept the complete 17-flag distribution and leave the 24,364 join nonmaterialized? Yes/No.

Recommendation: Accept the sourced distribution and record the unreconciled join difference.

<!-- finding:V13-08 -->
### V13-08

The 7-attribute analyst passed 12 SELECTs and 72 denials, including 1/11 and 4/24 matrices; memberships/ownership were 0/0, the mode 0600 handoff had 5 names and 0 exposed values, with 1 admin-session transport, 0 direct analyst authentications, and 1 pending HBA action.

| Evidence | Value | Tracked source |
|---|---:|---|
| role cosmos2025_v11_ro | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L699-L704` |
| role attributes: LOGIN/NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOINHERIT/NOREPLICATION/NOBYPASSRLS | 7 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L690-L692` |
| analyst SELECTs | 12 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1201-L1204` |
| analyst denials | 72 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1201-L1204` |
| master matrix SELECTs | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L693` |
| master matrix denials | 11 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L693` |
| supplement matrix SELECTs | 4 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L859-L862` |
| supplement matrix denials | 24 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L859-L862` |
| role memberships | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L690-L692` |
| role ownership | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L690-L692` |
| handoff mode | 600 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L710-L715` |
| handoff path internal-files/cosmos2025-v11.env | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L710-L715` |
| handoff names PGSQL01_HOST, PGSQL01_PORT, PGSQL01_COSMOS2025_V11_DB, PGSQL01_COSMOS2025_V11_USER, PGSQL01_COSMOS2025_V11_PASSWORD | 5 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L710-L715` |
| secret values exposed | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L710-L715` |
| operator-approved clusteradmin session authorization | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L699-L704` |
| direct analyst network authentications exercised | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L699-L704` |
| pending direct ML01 SCRAM HBA correction | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L699-L704` |

Question: Accept the 12/72 admin-session security evidence while direct ML01 HBA access remains pending? Yes/No.

Recommendation: Accept the privilege contract; complete the separate direct-analyst HBA operator action.

<!-- finding:V13-09 -->
### V13-09

The 8-table v1 fingerprint passed 1 before/after identity check with 0 recorded v1 writes.

| Evidence | Value | Tracked source |
|---|---:|---|
| v1 user tables | 8 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1157-L1158` |
| fingerprint 82fb7e09f21253f2e9b78e8232c43b737008aa4bfb44daf28640463bea82abe7 | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1157-L1158` |
| v1 writes | 0 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L1157-L1158` |

Question: Accept that the historical 8-table cosmos2025 baseline remained unmodified? Yes/No.

Recommendation: Accept the unchanged v1 identity evidence.

## Complete evidence appendices

### Upstream description gaps

| Case | Table | Column | Source | Locator | Source column |
|---|---|---|---|---|---|
<!-- gap:0531:cigale.ebv_stars -->
| `0531:cigale.ebv_stars` | `cigale` | `ebv_stars` | `/mnt/nvme01/cosmos-web-dr1-catalog/COSMOSWeb_mastercatalog_v1.1_cigale.fits` | HDU 1 [CIGALE] | `ebv_stars` |
<!-- gap:0532:cigale.ebv_stars_err -->
| `0532:cigale.ebv_stars_err` | `cigale` | `ebv_stars_err` | `/mnt/nvme01/cosmos-web-dr1-catalog/COSMOSWeb_mastercatalog_v1.1_cigale.fits` | HDU 1 [CIGALE] | `ebv_stars_err` |
<!-- gap:1367:galaxy_groups.id -->
| `1367:galaxy_groups.id` | `galaxy_groups` | `id` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `ID` |
<!-- gap:1368:galaxy_groups.ra -->
| `1368:galaxy_groups.ra` | `galaxy_groups` | `ra` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `RA` |
<!-- gap:1369:galaxy_groups.dec -->
| `1369:galaxy_groups.dec` | `galaxy_groups` | `dec` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `DEC` |
<!-- gap:1370:galaxy_groups.z -->
| `1370:galaxy_groups.z` | `galaxy_groups` | `z` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `Z` |
<!-- gap:1371:galaxy_groups.sn -->
| `1371:galaxy_groups.sn` | `galaxy_groups` | `sn` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `SN` |
<!-- gap:1372:galaxy_groups.sn_nocl -->
| `1372:galaxy_groups.sn_nocl` | `galaxy_groups` | `sn_nocl` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `SN_NOCL` |
<!-- gap:1373:galaxy_groups.amp -->
| `1373:galaxy_groups.amp` | `galaxy_groups` | `amp` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `AMP` |
<!-- gap:1374:galaxy_groups.mskfrc -->
| `1374:galaxy_groups.mskfrc` | `galaxy_groups` | `mskfrc` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `MSKFRC` |
<!-- gap:1375:galaxy_groups.lambda -->
| `1375:galaxy_groups.lambda` | `galaxy_groups` | `lambda` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `LAMBDA` |
<!-- gap:1376:galaxy_groups.lambda_star -->
| `1376:galaxy_groups.lambda_star` | `galaxy_groups` | `lambda_star` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `LAMBDA_STAR` |
<!-- gap:1377:galaxy_groups.detection_flag -->
| `1377:galaxy_groups.detection_flag` | `galaxy_groups` | `detection_flag` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `DETECTION_FLAG` |
<!-- gap:1378:galaxy_groups.n_spec -->
| `1378:galaxy_groups.n_spec` | `galaxy_groups` | `n_spec` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `N_SPEC` |
<!-- gap:1379:galaxy_groups.zphys_sigm -->
| `1379:galaxy_groups.zphys_sigm` | `galaxy_groups` | `zphys_sigm` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `ZPHYS_SIGM` |
<!-- gap:1380:galaxy_groups.zphys_sigp -->
| `1380:galaxy_groups.zphys_sigp` | `galaxy_groups` | `zphys_sigp` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/groups.txt` | text table, header line 1 | `ZPHYS_SIGP` |
<!-- gap:1381:galaxy_group_memberships.galid -->
| `1381:galaxy_group_memberships.galid` | `galaxy_group_memberships` | `galid` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/memberships.txt` | text table, header line 1 | `GALID` |
<!-- gap:1382:galaxy_group_memberships.field_prob -->
| `1382:galaxy_group_memberships.field_prob` | `galaxy_group_memberships` | `field_prob` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/memberships.txt` | text table, header line 1 | `FIELD_PROB` |
<!-- gap:1383:galaxy_group_memberships.id -->
| `1383:galaxy_group_memberships.id` | `galaxy_group_memberships` | `id` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/memberships.txt` | text table, header line 1 | `ID` |
<!-- gap:1384:galaxy_group_memberships.assoc_prob -->
| `1384:galaxy_group_memberships.assoc_prob` | `galaxy_group_memberships` | `assoc_prob` | `/mnt/nvme01/cosmos-web-dr1-catalog/toni/memberships.txt` | text table, header line 1 | `ASSOC_PROB` |
<!-- gap:1385:specz_compilation.id_specz -->
| `1385:specz_compilation.id_specz` | `specz_compilation` | `id_specz` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_specz` |
<!-- gap:1386:specz_compilation.id_original -->
| `1386:specz_compilation.id_original` | `specz_compilation` | `id_original` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_original` |
<!-- gap:1387:specz_compilation.ra_original -->
| `1387:specz_compilation.ra_original` | `specz_compilation` | `ra_original` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_original` |
<!-- gap:1388:specz_compilation.dec_original -->
| `1388:specz_compilation.dec_original` | `specz_compilation` | `dec_original` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_original` |
<!-- gap:1389:specz_compilation.ra_corrected -->
| `1389:specz_compilation.ra_corrected` | `specz_compilation` | `ra_corrected` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_corrected` |
<!-- gap:1390:specz_compilation.dec_corrected -->
| `1390:specz_compilation.dec_corrected` | `specz_compilation` | `dec_corrected` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_corrected` |
<!-- gap:1391:specz_compilation.priority -->
| `1391:specz_compilation.priority` | `specz_compilation` | `priority` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Priority` |
<!-- gap:1392:specz_compilation.specz -->
| `1392:specz_compilation.specz` | `specz_compilation` | `specz` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `specz` |
<!-- gap:1396:specz_compilation.compilation_year -->
| `1396:specz_compilation.compilation_year` | `specz_compilation` | `compilation_year` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `compilation_year` |
<!-- gap:1397:specz_compilation.public_or_private -->
| `1397:specz_compilation.public_or_private` | `specz_compilation` | `public_or_private` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `public_or_private` |
<!-- gap:1398:specz_compilation.id_cos20_classic -->
| `1398:specz_compilation.id_cos20_classic` | `specz_compilation` | `id_cos20_classic` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_COS20_Classic` |
<!-- gap:1399:specz_compilation.ra_cos20_classic -->
| `1399:specz_compilation.ra_cos20_classic` | `specz_compilation` | `ra_cos20_classic` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_COS20_Classic` |
<!-- gap:1400:specz_compilation.dec_cos20_classic -->
| `1400:specz_compilation.dec_cos20_classic` | `specz_compilation` | `dec_cos20_classic` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_COS20_Classic` |
<!-- gap:1401:specz_compilation.id_cos20_farmer -->
| `1401:specz_compilation.id_cos20_farmer` | `specz_compilation` | `id_cos20_farmer` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_COS20_Farmer` |
<!-- gap:1402:specz_compilation.ra_cos20_farmer -->
| `1402:specz_compilation.ra_cos20_farmer` | `specz_compilation` | `ra_cos20_farmer` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_COS20_Farmer` |
<!-- gap:1403:specz_compilation.dec_cos20_farmer -->
| `1403:specz_compilation.dec_cos20_farmer` | `specz_compilation` | `dec_cos20_farmer` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_COS20_Farmer` |
<!-- gap:1404:specz_compilation.id_cosmos25 -->
| `1404:specz_compilation.id_cosmos25` | `specz_compilation` | `id_cosmos25` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_COSMOS25` |
<!-- gap:1405:specz_compilation.ra_cosmos25 -->
| `1405:specz_compilation.ra_cosmos25` | `specz_compilation` | `ra_cosmos25` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_COSMOS25` |
<!-- gap:1406:specz_compilation.dec_cosmos25 -->
| `1406:specz_compilation.dec_cosmos25` | `specz_compilation` | `dec_cosmos25` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_COSMOS25` |
<!-- gap:1407:specz_compilation.id_cosmos15 -->
| `1407:specz_compilation.id_cosmos15` | `specz_compilation` | `id_cosmos15` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_COSMOS15` |
<!-- gap:1408:specz_compilation.ra_cosmos15 -->
| `1408:specz_compilation.ra_cosmos15` | `specz_compilation` | `ra_cosmos15` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_COSMOS15` |
<!-- gap:1409:specz_compilation.dec_cosmos15 -->
| `1409:specz_compilation.dec_cosmos15` | `specz_compilation` | `dec_cosmos15` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_COSMOS15` |
<!-- gap:1410:specz_compilation.id_cosmos09 -->
| `1410:specz_compilation.id_cosmos09` | `specz_compilation` | `id_cosmos09` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `Id_COSMOS09` |
<!-- gap:1411:specz_compilation.ra_cosmos09 -->
| `1411:specz_compilation.ra_cosmos09` | `specz_compilation` | `ra_cosmos09` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `ra_COSMOS09` |
<!-- gap:1412:specz_compilation.dec_cosmos09 -->
| `1412:specz_compilation.dec_cosmos09` | `specz_compilation` | `dec_cosmos09` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `dec_COSMOS09` |
<!-- gap:1413:specz_compilation.photoz -->
| `1413:specz_compilation.photoz` | `specz_compilation` | `photoz` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `photoz` |
<!-- gap:1414:specz_compilation.photoz_type -->
| `1414:specz_compilation.photoz_type` | `specz_compilation` | `photoz_type` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `photoz_type` |
<!-- gap:1415:specz_compilation.groupid -->
| `1415:specz_compilation.groupid` | `specz_compilation` | `groupid` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `GroupID` |
<!-- gap:1416:specz_compilation.groupsize -->
| `1416:specz_compilation.groupsize` | `specz_compilation` | `groupsize` | `/opt/agents/repos/reference-files/speczcompilation/specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | HDU 1 | `GroupSize` |

### Finite candidate observations

Candidates remain finite source values; any future cleaning rule requires scientific review.

| Case | Table.column | Locator | Index | Value | Count | Denominator | Fraction | Rule |
|---|---|---|---:|---:|---:|---:|---:|---|
<!-- candidate:0001:0078:photometry_primary.seg_area -->
| `0078:photometry_primary.seg_area` | `photometry_primary.seg_area` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 99.0 | 1,913 | 784,016 | 0.0024400012244648068 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0002:0101:photometry_primary.mag_model_f115w -->
| `0101:photometry_primary.mag_model_f115w` | `photometry_primary.mag_model_f115w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 27,311 | 784,016 | 0.034834748270443458 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0003:0102:photometry_primary.mag_model_f150w -->
| `0102:photometry_primary.mag_model_f150w` | `photometry_primary.mag_model_f150w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 17,142 | 784,016 | 0.021864349707148834 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0004:0103:photometry_primary.mag_model_f277w -->
| `0103:photometry_primary.mag_model_f277w` | `photometry_primary.mag_model_f277w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 25,849 | 784,016 | 0.032969990408359011 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0005:0104:photometry_primary.mag_model_f444w -->
| `0104:photometry_primary.mag_model_f444w` | `photometry_primary.mag_model_f444w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 34,220 | 784,016 | 0.043647068427174952 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0006:0105:photometry_primary.mag_model_hst_f814w -->
| `0105:photometry_primary.mag_model_hst_f814w` | `photometry_primary.mag_model_hst_f814w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 51,946 | 784,016 | 0.06625630089181854 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0007:0106:photometry_primary.mag_model_f770w -->
| `0106:photometry_primary.mag_model_f770w` | `photometry_primary.mag_model_f770w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 75,988 | 784,016 | 0.096921491398134732 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0008:0107:photometry_primary.mag_model_cfht_u -->
| `0107:photometry_primary.mag_model_cfht_u` | `photometry_primary.mag_model_cfht_u` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 215,357 | 784,016 | 0.27468444521540375 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0009:0108:photometry_primary.mag_model_hsc_g -->
| `0108:photometry_primary.mag_model_hsc_g` | `photometry_primary.mag_model_hsc_g` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 147,990 | 784,016 | 0.18875890287953306 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0010:0109:photometry_primary.mag_model_hsc_r -->
| `0109:photometry_primary.mag_model_hsc_r` | `photometry_primary.mag_model_hsc_r` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 119,392 | 784,016 | 0.15228260647741884 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0011:0110:photometry_primary.mag_model_hsc_i -->
| `0110:photometry_primary.mag_model_hsc_i` | `photometry_primary.mag_model_hsc_i` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 89,006 | 784,016 | 0.11352574437256382 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0012:0111:photometry_primary.mag_model_hsc_z -->
| `0111:photometry_primary.mag_model_hsc_z` | `photometry_primary.mag_model_hsc_z` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 97,494 | 784,016 | 0.12435205403971347 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0013:0112:photometry_primary.mag_model_hsc_y -->
| `0112:photometry_primary.mag_model_hsc_y` | `photometry_primary.mag_model_hsc_y` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 184,074 | 784,016 | 0.23478347380665701 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0014:0113:photometry_primary.mag_model_hsc_nb0816 -->
| `0113:photometry_primary.mag_model_hsc_nb0816` | `photometry_primary.mag_model_hsc_nb0816` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 181,332 | 784,016 | 0.23128609620211832 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0015:0114:photometry_primary.mag_model_hsc_nb0921 -->
| `0114:photometry_primary.mag_model_hsc_nb0921` | `photometry_primary.mag_model_hsc_nb0921` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 160,264 | 784,016 | 0.20441419562866064 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0016:0115:photometry_primary.mag_model_hsc_nb1010 -->
| `0115:photometry_primary.mag_model_hsc_nb1010` | `photometry_primary.mag_model_hsc_nb1010` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 327,643 | 784,016 | 0.41790346115385402 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0017:0116:photometry_primary.mag_model_uvista_y -->
| `0116:photometry_primary.mag_model_uvista_y` | `photometry_primary.mag_model_uvista_y` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 160,803 | 784,016 | 0.20510168159833472 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0018:0117:photometry_primary.mag_model_uvista_j -->
| `0117:photometry_primary.mag_model_uvista_j` | `photometry_primary.mag_model_uvista_j` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 144,200 | 784,016 | 0.18392481786085998 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0019:0118:photometry_primary.mag_model_uvista_h -->
| `0118:photometry_primary.mag_model_uvista_h` | `photometry_primary.mag_model_uvista_h` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 154,865 | 784,016 | 0.19752785657435562 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0020:0119:photometry_primary.mag_model_uvista_ks -->
| `0119:photometry_primary.mag_model_uvista_ks` | `photometry_primary.mag_model_uvista_ks` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 184,433 | 784,016 | 0.23524137262504846 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0021:0120:photometry_primary.mag_model_uvista_nb118 -->
| `0120:photometry_primary.mag_model_uvista_nb118` | `photometry_primary.mag_model_uvista_nb118` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 291,190 | 784,016 | 0.37140823656660066 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0022:0121:photometry_primary.mag_model_sc_ia484 -->
| `0121:photometry_primary.mag_model_sc_ia484` | `photometry_primary.mag_model_sc_ia484` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 229,209 | 784,016 | 0.2923524519907757 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0023:0122:photometry_primary.mag_model_sc_ia527 -->
| `0122:photometry_primary.mag_model_sc_ia527` | `photometry_primary.mag_model_sc_ia527` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 217,466 | 784,016 | 0.27737444133793188 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0024:0123:photometry_primary.mag_model_sc_ia624 -->
| `0123:photometry_primary.mag_model_sc_ia624` | `photometry_primary.mag_model_sc_ia624` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 196,826 | 784,016 | 0.25104844799085735 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0025:0124:photometry_primary.mag_model_sc_ia679 -->
| `0124:photometry_primary.mag_model_sc_ia679` | `photometry_primary.mag_model_sc_ia679` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 296,216 | 784,016 | 0.37781882002408113 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0026:0125:photometry_primary.mag_model_sc_ia738 -->
| `0125:photometry_primary.mag_model_sc_ia738` | `photometry_primary.mag_model_sc_ia738` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 206,702 | 784,016 | 0.26364512969123077 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0027:0126:photometry_primary.mag_model_sc_ia767 -->
| `0126:photometry_primary.mag_model_sc_ia767` | `photometry_primary.mag_model_sc_ia767` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 284,365 | 784,016 | 0.36270305708046774 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0028:0127:photometry_primary.mag_model_sc_ib427 -->
| `0127:photometry_primary.mag_model_sc_ib427` | `photometry_primary.mag_model_sc_ib427` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 296,480 | 784,016 | 0.37815554784596234 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0029:0128:photometry_primary.mag_model_sc_ib505 -->
| `0128:photometry_primary.mag_model_sc_ib505` | `photometry_primary.mag_model_sc_ib505` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 261,948 | 784,016 | 0.33411052835656413 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0030:0129:photometry_primary.mag_model_sc_ib574 -->
| `0129:photometry_primary.mag_model_sc_ib574` | `photometry_primary.mag_model_sc_ib574` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 314,037 | 784,016 | 0.40054922348523497 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0031:0130:photometry_primary.mag_model_sc_ib709 -->
| `0130:photometry_primary.mag_model_sc_ib709` | `photometry_primary.mag_model_sc_ib709` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 265,133 | 784,016 | 0.33817294545009285 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0032:0131:photometry_primary.mag_model_sc_ib827 -->
| `0131:photometry_primary.mag_model_sc_ib827` | `photometry_primary.mag_model_sc_ib827` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 291,955 | 784,016 | 0.37238398195955186 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0033:0132:photometry_primary.mag_model_sc_nb711 -->
| `0132:photometry_primary.mag_model_sc_nb711` | `photometry_primary.mag_model_sc_nb711` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 230,816 | 784,016 | 0.29440215505806006 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0034:0133:photometry_primary.mag_model_sc_nb816 -->
| `0133:photometry_primary.mag_model_sc_nb816` | `photometry_primary.mag_model_sc_nb816` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 301,205 | 784,016 | 0.38418221056713131 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0035:0134:photometry_primary.mag_model_irac_ch1 -->
| `0134:photometry_primary.mag_model_irac_ch1` | `photometry_primary.mag_model_irac_ch1` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 198,292 | 784,016 | 0.25291830778963692 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0036:0135:photometry_primary.mag_model_irac_ch2 -->
| `0135:photometry_primary.mag_model_irac_ch2` | `photometry_primary.mag_model_irac_ch2` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 226,558 | 784,016 | 0.28897114344605213 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0037:0136:photometry_primary.mag_model_irac_ch3 -->
| `0136:photometry_primary.mag_model_irac_ch3` | `photometry_primary.mag_model_irac_ch3` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 387,379 | 784,016 | 0.49409578375951513 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0038:0137:photometry_primary.mag_model_irac_ch4 -->
| `0137:photometry_primary.mag_model_irac_ch4` | `photometry_primary.mag_model_irac_ch4` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | 999.0 | 400,710 | 784,016 | 0.51109926328034117 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0039:0138:photometry_primary.mag_err_model_f115w -->
| `0138:photometry_primary.mag_err_model_f115w` | `photometry_primary.mag_err_model_f115w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 16,526 | 784,016 | 0.021078651456092733 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0040:0139:photometry_primary.mag_err_model_f150w -->
| `0139:photometry_primary.mag_err_model_f150w` | `photometry_primary.mag_err_model_f150w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 10,596 | 784,016 | 0.01351503030550397 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0041:0140:photometry_primary.mag_err_model_f277w -->
| `0140:photometry_primary.mag_err_model_f277w` | `photometry_primary.mag_err_model_f277w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 11,667 | 784,016 | 0.014881073855635599 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0042:0141:photometry_primary.mag_err_model_f444w -->
| `0141:photometry_primary.mag_err_model_f444w` | `photometry_primary.mag_err_model_f444w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 17,456 | 784,016 | 0.022264851737719638 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0043:0142:photometry_primary.mag_err_model_hst_f814w -->
| `0142:photometry_primary.mag_err_model_hst_f814w` | `photometry_primary.mag_err_model_hst_f814w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 33,853 | 784,016 | 0.043178965735393156 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0044:0143:photometry_primary.mag_err_model_f770w -->
| `0143:photometry_primary.mag_err_model_f770w` | `photometry_primary.mag_err_model_f770w` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 21,302 | 784,016 | 0.0271703638701251 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0045:0144:photometry_primary.mag_err_model_cfht_u -->
| `0144:photometry_primary.mag_err_model_cfht_u` | `photometry_primary.mag_err_model_cfht_u` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 117,574 | 784,016 | 0.1499637762494643 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0046:0145:photometry_primary.mag_err_model_hsc_g -->
| `0145:photometry_primary.mag_err_model_hsc_g` | `photometry_primary.mag_err_model_hsc_g` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 77,877 | 784,016 | 0.099330881002428525 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0047:0146:photometry_primary.mag_err_model_hsc_r -->
| `0146:photometry_primary.mag_err_model_hsc_r` | `photometry_primary.mag_err_model_hsc_r` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 70,147 | 784,016 | 0.089471388339013483 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0048:0147:photometry_primary.mag_err_model_hsc_i -->
| `0147:photometry_primary.mag_err_model_hsc_i` | `photometry_primary.mag_err_model_hsc_i` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 51,886 | 784,016 | 0.066179771841390997 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0049:0148:photometry_primary.mag_err_model_hsc_z -->
| `0148:photometry_primary.mag_err_model_hsc_z` | `photometry_primary.mag_err_model_hsc_z` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 63,954 | 784,016 | 0.081572314850717337 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0050:0149:photometry_primary.mag_err_model_hsc_y -->
| `0149:photometry_primary.mag_err_model_hsc_y` | `photometry_primary.mag_err_model_hsc_y` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 121,534 | 784,016 | 0.15501469357768208 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0051:0150:photometry_primary.mag_err_model_hsc_nb0816 -->
| `0150:photometry_primary.mag_err_model_hsc_nb0816` | `photometry_primary.mag_err_model_hsc_nb0816` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 134,263 | 784,016 | 0.17125033162588518 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0052:0151:photometry_primary.mag_err_model_hsc_nb0921 -->
| `0151:photometry_primary.mag_err_model_hsc_nb0921` | `photometry_primary.mag_err_model_hsc_nb0921` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 119,575 | 784,016 | 0.15251602008122284 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0053:0152:photometry_primary.mag_err_model_hsc_nb1010 -->
| `0152:photometry_primary.mag_err_model_hsc_nb1010` | `photometry_primary.mag_err_model_hsc_nb1010` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 259,318 | 784,016 | 0.3307560049794902 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0054:0153:photometry_primary.mag_err_model_uvista_y -->
| `0153:photometry_primary.mag_err_model_uvista_y` | `photometry_primary.mag_err_model_uvista_y` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 53,120 | 784,016 | 0.067753719311850785 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0055:0154:photometry_primary.mag_err_model_uvista_j -->
| `0154:photometry_primary.mag_err_model_uvista_j` | `photometry_primary.mag_err_model_uvista_j` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 53,560 | 784,016 | 0.068314932348319424 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0056:0155:photometry_primary.mag_err_model_uvista_h -->
| `0155:photometry_primary.mag_err_model_uvista_h` | `photometry_primary.mag_err_model_uvista_h` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 62,507 | 784,016 | 0.079726689251239768 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0057:0156:photometry_primary.mag_err_model_uvista_ks -->
| `0156:photometry_primary.mag_err_model_uvista_ks` | `photometry_primary.mag_err_model_uvista_ks` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 79,109 | 784,016 | 0.10090227750454073 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0058:0157:photometry_primary.mag_err_model_uvista_nb118 -->
| `0157:photometry_primary.mag_err_model_uvista_nb118` | `photometry_primary.mag_err_model_uvista_nb118` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 130,312 | 784,016 | 0.16621089365523153 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0059:0158:photometry_primary.mag_err_model_sc_ia484 -->
| `0158:photometry_primary.mag_err_model_sc_ia484` | `photometry_primary.mag_err_model_sc_ia484` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 106,292 | 784,016 | 0.13557376380073877 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0060:0159:photometry_primary.mag_err_model_sc_ia527 -->
| `0159:photometry_primary.mag_err_model_sc_ia527` | `photometry_primary.mag_err_model_sc_ia527` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 110,140 | 784,016 | 0.1404818269014918 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0061:0160:photometry_primary.mag_err_model_sc_ia624 -->
| `0160:photometry_primary.mag_err_model_sc_ia624` | `photometry_primary.mag_err_model_sc_ia624` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 82,002 | 784,016 | 0.10459225321932206 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0062:0161:photometry_primary.mag_err_model_sc_ia679 -->
| `0161:photometry_primary.mag_err_model_sc_ia679` | `photometry_primary.mag_err_model_sc_ia679` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 229,641 | 784,016 | 0.29290346115385402 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0063:0162:photometry_primary.mag_err_model_sc_ia738 -->
| `0162:photometry_primary.mag_err_model_sc_ia738` | `photometry_primary.mag_err_model_sc_ia738` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 89,093 | 784,016 | 0.11363671149568376 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0064:0163:photometry_primary.mag_err_model_sc_ia767 -->
| `0163:photometry_primary.mag_err_model_sc_ia767` | `photometry_primary.mag_err_model_sc_ia767` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 200,077 | 784,016 | 0.25519504703985635 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0065:0164:photometry_primary.mag_err_model_sc_ib427 -->
| `0164:photometry_primary.mag_err_model_sc_ib427` | `photometry_primary.mag_err_model_sc_ib427` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 224,426 | 784,016 | 0.28625181118752679 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0066:0165:photometry_primary.mag_err_model_sc_ib505 -->
| `0165:photometry_primary.mag_err_model_sc_ib505` | `photometry_primary.mag_err_model_sc_ib505` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 157,428 | 784,016 | 0.20079692251178546 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0067:0166:photometry_primary.mag_err_model_sc_ib574 -->
| `0166:photometry_primary.mag_err_model_sc_ib574` | `photometry_primary.mag_err_model_sc_ib574` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 240,092 | 784,016 | 0.30623354625415805 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0068:0167:photometry_primary.mag_err_model_sc_ib709 -->
| `0167:photometry_primary.mag_err_model_sc_ib709` | `photometry_primary.mag_err_model_sc_ib709` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 173,415 | 784,016 | 0.22118808799820411 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0069:0168:photometry_primary.mag_err_model_sc_ib827 -->
| `0168:photometry_primary.mag_err_model_sc_ib827` | `photometry_primary.mag_err_model_sc_ib827` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 209,160 | 784,016 | 0.26678026979041242 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0070:0169:photometry_primary.mag_err_model_sc_nb711 -->
| `0169:photometry_primary.mag_err_model_sc_nb711` | `photometry_primary.mag_err_model_sc_nb711` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 77,858 | 784,016 | 0.099306646803126467 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0071:0170:photometry_primary.mag_err_model_sc_nb816 -->
| `0170:photometry_primary.mag_err_model_sc_nb816` | `photometry_primary.mag_err_model_sc_nb816` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 229,227 | 784,016 | 0.29237541070590395 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0072:0171:photometry_primary.mag_err_model_irac_ch1 -->
| `0171:photometry_primary.mag_err_model_irac_ch1` | `photometry_primary.mag_err_model_irac_ch1` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 31,781 | 784,016 | 0.040536162527295361 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0073:0172:photometry_primary.mag_err_model_irac_ch2 -->
| `0172:photometry_primary.mag_err_model_irac_ch2` | `photometry_primary.mag_err_model_irac_ch2` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 38,222 | 784,016 | 0.048751556090692025 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0074:0173:photometry_primary.mag_err_model_irac_ch3 -->
| `0173:photometry_primary.mag_err_model_irac_ch3` | `photometry_primary.mag_err_model_irac_ch3` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 89,234 | 784,016 | 0.11381655476418849 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0075:0174:photometry_primary.mag_err_model_irac_ch4 -->
| `0174:photometry_primary.mag_err_model_irac_ch4` | `photometry_primary.mag_err_model_irac_ch4` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 92,130 | 784,016 | 0.1175103569314912 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0076:0218:photometry_primary.flux_err_uncal_model_cfht_u -->
| `0218:photometry_primary.flux_err_uncal_model_cfht_u` | `photometry_primary.flux_err_uncal_model_cfht_u` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 2,600 | 784,016 | 0.0033162588518601661 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0077:0219:photometry_primary.flux_err_uncal_model_hsc_g -->
| `0219:photometry_primary.flux_err_uncal_model_hsc_g` | `photometry_primary.flux_err_uncal_model_hsc_g` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 2,474 | 784,016 | 0.0031555478459623274 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0078:0220:photometry_primary.flux_err_uncal_model_hsc_r -->
| `0220:photometry_primary.flux_err_uncal_model_hsc_r` | `photometry_primary.flux_err_uncal_model_hsc_r` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,766 | 784,016 | 0.0022525050509173282 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0079:0221:photometry_primary.flux_err_uncal_model_hsc_i -->
| `0221:photometry_primary.flux_err_uncal_model_hsc_i` | `photometry_primary.flux_err_uncal_model_hsc_i` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,059 | 784,016 | 0.0013507377400461215 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0080:0222:photometry_primary.flux_err_uncal_model_hsc_z -->
| `0222:photometry_primary.flux_err_uncal_model_hsc_z` | `photometry_primary.flux_err_uncal_model_hsc_z` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,022 | 784,016 | 0.0013035448256158038 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0081:0223:photometry_primary.flux_err_uncal_model_hsc_y -->
| `0223:photometry_primary.flux_err_uncal_model_hsc_y` | `photometry_primary.flux_err_uncal_model_hsc_y` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,994 | 784,016 | 0.0025433154425419892 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0082:0224:photometry_primary.flux_err_uncal_model_hsc_nb0816 -->
| `0224:photometry_primary.flux_err_uncal_model_hsc_nb0816` | `photometry_primary.flux_err_uncal_model_hsc_nb0816` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,566 | 784,016 | 0.0019974082161588538 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0083:0225:photometry_primary.flux_err_uncal_model_hsc_nb0921 -->
| `0225:photometry_primary.flux_err_uncal_model_hsc_nb0921` | `photometry_primary.flux_err_uncal_model_hsc_nb0921` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,119 | 784,016 | 0.0014272667904736639 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0084:0226:photometry_primary.flux_err_uncal_model_hsc_nb1010 -->
| `0226:photometry_primary.flux_err_uncal_model_hsc_nb1010` | `photometry_primary.flux_err_uncal_model_hsc_nb1010` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 2,391 | 784,016 | 0.0030496826595375606 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0085:0227:photometry_primary.flux_err_uncal_model_uvista_y -->
| `0227:photometry_primary.flux_err_uncal_model_uvista_y` | `photometry_primary.flux_err_uncal_model_uvista_y` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,264 | 784,016 | 0.0016122119956735576 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0086:0231:photometry_primary.flux_err_uncal_model_uvista_nb118 -->
| `0231:photometry_primary.flux_err_uncal_model_uvista_nb118` | `photometry_primary.flux_err_uncal_model_uvista_nb118` | HDU 1 [PHOTOMETRY HOTCOLD AND SE++] | scalar | -999.0 | 1,222 | 784,016 | 0.001558641660374278 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0087:0288:lephare.zfinal -->
| `0288:lephare.zfinal` | `lephare.zfinal` | HDU 1 [LEPHARE] | scalar | -99.0 | 92,226 | 784,016 | 0.11763280341217526 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0088:0302:lephare.ebv_minchi2 -->
| `0302:lephare.ebv_minchi2` | `lephare.ebv_minchi2` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0089:0303:lephare.law_minchi2 -->
| `0303:lephare.law_minchi2` | `lephare.law_minchi2` | HDU 1 [LEPHARE] | scalar | -999 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0090:0305:lephare.mass_minchi2 -->
| `0305:lephare.mass_minchi2` | `lephare.mass_minchi2` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0091:0306:lephare.sfr_minchi2 -->
| `0306:lephare.sfr_minchi2` | `lephare.sfr_minchi2` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0092:0307:lephare.ssfr_minchi2 -->
| `0307:lephare.ssfr_minchi2` | `lephare.ssfr_minchi2` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0093:0320:lephare.l_nuv -->
| `0320:lephare.l_nuv` | `lephare.l_nuv` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0094:0321:lephare.l_r -->
| `0321:lephare.l_r` | `lephare.l_r` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0095:0322:lephare.l_k -->
| `0322:lephare.l_k` | `lephare.l_k` | HDU 1 [LEPHARE] | scalar | -999.0 | 5,397 | 784,016 | 0.0068837880859574296 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0096:0331:photometry_aper.mag_aper_f115w -->
| `0331:photometry_aper.mag_aper_f115w` | `photometry_aper.mag_aper_f115w` | HDU 1 [SE++APER] | 0 | 999.0 | 33,464 | 784,016 | 0.04268280239178792 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0097:0331:photometry_aper.mag_aper_f115w -->
| `0331:photometry_aper.mag_aper_f115w` | `photometry_aper.mag_aper_f115w` | HDU 1 [SE++APER] | 1 | 999.0 | 26,722 | 784,016 | 0.034083488092079756 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0098:0331:photometry_aper.mag_aper_f115w -->
| `0331:photometry_aper.mag_aper_f115w` | `photometry_aper.mag_aper_f115w` | HDU 1 [SE++APER] | 2 | 999.0 | 53,119 | 784,016 | 0.067752443827676992 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0099:0331:photometry_aper.mag_aper_f115w -->
| `0331:photometry_aper.mag_aper_f115w` | `photometry_aper.mag_aper_f115w` | HDU 1 [SE++APER] | 3 | 999.0 | 133,610 | 784,016 | 0.17041744046039878 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0100:0331:photometry_aper.mag_aper_f115w -->
| `0331:photometry_aper.mag_aper_f115w` | `photometry_aper.mag_aper_f115w` | HDU 1 [SE++APER] | 4 | 999.0 | 202,608 | 784,016 | 0.25842329748372483 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0101:0332:photometry_aper.mag_aper_f150w -->
| `0332:photometry_aper.mag_aper_f150w` | `photometry_aper.mag_aper_f150w` | HDU 1 [SE++APER] | 0 | 999.0 | 18,911 | 784,016 | 0.024120681210587538 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0102:0332:photometry_aper.mag_aper_f150w -->
| `0332:photometry_aper.mag_aper_f150w` | `photometry_aper.mag_aper_f150w` | HDU 1 [SE++APER] | 1 | 999.0 | 15,351 | 784,016 | 0.019579957551886695 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0103:0332:photometry_aper.mag_aper_f150w -->
| `0332:photometry_aper.mag_aper_f150w` | `photometry_aper.mag_aper_f150w` | HDU 1 [SE++APER] | 2 | 999.0 | 29,659 | 784,016 | 0.037829585110507949 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0104:0332:photometry_aper.mag_aper_f150w -->
| `0332:photometry_aper.mag_aper_f150w` | `photometry_aper.mag_aper_f150w` | HDU 1 [SE++APER] | 3 | 999.0 | 95,777 | 784,016 | 0.12216204771331197 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0105:0332:photometry_aper.mag_aper_f150w -->
| `0332:photometry_aper.mag_aper_f150w` | `photometry_aper.mag_aper_f150w` | HDU 1 [SE++APER] | 4 | 999.0 | 164,137 | 784,016 | 0.2093541458337585 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0106:0333:photometry_aper.mag_aper_f277w -->
| `0333:photometry_aper.mag_aper_f277w` | `photometry_aper.mag_aper_f277w` | HDU 1 [SE++APER] | 0 | 999.0 | 18,828 | 784,016 | 0.024014816024162774 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0107:0333:photometry_aper.mag_aper_f277w -->
| `0333:photometry_aper.mag_aper_f277w` | `photometry_aper.mag_aper_f277w` | HDU 1 [SE++APER] | 1 | 999.0 | 18,145 | 784,016 | 0.023143660333462584 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0108:0333:photometry_aper.mag_aper_f277w -->
| `0333:photometry_aper.mag_aper_f277w` | `photometry_aper.mag_aper_f277w` | HDU 1 [SE++APER] | 2 | 999.0 | 22,959 | 784,016 | 0.029283841146099058 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0109:0333:photometry_aper.mag_aper_f277w -->
| `0333:photometry_aper.mag_aper_f277w` | `photometry_aper.mag_aper_f277w` | HDU 1 [SE++APER] | 3 | 999.0 | 44,695 | 784,016 | 0.057007765147650047 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0110:0333:photometry_aper.mag_aper_f277w -->
| `0333:photometry_aper.mag_aper_f277w` | `photometry_aper.mag_aper_f277w` | HDU 1 [SE++APER] | 4 | 999.0 | 85,369 | 784,016 | 0.10888680843248097 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0111:0334:photometry_aper.mag_aper_f444w -->
| `0334:photometry_aper.mag_aper_f444w` | `photometry_aper.mag_aper_f444w` | HDU 1 [SE++APER] | 0 | 999.0 | 30,665 | 784,016 | 0.039112722189343072 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0112:0334:photometry_aper.mag_aper_f444w -->
| `0334:photometry_aper.mag_aper_f444w` | `photometry_aper.mag_aper_f444w` | HDU 1 [SE++APER] | 1 | 999.0 | 24,873 | 784,016 | 0.03172511785473766 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0113:0334:photometry_aper.mag_aper_f444w -->
| `0334:photometry_aper.mag_aper_f444w` | `photometry_aper.mag_aper_f444w` | HDU 1 [SE++APER] | 2 | 999.0 | 34,530 | 784,016 | 0.044042468521050593 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0114:0334:photometry_aper.mag_aper_f444w -->
| `0334:photometry_aper.mag_aper_f444w` | `photometry_aper.mag_aper_f444w` | HDU 1 [SE++APER] | 3 | 999.0 | 73,460 | 784,016 | 0.093697067406787612 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0115:0334:photometry_aper.mag_aper_f444w -->
| `0334:photometry_aper.mag_aper_f444w` | `photometry_aper.mag_aper_f444w` | HDU 1 [SE++APER] | 4 | 999.0 | 124,865 | 784,016 | 0.15926333136058449 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0116:0335:photometry_aper.mag_aper_hst_f814w -->
| `0335:photometry_aper.mag_aper_hst_f814w` | `photometry_aper.mag_aper_hst_f814w` | HDU 1 [SE++APER] | 0 | 999.0 | 75,271 | 784,016 | 0.096006969245525597 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0117:0335:photometry_aper.mag_aper_hst_f814w -->
| `0335:photometry_aper.mag_aper_hst_f814w` | `photometry_aper.mag_aper_hst_f814w` | HDU 1 [SE++APER] | 1 | 999.0 | 57,877 | 784,016 | 0.073821197526581089 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0118:0335:photometry_aper.mag_aper_hst_f814w -->
| `0335:photometry_aper.mag_aper_hst_f814w` | `photometry_aper.mag_aper_hst_f814w` | HDU 1 [SE++APER] | 2 | 999.0 | 69,497 | 784,016 | 0.088642323626048444 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0119:0335:photometry_aper.mag_aper_hst_f814w -->
| `0335:photometry_aper.mag_aper_hst_f814w` | `photometry_aper.mag_aper_hst_f814w` | HDU 1 [SE++APER] | 3 | 999.0 | 119,346 | 784,016 | 0.15222393420542438 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0120:0335:photometry_aper.mag_aper_hst_f814w -->
| `0335:photometry_aper.mag_aper_hst_f814w` | `photometry_aper.mag_aper_hst_f814w` | HDU 1 [SE++APER] | 4 | 999.0 | 163,982 | 784,016 | 0.20915644578682069 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0121:0336:photometry_aper.mag_aper_f770w -->
| `0336:photometry_aper.mag_aper_f770w` | `photometry_aper.mag_aper_f770w` | HDU 1 [SE++APER] | 0 | 999.0 | 77,550 | 784,016 | 0.09891379767759842 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0122:0336:photometry_aper.mag_aper_f770w -->
| `0336:photometry_aper.mag_aper_f770w` | `photometry_aper.mag_aper_f770w` | HDU 1 [SE++APER] | 1 | 999.0 | 69,550 | 784,016 | 0.088709924287259448 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0123:0336:photometry_aper.mag_aper_f770w -->
| `0336:photometry_aper.mag_aper_f770w` | `photometry_aper.mag_aper_f770w` | HDU 1 [SE++APER] | 2 | 999.0 | 70,266 | 784,016 | 0.089623170955694775 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0124:0336:photometry_aper.mag_aper_f770w -->
| `0336:photometry_aper.mag_aper_f770w` | `photometry_aper.mag_aper_f770w` | HDU 1 [SE++APER] | 3 | 999.0 | 89,924 | 784,016 | 0.11469663884410522 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0125:0336:photometry_aper.mag_aper_f770w -->
| `0336:photometry_aper.mag_aper_f770w` | `photometry_aper.mag_aper_f770w` | HDU 1 [SE++APER] | 4 | 999.0 | 106,149 | 784,016 | 0.13539136956388645 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0126:0337:photometry_aper.mag_aper_cfht_u -->
| `0337:photometry_aper.mag_aper_cfht_u` | `photometry_aper.mag_aper_cfht_u` | HDU 1 [SE++APER] | 0 | 999.0 | 96,489 | 784,016 | 0.12307019244505214 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0127:0337:photometry_aper.mag_aper_cfht_u -->
| `0337:photometry_aper.mag_aper_cfht_u` | `photometry_aper.mag_aper_cfht_u` | HDU 1 [SE++APER] | 1 | 999.0 | 172,985 | 784,016 | 0.2206396298034734 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0128:0337:photometry_aper.mag_aper_cfht_u -->
| `0337:photometry_aper.mag_aper_cfht_u` | `photometry_aper.mag_aper_cfht_u` | HDU 1 [SE++APER] | 2 | 999.0 | 160,010 | 784,016 | 0.20409022264851737 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0129:0337:photometry_aper.mag_aper_cfht_u -->
| `0337:photometry_aper.mag_aper_cfht_u` | `photometry_aper.mag_aper_cfht_u` | HDU 1 [SE++APER] | 3 | 999.0 | 167,111 | 784,016 | 0.21314743576661702 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0130:0337:photometry_aper.mag_aper_cfht_u -->
| `0337:photometry_aper.mag_aper_cfht_u` | `photometry_aper.mag_aper_cfht_u` | HDU 1 [SE++APER] | 4 | 999.0 | 185,658 | 784,016 | 0.23680384073794411 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0131:0338:photometry_aper.mag_aper_hsc_g -->
| `0338:photometry_aper.mag_aper_hsc_g` | `photometry_aper.mag_aper_hsc_g` | HDU 1 [SE++APER] | 0 | 999.0 | 46,335 | 784,016 | 0.059099559192669536 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0132:0338:photometry_aper.mag_aper_hsc_g -->
| `0338:photometry_aper.mag_aper_hsc_g` | `photometry_aper.mag_aper_hsc_g` | HDU 1 [SE++APER] | 1 | 999.0 | 101,837 | 784,016 | 0.12989148180649374 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0133:0338:photometry_aper.mag_aper_hsc_g -->
| `0338:photometry_aper.mag_aper_hsc_g` | `photometry_aper.mag_aper_hsc_g` | HDU 1 [SE++APER] | 2 | 999.0 | 91,702 | 784,016 | 0.11696444970510805 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0134:0338:photometry_aper.mag_aper_hsc_g -->
| `0338:photometry_aper.mag_aper_hsc_g` | `photometry_aper.mag_aper_hsc_g` | HDU 1 [SE++APER] | 3 | 999.0 | 99,057 | 784,016 | 0.12634563580335095 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0135:0338:photometry_aper.mag_aper_hsc_g -->
| `0338:photometry_aper.mag_aper_hsc_g` | `photometry_aper.mag_aper_hsc_g` | HDU 1 [SE++APER] | 4 | 999.0 | 113,578 | 784,016 | 0.14486694149098997 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0136:0339:photometry_aper.mag_aper_hsc_r -->
| `0339:photometry_aper.mag_aper_hsc_r` | `photometry_aper.mag_aper_hsc_r` | HDU 1 [SE++APER] | 0 | 999.0 | 37,670 | 784,016 | 0.04804748882675864 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0137:0339:photometry_aper.mag_aper_hsc_r -->
| `0339:photometry_aper.mag_aper_hsc_r` | `photometry_aper.mag_aper_hsc_r` | HDU 1 [SE++APER] | 1 | 999.0 | 81,311 | 784,016 | 0.10371089365523152 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0138:0339:photometry_aper.mag_aper_hsc_r -->
| `0339:photometry_aper.mag_aper_hsc_r` | `photometry_aper.mag_aper_hsc_r` | HDU 1 [SE++APER] | 2 | 999.0 | 70,882 | 784,016 | 0.090408869206750883 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0139:0339:photometry_aper.mag_aper_hsc_r -->
| `0339:photometry_aper.mag_aper_hsc_r` | `photometry_aper.mag_aper_hsc_r` | HDU 1 [SE++APER] | 3 | 999.0 | 80,682 | 784,016 | 0.10290861410991613 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0140:0339:photometry_aper.mag_aper_hsc_r -->
| `0339:photometry_aper.mag_aper_hsc_r` | `photometry_aper.mag_aper_hsc_r` | HDU 1 [SE++APER] | 4 | 999.0 | 100,167 | 784,016 | 0.1277614232362605 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0141:0340:photometry_aper.mag_aper_hsc_i -->
| `0340:photometry_aper.mag_aper_hsc_i` | `photometry_aper.mag_aper_hsc_i` | HDU 1 [SE++APER] | 0 | 999.0 | 28,070 | 784,016 | 0.03580284075835187 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0142:0340:photometry_aper.mag_aper_hsc_i -->
| `0340:photometry_aper.mag_aper_hsc_i` | `photometry_aper.mag_aper_hsc_i` | HDU 1 [SE++APER] | 1 | 999.0 | 60,352 | 784,016 | 0.076978020856717205 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0143:0340:photometry_aper.mag_aper_hsc_i -->
| `0340:photometry_aper.mag_aper_hsc_i` | `photometry_aper.mag_aper_hsc_i` | HDU 1 [SE++APER] | 2 | 999.0 | 53,153 | 784,016 | 0.067795810289585923 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0144:0340:photometry_aper.mag_aper_hsc_i -->
| `0340:photometry_aper.mag_aper_hsc_i` | `photometry_aper.mag_aper_hsc_i` | HDU 1 [SE++APER] | 3 | 999.0 | 62,510 | 784,016 | 0.079730515703761148 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0145:0340:photometry_aper.mag_aper_hsc_i -->
| `0340:photometry_aper.mag_aper_hsc_i` | `photometry_aper.mag_aper_hsc_i` | HDU 1 [SE++APER] | 4 | 999.0 | 80,705 | 784,016 | 0.10293795024591335 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0146:0341:photometry_aper.mag_aper_hsc_z -->
| `0341:photometry_aper.mag_aper_hsc_z` | `photometry_aper.mag_aper_hsc_z` | HDU 1 [SE++APER] | 0 | 999.0 | 34,436 | 784,016 | 0.043922573008714105 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0147:0341:photometry_aper.mag_aper_hsc_z -->
| `0341:photometry_aper.mag_aper_hsc_z` | `photometry_aper.mag_aper_hsc_z` | HDU 1 [SE++APER] | 1 | 999.0 | 72,032 | 784,016 | 0.091875676006612103 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0148:0341:photometry_aper.mag_aper_hsc_z -->
| `0341:photometry_aper.mag_aper_hsc_z` | `photometry_aper.mag_aper_hsc_z` | HDU 1 [SE++APER] | 2 | 999.0 | 58,976 | 784,016 | 0.075222954633578906 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0149:0341:photometry_aper.mag_aper_hsc_z -->
| `0341:photometry_aper.mag_aper_hsc_z` | `photometry_aper.mag_aper_hsc_z` | HDU 1 [SE++APER] | 3 | 999.0 | 70,751 | 784,016 | 0.090241780779984085 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0150:0341:photometry_aper.mag_aper_hsc_z -->
| `0341:photometry_aper.mag_aper_hsc_z` | `photometry_aper.mag_aper_hsc_z` | HDU 1 [SE++APER] | 4 | 999.0 | 97,126 | 784,016 | 0.12388267586375788 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0151:0342:photometry_aper.mag_aper_hsc_y -->
| `0342:photometry_aper.mag_aper_hsc_y` | `photometry_aper.mag_aper_hsc_y` | HDU 1 [SE++APER] | 0 | 999.0 | 64,179 | 784,016 | 0.081859298789820623 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0152:0342:photometry_aper.mag_aper_hsc_y -->
| `0342:photometry_aper.mag_aper_hsc_y` | `photometry_aper.mag_aper_hsc_y` | HDU 1 [SE++APER] | 1 | 999.0 | 137,982 | 784,016 | 0.17599385726821901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0153:0342:photometry_aper.mag_aper_hsc_y -->
| `0342:photometry_aper.mag_aper_hsc_y` | `photometry_aper.mag_aper_hsc_y` | HDU 1 [SE++APER] | 2 | 999.0 | 112,763 | 784,016 | 0.14382742188934919 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0154:0342:photometry_aper.mag_aper_hsc_y -->
| `0342:photometry_aper.mag_aper_hsc_y` | `photometry_aper.mag_aper_hsc_y` | HDU 1 [SE++APER] | 3 | 999.0 | 125,380 | 784,016 | 0.15992020571008755 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0155:0342:photometry_aper.mag_aper_hsc_y -->
| `0342:photometry_aper.mag_aper_hsc_y` | `photometry_aper.mag_aper_hsc_y` | HDU 1 [SE++APER] | 4 | 999.0 | 159,988 | 784,016 | 0.20406216199669394 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0156:0343:photometry_aper.mag_aper_hsc_nb0816 -->
| `0343:photometry_aper.mag_aper_hsc_nb0816` | `photometry_aper.mag_aper_hsc_nb0816` | HDU 1 [SE++APER] | 0 | 999.0 | 71,167 | 784,016 | 0.090772382196281712 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0157:0343:photometry_aper.mag_aper_hsc_nb0816 -->
| `0343:photometry_aper.mag_aper_hsc_nb0816` | `photometry_aper.mag_aper_hsc_nb0816` | HDU 1 [SE++APER] | 1 | 999.0 | 153,043 | 784,016 | 0.19520392440970594 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0158:0343:photometry_aper.mag_aper_hsc_nb0816 -->
| `0343:photometry_aper.mag_aper_hsc_nb0816` | `photometry_aper.mag_aper_hsc_nb0816` | HDU 1 [SE++APER] | 2 | 999.0 | 123,831 | 784,016 | 0.15794448072488318 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0159:0343:photometry_aper.mag_aper_hsc_nb0816 -->
| `0343:photometry_aper.mag_aper_hsc_nb0816` | `photometry_aper.mag_aper_hsc_nb0816` | HDU 1 [SE++APER] | 3 | 999.0 | 132,091 | 784,016 | 0.16847998000040815 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0160:0343:photometry_aper.mag_aper_hsc_nb0816 -->
| `0343:photometry_aper.mag_aper_hsc_nb0816` | `photometry_aper.mag_aper_hsc_nb0816` | HDU 1 [SE++APER] | 4 | 999.0 | 166,388 | 784,016 | 0.21222526070896514 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0161:0344:photometry_aper.mag_aper_hsc_nb0921 -->
| `0344:photometry_aper.mag_aper_hsc_nb0921` | `photometry_aper.mag_aper_hsc_nb0921` | HDU 1 [SE++APER] | 0 | 999.0 | 65,352 | 784,016 | 0.083355441725679061 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0162:0344:photometry_aper.mag_aper_hsc_nb0921 -->
| `0344:photometry_aper.mag_aper_hsc_nb0921` | `photometry_aper.mag_aper_hsc_nb0921` | HDU 1 [SE++APER] | 1 | 999.0 | 139,508 | 784,016 | 0.17794024611742618 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0163:0344:photometry_aper.mag_aper_hsc_nb0921 -->
| `0344:photometry_aper.mag_aper_hsc_nb0921` | `photometry_aper.mag_aper_hsc_nb0921` | HDU 1 [SE++APER] | 2 | 999.0 | 110,624 | 784,016 | 0.14109916124160732 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0164:0344:photometry_aper.mag_aper_hsc_nb0921 -->
| `0344:photometry_aper.mag_aper_hsc_nb0921` | `photometry_aper.mag_aper_hsc_nb0921` | HDU 1 [SE++APER] | 3 | 999.0 | 119,888 | 784,016 | 0.15291524662761985 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0165:0344:photometry_aper.mag_aper_hsc_nb0921 -->
| `0344:photometry_aper.mag_aper_hsc_nb0921` | `photometry_aper.mag_aper_hsc_nb0921` | HDU 1 [SE++APER] | 4 | 999.0 | 155,196 | 784,016 | 0.19795004183588091 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0166:0345:photometry_aper.mag_aper_hsc_nb1010 -->
| `0345:photometry_aper.mag_aper_hsc_nb1010` | `photometry_aper.mag_aper_hsc_nb1010` | HDU 1 [SE++APER] | 0 | 999.0 | 127,170 | 784,016 | 0.16220332238117591 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0167:0345:photometry_aper.mag_aper_hsc_nb1010 -->
| `0345:photometry_aper.mag_aper_hsc_nb1010` | `photometry_aper.mag_aper_hsc_nb1010` | HDU 1 [SE++APER] | 1 | 999.0 | 290,781 | 784,016 | 0.3708865635395196 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0168:0345:photometry_aper.mag_aper_hsc_nb1010 -->
| `0345:photometry_aper.mag_aper_hsc_nb1010` | `photometry_aper.mag_aper_hsc_nb1010` | HDU 1 [SE++APER] | 2 | 999.0 | 265,953 | 784,016 | 0.33921884247260259 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0169:0345:photometry_aper.mag_aper_hsc_nb1010 -->
| `0345:photometry_aper.mag_aper_hsc_nb1010` | `photometry_aper.mag_aper_hsc_nb1010` | HDU 1 [SE++APER] | 3 | 999.0 | 269,167 | 784,016 | 0.34331824860717131 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0170:0345:photometry_aper.mag_aper_hsc_nb1010 -->
| `0345:photometry_aper.mag_aper_hsc_nb1010` | `photometry_aper.mag_aper_hsc_nb1010` | HDU 1 [SE++APER] | 4 | 999.0 | 298,697 | 784,016 | 0.38098329625926003 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0171:0346:photometry_aper.mag_aper_uvista_y -->
| `0346:photometry_aper.mag_aper_uvista_y` | `photometry_aper.mag_aper_uvista_y` | HDU 1 [SE++APER] | 0 | 999.0 | 51,229 | 784,016 | 0.065341778739209405 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0172:0346:photometry_aper.mag_aper_uvista_y -->
| `0346:photometry_aper.mag_aper_uvista_y` | `photometry_aper.mag_aper_uvista_y` | HDU 1 [SE++APER] | 1 | 999.0 | 95,356 | 784,016 | 0.12162506887614538 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0173:0346:photometry_aper.mag_aper_uvista_y -->
| `0346:photometry_aper.mag_aper_uvista_y` | `photometry_aper.mag_aper_uvista_y` | HDU 1 [SE++APER] | 2 | 999.0 | 93,576 | 784,016 | 0.11935470704679496 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0174:0346:photometry_aper.mag_aper_uvista_y -->
| `0346:photometry_aper.mag_aper_uvista_y` | `photometry_aper.mag_aper_uvista_y` | HDU 1 [SE++APER] | 3 | 999.0 | 102,023 | 784,016 | 0.13012872186281912 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0175:0346:photometry_aper.mag_aper_uvista_y -->
| `0346:photometry_aper.mag_aper_uvista_y` | `photometry_aper.mag_aper_uvista_y` | HDU 1 [SE++APER] | 4 | 999.0 | 123,928 | 784,016 | 0.15806820268974103 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0176:0347:photometry_aper.mag_aper_uvista_j -->
| `0347:photometry_aper.mag_aper_uvista_j` | `photometry_aper.mag_aper_uvista_j` | HDU 1 [SE++APER] | 0 | 999.0 | 46,833 | 784,016 | 0.059734750311218138 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0177:0347:photometry_aper.mag_aper_uvista_j -->
| `0347:photometry_aper.mag_aper_uvista_j` | `photometry_aper.mag_aper_uvista_j` | HDU 1 [SE++APER] | 1 | 999.0 | 86,814 | 784,016 | 0.11072988306361095 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0178:0347:photometry_aper.mag_aper_uvista_j -->
| `0347:photometry_aper.mag_aper_uvista_j` | `photometry_aper.mag_aper_uvista_j` | HDU 1 [SE++APER] | 2 | 999.0 | 84,394 | 784,016 | 0.10764321136303341 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0179:0347:photometry_aper.mag_aper_uvista_j -->
| `0347:photometry_aper.mag_aper_uvista_j` | `photometry_aper.mag_aper_uvista_j` | HDU 1 [SE++APER] | 3 | 999.0 | 92,842 | 784,016 | 0.11841850166323137 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0180:0347:photometry_aper.mag_aper_uvista_j -->
| `0347:photometry_aper.mag_aper_uvista_j` | `photometry_aper.mag_aper_uvista_j` | HDU 1 [SE++APER] | 4 | 999.0 | 115,987 | 784,016 | 0.14793958286565581 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0181:0348:photometry_aper.mag_aper_uvista_h -->
| `0348:photometry_aper.mag_aper_uvista_h` | `photometry_aper.mag_aper_uvista_h` | HDU 1 [SE++APER] | 0 | 999.0 | 54,490 | 784,016 | 0.069501132629946324 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0182:0348:photometry_aper.mag_aper_uvista_h -->
| `0348:photometry_aper.mag_aper_uvista_h` | `photometry_aper.mag_aper_uvista_h` | HDU 1 [SE++APER] | 1 | 999.0 | 100,805 | 784,016 | 0.12857518213914002 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0183:0348:photometry_aper.mag_aper_uvista_h -->
| `0348:photometry_aper.mag_aper_uvista_h` | `photometry_aper.mag_aper_uvista_h` | HDU 1 [SE++APER] | 2 | 999.0 | 97,324 | 784,016 | 0.12413522173016878 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0184:0348:photometry_aper.mag_aper_uvista_h -->
| `0348:photometry_aper.mag_aper_uvista_h` | `photometry_aper.mag_aper_uvista_h` | HDU 1 [SE++APER] | 3 | 999.0 | 104,958 | 784,016 | 0.13387226791289975 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0185:0348:photometry_aper.mag_aper_uvista_h -->
| `0348:photometry_aper.mag_aper_uvista_h` | `photometry_aper.mag_aper_uvista_h` | HDU 1 [SE++APER] | 4 | 999.0 | 130,205 | 784,016 | 0.16607441684863575 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0186:0349:photometry_aper.mag_aper_uvista_ks -->
| `0349:photometry_aper.mag_aper_uvista_ks` | `photometry_aper.mag_aper_uvista_ks` | HDU 1 [SE++APER] | 0 | 999.0 | 70,814 | 784,016 | 0.090322136282933008 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0187:0349:photometry_aper.mag_aper_uvista_ks -->
| `0349:photometry_aper.mag_aper_uvista_ks` | `photometry_aper.mag_aper_uvista_ks` | HDU 1 [SE++APER] | 1 | 999.0 | 130,794 | 784,016 | 0.16682567702699944 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0188:0349:photometry_aper.mag_aper_uvista_ks -->
| `0349:photometry_aper.mag_aper_uvista_ks` | `photometry_aper.mag_aper_uvista_ks` | HDU 1 [SE++APER] | 2 | 999.0 | 125,864 | 784,016 | 0.16053754005020307 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0189:0349:photometry_aper.mag_aper_uvista_ks -->
| `0349:photometry_aper.mag_aper_uvista_ks` | `photometry_aper.mag_aper_uvista_ks` | HDU 1 [SE++APER] | 3 | 999.0 | 131,525 | 784,016 | 0.16775805595804166 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0190:0349:photometry_aper.mag_aper_uvista_ks -->
| `0349:photometry_aper.mag_aper_uvista_ks` | `photometry_aper.mag_aper_uvista_ks` | HDU 1 [SE++APER] | 4 | 999.0 | 158,045 | 784,016 | 0.20158389624701537 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0191:0350:photometry_aper.mag_aper_uvista_nb118 -->
| `0350:photometry_aper.mag_aper_uvista_nb118` | `photometry_aper.mag_aper_uvista_nb118` | HDU 1 [SE++APER] | 0 | 999.0 | 130,779 | 784,016 | 0.16680654476439255 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0192:0350:photometry_aper.mag_aper_uvista_nb118 -->
| `0350:photometry_aper.mag_aper_uvista_nb118` | `photometry_aper.mag_aper_uvista_nb118` | HDU 1 [SE++APER] | 1 | 999.0 | 243,284 | 784,016 | 0.31030489173690334 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0193:0350:photometry_aper.mag_aper_uvista_nb118 -->
| `0350:photometry_aper.mag_aper_uvista_nb118` | `photometry_aper.mag_aper_uvista_nb118` | HDU 1 [SE++APER] | 2 | 999.0 | 237,513 | 784,016 | 0.30294407256994754 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0194:0350:photometry_aper.mag_aper_uvista_nb118 -->
| `0350:photometry_aper.mag_aper_uvista_nb118` | `photometry_aper.mag_aper_uvista_nb118` | HDU 1 [SE++APER] | 3 | 999.0 | 237,862 | 784,016 | 0.30338921654660111 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0195:0350:photometry_aper.mag_aper_uvista_nb118 -->
| `0350:photometry_aper.mag_aper_uvista_nb118` | `photometry_aper.mag_aper_uvista_nb118` | HDU 1 [SE++APER] | 4 | 999.0 | 257,733 | 784,016 | 0.32873436256402933 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0196:0351:photometry_aper.mag_aper_sc_ia484 -->
| `0351:photometry_aper.mag_aper_sc_ia484` | `photometry_aper.mag_aper_sc_ia484` | HDU 1 [SE++APER] | 0 | 999.0 | 103,880 | 784,016 | 0.13249729597355156 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0197:0351:photometry_aper.mag_aper_sc_ia484 -->
| `0351:photometry_aper.mag_aper_sc_ia484` | `photometry_aper.mag_aper_sc_ia484` | HDU 1 [SE++APER] | 1 | 999.0 | 192,856 | 784,016 | 0.24598477582090161 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0198:0351:photometry_aper.mag_aper_sc_ia484 -->
| `0351:photometry_aper.mag_aper_sc_ia484` | `photometry_aper.mag_aper_sc_ia484` | HDU 1 [SE++APER] | 2 | 999.0 | 186,414 | 784,016 | 0.23776810677333116 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0199:0351:photometry_aper.mag_aper_sc_ia484 -->
| `0351:photometry_aper.mag_aper_sc_ia484` | `photometry_aper.mag_aper_sc_ia484` | HDU 1 [SE++APER] | 3 | 999.0 | 174,629 | 784,016 | 0.22273652578518804 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0200:0351:photometry_aper.mag_aper_sc_ia484 -->
| `0351:photometry_aper.mag_aper_sc_ia484` | `photometry_aper.mag_aper_sc_ia484` | HDU 1 [SE++APER] | 4 | 999.0 | 186,025 | 784,016 | 0.23727194342972593 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0201:0352:photometry_aper.mag_aper_sc_ia527 -->
| `0352:photometry_aper.mag_aper_sc_ia527` | `photometry_aper.mag_aper_sc_ia527` | HDU 1 [SE++APER] | 0 | 999.0 | 103,761 | 784,016 | 0.13234551335687028 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0202:0352:photometry_aper.mag_aper_sc_ia527 -->
| `0352:photometry_aper.mag_aper_sc_ia527` | `photometry_aper.mag_aper_sc_ia527` | HDU 1 [SE++APER] | 1 | 999.0 | 193,404 | 784,016 | 0.24668374114813985 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0203:0352:photometry_aper.mag_aper_sc_ia527 -->
| `0352:photometry_aper.mag_aper_sc_ia527` | `photometry_aper.mag_aper_sc_ia527` | HDU 1 [SE++APER] | 2 | 999.0 | 186,610 | 784,016 | 0.23801810167139445 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0204:0352:photometry_aper.mag_aper_sc_ia527 -->
| `0352:photometry_aper.mag_aper_sc_ia527` | `photometry_aper.mag_aper_sc_ia527` | HDU 1 [SE++APER] | 3 | 999.0 | 168,043 | 784,016 | 0.21433618701659149 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0205:0352:photometry_aper.mag_aper_sc_ia527 -->
| `0352:photometry_aper.mag_aper_sc_ia527` | `photometry_aper.mag_aper_sc_ia527` | HDU 1 [SE++APER] | 4 | 999.0 | 176,941 | 784,016 | 0.22568544519499603 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0206:0353:photometry_aper.mag_aper_sc_ia624 -->
| `0353:photometry_aper.mag_aper_sc_ia624` | `photometry_aper.mag_aper_sc_ia624` | HDU 1 [SE++APER] | 0 | 999.0 | 82,235 | 784,016 | 0.10488944103181568 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0207:0353:photometry_aper.mag_aper_sc_ia624 -->
| `0353:photometry_aper.mag_aper_sc_ia624` | `photometry_aper.mag_aper_sc_ia624` | HDU 1 [SE++APER] | 1 | 999.0 | 152,833 | 784,016 | 0.19493607273320954 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0208:0353:photometry_aper.mag_aper_sc_ia624 -->
| `0353:photometry_aper.mag_aper_sc_ia624` | `photometry_aper.mag_aper_sc_ia624` | HDU 1 [SE++APER] | 2 | 999.0 | 148,134 | 784,016 | 0.18894257260055916 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0209:0353:photometry_aper.mag_aper_sc_ia624 -->
| `0353:photometry_aper.mag_aper_sc_ia624` | `photometry_aper.mag_aper_sc_ia624` | HDU 1 [SE++APER] | 3 | 999.0 | 142,511 | 784,016 | 0.18177052509132466 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0210:0353:photometry_aper.mag_aper_sc_ia624 -->
| `0353:photometry_aper.mag_aper_sc_ia624` | `photometry_aper.mag_aper_sc_ia624` | HDU 1 [SE++APER] | 4 | 999.0 | 155,050 | 784,016 | 0.1977638211465072 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0211:0354:photometry_aper.mag_aper_sc_ia679 -->
| `0354:photometry_aper.mag_aper_sc_ia679` | `photometry_aper.mag_aper_sc_ia679` | HDU 1 [SE++APER] | 0 | 999.0 | 152,710 | 784,016 | 0.19477918817983306 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0212:0354:photometry_aper.mag_aper_sc_ia679 -->
| `0354:photometry_aper.mag_aper_sc_ia679` | `photometry_aper.mag_aper_sc_ia679` | HDU 1 [SE++APER] | 1 | 999.0 | 284,359 | 784,016 | 0.36269540417542501 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0213:0354:photometry_aper.mag_aper_sc_ia679 -->
| `0354:photometry_aper.mag_aper_sc_ia679` | `photometry_aper.mag_aper_sc_ia679` | HDU 1 [SE++APER] | 2 | 999.0 | 273,907 | 784,016 | 0.34936404359094714 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0214:0354:photometry_aper.mag_aper_sc_ia679 -->
| `0354:photometry_aper.mag_aper_sc_ia679` | `photometry_aper.mag_aper_sc_ia679` | HDU 1 [SE++APER] | 3 | 999.0 | 235,582 | 784,016 | 0.30048111263035449 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0215:0354:photometry_aper.mag_aper_sc_ia679 -->
| `0354:photometry_aper.mag_aper_sc_ia679` | `photometry_aper.mag_aper_sc_ia679` | HDU 1 [SE++APER] | 4 | 999.0 | 251,835 | 784,016 | 0.32121155690700187 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0216:0355:photometry_aper.mag_aper_sc_ia738 -->
| `0355:photometry_aper.mag_aper_sc_ia738` | `photometry_aper.mag_aper_sc_ia738` | HDU 1 [SE++APER] | 0 | 999.0 | 88,602 | 784,016 | 0.1130104487663517 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0217:0355:photometry_aper.mag_aper_sc_ia738 -->
| `0355:photometry_aper.mag_aper_sc_ia738` | `photometry_aper.mag_aper_sc_ia738` | HDU 1 [SE++APER] | 1 | 999.0 | 164,647 | 784,016 | 0.21000464276239261 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0218:0355:photometry_aper.mag_aper_sc_ia738 -->
| `0355:photometry_aper.mag_aper_sc_ia738` | `photometry_aper.mag_aper_sc_ia738` | HDU 1 [SE++APER] | 2 | 999.0 | 159,804 | 784,016 | 0.20382747290871614 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0219:0355:photometry_aper.mag_aper_sc_ia738 -->
| `0355:photometry_aper.mag_aper_sc_ia738` | `photometry_aper.mag_aper_sc_ia738` | HDU 1 [SE++APER] | 3 | 999.0 | 153,198 | 784,016 | 0.19540162445664375 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0220:0355:photometry_aper.mag_aper_sc_ia738 -->
| `0355:photometry_aper.mag_aper_sc_ia738` | `photometry_aper.mag_aper_sc_ia738` | HDU 1 [SE++APER] | 4 | 999.0 | 164,908 | 784,016 | 0.2103375441317524 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0221:0356:photometry_aper.mag_aper_sc_ia767 -->
| `0356:photometry_aper.mag_aper_sc_ia767` | `photometry_aper.mag_aper_sc_ia767` | HDU 1 [SE++APER] | 0 | 999.0 | 144,344 | 784,016 | 0.18410848758188608 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0222:0356:photometry_aper.mag_aper_sc_ia767 -->
| `0356:photometry_aper.mag_aper_sc_ia767` | `photometry_aper.mag_aper_sc_ia767` | HDU 1 [SE++APER] | 1 | 999.0 | 268,409 | 784,016 | 0.34235143160343667 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0223:0356:photometry_aper.mag_aper_sc_ia767 -->
| `0356:photometry_aper.mag_aper_sc_ia767` | `photometry_aper.mag_aper_sc_ia767` | HDU 1 [SE++APER] | 2 | 999.0 | 258,720 | 784,016 | 0.32999326544356239 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0224:0356:photometry_aper.mag_aper_sc_ia767 -->
| `0356:photometry_aper.mag_aper_sc_ia767` | `photometry_aper.mag_aper_sc_ia767` | HDU 1 [SE++APER] | 3 | 999.0 | 226,242 | 784,016 | 0.28856809044713372 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0225:0356:photometry_aper.mag_aper_sc_ia767 -->
| `0356:photometry_aper.mag_aper_sc_ia767` | `photometry_aper.mag_aper_sc_ia767` | HDU 1 [SE++APER] | 4 | 999.0 | 239,515 | 784,016 | 0.30549759188587988 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0226:0357:photometry_aper.mag_aper_sc_ib427 -->
| `0357:photometry_aper.mag_aper_sc_ib427` | `photometry_aper.mag_aper_sc_ib427` | HDU 1 [SE++APER] | 0 | 999.0 | 161,808 | 784,016 | 0.20638354319299607 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0227:0357:photometry_aper.mag_aper_sc_ib427 -->
| `0357:photometry_aper.mag_aper_sc_ib427` | `photometry_aper.mag_aper_sc_ib427` | HDU 1 [SE++APER] | 1 | 999.0 | 301,895 | 784,016 | 0.385062294647048 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0228:0357:photometry_aper.mag_aper_sc_ib427 -->
| `0357:photometry_aper.mag_aper_sc_ib427` | `photometry_aper.mag_aper_sc_ib427` | HDU 1 [SE++APER] | 2 | 999.0 | 293,195 | 784,016 | 0.37396558233505439 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0229:0357:photometry_aper.mag_aper_sc_ib427 -->
| `0357:photometry_aper.mag_aper_sc_ib427` | `photometry_aper.mag_aper_sc_ib427` | HDU 1 [SE++APER] | 3 | 999.0 | 257,703 | 784,016 | 0.32869609803881555 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0230:0357:photometry_aper.mag_aper_sc_ib427 -->
| `0357:photometry_aper.mag_aper_sc_ib427` | `photometry_aper.mag_aper_sc_ib427` | HDU 1 [SE++APER] | 4 | 999.0 | 261,848 | 784,016 | 0.33398297993918491 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0231:0358:photometry_aper.mag_aper_sc_ib505 -->
| `0358:photometry_aper.mag_aper_sc_ib505` | `photometry_aper.mag_aper_sc_ib505` | HDU 1 [SE++APER] | 0 | 999.0 | 132,164 | 784,016 | 0.16857309034509499 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0232:0358:photometry_aper.mag_aper_sc_ib505 -->
| `0358:photometry_aper.mag_aper_sc_ib505` | `photometry_aper.mag_aper_sc_ib505` | HDU 1 [SE++APER] | 1 | 999.0 | 245,691 | 784,016 | 0.31337498214322157 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0233:0358:photometry_aper.mag_aper_sc_ib505 -->
| `0358:photometry_aper.mag_aper_sc_ib505` | `photometry_aper.mag_aper_sc_ib505` | HDU 1 [SE++APER] | 2 | 999.0 | 236,162 | 784,016 | 0.30122089345115405 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0234:0358:photometry_aper.mag_aper_sc_ib505 -->
| `0358:photometry_aper.mag_aper_sc_ib505` | `photometry_aper.mag_aper_sc_ib505` | HDU 1 [SE++APER] | 3 | 999.0 | 209,606 | 784,016 | 0.26734913573192381 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0235:0358:photometry_aper.mag_aper_sc_ib505 -->
| `0358:photometry_aper.mag_aper_sc_ib505` | `photometry_aper.mag_aper_sc_ib505` | HDU 1 [SE++APER] | 4 | 999.0 | 220,601 | 784,016 | 0.28137308422277096 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0236:0359:photometry_aper.mag_aper_sc_ib574 -->
| `0359:photometry_aper.mag_aper_sc_ib574` | `photometry_aper.mag_aper_sc_ib574` | HDU 1 [SE++APER] | 0 | 999.0 | 163,219 | 784,016 | 0.2081832513622171 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0237:0359:photometry_aper.mag_aper_sc_ib574 -->
| `0359:photometry_aper.mag_aper_sc_ib574` | `photometry_aper.mag_aper_sc_ib574` | HDU 1 [SE++APER] | 1 | 999.0 | 305,022 | 784,016 | 0.38905073365849674 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0238:0359:photometry_aper.mag_aper_sc_ib574 -->
| `0359:photometry_aper.mag_aper_sc_ib574` | `photometry_aper.mag_aper_sc_ib574` | HDU 1 [SE++APER] | 2 | 999.0 | 295,687 | 784,016 | 0.37714408889614498 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0239:0359:photometry_aper.mag_aper_sc_ib574 -->
| `0359:photometry_aper.mag_aper_sc_ib574` | `photometry_aper.mag_aper_sc_ib574` | HDU 1 [SE++APER] | 3 | 999.0 | 261,851 | 784,016 | 0.3339868063917063 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0240:0359:photometry_aper.mag_aper_sc_ib574 -->
| `0359:photometry_aper.mag_aper_sc_ib574` | `photometry_aper.mag_aper_sc_ib574` | HDU 1 [SE++APER] | 4 | 999.0 | 270,659 | 784,016 | 0.34522127099446948 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0241:0360:photometry_aper.mag_aper_sc_ib709 -->
| `0360:photometry_aper.mag_aper_sc_ib709` | `photometry_aper.mag_aper_sc_ib709` | HDU 1 [SE++APER] | 0 | 999.0 | 132,572 | 784,016 | 0.1690934878880023 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0242:0360:photometry_aper.mag_aper_sc_ib709 -->
| `0360:photometry_aper.mag_aper_sc_ib709` | `photometry_aper.mag_aper_sc_ib709` | HDU 1 [SE++APER] | 1 | 999.0 | 246,575 | 784,016 | 0.31450251015285402 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0243:0360:photometry_aper.mag_aper_sc_ib709 -->
| `0360:photometry_aper.mag_aper_sc_ib709` | `photometry_aper.mag_aper_sc_ib709` | HDU 1 [SE++APER] | 2 | 999.0 | 237,238 | 784,016 | 0.30259331442215465 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0244:0360:photometry_aper.mag_aper_sc_ib709 -->
| `0360:photometry_aper.mag_aper_sc_ib709` | `photometry_aper.mag_aper_sc_ib709` | HDU 1 [SE++APER] | 3 | 999.0 | 209,328 | 784,016 | 0.26699455113160958 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0245:0360:photometry_aper.mag_aper_sc_ib709 -->
| `0360:photometry_aper.mag_aper_sc_ib709` | `photometry_aper.mag_aper_sc_ib709` | HDU 1 [SE++APER] | 4 | 999.0 | 219,337 | 784,016 | 0.27976087222709739 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0246:0361:photometry_aper.mag_aper_sc_ib827 -->
| `0361:photometry_aper.mag_aper_sc_ib827` | `photometry_aper.mag_aper_sc_ib827` | HDU 1 [SE++APER] | 0 | 999.0 | 148,520 | 784,016 | 0.18943490949164302 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0247:0361:photometry_aper.mag_aper_sc_ib827 -->
| `0361:photometry_aper.mag_aper_sc_ib827` | `photometry_aper.mag_aper_sc_ib827` | HDU 1 [SE++APER] | 1 | 999.0 | 277,308 | 784,016 | 0.35370196526601499 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0248:0361:photometry_aper.mag_aper_sc_ib827 -->
| `0361:photometry_aper.mag_aper_sc_ib827` | `photometry_aper.mag_aper_sc_ib827` | HDU 1 [SE++APER] | 2 | 999.0 | 267,978 | 784,016 | 0.34180169792453213 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0249:0361:photometry_aper.mag_aper_sc_ib827 -->
| `0361:photometry_aper.mag_aper_sc_ib827` | `photometry_aper.mag_aper_sc_ib827` | HDU 1 [SE++APER] | 3 | 999.0 | 235,831 | 784,016 | 0.30079870818962878 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0250:0361:photometry_aper.mag_aper_sc_ib827 -->
| `0361:photometry_aper.mag_aper_sc_ib827` | `photometry_aper.mag_aper_sc_ib827` | HDU 1 [SE++APER] | 4 | 999.0 | 247,002 | 784,016 | 0.31504714189506339 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0251:0362:photometry_aper.mag_aper_sc_nb711 -->
| `0362:photometry_aper.mag_aper_sc_nb711` | `photometry_aper.mag_aper_sc_nb711` | HDU 1 [SE++APER] | 0 | 999.0 | 93,506 | 784,016 | 0.1192654231546295 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0252:0362:photometry_aper.mag_aper_sc_nb711 -->
| `0362:photometry_aper.mag_aper_sc_nb711` | `photometry_aper.mag_aper_sc_nb711` | HDU 1 [SE++APER] | 1 | 999.0 | 175,726 | 784,016 | 0.22413573192383829 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0253:0362:photometry_aper.mag_aper_sc_nb711 -->
| `0362:photometry_aper.mag_aper_sc_nb711` | `photometry_aper.mag_aper_sc_nb711` | HDU 1 [SE++APER] | 2 | 999.0 | 175,723 | 784,016 | 0.22413190547131692 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0254:0362:photometry_aper.mag_aper_sc_nb711 -->
| `0362:photometry_aper.mag_aper_sc_nb711` | `photometry_aper.mag_aper_sc_nb711` | HDU 1 [SE++APER] | 3 | 999.0 | 180,563 | 784,016 | 0.230305248872472 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0255:0362:photometry_aper.mag_aper_sc_nb711 -->
| `0362:photometry_aper.mag_aper_sc_nb711` | `photometry_aper.mag_aper_sc_nb711` | HDU 1 [SE++APER] | 4 | 999.0 | 193,606 | 784,016 | 0.2469413889512459 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0256:0363:photometry_aper.mag_aper_sc_nb816 -->
| `0363:photometry_aper.mag_aper_sc_nb816` | `photometry_aper.mag_aper_sc_nb816` | HDU 1 [SE++APER] | 0 | 999.0 | 150,612 | 784,016 | 0.19210322238321667 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0257:0363:photometry_aper.mag_aper_sc_nb816 -->
| `0363:photometry_aper.mag_aper_sc_nb816` | `photometry_aper.mag_aper_sc_nb816` | HDU 1 [SE++APER] | 1 | 999.0 | 279,562 | 784,016 | 0.35657690659374297 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0258:0363:photometry_aper.mag_aper_sc_nb816 -->
| `0363:photometry_aper.mag_aper_sc_nb816` | `photometry_aper.mag_aper_sc_nb816` | HDU 1 [SE++APER] | 2 | 999.0 | 270,165 | 784,016 | 0.34459118181261605 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0259:0363:photometry_aper.mag_aper_sc_nb816 -->
| `0363:photometry_aper.mag_aper_sc_nb816` | `photometry_aper.mag_aper_sc_nb816` | HDU 1 [SE++APER] | 3 | 999.0 | 236,074 | 784,016 | 0.30110865084386035 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0260:0363:photometry_aper.mag_aper_sc_nb816 -->
| `0363:photometry_aper.mag_aper_sc_nb816` | `photometry_aper.mag_aper_sc_nb816` | HDU 1 [SE++APER] | 4 | 999.0 | 253,246 | 784,016 | 0.32301126507622291 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0261:0364:photometry_aper.mag_aper_irac_ch1 -->
| `0364:photometry_aper.mag_aper_irac_ch1` | `photometry_aper.mag_aper_irac_ch1` | HDU 1 [SE++APER] | 0 | 999.0 | 55,830 | 784,016 | 0.071210281422828106 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0262:0364:photometry_aper.mag_aper_irac_ch1 -->
| `0364:photometry_aper.mag_aper_irac_ch1` | `photometry_aper.mag_aper_irac_ch1` | HDU 1 [SE++APER] | 1 | 999.0 | 105,145 | 784,016 | 0.13411078345339891 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0263:0364:photometry_aper.mag_aper_irac_ch1 -->
| `0364:photometry_aper.mag_aper_irac_ch1` | `photometry_aper.mag_aper_irac_ch1` | HDU 1 [SE++APER] | 2 | 999.0 | 105,277 | 784,016 | 0.13427914736433949 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0264:0364:photometry_aper.mag_aper_irac_ch1 -->
| `0364:photometry_aper.mag_aper_irac_ch1` | `photometry_aper.mag_aper_irac_ch1` | HDU 1 [SE++APER] | 3 | 999.0 | 106,501 | 784,016 | 0.13584033999306136 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0265:0364:photometry_aper.mag_aper_irac_ch1 -->
| `0364:photometry_aper.mag_aper_irac_ch1` | `photometry_aper.mag_aper_irac_ch1` | HDU 1 [SE++APER] | 4 | 999.0 | 109,950 | 784,016 | 0.14023948490847127 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0266:0365:photometry_aper.mag_aper_irac_ch2 -->
| `0365:photometry_aper.mag_aper_irac_ch2` | `photometry_aper.mag_aper_irac_ch2` | HDU 1 [SE++APER] | 0 | 999.0 | 67,228 | 784,016 | 0.085748250035713555 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0267:0365:photometry_aper.mag_aper_irac_ch2 -->
| `0365:photometry_aper.mag_aper_irac_ch2` | `photometry_aper.mag_aper_irac_ch2` | HDU 1 [SE++APER] | 1 | 999.0 | 126,769 | 784,016 | 0.16169185322748517 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0268:0365:photometry_aper.mag_aper_irac_ch2 -->
| `0365:photometry_aper.mag_aper_irac_ch2` | `photometry_aper.mag_aper_irac_ch2` | HDU 1 [SE++APER] | 2 | 999.0 | 126,698 | 784,016 | 0.16160129385114588 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0269:0365:photometry_aper.mag_aper_irac_ch2 -->
| `0365:photometry_aper.mag_aper_irac_ch2` | `photometry_aper.mag_aper_irac_ch2` | HDU 1 [SE++APER] | 3 | 999.0 | 127,353 | 784,016 | 0.1624367359849799 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0270:0365:photometry_aper.mag_aper_irac_ch2 -->
| `0365:photometry_aper.mag_aper_irac_ch2` | `photometry_aper.mag_aper_irac_ch2` | HDU 1 [SE++APER] | 4 | 999.0 | 130,971 | 784,016 | 0.1670514377257607 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0271:0366:photometry_aper.mag_aper_irac_ch3 -->
| `0366:photometry_aper.mag_aper_irac_ch3` | `photometry_aper.mag_aper_irac_ch3` | HDU 1 [SE++APER] | 0 | 999.0 | 189,554 | 784,016 | 0.2417731270790392 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0272:0366:photometry_aper.mag_aper_irac_ch3 -->
| `0366:photometry_aper.mag_aper_irac_ch3` | `photometry_aper.mag_aper_irac_ch3` | HDU 1 [SE++APER] | 1 | 999.0 | 356,670 | 784,016 | 0.45492694026652519 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0273:0366:photometry_aper.mag_aper_irac_ch3 -->
| `0366:photometry_aper.mag_aper_irac_ch3` | `photometry_aper.mag_aper_irac_ch3` | HDU 1 [SE++APER] | 2 | 999.0 | 355,935 | 784,016 | 0.45398945939878776 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0274:0366:photometry_aper.mag_aper_irac_ch3 -->
| `0366:photometry_aper.mag_aper_irac_ch3` | `photometry_aper.mag_aper_irac_ch3` | HDU 1 [SE++APER] | 3 | 999.0 | 354,527 | 784,016 | 0.45219357768208812 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0275:0366:photometry_aper.mag_aper_irac_ch3 -->
| `0366:photometry_aper.mag_aper_irac_ch3` | `photometry_aper.mag_aper_irac_ch3` | HDU 1 [SE++APER] | 4 | 999.0 | 353,824 | 784,016 | 0.45129691230791208 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0276:0367:photometry_aper.mag_aper_irac_ch4 -->
| `0367:photometry_aper.mag_aper_irac_ch4` | `photometry_aper.mag_aper_irac_ch4` | HDU 1 [SE++APER] | 0 | 999.0 | 195,284 | 784,016 | 0.24908165139486949 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0277:0367:photometry_aper.mag_aper_irac_ch4 -->
| `0367:photometry_aper.mag_aper_irac_ch4` | `photometry_aper.mag_aper_irac_ch4` | HDU 1 [SE++APER] | 1 | 999.0 | 368,018 | 784,016 | 0.46940113467072103 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0278:0367:photometry_aper.mag_aper_irac_ch4 -->
| `0367:photometry_aper.mag_aper_irac_ch4` | `photometry_aper.mag_aper_irac_ch4` | HDU 1 [SE++APER] | 2 | 999.0 | 367,726 | 784,016 | 0.46902869329197361 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0279:0367:photometry_aper.mag_aper_irac_ch4 -->
| `0367:photometry_aper.mag_aper_irac_ch4` | `photometry_aper.mag_aper_irac_ch4` | HDU 1 [SE++APER] | 3 | 999.0 | 366,754 | 784,016 | 0.46778892267504746 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0280:0367:photometry_aper.mag_aper_irac_ch4 -->
| `0367:photometry_aper.mag_aper_irac_ch4` | `photometry_aper.mag_aper_irac_ch4` | HDU 1 [SE++APER] | 4 | 999.0 | 366,251 | 784,016 | 0.46714735413562991 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0281:0368:photometry_aper.mag_err_aper_f115w -->
| `0368:photometry_aper.mag_err_aper_f115w` | `photometry_aper.mag_err_aper_f115w` | HDU 1 [SE++APER] | 0 | -999.0 | 23,296 | 784,016 | 0.02971367931266709 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0282:0368:photometry_aper.mag_err_aper_f115w -->
| `0368:photometry_aper.mag_err_aper_f115w` | `photometry_aper.mag_err_aper_f115w` | HDU 1 [SE++APER] | 1 | -999.0 | 15,513 | 784,016 | 0.019786585988041061 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0283:0368:photometry_aper.mag_err_aper_f115w -->
| `0368:photometry_aper.mag_err_aper_f115w` | `photometry_aper.mag_err_aper_f115w` | HDU 1 [SE++APER] | 2 | -999.0 | 29,133 | 784,016 | 0.037158680435093162 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0284:0368:photometry_aper.mag_err_aper_f115w -->
| `0368:photometry_aper.mag_err_aper_f115w` | `photometry_aper.mag_err_aper_f115w` | HDU 1 [SE++APER] | 3 | -999.0 | 61,851 | 784,016 | 0.07888997163323197 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0285:0368:photometry_aper.mag_err_aper_f115w -->
| `0368:photometry_aper.mag_err_aper_f115w` | `photometry_aper.mag_err_aper_f115w` | HDU 1 [SE++APER] | 4 | -999.0 | 80,589 | 784,016 | 0.10278999408175343 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0286:0369:photometry_aper.mag_err_aper_f150w -->
| `0369:photometry_aper.mag_err_aper_f150w` | `photometry_aper.mag_err_aper_f150w` | HDU 1 [SE++APER] | 0 | -999.0 | 12,804 | 784,016 | 0.016331299361237527 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0287:0369:photometry_aper.mag_err_aper_f150w -->
| `0369:photometry_aper.mag_err_aper_f150w` | `photometry_aper.mag_err_aper_f150w` | HDU 1 [SE++APER] | 1 | -999.0 | 8,280 | 784,016 | 0.010561008959000837 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0288:0369:photometry_aper.mag_err_aper_f150w -->
| `0369:photometry_aper.mag_err_aper_f150w` | `photometry_aper.mag_err_aper_f150w` | HDU 1 [SE++APER] | 2 | -999.0 | 16,045 | 784,016 | 0.020465143568498601 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0289:0369:photometry_aper.mag_err_aper_f150w -->
| `0369:photometry_aper.mag_err_aper_f150w` | `photometry_aper.mag_err_aper_f150w` | HDU 1 [SE++APER] | 3 | -999.0 | 45,420 | 784,016 | 0.057932491173649514 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0290:0369:photometry_aper.mag_err_aper_f150w -->
| `0369:photometry_aper.mag_err_aper_f150w` | `photometry_aper.mag_err_aper_f150w` | HDU 1 [SE++APER] | 4 | -999.0 | 65,463 | 784,016 | 0.083497020468970021 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0291:0370:photometry_aper.mag_err_aper_f277w -->
| `0370:photometry_aper.mag_err_aper_f277w` | `photometry_aper.mag_err_aper_f277w` | HDU 1 [SE++APER] | 0 | -999.0 | 13,535 | 784,016 | 0.01726367829227975 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0292:0370:photometry_aper.mag_err_aper_f277w -->
| `0370:photometry_aper.mag_err_aper_f277w` | `photometry_aper.mag_err_aper_f277w` | HDU 1 [SE++APER] | 1 | -999.0 | 9,621 | 784,016 | 0.012271433236056407 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0293:0370:photometry_aper.mag_err_aper_f277w -->
| `0370:photometry_aper.mag_err_aper_f277w` | `photometry_aper.mag_err_aper_f277w` | HDU 1 [SE++APER] | 2 | -999.0 | 10,755 | 784,016 | 0.013717832289136957 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0294:0370:photometry_aper.mag_err_aper_f277w -->
| `0370:photometry_aper.mag_err_aper_f277w` | `photometry_aper.mag_err_aper_f277w` | HDU 1 [SE++APER] | 3 | -999.0 | 20,496 | 784,016 | 0.026142323626048448 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0295:0370:photometry_aper.mag_err_aper_f277w -->
| `0370:photometry_aper.mag_err_aper_f277w` | `photometry_aper.mag_err_aper_f277w` | HDU 1 [SE++APER] | 4 | -999.0 | 35,382 | 784,016 | 0.045129181037121692 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0296:0371:photometry_aper.mag_err_aper_f444w -->
| `0371:photometry_aper.mag_err_aper_f444w` | `photometry_aper.mag_err_aper_f444w` | HDU 1 [SE++APER] | 0 | -999.0 | 23,245 | 784,016 | 0.029648629619803676 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0297:0371:photometry_aper.mag_err_aper_f444w -->
| `0371:photometry_aper.mag_err_aper_f444w` | `photometry_aper.mag_err_aper_f444w` | HDU 1 [SE++APER] | 1 | -999.0 | 14,496 | 784,016 | 0.018489418583294219 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0298:0371:photometry_aper.mag_err_aper_f444w -->
| `0371:photometry_aper.mag_err_aper_f444w` | `photometry_aper.mag_err_aper_f444w` | HDU 1 [SE++APER] | 2 | -999.0 | 18,408 | 784,016 | 0.023479112671169977 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0299:0371:photometry_aper.mag_err_aper_f444w -->
| `0371:photometry_aper.mag_err_aper_f444w` | `photometry_aper.mag_err_aper_f444w` | HDU 1 [SE++APER] | 3 | -999.0 | 36,014 | 784,016 | 0.045935287034958472 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0300:0371:photometry_aper.mag_err_aper_f444w -->
| `0371:photometry_aper.mag_err_aper_f444w` | `photometry_aper.mag_err_aper_f444w` | HDU 1 [SE++APER] | 4 | -999.0 | 53,151 | 784,016 | 0.067793259321238336 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0301:0372:photometry_aper.mag_err_aper_hst_f814w -->
| `0372:photometry_aper.mag_err_aper_hst_f814w` | `photometry_aper.mag_err_aper_hst_f814w` | HDU 1 [SE++APER] | 0 | -999.0 | 44,566 | 784,016 | 0.056843227689230835 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0302:0372:photometry_aper.mag_err_aper_hst_f814w -->
| `0372:photometry_aper.mag_err_aper_hst_f814w` | `photometry_aper.mag_err_aper_hst_f814w` | HDU 1 [SE++APER] | 1 | -999.0 | 28,303 | 784,016 | 0.036100028570845495 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0303:0372:photometry_aper.mag_err_aper_hst_f814w -->
| `0372:photometry_aper.mag_err_aper_hst_f814w` | `photometry_aper.mag_err_aper_hst_f814w` | HDU 1 [SE++APER] | 2 | -999.0 | 31,956 | 784,016 | 0.04075937225770903 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0304:0372:photometry_aper.mag_err_aper_hst_f814w -->
| `0372:photometry_aper.mag_err_aper_hst_f814w` | `photometry_aper.mag_err_aper_hst_f814w` | HDU 1 [SE++APER] | 3 | -999.0 | 48,546 | 784,016 | 0.061919654700924469 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0305:0372:photometry_aper.mag_err_aper_hst_f814w -->
| `0372:photometry_aper.mag_err_aper_hst_f814w` | `photometry_aper.mag_err_aper_hst_f814w` | HDU 1 [SE++APER] | 4 | -999.0 | 56,496 | 784,016 | 0.072059753882573824 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0306:0373:photometry_aper.mag_err_aper_f770w -->
| `0373:photometry_aper.mag_err_aper_f770w` | `photometry_aper.mag_err_aper_f770w` | HDU 1 [SE++APER] | 0 | -999.0 | 50,186 | 784,016 | 0.064011448745943958 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0307:0373:photometry_aper.mag_err_aper_f770w -->
| `0373:photometry_aper.mag_err_aper_f770w` | `photometry_aper.mag_err_aper_f770w` | HDU 1 [SE++APER] | 1 | -999.0 | 30,678 | 784,016 | 0.039129303483602378 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0308:0373:photometry_aper.mag_err_aper_f770w -->
| `0373:photometry_aper.mag_err_aper_f770w` | `photometry_aper.mag_err_aper_f770w` | HDU 1 [SE++APER] | 2 | -999.0 | 26,614 | 784,016 | 0.033945735801310176 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0309:0373:photometry_aper.mag_err_aper_f770w -->
| `0373:photometry_aper.mag_err_aper_f770w` | `photometry_aper.mag_err_aper_f770w` | HDU 1 [SE++APER] | 3 | -999.0 | 27,744 | 784,016 | 0.035387032917695557 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0310:0373:photometry_aper.mag_err_aper_f770w -->
| `0373:photometry_aper.mag_err_aper_f770w` | `photometry_aper.mag_err_aper_f770w` | HDU 1 [SE++APER] | 4 | -999.0 | 28,069 | 784,016 | 0.035801565274178077 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0311:0374:photometry_aper.mag_err_aper_cfht_u -->
| `0374:photometry_aper.mag_err_aper_cfht_u` | `photometry_aper.mag_err_aper_cfht_u` | HDU 1 [SE++APER] | 0 | -999.0 | 85,172 | 784,016 | 0.10863553805024387 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0312:0374:photometry_aper.mag_err_aper_cfht_u -->
| `0374:photometry_aper.mag_err_aper_cfht_u` | `photometry_aper.mag_err_aper_cfht_u` | HDU 1 [SE++APER] | 1 | -999.0 | 120,759 | 784,016 | 0.154026193342993 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0313:0374:photometry_aper.mag_err_aper_cfht_u -->
| `0374:photometry_aper.mag_err_aper_cfht_u` | `photometry_aper.mag_err_aper_cfht_u` | HDU 1 [SE++APER] | 2 | -999.0 | 92,045 | 784,016 | 0.11740194077671884 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0314:0374:photometry_aper.mag_err_aper_cfht_u -->
| `0374:photometry_aper.mag_err_aper_cfht_u` | `photometry_aper.mag_err_aper_cfht_u` | HDU 1 [SE++APER] | 3 | -999.0 | 75,809 | 784,016 | 0.096693179731025897 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0315:0374:photometry_aper.mag_err_aper_cfht_u -->
| `0374:photometry_aper.mag_err_aper_cfht_u` | `photometry_aper.mag_err_aper_cfht_u` | HDU 1 [SE++APER] | 4 | -999.0 | 68,756 | 784,016 | 0.087697189853268298 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0316:0375:photometry_aper.mag_err_aper_hsc_g -->
| `0375:photometry_aper.mag_err_aper_hsc_g` | `photometry_aper.mag_err_aper_hsc_g` | HDU 1 [SE++APER] | 0 | -999.0 | 41,457 | 784,016 | 0.052877747392910346 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0317:0375:photometry_aper.mag_err_aper_hsc_g -->
| `0375:photometry_aper.mag_err_aper_hsc_g` | `photometry_aper.mag_err_aper_hsc_g` | HDU 1 [SE++APER] | 1 | -999.0 | 79,043 | 784,016 | 0.10081809554907042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0318:0375:photometry_aper.mag_err_aper_hsc_g -->
| `0375:photometry_aper.mag_err_aper_hsc_g` | `photometry_aper.mag_err_aper_hsc_g` | HDU 1 [SE++APER] | 2 | -999.0 | 61,201 | 784,016 | 0.078060906920266931 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0319:0375:photometry_aper.mag_err_aper_hsc_g -->
| `0375:photometry_aper.mag_err_aper_hsc_g` | `photometry_aper.mag_err_aper_hsc_g` | HDU 1 [SE++APER] | 3 | -999.0 | 48,972 | 784,016 | 0.062463010958960022 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0320:0375:photometry_aper.mag_err_aper_hsc_g -->
| `0375:photometry_aper.mag_err_aper_hsc_g` | `photometry_aper.mag_err_aper_hsc_g` | HDU 1 [SE++APER] | 4 | -999.0 | 43,931 | 784,016 | 0.056033295238872675 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0321:0376:photometry_aper.mag_err_aper_hsc_r -->
| `0376:photometry_aper.mag_err_aper_hsc_r` | `photometry_aper.mag_err_aper_hsc_r` | HDU 1 [SE++APER] | 0 | -999.0 | 34,106 | 784,016 | 0.043501663231362626 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0322:0376:photometry_aper.mag_err_aper_hsc_r -->
| `0376:photometry_aper.mag_err_aper_hsc_r` | `photometry_aper.mag_err_aper_hsc_r` | HDU 1 [SE++APER] | 1 | -999.0 | 64,233 | 784,016 | 0.081928174935205406 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0323:0376:photometry_aper.mag_err_aper_hsc_r -->
| `0376:photometry_aper.mag_err_aper_hsc_r` | `photometry_aper.mag_err_aper_hsc_r` | HDU 1 [SE++APER] | 2 | -999.0 | 48,226 | 784,016 | 0.061511499765310909 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0324:0376:photometry_aper.mag_err_aper_hsc_r -->
| `0376:photometry_aper.mag_err_aper_hsc_r` | `photometry_aper.mag_err_aper_hsc_r` | HDU 1 [SE++APER] | 3 | -999.0 | 41,965 | 784,016 | 0.053525693353196874 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0325:0376:photometry_aper.mag_err_aper_hsc_r -->
| `0376:photometry_aper.mag_err_aper_hsc_r` | `photometry_aper.mag_err_aper_hsc_r` | HDU 1 [SE++APER] | 4 | -999.0 | 42,460 | 784,016 | 0.054157058019224096 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0326:0377:photometry_aper.mag_err_aper_hsc_i -->
| `0377:photometry_aper.mag_err_aper_hsc_i` | `photometry_aper.mag_err_aper_hsc_i` | HDU 1 [SE++APER] | 0 | -999.0 | 25,398 | 784,016 | 0.032394747045978653 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0327:0377:photometry_aper.mag_err_aper_hsc_i -->
| `0377:photometry_aper.mag_err_aper_hsc_i` | `photometry_aper.mag_err_aper_hsc_i` | HDU 1 [SE++APER] | 1 | -999.0 | 47,664 | 784,016 | 0.060794677659639598 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0328:0377:photometry_aper.mag_err_aper_hsc_i -->
| `0377:photometry_aper.mag_err_aper_hsc_i` | `photometry_aper.mag_err_aper_hsc_i` | HDU 1 [SE++APER] | 2 | -999.0 | 35,430 | 784,016 | 0.045190404277463722 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0329:0377:photometry_aper.mag_err_aper_hsc_i -->
| `0377:photometry_aper.mag_err_aper_hsc_i` | `photometry_aper.mag_err_aper_hsc_i` | HDU 1 [SE++APER] | 3 | -999.0 | 31,433 | 784,016 | 0.040092294034815616 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0330:0377:photometry_aper.mag_err_aper_hsc_i -->
| `0377:photometry_aper.mag_err_aper_hsc_i` | `photometry_aper.mag_err_aper_hsc_i` | HDU 1 [SE++APER] | 4 | -999.0 | 33,318 | 784,016 | 0.042496581702414236 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0331:0378:photometry_aper.mag_err_aper_hsc_z -->
| `0378:photometry_aper.mag_err_aper_hsc_z` | `photometry_aper.mag_err_aper_hsc_z` | HDU 1 [SE++APER] | 0 | -999.0 | 31,361 | 784,016 | 0.040000459174302568 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0332:0378:photometry_aper.mag_err_aper_hsc_z -->
| `0378:photometry_aper.mag_err_aper_hsc_z` | `photometry_aper.mag_err_aper_hsc_z` | HDU 1 [SE++APER] | 1 | -999.0 | 57,661 | 784,016 | 0.073545692945041943 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0333:0378:photometry_aper.mag_err_aper_hsc_z -->
| `0378:photometry_aper.mag_err_aper_hsc_z` | `photometry_aper.mag_err_aper_hsc_z` | HDU 1 [SE++APER] | 2 | -999.0 | 41,219 | 784,016 | 0.052574182159547761 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0334:0378:photometry_aper.mag_err_aper_hsc_z -->
| `0378:photometry_aper.mag_err_aper_hsc_z` | `photometry_aper.mag_err_aper_hsc_z` | HDU 1 [SE++APER] | 3 | -999.0 | 39,567 | 784,016 | 0.050467082304442766 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0335:0378:photometry_aper.mag_err_aper_hsc_z -->
| `0378:photometry_aper.mag_err_aper_hsc_z` | `photometry_aper.mag_err_aper_hsc_z` | HDU 1 [SE++APER] | 4 | -999.0 | 46,447 | 784,016 | 0.059242413420134282 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0336:0379:photometry_aper.mag_err_aper_hsc_y -->
| `0379:photometry_aper.mag_err_aper_hsc_y` | `photometry_aper.mag_err_aper_hsc_y` | HDU 1 [SE++APER] | 0 | -999.0 | 57,825 | 784,016 | 0.073754872349543893 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0337:0379:photometry_aper.mag_err_aper_hsc_y -->
| `0379:photometry_aper.mag_err_aper_hsc_y` | `photometry_aper.mag_err_aper_hsc_y` | HDU 1 [SE++APER] | 1 | -999.0 | 110,053 | 784,016 | 0.14037085977837188 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0338:0379:photometry_aper.mag_err_aper_hsc_y -->
| `0379:photometry_aper.mag_err_aper_hsc_y` | `photometry_aper.mag_err_aper_hsc_y` | HDU 1 [SE++APER] | 2 | -999.0 | 82,581 | 784,016 | 0.10533075855594784 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0339:0379:photometry_aper.mag_err_aper_hsc_y -->
| `0379:photometry_aper.mag_err_aper_hsc_y` | `photometry_aper.mag_err_aper_hsc_y` | HDU 1 [SE++APER] | 3 | -999.0 | 76,349 | 784,016 | 0.097381941184873783 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0340:0379:photometry_aper.mag_err_aper_hsc_y -->
| `0379:photometry_aper.mag_err_aper_hsc_y` | `photometry_aper.mag_err_aper_hsc_y` | HDU 1 [SE++APER] | 4 | -999.0 | 79,571 | 784,016 | 0.1014915511928328 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0341:0380:photometry_aper.mag_err_aper_hsc_nb0816 -->
| `0380:photometry_aper.mag_err_aper_hsc_nb0816` | `photometry_aper.mag_err_aper_hsc_nb0816` | HDU 1 [SE++APER] | 0 | -999.0 | 63,740 | 784,016 | 0.081299361237525763 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0342:0380:photometry_aper.mag_err_aper_hsc_nb0816 -->
| `0380:photometry_aper.mag_err_aper_hsc_nb0816` | `photometry_aper.mag_err_aper_hsc_nb0816` | HDU 1 [SE++APER] | 1 | -999.0 | 120,139 | 784,016 | 0.15323539315524173 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0343:0380:photometry_aper.mag_err_aper_hsc_nb0816 -->
| `0380:photometry_aper.mag_err_aper_hsc_nb0816` | `photometry_aper.mag_err_aper_hsc_nb0816` | HDU 1 [SE++APER] | 2 | -999.0 | 91,208 | 784,016 | 0.11633436052325463 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0344:0380:photometry_aper.mag_err_aper_hsc_nb0816 -->
| `0380:photometry_aper.mag_err_aper_hsc_nb0816` | `photometry_aper.mag_err_aper_hsc_nb0816` | HDU 1 [SE++APER] | 3 | -999.0 | 85,342 | 784,016 | 0.10885237035978858 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0345:0380:photometry_aper.mag_err_aper_hsc_nb0816 -->
| `0380:photometry_aper.mag_err_aper_hsc_nb0816` | `photometry_aper.mag_err_aper_hsc_nb0816` | HDU 1 [SE++APER] | 4 | -999.0 | 93,844 | 784,016 | 0.11969653680537132 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0346:0381:photometry_aper.mag_err_aper_hsc_nb0921 -->
| `0381:photometry_aper.mag_err_aper_hsc_nb0921` | `photometry_aper.mag_err_aper_hsc_nb0921` | HDU 1 [SE++APER] | 0 | -999.0 | 58,778 | 784,016 | 0.074970408767168012 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0347:0381:photometry_aper.mag_err_aper_hsc_nb0921 -->
| `0381:photometry_aper.mag_err_aper_hsc_nb0921` | `photometry_aper.mag_err_aper_hsc_nb0921` | HDU 1 [SE++APER] | 1 | -999.0 | 110,408 | 784,016 | 0.14082365666006816 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0348:0381:photometry_aper.mag_err_aper_hsc_nb0921 -->
| `0381:photometry_aper.mag_err_aper_hsc_nb0921` | `photometry_aper.mag_err_aper_hsc_nb0921` | HDU 1 [SE++APER] | 2 | -999.0 | 81,854 | 784,016 | 0.10440348156160079 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0349:0381:photometry_aper.mag_err_aper_hsc_nb0921 -->
| `0381:photometry_aper.mag_err_aper_hsc_nb0921` | `photometry_aper.mag_err_aper_hsc_nb0921` | HDU 1 [SE++APER] | 3 | -999.0 | 77,730 | 784,016 | 0.099143384828881048 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0350:0381:photometry_aper.mag_err_aper_hsc_nb0921 -->
| `0381:photometry_aper.mag_err_aper_hsc_nb0921` | `photometry_aper.mag_err_aper_hsc_nb0921` | HDU 1 [SE++APER] | 4 | -999.0 | 87,304 | 784,016 | 0.11135487030876921 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0351:0382:photometry_aper.mag_err_aper_hsc_nb1010 -->
| `0382:photometry_aper.mag_err_aper_hsc_nb1010` | `photometry_aper.mag_err_aper_hsc_nb1010` | HDU 1 [SE++APER] | 0 | -999.0 | 109,864 | 784,016 | 0.1401297932695251 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0352:0382:photometry_aper.mag_err_aper_hsc_nb1010 -->
| `0382:photometry_aper.mag_err_aper_hsc_nb1010` | `photometry_aper.mag_err_aper_hsc_nb1010` | HDU 1 [SE++APER] | 1 | -999.0 | 213,315 | 784,016 | 0.27207990653251973 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0353:0382:photometry_aper.mag_err_aper_hsc_nb1010 -->
| `0382:photometry_aper.mag_err_aper_hsc_nb1010` | `photometry_aper.mag_err_aper_hsc_nb1010` | HDU 1 [SE++APER] | 2 | -999.0 | 187,229 | 784,016 | 0.23880762637497194 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0354:0382:photometry_aper.mag_err_aper_hsc_nb1010 -->
| `0382:photometry_aper.mag_err_aper_hsc_nb1010` | `photometry_aper.mag_err_aper_hsc_nb1010` | HDU 1 [SE++APER] | 3 | -999.0 | 176,168 | 784,016 | 0.22469949592865451 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0355:0382:photometry_aper.mag_err_aper_hsc_nb1010 -->
| `0382:photometry_aper.mag_err_aper_hsc_nb1010` | `photometry_aper.mag_err_aper_hsc_nb1010` | HDU 1 [SE++APER] | 4 | -999.0 | 180,289 | 784,016 | 0.22995576620885289 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0356:0383:photometry_aper.mag_err_aper_uvista_y -->
| `0383:photometry_aper.mag_err_aper_uvista_y` | `photometry_aper.mag_err_aper_uvista_y` | HDU 1 [SE++APER] | 0 | -999.0 | 48,177 | 784,016 | 0.061449001040795086 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0357:0383:photometry_aper.mag_err_aper_uvista_y -->
| `0383:photometry_aper.mag_err_aper_uvista_y` | `photometry_aper.mag_err_aper_uvista_y` | HDU 1 [SE++APER] | 1 | -999.0 | 71,971 | 784,016 | 0.091797871472010781 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0358:0383:photometry_aper.mag_err_aper_uvista_y -->
| `0383:photometry_aper.mag_err_aper_uvista_y` | `photometry_aper.mag_err_aper_uvista_y` | HDU 1 [SE++APER] | 2 | -999.0 | 47,940 | 784,016 | 0.061146711291606294 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0359:0383:photometry_aper.mag_err_aper_uvista_y -->
| `0383:photometry_aper.mag_err_aper_uvista_y` | `photometry_aper.mag_err_aper_uvista_y` | HDU 1 [SE++APER] | 3 | -999.0 | 34,431 | 784,016 | 0.043916195587845146 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0360:0383:photometry_aper.mag_err_aper_uvista_y -->
| `0383:photometry_aper.mag_err_aper_uvista_y` | `photometry_aper.mag_err_aper_uvista_y` | HDU 1 [SE++APER] | 4 | -999.0 | 30,970 | 784,016 | 0.039501744862349746 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0361:0384:photometry_aper.mag_err_aper_uvista_j -->
| `0384:photometry_aper.mag_err_aper_uvista_j` | `photometry_aper.mag_err_aper_uvista_j` | HDU 1 [SE++APER] | 0 | -999.0 | 44,292 | 784,016 | 0.056493745025611719 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0362:0384:photometry_aper.mag_err_aper_uvista_j -->
| `0384:photometry_aper.mag_err_aper_uvista_j` | `photometry_aper.mag_err_aper_uvista_j` | HDU 1 [SE++APER] | 1 | -999.0 | 66,425 | 784,016 | 0.084724036244158279 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0363:0384:photometry_aper.mag_err_aper_uvista_j -->
| `0384:photometry_aper.mag_err_aper_uvista_j` | `photometry_aper.mag_err_aper_uvista_j` | HDU 1 [SE++APER] | 2 | -999.0 | 44,626 | 784,016 | 0.056919756739658371 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0364:0384:photometry_aper.mag_err_aper_uvista_j -->
| `0384:photometry_aper.mag_err_aper_uvista_j` | `photometry_aper.mag_err_aper_uvista_j` | HDU 1 [SE++APER] | 3 | -999.0 | 33,969 | 784,016 | 0.043326921899553068 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0365:0384:photometry_aper.mag_err_aper_uvista_j -->
| `0384:photometry_aper.mag_err_aper_uvista_j` | `photometry_aper.mag_err_aper_uvista_j` | HDU 1 [SE++APER] | 4 | -999.0 | 31,682 | 784,016 | 0.040409889594089914 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0366:0385:photometry_aper.mag_err_aper_uvista_h -->
| `0385:photometry_aper.mag_err_aper_uvista_h` | `photometry_aper.mag_err_aper_uvista_h` | HDU 1 [SE++APER] | 0 | -999.0 | 50,795 | 784,016 | 0.064788218607783513 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0367:0385:photometry_aper.mag_err_aper_uvista_h -->
| `0385:photometry_aper.mag_err_aper_uvista_h` | `photometry_aper.mag_err_aper_uvista_h` | HDU 1 [SE++APER] | 1 | -999.0 | 74,625 | 784,016 | 0.095183006469255732 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0368:0385:photometry_aper.mag_err_aper_uvista_h -->
| `0385:photometry_aper.mag_err_aper_uvista_h` | `photometry_aper.mag_err_aper_uvista_h` | HDU 1 [SE++APER] | 2 | -999.0 | 49,851 | 784,016 | 0.063584161547723519 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0369:0385:photometry_aper.mag_err_aper_uvista_h -->
| `0385:photometry_aper.mag_err_aper_uvista_h` | `photometry_aper.mag_err_aper_uvista_h` | HDU 1 [SE++APER] | 3 | -999.0 | 38,711 | 784,016 | 0.049375267851676494 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0370:0385:photometry_aper.mag_err_aper_uvista_h -->
| `0385:photometry_aper.mag_err_aper_uvista_h` | `photometry_aper.mag_err_aper_uvista_h` | HDU 1 [SE++APER] | 4 | -999.0 | 37,367 | 784,016 | 0.047661017122099546 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0371:0386:photometry_aper.mag_err_aper_uvista_ks -->
| `0386:photometry_aper.mag_err_aper_uvista_ks` | `photometry_aper.mag_err_aper_uvista_ks` | HDU 1 [SE++APER] | 0 | -999.0 | 64,947 | 784,016 | 0.08283887063529316 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0372:0386:photometry_aper.mag_err_aper_uvista_ks -->
| `0386:photometry_aper.mag_err_aper_uvista_ks` | `photometry_aper.mag_err_aper_uvista_ks` | HDU 1 [SE++APER] | 1 | -999.0 | 92,558 | 784,016 | 0.11805626415787433 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0373:0386:photometry_aper.mag_err_aper_uvista_ks -->
| `0386:photometry_aper.mag_err_aper_uvista_ks` | `photometry_aper.mag_err_aper_uvista_ks` | HDU 1 [SE++APER] | 2 | -999.0 | 61,484 | 784,016 | 0.078421868941450174 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0374:0386:photometry_aper.mag_err_aper_uvista_ks -->
| `0386:photometry_aper.mag_err_aper_uvista_ks` | `photometry_aper.mag_err_aper_uvista_ks` | HDU 1 [SE++APER] | 3 | -999.0 | 48,098 | 784,016 | 0.061348237791065491 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0375:0386:photometry_aper.mag_err_aper_uvista_ks -->
| `0386:photometry_aper.mag_err_aper_uvista_ks` | `photometry_aper.mag_err_aper_uvista_ks` | HDU 1 [SE++APER] | 4 | -999.0 | 46,891 | 784,016 | 0.059808728393298094 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0376:0387:photometry_aper.mag_err_aper_uvista_nb118 -->
| `0387:photometry_aper.mag_err_aper_uvista_nb118` | `photometry_aper.mag_err_aper_uvista_nb118` | HDU 1 [SE++APER] | 0 | -999.0 | 115,771 | 784,016 | 0.14766407828411665 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0377:0387:photometry_aper.mag_err_aper_uvista_nb118 -->
| `0387:photometry_aper.mag_err_aper_uvista_nb118` | `photometry_aper.mag_err_aper_uvista_nb118` | HDU 1 [SE++APER] | 1 | -999.0 | 155,788 | 784,016 | 0.198705128466766 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0378:0387:photometry_aper.mag_err_aper_uvista_nb118 -->
| `0387:photometry_aper.mag_err_aper_uvista_nb118` | `photometry_aper.mag_err_aper_uvista_nb118` | HDU 1 [SE++APER] | 2 | -999.0 | 102,325 | 784,016 | 0.13051391808330443 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0379:0387:photometry_aper.mag_err_aper_uvista_nb118 -->
| `0387:photometry_aper.mag_err_aper_uvista_nb118` | `photometry_aper.mag_err_aper_uvista_nb118` | HDU 1 [SE++APER] | 3 | -999.0 | 80,087 | 784,016 | 0.10214970102650966 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0380:0387:photometry_aper.mag_err_aper_uvista_nb118 -->
| `0387:photometry_aper.mag_err_aper_uvista_nb118` | `photometry_aper.mag_err_aper_uvista_nb118` | HDU 1 [SE++APER] | 4 | -999.0 | 74,176 | 784,016 | 0.094610314075222954 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0381:0388:photometry_aper.mag_err_aper_sc_ia484 -->
| `0388:photometry_aper.mag_err_aper_sc_ia484` | `photometry_aper.mag_err_aper_sc_ia484` | HDU 1 [SE++APER] | 0 | -999.0 | 92,769 | 784,016 | 0.11832539131854453 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0382:0388:photometry_aper.mag_err_aper_sc_ia484 -->
| `0388:photometry_aper.mag_err_aper_sc_ia484` | `photometry_aper.mag_err_aper_sc_ia484` | HDU 1 [SE++APER] | 1 | -999.0 | 126,692 | 784,016 | 0.16159364094610315 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0383:0388:photometry_aper.mag_err_aper_sc_ia484 -->
| `0388:photometry_aper.mag_err_aper_sc_ia484` | `photometry_aper.mag_err_aper_sc_ia484` | HDU 1 [SE++APER] | 2 | -999.0 | 80,961 | 784,016 | 0.1032644741944042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0384:0388:photometry_aper.mag_err_aper_sc_ia484 -->
| `0388:photometry_aper.mag_err_aper_sc_ia484` | `photometry_aper.mag_err_aper_sc_ia484` | HDU 1 [SE++APER] | 3 | -999.0 | 62,622 | 784,016 | 0.079873369931225888 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0385:0388:photometry_aper.mag_err_aper_sc_ia484 -->
| `0388:photometry_aper.mag_err_aper_sc_ia484` | `photometry_aper.mag_err_aper_sc_ia484` | HDU 1 [SE++APER] | 4 | -999.0 | 58,177 | 784,016 | 0.074203842778718804 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0386:0389:photometry_aper.mag_err_aper_sc_ia527 -->
| `0389:photometry_aper.mag_err_aper_sc_ia527` | `photometry_aper.mag_err_aper_sc_ia527` | HDU 1 [SE++APER] | 0 | -999.0 | 88,467 | 784,016 | 0.11283825840288973 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0387:0389:photometry_aper.mag_err_aper_sc_ia527 -->
| `0389:photometry_aper.mag_err_aper_sc_ia527` | `photometry_aper.mag_err_aper_sc_ia527` | HDU 1 [SE++APER] | 1 | -999.0 | 120,413 | 784,016 | 0.15358487581886085 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0388:0389:photometry_aper.mag_err_aper_sc_ia527 -->
| `0389:photometry_aper.mag_err_aper_sc_ia527` | `photometry_aper.mag_err_aper_sc_ia527` | HDU 1 [SE++APER] | 2 | -999.0 | 78,487 | 784,016 | 0.10010892634844187 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0389:0389:photometry_aper.mag_err_aper_sc_ia527 -->
| `0389:photometry_aper.mag_err_aper_sc_ia527` | `photometry_aper.mag_err_aper_sc_ia527` | HDU 1 [SE++APER] | 3 | -999.0 | 66,676 | 784,016 | 0.085044182771780163 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0390:0389:photometry_aper.mag_err_aper_sc_ia527 -->
| `0389:photometry_aper.mag_err_aper_sc_ia527` | `photometry_aper.mag_err_aper_sc_ia527` | HDU 1 [SE++APER] | 4 | -999.0 | 63,751 | 784,016 | 0.081313391563437476 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0391:0390:photometry_aper.mag_err_aper_sc_ia624 -->
| `0390:photometry_aper.mag_err_aper_sc_ia624` | `photometry_aper.mag_err_aper_sc_ia624` | HDU 1 [SE++APER] | 0 | -999.0 | 74,689 | 784,016 | 0.095264637456378448 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0392:0390:photometry_aper.mag_err_aper_sc_ia624 -->
| `0390:photometry_aper.mag_err_aper_sc_ia624` | `photometry_aper.mag_err_aper_sc_ia624` | HDU 1 [SE++APER] | 1 | -999.0 | 103,500 | 784,016 | 0.13201261198751046 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0393:0390:photometry_aper.mag_err_aper_sc_ia624 -->
| `0390:photometry_aper.mag_err_aper_sc_ia624` | `photometry_aper.mag_err_aper_sc_ia624` | HDU 1 [SE++APER] | 2 | -999.0 | 65,310 | 784,016 | 0.083301871390379784 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0394:0390:photometry_aper.mag_err_aper_sc_ia624 -->
| `0390:photometry_aper.mag_err_aper_sc_ia624` | `photometry_aper.mag_err_aper_sc_ia624` | HDU 1 [SE++APER] | 3 | -999.0 | 47,579 | 784,016 | 0.06068626150486725 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0395:0390:photometry_aper.mag_err_aper_sc_ia624 -->
| `0390:photometry_aper.mag_err_aper_sc_ia624` | `photometry_aper.mag_err_aper_sc_ia624` | HDU 1 [SE++APER] | 4 | -999.0 | 43,753 | 784,016 | 0.055806259055937633 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0396:0391:photometry_aper.mag_err_aper_sc_ia679 -->
| `0391:photometry_aper.mag_err_aper_sc_ia679` | `photometry_aper.mag_err_aper_sc_ia679` | HDU 1 [SE++APER] | 0 | -999.0 | 133,253 | 784,016 | 0.16996209261035489 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0397:0391:photometry_aper.mag_err_aper_sc_ia679 -->
| `0391:photometry_aper.mag_err_aper_sc_ia679` | `photometry_aper.mag_err_aper_sc_ia679` | HDU 1 [SE++APER] | 1 | -999.0 | 177,000 | 784,016 | 0.22576069876124977 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0398:0391:photometry_aper.mag_err_aper_sc_ia679 -->
| `0391:photometry_aper.mag_err_aper_sc_ia679` | `photometry_aper.mag_err_aper_sc_ia679` | HDU 1 [SE++APER] | 2 | -999.0 | 119,137 | 784,016 | 0.15195735801310178 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0399:0391:photometry_aper.mag_err_aper_sc_ia679 -->
| `0391:photometry_aper.mag_err_aper_sc_ia679` | `photometry_aper.mag_err_aper_sc_ia679` | HDU 1 [SE++APER] | 3 | -999.0 | 137,695 | 784,016 | 0.17562779331034062 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0400:0391:photometry_aper.mag_err_aper_sc_ia679 -->
| `0391:photometry_aper.mag_err_aper_sc_ia679` | `photometry_aper.mag_err_aper_sc_ia679` | HDU 1 [SE++APER] | 4 | -999.0 | 143,704 | 784,016 | 0.18329217771065898 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0401:0392:photometry_aper.mag_err_aper_sc_ia738 -->
| `0392:photometry_aper.mag_err_aper_sc_ia738` | `photometry_aper.mag_err_aper_sc_ia738` | HDU 1 [SE++APER] | 0 | -999.0 | 80,437 | 784,016 | 0.10259612048733699 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0402:0392:photometry_aper.mag_err_aper_sc_ia738 -->
| `0392:photometry_aper.mag_err_aper_sc_ia738` | `photometry_aper.mag_err_aper_sc_ia738` | HDU 1 [SE++APER] | 1 | -999.0 | 111,260 | 784,016 | 0.14191036917613925 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0403:0392:photometry_aper.mag_err_aper_sc_ia738 -->
| `0392:photometry_aper.mag_err_aper_sc_ia738` | `photometry_aper.mag_err_aper_sc_ia738` | HDU 1 [SE++APER] | 2 | -999.0 | 70,373 | 784,016 | 0.089759647762290562 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0404:0392:photometry_aper.mag_err_aper_sc_ia738 -->
| `0392:photometry_aper.mag_err_aper_sc_ia738` | `photometry_aper.mag_err_aper_sc_ia738` | HDU 1 [SE++APER] | 3 | -999.0 | 51,269 | 784,016 | 0.065392798106161096 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0405:0392:photometry_aper.mag_err_aper_sc_ia738 -->
| `0392:photometry_aper.mag_err_aper_sc_ia738` | `photometry_aper.mag_err_aper_sc_ia738` | HDU 1 [SE++APER] | 4 | -999.0 | 47,609 | 784,016 | 0.060724526030081022 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0406:0393:photometry_aper.mag_err_aper_sc_ia767 -->
| `0393:photometry_aper.mag_err_aper_sc_ia767` | `photometry_aper.mag_err_aper_sc_ia767` | HDU 1 [SE++APER] | 0 | -999.0 | 127,469 | 784,016 | 0.16258469214913981 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0407:0393:photometry_aper.mag_err_aper_sc_ia767 -->
| `0393:photometry_aper.mag_err_aper_sc_ia767` | `photometry_aper.mag_err_aper_sc_ia767` | HDU 1 [SE++APER] | 1 | -999.0 | 172,773 | 784,016 | 0.22036922715862942 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0408:0393:photometry_aper.mag_err_aper_sc_ia767 -->
| `0393:photometry_aper.mag_err_aper_sc_ia767` | `photometry_aper.mag_err_aper_sc_ia767` | HDU 1 [SE++APER] | 2 | -999.0 | 116,129 | 784,016 | 0.14812070161833432 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0409:0393:photometry_aper.mag_err_aper_sc_ia767 -->
| `0393:photometry_aper.mag_err_aper_sc_ia767` | `photometry_aper.mag_err_aper_sc_ia767` | HDU 1 [SE++APER] | 3 | -999.0 | 118,517 | 784,016 | 0.15116655782535049 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0410:0393:photometry_aper.mag_err_aper_sc_ia767 -->
| `0393:photometry_aper.mag_err_aper_sc_ia767` | `photometry_aper.mag_err_aper_sc_ia767` | HDU 1 [SE++APER] | 4 | -999.0 | 122,894 | 784,016 | 0.15674935205403973 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0411:0394:photometry_aper.mag_err_aper_sc_ib427 -->
| `0394:photometry_aper.mag_err_aper_sc_ib427` | `photometry_aper.mag_err_aper_sc_ib427` | HDU 1 [SE++APER] | 0 | -999.0 | 137,867 | 784,016 | 0.1758471765882329 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0412:0394:photometry_aper.mag_err_aper_sc_ib427 -->
| `0394:photometry_aper.mag_err_aper_sc_ib427` | `photometry_aper.mag_err_aper_sc_ib427` | HDU 1 [SE++APER] | 1 | -999.0 | 183,712 | 784,016 | 0.23432174853574417 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0413:0394:photometry_aper.mag_err_aper_sc_ib427 -->
| `0394:photometry_aper.mag_err_aper_sc_ib427` | `photometry_aper.mag_err_aper_sc_ib427` | HDU 1 [SE++APER] | 2 | -999.0 | 126,827 | 784,016 | 0.16176583130956512 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0414:0394:photometry_aper.mag_err_aper_sc_ib427 -->
| `0394:photometry_aper.mag_err_aper_sc_ib427` | `photometry_aper.mag_err_aper_sc_ib427` | HDU 1 [SE++APER] | 3 | -999.0 | 141,270 | 784,016 | 0.18018764923164834 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0415:0394:photometry_aper.mag_err_aper_sc_ib427 -->
| `0394:photometry_aper.mag_err_aper_sc_ib427` | `photometry_aper.mag_err_aper_sc_ib427` | HDU 1 [SE++APER] | 4 | -999.0 | 148,410 | 784,016 | 0.18929460623252586 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0416:0395:photometry_aper.mag_err_aper_sc_ib505 -->
| `0395:photometry_aper.mag_err_aper_sc_ib505` | `photometry_aper.mag_err_aper_sc_ib505` | HDU 1 [SE++APER] | 0 | -999.0 | 116,353 | 784,016 | 0.1484064100732638 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0417:0395:photometry_aper.mag_err_aper_sc_ib505 -->
| `0395:photometry_aper.mag_err_aper_sc_ib505` | `photometry_aper.mag_err_aper_sc_ib505` | HDU 1 [SE++APER] | 1 | -999.0 | 155,912 | 784,016 | 0.19886328850431623 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0418:0395:photometry_aper.mag_err_aper_sc_ib505 -->
| `0395:photometry_aper.mag_err_aper_sc_ib505` | `photometry_aper.mag_err_aper_sc_ib505` | HDU 1 [SE++APER] | 2 | -999.0 | 102,652 | 784,016 | 0.13093100140813452 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0419:0395:photometry_aper.mag_err_aper_sc_ib505 -->
| `0395:photometry_aper.mag_err_aper_sc_ib505` | `photometry_aper.mag_err_aper_sc_ib505` | HDU 1 [SE++APER] | 3 | -999.0 | 94,649 | 784,016 | 0.12072330156527418 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0420:0395:photometry_aper.mag_err_aper_sc_ib505 -->
| `0395:photometry_aper.mag_err_aper_sc_ib505` | `photometry_aper.mag_err_aper_sc_ib505` | HDU 1 [SE++APER] | 4 | -999.0 | 91,738 | 784,016 | 0.11701036713536458 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0421:0396:photometry_aper.mag_err_aper_sc_ib574 -->
| `0396:photometry_aper.mag_err_aper_sc_ib574` | `photometry_aper.mag_err_aper_sc_ib574` | HDU 1 [SE++APER] | 0 | -999.0 | 141,851 | 784,016 | 0.18092870553662171 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0422:0396:photometry_aper.mag_err_aper_sc_ib574 -->
| `0396:photometry_aper.mag_err_aper_sc_ib574` | `photometry_aper.mag_err_aper_sc_ib574` | HDU 1 [SE++APER] | 1 | -999.0 | 189,724 | 784,016 | 0.24198995938858392 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0423:0396:photometry_aper.mag_err_aper_sc_ib574 -->
| `0396:photometry_aper.mag_err_aper_sc_ib574` | `photometry_aper.mag_err_aper_sc_ib574` | HDU 1 [SE++APER] | 2 | -999.0 | 127,777 | 784,016 | 0.16297754127466788 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0424:0396:photometry_aper.mag_err_aper_sc_ib574 -->
| `0396:photometry_aper.mag_err_aper_sc_ib574` | `photometry_aper.mag_err_aper_sc_ib574` | HDU 1 [SE++APER] | 3 | -999.0 | 143,032 | 784,016 | 0.18243505234587049 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0425:0396:photometry_aper.mag_err_aper_sc_ib574 -->
| `0396:photometry_aper.mag_err_aper_sc_ib574` | `photometry_aper.mag_err_aper_sc_ib574` | HDU 1 [SE++APER] | 4 | -999.0 | 151,433 | 784,016 | 0.19315039488990021 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0426:0397:photometry_aper.mag_err_aper_sc_ib709 -->
| `0397:photometry_aper.mag_err_aper_sc_ib709` | `photometry_aper.mag_err_aper_sc_ib709` | HDU 1 [SE++APER] | 0 | -999.0 | 117,779 | 784,016 | 0.15022525050509172 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0427:0397:photometry_aper.mag_err_aper_sc_ib709 -->
| `0397:photometry_aper.mag_err_aper_sc_ib709` | `photometry_aper.mag_err_aper_sc_ib709` | HDU 1 [SE++APER] | 1 | -999.0 | 159,644 | 784,016 | 0.20362339544090938 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0428:0397:photometry_aper.mag_err_aper_sc_ib709 -->
| `0397:photometry_aper.mag_err_aper_sc_ib709` | `photometry_aper.mag_err_aper_sc_ib709` | HDU 1 [SE++APER] | 2 | -999.0 | 105,290 | 784,016 | 0.13429572865859882 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0429:0397:photometry_aper.mag_err_aper_sc_ib709 -->
| `0397:photometry_aper.mag_err_aper_sc_ib709` | `photometry_aper.mag_err_aper_sc_ib709` | HDU 1 [SE++APER] | 3 | -999.0 | 99,485 | 784,016 | 0.1268915430297341 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0430:0397:photometry_aper.mag_err_aper_sc_ib709 -->
| `0397:photometry_aper.mag_err_aper_sc_ib709` | `photometry_aper.mag_err_aper_sc_ib709` | HDU 1 [SE++APER] | 4 | -999.0 | 105,687 | 784,016 | 0.13480209587559439 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0431:0398:photometry_aper.mag_err_aper_sc_ib827 -->
| `0398:photometry_aper.mag_err_aper_sc_ib827` | `photometry_aper.mag_err_aper_sc_ib827` | HDU 1 [SE++APER] | 0 | -999.0 | 128,017 | 784,016 | 0.16328365747637805 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0432:0398:photometry_aper.mag_err_aper_sc_ib827 -->
| `0398:photometry_aper.mag_err_aper_sc_ib827` | `photometry_aper.mag_err_aper_sc_ib827` | HDU 1 [SE++APER] | 1 | -999.0 | 171,050 | 784,016 | 0.21817156792718517 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0433:0398:photometry_aper.mag_err_aper_sc_ib827 -->
| `0398:photometry_aper.mag_err_aper_sc_ib827` | `photometry_aper.mag_err_aper_sc_ib827` | HDU 1 [SE++APER] | 2 | -999.0 | 114,586 | 784,016 | 0.14615262953817268 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0434:0398:photometry_aper.mag_err_aper_sc_ib827 -->
| `0398:photometry_aper.mag_err_aper_sc_ib827` | `photometry_aper.mag_err_aper_sc_ib827` | HDU 1 [SE++APER] | 3 | -999.0 | 120,760 | 784,016 | 0.15402746882716678 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0435:0398:photometry_aper.mag_err_aper_sc_ib827 -->
| `0398:photometry_aper.mag_err_aper_sc_ib827` | `photometry_aper.mag_err_aper_sc_ib827` | HDU 1 [SE++APER] | 4 | -999.0 | 130,109 | 784,016 | 0.16595197036795167 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0436:0399:photometry_aper.mag_err_aper_sc_nb711 -->
| `0399:photometry_aper.mag_err_aper_sc_nb711` | `photometry_aper.mag_err_aper_sc_nb711` | HDU 1 [SE++APER] | 0 | -999.0 | 84,748 | 784,016 | 0.10809473276055591 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0437:0399:photometry_aper.mag_err_aper_sc_nb711 -->
| `0399:photometry_aper.mag_err_aper_sc_nb711` | `photometry_aper.mag_err_aper_sc_nb711` | HDU 1 [SE++APER] | 1 | -999.0 | 116,361 | 784,016 | 0.14841661394665415 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0438:0399:photometry_aper.mag_err_aper_sc_nb711 -->
| `0399:photometry_aper.mag_err_aper_sc_nb711` | `photometry_aper.mag_err_aper_sc_nb711` | HDU 1 [SE++APER] | 2 | -999.0 | 71,024 | 784,016 | 0.090589987959429394 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0439:0399:photometry_aper.mag_err_aper_sc_nb711 -->
| `0399:photometry_aper.mag_err_aper_sc_nb711` | `photometry_aper.mag_err_aper_sc_nb711` | HDU 1 [SE++APER] | 3 | -999.0 | 46,473 | 784,016 | 0.059275576008652887 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0440:0399:photometry_aper.mag_err_aper_sc_nb711 -->
| `0399:photometry_aper.mag_err_aper_sc_nb711` | `photometry_aper.mag_err_aper_sc_nb711` | HDU 1 [SE++APER] | 4 | -999.0 | 40,038 | 784,016 | 0.051067835350298976 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0441:0400:photometry_aper.mag_err_aper_sc_nb816 -->
| `0400:photometry_aper.mag_err_aper_sc_nb816` | `photometry_aper.mag_err_aper_sc_nb816` | HDU 1 [SE++APER] | 0 | -999.0 | 132,628 | 784,016 | 0.16916491500173467 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0442:0400:photometry_aper.mag_err_aper_sc_nb816 -->
| `0400:photometry_aper.mag_err_aper_sc_nb816` | `photometry_aper.mag_err_aper_sc_nb816` | HDU 1 [SE++APER] | 1 | -999.0 | 179,479 | 784,016 | 0.22892262402808106 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0443:0400:photometry_aper.mag_err_aper_sc_nb816 -->
| `0400:photometry_aper.mag_err_aper_sc_nb816` | `photometry_aper.mag_err_aper_sc_nb816` | HDU 1 [SE++APER] | 2 | -999.0 | 122,202 | 784,016 | 0.1558667170057754 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0444:0400:photometry_aper.mag_err_aper_sc_nb816 -->
| `0400:photometry_aper.mag_err_aper_sc_nb816` | `photometry_aper.mag_err_aper_sc_nb816` | HDU 1 [SE++APER] | 3 | -999.0 | 138,638 | 784,016 | 0.1768305748862268 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0445:0400:photometry_aper.mag_err_aper_sc_nb816 -->
| `0400:photometry_aper.mag_err_aper_sc_nb816` | `photometry_aper.mag_err_aper_sc_nb816` | HDU 1 [SE++APER] | 4 | -999.0 | 146,816 | 784,016 | 0.18726148445950083 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0446:0401:photometry_aper.mag_err_aper_irac_ch1 -->
| `0401:photometry_aper.mag_err_aper_irac_ch1` | `photometry_aper.mag_err_aper_irac_ch1` | HDU 1 [SE++APER] | 0 | -999.0 | 54,773 | 784,016 | 0.069862094651129567 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0447:0401:photometry_aper.mag_err_aper_irac_ch1 -->
| `0401:photometry_aper.mag_err_aper_irac_ch1` | `photometry_aper.mag_err_aper_irac_ch1` | HDU 1 [SE++APER] | 1 | -999.0 | 91,329 | 784,016 | 0.11648869410828351 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0448:0401:photometry_aper.mag_err_aper_irac_ch1 -->
| `0401:photometry_aper.mag_err_aper_irac_ch1` | `photometry_aper.mag_err_aper_irac_ch1` | HDU 1 [SE++APER] | 2 | -999.0 | 61,147 | 784,016 | 0.077992030774882148 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0449:0401:photometry_aper.mag_err_aper_irac_ch1 -->
| `0401:photometry_aper.mag_err_aper_irac_ch1` | `photometry_aper.mag_err_aper_irac_ch1` | HDU 1 [SE++APER] | 3 | -999.0 | 35,791 | 784,016 | 0.045650854064202773 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0450:0401:photometry_aper.mag_err_aper_irac_ch1 -->
| `0401:photometry_aper.mag_err_aper_irac_ch1` | `photometry_aper.mag_err_aper_irac_ch1` | HDU 1 [SE++APER] | 4 | -999.0 | 26,366 | 784,016 | 0.033629415726209672 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0451:0402:photometry_aper.mag_err_aper_irac_ch2 -->
| `0402:photometry_aper.mag_err_aper_irac_ch2` | `photometry_aper.mag_err_aper_irac_ch2` | HDU 1 [SE++APER] | 0 | -999.0 | 65,707 | 784,016 | 0.083808238607375365 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0452:0402:photometry_aper.mag_err_aper_irac_ch2 -->
| `0402:photometry_aper.mag_err_aper_irac_ch2` | `photometry_aper.mag_err_aper_irac_ch2` | HDU 1 [SE++APER] | 1 | -999.0 | 106,031 | 784,016 | 0.13524086243137895 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0453:0402:photometry_aper.mag_err_aper_irac_ch2 -->
| `0402:photometry_aper.mag_err_aper_irac_ch2` | `photometry_aper.mag_err_aper_irac_ch2` | HDU 1 [SE++APER] | 2 | -999.0 | 68,000 | 784,016 | 0.086732923817881266 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0454:0402:photometry_aper.mag_err_aper_irac_ch2 -->
| `0402:photometry_aper.mag_err_aper_irac_ch2` | `photometry_aper.mag_err_aper_irac_ch2` | HDU 1 [SE++APER] | 3 | -999.0 | 39,427 | 784,016 | 0.050288514520111835 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0455:0402:photometry_aper.mag_err_aper_irac_ch2 -->
| `0402:photometry_aper.mag_err_aper_irac_ch2` | `photometry_aper.mag_err_aper_irac_ch2` | HDU 1 [SE++APER] | 4 | -999.0 | 29,377 | 784,016 | 0.0374698985734985 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0456:0403:photometry_aper.mag_err_aper_irac_ch3 -->
| `0403:photometry_aper.mag_err_aper_irac_ch3` | `photometry_aper.mag_err_aper_irac_ch3` | HDU 1 [SE++APER] | 0 | -999.0 | 162,608 | 784,016 | 0.20740393053202996 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0457:0403:photometry_aper.mag_err_aper_irac_ch3 -->
| `0403:photometry_aper.mag_err_aper_irac_ch3` | `photometry_aper.mag_err_aper_irac_ch3` | HDU 1 [SE++APER] | 1 | -999.0 | 201,586 | 784,016 | 0.25711975265810899 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0458:0403:photometry_aper.mag_err_aper_irac_ch3 -->
| `0403:photometry_aper.mag_err_aper_irac_ch3` | `photometry_aper.mag_err_aper_irac_ch3` | HDU 1 [SE++APER] | 2 | -999.0 | 112,146 | 784,016 | 0.14304044815411932 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0459:0403:photometry_aper.mag_err_aper_irac_ch3 -->
| `0403:photometry_aper.mag_err_aper_irac_ch3` | `photometry_aper.mag_err_aper_irac_ch3` | HDU 1 [SE++APER] | 3 | -999.0 | 66,632 | 784,016 | 0.0849880614681333 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0460:0403:photometry_aper.mag_err_aper_irac_ch3 -->
| `0403:photometry_aper.mag_err_aper_irac_ch3` | `photometry_aper.mag_err_aper_irac_ch3` | HDU 1 [SE++APER] | 4 | -999.0 | 54,635 | 784,016 | 0.069686077835146215 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0461:0404:photometry_aper.mag_err_aper_irac_ch4 -->
| `0404:photometry_aper.mag_err_aper_irac_ch4` | `photometry_aper.mag_err_aper_irac_ch4` | HDU 1 [SE++APER] | 0 | -999.0 | 165,961 | 784,016 | 0.21168062896675577 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0462:0404:photometry_aper.mag_err_aper_irac_ch4 -->
| `0404:photometry_aper.mag_err_aper_irac_ch4` | `photometry_aper.mag_err_aper_irac_ch4` | HDU 1 [SE++APER] | 1 | -999.0 | 203,607 | 784,016 | 0.25969750617334342 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0463:0404:photometry_aper.mag_err_aper_irac_ch4 -->
| `0404:photometry_aper.mag_err_aper_irac_ch4` | `photometry_aper.mag_err_aper_irac_ch4` | HDU 1 [SE++APER] | 2 | -999.0 | 112,953 | 784,016 | 0.14406976388236975 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0464:0404:photometry_aper.mag_err_aper_irac_ch4 -->
| `0404:photometry_aper.mag_err_aper_irac_ch4` | `photometry_aper.mag_err_aper_irac_ch4` | HDU 1 [SE++APER] | 3 | -999.0 | 67,533 | 784,016 | 0.086137272708720236 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0465:0404:photometry_aper.mag_err_aper_irac_ch4 -->
| `0404:photometry_aper.mag_err_aper_irac_ch4` | `photometry_aper.mag_err_aper_irac_ch4` | HDU 1 [SE++APER] | 4 | -999.0 | 55,968 | 784,016 | 0.071386298238811458 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0466:0698:bulge_disk.mag_model_bd_total_f115w -->
| `0698:bulge_disk.mag_model_bd_total_f115w` | `bulge_disk.mag_model_bd_total_f115w` | HDU 1 [B+D] | scalar | 999.0 | 27,767 | 784,016 | 0.035416369053692782 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0467:0699:bulge_disk.mag_model_bd_total_f150w -->
| `0699:bulge_disk.mag_model_bd_total_f150w` | `bulge_disk.mag_model_bd_total_f150w` | HDU 1 [B+D] | scalar | 999.0 | 17,406 | 784,016 | 0.022201077529030021 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0468:0700:bulge_disk.mag_model_bd_total_f277w -->
| `0700:bulge_disk.mag_model_bd_total_f277w` | `bulge_disk.mag_model_bd_total_f277w` | HDU 1 [B+D] | scalar | 999.0 | 25,329 | 784,016 | 0.032306738637986977 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0469:0701:bulge_disk.mag_model_bd_total_f444w -->
| `0701:bulge_disk.mag_model_bd_total_f444w` | `bulge_disk.mag_model_bd_total_f444w` | HDU 1 [B+D] | scalar | 999.0 | 34,301 | 784,016 | 0.043750382645252141 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0470:0702:bulge_disk.mag_err_model_bd_total_f115w -->
| `0702:bulge_disk.mag_err_model_bd_total_f115w` | `bulge_disk.mag_err_model_bd_total_f115w` | HDU 1 [B+D] | scalar | -999.0 | 13,563 | 784,016 | 0.017299391849145935 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0471:0703:bulge_disk.mag_err_model_bd_total_f150w -->
| `0703:bulge_disk.mag_err_model_bd_total_f150w` | `bulge_disk.mag_err_model_bd_total_f150w` | HDU 1 [B+D] | scalar | -999.0 | 8,567 | 784,016 | 0.010927072916879247 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0472:0704:bulge_disk.mag_err_model_bd_total_f277w -->
| `0704:bulge_disk.mag_err_model_bd_total_f277w` | `bulge_disk.mag_err_model_bd_total_f277w` | HDU 1 [B+D] | scalar | -999.0 | 9,831 | 784,016 | 0.012539284912552805 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0473:0705:bulge_disk.mag_err_model_bd_total_f444w -->
| `0705:bulge_disk.mag_err_model_bd_total_f444w` | `bulge_disk.mag_err_model_bd_total_f444w` | HDU 1 [B+D] | scalar | -999.0 | 15,268 | 784,016 | 0.01947409236546193 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0474:0706:bulge_disk.mag_model_bulge_f115w -->
| `0706:bulge_disk.mag_model_bulge_f115w` | `bulge_disk.mag_model_bulge_f115w` | HDU 1 [B+D] | scalar | 999.0 | 27,767 | 784,016 | 0.035416369053692782 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0475:0707:bulge_disk.mag_model_bulge_f150w -->
| `0707:bulge_disk.mag_model_bulge_f150w` | `bulge_disk.mag_model_bulge_f150w` | HDU 1 [B+D] | scalar | 999.0 | 17,406 | 784,016 | 0.022201077529030021 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0476:0708:bulge_disk.mag_model_bulge_f277w -->
| `0708:bulge_disk.mag_model_bulge_f277w` | `bulge_disk.mag_model_bulge_f277w` | HDU 1 [B+D] | scalar | 999.0 | 25,329 | 784,016 | 0.032306738637986977 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0477:0709:bulge_disk.mag_model_bulge_f444w -->
| `0709:bulge_disk.mag_model_bulge_f444w` | `bulge_disk.mag_model_bulge_f444w` | HDU 1 [B+D] | scalar | 999.0 | 34,301 | 784,016 | 0.043750382645252141 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0478:0710:bulge_disk.mag_err_model_bulge_f115w -->
| `0710:bulge_disk.mag_err_model_bulge_f115w` | `bulge_disk.mag_err_model_bulge_f115w` | HDU 1 [B+D] | scalar | -999.0 | 28,567 | 784,016 | 0.036436756392726678 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0479:0711:bulge_disk.mag_err_model_bulge_f150w -->
| `0711:bulge_disk.mag_err_model_bulge_f150w` | `bulge_disk.mag_err_model_bulge_f150w` | HDU 1 [B+D] | scalar | -999.0 | 18,169 | 784,016 | 0.023174271953633599 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0480:0712:bulge_disk.mag_err_model_bulge_f277w -->
| `0712:bulge_disk.mag_err_model_bulge_f277w` | `bulge_disk.mag_err_model_bulge_f277w` | HDU 1 [B+D] | scalar | -999.0 | 25,197 | 784,016 | 0.032138374727046386 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0481:0713:bulge_disk.mag_err_model_bulge_f444w -->
| `0713:bulge_disk.mag_err_model_bulge_f444w` | `bulge_disk.mag_err_model_bulge_f444w` | HDU 1 [B+D] | scalar | -999.0 | 32,276 | 784,016 | 0.041167527193322583 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0482:0714:bulge_disk.mag_model_disk_f115w -->
| `0714:bulge_disk.mag_model_disk_f115w` | `bulge_disk.mag_model_disk_f115w` | HDU 1 [B+D] | scalar | 999.0 | 27,651 | 784,016 | 0.03526841288953287 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0483:0715:bulge_disk.mag_model_disk_f150w -->
| `0715:bulge_disk.mag_model_disk_f150w` | `bulge_disk.mag_model_disk_f150w` | HDU 1 [B+D] | scalar | 999.0 | 17,297 | 784,016 | 0.022062049754086651 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0484:0716:bulge_disk.mag_model_disk_f277w -->
| `0716:bulge_disk.mag_model_disk_f277w` | `bulge_disk.mag_model_disk_f277w` | HDU 1 [B+D] | scalar | 999.0 | 25,244 | 784,016 | 0.032198322483214629 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0485:0717:bulge_disk.mag_model_disk_f444w -->
| `0717:bulge_disk.mag_model_disk_f444w` | `bulge_disk.mag_model_disk_f444w` | HDU 1 [B+D] | scalar | 999.0 | 34,210 | 784,016 | 0.043634313585437033 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0486:0718:bulge_disk.mag_err_model_disk_f115w -->
| `0718:bulge_disk.mag_err_model_disk_f115w` | `bulge_disk.mag_err_model_disk_f115w` | HDU 1 [B+D] | scalar | -999.0 | 20,135 | 784,016 | 0.025681873839309401 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0487:0719:bulge_disk.mag_err_model_disk_f150w -->
| `0719:bulge_disk.mag_err_model_disk_f150w` | `bulge_disk.mag_err_model_disk_f150w` | HDU 1 [B+D] | scalar | -999.0 | 13,395 | 784,016 | 0.017085110507948819 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0488:0720:bulge_disk.mag_err_model_disk_f277w -->
| `0720:bulge_disk.mag_err_model_disk_f277w` | `bulge_disk.mag_err_model_disk_f277w` | HDU 1 [B+D] | scalar | -999.0 | 16,214 | 784,016 | 0.020680700393869513 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0489:0721:bulge_disk.mag_err_model_disk_f444w -->
| `0721:bulge_disk.mag_err_model_disk_f444w` | `bulge_disk.mag_err_model_disk_f444w` | HDU 1 [B+D] | scalar | -999.0 | 22,834 | 784,016 | 0.029124405624375013 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0490:0734:bulge_disk.flux_err_model_bulge_f115w -->
| `0734:bulge_disk.flux_err_model_bulge_f115w` | `bulge_disk.flux_err_model_bulge_f115w` | HDU 1 [B+D] | scalar | -999.0 | 2,732 | 784,016 | 0.0034846227628007593 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0491:0735:bulge_disk.flux_err_model_bulge_f150w -->
| `0735:bulge_disk.flux_err_model_bulge_f150w` | `bulge_disk.flux_err_model_bulge_f150w` | HDU 1 [B+D] | scalar | -999.0 | 2,184 | 784,016 | 0.0027856574355625396 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0492:0736:bulge_disk.flux_err_model_bulge_f277w -->
| `0736:bulge_disk.flux_err_model_bulge_f277w` | `bulge_disk.flux_err_model_bulge_f277w` | HDU 1 [B+D] | scalar | -999.0 | 1,492 | 784,016 | 0.0019030223872982183 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0493:0742:bulge_disk.flux_err_model_disk_f115w -->
| `0742:bulge_disk.flux_err_model_disk_f115w` | `bulge_disk.flux_err_model_disk_f115w` | HDU 1 [B+D] | scalar | -999.0 | 2,732 | 784,016 | 0.0034846227628007593 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0494:0743:bulge_disk.flux_err_model_disk_f150w -->
| `0743:bulge_disk.flux_err_model_disk_f150w` | `bulge_disk.flux_err_model_disk_f150w` | HDU 1 [B+D] | scalar | -999.0 | 2,184 | 784,016 | 0.0027856574355625396 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0495:0744:bulge_disk.flux_err_model_disk_f277w -->
| `0744:bulge_disk.flux_err_model_disk_f277w` | `bulge_disk.flux_err_model_disk_f277w` | HDU 1 [B+D] | scalar | -999.0 | 1,492 | 784,016 | 0.0019030223872982183 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0496:0754:bulge_disk.mag_model_bd_total_hst_f814w -->
| `0754:bulge_disk.mag_model_bd_total_hst_f814w` | `bulge_disk.mag_model_bd_total_hst_f814w` | HDU 1 [B+D] | scalar | 999.0 | 47,109 | 784,016 | 0.060086783943184834 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0497:0755:bulge_disk.mag_model_bd_total_f770w -->
| `0755:bulge_disk.mag_model_bd_total_f770w` | `bulge_disk.mag_model_bd_total_f770w` | HDU 1 [B+D] | scalar | 999.0 | 72,930 | 784,016 | 0.09302106079467766 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0498:0756:bulge_disk.mag_model_bd_total_cfht_u -->
| `0756:bulge_disk.mag_model_bd_total_cfht_u` | `bulge_disk.mag_model_bd_total_cfht_u` | HDU 1 [B+D] | scalar | 999.0 | 234,217 | 784,016 | 0.29874007673312791 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0499:0757:bulge_disk.mag_model_bd_total_hsc_g -->
| `0757:bulge_disk.mag_model_bd_total_hsc_g` | `bulge_disk.mag_model_bd_total_hsc_g` | HDU 1 [B+D] | scalar | 999.0 | 168,356 | 784,016 | 0.2147354135629885 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0500:0758:bulge_disk.mag_model_bd_total_hsc_r -->
| `0758:bulge_disk.mag_model_bd_total_hsc_r` | `bulge_disk.mag_model_bd_total_hsc_r` | HDU 1 [B+D] | scalar | 999.0 | 132,324 | 784,016 | 0.16877716781290178 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0501:0759:bulge_disk.mag_model_bd_total_hsc_i -->
| `0759:bulge_disk.mag_model_bd_total_hsc_i` | `bulge_disk.mag_model_bd_total_hsc_i` | HDU 1 [B+D] | scalar | 999.0 | 95,502 | 784,016 | 0.12181128956551907 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0502:0760:bulge_disk.mag_model_bd_total_hsc_z -->
| `0760:bulge_disk.mag_model_bd_total_hsc_z` | `bulge_disk.mag_model_bd_total_hsc_z` | HDU 1 [B+D] | scalar | 999.0 | 98,505 | 784,016 | 0.12564156853941758 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0503:0761:bulge_disk.mag_model_bd_total_hsc_y -->
| `0761:bulge_disk.mag_model_bd_total_hsc_y` | `bulge_disk.mag_model_bd_total_hsc_y` | HDU 1 [B+D] | scalar | 999.0 | 179,391 | 784,016 | 0.22881038142078733 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0504:0762:bulge_disk.mag_model_bd_total_hsc_nb0816 -->
| `0762:bulge_disk.mag_model_bd_total_hsc_nb0816` | `bulge_disk.mag_model_bd_total_hsc_nb0816` | HDU 1 [B+D] | scalar | 999.0 | 182,372 | 784,016 | 0.23261259974286239 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0505:0763:bulge_disk.mag_model_bd_total_hsc_nb0921 -->
| `0763:bulge_disk.mag_model_bd_total_hsc_nb0921` | `bulge_disk.mag_model_bd_total_hsc_nb0921` | HDU 1 [B+D] | scalar | 999.0 | 157,920 | 784,016 | 0.20142446072529133 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0506:0764:bulge_disk.mag_model_bd_total_hsc_nb1010 -->
| `0764:bulge_disk.mag_model_bd_total_hsc_nb1010` | `bulge_disk.mag_model_bd_total_hsc_nb1010` | HDU 1 [B+D] | scalar | 999.0 | 306,620 | 784,016 | 0.39108895736821697 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0507:0765:bulge_disk.mag_model_bd_total_uvista_y -->
| `0765:bulge_disk.mag_model_bd_total_uvista_y` | `bulge_disk.mag_model_bd_total_uvista_y` | HDU 1 [B+D] | scalar | 999.0 | 157,914 | 784,016 | 0.20141680782024857 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0508:0766:bulge_disk.mag_model_bd_total_uvista_j -->
| `0766:bulge_disk.mag_model_bd_total_uvista_j` | `bulge_disk.mag_model_bd_total_uvista_j` | HDU 1 [B+D] | scalar | 999.0 | 136,748 | 784,016 | 0.17441990979775923 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0509:0767:bulge_disk.mag_model_bd_total_uvista_h -->
| `0767:bulge_disk.mag_model_bd_total_uvista_h` | `bulge_disk.mag_model_bd_total_uvista_h` | HDU 1 [B+D] | scalar | 999.0 | 142,859 | 784,016 | 0.18221439358380442 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0510:0768:bulge_disk.mag_model_bd_total_uvista_ks -->
| `0768:bulge_disk.mag_model_bd_total_uvista_ks` | `bulge_disk.mag_model_bd_total_uvista_ks` | HDU 1 [B+D] | scalar | 999.0 | 166,720 | 784,016 | 0.21264872145466418 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0511:0769:bulge_disk.mag_model_bd_total_sc_ia484 -->
| `0769:bulge_disk.mag_model_bd_total_sc_ia484` | `bulge_disk.mag_model_bd_total_sc_ia484` | HDU 1 [B+D] | scalar | 999.0 | 239,144 | 784,016 | 0.30502438725740288 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0512:0770:bulge_disk.mag_model_bd_total_sc_ia527 -->
| `0770:bulge_disk.mag_model_bd_total_sc_ia527` | `bulge_disk.mag_model_bd_total_sc_ia527` | HDU 1 [B+D] | scalar | 999.0 | 226,918 | 784,016 | 0.28943031774861738 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0513:0771:bulge_disk.mag_model_bd_total_sc_ia624 -->
| `0771:bulge_disk.mag_model_bd_total_sc_ia624` | `bulge_disk.mag_model_bd_total_sc_ia624` | HDU 1 [B+D] | scalar | 999.0 | 203,653 | 784,016 | 0.25975617844533783 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0514:0772:bulge_disk.mag_model_bd_total_sc_ia679 -->
| `0772:bulge_disk.mag_model_bd_total_sc_ia679` | `bulge_disk.mag_model_bd_total_sc_ia679` | HDU 1 [B+D] | scalar | 999.0 | 289,130 | 784,016 | 0.36878073916858839 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0515:0773:bulge_disk.mag_model_bd_total_sc_ia738 -->
| `0773:bulge_disk.mag_model_bd_total_sc_ia738` | `bulge_disk.mag_model_bd_total_sc_ia738` | HDU 1 [B+D] | scalar | 999.0 | 208,934 | 784,016 | 0.26649201036713538 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0516:0774:bulge_disk.mag_model_bd_total_sc_ia767 -->
| `0774:bulge_disk.mag_model_bd_total_sc_ia767` | `bulge_disk.mag_model_bd_total_sc_ia767` | HDU 1 [B+D] | scalar | 999.0 | 278,054 | 784,016 | 0.35465347645966411 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0517:0775:bulge_disk.mag_model_bd_total_sc_ib427 -->
| `0775:bulge_disk.mag_model_bd_total_sc_ib427` | `bulge_disk.mag_model_bd_total_sc_ib427` | HDU 1 [B+D] | scalar | 999.0 | 300,321 | 784,016 | 0.3830546825574988 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0518:0776:bulge_disk.mag_model_bd_total_sc_ib505 -->
| `0776:bulge_disk.mag_model_bd_total_sc_ib505` | `bulge_disk.mag_model_bd_total_sc_ib505` | HDU 1 [B+D] | scalar | 999.0 | 266,133 | 784,016 | 0.33944842962388522 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0519:0777:bulge_disk.mag_model_bd_total_sc_ib574 -->
| `0777:bulge_disk.mag_model_bd_total_sc_ib574` | `bulge_disk.mag_model_bd_total_sc_ib574` | HDU 1 [B+D] | scalar | 999.0 | 309,597 | 784,016 | 0.39488607375359686 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0520:0778:bulge_disk.mag_model_bd_total_sc_ib709 -->
| `0778:bulge_disk.mag_model_bd_total_sc_ib709` | `bulge_disk.mag_model_bd_total_sc_ib709` | HDU 1 [B+D] | scalar | 999.0 | 263,286 | 784,016 | 0.33581712618109832 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0521:0779:bulge_disk.mag_model_bd_total_sc_ib827 -->
| `0779:bulge_disk.mag_model_bd_total_sc_ib827` | `bulge_disk.mag_model_bd_total_sc_ib827` | HDU 1 [B+D] | scalar | 999.0 | 283,120 | 784,016 | 0.36111507928409625 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0522:0780:bulge_disk.mag_model_bd_total_sc_nb711 -->
| `0780:bulge_disk.mag_model_bd_total_sc_nb711` | `bulge_disk.mag_model_bd_total_sc_nb711` | HDU 1 [B+D] | scalar | 999.0 | 228,694 | 784,016 | 0.29169557764127263 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0523:0781:bulge_disk.mag_model_bd_total_sc_nb816 -->
| `0781:bulge_disk.mag_model_bd_total_sc_nb816` | `bulge_disk.mag_model_bd_total_sc_nb816` | HDU 1 [B+D] | scalar | 999.0 | 295,003 | 784,016 | 0.37627165772127097 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0524:0782:bulge_disk.mag_err_model_bd_total_hst_f814w -->
| `0782:bulge_disk.mag_err_model_bd_total_hst_f814w` | `bulge_disk.mag_err_model_bd_total_hst_f814w` | HDU 1 [B+D] | scalar | -999.0 | 29,579 | 784,016 | 0.037727546376604561 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0525:0783:bulge_disk.mag_err_model_bd_total_f770w -->
| `0783:bulge_disk.mag_err_model_bd_total_f770w` | `bulge_disk.mag_err_model_bd_total_f770w` | HDU 1 [B+D] | scalar | -999.0 | 39,362 | 784,016 | 0.050205608048815333 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0526:0784:bulge_disk.mag_err_model_bd_total_cfht_u -->
| `0784:bulge_disk.mag_err_model_bd_total_cfht_u` | `bulge_disk.mag_err_model_bd_total_cfht_u` | HDU 1 [B+D] | scalar | -999.0 | 113,597 | 784,016 | 0.14489117569029203 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0527:0785:bulge_disk.mag_err_model_bd_total_hsc_g -->
| `0785:bulge_disk.mag_err_model_bd_total_hsc_g` | `bulge_disk.mag_err_model_bd_total_hsc_g` | HDU 1 [B+D] | scalar | -999.0 | 77,482 | 784,016 | 0.09882706475378053 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0528:0786:bulge_disk.mag_err_model_bd_total_hsc_r -->
| `0786:bulge_disk.mag_err_model_bd_total_hsc_r` | `bulge_disk.mag_err_model_bd_total_hsc_r` | HDU 1 [B+D] | scalar | -999.0 | 71,560 | 784,016 | 0.091273647476582107 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0529:0787:bulge_disk.mag_err_model_bd_total_hsc_i -->
| `0787:bulge_disk.mag_err_model_bd_total_hsc_i` | `bulge_disk.mag_err_model_bd_total_hsc_i` | HDU 1 [B+D] | scalar | -999.0 | 53,868 | 784,016 | 0.068707781473847471 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0530:0788:bulge_disk.mag_err_model_bd_total_hsc_z -->
| `0788:bulge_disk.mag_err_model_bd_total_hsc_z` | `bulge_disk.mag_err_model_bd_total_hsc_z` | HDU 1 [B+D] | scalar | -999.0 | 65,627 | 784,016 | 0.08370619987347197 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0531:0789:bulge_disk.mag_err_model_bd_total_hsc_y -->
| `0789:bulge_disk.mag_err_model_bd_total_hsc_y` | `bulge_disk.mag_err_model_bd_total_hsc_y` | HDU 1 [B+D] | scalar | -999.0 | 125,729 | 784,016 | 0.1603653496867411 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0532:0790:bulge_disk.mag_err_model_bd_total_hsc_nb0816 -->
| `0790:bulge_disk.mag_err_model_bd_total_hsc_nb0816` | `bulge_disk.mag_err_model_bd_total_hsc_nb0816` | HDU 1 [B+D] | scalar | -999.0 | 137,690 | 784,016 | 0.17562141588947164 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0533:0791:bulge_disk.mag_err_model_bd_total_hsc_nb0921 -->
| `0791:bulge_disk.mag_err_model_bd_total_hsc_nb0921` | `bulge_disk.mag_err_model_bd_total_hsc_nb0921` | HDU 1 [B+D] | scalar | -999.0 | 122,170 | 784,016 | 0.15582590151221404 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0534:0792:bulge_disk.mag_err_model_bd_total_hsc_nb1010 -->
| `0792:bulge_disk.mag_err_model_bd_total_hsc_nb1010` | `bulge_disk.mag_err_model_bd_total_hsc_nb1010` | HDU 1 [B+D] | scalar | -999.0 | 254,308 | 784,016 | 0.32436582926879043 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0535:0793:bulge_disk.mag_err_model_bd_total_uvista_y -->
| `0793:bulge_disk.mag_err_model_bd_total_uvista_y` | `bulge_disk.mag_err_model_bd_total_uvista_y` | HDU 1 [B+D] | scalar | -999.0 | 56,463 | 784,016 | 0.072017662904838672 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0536:0794:bulge_disk.mag_err_model_bd_total_uvista_j -->
| `0794:bulge_disk.mag_err_model_bd_total_uvista_j` | `bulge_disk.mag_err_model_bd_total_uvista_j` | HDU 1 [B+D] | scalar | -999.0 | 56,411 | 784,016 | 0.071951337727801476 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0537:0795:bulge_disk.mag_err_model_bd_total_uvista_h -->
| `0795:bulge_disk.mag_err_model_bd_total_uvista_h` | `bulge_disk.mag_err_model_bd_total_uvista_h` | HDU 1 [B+D] | scalar | -999.0 | 64,728 | 784,016 | 0.082559539601232634 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0538:0796:bulge_disk.mag_err_model_bd_total_uvista_ks -->
| `0796:bulge_disk.mag_err_model_bd_total_uvista_ks` | `bulge_disk.mag_err_model_bd_total_uvista_ks` | HDU 1 [B+D] | scalar | -999.0 | 81,141 | 784,016 | 0.10349406134568682 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0539:0797:bulge_disk.mag_err_model_bd_total_sc_ia484 -->
| `0797:bulge_disk.mag_err_model_bd_total_sc_ia484` | `bulge_disk.mag_err_model_bd_total_sc_ia484` | HDU 1 [B+D] | scalar | -999.0 | 104,783 | 784,016 | 0.13364905818248607 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0540:0798:bulge_disk.mag_err_model_bd_total_sc_ia527 -->
| `0798:bulge_disk.mag_err_model_bd_total_sc_ia527` | `bulge_disk.mag_err_model_bd_total_sc_ia527` | HDU 1 [B+D] | scalar | -999.0 | 109,728 | 784,016 | 0.13995632742188935 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0541:0799:bulge_disk.mag_err_model_bd_total_sc_ia624 -->
| `0799:bulge_disk.mag_err_model_bd_total_sc_ia624` | `bulge_disk.mag_err_model_bd_total_sc_ia624` | HDU 1 [B+D] | scalar | -999.0 | 82,443 | 784,016 | 0.10515474173996449 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0542:0800:bulge_disk.mag_err_model_bd_total_sc_ia679 -->
| `0800:bulge_disk.mag_err_model_bd_total_sc_ia679` | `bulge_disk.mag_err_model_bd_total_sc_ia679` | HDU 1 [B+D] | scalar | -999.0 | 229,451 | 784,016 | 0.29266111916083343 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0543:0801:bulge_disk.mag_err_model_bd_total_sc_ia738 -->
| `0801:bulge_disk.mag_err_model_bd_total_sc_ia738` | `bulge_disk.mag_err_model_bd_total_sc_ia738` | HDU 1 [B+D] | scalar | -999.0 | 90,590 | 784,016 | 0.11554611130385094 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0544:0802:bulge_disk.mag_err_model_bd_total_sc_ia767 -->
| `0802:bulge_disk.mag_err_model_bd_total_sc_ia767` | `bulge_disk.mag_err_model_bd_total_sc_ia767` | HDU 1 [B+D] | scalar | -999.0 | 200,351 | 784,016 | 0.25554452970347546 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0545:0803:bulge_disk.mag_err_model_bd_total_sc_ib427 -->
| `0803:bulge_disk.mag_err_model_bd_total_sc_ib427` | `bulge_disk.mag_err_model_bd_total_sc_ib427` | HDU 1 [B+D] | scalar | -999.0 | 219,374 | 784,016 | 0.27980806514152773 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0546:0804:bulge_disk.mag_err_model_bd_total_sc_ib505 -->
| `0804:bulge_disk.mag_err_model_bd_total_sc_ib505` | `bulge_disk.mag_err_model_bd_total_sc_ib505` | HDU 1 [B+D] | scalar | -999.0 | 154,214 | 784,016 | 0.1966975163772168 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0547:0805:bulge_disk.mag_err_model_bd_total_sc_ib574 -->
| `0805:bulge_disk.mag_err_model_bd_total_sc_ib574` | `bulge_disk.mag_err_model_bd_total_sc_ib574` | HDU 1 [B+D] | scalar | -999.0 | 235,528 | 784,016 | 0.30041223648496967 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0548:0806:bulge_disk.mag_err_model_bd_total_sc_ib709 -->
| `0806:bulge_disk.mag_err_model_bd_total_sc_ib709` | `bulge_disk.mag_err_model_bd_total_sc_ib709` | HDU 1 [B+D] | scalar | -999.0 | 173,354 | 784,016 | 0.22111028346360279 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0549:0807:bulge_disk.mag_err_model_bd_total_sc_ib827 -->
| `0807:bulge_disk.mag_err_model_bd_total_sc_ib827` | `bulge_disk.mag_err_model_bd_total_sc_ib827` | HDU 1 [B+D] | scalar | -999.0 | 209,844 | 784,016 | 0.26765270096528643 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0550:0808:bulge_disk.mag_err_model_bd_total_sc_nb711 -->
| `0808:bulge_disk.mag_err_model_bd_total_sc_nb711` | `bulge_disk.mag_err_model_bd_total_sc_nb711` | HDU 1 [B+D] | scalar | -999.0 | 77,648 | 784,016 | 0.099038795126630066 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0551:0809:bulge_disk.mag_err_model_bd_total_sc_nb816 -->
| `0809:bulge_disk.mag_err_model_bd_total_sc_nb816` | `bulge_disk.mag_err_model_bd_total_sc_nb816` | HDU 1 [B+D] | scalar | -999.0 | 231,449 | 784,016 | 0.29520953654007059 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0552:0810:bulge_disk.mag_model_bulge_hst_f814w -->
| `0810:bulge_disk.mag_model_bulge_hst_f814w` | `bulge_disk.mag_model_bulge_hst_f814w` | HDU 1 [B+D] | scalar | 999.0 | 47,109 | 784,016 | 0.060086783943184834 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0553:0811:bulge_disk.mag_model_bulge_f770w -->
| `0811:bulge_disk.mag_model_bulge_f770w` | `bulge_disk.mag_model_bulge_f770w` | HDU 1 [B+D] | scalar | 999.0 | 72,930 | 784,016 | 0.09302106079467766 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0554:0812:bulge_disk.mag_model_bulge_cfht_u -->
| `0812:bulge_disk.mag_model_bulge_cfht_u` | `bulge_disk.mag_model_bulge_cfht_u` | HDU 1 [B+D] | scalar | 999.0 | 234,217 | 784,016 | 0.29874007673312791 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0555:0813:bulge_disk.mag_model_bulge_hsc_g -->
| `0813:bulge_disk.mag_model_bulge_hsc_g` | `bulge_disk.mag_model_bulge_hsc_g` | HDU 1 [B+D] | scalar | 999.0 | 168,356 | 784,016 | 0.2147354135629885 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0556:0814:bulge_disk.mag_model_bulge_hsc_r -->
| `0814:bulge_disk.mag_model_bulge_hsc_r` | `bulge_disk.mag_model_bulge_hsc_r` | HDU 1 [B+D] | scalar | 999.0 | 132,324 | 784,016 | 0.16877716781290178 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0557:0815:bulge_disk.mag_model_bulge_hsc_i -->
| `0815:bulge_disk.mag_model_bulge_hsc_i` | `bulge_disk.mag_model_bulge_hsc_i` | HDU 1 [B+D] | scalar | 999.0 | 95,502 | 784,016 | 0.12181128956551907 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0558:0816:bulge_disk.mag_model_bulge_hsc_z -->
| `0816:bulge_disk.mag_model_bulge_hsc_z` | `bulge_disk.mag_model_bulge_hsc_z` | HDU 1 [B+D] | scalar | 999.0 | 98,505 | 784,016 | 0.12564156853941758 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0559:0817:bulge_disk.mag_model_bulge_hsc_y -->
| `0817:bulge_disk.mag_model_bulge_hsc_y` | `bulge_disk.mag_model_bulge_hsc_y` | HDU 1 [B+D] | scalar | 999.0 | 179,391 | 784,016 | 0.22881038142078733 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0560:0818:bulge_disk.mag_model_bulge_hsc_nb0816 -->
| `0818:bulge_disk.mag_model_bulge_hsc_nb0816` | `bulge_disk.mag_model_bulge_hsc_nb0816` | HDU 1 [B+D] | scalar | 999.0 | 182,372 | 784,016 | 0.23261259974286239 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0561:0819:bulge_disk.mag_model_bulge_hsc_nb0921 -->
| `0819:bulge_disk.mag_model_bulge_hsc_nb0921` | `bulge_disk.mag_model_bulge_hsc_nb0921` | HDU 1 [B+D] | scalar | 999.0 | 157,920 | 784,016 | 0.20142446072529133 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0562:0820:bulge_disk.mag_model_bulge_hsc_nb1010 -->
| `0820:bulge_disk.mag_model_bulge_hsc_nb1010` | `bulge_disk.mag_model_bulge_hsc_nb1010` | HDU 1 [B+D] | scalar | 999.0 | 306,620 | 784,016 | 0.39108895736821697 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0563:0821:bulge_disk.mag_model_bulge_uvista_y -->
| `0821:bulge_disk.mag_model_bulge_uvista_y` | `bulge_disk.mag_model_bulge_uvista_y` | HDU 1 [B+D] | scalar | 999.0 | 157,914 | 784,016 | 0.20141680782024857 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0564:0822:bulge_disk.mag_model_bulge_uvista_j -->
| `0822:bulge_disk.mag_model_bulge_uvista_j` | `bulge_disk.mag_model_bulge_uvista_j` | HDU 1 [B+D] | scalar | 999.0 | 136,748 | 784,016 | 0.17441990979775923 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0565:0823:bulge_disk.mag_model_bulge_uvista_h -->
| `0823:bulge_disk.mag_model_bulge_uvista_h` | `bulge_disk.mag_model_bulge_uvista_h` | HDU 1 [B+D] | scalar | 999.0 | 142,859 | 784,016 | 0.18221439358380442 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0566:0824:bulge_disk.mag_model_bulge_uvista_ks -->
| `0824:bulge_disk.mag_model_bulge_uvista_ks` | `bulge_disk.mag_model_bulge_uvista_ks` | HDU 1 [B+D] | scalar | 999.0 | 166,720 | 784,016 | 0.21264872145466418 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0567:0825:bulge_disk.mag_model_bulge_sc_ia484 -->
| `0825:bulge_disk.mag_model_bulge_sc_ia484` | `bulge_disk.mag_model_bulge_sc_ia484` | HDU 1 [B+D] | scalar | 999.0 | 239,144 | 784,016 | 0.30502438725740288 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0568:0826:bulge_disk.mag_model_bulge_sc_ia527 -->
| `0826:bulge_disk.mag_model_bulge_sc_ia527` | `bulge_disk.mag_model_bulge_sc_ia527` | HDU 1 [B+D] | scalar | 999.0 | 226,918 | 784,016 | 0.28943031774861738 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0569:0827:bulge_disk.mag_model_bulge_sc_ia624 -->
| `0827:bulge_disk.mag_model_bulge_sc_ia624` | `bulge_disk.mag_model_bulge_sc_ia624` | HDU 1 [B+D] | scalar | 999.0 | 203,653 | 784,016 | 0.25975617844533783 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0570:0828:bulge_disk.mag_model_bulge_sc_ia679 -->
| `0828:bulge_disk.mag_model_bulge_sc_ia679` | `bulge_disk.mag_model_bulge_sc_ia679` | HDU 1 [B+D] | scalar | 999.0 | 289,130 | 784,016 | 0.36878073916858839 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0571:0829:bulge_disk.mag_model_bulge_sc_ia738 -->
| `0829:bulge_disk.mag_model_bulge_sc_ia738` | `bulge_disk.mag_model_bulge_sc_ia738` | HDU 1 [B+D] | scalar | 999.0 | 208,934 | 784,016 | 0.26649201036713538 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0572:0830:bulge_disk.mag_model_bulge_sc_ia767 -->
| `0830:bulge_disk.mag_model_bulge_sc_ia767` | `bulge_disk.mag_model_bulge_sc_ia767` | HDU 1 [B+D] | scalar | 999.0 | 278,054 | 784,016 | 0.35465347645966411 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0573:0831:bulge_disk.mag_model_bulge_sc_ib427 -->
| `0831:bulge_disk.mag_model_bulge_sc_ib427` | `bulge_disk.mag_model_bulge_sc_ib427` | HDU 1 [B+D] | scalar | 999.0 | 300,321 | 784,016 | 0.3830546825574988 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0574:0832:bulge_disk.mag_model_bulge_sc_ib505 -->
| `0832:bulge_disk.mag_model_bulge_sc_ib505` | `bulge_disk.mag_model_bulge_sc_ib505` | HDU 1 [B+D] | scalar | 999.0 | 266,133 | 784,016 | 0.33944842962388522 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0575:0833:bulge_disk.mag_model_bulge_sc_ib574 -->
| `0833:bulge_disk.mag_model_bulge_sc_ib574` | `bulge_disk.mag_model_bulge_sc_ib574` | HDU 1 [B+D] | scalar | 999.0 | 309,597 | 784,016 | 0.39488607375359686 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0576:0834:bulge_disk.mag_model_bulge_sc_ib709 -->
| `0834:bulge_disk.mag_model_bulge_sc_ib709` | `bulge_disk.mag_model_bulge_sc_ib709` | HDU 1 [B+D] | scalar | 999.0 | 263,286 | 784,016 | 0.33581712618109832 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0577:0835:bulge_disk.mag_model_bulge_sc_ib827 -->
| `0835:bulge_disk.mag_model_bulge_sc_ib827` | `bulge_disk.mag_model_bulge_sc_ib827` | HDU 1 [B+D] | scalar | 999.0 | 283,120 | 784,016 | 0.36111507928409625 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0578:0836:bulge_disk.mag_model_bulge_sc_nb711 -->
| `0836:bulge_disk.mag_model_bulge_sc_nb711` | `bulge_disk.mag_model_bulge_sc_nb711` | HDU 1 [B+D] | scalar | 999.0 | 228,694 | 784,016 | 0.29169557764127263 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0579:0837:bulge_disk.mag_model_bulge_sc_nb816 -->
| `0837:bulge_disk.mag_model_bulge_sc_nb816` | `bulge_disk.mag_model_bulge_sc_nb816` | HDU 1 [B+D] | scalar | 999.0 | 295,003 | 784,016 | 0.37627165772127097 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0580:0838:bulge_disk.mag_err_model_bulge_hst_f814w -->
| `0838:bulge_disk.mag_err_model_bulge_hst_f814w` | `bulge_disk.mag_err_model_bulge_hst_f814w` | HDU 1 [B+D] | scalar | -999.0 | 52,925 | 784,016 | 0.067504999897961271 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0581:0839:bulge_disk.mag_err_model_bulge_f770w -->
| `0839:bulge_disk.mag_err_model_bulge_f770w` | `bulge_disk.mag_err_model_bulge_f770w` | HDU 1 [B+D] | scalar | -999.0 | 70,745 | 784,016 | 0.090234127874941325 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0582:0840:bulge_disk.mag_err_model_bulge_cfht_u -->
| `0840:bulge_disk.mag_err_model_bulge_cfht_u` | `bulge_disk.mag_err_model_bulge_cfht_u` | HDU 1 [B+D] | scalar | -999.0 | 227,136 | 784,016 | 0.28970837329850413 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0583:0841:bulge_disk.mag_err_model_bulge_hsc_g -->
| `0841:bulge_disk.mag_err_model_bulge_hsc_g` | `bulge_disk.mag_err_model_bulge_hsc_g` | HDU 1 [B+D] | scalar | -999.0 | 164,077 | 784,016 | 0.20927761678333096 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0584:0842:bulge_disk.mag_err_model_bulge_hsc_r -->
| `0842:bulge_disk.mag_err_model_bulge_hsc_r` | `bulge_disk.mag_err_model_bulge_hsc_r` | HDU 1 [B+D] | scalar | -999.0 | 131,946 | 784,016 | 0.16829503479520827 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0585:0843:bulge_disk.mag_err_model_bulge_hsc_i -->
| `0843:bulge_disk.mag_err_model_bulge_hsc_i` | `bulge_disk.mag_err_model_bulge_hsc_i` | HDU 1 [B+D] | scalar | -999.0 | 98,033 | 784,016 | 0.12503954000938755 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0586:0844:bulge_disk.mag_err_model_bulge_hsc_z -->
| `0844:bulge_disk.mag_err_model_bulge_hsc_z` | `bulge_disk.mag_err_model_bulge_hsc_z` | HDU 1 [B+D] | scalar | -999.0 | 100,461 | 784,016 | 0.12813641558335545 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0587:0845:bulge_disk.mag_err_model_bulge_hsc_y -->
| `0845:bulge_disk.mag_err_model_bulge_hsc_y` | `bulge_disk.mag_err_model_bulge_hsc_y` | HDU 1 [B+D] | scalar | -999.0 | 180,212 | 784,016 | 0.22985755392747087 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0588:0846:bulge_disk.mag_err_model_bulge_hsc_nb0816 -->
| `0846:bulge_disk.mag_err_model_bulge_hsc_nb0816` | `bulge_disk.mag_err_model_bulge_hsc_nb0816` | HDU 1 [B+D] | scalar | -999.0 | 182,596 | 784,016 | 0.23289830819779189 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0589:0847:bulge_disk.mag_err_model_bulge_hsc_nb0921 -->
| `0847:bulge_disk.mag_err_model_bulge_hsc_nb0921` | `bulge_disk.mag_err_model_bulge_hsc_nb0921` | HDU 1 [B+D] | scalar | -999.0 | 158,560 | 784,016 | 0.20224077059651843 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0590:0848:bulge_disk.mag_err_model_bulge_hsc_nb1010 -->
| `0848:bulge_disk.mag_err_model_bulge_hsc_nb1010` | `bulge_disk.mag_err_model_bulge_hsc_nb1010` | HDU 1 [B+D] | scalar | -999.0 | 307,114 | 784,016 | 0.39171904655007039 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0591:0849:bulge_disk.mag_err_model_bulge_uvista_y -->
| `0849:bulge_disk.mag_err_model_bulge_uvista_y` | `bulge_disk.mag_err_model_bulge_uvista_y` | HDU 1 [B+D] | scalar | -999.0 | 164,299 | 784,016 | 0.20956077426991285 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0592:0850:bulge_disk.mag_err_model_bulge_uvista_j -->
| `0850:bulge_disk.mag_err_model_bulge_uvista_j` | `bulge_disk.mag_err_model_bulge_uvista_j` | HDU 1 [B+D] | scalar | -999.0 | 143,510 | 784,016 | 0.18304473378094324 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0593:0851:bulge_disk.mag_err_model_bulge_uvista_h -->
| `0851:bulge_disk.mag_err_model_bulge_uvista_h` | `bulge_disk.mag_err_model_bulge_uvista_h` | HDU 1 [B+D] | scalar | -999.0 | 149,029 | 784,016 | 0.19008413093610335 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0594:0852:bulge_disk.mag_err_model_bulge_uvista_ks -->
| `0852:bulge_disk.mag_err_model_bulge_uvista_ks` | `bulge_disk.mag_err_model_bulge_uvista_ks` | HDU 1 [B+D] | scalar | -999.0 | 171,391 | 784,016 | 0.21860650803044837 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0595:0853:bulge_disk.mag_err_model_bulge_sc_ia484 -->
| `0853:bulge_disk.mag_err_model_bulge_sc_ia484` | `bulge_disk.mag_err_model_bulge_sc_ia484` | HDU 1 [B+D] | scalar | -999.0 | 233,923 | 784,016 | 0.29836508438603293 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0596:0854:bulge_disk.mag_err_model_bulge_sc_ia527 -->
| `0854:bulge_disk.mag_err_model_bulge_sc_ia527` | `bulge_disk.mag_err_model_bulge_sc_ia527` | HDU 1 [B+D] | scalar | -999.0 | 222,759 | 784,016 | 0.28412557906981489 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0597:0855:bulge_disk.mag_err_model_bulge_sc_ia624 -->
| `0855:bulge_disk.mag_err_model_bulge_sc_ia624` | `bulge_disk.mag_err_model_bulge_sc_ia624` | HDU 1 [B+D] | scalar | -999.0 | 201,009 | 784,016 | 0.25638379828983082 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0598:0856:bulge_disk.mag_err_model_bulge_sc_ia679 -->
| `0856:bulge_disk.mag_err_model_bulge_sc_ia679` | `bulge_disk.mag_err_model_bulge_sc_ia679` | HDU 1 [B+D] | scalar | -999.0 | 288,018 | 784,016 | 0.36736240076733129 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0599:0857:bulge_disk.mag_err_model_bulge_sc_ia738 -->
| `0857:bulge_disk.mag_err_model_bulge_sc_ia738` | `bulge_disk.mag_err_model_bulge_sc_ia738` | HDU 1 [B+D] | scalar | -999.0 | 206,829 | 784,016 | 0.26380711618130243 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0600:0858:bulge_disk.mag_err_model_bulge_sc_ia767 -->
| `0858:bulge_disk.mag_err_model_bulge_sc_ia767` | `bulge_disk.mag_err_model_bulge_sc_ia767` | HDU 1 [B+D] | scalar | -999.0 | 276,303 | 784,016 | 0.35242010367135362 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0601:0859:bulge_disk.mag_err_model_bulge_sc_ib427 -->
| `0859:bulge_disk.mag_err_model_bulge_sc_ib427` | `bulge_disk.mag_err_model_bulge_sc_ib427` | HDU 1 [B+D] | scalar | -999.0 | 295,389 | 784,016 | 0.37676399461235482 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0602:0860:bulge_disk.mag_err_model_bulge_sc_ib505 -->
| `0860:bulge_disk.mag_err_model_bulge_sc_ib505` | `bulge_disk.mag_err_model_bulge_sc_ib505` | HDU 1 [B+D] | scalar | -999.0 | 260,346 | 784,016 | 0.33206720271014878 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0603:0861:bulge_disk.mag_err_model_bulge_sc_ib574 -->
| `0861:bulge_disk.mag_err_model_bulge_sc_ib574` | `bulge_disk.mag_err_model_bulge_sc_ib574` | HDU 1 [B+D] | scalar | -999.0 | 305,896 | 784,016 | 0.39016550682639128 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0604:0862:bulge_disk.mag_err_model_bulge_sc_ib709 -->
| `0862:bulge_disk.mag_err_model_bulge_sc_ib709` | `bulge_disk.mag_err_model_bulge_sc_ib709` | HDU 1 [B+D] | scalar | -999.0 | 259,790 | 784,016 | 0.3313580335095202 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0605:0863:bulge_disk.mag_err_model_bulge_sc_ib827 -->
| `0863:bulge_disk.mag_err_model_bulge_sc_ib827` | `bulge_disk.mag_err_model_bulge_sc_ib827` | HDU 1 [B+D] | scalar | -999.0 | 281,085 | 784,016 | 0.35851946899042875 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0606:0864:bulge_disk.mag_err_model_bulge_sc_nb711 -->
| `0864:bulge_disk.mag_err_model_bulge_sc_nb711` | `bulge_disk.mag_err_model_bulge_sc_nb711` | HDU 1 [B+D] | scalar | -999.0 | 222,336 | 784,016 | 0.28358604926430075 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0607:0865:bulge_disk.mag_err_model_bulge_sc_nb816 -->
| `0865:bulge_disk.mag_err_model_bulge_sc_nb816` | `bulge_disk.mag_err_model_bulge_sc_nb816` | HDU 1 [B+D] | scalar | -999.0 | 293,109 | 784,016 | 0.37385589069610825 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0608:0866:bulge_disk.mag_model_disk_hst_f814w -->
| `0866:bulge_disk.mag_model_disk_hst_f814w` | `bulge_disk.mag_model_disk_hst_f814w` | HDU 1 [B+D] | scalar | 999.0 | 46,769 | 784,016 | 0.059653119324095429 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0609:0867:bulge_disk.mag_model_disk_f770w -->
| `0867:bulge_disk.mag_model_disk_f770w` | `bulge_disk.mag_model_disk_f770w` | HDU 1 [B+D] | scalar | 999.0 | 72,162 | 784,016 | 0.092041488949205122 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0610:0868:bulge_disk.mag_model_disk_cfht_u -->
| `0868:bulge_disk.mag_model_disk_cfht_u` | `bulge_disk.mag_model_disk_cfht_u` | HDU 1 [B+D] | scalar | 999.0 | 230,341 | 784,016 | 0.29379630007550867 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0611:0869:bulge_disk.mag_model_disk_hsc_g -->
| `0869:bulge_disk.mag_model_disk_hsc_g` | `bulge_disk.mag_model_disk_hsc_g` | HDU 1 [B+D] | scalar | 999.0 | 164,688 | 784,016 | 0.2100569376135181 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0612:0870:bulge_disk.mag_model_disk_hsc_r -->
| `0870:bulge_disk.mag_model_disk_hsc_r` | `bulge_disk.mag_model_disk_hsc_r` | HDU 1 [B+D] | scalar | 999.0 | 130,151 | 784,016 | 0.16600554070325096 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0613:0871:bulge_disk.mag_model_disk_hsc_i -->
| `0871:bulge_disk.mag_model_disk_hsc_i` | `bulge_disk.mag_model_disk_hsc_i` | HDU 1 [B+D] | scalar | 999.0 | 94,070 | 784,016 | 0.1199847962286484 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0614:0872:bulge_disk.mag_model_disk_hsc_z -->
| `0872:bulge_disk.mag_model_disk_hsc_z` | `bulge_disk.mag_model_disk_hsc_z` | HDU 1 [B+D] | scalar | 999.0 | 97,763 | 784,016 | 0.12469515928246362 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0615:0873:bulge_disk.mag_model_disk_hsc_y -->
| `0873:bulge_disk.mag_model_disk_hsc_y` | `bulge_disk.mag_model_disk_hsc_y` | HDU 1 [B+D] | scalar | 999.0 | 178,981 | 784,016 | 0.22828743290953246 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0616:0874:bulge_disk.mag_model_disk_hsc_nb0816 -->
| `0874:bulge_disk.mag_model_disk_hsc_nb0816` | `bulge_disk.mag_model_disk_hsc_nb0816` | HDU 1 [B+D] | scalar | 999.0 | 181,722 | 784,016 | 0.23178353502989735 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0617:0875:bulge_disk.mag_model_disk_hsc_nb0921 -->
| `0875:bulge_disk.mag_model_disk_hsc_nb0921` | `bulge_disk.mag_model_disk_hsc_nb0921` | HDU 1 [B+D] | scalar | 999.0 | 157,499 | 784,016 | 0.20088748188812472 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0618:0876:bulge_disk.mag_model_disk_hsc_nb1010 -->
| `0876:bulge_disk.mag_model_disk_hsc_nb1010` | `bulge_disk.mag_model_disk_hsc_nb1010` | HDU 1 [B+D] | scalar | 999.0 | 306,252 | 784,016 | 0.39061957919226137 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0619:0877:bulge_disk.mag_model_disk_uvista_y -->
| `0877:bulge_disk.mag_model_disk_uvista_y` | `bulge_disk.mag_model_disk_uvista_y` | HDU 1 [B+D] | scalar | 999.0 | 157,181 | 784,016 | 0.20048187792085875 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0620:0878:bulge_disk.mag_model_disk_uvista_j -->
| `0878:bulge_disk.mag_model_disk_uvista_j` | `bulge_disk.mag_model_disk_uvista_j` | HDU 1 [B+D] | scalar | 999.0 | 136,440 | 784,016 | 0.17402706067223117 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0621:0879:bulge_disk.mag_model_disk_uvista_h -->
| `0879:bulge_disk.mag_model_disk_uvista_h` | `bulge_disk.mag_model_disk_uvista_h` | HDU 1 [B+D] | scalar | 999.0 | 142,666 | 784,016 | 0.1819682251382625 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0622:0880:bulge_disk.mag_model_disk_uvista_ks -->
| `0880:bulge_disk.mag_model_disk_uvista_ks` | `bulge_disk.mag_model_disk_uvista_ks` | HDU 1 [B+D] | scalar | 999.0 | 166,561 | 784,016 | 0.2124459194710312 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0623:0881:bulge_disk.mag_model_disk_sc_ia484 -->
| `0881:bulge_disk.mag_model_disk_sc_ia484` | `bulge_disk.mag_model_disk_sc_ia484` | HDU 1 [B+D] | scalar | 999.0 | 236,698 | 784,016 | 0.30190455296830676 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0624:0882:bulge_disk.mag_model_disk_sc_ia527 -->
| `0882:bulge_disk.mag_model_disk_sc_ia527` | `bulge_disk.mag_model_disk_sc_ia527` | HDU 1 [B+D] | scalar | 999.0 | 224,600 | 784,016 | 0.28647374543376664 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0625:0883:bulge_disk.mag_model_disk_sc_ia624 -->
| `0883:bulge_disk.mag_model_disk_sc_ia624` | `bulge_disk.mag_model_disk_sc_ia624` | HDU 1 [B+D] | scalar | 999.0 | 201,630 | 784,016 | 0.2571758739617559 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0626:0884:bulge_disk.mag_model_disk_sc_ia679 -->
| `0884:bulge_disk.mag_model_disk_sc_ia679` | `bulge_disk.mag_model_disk_sc_ia679` | HDU 1 [B+D] | scalar | 999.0 | 288,300 | 784,016 | 0.36772208730434075 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0627:0885:bulge_disk.mag_model_disk_sc_ia738 -->
| `0885:bulge_disk.mag_model_disk_sc_ia738` | `bulge_disk.mag_model_disk_sc_ia738` | HDU 1 [B+D] | scalar | 999.0 | 207,537 | 784,016 | 0.26471015897634742 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0628:0886:bulge_disk.mag_model_disk_sc_ia767 -->
| `0886:bulge_disk.mag_model_disk_sc_ia767` | `bulge_disk.mag_model_disk_sc_ia767` | HDU 1 [B+D] | scalar | 999.0 | 277,278 | 784,016 | 0.35366370074080122 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0629:0887:bulge_disk.mag_model_disk_sc_ib427 -->
| `0887:bulge_disk.mag_model_disk_sc_ib427` | `bulge_disk.mag_model_disk_sc_ib427` | HDU 1 [B+D] | scalar | 999.0 | 297,693 | 784,016 | 0.37970271014877249 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0630:0888:bulge_disk.mag_model_disk_sc_ib505 -->
| `0888:bulge_disk.mag_model_disk_sc_ib505` | `bulge_disk.mag_model_disk_sc_ib505` | HDU 1 [B+D] | scalar | 999.0 | 263,953 | 784,016 | 0.33666787412501786 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0631:0889:bulge_disk.mag_model_disk_sc_ib574 -->
| `0889:bulge_disk.mag_model_disk_sc_ib574` | `bulge_disk.mag_model_disk_sc_ib574` | HDU 1 [B+D] | scalar | 999.0 | 308,050 | 784,016 | 0.39291289973674004 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0632:0890:bulge_disk.mag_model_disk_sc_ib709 -->
| `0890:bulge_disk.mag_model_disk_sc_ib709` | `bulge_disk.mag_model_disk_sc_ib709` | HDU 1 [B+D] | scalar | 999.0 | 262,191 | 784,016 | 0.33442047101079569 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0633:0891:bulge_disk.mag_model_disk_sc_ib827 -->
| `0891:bulge_disk.mag_model_disk_sc_ib827` | `bulge_disk.mag_model_disk_sc_ib827` | HDU 1 [B+D] | scalar | 999.0 | 282,511 | 784,016 | 0.3603383094222567 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0634:0892:bulge_disk.mag_model_disk_sc_nb711 -->
| `0892:bulge_disk.mag_model_disk_sc_nb711` | `bulge_disk.mag_model_disk_sc_nb711` | HDU 1 [B+D] | scalar | 999.0 | 227,237 | 784,016 | 0.28983719720005713 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0635:0893:bulge_disk.mag_model_disk_sc_nb816 -->
| `0893:bulge_disk.mag_model_disk_sc_nb816` | `bulge_disk.mag_model_disk_sc_nb816` | HDU 1 [B+D] | scalar | 999.0 | 294,494 | 784,016 | 0.37562243627681069 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0636:0894:bulge_disk.mag_err_model_disk_hst_f814w -->
| `0894:bulge_disk.mag_err_model_disk_hst_f814w` | `bulge_disk.mag_err_model_disk_hst_f814w` | HDU 1 [B+D] | scalar | -999.0 | 44,926 | 784,016 | 0.057302401991796086 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0637:0895:bulge_disk.mag_err_model_disk_f770w -->
| `0895:bulge_disk.mag_err_model_disk_f770w` | `bulge_disk.mag_err_model_disk_f770w` | HDU 1 [B+D] | scalar | -999.0 | 62,160 | 784,016 | 0.079284096242933824 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0638:0896:bulge_disk.mag_err_model_disk_cfht_u -->
| `0896:bulge_disk.mag_err_model_disk_cfht_u` | `bulge_disk.mag_err_model_disk_cfht_u` | HDU 1 [B+D] | scalar | -999.0 | 137,639 | 784,016 | 0.17555636619660822 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0639:0897:bulge_disk.mag_err_model_disk_hsc_g -->
| `0897:bulge_disk.mag_err_model_disk_hsc_g` | `bulge_disk.mag_err_model_disk_hsc_g` | HDU 1 [B+D] | scalar | -999.0 | 105,821 | 784,016 | 0.13497301075488255 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0640:0898:bulge_disk.mag_err_model_disk_hsc_r -->
| `0898:bulge_disk.mag_err_model_disk_hsc_r` | `bulge_disk.mag_err_model_disk_hsc_r` | HDU 1 [B+D] | scalar | -999.0 | 94,238 | 784,016 | 0.12019907756984552 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0641:0899:bulge_disk.mag_err_model_disk_hsc_i -->
| `0899:bulge_disk.mag_err_model_disk_hsc_i` | `bulge_disk.mag_err_model_disk_hsc_i` | HDU 1 [B+D] | scalar | -999.0 | 75,687 | 784,016 | 0.096537570661823224 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0642:0900:bulge_disk.mag_err_model_disk_hsc_z -->
| `0900:bulge_disk.mag_err_model_disk_hsc_z` | `bulge_disk.mag_err_model_disk_hsc_z` | HDU 1 [B+D] | scalar | -999.0 | 80,861 | 784,016 | 0.10313692577702496 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0643:0901:bulge_disk.mag_err_model_disk_hsc_y -->
| `0901:bulge_disk.mag_err_model_disk_hsc_y` | `bulge_disk.mag_err_model_disk_hsc_y` | HDU 1 [B+D] | scalar | -999.0 | 139,808 | 784,016 | 0.17832289136956389 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0644:0902:bulge_disk.mag_err_model_disk_hsc_nb0816 -->
| `0902:bulge_disk.mag_err_model_disk_hsc_nb0816` | `bulge_disk.mag_err_model_disk_hsc_nb0816` | HDU 1 [B+D] | scalar | -999.0 | 150,990 | 784,016 | 0.19258535540091018 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0645:0903:bulge_disk.mag_err_model_disk_hsc_nb0921 -->
| `0903:bulge_disk.mag_err_model_disk_hsc_nb0921` | `bulge_disk.mag_err_model_disk_hsc_nb0921` | HDU 1 [B+D] | scalar | -999.0 | 133,147 | 784,016 | 0.16982689128793291 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0646:0904:bulge_disk.mag_err_model_disk_hsc_nb1010 -->
| `0904:bulge_disk.mag_err_model_disk_hsc_nb1010` | `bulge_disk.mag_err_model_disk_hsc_nb1010` | HDU 1 [B+D] | scalar | -999.0 | 262,888 | 784,016 | 0.335309483479929 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0647:0905:bulge_disk.mag_err_model_disk_uvista_y -->
| `0905:bulge_disk.mag_err_model_disk_uvista_y` | `bulge_disk.mag_err_model_disk_uvista_y` | HDU 1 [B+D] | scalar | -999.0 | 97,657 | 784,016 | 0.12455995796004163 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0648:0906:bulge_disk.mag_err_model_disk_uvista_j -->
| `0906:bulge_disk.mag_err_model_disk_uvista_j` | `bulge_disk.mag_err_model_disk_uvista_j` | HDU 1 [B+D] | scalar | -999.0 | 90,464 | 784,016 | 0.11538540029795311 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0649:0907:bulge_disk.mag_err_model_disk_uvista_h -->
| `0907:bulge_disk.mag_err_model_disk_uvista_h` | `bulge_disk.mag_err_model_disk_uvista_h` | HDU 1 [B+D] | scalar | -999.0 | 96,984 | 784,016 | 0.12370155711107937 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0650:0908:bulge_disk.mag_err_model_disk_uvista_ks -->
| `0908:bulge_disk.mag_err_model_disk_uvista_ks` | `bulge_disk.mag_err_model_disk_uvista_ks` | HDU 1 [B+D] | scalar | -999.0 | 111,697 | 784,016 | 0.14246775576008652 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0651:0909:bulge_disk.mag_err_model_disk_sc_ia484 -->
| `0909:bulge_disk.mag_err_model_disk_sc_ia484` | `bulge_disk.mag_err_model_disk_sc_ia484` | HDU 1 [B+D] | scalar | -999.0 | 126,757 | 784,016 | 0.16167654741739965 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0652:0910:bulge_disk.mag_err_model_disk_sc_ia527 -->
| `0910:bulge_disk.mag_err_model_disk_sc_ia527` | `bulge_disk.mag_err_model_disk_sc_ia527` | HDU 1 [B+D] | scalar | -999.0 | 132,441 | 784,016 | 0.16892639946123547 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0653:0911:bulge_disk.mag_err_model_disk_sc_ia624 -->
| `0911:bulge_disk.mag_err_model_disk_sc_ia624` | `bulge_disk.mag_err_model_disk_sc_ia624` | HDU 1 [B+D] | scalar | -999.0 | 105,559 | 784,016 | 0.13463883390134895 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0654:0912:bulge_disk.mag_err_model_disk_sc_ia679 -->
| `0912:bulge_disk.mag_err_model_disk_sc_ia679` | `bulge_disk.mag_err_model_disk_sc_ia679` | HDU 1 [B+D] | scalar | -999.0 | 242,153 | 784,016 | 0.30886231913634415 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0655:0913:bulge_disk.mag_err_model_disk_sc_ia738 -->
| `0913:bulge_disk.mag_err_model_disk_sc_ia738` | `bulge_disk.mag_err_model_disk_sc_ia738` | HDU 1 [B+D] | scalar | -999.0 | 111,381 | 784,016 | 0.14206470276116814 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0656:0914:bulge_disk.mag_err_model_disk_sc_ia767 -->
| `0914:bulge_disk.mag_err_model_disk_sc_ia767` | `bulge_disk.mag_err_model_disk_sc_ia767` | HDU 1 [B+D] | scalar | -999.0 | 215,088 | 784,016 | 0.27434133997265364 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0657:0915:bulge_disk.mag_err_model_disk_sc_ib427 -->
| `0915:bulge_disk.mag_err_model_disk_sc_ib427` | `bulge_disk.mag_err_model_disk_sc_ib427` | HDU 1 [B+D] | scalar | -999.0 | 235,991 | 784,016 | 0.30100278565743555 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0658:0916:bulge_disk.mag_err_model_disk_sc_ib505 -->
| `0916:bulge_disk.mag_err_model_disk_sc_ib505` | `bulge_disk.mag_err_model_disk_sc_ib505` | HDU 1 [B+D] | scalar | -999.0 | 172,281 | 784,016 | 0.21974168894512358 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0659:0917:bulge_disk.mag_err_model_disk_sc_ib574 -->
| `0917:bulge_disk.mag_err_model_disk_sc_ib574` | `bulge_disk.mag_err_model_disk_sc_ib574` | HDU 1 [B+D] | scalar | -999.0 | 250,150 | 784,016 | 0.31906236607416177 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0660:0918:bulge_disk.mag_err_model_disk_sc_ib709 -->
| `0918:bulge_disk.mag_err_model_disk_sc_ib709` | `bulge_disk.mag_err_model_disk_sc_ib709` | HDU 1 [B+D] | scalar | -999.0 | 189,132 | 784,016 | 0.24123487275769881 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0661:0919:bulge_disk.mag_err_model_disk_sc_ib827 -->
| `0919:bulge_disk.mag_err_model_disk_sc_ib827` | `bulge_disk.mag_err_model_disk_sc_ib827` | HDU 1 [B+D] | scalar | -999.0 | 222,636 | 784,016 | 0.28396869451643841 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0662:0920:bulge_disk.mag_err_model_disk_sc_nb711 -->
| `0920:bulge_disk.mag_err_model_disk_sc_nb711` | `bulge_disk.mag_err_model_disk_sc_nb711` | HDU 1 [B+D] | scalar | -999.0 | 96,582 | 784,016 | 0.12318881247321484 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0663:0921:bulge_disk.mag_err_model_disk_sc_nb816 -->
| `0921:bulge_disk.mag_err_model_disk_sc_nb816` | `bulge_disk.mag_err_model_disk_sc_nb816` | HDU 1 [B+D] | scalar | -999.0 | 242,816 | 784,016 | 0.30970796514356852 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0664:0952:bulge_disk.flux_err_model_bd_total_cfht_u -->
| `0952:bulge_disk.flux_err_model_bd_total_cfht_u` | `bulge_disk.flux_err_model_bd_total_cfht_u` | HDU 1 [B+D] | scalar | -999.0 | 2,091 | 784,016 | 0.0026670374073998488 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0665:0953:bulge_disk.flux_err_model_bd_total_hsc_g -->
| `0953:bulge_disk.flux_err_model_bd_total_hsc_g` | `bulge_disk.flux_err_model_bd_total_hsc_g` | HDU 1 [B+D] | scalar | -999.0 | 2,139 | 784,016 | 0.0027282606477418828 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0666:0954:bulge_disk.flux_err_model_bd_total_hsc_r -->
| `0954:bulge_disk.flux_err_model_bd_total_hsc_r` | `bulge_disk.flux_err_model_bd_total_hsc_r` | HDU 1 [B+D] | scalar | -999.0 | 1,569 | 784,016 | 0.0020012346686802312 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0667:0955:bulge_disk.flux_err_model_bd_total_hsc_i -->
| `0955:bulge_disk.flux_err_model_bd_total_hsc_i` | `bulge_disk.flux_err_model_bd_total_hsc_i` | HDU 1 [B+D] | scalar | -999.0 | 1,156 | 784,016 | 0.0014744597049039816 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0668:0956:bulge_disk.flux_err_model_bd_total_hsc_z -->
| `0956:bulge_disk.flux_err_model_bd_total_hsc_z` | `bulge_disk.flux_err_model_bd_total_hsc_z` | HDU 1 [B+D] | scalar | -999.0 | 1,117 | 784,016 | 0.001424715822126079 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0669:0957:bulge_disk.flux_err_model_bd_total_hsc_y -->
| `0957:bulge_disk.flux_err_model_bd_total_hsc_y` | `bulge_disk.flux_err_model_bd_total_hsc_y` | HDU 1 [B+D] | scalar | -999.0 | 1,828 | 784,016 | 0.0023315850696924551 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0670:0958:bulge_disk.flux_err_model_bd_total_hsc_nb0816 -->
| `0958:bulge_disk.flux_err_model_bd_total_hsc_nb0816` | `bulge_disk.flux_err_model_bd_total_hsc_nb0816` | HDU 1 [B+D] | scalar | -999.0 | 1,613 | 784,016 | 0.0020573559723270954 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0671:0959:bulge_disk.flux_err_model_bd_total_hsc_nb0921 -->
| `0959:bulge_disk.flux_err_model_bd_total_hsc_nb0921` | `bulge_disk.flux_err_model_bd_total_hsc_nb0921` | HDU 1 [B+D] | scalar | -999.0 | 1,484 | 784,016 | 0.0018928185139078795 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0672:0960:bulge_disk.flux_err_model_bd_total_hsc_nb1010 -->
| `0960:bulge_disk.flux_err_model_bd_total_hsc_nb1010` | `bulge_disk.flux_err_model_bd_total_hsc_nb1010` | HDU 1 [B+D] | scalar | -999.0 | 2,340 | 784,016 | 0.0029846329666741497 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0673:0961:bulge_disk.flux_err_model_bd_total_uvista_y -->
| `0961:bulge_disk.flux_err_model_bd_total_uvista_y` | `bulge_disk.flux_err_model_bd_total_uvista_y` | HDU 1 [B+D] | scalar | -999.0 | 1,464 | 784,016 | 0.001867308830432032 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0674:0962:bulge_disk.flux_err_model_bd_total_uvista_j -->
| `0962:bulge_disk.flux_err_model_bd_total_uvista_j` | `bulge_disk.flux_err_model_bd_total_uvista_j` | HDU 1 [B+D] | scalar | -999.0 | 1,190 | 784,016 | 0.0015178261668129221 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0675:0963:bulge_disk.flux_err_model_bd_total_uvista_h -->
| `0963:bulge_disk.flux_err_model_bd_total_uvista_h` | `bulge_disk.flux_err_model_bd_total_uvista_h` | HDU 1 [B+D] | scalar | -999.0 | 1,143 | 784,016 | 0.0014578784106446807 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0676:0964:bulge_disk.flux_err_model_bd_total_uvista_ks -->
| `0964:bulge_disk.flux_err_model_bd_total_uvista_ks` | `bulge_disk.flux_err_model_bd_total_uvista_ks` | HDU 1 [B+D] | scalar | -999.0 | 1,271 | 784,016 | 0.0016211403848901042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0677:0965:bulge_disk.flux_err_model_bd_total_sc_ia484 -->
| `0965:bulge_disk.flux_err_model_bd_total_sc_ia484` | `bulge_disk.flux_err_model_bd_total_sc_ia484` | HDU 1 [B+D] | scalar | -999.0 | 2,029 | 784,016 | 0.0025879573886247219 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0678:0966:bulge_disk.flux_err_model_bd_total_sc_ia527 -->
| `0966:bulge_disk.flux_err_model_bd_total_sc_ia527` | `bulge_disk.flux_err_model_bd_total_sc_ia527` | HDU 1 [B+D] | scalar | -999.0 | 1,605 | 784,016 | 0.0020471520989367564 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0679:0967:bulge_disk.flux_err_model_bd_total_sc_ia624 -->
| `0967:bulge_disk.flux_err_model_bd_total_sc_ia624` | `bulge_disk.flux_err_model_bd_total_sc_ia624` | HDU 1 [B+D] | scalar | -999.0 | 1,246 | 784,016 | 0.001589253280545295 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0680:0968:bulge_disk.flux_err_model_bd_total_sc_ia679 -->
| `0968:bulge_disk.flux_err_model_bd_total_sc_ia679` | `bulge_disk.flux_err_model_bd_total_sc_ia679` | HDU 1 [B+D] | scalar | -999.0 | 1,691 | 784,016 | 0.0021568437378829005 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0681:0970:bulge_disk.flux_err_model_bd_total_sc_ia767 -->
| `0970:bulge_disk.flux_err_model_bd_total_sc_ia767` | `bulge_disk.flux_err_model_bd_total_sc_ia767` | HDU 1 [B+D] | scalar | -999.0 | 1,151 | 784,016 | 0.0014680822840350198 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0682:0971:bulge_disk.flux_err_model_bd_total_sc_ib427 -->
| `0971:bulge_disk.flux_err_model_bd_total_sc_ib427` | `bulge_disk.flux_err_model_bd_total_sc_ib427` | HDU 1 [B+D] | scalar | -999.0 | 1,316 | 784,016 | 0.001678537172710761 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0683:1006:bulge_disk.flux_err_model_bulge_hst_f814w -->
| `1006:bulge_disk.flux_err_model_bulge_hst_f814w` | `bulge_disk.flux_err_model_bulge_hst_f814w` | HDU 1 [B+D] | scalar | -999.0 | 7,383 | 784,016 | 0.0094168996551090792 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0684:1007:bulge_disk.flux_err_model_bulge_f770w -->
| `1007:bulge_disk.flux_err_model_bulge_f770w` | `bulge_disk.flux_err_model_bulge_f770w` | HDU 1 [B+D] | scalar | -999.0 | 4,694 | 784,016 | 0.0059871227117813926 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0685:1008:bulge_disk.flux_err_model_bulge_cfht_u -->
| `1008:bulge_disk.flux_err_model_bulge_cfht_u` | `bulge_disk.flux_err_model_bulge_cfht_u` | HDU 1 [B+D] | scalar | -999.0 | 12,137 | 784,016 | 0.015480551417318014 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0686:1009:bulge_disk.flux_err_model_bulge_hsc_g -->
| `1009:bulge_disk.flux_err_model_bulge_hsc_g` | `bulge_disk.flux_err_model_bulge_hsc_g` | HDU 1 [B+D] | scalar | -999.0 | 12,927 | 784,016 | 0.016488183914613989 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0687:1010:bulge_disk.flux_err_model_bulge_hsc_r -->
| `1010:bulge_disk.flux_err_model_bulge_hsc_r` | `bulge_disk.flux_err_model_bulge_hsc_r` | HDU 1 [B+D] | scalar | -999.0 | 9,409 | 784,016 | 0.012001030591212424 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0688:1011:bulge_disk.flux_err_model_bulge_hsc_i -->
| `1011:bulge_disk.flux_err_model_bulge_hsc_i` | `bulge_disk.flux_err_model_bulge_hsc_i` | HDU 1 [B+D] | scalar | -999.0 | 8,583 | 784,016 | 0.010947480663659925 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0689:1012:bulge_disk.flux_err_model_bulge_hsc_z -->
| `1012:bulge_disk.flux_err_model_bulge_hsc_z` | `bulge_disk.flux_err_model_bulge_hsc_z` | HDU 1 [B+D] | scalar | -999.0 | 5,534 | 784,016 | 0.0070585294177669842 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0690:1013:bulge_disk.flux_err_model_bulge_hsc_y -->
| `1013:bulge_disk.flux_err_model_bulge_hsc_y` | `bulge_disk.flux_err_model_bulge_hsc_y` | HDU 1 [B+D] | scalar | -999.0 | 4,537 | 784,016 | 0.0057868716964959901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0691:1014:bulge_disk.flux_err_model_bulge_hsc_nb0816 -->
| `1014:bulge_disk.flux_err_model_bulge_hsc_nb0816` | `bulge_disk.flux_err_model_bulge_hsc_nb0816` | HDU 1 [B+D] | scalar | -999.0 | 4,287 | 784,016 | 0.0054680006530478968 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0692:1015:bulge_disk.flux_err_model_bulge_hsc_nb0921 -->
| `1015:bulge_disk.flux_err_model_bulge_hsc_nb0921` | `bulge_disk.flux_err_model_bulge_hsc_nb0921` | HDU 1 [B+D] | scalar | -999.0 | 3,715 | 784,016 | 0.0047384237056386606 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0693:1016:bulge_disk.flux_err_model_bulge_hsc_nb1010 -->
| `1016:bulge_disk.flux_err_model_bulge_hsc_nb1010` | `bulge_disk.flux_err_model_bulge_hsc_nb1010` | HDU 1 [B+D] | scalar | -999.0 | 3,264 | 784,016 | 0.004163180343258301 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0694:1017:bulge_disk.flux_err_model_bulge_uvista_y -->
| `1017:bulge_disk.flux_err_model_bulge_uvista_y` | `bulge_disk.flux_err_model_bulge_uvista_y` | HDU 1 [B+D] | scalar | -999.0 | 11,582 | 784,016 | 0.014772657700863247 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0695:1018:bulge_disk.flux_err_model_bulge_uvista_j -->
| `1018:bulge_disk.flux_err_model_bulge_uvista_j` | `bulge_disk.flux_err_model_bulge_uvista_j` | HDU 1 [B+D] | scalar | -999.0 | 9,550 | 784,016 | 0.012180873859717148 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0696:1019:bulge_disk.flux_err_model_bulge_uvista_h -->
| `1019:bulge_disk.flux_err_model_bulge_uvista_h` | `bulge_disk.flux_err_model_bulge_uvista_h` | HDU 1 [B+D] | scalar | -999.0 | 8,473 | 784,016 | 0.010807177404542765 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0697:1020:bulge_disk.flux_err_model_bulge_uvista_ks -->
| `1020:bulge_disk.flux_err_model_bulge_uvista_ks` | `bulge_disk.flux_err_model_bulge_uvista_ks` | HDU 1 [B+D] | scalar | -999.0 | 6,941 | 784,016 | 0.0088531356502928506 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0698:1021:bulge_disk.flux_err_model_bulge_sc_ia484 -->
| `1021:bulge_disk.flux_err_model_bulge_sc_ia484` | `bulge_disk.flux_err_model_bulge_sc_ia484` | HDU 1 [B+D] | scalar | -999.0 | 8,204 | 784,016 | 0.010464072161792617 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0699:1022:bulge_disk.flux_err_model_bulge_sc_ia527 -->
| `1022:bulge_disk.flux_err_model_bulge_sc_ia527` | `bulge_disk.flux_err_model_bulge_sc_ia527` | HDU 1 [B+D] | scalar | -999.0 | 7,925 | 784,016 | 0.010108212077304545 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0700:1023:bulge_disk.flux_err_model_bulge_sc_ia624 -->
| `1023:bulge_disk.flux_err_model_bulge_sc_ia624` | `bulge_disk.flux_err_model_bulge_sc_ia624` | HDU 1 [B+D] | scalar | -999.0 | 7,477 | 784,016 | 0.0095367951674455616 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0701:1024:bulge_disk.flux_err_model_bulge_sc_ia679 -->
| `1024:bulge_disk.flux_err_model_bulge_sc_ia679` | `bulge_disk.flux_err_model_bulge_sc_ia679` | HDU 1 [B+D] | scalar | -999.0 | 3,129 | 784,016 | 0.0039909899797963303 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0702:1025:bulge_disk.flux_err_model_bulge_sc_ia738 -->
| `1025:bulge_disk.flux_err_model_bulge_sc_ia738` | `bulge_disk.flux_err_model_bulge_sc_ia738` | HDU 1 [B+D] | scalar | -999.0 | 4,760 | 784,016 | 0.0060713046672516884 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0703:1026:bulge_disk.flux_err_model_bulge_sc_ia767 -->
| `1026:bulge_disk.flux_err_model_bulge_sc_ia767` | `bulge_disk.flux_err_model_bulge_sc_ia767` | HDU 1 [B+D] | scalar | -999.0 | 2,352 | 784,016 | 0.0029999387767596581 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0704:1027:bulge_disk.flux_err_model_bulge_sc_ib427 -->
| `1027:bulge_disk.flux_err_model_bulge_sc_ib427` | `bulge_disk.flux_err_model_bulge_sc_ib427` | HDU 1 [B+D] | scalar | -999.0 | 3,148 | 784,016 | 0.0040152241790983858 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0705:1028:bulge_disk.flux_err_model_bulge_sc_ib505 -->
| `1028:bulge_disk.flux_err_model_bulge_sc_ib505` | `bulge_disk.flux_err_model_bulge_sc_ib505` | HDU 1 [B+D] | scalar | -999.0 | 2,554 | 784,016 | 0.0032575865798657169 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0706:1029:bulge_disk.flux_err_model_bulge_sc_ib574 -->
| `1029:bulge_disk.flux_err_model_bulge_sc_ib574` | `bulge_disk.flux_err_model_bulge_sc_ib574` | HDU 1 [B+D] | scalar | -999.0 | 1,629 | 784,016 | 0.0020777637191077732 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0707:1062:bulge_disk.flux_err_model_disk_hst_f814w -->
| `1062:bulge_disk.flux_err_model_disk_hst_f814w` | `bulge_disk.flux_err_model_disk_hst_f814w` | HDU 1 [B+D] | scalar | -999.0 | 7,383 | 784,016 | 0.0094168996551090792 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0708:1063:bulge_disk.flux_err_model_disk_f770w -->
| `1063:bulge_disk.flux_err_model_disk_f770w` | `bulge_disk.flux_err_model_disk_f770w` | HDU 1 [B+D] | scalar | -999.0 | 4,694 | 784,016 | 0.0059871227117813926 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0709:1064:bulge_disk.flux_err_model_disk_cfht_u -->
| `1064:bulge_disk.flux_err_model_disk_cfht_u` | `bulge_disk.flux_err_model_disk_cfht_u` | HDU 1 [B+D] | scalar | -999.0 | 12,137 | 784,016 | 0.015480551417318014 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0710:1065:bulge_disk.flux_err_model_disk_hsc_g -->
| `1065:bulge_disk.flux_err_model_disk_hsc_g` | `bulge_disk.flux_err_model_disk_hsc_g` | HDU 1 [B+D] | scalar | -999.0 | 12,927 | 784,016 | 0.016488183914613989 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0711:1066:bulge_disk.flux_err_model_disk_hsc_r -->
| `1066:bulge_disk.flux_err_model_disk_hsc_r` | `bulge_disk.flux_err_model_disk_hsc_r` | HDU 1 [B+D] | scalar | -999.0 | 9,409 | 784,016 | 0.012001030591212424 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0712:1067:bulge_disk.flux_err_model_disk_hsc_i -->
| `1067:bulge_disk.flux_err_model_disk_hsc_i` | `bulge_disk.flux_err_model_disk_hsc_i` | HDU 1 [B+D] | scalar | -999.0 | 8,583 | 784,016 | 0.010947480663659925 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0713:1068:bulge_disk.flux_err_model_disk_hsc_z -->
| `1068:bulge_disk.flux_err_model_disk_hsc_z` | `bulge_disk.flux_err_model_disk_hsc_z` | HDU 1 [B+D] | scalar | -999.0 | 5,534 | 784,016 | 0.0070585294177669842 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0714:1069:bulge_disk.flux_err_model_disk_hsc_y -->
| `1069:bulge_disk.flux_err_model_disk_hsc_y` | `bulge_disk.flux_err_model_disk_hsc_y` | HDU 1 [B+D] | scalar | -999.0 | 4,537 | 784,016 | 0.0057868716964959901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0715:1070:bulge_disk.flux_err_model_disk_hsc_nb0816 -->
| `1070:bulge_disk.flux_err_model_disk_hsc_nb0816` | `bulge_disk.flux_err_model_disk_hsc_nb0816` | HDU 1 [B+D] | scalar | -999.0 | 4,287 | 784,016 | 0.0054680006530478968 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0716:1071:bulge_disk.flux_err_model_disk_hsc_nb0921 -->
| `1071:bulge_disk.flux_err_model_disk_hsc_nb0921` | `bulge_disk.flux_err_model_disk_hsc_nb0921` | HDU 1 [B+D] | scalar | -999.0 | 3,715 | 784,016 | 0.0047384237056386606 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0717:1072:bulge_disk.flux_err_model_disk_hsc_nb1010 -->
| `1072:bulge_disk.flux_err_model_disk_hsc_nb1010` | `bulge_disk.flux_err_model_disk_hsc_nb1010` | HDU 1 [B+D] | scalar | -999.0 | 3,264 | 784,016 | 0.004163180343258301 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0718:1073:bulge_disk.flux_err_model_disk_uvista_y -->
| `1073:bulge_disk.flux_err_model_disk_uvista_y` | `bulge_disk.flux_err_model_disk_uvista_y` | HDU 1 [B+D] | scalar | -999.0 | 11,582 | 784,016 | 0.014772657700863247 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0719:1074:bulge_disk.flux_err_model_disk_uvista_j -->
| `1074:bulge_disk.flux_err_model_disk_uvista_j` | `bulge_disk.flux_err_model_disk_uvista_j` | HDU 1 [B+D] | scalar | -999.0 | 9,550 | 784,016 | 0.012180873859717148 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0720:1075:bulge_disk.flux_err_model_disk_uvista_h -->
| `1075:bulge_disk.flux_err_model_disk_uvista_h` | `bulge_disk.flux_err_model_disk_uvista_h` | HDU 1 [B+D] | scalar | -999.0 | 8,473 | 784,016 | 0.010807177404542765 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0721:1076:bulge_disk.flux_err_model_disk_uvista_ks -->
| `1076:bulge_disk.flux_err_model_disk_uvista_ks` | `bulge_disk.flux_err_model_disk_uvista_ks` | HDU 1 [B+D] | scalar | -999.0 | 6,941 | 784,016 | 0.0088531356502928506 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0722:1077:bulge_disk.flux_err_model_disk_sc_ia484 -->
| `1077:bulge_disk.flux_err_model_disk_sc_ia484` | `bulge_disk.flux_err_model_disk_sc_ia484` | HDU 1 [B+D] | scalar | -999.0 | 8,204 | 784,016 | 0.010464072161792617 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0723:1078:bulge_disk.flux_err_model_disk_sc_ia527 -->
| `1078:bulge_disk.flux_err_model_disk_sc_ia527` | `bulge_disk.flux_err_model_disk_sc_ia527` | HDU 1 [B+D] | scalar | -999.0 | 7,925 | 784,016 | 0.010108212077304545 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0724:1079:bulge_disk.flux_err_model_disk_sc_ia624 -->
| `1079:bulge_disk.flux_err_model_disk_sc_ia624` | `bulge_disk.flux_err_model_disk_sc_ia624` | HDU 1 [B+D] | scalar | -999.0 | 7,477 | 784,016 | 0.0095367951674455616 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0725:1080:bulge_disk.flux_err_model_disk_sc_ia679 -->
| `1080:bulge_disk.flux_err_model_disk_sc_ia679` | `bulge_disk.flux_err_model_disk_sc_ia679` | HDU 1 [B+D] | scalar | -999.0 | 3,129 | 784,016 | 0.0039909899797963303 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0726:1081:bulge_disk.flux_err_model_disk_sc_ia738 -->
| `1081:bulge_disk.flux_err_model_disk_sc_ia738` | `bulge_disk.flux_err_model_disk_sc_ia738` | HDU 1 [B+D] | scalar | -999.0 | 4,760 | 784,016 | 0.0060713046672516884 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0727:1082:bulge_disk.flux_err_model_disk_sc_ia767 -->
| `1082:bulge_disk.flux_err_model_disk_sc_ia767` | `bulge_disk.flux_err_model_disk_sc_ia767` | HDU 1 [B+D] | scalar | -999.0 | 2,352 | 784,016 | 0.0029999387767596581 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0728:1083:bulge_disk.flux_err_model_disk_sc_ib427 -->
| `1083:bulge_disk.flux_err_model_disk_sc_ib427` | `bulge_disk.flux_err_model_disk_sc_ib427` | HDU 1 [B+D] | scalar | -999.0 | 3,148 | 784,016 | 0.0040152241790983858 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0729:1084:bulge_disk.flux_err_model_disk_sc_ib505 -->
| `1084:bulge_disk.flux_err_model_disk_sc_ib505` | `bulge_disk.flux_err_model_disk_sc_ib505` | HDU 1 [B+D] | scalar | -999.0 | 2,554 | 784,016 | 0.0032575865798657169 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0730:1085:bulge_disk.flux_err_model_disk_sc_ib574 -->
| `1085:bulge_disk.flux_err_model_disk_sc_ib574` | `bulge_disk.flux_err_model_disk_sc_ib574` | HDU 1 [B+D] | scalar | -999.0 | 1,629 | 784,016 | 0.0020777637191077732 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0731:1191:galight_morph.asymmetry_f115w -->
| `1191:galight_morph.asymmetry_f115w` | `galight_morph.asymmetry_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 9,459 | 784,016 | 0.012064804799902042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0732:1191:galight_morph.asymmetry_f115w -->
| `1191:galight_morph.asymmetry_f115w` | `galight_morph.asymmetry_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 25,153 | 784,016 | 0.032082253423399522 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0733:1192:galight_morph.smoothness_f115w -->
| `1192:galight_morph.smoothness_f115w` | `galight_morph.smoothness_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 9,459 | 784,016 | 0.012064804799902042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0734:1192:galight_morph.smoothness_f115w -->
| `1192:galight_morph.smoothness_f115w` | `galight_morph.smoothness_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 73,053 | 784,016 | 0.093177945348054125 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0735:1193:galight_morph.concentration_f115w -->
| `1193:galight_morph.concentration_f115w` | `galight_morph.concentration_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 9,459 | 784,016 | 0.012064804799902042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0736:1193:galight_morph.concentration_f115w -->
| `1193:galight_morph.concentration_f115w` | `galight_morph.concentration_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 25,153 | 784,016 | 0.032082253423399522 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0737:1194:galight_morph.gini_f115w -->
| `1194:galight_morph.gini_f115w` | `galight_morph.gini_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 9,459 | 784,016 | 0.012064804799902042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0738:1194:galight_morph.gini_f115w -->
| `1194:galight_morph.gini_f115w` | `galight_morph.gini_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 29,161 | 784,016 | 0.037194393991959347 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0739:1195:galight_morph.m20_f115w -->
| `1195:galight_morph.m20_f115w` | `galight_morph.m20_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 9,459 | 784,016 | 0.012064804799902042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0740:1195:galight_morph.m20_f115w -->
| `1195:galight_morph.m20_f115w` | `galight_morph.m20_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 35,822 | 784,016 | 0.045690394073590337 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0741:1196:galight_morph.cas_flag_f115w -->
| `1196:galight_morph.cas_flag_f115w` | `galight_morph.cas_flag_f115w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 9,459 | 784,016 | 0.012064804799902042 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0742:1242:galight_morph.asymmetry_f150w -->
| `1242:galight_morph.asymmetry_f150w` | `galight_morph.asymmetry_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 8,574 | 784,016 | 0.010936001306095794 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0743:1242:galight_morph.asymmetry_f150w -->
| `1242:galight_morph.asymmetry_f150w` | `galight_morph.asymmetry_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 15,002 | 784,016 | 0.01913481357523316 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0744:1243:galight_morph.smoothness_f150w -->
| `1243:galight_morph.smoothness_f150w` | `galight_morph.smoothness_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 8,574 | 784,016 | 0.010936001306095794 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0745:1243:galight_morph.smoothness_f150w -->
| `1243:galight_morph.smoothness_f150w` | `galight_morph.smoothness_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 41,897 | 784,016 | 0.053438960429378991 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0746:1244:galight_morph.concentration_f150w -->
| `1244:galight_morph.concentration_f150w` | `galight_morph.concentration_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 8,574 | 784,016 | 0.010936001306095794 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0747:1244:galight_morph.concentration_f150w -->
| `1244:galight_morph.concentration_f150w` | `galight_morph.concentration_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 15,002 | 784,016 | 0.01913481357523316 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0748:1245:galight_morph.gini_f150w -->
| `1245:galight_morph.gini_f150w` | `galight_morph.gini_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 8,574 | 784,016 | 0.010936001306095794 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0749:1245:galight_morph.gini_f150w -->
| `1245:galight_morph.gini_f150w` | `galight_morph.gini_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 17,346 | 784,016 | 0.022124548478602478 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0750:1246:galight_morph.m20_f150w -->
| `1246:galight_morph.m20_f150w` | `galight_morph.m20_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 8,574 | 784,016 | 0.010936001306095794 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0751:1246:galight_morph.m20_f150w -->
| `1246:galight_morph.m20_f150w` | `galight_morph.m20_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 21,247 | 784,016 | 0.02710021224056652 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0752:1247:galight_morph.cas_flag_f150w -->
| `1247:galight_morph.cas_flag_f150w` | `galight_morph.cas_flag_f150w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 8,574 | 784,016 | 0.010936001306095794 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0753:1293:galight_morph.asymmetry_f277w -->
| `1293:galight_morph.asymmetry_f277w` | `galight_morph.asymmetry_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,822 | 784,016 | 0.0099768372074039314 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0754:1293:galight_morph.asymmetry_f277w -->
| `1293:galight_morph.asymmetry_f277w` | `galight_morph.asymmetry_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 18,812 | 784,016 | 0.023994408277382095 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0755:1294:galight_morph.smoothness_f277w -->
| `1294:galight_morph.smoothness_f277w` | `galight_morph.smoothness_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,822 | 784,016 | 0.0099768372074039314 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0756:1294:galight_morph.smoothness_f277w -->
| `1294:galight_morph.smoothness_f277w` | `galight_morph.smoothness_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 30,287 | 784,016 | 0.038630589171649556 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0757:1295:galight_morph.concentration_f277w -->
| `1295:galight_morph.concentration_f277w` | `galight_morph.concentration_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,822 | 784,016 | 0.0099768372074039314 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0758:1295:galight_morph.concentration_f277w -->
| `1295:galight_morph.concentration_f277w` | `galight_morph.concentration_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 18,812 | 784,016 | 0.023994408277382095 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0759:1296:galight_morph.gini_f277w -->
| `1296:galight_morph.gini_f277w` | `galight_morph.gini_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,822 | 784,016 | 0.0099768372074039314 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0760:1296:galight_morph.gini_f277w -->
| `1296:galight_morph.gini_f277w` | `galight_morph.gini_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 19,905 | 784,016 | 0.025388512479337155 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0761:1297:galight_morph.m20_f277w -->
| `1297:galight_morph.m20_f277w` | `galight_morph.m20_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,822 | 784,016 | 0.0099768372074039314 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0762:1297:galight_morph.m20_f277w -->
| `1297:galight_morph.m20_f277w` | `galight_morph.m20_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 21,474 | 784,016 | 0.027389747148017389 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0763:1298:galight_morph.cas_flag_f277w -->
| `1298:galight_morph.cas_flag_f277w` | `galight_morph.cas_flag_f277w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,822 | 784,016 | 0.0099768372074039314 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0764:1344:galight_morph.asymmetry_f444w -->
| `1344:galight_morph.asymmetry_f444w` | `galight_morph.asymmetry_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,957 | 784,016 | 0.010149027570865901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0765:1344:galight_morph.asymmetry_f444w -->
| `1344:galight_morph.asymmetry_f444w` | `galight_morph.asymmetry_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 25,821 | 784,016 | 0.032934276851492826 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0766:1345:galight_morph.smoothness_f444w -->
| `1345:galight_morph.smoothness_f444w` | `galight_morph.smoothness_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,957 | 784,016 | 0.010149027570865901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0767:1345:galight_morph.smoothness_f444w -->
| `1345:galight_morph.smoothness_f444w` | `galight_morph.smoothness_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 53,045 | 784,016 | 0.067658057998816357 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0768:1346:galight_morph.concentration_f444w -->
| `1346:galight_morph.concentration_f444w` | `galight_morph.concentration_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,957 | 784,016 | 0.010149027570865901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0769:1346:galight_morph.concentration_f444w -->
| `1346:galight_morph.concentration_f444w` | `galight_morph.concentration_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 25,821 | 784,016 | 0.032934276851492826 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0770:1347:galight_morph.gini_f444w -->
| `1347:galight_morph.gini_f444w` | `galight_morph.gini_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,957 | 784,016 | 0.010149027570865901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0771:1347:galight_morph.gini_f444w -->
| `1347:galight_morph.gini_f444w` | `galight_morph.gini_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 28,241 | 784,016 | 0.036020948552070366 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0772:1348:galight_morph.m20_f444w -->
| `1348:galight_morph.m20_f444w` | `galight_morph.m20_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,957 | 784,016 | 0.010149027570865901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0773:1348:galight_morph.m20_f444w -->
| `1348:galight_morph.m20_f444w` | `galight_morph.m20_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -99.0 | 31,690 | 784,016 | 0.040420093467480253 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0774:1349:galight_morph.cas_flag_f444w -->
| `1349:galight_morph.cas_flag_f444w` | `galight_morph.cas_flag_f444w` | HDU 1 [GALIGHT-MORPHO] | scalar | -999.0 | 7,957 | 784,016 | 0.010149027570865901 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0775:1392:specz_compilation.specz -->
| `1392:specz_compilation.specz` | `specz_compilation.specz` | HDU 1 | scalar | -99.0 | 24,781 | 261,975 | 0.094592995514839198 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0776:1398:specz_compilation.id_cos20_classic -->
| `1398:specz_compilation.id_cos20_classic` | `specz_compilation.id_cos20_classic` | HDU 1 | scalar | -999 | 131,910 | 261,975 | 0.50352132837102781 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0777:1399:specz_compilation.ra_cos20_classic -->
| `1399:specz_compilation.ra_cos20_classic` | `specz_compilation.ra_cos20_classic` | HDU 1 | scalar | -999.0 | 131,910 | 261,975 | 0.50352132837102781 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0778:1400:specz_compilation.dec_cos20_classic -->
| `1400:specz_compilation.dec_cos20_classic` | `specz_compilation.dec_cos20_classic` | HDU 1 | scalar | -999.0 | 131,910 | 261,975 | 0.50352132837102781 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0779:1401:specz_compilation.id_cos20_farmer -->
| `1401:specz_compilation.id_cos20_farmer` | `specz_compilation.id_cos20_farmer` | HDU 1 | scalar | -999 | 189,993 | 261,975 | 0.72523332379043803 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0780:1402:specz_compilation.ra_cos20_farmer -->
| `1402:specz_compilation.ra_cos20_farmer` | `specz_compilation.ra_cos20_farmer` | HDU 1 | scalar | -999.0 | 189,993 | 261,975 | 0.72523332379043803 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0781:1403:specz_compilation.dec_cos20_farmer -->
| `1403:specz_compilation.dec_cos20_farmer` | `specz_compilation.dec_cos20_farmer` | HDU 1 | scalar | -999.0 | 189,993 | 261,975 | 0.72523332379043803 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0782:1404:specz_compilation.id_cosmos25 -->
| `1404:specz_compilation.id_cosmos25` | `specz_compilation.id_cosmos25` | HDU 1 | scalar | -999 | 216,782 | 261,975 | 0.82749117282183415 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0783:1405:specz_compilation.ra_cosmos25 -->
| `1405:specz_compilation.ra_cosmos25` | `specz_compilation.ra_cosmos25` | HDU 1 | scalar | -999.0 | 216,782 | 261,975 | 0.82749117282183415 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0784:1406:specz_compilation.dec_cosmos25 -->
| `1406:specz_compilation.dec_cosmos25` | `specz_compilation.dec_cosmos25` | HDU 1 | scalar | -999.0 | 216,782 | 261,975 | 0.82749117282183415 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0785:1407:specz_compilation.id_cosmos15 -->
| `1407:specz_compilation.id_cosmos15` | `specz_compilation.id_cosmos15` | HDU 1 | scalar | -999 | 155,128 | 261,975 | 0.59214810573528009 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0786:1408:specz_compilation.ra_cosmos15 -->
| `1408:specz_compilation.ra_cosmos15` | `specz_compilation.ra_cosmos15` | HDU 1 | scalar | -999.0 | 155,128 | 261,975 | 0.59214810573528009 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0787:1409:specz_compilation.dec_cosmos15 -->
| `1409:specz_compilation.dec_cosmos15` | `specz_compilation.dec_cosmos15` | HDU 1 | scalar | -999.0 | 155,128 | 261,975 | 0.59214810573528009 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0788:1410:specz_compilation.id_cosmos09 -->
| `1410:specz_compilation.id_cosmos09` | `specz_compilation.id_cosmos09` | HDU 1 | scalar | -999 | 163,540 | 261,975 | 0.6242580398893024 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0789:1411:specz_compilation.ra_cosmos09 -->
| `1411:specz_compilation.ra_cosmos09` | `specz_compilation.ra_cosmos09` | HDU 1 | scalar | -999.0 | 163,540 | 261,975 | 0.6242580398893024 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0790:1412:specz_compilation.dec_cosmos09 -->
| `1412:specz_compilation.dec_cosmos09` | `specz_compilation.dec_cosmos09` | HDU 1 | scalar | -999.0 | 163,540 | 261,975 | 0.6242580398893024 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0791:1413:specz_compilation.photoz -->
| `1413:specz_compilation.photoz` | `specz_compilation.photoz` | HDU 1 | scalar | -999.0 | 130,904 | 261,975 | 0.49968126729649776 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0792:1413:specz_compilation.photoz -->
| `1413:specz_compilation.photoz` | `specz_compilation.photoz` | HDU 1 | scalar | -99.0 | 61,438 | 261,975 | 0.23451856093138659 | `cosmos_v11_candidate_sentinel_v1` |
<!-- candidate:0793:1414:specz_compilation.photoz_type -->
| `1414:specz_compilation.photoz_type` | `specz_compilation.photoz_type` | HDU 1 | scalar | -999 | 130,874 | 261,975 | 0.49956675255272448 | `cosmos_v11_candidate_sentinel_v1` |

### Dual-hash provenance

| Table | Rows | Load xmin | Declared SHA-256 | Observed SHA-256 | Source |
|---|---:|---:|---|---|---|
<!-- provenance:photometry_primary -->
| `photometry_primary` | 784,016 | 11273452 | `878c318e22780b73742940c7b8807f2bbbe210ead51472706bbe0f43923e618f` | `878c318e22780b73742940c7b8807f2bbbe210ead51472706bbe0f43923e618f` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L943` |
<!-- provenance:photometry_aper -->
| `photometry_aper` | 784,016 | 11273453 | `2c5326cb878c85cdf85c9e90e8bf69f4a38720187ddd8e6e4b3d210a7cd21951` | `2c5326cb878c85cdf85c9e90e8bf69f4a38720187ddd8e6e4b3d210a7cd21951` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L944` |
<!-- provenance:lephare -->
| `lephare` | 784,016 | 11273459 | `b46b0003ad0cfeef7710758d402f8b4883537b341a36223909e25e82901721ed` | `b46b0003ad0cfeef7710758d402f8b4883537b341a36223909e25e82901721ed` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L945` |
<!-- provenance:cigale -->
| `cigale` | 784,016 | 11273460 | `018f9de6e6d089f11db40f3c0a8af8e25ae14a703b76d0f22f97a469b68d58f3` | `018f9de6e6d089f11db40f3c0a8af8e25ae14a703b76d0f22f97a469b68d58f3` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L946` |
<!-- provenance:ml_morpho -->
| `ml_morpho` | 784,016 | 11273462 | `42a93b037ce0f507478749c5dba5376c87dc42ae3601b638c34e64a499d3ce66` | `42a93b037ce0f507478749c5dba5376c87dc42ae3601b638c34e64a499d3ce66` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L947` |
<!-- provenance:bulge_disk -->
| `bulge_disk` | 784,016 | 11273464 | `786da57b506920db5403b559ad4acd8b3ad374f78109281f13cffad6924225cf` | `786da57b506920db5403b559ad4acd8b3ad374f78109281f13cffad6924225cf` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L948` |
<!-- provenance:galight_morph -->
| `galight_morph` | 784,016 | 11273466 | `19007dae6114900aa483d53adf8c697ea87a5d2769704cfa07d5fa1a3925e327` | `19007dae6114900aa483d53adf8c697ea87a5d2769704cfa07d5fa1a3925e327` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L949` |
<!-- provenance:lss_overdensity -->
| `lss_overdensity` | 164,155 | 11273564 | `c8944f0250e1fc59f8905d016f10ba1da484a2a2ea30f655cd436c99aeaa4829` | `c8944f0250e1fc59f8905d016f10ba1da484a2a2ea30f655cd436c99aeaa4829` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L950` |
<!-- provenance:galaxy_groups -->
| `galaxy_groups` | 1,678 | 11273565 | `c94a9ac4078b7078961712d263ad1c97e8e031aecab60324b1a10b3ce2b5521a` | `c94a9ac4078b7078961712d263ad1c97e8e031aecab60324b1a10b3ce2b5521a` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L951` |
<!-- provenance:galaxy_group_memberships -->
| `galaxy_group_memberships` | 1,745,652 | 11273566 | `c66b3a4657d0e152314efc8328fa59fe3d9f8fc7d15badac39ecdd15211fad77` | `c66b3a4657d0e152314efc8328fa59fe3d9f8fc7d15badac39ecdd15211fad77` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L952` |
<!-- provenance:specz_compilation -->
| `specz_compilation` | 261,975 | 11273567 | `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99` | `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99` | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L953` |

### Complete spec-z quality distribution

The earlier 16-value planning count was corrected: the tracked complete distribution has 17 observed values totaling 261,975.

| Flag | Rows | Tracked source |
|---:|---:|---|
<!-- flag:-99 -->
| -99 | 67 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:-2 -->
| -2 | 1 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:-1 -->
| -1 | 1,794 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:0 -->
| 0 | 24,594 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:1 -->
| 1 | 18,526 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:2 -->
| 2 | 27,013 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:3 -->
| 3 | 7,217 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:4 -->
| 4 | 176,004 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:5 -->
| 5 | 2 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:6 -->
| 6 | 3 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:9 -->
| 9 | 2,326 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:10 -->
| 10 | 12 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:11 -->
| 11 | 17 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:12 -->
| 12 | 43 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:13 -->
| 13 | 59 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:14 -->
| 14 | 4,269 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |
<!-- flag:19 -->
| 19 | 28 | `work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md:L847-L850` |

## Questions deferred to T_A v2

<!-- finding:D13-01 -->
### D13-01: chi2_ratio

The 1 chi2_ratio policy repair remains outside ETL v2.

| Evidence | Value | Tracked source |
|---|---:|---|
| deferred policy | 1 | `/opt/agents/repos/spec/2026-08/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md:L395` |

Question: Should T_A v2 repair chi2_ratio before anomaly ranking? Yes/No.

Recommendation: Deferred to T_A v2; recommend repairing and validating the formula before ranking.

<!-- finding:D13-02 -->
### D13-02: SFR censoring

The 1 SFR censoring redesign remains outside ETL v2.

| Evidence | Value | Tracked source |
|---|---:|---|
| deferred policy | 1 | `docs/reference/unit-conventions.md:L65` |

Question: Should T_A v2 model SFR censoring explicitly rather than treating limits as detections? Yes/No.

Recommendation: Deferred to T_A v2; recommend explicit censoring-aware analysis.

<!-- finding:D13-03 -->
### D13-03: analysis-sample

The 1 analysis-sample definition remains outside ETL v2.

| Evidence | Value | Tracked source |
|---|---:|---|
| deferred policy | 1 | `/opt/agents/repos/spec/2026-08/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md:L395` |

Question: Should T_A v2 freeze a reproducible analysis-sample definition before discovery scoring? Yes/No.

Recommendation: Deferred to T_A v2; recommend a versioned, auditable sample definition.

<!-- finding:D13-04 -->
### D13-04: spec-z calibration/validation

The 1 spec-z calibration/validation allocation remains outside ETL v2.

| Evidence | Value | Tracked source |
|---|---:|---|
| deferred policy | 1 | `/opt/agents/repos/spec/2026-08/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md:L395` |

Question: Should T_A v2 allocate spec-z rows between calibration and validation before modeling? Yes/No.

Recommendation: Deferred to T_A v2; recommend a leakage-safe allocation policy.

<!-- finding:D13-05 -->
### D13-05: morphology contextual features

The 2 new morphology sources remain contextual-feature candidates outside ETL v2.

| Evidence | Value | Tracked source |
|---|---:|---|
| O1/O5 opportunities | 2 | `docs/research/science-opportunities.md:L25,L37` |

Question: Should T_A v2 use the new morphology tables as contextual features? Yes/No.

Recommendation: Deferred to T_A v2; recommend evaluating them as context before model inclusion.

## Evidence limitations

The six keyless master extensions retain the inherited cross-HDU ordinal contract; equal ordinals are not an independent object-identity proof.

The spec-z join is computed but nonmaterialized; its 24,364 matches remain 12,855 below the 37,219 prior.

Analyst checks used operator-approved admin-session authorization; direct analyst network authentication was not exercised, and direct ML01 HBA coverage remains an operator infrastructure action.

The historical v1 fingerprint remained `82fb7e09f21253f2e9b78e8232c43b737008aa4bfb44daf28640463bea82abe7` and no v1 write was recorded.

## Operator decisions

Successful verification does not fill these cells.

The governing 2-decision boundary is `/opt/agents/repos/spec/2026-08/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md:L428`.

| Decision | Generator recommendation | Operator disposition |
|---|---|---|
| MetaMCP redirect | Recommended |  |
| T_A v2 dispatch | Recommended |  |
