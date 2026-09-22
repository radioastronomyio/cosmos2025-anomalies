<!--
---
title: "P-06 Frozen Tile Map"
description: "The frozen source-level partition map for P2R-05 with its canonical digest; assigned before any fitting, tuning, or photo-z outcome analysis"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.0"
status: "Active - frozen"
tags:
  - type: reference
  - domain: astronomy
  - tech: python
related_documents:
  - "[P2R-05 README](README.md)"
---
-->

# P-06 Frozen Tile Map

Algorithm: SHA-256 over UTF-8 `cosmos2025-p2r05-spatial-v1|<tile>`
(no trailing newline); labels sorted by full hexadecimal digest, ties
broken by tile string; first four holdout, next four validation,
remaining twelve development. Native production tile domain: all 20
documented labels observed, zero unassigned sources.

Canonical digest (`tile=assignment` lines, sorted tiles):

`c6406d37e32e4b5cfeb89fc91cda0eb9ed4abf0a192d8c5ab7e56fb893635937`

| Tile | Partition |
|---|---|
| A1 | holdout |
| A10 | validation |
| A2 | development |
| A3 | validation |
| A4 | development |
| A5 | development |
| A6 | development |
| A7 | holdout |
| A8 | development |
| A9 | development |
| B1 | validation |
| B10 | development |
| B2 | development |
| B3 | holdout |
| B4 | development |
| B5 | validation |
| B6 | development |
| B7 | holdout |
| B8 | development |
| B9 | development |

These are 4/4/12 of tiles (20/20/60 percent of tiles), not promises
about source counts. Observed source counts: development 476,137,
validation 147,721, holdout 160,158, unassigned 0. Survey and
confidence balance are diagnostics only; the salt may not be re-rolled
and tiles may not be moved to improve balance or outcome metrics.
