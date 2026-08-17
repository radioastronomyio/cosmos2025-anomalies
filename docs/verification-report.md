<!--
---
title: "COSMOS2025 ETL Verification Report"
description: "v1 ETL verification record generated 2026-04-05"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Archived"
tags:
  - type: report
  - domain: etl
---
-->

# COSMOS2025 ETL Verification Report

Generated: 2026-04-05 04:57 UTC
Runtime: 8.9s
Database: cosmos2025 on psql01 (10.25.20.8)

**Unit Reference (critical for cross-code comparison):**

| Column | Units | Space |
|--------|-------|-------|
| lephare.mass_med / mass_l68 / mass_u68 | log10(M/M_sun) | log10 |
| lephare.sfr_med / sfr_l68 / sfr_u68 | log10(SFR / M_sun yr-1) | log10 |
| lephare.ssfr_med / ssfr_l68 / ssfr_u68 | log10(sSFR / yr-1) | log10 |
| cigale.mass / mass_err | M_sun | linear |
| cigale.sfr_inst / sfr_100myr | M_sun yr-1 | linear |
| cigale.ssfr_cigale (derived) | yr-1 | linear |

Cross-code comparison formula: `delta = lephare_log10_value - LOG10(cigale_linear_value)`

**Overall: PASS** | 47 passed, 0 failed, 0 warnings, 46 info | 93 checks total

---

## Row Counts

| Status | Check | Detail |
|--------|-------|--------|
| ✅ PASS | catalog.photometry_core row count | 784,016 rows (expected 784,016) |
| ✅ PASS | catalog.lephare row count | 784,016 rows (expected 784,016) |
| ✅ PASS | catalog.cigale row count | 784,016 rows (expected 784,016) |
| ✅ PASS | catalog.morphology row count | 784,016 rows (expected 784,016) |
| ✅ PASS | catalog.lss_overdensity row count | 164,155 rows |
| ✅ PASS | catalog.galaxy_groups row count | 1,678 rows |
| ✅ PASS | catalog.galaxy_group_memberships row count | 1,745,652 rows |

## Column Counts

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | catalog.photometry_core columns | 158 columns |
| ℹ️ INFO | catalog.lephare columns | 44 columns |
| ℹ️ INFO | catalog.cigale columns | 56 columns |
| ℹ️ INFO | catalog.morphology columns | 31 columns |
| ℹ️ INFO | catalog.lss_overdensity columns | 4 columns |
| ℹ️ INFO | catalog.galaxy_groups columns | 14 columns |
| ℹ️ INFO | catalog.galaxy_group_memberships columns | 4 columns |

## Sentinel Residual Checks (should all be 0)

| Status | Check | Detail |
|--------|-------|--------|
| ✅ PASS | No residual lephare.zfinal = -99 | 0 rows with sentinel |
| ✅ PASS | No residual lephare.zfinal = -99.0 | 0 rows with sentinel |
| ✅ PASS | No residual lephare.mass_med = -999 | 0 rows with sentinel |
| ✅ PASS | No residual lephare.sfr_med = -999 | 0 rows with sentinel |
| ✅ PASS | No residual lephare.law_minchi2 = -999 | 0 rows with sentinel |
| ✅ PASS | No residual lephare.mod_minchi2_phys = -99 | 0 rows with sentinel |
| ✅ PASS | No residual cigale.mass = -999 | 0 rows with sentinel |
| ✅ PASS | No residual cigale.sfr_inst = -999 | 0 rows with sentinel |
| ✅ PASS | No residual morphology.morph_flag_f444w = 999999 | 0 rows with sentinel |
| ✅ PASS | No residual morphology.morph_flag_f150w = 999999 | 0 rows with sentinel |
| ✅ PASS | No residual photometry_core.id_specz_khostovan25 = -999 | 0 rows with sentinel |
| ✅ PASS | No residual photometry_core.mag_err_model_f444w = -999 | 0 rows with sentinel |

## NULL Distribution (converted sentinels)

| Status | Check | Detail |
|--------|-------|--------|
| ✅ PASS | lephare.zfinal IS NULL | 92,731 NULL (11.8%) |
| ✅ PASS | lephare.mass_med IS NULL | 2,361 NULL (0.3%) |
| ✅ PASS | lephare.sfr_med IS NULL | 2,361 NULL (0.3%) |
| ✅ PASS | lephare.law_minchi2 IS NULL | 5,599 NULL (0.7%) |
| ✅ PASS | cigale.mass IS NULL | 195,471 NULL (24.9%) |
| ✅ PASS | cigale.sfr_inst IS NULL | 195,471 NULL (24.9%) |
| ✅ PASS | cigale.ssfr_cigale IS NULL | 195,471 NULL (24.9%) |
| ✅ PASS | morphology.morph_flag_f444w IS NULL | 330,462 NULL (42.1%) |
| ✅ PASS | morphology.morph_flag_f150w IS NULL | 330,462 NULL (42.1%) |
| ✅ PASS | photometry_core.id_specz_khostovan25 IS NULL | 746,797 NULL (95.3%) |

## Cross-Table Join Integrity

| Status | Check | Detail |
|--------|-------|--------|
| ✅ PASS | photometry_core -> lephare join completeness | 0 IDs in photometry_core missing from lephare |
| ✅ PASS | photometry_core -> cigale join completeness | 0 IDs in photometry_core missing from cigale |
| ✅ PASS | photometry_core -> morphology join completeness | 0 IDs in photometry_core missing from morphology |
| ✅ PASS | lephare -> photometry_core (no orphans) | 0 orphan IDs in lephare |
| ✅ PASS | cigale -> photometry_core (no orphans) | 0 orphan IDs in cigale |
| ✅ PASS | morphology -> photometry_core (no orphans) | 0 orphan IDs in morphology |
| ✅ PASS | lss_overdensity -> photometry_core (no orphans) | 0 LSS IDs not in photometry_core |
| ✅ PASS | group_memberships.galid -> photometry_core | 0 membership galids not in photometry_core |
| ✅ PASS | group_memberships.group_id -> galaxy_groups | 0 membership group_ids not in galaxy_groups |

## Unit Validation (LePhare=log10, CIGALE=linear)

| Status | Check | Detail |
|--------|-------|--------|
| ✅ PASS | lephare.mass_med is log10(M/M_sun) | range=[3.02, 12.60], median=7.84 (expected ~3 to ~13) |
| ✅ PASS | lephare.sfr_med is log10(SFR/M_sun yr-1) | range=[-9.95, 4.70], median=-0.69 (expected ~ -5 to ~4) |
| ✅ PASS | lephare.ssfr_med is log10(sSFR/yr-1) | range=[-24.95, -7.30], median=-8.61 (expected ~ -14 to ~ -6) |
| ✅ PASS | cigale.mass is linear M_sun | linear range=[2.14e-11, 3.65e+14], log10 range=[-10.67, 14.56], log10 median=8.15 |
| ✅ PASS | cigale.sfr_inst is linear M_sun/yr | linear range=[4.31e-24, 9.42e+04], log10 range=[-23.37, 4.97], log10 median=-0.91 |
| ℹ️ INFO | cigale.ssfr_cigale is linear yr-1 | log10 range=[-15.65, -7.12], log10 median=-9.17 (expected ~ -14 to ~ -6) |

## Value Range Checks

| Status | Check | Detail |
|--------|-------|--------|
| ✅ PASS | RA range within COSMOS field | [149.6641, 150.5789] (expected ~[149.3, 150.8]) |
| ✅ PASS | Dec range within COSMOS field | [1.7283, 2.6899] (expected ~[1.5, 3.0]) |
| ✅ PASS | F444W morphology probs sum to ~1.0 | avg=1.0000, range=[1.0000, 1.0000] |
| ℹ️ INFO | density_excess distribution | min=0.000, max=12.596, mean=1.304, median=1.210 |
| ✅ PASS | ssfr_cigale valid count | 588,536 sources with ssfr_cigale > 0 |

## Quality Flag & Classification Distribution

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | warn_flag = 0 | 694,341 sources (88.6%) |
| ℹ️ INFO | warn_flag = 1 | 13,241 sources (1.7%) |
| ℹ️ INFO | warn_flag = 2 | 51,793 sources (6.6%) |
| ℹ️ INFO | warn_flag = 3 | 157 sources (0.0%) |
| ℹ️ INFO | warn_flag = 4 | 17,520 sources (2.2%) |
| ℹ️ INFO | warn_flag = 5 | 133 sources (0.0%) |
| ℹ️ INFO | warn_flag = 6 | 6,831 sources (0.9%) |
| ℹ️ INFO | flag_star = true | 4,410 stars (0.6%) |
| ℹ️ INFO | lephare.type = 0 (galaxy) | 760,933 sources |
| ℹ️ INFO | lephare.type = 1 (star) | 16,974 sources |
| ℹ️ INFO | lephare.type = 2 (QSO) | 6,109 sources |

## CIGALE NULL Coverage

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | CIGALE fully NULL (unfittable sources) | 195,471 sources (24.9%) |
| ℹ️ INFO | cigale.mass IS NULL | 195,471 (24.9%) |
| ℹ️ INFO | cigale.sfr_inst IS NULL | 195,471 (24.9%) |
| ℹ️ INFO | cigale.sfr_100myr IS NULL | 195,471 (24.9%) |
| ℹ️ INFO | cigale.chi2_best_fit IS NULL | 195,471 (24.9%) |

## MIRI F770W Coverage

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | F770W zero-weight (no MIRI coverage) | 517,148 sources (66.0%) |

## Cross-Code Mass/SFR Comparison (O1 Readiness)

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | Sources with valid mass from both codes | 588,026 sources |
| ℹ️ INFO | |delta log M*| percentiles (mass_med - log10(mass)) | p50=0.237, p90=0.405, p95=0.516, p99=13.250, max=22.526 |
| ℹ️ INFO | |delta log M*| > 0.3 dex (O1 mass candidates) | 178,920 sources (30.4% of dual-valid) |
| ℹ️ INFO | |delta log M*| > 0.5 dex | 31,775 sources |
| ℹ️ INFO | |delta log M*| > 1.0 dex | 10,955 sources |
| ℹ️ INFO | Sources with valid SFR from both codes | 588,017 sources |
| ℹ️ INFO | |delta log SFR| percentiles (sfr_med - log10(sfr_inst)) | p50=0.263, p90=0.879, p95=1.187, p99=10.528, max=24.205 |
| ℹ️ INFO | |delta log SFR| > 0.5 dex | 162,031 sources |
| ℹ️ INFO | |delta log SFR| > 1.0 dex | 43,165 sources |
| ℹ️ INFO | |delta log SFR| > 2.0 dex | 13,357 sources |
| ℹ️ INFO | Top 1 mass outlier (id=399409) | LP=12.29, CIG=-10.23, delta=+22.53 dex, warn_flag=0 |
| ℹ️ INFO | Top 2 mass outlier (id=601334) | LP=12.09, CIG=-10.28, delta=+22.37 dex, warn_flag=1 |
| ℹ️ INFO | Top 3 mass outlier (id=251226) | LP=10.89, CIG=-10.50, delta=+21.39 dex, warn_flag=0 |
| ℹ️ INFO | Top 4 mass outlier (id=220164) | LP=10.97, CIG=-10.34, delta=+21.31 dex, warn_flag=0 |
| ℹ️ INFO | Top 5 mass outlier (id=346041) | LP=10.69, CIG=-10.60, delta=+21.29 dex, warn_flag=0 |

## Supplementary Catalog Sanity

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | LSS overdensity coverage | 164,155 / 784,016 (20.9%) of sources have LSS data |
| ℹ️ INFO | Group redshift range | z = [0.080, 3.700], mean=1.555 (expected max ~3.7) |
| ℹ️ INFO | Avg memberships per group | 1040.3 members/group |
| ℹ️ INFO | Distinct galaxies in group memberships | 364,674 unique galaxies |

## Index Verification

| Status | Check | Detail |
|--------|-------|--------|
| ℹ️ INFO | Indexes present | 20 indexes: cigale_pkey, galaxy_group_memberships_pkey, galaxy_groups_pkey, idx_cigale_mass, idx_groups_z, idx_lephare_mass_med, idx_lephare_zfinal, idx_lss_density, idx_lss_radec, idx_memberships_galid, idx_memberships_group, idx_morph_delta_f444w, idx_morph_flag_f444w, idx_phot_flag_star, idx_phot_radec, idx_phot_warn_flag, lephare_pkey, lss_overdensity_pkey, morphology_pkey, photometry_core_pkey |

---

*Generated by `src/etl/verify_catalog.py`*