<!--
---
title: "Data Manifest v1.1"
description: "SHA-256 pin of the COSMOS-Web v1.1 holdings and the spec-z compilation checkout"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.4"
status: "Active"
tags:
  - type: reference
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Project State](../project-state.md)"
  - "[CIGALE SED Subtree Digest](data-manifest-v1.1-cigale-seds.md)"
  - "[v1.1 Structural Profile](master-catalog-profile-v1.1.md)"
  - "[v1.1 Readiness Review](../research/v11-readiness-review.md)"
---
-->

# Data Manifest v1.1

Provenance anchor for the v1.1 rebuild. Machine layer: [data-manifest-v1.1.csv](data-manifest-v1.1.csv) (155 rows: SHA-256, bytes, mtime UTC per file). Builder: `src/inspection/build_data_manifest.py` (read-only against the roots). Generated 2026-08-16T03:32:50Z; amended 2026-08-17 by spec P2R-02A to exclude mutable Git internals and establish a durable worktree-only boundary; the CIGALE SED subtree was pinned into root 1 by P2R-02C under operator disposition and then lifted back out by P2R-02D, which pins it by aggregate digest in [data-manifest-v1.1-cigale-seds.md](data-manifest-v1.1-cigale-seds.md) rather than per-file rows. The tracked CSV is byte-identical to the `0f3e31d` baseline minus its 29 `.git/**` records, in original order and serialization. **Nothing under either hashed root may change after this point; a single modified byte unpins every downstream artifact.**

---

## 1. Provenance Roots

| # | Root | Location | Files | Bytes | Role |
|---|------|----------|------:|------:|------|
| 1 | NVMe v1.1 holdings | `/mnt/nvme01/cosmos-web-dr1-catalog` | 103 | 130,197,210,900 | Hashed here per file; raw and immutable. Excludes the `cigale-seds/` subtree, which is a declared out-of-boundary region pinned by aggregate digest |
| 2 | speczcompilation checkout | `/opt/agents/repos/reference-files/speczcompilation` | 52 | 1,465,763,774 | Hashed here; worktree-only boundary excludes `.git/**`, git HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0` |
| 3 | CIGALE SED subtree | `/mnt/nvme01/cosmos-web-dr1-catalog/cigale-seds/` (P1: 1,154,766 files; P2: 30,556 files) | 1,185,322 | 468,554,723,694 | Local since 2026-08-16 19:42 EDT. Pinned by aggregate digest, not per-file rows; see [data-manifest-v1.1-cigale-seds.md](data-manifest-v1.1-cigale-seds.md) |

Row-count verification (manifest vs filesystem, run 2026-08-16, **P2R-01**):

```
find /mnt/nvme01/cosmos-web-dr1-catalog -type f | wc -l   → 103
find /opt/agents/repos/reference-files/speczcompilation -type f ! -path '*/.git/*' | wc -l   → 52
manifest rows: 155 = 103 + 52
```

Row-count verification (manifest vs filesystem, run 2026-08-17, **P2R-02D**):

```
find /mnt/nvme01/cosmos-web-dr1-catalog -type f ! -path '*/cigale-seds/*' | wc -l   → 103
find /opt/agents/repos/reference-files/speczcompilation -type f ! -path '*/.git/*' | wc -l   → 52
manifest rows: 155 = 103 + 52
baseline proof: committed CSV is byte-identical to the 0f3e31d baseline
minus its 29 .git/** records (order and CRLF preserved)
cigale-seds/ subtree: 1,185,322 files pinned by aggregate digest
```

Amendment 2026-08-17 (P2R-02A): provenance boundary corrected to worktree-only by excluding `.git/**` from the speczcompilation hash set. The mutable Git transport layer (config, index, hooks, LFS store, temporaries) is outside the manifest; the manifest records worktree artifacts and the Git commit SHA, not repository internals. All 52 worktree files were freshly hash-verified against disk at amendment gate A1.1 and match the CSV rows.

Amendment 2026-08-17 (P2R-02C): the CIGALE SED store — recorded off-box and un-hashed at P2R-01 time because it had not yet been downloaded — was staged into `/mnt/nvme01/cosmos-web-dr1-catalog/cigale-seds/` at 2026-08-16 19:42 EDT, completing the dataset on disk. The operator dispositioned pinning it into root 1 rather than recording it as a named un-hashed subtree. 1,185,322 SED rows were added by the same deterministic builder walk, and the discriminating full verifier passed with zero mismatch over the complete boundary.

Amendment 2026-08-17 (P2R-02D): those per-file rows made the tracked CSV a 192 MB artifact, past GitHub's 100 MB object limit and past what a reviewable provenance anchor should be. The subtree was lifted back out and pinned by aggregate digest instead; the tracked CSV returns to the 155-row catalog boundary and is now byte-identical to the `0f3e31d` baseline minus its 29 `.git/**` records, verified by `cmp` rather than asserted. The per-file pins are preserved intact in the full listing on NVMe, whose own SHA-256 and row-block digest are recorded in [data-manifest-v1.1-cigale-seds.md](data-manifest-v1.1-cigale-seds.md). No file was re-hashed and no pin was retaken: the SED rows in the digest are the same bytes P2R-02C computed.

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

**CIGALE SED subtree (2026-08-17, P2R-02C pin, P2R-02D digest).** The SED store (per-source best-model SEDs used for per-source lookup after candidate triage) was recorded at P2R-01 as off-box on `vps3557752`, un-hashed, because the ~200+ GB download had not completed. It was staged into the NVMe root at 2026-08-16 19:42 EDT (subtree mtimes preserve the 2025-04-14 source timestamps), landing after the 2026-08-16T03:32:50Z pin. P2R-02C hashed all 1,185,322 files under operator disposition; P2R-02D moved those rows out of the tracked CSV into an aggregate digest without recomputing them. Root 1's per-file boundary is the 103 catalog files; the subtree is pinned separately and is a declared exclusion in the builder and validator.

**Naming caution.** The compilation's data files are named `..._COSMOS_DR1.1_...`: that `DR1.1` is the spectroscopic compilation's own release version and is **unrelated to COSMOS-Web v1.1**. Two different "1.1" versions appear on adjacent manifest rows; do not conflate them.

---

## 3. Holdings Shape (top-level)

35 root-level files: 10 master/per-extension catalog FITS + AGN-DESI cross-id FITS, PDFz pickle, LePhare SEDs HDF5, 20 JWST star-mask FITS + 1 DS9 region file, column-description text, flag-construction PNG, flowchart PNG. Plus subdirectories: 20 detection images + README, arXiv paper source (LaTeX + 29 figures), LSS supplement (catalog + readme), group supplements (groups, memberships), and the `cigale-seds/` subtree (P1 + P2 per-source SED FITS), which is pinned by aggregate digest rather than per-file rows.

Disk-hygiene observations recorded for the operator (no action taken; raw root is immutable): none beyond the SED staging event recorded in §2 — the holdings directory contains no redundant archives or stray downloads at manifest time.
