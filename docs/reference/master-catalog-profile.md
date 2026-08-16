<!--
---
title: "COSMOS-Web DR1 Master Catalog Profile (v1)"
description: "Documented v1 structural profile; historical record superseded by the v1.1 profile"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Archived"
tags:
  - type: reference
  - domain: cosmos-web
---
-->

# COSMOS-Web DR1 Master Catalog Profile

**File:** `COSMOSWeb_mastercatalog_v1.fits`
**Size:** 8.4 GB
**Extensions:** 6
**Profile time:** 11.3s
**Sample size per extension:** 50,000 rows

---

## Extension Summary

| # | Extension | Rows | Columns |
|---|-----------|------|---------|
| 1 | PHOTOMETRY HOTCOLD AND SE++ | 784,016 | 287 |
| 2 | LEPHARE | 784,016 | 43 |
| 3 | SE++APER | 784,016 | 148 |
| 4 | CIGALE | 784,016 | 54 |
| 5 | ML-MORPHO | 784,016 | 150 |
| 6 | B+D | 784,016 | 461 |

---

## Extension 1: PHOTOMETRY HOTCOLD AND SE++

**Rows:** 784,016 | **Columns:** 287

### Column Inventory

| Column | FITS Format | Type | Unit |
|--------|-------------|------|------|
| `id` | K | int64 |  |
| `segment-id` | K | int64 |  |
| `tile` | 3A | string[3] |  |
| `id_specz_khostovan25` | K | int64 |  |
| `ra` | D | float64 |  |
| `dec` | D | float64 |  |
| `x_image` | D | float64 |  |
| `y_image` | D | float64 |  |
| `a_image` | D | float64 |  |
| `b_image` | D | float64 |  |
| `theta_image` | D | float64 |  |
| `theta_world` | D | float64 |  |
| `chi2_max` | D | float64 |  |
| `mode` | 4A | string[4] |  |
| `snr_hst-f814w` | D | float64 |  |
| `wht_hst-f814w` | D | float64 |  |
| `flux_auto_hst-f814w` | D | float64 |  |
| `flux_err_auto_hst-f814w` | D | float64 |  |
| `mag_auto_hst-f814w` | D | float64 |  |
| `flux_aper_hst-f814w` | 5D | float64[5] |  |
| `flux_err_aper_hst-f814w` | 5D | float64[5] |  |
| `mag_aper_hst-f814w` | 5D | float64[5] |  |
| `snr_f115w` | D | float64 |  |
| `wht_f115w` | D | float64 |  |
| `flux_auto_f115w` | D | float64 |  |
| `flux_err_auto_f115w` | D | float64 |  |
| `mag_auto_f115w` | D | float64 |  |
| `flux_aper_f115w` | 5D | float64[5] |  |
| `flux_err_aper_f115w` | 5D | float64[5] |  |
| `mag_aper_f115w` | 5D | float64[5] |  |
| `snr_f150w` | D | float64 |  |
| `wht_f150w` | D | float64 |  |
| `flux_auto_f150w` | D | float64 |  |
| `flux_err_auto_f150w` | D | float64 |  |
| `mag_auto_f150w` | D | float64 |  |
| `flux_aper_f150w` | 5D | float64[5] |  |
| `flux_err_aper_f150w` | 5D | float64[5] |  |
| `mag_aper_f150w` | 5D | float64[5] |  |
| `snr_f277w` | D | float64 |  |
| `wht_f277w` | D | float64 |  |
| `flux_auto_f277w` | D | float64 |  |
| `flux_err_auto_f277w` | D | float64 |  |
| `mag_auto_f277w` | D | float64 |  |
| `flux_aper_f277w` | 5D | float64[5] |  |
| `flux_err_aper_f277w` | 5D | float64[5] |  |
| `mag_aper_f277w` | 5D | float64[5] |  |
| `snr_f444w` | D | float64 |  |
| `wht_f444w` | D | float64 |  |
| `flux_auto_f444w` | D | float64 |  |
| `flux_err_auto_f444w` | D | float64 |  |
| `mag_auto_f444w` | D | float64 |  |
| `flux_aper_f444w` | 5D | float64[5] |  |
| `flux_err_aper_f444w` | 5D | float64[5] |  |
| `mag_aper_f444w` | 5D | float64[5] |  |
| `snr_f770w` | D | float64 |  |
| `wht_f770w` | D | float64 |  |
| `flux_auto_f770w` | D | float64 |  |
| `flux_err_auto_f770w` | D | float64 |  |
| `mag_auto_f770w` | D | float64 |  |
| `flux_aper_f770w` | 5D | float64[5] |  |
| `flux_err_aper_f770w` | 5D | float64[5] |  |
| `mag_aper_f770w` | 5D | float64[5] |  |
| `c_f444w` | D | float64 |  |
| `fwhm` | D | float64 |  |
| `mu_max_hst-f814w` | D | float64 |  |
| `mu_max_f115w` | D | float64 |  |
| `mu_max_f150w` | D | float64 |  |
| `mu_max_f277w` | D | float64 |  |
| `mu_max_f444w` | D | float64 |  |
| `mu_max_f770w` | D | float64 |  |
| `kron_rad` | D | float64 |  |
| `kron1_a` | D | float64 |  |
| `kron1_b` | D | float64 |  |
| `kron1_area` | D | float64 |  |
| `kron2_a` | D | float64 |  |
| `kron2_b` | D | float64 |  |
| `kron2_area` | D | float64 |  |
| `seg_area` | D | float64 |  |
| `kron_corr` | D | float64 |  |
| `kron_f444w_psf_corr` | D | float64 |  |
| `kron_f770w_psf_corr` | D | float64 |  |
| `kron_f770w_ap_corr` | D | float64 |  |
| `flag_star` | L | bool |  |
| `flag_blend` | L | bool |  |
| `ra_model` | D | float64 |  |
| `dec_model` | D | float64 |  |
| `radius_sersic` | D | float64 |  |
| `radius_sersic_err` | D | float64 |  |
| `axratio_sersic` | D | float64 |  |
| `axratio_sersic_err` | D | float64 |  |
| `sersic` | D | float64 |  |
| `sersic_err` | D | float64 |  |
| `angle_sersic` | D | float64 |  |
| `angle_sersic_err` | D | float64 |  |
| `e1` | D | float64 |  |
| `e1_err` | D | float64 |  |
| `e2` | D | float64 |  |
| `e2_err` | D | float64 |  |
| `fmf_chi2` | D | float64 |  |
| `group_id` | K | int64 |  |
| `mag_model_f115w` | D | float64 |  |
| `mag_model_f150w` | D | float64 |  |
| `mag_model_f277w` | D | float64 |  |
| `mag_model_f444w` | D | float64 |  |
| `mag_model_hst-f814w` | D | float64 |  |
| `mag_model_f770w` | D | float64 |  |
| `mag_model_cfht-u` | D | float64 |  |
| `mag_model_hsc-g` | D | float64 |  |
| `mag_model_hsc-r` | D | float64 |  |
| `mag_model_hsc-i` | D | float64 |  |
| `mag_model_hsc-z` | D | float64 |  |
| `mag_model_hsc-y` | D | float64 |  |
| `mag_model_hsc-nb0816` | D | float64 |  |
| `mag_model_hsc-nb0921` | D | float64 |  |
| `mag_model_hsc-nb1010` | D | float64 |  |
| `mag_model_uvista-y` | D | float64 |  |
| `mag_model_uvista-j` | D | float64 |  |
| `mag_model_uvista-h` | D | float64 |  |
| `mag_model_uvista-ks` | D | float64 |  |
| `mag_model_uvista-nb118` | D | float64 |  |
| `mag_model_sc-ia484` | D | float64 |  |
| `mag_model_sc-ia527` | D | float64 |  |
| `mag_model_sc-ia624` | D | float64 |  |
| `mag_model_sc-ia679` | D | float64 |  |
| `mag_model_sc-ia738` | D | float64 |  |
| `mag_model_sc-ia767` | D | float64 |  |
| `mag_model_sc-ib427` | D | float64 |  |
| `mag_model_sc-ib505` | D | float64 |  |
| `mag_model_sc-ib574` | D | float64 |  |
| `mag_model_sc-ib709` | D | float64 |  |
| `mag_model_sc-ib827` | D | float64 |  |
| `mag_model_sc-nb711` | D | float64 |  |
| `mag_model_sc-nb816` | D | float64 |  |
| `mag_model_irac-ch1` | D | float64 |  |
| `mag_model_irac-ch2` | D | float64 |  |
| `mag_model_irac-ch3` | D | float64 |  |
| `mag_model_irac-ch4` | D | float64 |  |
| `mag_err_model_f115w` | D | float64 |  |
| `mag_err_model_f150w` | D | float64 |  |
| `mag_err_model_f277w` | D | float64 |  |
| `mag_err_model_f444w` | D | float64 |  |
| `mag_err_model_hst-f814w` | D | float64 |  |
| `mag_err_model_f770w` | D | float64 |  |
| `mag_err_model_cfht-u` | D | float64 |  |
| `mag_err_model_hsc-g` | D | float64 |  |
| `mag_err_model_hsc-r` | D | float64 |  |
| `mag_err_model_hsc-i` | D | float64 |  |
| `mag_err_model_hsc-z` | D | float64 |  |
| `mag_err_model_hsc-y` | D | float64 |  |
| `mag_err_model_hsc-nb0816` | D | float64 |  |
| `mag_err_model_hsc-nb0921` | D | float64 |  |
| `mag_err_model_hsc-nb1010` | D | float64 |  |
| `mag_err_model_uvista-y` | D | float64 |  |
| `mag_err_model_uvista-j` | D | float64 |  |
| `mag_err_model_uvista-h` | D | float64 |  |
| `mag_err_model_uvista-ks` | D | float64 |  |
| `mag_err_model_uvista-nb118` | D | float64 |  |
| `mag_err_model_sc-ia484` | D | float64 |  |
| `mag_err_model_sc-ia527` | D | float64 |  |
| `mag_err_model_sc-ia624` | D | float64 |  |
| `mag_err_model_sc-ia679` | D | float64 |  |
| `mag_err_model_sc-ia738` | D | float64 |  |
| `mag_err_model_sc-ia767` | D | float64 |  |
| `mag_err_model_sc-ib427` | D | float64 |  |
| `mag_err_model_sc-ib505` | D | float64 |  |
| `mag_err_model_sc-ib574` | D | float64 |  |
| `mag_err_model_sc-ib709` | D | float64 |  |
| `mag_err_model_sc-ib827` | D | float64 |  |
| `mag_err_model_sc-nb711` | D | float64 |  |
| `mag_err_model_sc-nb816` | D | float64 |  |
| `mag_err_model_irac-ch1` | D | float64 |  |
| `mag_err_model_irac-ch2` | D | float64 |  |
| `mag_err_model_irac-ch3` | D | float64 |  |
| `mag_err_model_irac-ch4` | D | float64 |  |
| `flux_model_f115w` | D | float64 |  |
| `flux_model_f150w` | D | float64 |  |
| `flux_model_f277w` | D | float64 |  |
| `flux_model_f444w` | D | float64 |  |
| `flux_model_hst-f814w` | D | float64 |  |
| `flux_model_f770w` | D | float64 |  |
| `flux_model_cfht-u` | D | float64 |  |
| `flux_model_hsc-g` | D | float64 |  |
| `flux_model_hsc-r` | D | float64 |  |
| `flux_model_hsc-i` | D | float64 |  |
| `flux_model_hsc-z` | D | float64 |  |
| `flux_model_hsc-y` | D | float64 |  |
| `flux_model_hsc-nb0816` | D | float64 |  |
| `flux_model_hsc-nb0921` | D | float64 |  |
| `flux_model_hsc-nb1010` | D | float64 |  |
| `flux_model_uvista-y` | D | float64 |  |
| `flux_model_uvista-j` | D | float64 |  |
| `flux_model_uvista-h` | D | float64 |  |
| `flux_model_uvista-ks` | D | float64 |  |
| `flux_model_uvista-nb118` | D | float64 |  |
| `flux_model_sc-ia484` | D | float64 |  |
| `flux_model_sc-ia527` | D | float64 |  |
| `flux_model_sc-ia624` | D | float64 |  |
| `flux_model_sc-ia679` | D | float64 |  |
| `flux_model_sc-ia738` | D | float64 |  |
| `flux_model_sc-ia767` | D | float64 |  |
| `flux_model_sc-ib427` | D | float64 |  |
| `flux_model_sc-ib505` | D | float64 |  |
| `flux_model_sc-ib574` | D | float64 |  |
| `flux_model_sc-ib709` | D | float64 |  |
| `flux_model_sc-ib827` | D | float64 |  |
| `flux_model_sc-nb711` | D | float64 |  |
| `flux_model_sc-nb816` | D | float64 |  |
| `flux_model_irac-ch1` | D | float64 |  |
| `flux_model_irac-ch2` | D | float64 |  |
| `flux_model_irac-ch3` | D | float64 |  |
| `flux_model_irac-ch4` | D | float64 |  |
| `flux_err-uncal_model_f115w` | D | float64 |  |
| `flux_err-uncal_model_f150w` | D | float64 |  |
| `flux_err-uncal_model_f277w` | D | float64 |  |
| `flux_err-uncal_model_f444w` | D | float64 |  |
| `flux_err-uncal_model_hst-f814w` | D | float64 |  |
| `flux_err-uncal_model_f770w` | D | float64 |  |
| `flux_err-uncal_model_cfht-u` | D | float64 |  |
| `flux_err-uncal_model_hsc-g` | D | float64 |  |
| `flux_err-uncal_model_hsc-r` | D | float64 |  |
| `flux_err-uncal_model_hsc-i` | D | float64 |  |
| `flux_err-uncal_model_hsc-z` | D | float64 |  |
| `flux_err-uncal_model_hsc-y` | D | float64 |  |
| `flux_err-uncal_model_hsc-nb0816` | D | float64 |  |
| `flux_err-uncal_model_hsc-nb0921` | D | float64 |  |
| `flux_err-uncal_model_hsc-nb1010` | D | float64 |  |
| `flux_err-uncal_model_uvista-y` | D | float64 |  |
| `flux_err-uncal_model_uvista-j` | D | float64 |  |
| `flux_err-uncal_model_uvista-h` | D | float64 |  |
| `flux_err-uncal_model_uvista-ks` | D | float64 |  |
| `flux_err-uncal_model_uvista-nb118` | D | float64 |  |
| `flux_err-uncal_model_sc-ia484` | D | float64 |  |
| `flux_err-uncal_model_sc-ia527` | D | float64 |  |
| `flux_err-uncal_model_sc-ia624` | D | float64 |  |
| `flux_err-uncal_model_sc-ia679` | D | float64 |  |
| `flux_err-uncal_model_sc-ia738` | D | float64 |  |
| `flux_err-uncal_model_sc-ia767` | D | float64 |  |
| `flux_err-uncal_model_sc-ib427` | D | float64 |  |
| `flux_err-uncal_model_sc-ib505` | D | float64 |  |
| `flux_err-uncal_model_sc-ib574` | D | float64 |  |
| `flux_err-uncal_model_sc-ib709` | D | float64 |  |
| `flux_err-uncal_model_sc-ib827` | D | float64 |  |
| `flux_err-uncal_model_sc-nb711` | D | float64 |  |
| `flux_err-uncal_model_sc-nb816` | D | float64 |  |
| `flux_err-uncal_model_irac-ch1` | D | float64 |  |
| `flux_err-uncal_model_irac-ch2` | D | float64 |  |
| `flux_err-uncal_model_irac-ch3` | D | float64 |  |
| `flux_err-uncal_model_irac-ch4` | D | float64 |  |
| `flag_star_hsc` | I | int16 |  |
| `flux_err-cal_model_f115w` | D | float64 |  |
| `flux_err-cal_model_f150w` | D | float64 |  |
| `flux_err-cal_model_f277w` | D | float64 |  |
| `flux_err-cal_model_f444w` | D | float64 |  |
| `flux_err-cal_model_hst-f814w` | D | float64 |  |
| `flux_err-cal_model_f770w` | D | float64 |  |
| `flux_err-cal_model_cfht-u` | D | float64 |  |
| `flux_err-cal_model_hsc-g` | D | float64 |  |
| `flux_err-cal_model_hsc-r` | D | float64 |  |
| `flux_err-cal_model_hsc-i` | D | float64 |  |
| `flux_err-cal_model_hsc-z` | D | float64 |  |
| `flux_err-cal_model_hsc-y` | D | float64 |  |
| `flux_err-cal_model_hsc-nb0816` | D | float64 |  |
| `flux_err-cal_model_hsc-nb0921` | D | float64 |  |
| `flux_err-cal_model_hsc-nb1010` | D | float64 |  |
| `flux_err-cal_model_uvista-y` | D | float64 |  |
| `flux_err-cal_model_uvista-j` | D | float64 |  |
| `flux_err-cal_model_uvista-h` | D | float64 |  |
| `flux_err-cal_model_uvista-ks` | D | float64 |  |
| `flux_err-cal_model_uvista-nb118` | D | float64 |  |
| `flux_err-cal_model_sc-ia484` | D | float64 |  |
| `flux_err-cal_model_sc-ia527` | D | float64 |  |
| `flux_err-cal_model_sc-ia624` | D | float64 |  |
| `flux_err-cal_model_sc-ia679` | D | float64 |  |
| `flux_err-cal_model_sc-ia738` | D | float64 |  |
| `flux_err-cal_model_sc-ia767` | D | float64 |  |
| `flux_err-cal_model_sc-ib427` | D | float64 |  |
| `flux_err-cal_model_sc-ib505` | D | float64 |  |
| `flux_err-cal_model_sc-ib574` | D | float64 |  |
| `flux_err-cal_model_sc-ib709` | D | float64 |  |
| `flux_err-cal_model_sc-ib827` | D | float64 |  |
| `flux_err-cal_model_sc-nb711` | D | float64 |  |
| `flux_err-cal_model_sc-nb816` | D | float64 |  |
| `flux_err-cal_model_irac-ch1` | D | float64 |  |
| `flux_err-cal_model_irac-ch2` | D | float64 |  |
| `flux_err-cal_model_irac-ch3` | D | float64 |  |
| `flux_err-cal_model_irac-ch4` | D | float64 |  |
| `warn_flag` | K | int64 |  |

### Sample Statistics

Based on first 50,000 of 784,016 rows.

**Array columns (multi-value per row):**

- `flux_aper_hst-f814w`: shape (5,)
- `flux_err_aper_hst-f814w`: shape (5,)
- `mag_aper_hst-f814w`: shape (5,)
- `flux_aper_f115w`: shape (5,)
- `flux_err_aper_f115w`: shape (5,)
- `mag_aper_f115w`: shape (5,)
- `flux_aper_f150w`: shape (5,)
- `flux_err_aper_f150w`: shape (5,)
- `mag_aper_f150w`: shape (5,)
- `flux_aper_f277w`: shape (5,)
- `flux_err_aper_f277w`: shape (5,)
- `mag_aper_f277w`: shape (5,)
- `flux_aper_f444w`: shape (5,)
- `flux_err_aper_f444w`: shape (5,)
- `mag_aper_f444w`: shape (5,)
- `flux_aper_f770w`: shape (5,)
- `flux_err_aper_f770w`: shape (5,)
- `mag_aper_f770w`: shape (5,)

**Columns with NaN values:**

| Column | NaN count | Inf count | Min | Max |
|--------|-----------|-----------|-----|-----|
| `mag_aper_f770w` | 166,323 (332.6%) | 0 | 17.81 | 38.94 |
| `flux_aper_f770w` | 139,325 (278.6%) | 0 | -0.5639 | 273.3 |
| `flux_err_aper_f770w` | 139,325 (278.6%) | 0 | 0.005288 | 0.1608 |
| `mag_auto_f770w` | 32,853 (65.7%) | 0 | 16.31 | 36.73 |
| `flux_auto_f770w` | 27,925 (55.9%) | 0 | -76.71 | 1087 |
| `flux_err_auto_f770w` | 27,925 (55.9%) | 0 | 0.008927 | 16.45 |
| `snr_f770w` | 27,865 (55.7%) | 0 | -16.9 | 2.237e+04 |
| `mu_max_f770w` | 27,524 (55.0%) | 0 | 15.82 | 31.26 |
| `mag_aper_hst-f814w` | 21,429 (42.9%) | 0 | 17.67 | 40.07 |
| `mag_aper_f115w` | 14,063 (28.1%) | 0 | 18.04 | 39.94 |
| `mag_aper_f444w` | 10,034 (20.1%) | 0 | 18.05 | 37.84 |
| `mag_aper_f150w` | 9,358 (18.7%) | 0 | 17.82 | 38.97 |
| `mag_aper_f277w` | 6,429 (12.9%) | 0 | 17.88 | 40.89 |
| `mag_auto_hst-f814w` | 3,287 (6.6%) | 0 | 17.33 | 38.65 |
| `mag_auto_f115w` | 1,412 (2.8%) | 0 | 16.79 | 37.69 |
| `mag_auto_f444w` | 1,373 (2.7%) | 0 | 17.28 | 36.46 |
| `mag_auto_f277w` | 976 (2.0%) | 0 | 16.87 | 37.16 |
| `mag_auto_f150w` | 824 (1.6%) | 0 | 16.58 | 35.98 |
| `flux_aper_f444w` | 420 (0.8%) | 0 | -0.07249 | 218.8 |
| `flux_err_aper_f444w` | 420 (0.8%) | 0 | 0.001821 | 0.2168 |
| `radius_sersic_err` | 306 (0.6%) | 0 | 4.767e-16 | 0.001106 |
| `axratio_sersic_err` | 306 (0.6%) | 0 | 1.476e-09 | 2.359 |
| `angle_sersic_err` | 306 (0.6%) | 0 | 4.636e-08 | 3.234e+06 |
| `kron_f770w_ap_corr` | 213 (0.4%) | 0 | -3612 | 831.4 |
| `flux_aper_hst-f814w` | 192 (0.4%) | 0 | -0.1304 | 311.2 |
| `sersic_err` | 117 (0.2%) | 0 | 0 | 10.89 |
| `c_f444w` | 89 (0.2%) | 0 | -421.2 | 2027 |
| `snr_f444w` | 84 (0.2%) | 0 | -8.403 | 2.829e+04 |
| `flux_auto_f444w` | 84 (0.2%) | 0 | -0.06588 | 445.4 |
| `flux_err_auto_f444w` | 84 (0.2%) | 0 | 0.002224 | 0.846 |
| ... | (11 more columns with NaNs) | | | |

**Columns with potential sentinel values:**

| Column | Sentinel | Count |
|--------|----------|-------|
| `id_specz_khostovan25` | -999 | 47,609 (95.2%) |
| `wht_f770w` | 0.0 | 27,512 (55.0%) |
| `mag_err_model_f115w` | -999.0 | 849 (1.7%) |
| `mag_err_model_f150w` | -999.0 | 555 (1.1%) |
| `mag_err_model_f277w` | -999.0 | 675 (1.4%) |
| `mag_err_model_f444w` | -999.0 | 951 (1.9%) |
| `mag_err_model_hst-f814w` | -999.0 | 1,969 (3.9%) |
| `mag_err_model_f770w` | -999.0 | 3,411 (6.8%) |
| `mag_err_model_cfht-u` | -999.0 | 7,556 (15.1%) |
| `mag_err_model_hsc-g` | -999.0 | 4,792 (9.6%) |
| `mag_err_model_hsc-r` | -999.0 | 4,215 (8.4%) |
| `mag_err_model_hsc-i` | -999.0 | 3,048 (6.1%) |
| `mag_err_model_hsc-z` | -999.0 | 3,730 (7.5%) |
| `mag_err_model_hsc-y` | -999.0 | 7,186 (14.4%) |
| `mag_err_model_hsc-nb0816` | -999.0 | 7,964 (15.9%) |
| `mag_err_model_hsc-nb0921` | -999.0 | 7,045 (14.1%) |
| `mag_err_model_hsc-nb1010` | -999.0 | 16,091 (32.2%) |
| `mag_err_model_uvista-y` | -999.0 | 3,402 (6.8%) |
| `mag_err_model_uvista-j` | -999.0 | 3,177 (6.4%) |
| `mag_err_model_uvista-h` | -999.0 | 3,641 (7.3%) |
| `mag_err_model_uvista-ks` | -999.0 | 4,659 (9.3%) |
| `mag_err_model_uvista-nb118` | -999.0 | 8,195 (16.4%) |
| `mag_err_model_uvista-nb118` | 0.0 | 504 (1.0%) |
| `mag_err_model_sc-ia484` | -999.0 | 7,163 (14.3%) |
| `mag_err_model_sc-ia484` | 0.0 | 562 (1.1%) |

**Low-cardinality columns (categorical/flag):**

- `tile`: [A1, A2]
- `mode`: [cold, hot]
- `flag_star_hsc`: [0, 1]
- `warn_flag`: [0, 1, 2, 3, 4, 5, 6]

---

## Extension 2: LEPHARE

**Rows:** 784,016 | **Columns:** 43

### Column Inventory

| Column | FITS Format | Type | Unit |
|--------|-------------|------|------|
| `zfinal` | D | float64 |  |
| `type` | K | int64 |  |
| `zpdf_med` | D | float64 |  |
| `zpdf_l68` | D | float64 |  |
| `zpdf_u68` | D | float64 |  |
| `zchi2` | D | float64 |  |
| `chi2_best` | D | float64 |  |
| `nbfilt` | K | int64 |  |
| `zp_agn` | D | float64 |  |
| `chi2_agn` | D | float64 |  |
| `mod_agn` | D | float64 |  |
| `mod_star` | D | float64 |  |
| `chi_star` | D | float64 |  |
| `mod_minchi2_phys` | K | int64 |  |
| `ebv_minchi2` | D | float64 |  |
| `law_minchi2` | K | int64 |  |
| `age_minchi2` | D | float64 |  |
| `mass_minchi2` | D | float64 |  |
| `sfr_minchi2` | D | float64 |  |
| `ssfr_minchi2` | D | float64 |  |
| `age_l68` | D | float64 |  |
| `age_med` | D | float64 |  |
| `age_u68` | D | float64 |  |
| `mass_l68` | D | float64 |  |
| `mass_med` | D | float64 |  |
| `mass_u68` | D | float64 |  |
| `sfr_l68` | D | float64 |  |
| `sfr_med` | D | float64 |  |
| `sfr_u68` | D | float64 |  |
| `ssfr_l68` | D | float64 |  |
| `ssfr_med` | D | float64 |  |
| `ssfr_u68` | D | float64 |  |
| `l_nuv` | D | float64 |  |
| `l_r` | D | float64 |  |
| `l_k` | D | float64 |  |
| `mabs_nuv` | D | float64 |  |
| `mabs_r` | D | float64 |  |
| `mabs_j` | D | float64 |  |
| `mabs_k` | D | float64 |  |
| `flag_chandra` | D | float64 |  |
| `zpdf_med_space` | D | float64 |  |
| `zpdf_l68_space` | D | float64 |  |
| `zpdf_u68_space` | D | float64 |  |

### Sample Statistics

Based on first 50,000 of 784,016 rows.

**Columns with NaN values:**

| Column | NaN count | Inf count | Min | Max |
|--------|-----------|-----------|-----|-----|
| `age_minchi2` | 340 (0.7%) | 0 | 0.8864 | 1.005 |

**Columns with potential sentinel values:**

| Column | Sentinel | Count |
|--------|----------|-------|
| `zfinal` | -99.0 | 4,700 (9.4%) |
| `zfinal` | 0.0 | 679 (1.4%) |
| `type` | 0 | 48,615 (97.2%) |
| `zp_agn` | 0.0 | 12,258 (24.5%) |
| `ebv_minchi2` | 0.0 | 17,114 (34.2%) |
| `law_minchi2` | 0 | 25,856 (51.7%) |
| `flag_chandra` | 0.0 | 49,915 (99.8%) |

**Low-cardinality columns (categorical/flag):**

- `type`: [0, 1, 2]
- `nbfilt`: [5, 6, 29, 30, 31, 32]
- `mod_minchi2_phys`: [-99, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
- `law_minchi2`: [-999, 0, 1, 2]

---

## Extension 3: SE++APER

**Rows:** 784,016 | **Columns:** 148

### Column Inventory

| Column | FITS Format | Type | Unit |
|--------|-------------|------|------|
| `mag_aper_f115w` | 5E | float32[5] |  |
| `mag_aper_f150w` | 5E | float32[5] |  |
| `mag_aper_f277w` | 5E | float32[5] |  |
| `mag_aper_f444w` | 5E | float32[5] |  |
| `mag_aper_hst-f814w` | 5E | float32[5] |  |
| `mag_aper_f770w` | 5E | float32[5] |  |
| `mag_aper_cfht-u` | 5E | float32[5] |  |
| `mag_aper_hsc-g` | 5E | float32[5] |  |
| `mag_aper_hsc-r` | 5E | float32[5] |  |
| `mag_aper_hsc-i` | 5E | float32[5] |  |
| `mag_aper_hsc-z` | 5E | float32[5] |  |
| `mag_aper_hsc-y` | 5E | float32[5] |  |
| `mag_aper_hsc-nb0816` | 5E | float32[5] |  |
| `mag_aper_hsc-nb0921` | 5E | float32[5] |  |
| `mag_aper_hsc-nb1010` | 5E | float32[5] |  |
| `mag_aper_uvista-y` | 5E | float32[5] |  |
| `mag_aper_uvista-j` | 5E | float32[5] |  |
| `mag_aper_uvista-h` | 5E | float32[5] |  |
| `mag_aper_uvista-ks` | 5E | float32[5] |  |
| `mag_aper_uvista-nb118` | 5E | float32[5] |  |
| `mag_aper_sc-ia484` | 5E | float32[5] |  |
| `mag_aper_sc-ia527` | 5E | float32[5] |  |
| `mag_aper_sc-ia624` | 5E | float32[5] |  |
| `mag_aper_sc-ia679` | 5E | float32[5] |  |
| `mag_aper_sc-ia738` | 5E | float32[5] |  |
| `mag_aper_sc-ia767` | 5E | float32[5] |  |
| `mag_aper_sc-ib427` | 5E | float32[5] |  |
| `mag_aper_sc-ib505` | 5E | float32[5] |  |
| `mag_aper_sc-ib574` | 5E | float32[5] |  |
| `mag_aper_sc-ib709` | 5E | float32[5] |  |
| `mag_aper_sc-ib827` | 5E | float32[5] |  |
| `mag_aper_sc-nb711` | 5E | float32[5] |  |
| `mag_aper_sc-nb816` | 5E | float32[5] |  |
| `mag_aper_irac-ch1` | 5E | float32[5] |  |
| `mag_aper_irac-ch2` | 5E | float32[5] |  |
| `mag_aper_irac-ch3` | 5E | float32[5] |  |
| `mag_aper_irac-ch4` | 5E | float32[5] |  |
| `mag_err_aper_f115w` | 5E | float32[5] |  |
| `mag_err_aper_f150w` | 5E | float32[5] |  |
| `mag_err_aper_f277w` | 5E | float32[5] |  |
| `mag_err_aper_f444w` | 5E | float32[5] |  |
| `mag_err_aper_hst-f814w` | 5E | float32[5] |  |
| `mag_err_aper_f770w` | 5E | float32[5] |  |
| `mag_err_aper_cfht-u` | 5E | float32[5] |  |
| `mag_err_aper_hsc-g` | 5E | float32[5] |  |
| `mag_err_aper_hsc-r` | 5E | float32[5] |  |
| `mag_err_aper_hsc-i` | 5E | float32[5] |  |
| `mag_err_aper_hsc-z` | 5E | float32[5] |  |
| `mag_err_aper_hsc-y` | 5E | float32[5] |  |
| `mag_err_aper_hsc-nb0816` | 5E | float32[5] |  |
| `mag_err_aper_hsc-nb0921` | 5E | float32[5] |  |
| `mag_err_aper_hsc-nb1010` | 5E | float32[5] |  |
| `mag_err_aper_uvista-y` | 5E | float32[5] |  |
| `mag_err_aper_uvista-j` | 5E | float32[5] |  |
| `mag_err_aper_uvista-h` | 5E | float32[5] |  |
| `mag_err_aper_uvista-ks` | 5E | float32[5] |  |
| `mag_err_aper_uvista-nb118` | 5E | float32[5] |  |
| `mag_err_aper_sc-ia484` | 5E | float32[5] |  |
| `mag_err_aper_sc-ia527` | 5E | float32[5] |  |
| `mag_err_aper_sc-ia624` | 5E | float32[5] |  |
| `mag_err_aper_sc-ia679` | 5E | float32[5] |  |
| `mag_err_aper_sc-ia738` | 5E | float32[5] |  |
| `mag_err_aper_sc-ia767` | 5E | float32[5] |  |
| `mag_err_aper_sc-ib427` | 5E | float32[5] |  |
| `mag_err_aper_sc-ib505` | 5E | float32[5] |  |
| `mag_err_aper_sc-ib574` | 5E | float32[5] |  |
| `mag_err_aper_sc-ib709` | 5E | float32[5] |  |
| `mag_err_aper_sc-ib827` | 5E | float32[5] |  |
| `mag_err_aper_sc-nb711` | 5E | float32[5] |  |
| `mag_err_aper_sc-nb816` | 5E | float32[5] |  |
| `mag_err_aper_irac-ch1` | 5E | float32[5] |  |
| `mag_err_aper_irac-ch2` | 5E | float32[5] |  |
| `mag_err_aper_irac-ch3` | 5E | float32[5] |  |
| `mag_err_aper_irac-ch4` | 5E | float32[5] |  |
| `flux_aper_f115w` | 5E | float32[5] |  |
| `flux_aper_f150w` | 5E | float32[5] |  |
| `flux_aper_f277w` | 5E | float32[5] |  |
| `flux_aper_f444w` | 5E | float32[5] |  |
| `flux_aper_hst-f814w` | 5E | float32[5] |  |
| `flux_aper_f770w` | 5E | float32[5] |  |
| `flux_aper_cfht-u` | 5E | float32[5] |  |
| `flux_aper_hsc-g` | 5E | float32[5] |  |
| `flux_aper_hsc-r` | 5E | float32[5] |  |
| `flux_aper_hsc-i` | 5E | float32[5] |  |
| `flux_aper_hsc-z` | 5E | float32[5] |  |
| `flux_aper_hsc-y` | 5E | float32[5] |  |
| `flux_aper_hsc-nb0816` | 5E | float32[5] |  |
| `flux_aper_hsc-nb0921` | 5E | float32[5] |  |
| `flux_aper_hsc-nb1010` | 5E | float32[5] |  |
| `flux_aper_uvista-y` | 5E | float32[5] |  |
| `flux_aper_uvista-j` | 5E | float32[5] |  |
| `flux_aper_uvista-h` | 5E | float32[5] |  |
| `flux_aper_uvista-ks` | 5E | float32[5] |  |
| `flux_aper_uvista-nb118` | 5E | float32[5] |  |
| `flux_aper_sc-ia484` | 5E | float32[5] |  |
| `flux_aper_sc-ia527` | 5E | float32[5] |  |
| `flux_aper_sc-ia624` | 5E | float32[5] |  |
| `flux_aper_sc-ia679` | 5E | float32[5] |  |
| `flux_aper_sc-ia738` | 5E | float32[5] |  |
| `flux_aper_sc-ia767` | 5E | float32[5] |  |
| `flux_aper_sc-ib427` | 5E | float32[5] |  |
| `flux_aper_sc-ib505` | 5E | float32[5] |  |
| `flux_aper_sc-ib574` | 5E | float32[5] |  |
| `flux_aper_sc-ib709` | 5E | float32[5] |  |
| `flux_aper_sc-ib827` | 5E | float32[5] |  |
| `flux_aper_sc-nb711` | 5E | float32[5] |  |
| `flux_aper_sc-nb816` | 5E | float32[5] |  |
| `flux_aper_irac-ch1` | 5E | float32[5] |  |
| `flux_aper_irac-ch2` | 5E | float32[5] |  |
| `flux_aper_irac-ch3` | 5E | float32[5] |  |
| `flux_aper_irac-ch4` | 5E | float32[5] |  |
| `flux_err_aper_f115w` | 5E | float32[5] |  |
| `flux_err_aper_f150w` | 5E | float32[5] |  |
| `flux_err_aper_f277w` | 5E | float32[5] |  |
| `flux_err_aper_f444w` | 5E | float32[5] |  |
| `flux_err_aper_hst-f814w` | 5E | float32[5] |  |
| `flux_err_aper_f770w` | 5E | float32[5] |  |
| `flux_err_aper_cfht-u` | 5E | float32[5] |  |
| `flux_err_aper_hsc-g` | 5E | float32[5] |  |
| `flux_err_aper_hsc-r` | 5E | float32[5] |  |
| `flux_err_aper_hsc-i` | 5E | float32[5] |  |
| `flux_err_aper_hsc-z` | 5E | float32[5] |  |
| `flux_err_aper_hsc-y` | 5E | float32[5] |  |
| `flux_err_aper_hsc-nb0816` | 5E | float32[5] |  |
| `flux_err_aper_hsc-nb0921` | 5E | float32[5] |  |
| `flux_err_aper_hsc-nb1010` | 5E | float32[5] |  |
| `flux_err_aper_uvista-y` | 5E | float32[5] |  |
| `flux_err_aper_uvista-j` | 5E | float32[5] |  |
| `flux_err_aper_uvista-h` | 5E | float32[5] |  |
| `flux_err_aper_uvista-ks` | 5E | float32[5] |  |
| `flux_err_aper_uvista-nb118` | 5E | float32[5] |  |
| `flux_err_aper_sc-ia484` | 5E | float32[5] |  |
| `flux_err_aper_sc-ia527` | 5E | float32[5] |  |
| `flux_err_aper_sc-ia624` | 5E | float32[5] |  |
| `flux_err_aper_sc-ia679` | 5E | float32[5] |  |
| `flux_err_aper_sc-ia738` | 5E | float32[5] |  |
| `flux_err_aper_sc-ia767` | 5E | float32[5] |  |
| `flux_err_aper_sc-ib427` | 5E | float32[5] |  |
| `flux_err_aper_sc-ib505` | 5E | float32[5] |  |
| `flux_err_aper_sc-ib574` | 5E | float32[5] |  |
| `flux_err_aper_sc-ib709` | 5E | float32[5] |  |
| `flux_err_aper_sc-ib827` | 5E | float32[5] |  |
| `flux_err_aper_sc-nb711` | 5E | float32[5] |  |
| `flux_err_aper_sc-nb816` | 5E | float32[5] |  |
| `flux_err_aper_irac-ch1` | 5E | float32[5] |  |
| `flux_err_aper_irac-ch2` | 5E | float32[5] |  |
| `flux_err_aper_irac-ch3` | 5E | float32[5] |  |
| `flux_err_aper_irac-ch4` | 5E | float32[5] |  |

### Sample Statistics

Based on first 50,000 of 784,016 rows.

**Array columns (multi-value per row):**

- `mag_aper_f115w`: shape (5,)
- `mag_aper_f150w`: shape (5,)
- `mag_aper_f277w`: shape (5,)
- `mag_aper_f444w`: shape (5,)
- `mag_aper_hst-f814w`: shape (5,)
- `mag_aper_f770w`: shape (5,)
- `mag_aper_cfht-u`: shape (5,)
- `mag_aper_hsc-g`: shape (5,)
- `mag_aper_hsc-r`: shape (5,)
- `mag_aper_hsc-i`: shape (5,)
- `mag_aper_hsc-z`: shape (5,)
- `mag_aper_hsc-y`: shape (5,)
- `mag_aper_hsc-nb0816`: shape (5,)
- `mag_aper_hsc-nb0921`: shape (5,)
- `mag_aper_hsc-nb1010`: shape (5,)
- `mag_aper_uvista-y`: shape (5,)
- `mag_aper_uvista-j`: shape (5,)
- `mag_aper_uvista-h`: shape (5,)
- `mag_aper_uvista-ks`: shape (5,)
- `mag_aper_uvista-nb118`: shape (5,)
- `mag_aper_sc-ia484`: shape (5,)
- `mag_aper_sc-ia527`: shape (5,)
- `mag_aper_sc-ia624`: shape (5,)
- `mag_aper_sc-ia679`: shape (5,)
- `mag_aper_sc-ia738`: shape (5,)
- `mag_aper_sc-ia767`: shape (5,)
- `mag_aper_sc-ib427`: shape (5,)
- `mag_aper_sc-ib505`: shape (5,)
- `mag_aper_sc-ib574`: shape (5,)
- `mag_aper_sc-ib709`: shape (5,)
- `mag_aper_sc-ib827`: shape (5,)
- `mag_aper_sc-nb711`: shape (5,)
- `mag_aper_sc-nb816`: shape (5,)
- `mag_aper_irac-ch1`: shape (5,)
- `mag_aper_irac-ch2`: shape (5,)
- `mag_aper_irac-ch3`: shape (5,)
- `mag_aper_irac-ch4`: shape (5,)
- `mag_err_aper_f115w`: shape (5,)
- `mag_err_aper_f150w`: shape (5,)
- `mag_err_aper_f277w`: shape (5,)
- `mag_err_aper_f444w`: shape (5,)
- `mag_err_aper_hst-f814w`: shape (5,)
- `mag_err_aper_f770w`: shape (5,)
- `mag_err_aper_cfht-u`: shape (5,)
- `mag_err_aper_hsc-g`: shape (5,)
- `mag_err_aper_hsc-r`: shape (5,)
- `mag_err_aper_hsc-i`: shape (5,)
- `mag_err_aper_hsc-z`: shape (5,)
- `mag_err_aper_hsc-y`: shape (5,)
- `mag_err_aper_hsc-nb0816`: shape (5,)
- `mag_err_aper_hsc-nb0921`: shape (5,)
- `mag_err_aper_hsc-nb1010`: shape (5,)
- `mag_err_aper_uvista-y`: shape (5,)
- `mag_err_aper_uvista-j`: shape (5,)
- `mag_err_aper_uvista-h`: shape (5,)
- `mag_err_aper_uvista-ks`: shape (5,)
- `mag_err_aper_uvista-nb118`: shape (5,)
- `mag_err_aper_sc-ia484`: shape (5,)
- `mag_err_aper_sc-ia527`: shape (5,)
- `mag_err_aper_sc-ia624`: shape (5,)
- `mag_err_aper_sc-ia679`: shape (5,)
- `mag_err_aper_sc-ia738`: shape (5,)
- `mag_err_aper_sc-ia767`: shape (5,)
- `mag_err_aper_sc-ib427`: shape (5,)
- `mag_err_aper_sc-ib505`: shape (5,)
- `mag_err_aper_sc-ib574`: shape (5,)
- `mag_err_aper_sc-ib709`: shape (5,)
- `mag_err_aper_sc-ib827`: shape (5,)
- `mag_err_aper_sc-nb711`: shape (5,)
- `mag_err_aper_sc-nb816`: shape (5,)
- `mag_err_aper_irac-ch1`: shape (5,)
- `mag_err_aper_irac-ch2`: shape (5,)
- `mag_err_aper_irac-ch3`: shape (5,)
- `mag_err_aper_irac-ch4`: shape (5,)
- `flux_aper_f115w`: shape (5,)
- `flux_aper_f150w`: shape (5,)
- `flux_aper_f277w`: shape (5,)
- `flux_aper_f444w`: shape (5,)
- `flux_aper_hst-f814w`: shape (5,)
- `flux_aper_f770w`: shape (5,)
- `flux_aper_cfht-u`: shape (5,)
- `flux_aper_hsc-g`: shape (5,)
- `flux_aper_hsc-r`: shape (5,)
- `flux_aper_hsc-i`: shape (5,)
- `flux_aper_hsc-z`: shape (5,)
- `flux_aper_hsc-y`: shape (5,)
- `flux_aper_hsc-nb0816`: shape (5,)
- `flux_aper_hsc-nb0921`: shape (5,)
- `flux_aper_hsc-nb1010`: shape (5,)
- `flux_aper_uvista-y`: shape (5,)
- `flux_aper_uvista-j`: shape (5,)
- `flux_aper_uvista-h`: shape (5,)
- `flux_aper_uvista-ks`: shape (5,)
- `flux_aper_uvista-nb118`: shape (5,)
- `flux_aper_sc-ia484`: shape (5,)
- `flux_aper_sc-ia527`: shape (5,)
- `flux_aper_sc-ia624`: shape (5,)
- `flux_aper_sc-ia679`: shape (5,)
- `flux_aper_sc-ia738`: shape (5,)
- `flux_aper_sc-ia767`: shape (5,)
- `flux_aper_sc-ib427`: shape (5,)
- `flux_aper_sc-ib505`: shape (5,)
- `flux_aper_sc-ib574`: shape (5,)
- `flux_aper_sc-ib709`: shape (5,)
- `flux_aper_sc-ib827`: shape (5,)
- `flux_aper_sc-nb711`: shape (5,)
- `flux_aper_sc-nb816`: shape (5,)
- `flux_aper_irac-ch1`: shape (5,)
- `flux_aper_irac-ch2`: shape (5,)
- `flux_aper_irac-ch3`: shape (5,)
- `flux_aper_irac-ch4`: shape (5,)
- `flux_err_aper_f115w`: shape (5,)
- `flux_err_aper_f150w`: shape (5,)
- `flux_err_aper_f277w`: shape (5,)
- `flux_err_aper_f444w`: shape (5,)
- `flux_err_aper_hst-f814w`: shape (5,)
- `flux_err_aper_f770w`: shape (5,)
- `flux_err_aper_cfht-u`: shape (5,)
- `flux_err_aper_hsc-g`: shape (5,)
- `flux_err_aper_hsc-r`: shape (5,)
- `flux_err_aper_hsc-i`: shape (5,)
- `flux_err_aper_hsc-z`: shape (5,)
- `flux_err_aper_hsc-y`: shape (5,)
- `flux_err_aper_hsc-nb0816`: shape (5,)
- `flux_err_aper_hsc-nb0921`: shape (5,)
- `flux_err_aper_hsc-nb1010`: shape (5,)
- `flux_err_aper_uvista-y`: shape (5,)
- `flux_err_aper_uvista-j`: shape (5,)
- `flux_err_aper_uvista-h`: shape (5,)
- `flux_err_aper_uvista-ks`: shape (5,)
- `flux_err_aper_uvista-nb118`: shape (5,)
- `flux_err_aper_sc-ia484`: shape (5,)
- `flux_err_aper_sc-ia527`: shape (5,)
- `flux_err_aper_sc-ia624`: shape (5,)
- `flux_err_aper_sc-ia679`: shape (5,)
- `flux_err_aper_sc-ia738`: shape (5,)
- `flux_err_aper_sc-ia767`: shape (5,)
- `flux_err_aper_sc-ib427`: shape (5,)
- `flux_err_aper_sc-ib505`: shape (5,)
- `flux_err_aper_sc-ib574`: shape (5,)
- `flux_err_aper_sc-ib709`: shape (5,)
- `flux_err_aper_sc-ib827`: shape (5,)
- `flux_err_aper_sc-nb711`: shape (5,)
- `flux_err_aper_sc-nb816`: shape (5,)
- `flux_err_aper_irac-ch1`: shape (5,)
- `flux_err_aper_irac-ch2`: shape (5,)
- `flux_err_aper_irac-ch3`: shape (5,)
- `flux_err_aper_irac-ch4`: shape (5,)

**Columns with potential sentinel values:**

| Column | Sentinel | Count |
|--------|----------|-------|
| `mag_err_aper_f115w` | -999.0 | 11,685 (23.4%) |
| `mag_err_aper_f150w` | -999.0 | 7,976 (16.0%) |
| `mag_err_aper_f277w` | -999.0 | 4,967 (9.9%) |
| `mag_err_aper_f444w` | -999.0 | 8,111 (16.2%) |
| `mag_err_aper_hst-f814w` | -999.0 | 12,791 (25.6%) |
| `mag_err_aper_f770w` | -999.0 | 13,387 (26.8%) |
| `mag_err_aper_cfht-u` | -999.0 | 28,114 (56.2%) |
| `mag_err_aper_hsc-g` | -999.0 | 16,818 (33.6%) |
| `mag_err_aper_hsc-r` | -999.0 | 13,512 (27.0%) |
| `mag_err_aper_hsc-i` | -999.0 | 10,066 (20.1%) |
| `mag_err_aper_hsc-z` | -999.0 | 12,428 (24.9%) |
| `mag_err_aper_hsc-y` | -999.0 | 24,053 (48.1%) |
| `mag_err_aper_hsc-nb0816` | -999.0 | 27,496 (55.0%) |
| `mag_err_aper_hsc-nb0921` | -999.0 | 24,530 (49.1%) |
| `mag_err_aper_hsc-nb1010` | -999.0 | 54,111 (108.2%) |
| `mag_err_aper_uvista-y` | -999.0 | 13,838 (27.7%) |
| `mag_err_aper_uvista-j` | -999.0 | 12,231 (24.5%) |
| `mag_err_aper_uvista-h` | -999.0 | 14,269 (28.5%) |
| `mag_err_aper_uvista-ks` | -999.0 | 17,988 (36.0%) |
| `mag_err_aper_uvista-nb118` | -999.0 | 32,722 (65.4%) |
| `mag_err_aper_sc-ia484` | -999.0 | 27,821 (55.6%) |
| `mag_err_aper_sc-ia527` | -999.0 | 25,018 (50.0%) |
| `mag_err_aper_sc-ia624` | -999.0 | 19,449 (38.9%) |
| `mag_err_aper_sc-ia679` | -999.0 | 43,398 (86.8%) |
| `mag_err_aper_sc-ia738` | -999.0 | 21,200 (42.4%) |
| `mag_err_aper_sc-ia767` | -999.0 | 43,282 (86.6%) |
| `mag_err_aper_sc-ib427` | -999.0 | 50,452 (100.9%) |
| `mag_err_aper_sc-ib505` | -999.0 | 32,648 (65.3%) |
| `mag_err_aper_sc-ib574` | -999.0 | 48,248 (96.5%) |
| `mag_err_aper_sc-ib709` | -999.0 | 37,952 (75.9%) |

---

## Extension 4: CIGALE

**Rows:** 784,016 | **Columns:** 54

### Column Inventory

| Column | FITS Format | Type | Unit |
|--------|-------------|------|------|
| `age_form` | D | float64 |  |
| `age_form_err` | D | float64 |  |
| `sfr_mass_vector_dir` | D | float64 |  |
| `sfr_mass_vector_dir_err` | D | float64 |  |
| `sfh_sfr_bin1` | D | float64 |  |
| `sfh_sfr_bin1_err` | D | float64 |  |
| `sfh_sfr_bin2` | D | float64 |  |
| `sfh_sfr_bin2_err` | D | float64 |  |
| `sfh_sfr_bin3` | D | float64 |  |
| `sfh_sfr_bin3_err` | D | float64 |  |
| `sfh_sfr_bin4` | D | float64 |  |
| `sfh_sfr_bin4_err` | D | float64 |  |
| `sfh_sfr_bin5` | D | float64 |  |
| `sfh_sfr_bin5_err` | D | float64 |  |
| `sfh_sfr_bin6` | D | float64 |  |
| `sfh_sfr_bin6_err` | D | float64 |  |
| `sfh_sfr_bin7` | D | float64 |  |
| `sfh_sfr_bin7_err` | D | float64 |  |
| `sfh_sfr_bin8` | D | float64 |  |
| `sfh_sfr_bin8_err` | D | float64 |  |
| `sfh_sfr_bin9` | D | float64 |  |
| `sfh_sfr_bin9_err` | D | float64 |  |
| `sfr_mass_vector_norm` | D | float64 |  |
| `sfr_mass_vector_norm_err` | D | float64 |  |
| `sfh_time_bin1` | D | float64 |  |
| `sfh_time_bin1_err` | D | float64 |  |
| `sfh_time_bin2` | D | float64 |  |
| `sfh_time_bin2_err` | D | float64 |  |
| `sfh_time_bin3` | D | float64 |  |
| `sfh_time_bin3_err` | D | float64 |  |
| `sfh_time_bin4` | D | float64 |  |
| `sfh_time_bin4_err` | D | float64 |  |
| `sfh_time_bin5` | D | float64 |  |
| `sfh_time_bin5_err` | D | float64 |  |
| `sfh_time_bin6` | D | float64 |  |
| `sfh_time_bin6_err` | D | float64 |  |
| `sfh_time_bin7` | D | float64 |  |
| `sfh_time_bin7_err` | D | float64 |  |
| `sfh_time_bin8` | D | float64 |  |
| `sfh_time_bin8_err` | D | float64 |  |
| `sfh_time_bin9` | D | float64 |  |
| `sfh_time_bin9_err` | D | float64 |  |
| `metallicity` | D | float64 |  |
| `metallicity_err` | D | float64 |  |
| `sfh_integrated` | D | float64 |  |
| `sfh_integrated_err` | D | float64 |  |
| `sfr_inst` | D | float64 |  |
| `sfr_inst_err` | D | float64 |  |
| `sfr_100myr` | D | float64 |  |
| `sfr_100myr_err` | D | float64 |  |
| `mass` | D | float64 |  |
| `mass_err` | D | float64 |  |
| `chi2_best_fit` | D | float64 |  |
| `chi2_red_best_fit` | D | float64 |  |

### Sample Statistics

Based on first 50,000 of 784,016 rows.

**Columns with NaN values:**

| Column | NaN count | Inf count | Min | Max |
|--------|-----------|-----------|-----|-----|
| `age_form` | 8,073 (16.1%) | 0 | 8.227 | 9656 |
| `age_form_err` | 8,073 (16.1%) | 0 | 2.303e-23 | 3315 |
| `sfr_mass_vector_dir` | 8,073 (16.1%) | 0 | -90 | 89.99 |
| `sfr_mass_vector_dir_err` | 8,073 (16.1%) | 0 | 1.228e-22 | 89.91 |
| `sfh_sfr_bin1` | 8,073 (16.1%) | 0 | 1.159e-16 | 6.714e-08 |
| `sfh_sfr_bin1_err` | 8,073 (16.1%) | 0 | 0 | 2.855e-08 |
| `sfh_sfr_bin2` | 8,073 (16.1%) | 0 | 1.956e-16 | 5.042e-08 |
| `sfh_sfr_bin2_err` | 8,073 (16.1%) | 0 | 0 | 1.845e-08 |
| `sfh_sfr_bin3` | 8,073 (16.1%) | 0 | 1.792e-16 | 1.5e-08 |
| `sfh_sfr_bin3_err` | 8,073 (16.1%) | 0 | 0 | 1.026e-08 |
| `sfh_sfr_bin4` | 8,073 (16.1%) | 0 | 1.985e-16 | 2.696e-08 |
| `sfh_sfr_bin4_err` | 8,073 (16.1%) | 0 | 0 | 1.242e-08 |
| `sfh_sfr_bin5` | 8,073 (16.1%) | 0 | 2.739e-16 | 1.582e-08 |
| `sfh_sfr_bin5_err` | 8,073 (16.1%) | 0 | 0 | 6.025e-09 |
| `sfh_sfr_bin6` | 8,073 (16.1%) | 0 | 5.305e-16 | 7.359e-09 |
| `sfh_sfr_bin6_err` | 8,073 (16.1%) | 0 | 0 | 3.782e-09 |
| `sfh_sfr_bin7` | 8,073 (16.1%) | 0 | 1.73e-15 | 5.281e-09 |
| `sfh_sfr_bin7_err` | 8,073 (16.1%) | 0 | 0 | 2.943e-09 |
| `sfh_sfr_bin8` | 8,073 (16.1%) | 0 | 4.762e-13 | 5.401e-09 |
| `sfh_sfr_bin8_err` | 8,073 (16.1%) | 0 | 0 | 2.202e-09 |
| `sfh_sfr_bin9` | 8,073 (16.1%) | 0 | 8.539e-14 | 4.752e-09 |
| `sfh_sfr_bin9_err` | 8,073 (16.1%) | 0 | 0 | 2.559e-09 |
| `sfr_mass_vector_norm` | 8,073 (16.1%) | 0 | 7.225e-05 | 0.01609 |
| `sfr_mass_vector_norm_err` | 8,073 (16.1%) | 0 | 0 | 0.005038 |
| `sfh_time_bin1` | 8,073 (16.1%) | 0 | 10 | 10 |
| `sfh_time_bin1_err` | 8,073 (16.1%) | 0 | 0 | 1.243e-13 |
| `sfh_time_bin2` | 8,073 (16.1%) | 0 | 15 | 25 |
| `sfh_time_bin2_err` | 8,073 (16.1%) | 0 | 0 | 0.5 |
| `sfh_time_bin3` | 8,073 (16.1%) | 0 | 23 | 61 |
| `sfh_time_bin3_err` | 8,073 (16.1%) | 0 | 0 | 0.5 |
| ... | (24 more columns with NaNs) | | | |

**Columns with potential sentinel values:**

| Column | Sentinel | Count |
|--------|----------|-------|
| `sfh_time_bin1_err` | 0.0 | 6,010 (12.0%) |
| `sfh_time_bin2_err` | 0.0 | 4,544 (9.1%) |
| `sfh_time_bin3_err` | 0.0 | 1,538 (3.1%) |

---

## Extension 5: ML-MORPHO

**Rows:** 784,016 | **Columns:** 150

### Column Inventory

| Column | FITS Format | Type | Unit |
|--------|-------------|------|------|
| `sph_0_f150w` | D | float64 |  |
| `disk_0_f150w` | D | float64 |  |
| `irr_0_f150w` | D | float64 |  |
| `bd_0_f150w` | D | float64 |  |
| `sph_1_f150w` | D | float64 |  |
| `disk_1_f150w` | D | float64 |  |
| `irr_1_f150w` | D | float64 |  |
| `bd_1_f150w` | D | float64 |  |
| `sph_2_f150w` | D | float64 |  |
| `disk_2_f150w` | D | float64 |  |
| `irr_2_f150w` | D | float64 |  |
| `bd_2_f150w` | D | float64 |  |
| `sph_3_f150w` | D | float64 |  |
| `disk_3_f150w` | D | float64 |  |
| `irr_3_f150w` | D | float64 |  |
| `bd_3_f150w` | D | float64 |  |
| `sph_4_f150w` | D | float64 |  |
| `disk_4_f150w` | D | float64 |  |
| `irr_4_f150w` | D | float64 |  |
| `bd_4_f150w` | D | float64 |  |
| `sph_5_f150w` | D | float64 |  |
| `disk_5_f150w` | D | float64 |  |
| `irr_5_f150w` | D | float64 |  |
| `bd_5_f150w` | D | float64 |  |
| `sph_6_f150w` | D | float64 |  |
| `disk_6_f150w` | D | float64 |  |
| `irr_6_f150w` | D | float64 |  |
| `bd_6_f150w` | D | float64 |  |
| `sph_7_f150w` | D | float64 |  |
| `disk_7_f150w` | D | float64 |  |
| `irr_7_f150w` | D | float64 |  |
| `bd_7_f150w` | D | float64 |  |
| `sph_8_f150w` | D | float64 |  |
| `disk_8_f150w` | D | float64 |  |
| `irr_8_f150w` | D | float64 |  |
| `bd_8_f150w` | D | float64 |  |
| `sph_9_f150w` | D | float64 |  |
| `disk_9_f150w` | D | float64 |  |
| `irr_9_f150w` | D | float64 |  |
| `bd_9_f150w` | D | float64 |  |
| `sph_0_f277w` | D | float64 |  |
| `disk_0_f277w` | D | float64 |  |
| `irr_0_f277w` | D | float64 |  |
| `bd_0_f277w` | D | float64 |  |
| `sph_1_f277w` | D | float64 |  |
| `disk_1_f277w` | D | float64 |  |
| `irr_1_f277w` | D | float64 |  |
| `bd_1_f277w` | D | float64 |  |
| `sph_2_f277w` | D | float64 |  |
| `disk_2_f277w` | D | float64 |  |
| `irr_2_f277w` | D | float64 |  |
| `bd_2_f277w` | D | float64 |  |
| `sph_3_f277w` | D | float64 |  |
| `disk_3_f277w` | D | float64 |  |
| `irr_3_f277w` | D | float64 |  |
| `bd_3_f277w` | D | float64 |  |
| `sph_4_f277w` | D | float64 |  |
| `disk_4_f277w` | D | float64 |  |
| `irr_4_f277w` | D | float64 |  |
| `bd_4_f277w` | D | float64 |  |
| `sph_5_f277w` | D | float64 |  |
| `disk_5_f277w` | D | float64 |  |
| `irr_5_f277w` | D | float64 |  |
| `bd_5_f277w` | D | float64 |  |
| `sph_6_f277w` | D | float64 |  |
| `disk_6_f277w` | D | float64 |  |
| `irr_6_f277w` | D | float64 |  |
| `bd_6_f277w` | D | float64 |  |
| `sph_7_f277w` | D | float64 |  |
| `disk_7_f277w` | D | float64 |  |
| `irr_7_f277w` | D | float64 |  |
| `bd_7_f277w` | D | float64 |  |
| `sph_8_f277w` | D | float64 |  |
| `disk_8_f277w` | D | float64 |  |
| `irr_8_f277w` | D | float64 |  |
| `bd_8_f277w` | D | float64 |  |
| `sph_9_f277w` | D | float64 |  |
| `disk_9_f277w` | D | float64 |  |
| `irr_9_f277w` | D | float64 |  |
| `bd_9_f277w` | D | float64 |  |
| `sph_0_f444w` | D | float64 |  |
| `disk_0_f444w` | D | float64 |  |
| `irr_0_f444w` | D | float64 |  |
| `bd_0_f444w` | D | float64 |  |
| `sph_1_f444w` | D | float64 |  |
| `disk_1_f444w` | D | float64 |  |
| `irr_1_f444w` | D | float64 |  |
| `bd_1_f444w` | D | float64 |  |
| `sph_2_f444w` | D | float64 |  |
| `disk_2_f444w` | D | float64 |  |
| `irr_2_f444w` | D | float64 |  |
| `bd_2_f444w` | D | float64 |  |
| `sph_3_f444w` | D | float64 |  |
| `disk_3_f444w` | D | float64 |  |
| `irr_3_f444w` | D | float64 |  |
| `bd_3_f444w` | D | float64 |  |
| `sph_4_f444w` | D | float64 |  |
| `disk_4_f444w` | D | float64 |  |
| `irr_4_f444w` | D | float64 |  |
| `bd_4_f444w` | D | float64 |  |
| `sph_5_f444w` | D | float64 |  |
| `disk_5_f444w` | D | float64 |  |
| `irr_5_f444w` | D | float64 |  |
| `bd_5_f444w` | D | float64 |  |
| `sph_6_f444w` | D | float64 |  |
| `disk_6_f444w` | D | float64 |  |
| `irr_6_f444w` | D | float64 |  |
| `bd_6_f444w` | D | float64 |  |
| `sph_7_f444w` | D | float64 |  |
| `disk_7_f444w` | D | float64 |  |
| `irr_7_f444w` | D | float64 |  |
| `bd_7_f444w` | D | float64 |  |
| `sph_8_f444w` | D | float64 |  |
| `disk_8_f444w` | D | float64 |  |
| `irr_8_f444w` | D | float64 |  |
| `bd_8_f444w` | D | float64 |  |
| `sph_9_f444w` | D | float64 |  |
| `disk_9_f444w` | D | float64 |  |
| `irr_9_f444w` | D | float64 |  |
| `bd_9_f444w` | D | float64 |  |
| `sph_f150w_mean` | D | float64 |  |
| `sph_f150w_std` | D | float64 |  |
| `disk_f150w_mean` | D | float64 |  |
| `disk_f150w_std` | D | float64 |  |
| `irr_f150w_mean` | D | float64 |  |
| `irr_f150w_std` | D | float64 |  |
| `bd_f150w_mean` | D | float64 |  |
| `bd_f150w_std` | D | float64 |  |
| `sph_f277w_mean` | D | float64 |  |
| `sph_f277w_std` | D | float64 |  |
| `disk_f277w_mean` | D | float64 |  |
| `disk_f277w_std` | D | float64 |  |
| `irr_f277w_mean` | D | float64 |  |
| `irr_f277w_std` | D | float64 |  |
| `bd_f277w_mean` | D | float64 |  |
| `bd_f277w_std` | D | float64 |  |
| `sph_f444w_mean` | D | float64 |  |
| `sph_f444w_std` | D | float64 |  |
| `disk_f444w_mean` | D | float64 |  |
| `disk_f444w_std` | D | float64 |  |
| `irr_f444w_mean` | D | float64 |  |
| `irr_f444w_std` | D | float64 |  |
| `bd_f444w_mean` | D | float64 |  |
| `bd_f444w_std` | D | float64 |  |
| `morph_flag_f277w` | K | int64 |  |
| `delta_f277w` | D | float64 |  |
| `morph_flag_f444w` | K | int64 |  |
| `delta_f444w` | D | float64 |  |
| `morph_flag_f150w` | K | int64 |  |
| `delta_f150w` | D | float64 |  |

### Sample Statistics

Based on first 50,000 of 784,016 rows.

**Columns with NaN values:**

| Column | NaN count | Inf count | Min | Max |
|--------|-----------|-----------|-----|-----|
| `sph_0_f150w` | 19,405 (38.8%) | 0 | 4.311e-14 | 1 |
| `disk_0_f150w` | 19,405 (38.8%) | 0 | 1.863e-07 | 0.9864 |
| `irr_0_f150w` | 19,405 (38.8%) | 0 | 4.26e-10 | 1 |
| `bd_0_f150w` | 19,405 (38.8%) | 0 | 6.045e-22 | 0.9999 |
| `sph_1_f150w` | 19,405 (38.8%) | 0 | 4.703e-31 | 0.9954 |
| `disk_1_f150w` | 19,405 (38.8%) | 0 | 2.194e-07 | 0.9879 |
| `irr_1_f150w` | 19,405 (38.8%) | 0 | 0.000378 | 1 |
| `bd_1_f150w` | 19,405 (38.8%) | 0 | 5.615e-28 | 0.9911 |
| `sph_2_f150w` | 19,405 (38.8%) | 0 | 1.532e-28 | 0.9997 |
| `disk_2_f150w` | 19,405 (38.8%) | 0 | 1.104e-19 | 0.9872 |
| `irr_2_f150w` | 19,405 (38.8%) | 0 | 2.593e-05 | 1 |
| `bd_2_f150w` | 19,405 (38.8%) | 0 | 0 | 0.9677 |
| `sph_3_f150w` | 19,405 (38.8%) | 0 | 4.606e-21 | 0.9957 |
| `disk_3_f150w` | 19,405 (38.8%) | 0 | 7.337e-16 | 0.9954 |
| `irr_3_f150w` | 19,405 (38.8%) | 0 | 0.00121 | 1 |
| `bd_3_f150w` | 19,405 (38.8%) | 0 | 0 | 0.9672 |
| `sph_4_f150w` | 19,405 (38.8%) | 0 | 5.382e-27 | 0.9966 |
| `disk_4_f150w` | 19,405 (38.8%) | 0 | 9.847e-22 | 0.9867 |
| `irr_4_f150w` | 19,405 (38.8%) | 0 | 0.0005053 | 1 |
| `bd_4_f150w` | 19,405 (38.8%) | 0 | 0 | 0.9833 |
| `sph_5_f150w` | 19,405 (38.8%) | 0 | 4.861e-35 | 0.9979 |
| `disk_5_f150w` | 19,405 (38.8%) | 0 | 3.807e-22 | 0.9987 |
| `irr_5_f150w` | 19,405 (38.8%) | 0 | 4.911e-06 | 1 |
| `bd_5_f150w` | 19,405 (38.8%) | 0 | 0 | 0.9953 |
| `sph_6_f150w` | 19,405 (38.8%) | 0 | 6.219e-20 | 0.9934 |
| `disk_6_f150w` | 19,405 (38.8%) | 0 | 9.904e-17 | 0.9924 |
| `irr_6_f150w` | 19,405 (38.8%) | 0 | 0.0003708 | 1 |
| `bd_6_f150w` | 19,405 (38.8%) | 0 | 0 | 0.9685 |
| `sph_7_f150w` | 19,405 (38.8%) | 0 | 2.663e-29 | 0.9966 |
| `disk_7_f150w` | 19,405 (38.8%) | 0 | 3.098e-25 | 0.9928 |
| ... | (117 more columns with NaNs) | | | |

**Columns with potential sentinel values:**

| Column | Sentinel | Count |
|--------|----------|-------|

**Low-cardinality columns (categorical/flag):**

- `morph_flag_f277w`: [0, 1, 2, 3, 999999]
- `morph_flag_f444w`: [0, 1, 2, 3, 999999]
- `morph_flag_f150w`: [0, 1, 2, 3, 999999]

---

## Extension 6: B+D

**Rows:** 784,016 | **Columns:** 461

### Column Inventory

| Column | FITS Format | Type | Unit |
|--------|-------------|------|------|
| `ra_detec_bd` | D | float64 |  |
| `dec_detec_bd` | D | float64 |  |
| `disk_radius_deg` | D | float64 |  |
| `disk_radius_deg_err` | D | float64 |  |
| `bulge_radius_deg` | D | float64 |  |
| `bulge_radius_deg_err` | D | float64 |  |
| `angle_bd` | D | float64 |  |
| `angle_bd_err` | D | float64 |  |
| `disk_axratio` | D | float64 |  |
| `disk_axratio_err` | D | float64 |  |
| `bulge_axratio` | D | float64 |  |
| `bulge_axratio_err` | D | float64 |  |
| `fmf_b+d_chi2` | D | float64 |  |
| `mag_model_bd_total_f115w` | D | float64 |  |
| `mag_model_bd_total_f150w` | D | float64 |  |
| `mag_model_bd_total_f277w` | D | float64 |  |
| `mag_model_bd_total_f444w` | D | float64 |  |
| `mag_err_model_bd_total_f115w` | D | float64 |  |
| `mag_err_model_bd_total_f150w` | D | float64 |  |
| `mag_err_model_bd_total_f277w` | D | float64 |  |
| `mag_err_model_bd_total_f444w` | D | float64 |  |
| `mag_model_bulge_f115w` | D | float64 |  |
| `mag_model_bulge_f150w` | D | float64 |  |
| `mag_model_bulge_f277w` | D | float64 |  |
| `mag_model_bulge_f444w` | D | float64 |  |
| `mag_err_model_bulge_f115w` | D | float64 |  |
| `mag_err_model_bulge_f150w` | D | float64 |  |
| `mag_err_model_bulge_f277w` | D | float64 |  |
| `mag_err_model_bulge_f444w` | D | float64 |  |
| `mag_model_disk_f115w` | D | float64 |  |
| `mag_model_disk_f150w` | D | float64 |  |
| `mag_model_disk_f277w` | D | float64 |  |
| `mag_model_disk_f444w` | D | float64 |  |
| `mag_err_model_disk_f115w` | D | float64 |  |
| `mag_err_model_disk_f150w` | D | float64 |  |
| `mag_err_model_disk_f277w` | D | float64 |  |
| `mag_err_model_disk_f444w` | D | float64 |  |
| `flux_model_bd_total_f115w` | D | float64 |  |
| `flux_model_bd_total_f150w` | D | float64 |  |
| `flux_model_bd_total_f277w` | D | float64 |  |
| `flux_model_bd_total_f444w` | D | float64 |  |
| `flux_err_model_bd_total_f115w` | D | float64 |  |
| `flux_err_model_bd_total_f150w` | D | float64 |  |
| `flux_err_model_bd_total_f277w` | D | float64 |  |
| `flux_err_model_bd_total_f444w` | D | float64 |  |
| `flux_model_bulge_f115w` | D | float64 |  |
| `flux_model_bulge_f150w` | D | float64 |  |
| `flux_model_bulge_f277w` | D | float64 |  |
| `flux_model_bulge_f444w` | D | float64 |  |
| `flux_err_model_bulge_f115w` | D | float64 |  |
| `flux_err_model_bulge_f150w` | D | float64 |  |
| `flux_err_model_bulge_f277w` | D | float64 |  |
| `flux_err_model_bulge_f444w` | D | float64 |  |
| `flux_model_disk_f115w` | D | float64 |  |
| `flux_model_disk_f150w` | D | float64 |  |
| `flux_model_disk_f277w` | D | float64 |  |
| `flux_model_disk_f444w` | D | float64 |  |
| `flux_err_model_disk_f115w` | D | float64 |  |
| `flux_err_model_disk_f150w` | D | float64 |  |
| `flux_err_model_disk_f277w` | D | float64 |  |
| `flux_err_model_disk_f444w` | D | float64 |  |
| `b/t_f115w` | D | float64 |  |
| `b/t_f150w` | D | float64 |  |
| `b/t_f277w` | D | float64 |  |
| `b/t_f444w` | D | float64 |  |
| `b/t_err_f115w` | D | float64 |  |
| `b/t_err_f150w` | D | float64 |  |
| `b/t_err_f277w` | D | float64 |  |
| `b/t_err_f444w` | D | float64 |  |
| `mag_model_bd_total_hst-f814w` | D | float64 |  |
| `mag_model_bd_total_f770w` | D | float64 |  |
| `mag_model_bd_total_cfht-u` | D | float64 |  |
| `mag_model_bd_total_hsc-g` | D | float64 |  |
| `mag_model_bd_total_hsc-r` | D | float64 |  |
| `mag_model_bd_total_hsc-i` | D | float64 |  |
| `mag_model_bd_total_hsc-z` | D | float64 |  |
| `mag_model_bd_total_hsc-y` | D | float64 |  |
| `mag_model_bd_total_hsc-nb0816` | D | float64 |  |
| `mag_model_bd_total_hsc-nb0921` | D | float64 |  |
| `mag_model_bd_total_hsc-nb1010` | D | float64 |  |
| `mag_model_bd_total_uvista-y` | D | float64 |  |
| `mag_model_bd_total_uvista-j` | D | float64 |  |
| `mag_model_bd_total_uvista-h` | D | float64 |  |
| `mag_model_bd_total_uvista-ks` | D | float64 |  |
| `mag_model_bd_total_sc-ia484` | D | float64 |  |
| `mag_model_bd_total_sc-ia527` | D | float64 |  |
| `mag_model_bd_total_sc-ia624` | D | float64 |  |
| `mag_model_bd_total_sc-ia679` | D | float64 |  |
| `mag_model_bd_total_sc-ia738` | D | float64 |  |
| `mag_model_bd_total_sc-ia767` | D | float64 |  |
| `mag_model_bd_total_sc-ib427` | D | float64 |  |
| `mag_model_bd_total_sc-ib505` | D | float64 |  |
| `mag_model_bd_total_sc-ib574` | D | float64 |  |
| `mag_model_bd_total_sc-ib709` | D | float64 |  |
| `mag_model_bd_total_sc-ib827` | D | float64 |  |
| `mag_model_bd_total_sc-nb711` | D | float64 |  |
| `mag_model_bd_total_sc-nb816` | D | float64 |  |
| `mag_err_model_bd_total_hst-f814w` | D | float64 |  |
| `mag_err_model_bd_total_f770w` | D | float64 |  |
| `mag_err_model_bd_total_cfht-u` | D | float64 |  |
| `mag_err_model_bd_total_hsc-g` | D | float64 |  |
| `mag_err_model_bd_total_hsc-r` | D | float64 |  |
| `mag_err_model_bd_total_hsc-i` | D | float64 |  |
| `mag_err_model_bd_total_hsc-z` | D | float64 |  |
| `mag_err_model_bd_total_hsc-y` | D | float64 |  |
| `mag_err_model_bd_total_hsc-nb0816` | D | float64 |  |
| `mag_err_model_bd_total_hsc-nb0921` | D | float64 |  |
| `mag_err_model_bd_total_hsc-nb1010` | D | float64 |  |
| `mag_err_model_bd_total_uvista-y` | D | float64 |  |
| `mag_err_model_bd_total_uvista-j` | D | float64 |  |
| `mag_err_model_bd_total_uvista-h` | D | float64 |  |
| `mag_err_model_bd_total_uvista-ks` | D | float64 |  |
| `mag_err_model_bd_total_sc-ia484` | D | float64 |  |
| `mag_err_model_bd_total_sc-ia527` | D | float64 |  |
| `mag_err_model_bd_total_sc-ia624` | D | float64 |  |
| `mag_err_model_bd_total_sc-ia679` | D | float64 |  |
| `mag_err_model_bd_total_sc-ia738` | D | float64 |  |
| `mag_err_model_bd_total_sc-ia767` | D | float64 |  |
| `mag_err_model_bd_total_sc-ib427` | D | float64 |  |
| `mag_err_model_bd_total_sc-ib505` | D | float64 |  |
| `mag_err_model_bd_total_sc-ib574` | D | float64 |  |
| `mag_err_model_bd_total_sc-ib709` | D | float64 |  |
| `mag_err_model_bd_total_sc-ib827` | D | float64 |  |
| `mag_err_model_bd_total_sc-nb711` | D | float64 |  |
| `mag_err_model_bd_total_sc-nb816` | D | float64 |  |
| `mag_model_bulge_hst-f814w` | D | float64 |  |
| `mag_model_bulge_f770w` | D | float64 |  |
| `mag_model_bulge_cfht-u` | D | float64 |  |
| `mag_model_bulge_hsc-g` | D | float64 |  |
| `mag_model_bulge_hsc-r` | D | float64 |  |
| `mag_model_bulge_hsc-i` | D | float64 |  |
| `mag_model_bulge_hsc-z` | D | float64 |  |
| `mag_model_bulge_hsc-y` | D | float64 |  |
| `mag_model_bulge_hsc-nb0816` | D | float64 |  |
| `mag_model_bulge_hsc-nb0921` | D | float64 |  |
| `mag_model_bulge_hsc-nb1010` | D | float64 |  |
| `mag_model_bulge_uvista-y` | D | float64 |  |
| `mag_model_bulge_uvista-j` | D | float64 |  |
| `mag_model_bulge_uvista-h` | D | float64 |  |
| `mag_model_bulge_uvista-ks` | D | float64 |  |
| `mag_model_bulge_sc-ia484` | D | float64 |  |
| `mag_model_bulge_sc-ia527` | D | float64 |  |
| `mag_model_bulge_sc-ia624` | D | float64 |  |
| `mag_model_bulge_sc-ia679` | D | float64 |  |
| `mag_model_bulge_sc-ia738` | D | float64 |  |
| `mag_model_bulge_sc-ia767` | D | float64 |  |
| `mag_model_bulge_sc-ib427` | D | float64 |  |
| `mag_model_bulge_sc-ib505` | D | float64 |  |
| `mag_model_bulge_sc-ib574` | D | float64 |  |
| `mag_model_bulge_sc-ib709` | D | float64 |  |
| `mag_model_bulge_sc-ib827` | D | float64 |  |
| `mag_model_bulge_sc-nb711` | D | float64 |  |
| `mag_model_bulge_sc-nb816` | D | float64 |  |
| `mag_err_model_bulge_hst-f814w` | D | float64 |  |
| `mag_err_model_bulge_f770w` | D | float64 |  |
| `mag_err_model_bulge_cfht-u` | D | float64 |  |
| `mag_err_model_bulge_hsc-g` | D | float64 |  |
| `mag_err_model_bulge_hsc-r` | D | float64 |  |
| `mag_err_model_bulge_hsc-i` | D | float64 |  |
| `mag_err_model_bulge_hsc-z` | D | float64 |  |
| `mag_err_model_bulge_hsc-y` | D | float64 |  |
| `mag_err_model_bulge_hsc-nb0816` | D | float64 |  |
| `mag_err_model_bulge_hsc-nb0921` | D | float64 |  |
| `mag_err_model_bulge_hsc-nb1010` | D | float64 |  |
| `mag_err_model_bulge_uvista-y` | D | float64 |  |
| `mag_err_model_bulge_uvista-j` | D | float64 |  |
| `mag_err_model_bulge_uvista-h` | D | float64 |  |
| `mag_err_model_bulge_uvista-ks` | D | float64 |  |
| `mag_err_model_bulge_sc-ia484` | D | float64 |  |
| `mag_err_model_bulge_sc-ia527` | D | float64 |  |
| `mag_err_model_bulge_sc-ia624` | D | float64 |  |
| `mag_err_model_bulge_sc-ia679` | D | float64 |  |
| `mag_err_model_bulge_sc-ia738` | D | float64 |  |
| `mag_err_model_bulge_sc-ia767` | D | float64 |  |
| `mag_err_model_bulge_sc-ib427` | D | float64 |  |
| `mag_err_model_bulge_sc-ib505` | D | float64 |  |
| `mag_err_model_bulge_sc-ib574` | D | float64 |  |
| `mag_err_model_bulge_sc-ib709` | D | float64 |  |
| `mag_err_model_bulge_sc-ib827` | D | float64 |  |
| `mag_err_model_bulge_sc-nb711` | D | float64 |  |
| `mag_err_model_bulge_sc-nb816` | D | float64 |  |
| `mag_model_disk_hst-f814w` | D | float64 |  |
| `mag_model_disk_f770w` | D | float64 |  |
| `mag_model_disk_cfht-u` | D | float64 |  |
| `mag_model_disk_hsc-g` | D | float64 |  |
| `mag_model_disk_hsc-r` | D | float64 |  |
| `mag_model_disk_hsc-i` | D | float64 |  |
| `mag_model_disk_hsc-z` | D | float64 |  |
| `mag_model_disk_hsc-y` | D | float64 |  |
| `mag_model_disk_hsc-nb0816` | D | float64 |  |
| `mag_model_disk_hsc-nb0921` | D | float64 |  |
| `mag_model_disk_hsc-nb1010` | D | float64 |  |
| `mag_model_disk_uvista-y` | D | float64 |  |
| `mag_model_disk_uvista-j` | D | float64 |  |
| `mag_model_disk_uvista-h` | D | float64 |  |
| `mag_model_disk_uvista-ks` | D | float64 |  |
| `mag_model_disk_sc-ia484` | D | float64 |  |
| `mag_model_disk_sc-ia527` | D | float64 |  |
| `mag_model_disk_sc-ia624` | D | float64 |  |
| `mag_model_disk_sc-ia679` | D | float64 |  |
| `mag_model_disk_sc-ia738` | D | float64 |  |
| `mag_model_disk_sc-ia767` | D | float64 |  |
| `mag_model_disk_sc-ib427` | D | float64 |  |
| `mag_model_disk_sc-ib505` | D | float64 |  |
| `mag_model_disk_sc-ib574` | D | float64 |  |
| `mag_model_disk_sc-ib709` | D | float64 |  |
| `mag_model_disk_sc-ib827` | D | float64 |  |
| `mag_model_disk_sc-nb711` | D | float64 |  |
| `mag_model_disk_sc-nb816` | D | float64 |  |
| `mag_err_model_disk_hst-f814w` | D | float64 |  |
| `mag_err_model_disk_f770w` | D | float64 |  |
| `mag_err_model_disk_cfht-u` | D | float64 |  |
| `mag_err_model_disk_hsc-g` | D | float64 |  |
| `mag_err_model_disk_hsc-r` | D | float64 |  |
| `mag_err_model_disk_hsc-i` | D | float64 |  |
| `mag_err_model_disk_hsc-z` | D | float64 |  |
| `mag_err_model_disk_hsc-y` | D | float64 |  |
| `mag_err_model_disk_hsc-nb0816` | D | float64 |  |
| `mag_err_model_disk_hsc-nb0921` | D | float64 |  |
| `mag_err_model_disk_hsc-nb1010` | D | float64 |  |
| `mag_err_model_disk_uvista-y` | D | float64 |  |
| `mag_err_model_disk_uvista-j` | D | float64 |  |
| `mag_err_model_disk_uvista-h` | D | float64 |  |
| `mag_err_model_disk_uvista-ks` | D | float64 |  |
| `mag_err_model_disk_sc-ia484` | D | float64 |  |
| `mag_err_model_disk_sc-ia527` | D | float64 |  |
| `mag_err_model_disk_sc-ia624` | D | float64 |  |
| `mag_err_model_disk_sc-ia679` | D | float64 |  |
| `mag_err_model_disk_sc-ia738` | D | float64 |  |
| `mag_err_model_disk_sc-ia767` | D | float64 |  |
| `mag_err_model_disk_sc-ib427` | D | float64 |  |
| `mag_err_model_disk_sc-ib505` | D | float64 |  |
| `mag_err_model_disk_sc-ib574` | D | float64 |  |
| `mag_err_model_disk_sc-ib709` | D | float64 |  |
| `mag_err_model_disk_sc-ib827` | D | float64 |  |
| `mag_err_model_disk_sc-nb711` | D | float64 |  |
| `mag_err_model_disk_sc-nb816` | D | float64 |  |
| `flux_model_bd_total_hst-f814w` | D | float64 |  |
| `flux_model_bd_total_f770w` | D | float64 |  |
| `flux_model_bd_total_cfht-u` | D | float64 |  |
| `flux_model_bd_total_hsc-g` | D | float64 |  |
| `flux_model_bd_total_hsc-r` | D | float64 |  |
| `flux_model_bd_total_hsc-i` | D | float64 |  |
| `flux_model_bd_total_hsc-z` | D | float64 |  |
| `flux_model_bd_total_hsc-y` | D | float64 |  |
| `flux_model_bd_total_hsc-nb0816` | D | float64 |  |
| `flux_model_bd_total_hsc-nb0921` | D | float64 |  |
| `flux_model_bd_total_hsc-nb1010` | D | float64 |  |
| `flux_model_bd_total_uvista-y` | D | float64 |  |
| `flux_model_bd_total_uvista-j` | D | float64 |  |
| `flux_model_bd_total_uvista-h` | D | float64 |  |
| `flux_model_bd_total_uvista-ks` | D | float64 |  |
| `flux_model_bd_total_sc-ia484` | D | float64 |  |
| `flux_model_bd_total_sc-ia527` | D | float64 |  |
| `flux_model_bd_total_sc-ia624` | D | float64 |  |
| `flux_model_bd_total_sc-ia679` | D | float64 |  |
| `flux_model_bd_total_sc-ia738` | D | float64 |  |
| `flux_model_bd_total_sc-ia767` | D | float64 |  |
| `flux_model_bd_total_sc-ib427` | D | float64 |  |
| `flux_model_bd_total_sc-ib505` | D | float64 |  |
| `flux_model_bd_total_sc-ib574` | D | float64 |  |
| `flux_model_bd_total_sc-ib709` | D | float64 |  |
| `flux_model_bd_total_sc-ib827` | D | float64 |  |
| `flux_model_bd_total_sc-nb711` | D | float64 |  |
| `flux_model_bd_total_sc-nb816` | D | float64 |  |
| `flux_err_model_bd_total_hst-f814w` | D | float64 |  |
| `flux_err_model_bd_total_f770w` | D | float64 |  |
| `flux_err_model_bd_total_cfht-u` | D | float64 |  |
| `flux_err_model_bd_total_hsc-g` | D | float64 |  |
| `flux_err_model_bd_total_hsc-r` | D | float64 |  |
| `flux_err_model_bd_total_hsc-i` | D | float64 |  |
| `flux_err_model_bd_total_hsc-z` | D | float64 |  |
| `flux_err_model_bd_total_hsc-y` | D | float64 |  |
| `flux_err_model_bd_total_hsc-nb0816` | D | float64 |  |
| `flux_err_model_bd_total_hsc-nb0921` | D | float64 |  |
| `flux_err_model_bd_total_hsc-nb1010` | D | float64 |  |
| `flux_err_model_bd_total_uvista-y` | D | float64 |  |
| `flux_err_model_bd_total_uvista-j` | D | float64 |  |
| `flux_err_model_bd_total_uvista-h` | D | float64 |  |
| `flux_err_model_bd_total_uvista-ks` | D | float64 |  |
| `flux_err_model_bd_total_sc-ia484` | D | float64 |  |
| `flux_err_model_bd_total_sc-ia527` | D | float64 |  |
| `flux_err_model_bd_total_sc-ia624` | D | float64 |  |
| `flux_err_model_bd_total_sc-ia679` | D | float64 |  |
| `flux_err_model_bd_total_sc-ia738` | D | float64 |  |
| `flux_err_model_bd_total_sc-ia767` | D | float64 |  |
| `flux_err_model_bd_total_sc-ib427` | D | float64 |  |
| `flux_err_model_bd_total_sc-ib505` | D | float64 |  |
| `flux_err_model_bd_total_sc-ib574` | D | float64 |  |
| `flux_err_model_bd_total_sc-ib709` | D | float64 |  |
| `flux_err_model_bd_total_sc-ib827` | D | float64 |  |
| `flux_err_model_bd_total_sc-nb711` | D | float64 |  |
| `flux_err_model_bd_total_sc-nb816` | D | float64 |  |
| `flux_model_bulge_hst-f814w` | D | float64 |  |
| `flux_model_bulge_f770w` | D | float64 |  |
| `flux_model_bulge_cfht-u` | D | float64 |  |
| `flux_model_bulge_hsc-g` | D | float64 |  |
| `flux_model_bulge_hsc-r` | D | float64 |  |
| `flux_model_bulge_hsc-i` | D | float64 |  |
| `flux_model_bulge_hsc-z` | D | float64 |  |
| `flux_model_bulge_hsc-y` | D | float64 |  |
| `flux_model_bulge_hsc-nb0816` | D | float64 |  |
| `flux_model_bulge_hsc-nb0921` | D | float64 |  |
| `flux_model_bulge_hsc-nb1010` | D | float64 |  |
| `flux_model_bulge_uvista-y` | D | float64 |  |
| `flux_model_bulge_uvista-j` | D | float64 |  |
| `flux_model_bulge_uvista-h` | D | float64 |  |
| `flux_model_bulge_uvista-ks` | D | float64 |  |
| `flux_model_bulge_sc-ia484` | D | float64 |  |
| `flux_model_bulge_sc-ia527` | D | float64 |  |
| `flux_model_bulge_sc-ia624` | D | float64 |  |
| `flux_model_bulge_sc-ia679` | D | float64 |  |
| `flux_model_bulge_sc-ia738` | D | float64 |  |
| `flux_model_bulge_sc-ia767` | D | float64 |  |
| `flux_model_bulge_sc-ib427` | D | float64 |  |
| `flux_model_bulge_sc-ib505` | D | float64 |  |
| `flux_model_bulge_sc-ib574` | D | float64 |  |
| `flux_model_bulge_sc-ib709` | D | float64 |  |
| `flux_model_bulge_sc-ib827` | D | float64 |  |
| `flux_model_bulge_sc-nb711` | D | float64 |  |
| `flux_model_bulge_sc-nb816` | D | float64 |  |
| `flux_err_model_bulge_hst-f814w` | D | float64 |  |
| `flux_err_model_bulge_f770w` | D | float64 |  |
| `flux_err_model_bulge_cfht-u` | D | float64 |  |
| `flux_err_model_bulge_hsc-g` | D | float64 |  |
| `flux_err_model_bulge_hsc-r` | D | float64 |  |
| `flux_err_model_bulge_hsc-i` | D | float64 |  |
| `flux_err_model_bulge_hsc-z` | D | float64 |  |
| `flux_err_model_bulge_hsc-y` | D | float64 |  |
| `flux_err_model_bulge_hsc-nb0816` | D | float64 |  |
| `flux_err_model_bulge_hsc-nb0921` | D | float64 |  |
| `flux_err_model_bulge_hsc-nb1010` | D | float64 |  |
| `flux_err_model_bulge_uvista-y` | D | float64 |  |
| `flux_err_model_bulge_uvista-j` | D | float64 |  |
| `flux_err_model_bulge_uvista-h` | D | float64 |  |
| `flux_err_model_bulge_uvista-ks` | D | float64 |  |
| `flux_err_model_bulge_sc-ia484` | D | float64 |  |
| `flux_err_model_bulge_sc-ia527` | D | float64 |  |
| `flux_err_model_bulge_sc-ia624` | D | float64 |  |
| `flux_err_model_bulge_sc-ia679` | D | float64 |  |
| `flux_err_model_bulge_sc-ia738` | D | float64 |  |
| `flux_err_model_bulge_sc-ia767` | D | float64 |  |
| `flux_err_model_bulge_sc-ib427` | D | float64 |  |
| `flux_err_model_bulge_sc-ib505` | D | float64 |  |
| `flux_err_model_bulge_sc-ib574` | D | float64 |  |
| `flux_err_model_bulge_sc-ib709` | D | float64 |  |
| `flux_err_model_bulge_sc-ib827` | D | float64 |  |
| `flux_err_model_bulge_sc-nb711` | D | float64 |  |
| `flux_err_model_bulge_sc-nb816` | D | float64 |  |
| `flux_model_disk_hst-f814w` | D | float64 |  |
| `flux_model_disk_f770w` | D | float64 |  |
| `flux_model_disk_cfht-u` | D | float64 |  |
| `flux_model_disk_hsc-g` | D | float64 |  |
| `flux_model_disk_hsc-r` | D | float64 |  |
| `flux_model_disk_hsc-i` | D | float64 |  |
| `flux_model_disk_hsc-z` | D | float64 |  |
| `flux_model_disk_hsc-y` | D | float64 |  |
| `flux_model_disk_hsc-nb0816` | D | float64 |  |
| `flux_model_disk_hsc-nb0921` | D | float64 |  |
| `flux_model_disk_hsc-nb1010` | D | float64 |  |
| `flux_model_disk_uvista-y` | D | float64 |  |
| `flux_model_disk_uvista-j` | D | float64 |  |
| `flux_model_disk_uvista-h` | D | float64 |  |
| `flux_model_disk_uvista-ks` | D | float64 |  |
| `flux_model_disk_sc-ia484` | D | float64 |  |
| `flux_model_disk_sc-ia527` | D | float64 |  |
| `flux_model_disk_sc-ia624` | D | float64 |  |
| `flux_model_disk_sc-ia679` | D | float64 |  |
| `flux_model_disk_sc-ia738` | D | float64 |  |
| `flux_model_disk_sc-ia767` | D | float64 |  |
| `flux_model_disk_sc-ib427` | D | float64 |  |
| `flux_model_disk_sc-ib505` | D | float64 |  |
| `flux_model_disk_sc-ib574` | D | float64 |  |
| `flux_model_disk_sc-ib709` | D | float64 |  |
| `flux_model_disk_sc-ib827` | D | float64 |  |
| `flux_model_disk_sc-nb711` | D | float64 |  |
| `flux_model_disk_sc-nb816` | D | float64 |  |
| `flux_err_model_disk_hst-f814w` | D | float64 |  |
| `flux_err_model_disk_f770w` | D | float64 |  |
| `flux_err_model_disk_cfht-u` | D | float64 |  |
| `flux_err_model_disk_hsc-g` | D | float64 |  |
| `flux_err_model_disk_hsc-r` | D | float64 |  |
| `flux_err_model_disk_hsc-i` | D | float64 |  |
| `flux_err_model_disk_hsc-z` | D | float64 |  |
| `flux_err_model_disk_hsc-y` | D | float64 |  |
| `flux_err_model_disk_hsc-nb0816` | D | float64 |  |
| `flux_err_model_disk_hsc-nb0921` | D | float64 |  |
| `flux_err_model_disk_hsc-nb1010` | D | float64 |  |
| `flux_err_model_disk_uvista-y` | D | float64 |  |
| `flux_err_model_disk_uvista-j` | D | float64 |  |
| `flux_err_model_disk_uvista-h` | D | float64 |  |
| `flux_err_model_disk_uvista-ks` | D | float64 |  |
| `flux_err_model_disk_sc-ia484` | D | float64 |  |
| `flux_err_model_disk_sc-ia527` | D | float64 |  |
| `flux_err_model_disk_sc-ia624` | D | float64 |  |
| `flux_err_model_disk_sc-ia679` | D | float64 |  |
| `flux_err_model_disk_sc-ia738` | D | float64 |  |
| `flux_err_model_disk_sc-ia767` | D | float64 |  |
| `flux_err_model_disk_sc-ib427` | D | float64 |  |
| `flux_err_model_disk_sc-ib505` | D | float64 |  |
| `flux_err_model_disk_sc-ib574` | D | float64 |  |
| `flux_err_model_disk_sc-ib709` | D | float64 |  |
| `flux_err_model_disk_sc-ib827` | D | float64 |  |
| `flux_err_model_disk_sc-nb711` | D | float64 |  |
| `flux_err_model_disk_sc-nb816` | D | float64 |  |
| `b/t_hst-f814w` | D | float64 |  |
| `b/t_f770w` | D | float64 |  |
| `b/t_cfht-u` | D | float64 |  |
| `b/t_hsc-g` | D | float64 |  |
| `b/t_hsc-r` | D | float64 |  |
| `b/t_hsc-i` | D | float64 |  |
| `b/t_hsc-z` | D | float64 |  |
| `b/t_hsc-y` | D | float64 |  |
| `b/t_hsc-nb0816` | D | float64 |  |
| `b/t_hsc-nb0921` | D | float64 |  |
| `b/t_hsc-nb1010` | D | float64 |  |
| `b/t_uvista-y` | D | float64 |  |
| `b/t_uvista-j` | D | float64 |  |
| `b/t_uvista-h` | D | float64 |  |
| `b/t_uvista-ks` | D | float64 |  |
| `b/t_sc-ia484` | D | float64 |  |
| `b/t_sc-ia527` | D | float64 |  |
| `b/t_sc-ia624` | D | float64 |  |
| `b/t_sc-ia679` | D | float64 |  |
| `b/t_sc-ia738` | D | float64 |  |
| `b/t_sc-ia767` | D | float64 |  |
| `b/t_sc-ib427` | D | float64 |  |
| `b/t_sc-ib505` | D | float64 |  |
| `b/t_sc-ib574` | D | float64 |  |
| `b/t_sc-ib709` | D | float64 |  |
| `b/t_sc-ib827` | D | float64 |  |
| `b/t_sc-nb711` | D | float64 |  |
| `b/t_sc-nb816` | D | float64 |  |
| `b/t_err_hst-f814w` | D | float64 |  |
| `b/t_err_f770w` | D | float64 |  |
| `b/t_err_cfht-u` | D | float64 |  |
| `b/t_err_hsc-g` | D | float64 |  |
| `b/t_err_hsc-r` | D | float64 |  |
| `b/t_err_hsc-i` | D | float64 |  |
| `b/t_err_hsc-z` | D | float64 |  |
| `b/t_err_hsc-y` | D | float64 |  |
| `b/t_err_hsc-nb0816` | D | float64 |  |
| `b/t_err_hsc-nb0921` | D | float64 |  |
| `b/t_err_hsc-nb1010` | D | float64 |  |
| `b/t_err_uvista-y` | D | float64 |  |
| `b/t_err_uvista-j` | D | float64 |  |
| `b/t_err_uvista-h` | D | float64 |  |
| `b/t_err_uvista-ks` | D | float64 |  |
| `b/t_err_sc-ia484` | D | float64 |  |
| `b/t_err_sc-ia527` | D | float64 |  |
| `b/t_err_sc-ia624` | D | float64 |  |
| `b/t_err_sc-ia679` | D | float64 |  |
| `b/t_err_sc-ia738` | D | float64 |  |
| `b/t_err_sc-ia767` | D | float64 |  |
| `b/t_err_sc-ib427` | D | float64 |  |
| `b/t_err_sc-ib505` | D | float64 |  |
| `b/t_err_sc-ib574` | D | float64 |  |
| `b/t_err_sc-ib709` | D | float64 |  |
| `b/t_err_sc-ib827` | D | float64 |  |
| `b/t_err_sc-nb711` | D | float64 |  |
| `b/t_err_sc-nb816` | D | float64 |  |

### Sample Statistics

Based on first 50,000 of 784,016 rows.

**Columns with NaN values:**

| Column | NaN count | Inf count | Min | Max |
|--------|-----------|-----------|-----|-----|
| `b/t_err_hsc-g` | 709 (1.4%) | 0 | 0 | 3.574 |
| `b/t_err_cfht-u` | 638 (1.3%) | 0 | 0 | 5.889 |
| `b/t_err_uvista-y` | 628 (1.3%) | 0 | -0 | 5.414 |
| `bulge_radius_deg_err` | 576 (1.2%) | 0 | 3.149e-17 | 0.00312 |
| `bulge_axratio_err` | 576 (1.2%) | 0 | 1.762e-10 | 130.8 |
| `b/t_err_hsc-i` | 538 (1.1%) | 0 | 0 | 32.32 |
| `b/t_err_hsc-r` | 535 (1.1%) | 0 | 0 | 5.237 |
| `b/t_err_uvista-j` | 535 (1.1%) | 0 | -0 | 15.58 |
| `b/t_err_hst-f814w` | 509 (1.0%) | 0 | 0 | 12.35 |
| `b/t_err_uvista-h` | 481 (1.0%) | 0 | 0 | 10.53 |
| `b/t_err_sc-ia624` | 465 (0.9%) | 0 | 0 | 4.838 |
| `b/t_err_sc-ia527` | 393 (0.8%) | 0 | 0 | 5.124 |
| `b/t_err_uvista-ks` | 372 (0.7%) | 0 | -0 | 8.331 |
| `b/t_err_sc-ia484` | 370 (0.7%) | 0 | 0 | 4.822 |
| `disk_radius_deg_err` | 336 (0.7%) | 0 | 6.268e-15 | 0.001638 |
| `angle_bd_err` | 336 (0.7%) | 0 | 7.358e-05 | 1.662e+08 |
| `disk_axratio_err` | 336 (0.7%) | 0 | 8.542e-11 | 5.205 |
| `b/t_err_hsc-z` | 288 (0.6%) | 0 | 0 | 6.432 |
| `b/t_err_f770w` | 282 (0.6%) | 0 | 0 | 15.7 |
| `b/t_err_sc-ia738` | 272 (0.5%) | 0 | 0 | 5.515 |
| `b/t_err_hsc-nb0816` | 178 (0.4%) | 0 | 0 | 6.402 |
| `b/t_err_hsc-y` | 176 (0.4%) | 0 | 0 | 6.511 |
| `b/t_err_f115w` | 159 (0.3%) | 0 | -0 | 2.803 |
| `b/t_err_hsc-nb0921` | 156 (0.3%) | 0 | 0 | 13.14 |
| `b/t_err_sc-ib505` | 132 (0.3%) | 0 | 0 | 5.09 |
| `b/t_err_f150w` | 119 (0.2%) | 0 | 0 | 2.482 |
| `b/t_err_sc-ia679` | 114 (0.2%) | 0 | 0 | 6.029 |
| `b/t_err_sc-ib427` | 110 (0.2%) | 0 | 0 | 5.177 |
| `b/t_err_f277w` | 89 (0.2%) | 0 | 0 | 4.111 |
| `b/t_err_sc-ia767` | 80 (0.2%) | 0 | 0 | 6.044 |
| ... | (5 more columns with NaNs) | | | |

**Columns with potential sentinel values:**

| Column | Sentinel | Count |
|--------|----------|-------|
| `mag_err_model_bd_total_f115w` | -999.0 | 678 (1.4%) |
| `mag_err_model_bd_total_f277w` | -999.0 | 564 (1.1%) |
| `mag_err_model_bd_total_f444w` | -999.0 | 796 (1.6%) |
| `mag_err_model_bulge_f115w` | -999.0 | 1,493 (3.0%) |
| `mag_err_model_bulge_f150w` | -999.0 | 952 (1.9%) |
| `mag_err_model_bulge_f277w` | -999.0 | 1,444 (2.9%) |
| `mag_err_model_bulge_f444w` | -999.0 | 1,840 (3.7%) |
| `mag_err_model_disk_f115w` | -999.0 | 1,066 (2.1%) |
| `mag_err_model_disk_f150w` | -999.0 | 721 (1.4%) |
| `mag_err_model_disk_f277w` | -999.0 | 945 (1.9%) |
| `mag_err_model_disk_f444w` | -999.0 | 1,282 (2.6%) |
| `b/t_err_f277w` | 0.0 | 629 (1.3%) |
| `b/t_err_f444w` | 0.0 | 902 (1.8%) |
| `mag_err_model_bd_total_hst-f814w` | -999.0 | 1,722 (3.4%) |
| `mag_err_model_bd_total_hst-f814w` | 0.0 | 5,476 (11.0%) |
| `mag_err_model_bd_total_f770w` | -999.0 | 3,218 (6.4%) |
| `mag_err_model_bd_total_f770w` | 0.0 | 2,371 (4.7%) |
| `mag_err_model_bd_total_cfht-u` | -999.0 | 7,229 (14.5%) |
| `mag_err_model_bd_total_cfht-u` | 0.0 | 5,574 (11.1%) |

---

*Generated by profile_master_catalog.py*