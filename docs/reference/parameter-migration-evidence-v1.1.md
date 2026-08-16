<!--
---
title: "Parameter Migration Evidence (v1 → v1.1)"
description: "Value-level comparison of CIGALE and LePhare physical parameters between the live v1 tables and the v1.1 holdings"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-16"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: sed-fitting
  - domain: cosmos-web
related_documents:
  - "[v1 to v1.1 Delta](v1-to-v11-delta.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# Parameter Migration Evidence (v1 → v1.1)

Did v1.1 recompute the physical parameters, or only photometry? Answered by values, not changelogs. Generator: `src/inspection/param_migration_evidence.py` (run 2026-08-16 under `doppler run`; seed 20260815). Sample: 60,000 source IDs drawn from the 784,016 common to the v1.1 files and the live v1 tables; join on source ID; joined rows = 60,000 = sample size for every comparison (join asserted, not assumed). Tile groups: B5/B9/B10 (8,479 rows) vs all others (51,521 rows), tile from the master PHOTOMETRY extension. CIGALE deltas are relative (linear values); LePhare deltas are absolute (log10 values).

---

## 1. CIGALE — fully recomputed

Exact-match fraction **0.000000 on every column, in both tile groups**. Not one of 42,186 joined comparisons (5,112 + 37,074 valid rows) reproduced the v1 value bitwise.

| Column | Group | Match frac | Median rel. delta | \|rel\|>10% | \|rel\|>50% |
|--------|-------|-----------:|------------------:|------------:|------------:|
| mass | B5/B9/B10 | 0.000000 | −6.3×10⁻² | 63.0% | 9.3% |
| mass | others | 0.000000 | −5.6×10⁻² | 63.9% | 10.6% |
| sfr_inst | B5/B9/B10 | 0.000000 | +3.2×10⁻¹ | 91.1% | 57.0% |
| sfr_inst | others | 0.000000 | +2.9×10⁻¹ | 91.1% | 56.1% |
| sfr_100myr | B5/B9/B10 | 0.000000 | +4.3×10⁻² | 79.5% | 25.5% |
| sfr_100myr | others | 0.000000 | +4.9×10⁻² | 80.1% | 26.5% |
| chi2_red_best_fit | B5/B9/B10 | 0.000000 | +9.5×10⁻¹ | 94.0% | 71.5% |
| chi2_red_best_fit | others | 0.000000 | +9.7×10⁻¹ | 94.7% | 72.6% |

**Conclusion (both tile groups): CHANGED.** CIGALE physical parameters were recomputed for v1.1 — median mass shifts ~6%, instantaneous SFR ~30%, and reduced chi2 nearly doubles (median +95%). Any downstream tension metric computed against v1 CIGALE values is stale. The recomputation is field-wide: hot-tile and other-tile distributions are statistically indistinguishable.

## 2. LePhare — recomputed with small medians, heavy tails, intermediate exact-match fractions

| Column | Group | Match frac | Median Δ | p1 / p99 | \|Δ\|>0.1 |
|--------|-------|-----------:|---------:|----------:|----------:|
| zfinal | B5/B9/B10 | **0.029122** | +0.000000 | −1.071 / +0.273 | 8.0% |
| zfinal | others | **0.026480** | +0.000000 | −0.746 / +0.426 | 8.2% |
| mass_med | B5/B9/B10 | **0.009694** | +0.001290 dex | −0.865 / +0.327 | 12.0% |
| mass_med | others | **0.009619** | +0.001790 dex | −0.632 / +0.403 | 11.4% |
| sfr_med | B5/B9/B10 | **0.013359** | −0.000160 dex | −1.792 / +0.467 | 18.6% |
| sfr_med | others | **0.013065** | +0.000000 dex | −1.345 / +0.700 | 18.7% |

**Intermediate-match-fraction finding (rule applied, stated in advance):** every LePhare match fraction (~0.010–0.029) is neither approximately 0 nor approximately 1 and is therefore its own finding — the rerun leaves 1–3% of sources bitwise identical while the rest move; it is never averaged into a summary.

**Conclusion (both tile groups): CHANGED.** LePhare was rerun for v1.1: 92% of photo-z moves are <0.1 and medians sit at ~0, but 8% of zfinal, 11–12% of mass_med, and ~19% of sfr_med move by more than 0.1 (dex or z). Changes are **not concentrated in B5/B9/B10** — hot-tile and other-tile tail fractions agree to ~0.5 percentage points on every column.

## 3. Consequence for ETL v2

The v1 database cannot serve as a value baseline for either code's parameters after the rebuild; every cross-code product (`tension_scalars`, `v_analysis_sample`) must be recomputed from v1.1 inputs. This is input to readiness findings F2 (CIGALE recomputed) and F3 (LePhare changes field-wide, not tile-concentrated).
