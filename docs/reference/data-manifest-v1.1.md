<!--
---
title: "Data Manifest v1.1"
description: "SHA-256 pin of the COSMOS-Web v1.1 holdings and the spec-z compilation checkout"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.2"
status: "Active"
tags:
  - type: reference
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Project State](../project-state.md)"
  - "[v1.1 Structural Profile](master-catalog-profile-v1.1.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# Data Manifest v1.1

Provenance anchor for the v1.1 rebuild. Machine layer: [data-manifest-v1.1.csv](data-manifest-v1.1.csv) (155 rows: SHA-256, bytes, mtime UTC per file). Builder: `src/inspection/build_data_manifest.py` (read-only against the roots). Generated 2026-08-16T03:32:50Z; amended 2026-08-17 by spec P2R-02A to exclude mutable Git internals and establish a durable worktree-only boundary. **Nothing under either hashed root may change after this point; a single modified byte unpins every downstream artifact.**

---

## 1. Provenance Roots

| # | Root | Location | Files | Bytes | Role |
|---|------|----------|------:|------:|------|
| 1 | NVMe v1.1 holdings | `/mnt/nvme01/cosmos-web-dr1-catalog` | 103 | 130,197,210,900 | Hashed here; raw and immutable |
| 2 | speczcompilation checkout | `/opt/agents/repos/reference-files/speczcompilation` | 52 | 1,465,763,774 | Hashed here; worktree-only boundary excludes `.git/**`, git HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0` |
| 3 | CIGALE SEDs (external) | host `vps3557752`, path `/opt/agents/repos/cosmosweb2025-data/CIGALE_SEDs_v1/` |, | ~175 GB | **Off-box; recorded by name only, not hashed** |

Row-count verification (manifest vs filesystem, run 2026-08-16, **P2R-01**):

```
find /mnt/nvme01/cosmos-web-dr1-catalog -type f | wc -l   → 103
find /opt/agents/repos/reference-files/speczcompilation -type f ! -path '*/.git/*' | wc -l   → 52
manifest rows: 155 = 103 + 52
```

Amendment 2026-08-17 (P2R-02A): provenance boundary corrected to worktree-only by excluding `.git/**` from the speczcompilation hash set. The mutable Git transport layer (config, index, hooks, LFS store, temporaries) is outside the manifest; the manifest records worktree artifacts and the Git commit SHA, not repository internals. All 52 worktree files were freshly hash-verified against disk at amendment gate A1.1 and match the CSV rows.

---

## 2. Provenance Boundary and Repository Pin

**Durable boundary:** the manifest records worktree artifacts and the Git commit SHA, not mutable repository internals. The `.git` directory is excluded because it is transport machinery (config, index, object database, LFS store, hooks) that a `git checkout` necessarily mutates; it is not a data artifact. Every path declared in the CSV must reproduce its pin against the live filesystem; the validator rejects any row containing `/.git/` or starting `.git/`.

**Approved repository pin:** HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0`. The checkout carries a lightweight release ref `DR1.1` (object type `commit`, no tag object) pointing at commit `a634a9ed5c1c17ea2629b2326e4dc99f235d8027`, dated 2025-10-31T01:50:32Z ("finalized DR1.1 for release. 138 total programs included in this release"). HEAD sits two commits past the tag; both intervening commits (`1c40d27` "Update DOI badge in README.md" and `1924f5d` "Fix typo in SFR parameter description within README for Cigale results") touch no LFS-tracked path, so the seven LFS objects are identical at tag and pinned HEAD. The operator disposition (spec amendment 2026-08-17) is to retain the HEAD pin rather than retarget to the tag; both commits record the same data.

**LFS materialization and pointer-content reconciliation (2026-08-17T01:38–01:42Z).** The operator installed git-lfs (3.4.1) on ML01 and fetched content. For each of the seven LFS-pattern files, the SHA-256 of the materialized content equals the `oid sha256:` declared by the pointer blob at pinned HEAD `1924f5d0`, and the byte count equals the pointer's declared size — 7/7 on both. The manifest rows are content pins validated by that reconciliation:

| File | SHA-256 (content = pointer oid at `1924f5d0`) | Bytes |
|------|-------------------------------------------|------:|
| `specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99` | 70,223,040 |
| `specz_compilation/specz_compilation_COSMOS_DR1.1_all.fits` | `30675493d98014b23900d41fbcdd6157f5fc64962be22755a6077658d3068fd3` | 129,343,680 |
| `sed_fitting/cigale/cigale_results_specz_compilation_DR1.1.fits` | `43bd6bb671b972ba45c3ad3eed5280e51cbfafcdb5446afc4051f939dae37710` | 309,882,240 |
| `sed_fitting/lephare/lephare_results_specz_compilation_DR1.1.fits` | `555487d5ce682b39fc6e77b5918e474abbee6802b86ff1f4eafa5090c47dd1b3` | 49,271,040 |
| `soms/trained_som_lowz_i_band_26.0_magnitude_limit.pkl` | `2784dd9a10cca1e6f271a26c5a9f8a94b397ca8f94cae98d0055cc9021f12b28` | 359,235,918 |
| `soms/trained_som_midz_i_band_26.0_magnitude_limit.pkl` | `4e3f9c0393b8351fb468214f5ceac609d029d4556c167446f150657ffbd62296` | 359,533,902 |
| `soms/trained_som_highz_i_band_26.0_magnitude_limit.pkl` | `c1ded80b0cccfb17e8f8fb70645c4a348c4581cc588564612f64586caeb6b052` | 24,265,414 |

With content materialized, `astropy.io.fits.open` succeeds: `specz_compilation_COSMOS_DR1.1_unique.fits` carries a 261,975-row binary table and `_all.fits` a 482,579-row binary table.

**Naming caution.** The compilation's data files are named `..._COSMOS_DR1.1_...`: that `DR1.1` is the spectroscopic compilation's own release version and is **unrelated to COSMOS-Web v1.1**. Two different "1.1" versions appear on adjacent manifest rows; do not conflate them.

---

## 3. Holdings Shape (top-level)

103 files: 10 master/per-extension catalog FITS + AGN-DESI cross-id FITS, PDFz pickle, LePhare SEDs HDF5, 20 JWST star-mask FITS + 1 DS9 region file, 20 detection images + README, arXiv paper source (LaTeX + 29 figures), column-description text, flag-construction PNG, flowchart PNG, LSS supplement (catalog + readme), group supplements (groups, memberships).

Disk-hygiene observations recorded for the operator (no action taken; raw root is immutable): none, the holdings directory contains no redundant archives or stray downloads at manifest time.
