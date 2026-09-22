<!--
---
title: "Upstream Incompatibility Report Draft (Local, Unsent)"
description: "Reproducible local report of the release mismatch between the held COSMOS-Web DR1 photometric catalog and the held DR1.1 spec-z compilation, with the renumbering hypothesis explicitly unconfirmed; prepared for operator review, not transmitted"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.0"
status: "Draft - Local Only; Transmission Prohibited Until S5-Q05"
tags:
  - type: research
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Spec-z Linkage Evidence](../specz-linkage-evidence.md)"
  - "[P2R-05 Review](review.md)"
---
-->

# Draft Report: `id_specz_khostovan25` does not address the held DR1.1
spec-z compilation's identifier namespace

**Status: LOCAL DRAFT — NOT SENT.** Transmission through any channel is
prohibited until the operator answers S5-Q05. This document makes no
external contact.

## Releases in question (exact pins)

| Artifact | Pin |
|---|---|
| Photometric catalog | COSMOS-Web DR1 v1.1, `COSMOSWeb_mastercatalog_v1.1.fits` photometry-primary extension (held under `/mnt/nvme01/cosmos-web-dr1-catalog/`, SHA-256 pinned in `docs/reference/data-manifest-v1.1.csv`) |
| Spec-z compilation | Khostovan et al. (2025) compilation, DR1.1, git checkout at `/opt/agents/repos/reference-files/speczcompilation`, files `specz_compilation_COSMOS_DR1.1_unique.fits` (SHA-256 `6ffd1145...`) and `specz_compilation_COSMOS_DR1.1_all.fits` (SHA-256 `30675493...`; full digests in the manifest) |

## Claimed correspondence

The catalog column description for `id_specz_khostovan25` (upstream
detailed column descriptions, section 1, line 36; description hash pinned
in the repository dictionary) reads: "Unique ID of the source
corresponding to the Id_specz of the Khostovan et al. (2025) spec-z
compilation. -999 if no specz match".

## Measured behavior (corrected query definitions)

All queries associate compilation rows through the compilation's own
`Id_COSMOS25` crossmatch into `photometry_primary.id` and treat
`Id_specz` strictly as a compilation-entry identifier (identifier lookup
with uniqueness and membership checks, never row position).

- The catalog column does not resolve against the held compilation's
  `Id_specz` namespace except coincidentally: 24,364 of 37,219 distinct
  non-sentinel values occur in the galaxy-level `Id_specz` set; 12,855 do
  not. Stored values span 223–165,312 against a compilation `Id_specz`
  range of 1–487,666 (33.85 percent of the range; no value exceeds the
  maximum).
- The geometry is field-scale, not a crossmatch. Pairing each of the
  37,219 linked catalog sources' `photometry_primary.ra/dec` with the
  carried link's measurement-level `ra_corrected/dec_corrected` entry
  gives median separation **4,054.3415558937 arcsec** (p90 5,956.72",
  max 9,085.02").
- For contrast, the compilation's own crossmatch is exact: stored
  `ra_COSMOS25`/`dec_COSMOS25` equal `photometry_primary.ra/dec` at the
  row named by `Id_COSMOS25` (min/median/p90/p99/max separation
  0.00013"/0.0840"/0.2322"/0.6381"/0.9983" over 92,359 measurement rows;
  sub-arcsecond astrometric matches).

Reproduction (repository root):

```
python src/features/specz_science/verify.py   # defective-path median on the documented basis
python src/etl/verify_specz_linkage_v11.py    # sealed P2R-04 gate 4.1 evidence command
```

## Working hypothesis (explicitly unconfirmed)

The stored value range is consistent with the column having been populated
against an **earlier release of the compilation whose `Id_specz` values
were renumbered** for DR1.1. We hold no artifact defining such a mapping
and cannot test this hypothesis locally; only upstream can confirm the
release lineage. Until confirmed, "renumbering" remains a hypothesis, not
a finding.

## Suggested question for upstream

Can you confirm which compilation release `id_specz_khostovan25` was
populated against, and whether an `Id_specz` mapping between that release
and DR1.1 exists? If not, we recommend the DR1.1 column description note
that the field does not address the current compilation release.

## What we did locally (no upstream action implied)

The repository mirrors the column as shipped with a semantic note and a
database comment recording the non-resolution; all spec-z association for
the P2R-05 product uses `Id_COSMOS25` into `photometry_primary.id`. No
repair, rematch, or renumbering inference was performed.
