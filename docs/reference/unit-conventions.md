<!--
---
title: "Unit Conventions"
description: "Log10 vs linear space conventions for LePhare and CIGALE physical parameters"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: sed-fitting
  - tech: postgresql
related_documents:
  - "[Project State](../project-state.md)"
  - "[Tension Diagnostic Report](../phase2-tension-diagnostic-report.md)"
---
-->

# Unit Conventions

The two SED-fitting codes report physical parameters in different spaces. Every cross-code comparison in this project must apply the conversion below; a comparison that skips it is wrong by the full dynamic range of the linear values, not by a tolerance.

---

## 1. Parameter Spaces

| Code | Parameters | Space | Examples |
|------|-----------|-------|----------|
| LePhare | `mass_med`, `sfr_med`, `ssfr_med` (and their l68/u68 quantiles) | **log10** | `mass_med = 9.63` means 10^9.63 solar masses |
| CIGALE | `mass`, `sfr_inst`, `sfr_100myr`, `ssfr_cigale` (and `*_err`) | **linear** | `mass = 4.3e9` solar masses |

`ssfr_cigale` was derived at extraction (linear SFR / linear mass); it is NULL when the derivation is undefined.

---

## 2. Cross-Code Comparison Formula

The canonical delta between the two codes, in dex:

`delta = lephare_log10_value - LOG10(cigale_linear_value)`

In SQL (`LOG` is `log10` in PostgreSQL):

```sql
l.mass_med - LOG(c.mass)              AS delta_log_mass
l.sfr_med - LOG(c.sfr_100myr)         AS delta_log_sfr_100
l.sfr_med - LOG(c.sfr_inst)           AS delta_log_sfr_inst
```

Positive delta means LePhare reports the larger value.

---

## 3. Error Propagation to Log Space

CIGALE errors are linear. To propagate into dex:

`sigma_log = err / (val * ln(10))`  with `ln(10) = 2.302585`

LePhare quantile widths are already in dex: `sigma = (u68 - l68) / 2`.

Guard rules (implemented in `src/features/compute_tension_scalars.py`):

- Zero, negative, or NULL errors yield NULL sigmas, never infinite pulls.
- Exact-zero CIGALE SFR makes `LOG10(SFR)` undefined; the analysis sample gates on `sfr_inst > 0 AND sfr_100myr > 0` rather than manufacturing infinite tension. This gate is also the source of the censoring effect on the SFR tension ranking (see project state, section 1).

---

## 4. Systematic Floors

Tension metrics add a systematic floor in quadrature: `sigma_sys_mass = 0.1` dex, `sigma_sys_sfr = 0.2` dex (calibration starting points from Pacifici et al. 2023; the May diagnostic run found them adequate for bulk distributions).

Full column-by-column unit reference for the v1 load: `docs/verification-report.md`.
