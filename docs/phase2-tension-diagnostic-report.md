# Phase 2 Tension Scalar Diagnostic Report

Generated: 2026-05-02T01:01:36.552805+00:00

Sigma systematics used for this run:
- Mass: 0.100 dex
- SFR: 0.200 dex

## A. Sample Attrition

| Stage | Sources | Catalog Survival |
|---|---:|---:|
| Total catalog | 784,016 | 100.00% |
| After Gate 1: catalog security | 595,889 | 76.00% |
| After Gates 1+2: convergence | 578,667 | 73.81% |
| After Gates 1+2+3: physical plausibility | 553,830 | 70.64% |
| After all four gates | 553,830 | 70.64% |

## B. Pull Distribution Analysis

| Scalar | Count | Mean | Median | Std | Skewness | Excess Kurtosis | Min | Max | abs(T) > 2 | abs(T) > 3 | abs(T) > 5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t_mass | 553,830 | -1.001 | -0.921 | 0.875 | -2.114 | 15.358 | -20.351 | 6.668 | 7.71% | 2.79% | 0.67% |
| t_sfr_100 | 553,830 | 0.302 | 0.356 | 0.980 | -3.982 | 127.182 | -36.457 | 19.428 | 3.98% | 1.51% | 0.35% |
| t_sfr_inst | 553,830 | 0.578 | 0.251 | 1.384 | 0.311 | 28.192 | -40.003 | 20.357 | 13.66% | 6.13% | 1.08% |

Interpretation: if the bulk distribution is well-calibrated, the standard deviation should be near 1.0 and the mean near 0.0. Heavy tails (excess kurtosis) confirm survival of anomalous populations. If the standard deviation is substantially greater than 1.0, sigma_sys is too low. If substantially less, sigma_sys is too high.

## C. Tension vs Chi2 Decoupling Check

| Pair | Pearson r |
|---|---:|
| abs(t_mass) vs chi2_red_cig | 0.185 |
| abs(t_sfr_100) vs chi2_red_cig | 0.298 |

Interpretation: if correlation is strong (|r| > 0.3), the systematic floor is insufficient and tension is tracking fit quality rather than physical disagreement. This would indicate sigma_sys needs to be increased.

## D. SFR Timescale Stability

| Diagnostic | Value |
|---|---:|
| Pearson r: t_sfr_inst vs t_sfr_100 | 0.475 |
| Sign mismatch count | 152,615 |
| Top 1000 by abs(t_sfr_inst) not in top 1000 by abs(t_sfr_100) | 377 |

Interpretation: high instability suggests instantaneous SFR artifacts; t_sfr_100 should be the primary scalar for downstream anomaly detection.

## E. Zombie Leakage Verification

| Diagnostic | Value |
|---|---:|
| Min LOG10(CIGALE mass) | 6.000 |
| Max LOG10(CIGALE mass) | 14.562 |
| Min LePhare mass_med | 6.000 |
| Max LePhare mass_med | 12.599 |
| Sources with abs(delta_log_mass) > 3.0 dex | 1,128 |

## F. F770W Coverage and Quiescent Context

- F770W coverage: 194,052 / 553,830 (35.04%)
- LePhare quiescent: 15,672 / 553,830 (2.83%)

| Population | Count | Percentage | Median abs(t_sfr_100) |
|---|---:|---:|---:|
| Quiescent with F770W | 6,536 | 1.18% | 0.548 |
| Quiescent without F770W | 9,136 | 1.65% | 0.498 |
| Star-forming with F770W | 187,516 | 33.86% | 0.453 |
| Star-forming without F770W | 350,642 | 63.31% | 0.442 |
