<!--
---
title: "Worklog: P2R-04A Evidence-Layer Correction"
description: "RED regression coverage for the P2R-04 evidence-layer defects"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: testing
  - domain: spectroscopy
related_documents:
  - "docs/research/specz-linkage-evidence.md"
---
-->

# Worklog: P2R-04A Evidence-Layer Correction

## Summary

| Attribute | Value |
|-----------|-------|
| Status | In progress |
| Gate | A1.1 RED |
| Branch | `task/4-specz-linkage-correction` |
| Base | `04b42e16faacbd2388979d9c608d54db26118a50` |

Objective: establish deterministic regression tests for the P2R-04 evidence
layer before changing either generator.

## Gate checkpoints

### Gate A1.1: Reproduce both evidence defects

Added in-memory regression fixtures for the Gate 4.1 verifier and Gate 4.7
characterizer. D1 is attributed to executor deviation: the verifier uses
catalog identifier arithmetic when it must find the catalog source carrying
the stored link. D2 is attributed to executor deviation: the rendered
confidence distribution does not establish complete category coverage or a
reconciled population total. Focused RED command and output are recorded
after execution. No generator, report, database object, or parent worklog was
changed.

Focused RED command:

```bash
pytest tests/test_specz_linkage_evidence_regressions.py -v
```

Observed result: `4 failed in 0.40s`, intentionally. D1 reports `link 20
must pair with stored-link carrier catalog source 10 (ra=0.0), not catalog
source 20 (ra=10.0)` and observes `36000.0 == 0.0`; its row-permutation
fixture changes the defective-path result from 36,000 to 108,000 arcsec. D2
reports that observed category `85` is absent from rendered `{50, 97}` and
that its bucket total `2` does not equal rendered stated total `3`. The
separately present assertion confirms rendered stated total `3` equals the
independently counted population `3`.
