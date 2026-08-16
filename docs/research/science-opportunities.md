<!--
---
title: "Science Opportunities"
description: "Selected analysis targets for the anomaly detection program: O1 algorithmic disagreement and O5 contextual anomalies"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: report
  - domain: anomaly-detection
  - domain: astronomy
related_documents:
  - "[Project State](../project-state.md)"
  - "[Unit Conventions](reference/unit-conventions.md)"
---
-->

# Science Opportunities

The two selected analysis targets from the five GDR-identified opportunities, with the rationale and the deprioritization record. This document is a frozen input to the T_A v2 design unit; the restart does not reopen the selection.

---

## 1. O1, Algorithmic Disagreement (Lead paper)

LePhare vs CIGALE residuals for stellar mass and SFR. Objects with Δlog(M*) > 0.3 dex or Δlog(SFR) > 0.5 dex signal physically distinct populations:

- Line imposters: extreme emission line galaxies whose photometry fools one code's continuum assumptions.
- Obscured AGN: central engine flux contaminating one code's galaxy-only SED library.
- Dusty decoupling: decoupled UV/IR star formation where the IR-informed code sees what the UV-only fit cannot.

Why lead: pure catalog operations, least scoopable, dual-code framing genuinely novel for COSMOS-Web.

---

## 2. O5, Contextual Anomalies

Environmental outliers found by cross-referencing galaxy properties against the LSS density maps:

- Cluster starbursts: massive star-forming galaxies in the highest-density peaks.
- Void quenched: low-mass passive galaxies in voids.

Pairs naturally with O1: objects anomalous in BOTH dimensions are "super-anomalies." Depends on the LSS overdensity supplement and its version alignment with the v1.1 photo-z recompute (a readiness-review question, not an assumption).

---

## 3. Deprioritized

| Opportunity | Reason |
|-------------|--------|
| O2, Morphological Imposters | Enrichment only; dust degeneracy trap |
| O3, Low-Delta Uncertainty | Secondary analysis |
| O4, Green Peas | Too close to dropout searches; scoopable |
