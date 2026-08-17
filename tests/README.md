<!--
---
title: "Manifest Validator Tests"
description: "Discriminating tests for the v1.1 data manifest contract (spec P2R-02c gate A3.1)"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "2.0"
status: "Active"
tags:
  - type: documentation
  - domain: testing
related_documents:
  - "[Data Manifest v1.1](../docs/reference/data-manifest-v1.1.md)"
  - "[Builder](../src/inspection/build_data_manifest.py)"
---
-->

# Manifest Validator Tests

`test_build_data_manifest.py` proves the manifest machine contract in two layers.

## Isolated fixture tests

A passing temporary control (small root + its exact manifest) is mutated one
property at a time; each test asserts a nonzero exit and the named diagnostic:

| Mutation | Diagnostic |
|----------|------------|
| Missing header | `Header mismatch` |
| Renamed header field | `Header mismatch` |
| Reordered header | `Header mismatch` |
| Duplicate key | `Duplicate key` |
| Added `.git/config` row | `Git-internal path` |
| Manifest-only row missing on disk | `Manifest row missing on disk` |
| Disk-only file | `Disk file missing from manifest` |
| Hash-only drift | `Hash mismatch` (only) |
| Size-only drift | `Size mismatch` (only) |
| Mtime-only drift | `Mtime mismatch` (only) |

## Production tests

- The committed CSV is byte-for-byte the serialized `0f3e31d` baseline minus
  its 29 `.git/**` records (CRLF convention, order, and final newline included).
- Structure: exact ordered header, 155 data rows, 103 root-1 / 52 root-2,
  unique `(root, relative_path)` keys, zero `.git/**` paths.
- Full read-only production verify over both configured roots (integration;
  hashes ~131 GB, allow several minutes).

## Running

```bash
pytest tests/test_build_data_manifest.py -v              # full suite
python src/inspection/build_data_manifest.py --verify    # production verify
python src/inspection/build_data_manifest.py --verify \
  --csv <csv> --root <dir> [--root <dir>:git]            # isolated target
```
