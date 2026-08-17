<!--
---
title: "CIGALE SED Subtree Digest"
description: "Aggregate pin for the cigale-seds/ subtree, the declared out-of-boundary region of manifest root 1"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Data Manifest v1.1](data-manifest-v1.1.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# CIGALE SED Subtree Digest

Machine layer: [data-manifest-v1.1-cigale-seds.csv](data-manifest-v1.1-cigale-seds.csv), one row, fixed seven-field contract.

`/mnt/nvme01/cosmos-web-dr1-catalog/cigale-seds/` holds 1,185,322 per-source best-model SED files. They are pinned here by aggregate digest rather than by per-file rows in `data-manifest-v1.1.csv`.

## Why an aggregate rather than per-file rows

Per-file rows for this subtree made the tracked manifest a 192 MB file. That is not a reviewable provenance anchor: it cannot be read in a diff, it exceeds GitHub's 100 MB object limit, and it buries the 155-row catalog boundary that every downstream unit actually validates against inside a million lines of lookup-asset bookkeeping. The manifest form was designed when the boundary was 155 files and was carried unchanged through a four-order-of-magnitude expansion.

The aggregate keeps the property that matters. Any change to any SED file, its size, or its mtime changes `rows_sha256`. What is lost is per-file localization, which regenerating against the full listing recovers in one command.

## The pin

| Field | Value |
|---|---|
| Subtree | `cigale-seds/` under `/mnt/nvme01/cosmos-web-dr1-catalog` |
| Files | 1,185,322 (P1 1,154,766; P2 30,556) |
| Bytes | 468,554,723,694 |
| Row-block SHA-256 | `ff3cefd0b0086ad4a6ff861430c371cdfdd065df2c64ef338e4029e7c65b9810` |
| Full per-file listing | `/mnt/nvme01/cosmos-web-dr1-catalog-manifest/data-manifest-v1.1-full.csv` |
| Full listing SHA-256 | `7eef8f1198ddb61a2c5aaa57fe9dd0bcaa0401cd97f9e434cb0f146645ff7fa9` |

`rows_sha256` is taken over the SED rows exactly as `build_data_manifest.py` serialized them, sorted under the C collation. It is not a hash of file contents; it is a hash of the per-file pins, each of which is a content hash.

## Reproducing the digest

The full listing is the P2R-02c manifest as committed at `b4d24bf`, before the subtree was lifted out of the tracked CSV. It is the authority for per-file lookup; the two commands below are the exact ones that produced the values above.

```bash
FULL=/mnt/nvme01/cosmos-web-dr1-catalog-manifest/data-manifest-v1.1-full.csv

sha256sum $FULL
awk -F, 'NR>1 && $2 ~ /^cigale-seds\//' $FULL | LC_ALL=C sort | sha256sum
awk -F, 'NR>1 && $2 ~ /^cigale-seds\//' $FULL | wc -l
awk -F, 'NR>1 && $2 ~ /^cigale-seds\// {s+=$4} END {print s}' $FULL
```

The `awk` output preserves the source CRLF line endings, so the digest is over `\r`-terminated records. Reproducing it with lines stripped of `\r` yields a different value.

## Boundary status

`cigale-seds` is named in `EXCLUDED_SUBTREES` in `src/inspection/build_data_manifest.py`. The builder does not walk it, and the validator rejects any manifest row under it while skipping it on the disk side, the same treatment `.git/**` receives under P2R-02a. Membership in that set is a provenance decision: adding a name removes those files from the per-file pin.

The subtree is a manifested lookup asset for per-source triage after candidate selection. It is not inside any relational ingest boundary; P2R-03 mirrors eleven relational sources and neither reads nor loads these files.

## Recovery

If the full listing is lost, the per-file pins are not recoverable from this document; regenerating them from disk produces a new pin taken at a new time, which is a different claim. The listing is held on NVMe beside the data it describes and is covered by whatever backup policy covers that volume. Its own SHA-256 above is what detects tampering.
