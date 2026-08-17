<!--
---
title: "Data Manifest v1.1"
description: "SHA-256 pin of the COSMOS-Web v1.1 holdings and the spec-z compilation checkout"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.1"
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

Provenance anchor for the v1.1 rebuild. Machine layer: [data-manifest-v1.1.csv](data-manifest-v1.1.csv) (184 rows: SHA-256, bytes, mtime UTC per file). Builder: `src/inspection/build_data_manifest.py` (read-only against the roots). Originally generated 2026-08-16T03:32:50Z; amended 2026-08-17 by spec P2R-02, which re-pinned the seven speczcompilation LFS rows after materialization (§2). **Nothing under either hashed root may change after this point; a single modified byte unpins every downstream artifact.**

---

## 1. Provenance Roots

| # | Root | Location | Files | Bytes | Role |
|---|------|----------|------:|------:|------|
| 1 | NVMe v1.1 holdings | `/mnt/nvme01/cosmos-web-dr1-catalog` | 103 | 130,197,210,900 | Hashed here; raw and immutable |
| 2 | speczcompilation checkout | `/opt/agents/repos/reference-files/speczcompilation` | 81 | 1,546,861,535 | Hashed here; git HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0` |
| 3 | CIGALE SEDs (external) | host `vps3557752`, path `/opt/agents/repos/cosmosweb2025-data/CIGALE_SEDs_v1/` |, | ~175 GB | **Off-box; recorded by name only, not hashed** |

Row-count verification (manifest vs filesystem, run 2026-08-16, **pre-materialization state**):

```
find /mnt/nvme01/cosmos-web-dr1-catalog -type f | wc -l   → 103
find /opt/agents/repos/reference-files/speczcompilation -type f | wc -l → 81
manifest rows: 184 = 103 + 81
```

Amendment 2026-08-17: the speczcompilation filesystem now counts 103 files. All 22 additions and both modified files are git machinery under `.git/` (see §2, "Materialization side effects"); the 81 hashed worktree-and-repo files are unchanged except the seven re-pinned rows, and manifest rows remain 184.

Re-hash verification: three randomly chosen files (seed 20260815) re-hashed and compared against the manifest, `cosmos_web_starmask_jwst_B1.fits`, `COSMOSWeb_mastercatalog_v1.1_ml_morph.fits`, `logo/cosmos-logo-light.png`, all three reproduce the recorded SHA-256 and byte size exactly. Amendment re-verification (seed 20260817): three randomly chosen rows from the 177 untouched by the re-pin (`pack-8d499080....pack`, `COSMOSWeb_mastercatalog_v1.1_photom_primary.fits`, `detection_images/detection_chi2pos_SWLW_A7.fits`) all reproduce their recorded SHA-256 and byte size.

---

## 2. LFS Materialization Status (finding F-LFS, resolved 2026-08-17)

The speczcompilation checkout's `.gitattributes` LFS-tracks `*.fits` and `*.pkl`. **All seven LFS-pattern files are materialized data as of 2026-08-17T01:38–01:42Z**, after the operator installed git-lfs (3.4.1) on ML01 and fetched content. At manifest time 2026-08-16T03:32:50Z they were 133–134 byte pointer files, and the original seven CSV rows hashed those pointers; those rows were re-pinned on 2026-08-17 under spec P2R-02. **The other 177 rows carry their original P2R-01 pin of 2026-08-16T03:32:50Z and were not re-hashed.**

Pointer-versus-content reconciliation (spec P2R-02 gate 2.2): for each of the seven files, the SHA-256 of the materialized content equals the `oid sha256:` declared by the pointer blob committed at pinned HEAD `1924f5d0ee6c221b820035c8d3cd7302c02532b0`, and the byte count equals the pointer's declared size — 7/7 agree on both. The materialized bytes are therefore the bytes the pinned commit declared, not merely files of plausible size.

| File | SHA-256 (content, verified = pointer oid) | Bytes |
|------|-------------------------------------------|------:|
| `specz_compilation/specz_compilation_COSMOS_DR1.1_unique.fits` | `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99` | 70,223,040 |
| `specz_compilation/specz_compilation_COSMOS_DR1.1_all.fits` | `30675493d98014b23900d41fbcdd6157f5fc64962be22755a6077658d3068fd3` | 129,343,680 |
| `sed_fitting/cigale/cigale_results_specz_compilation_DR1.1.fits` | `43bd6bb671b972ba45c3ad3eed5280e51cbfafcdb5446afc4051f939dae37710` | 309,882,240 |
| `sed_fitting/lephare/lephare_results_specz_compilation_DR1.1.fits` | `555487d5ce682b39fc6e77b5918e474abbee6802b86ff1f4eafa5090c47dd1b3` | 49,271,040 |
| `soms/trained_som_lowz_i_band_26.0_magnitude_limit.pkl` | `2784dd9a10cca1e6f271a26c5a9f8a94b397ca8f94cae98d0055cc9021f12b28` | 359,235,918 |
| `soms/trained_som_midz_i_band_26.0_magnitude_limit.pkl` | `4e3f9c0393b8351fb468214f5ceac609d029d4556c167446f150657ffbd62296` | 359,533,902 |
| `soms/trained_som_highz_i_band_26.0_magnitude_limit.pkl` | `c1ded80b0cccfb17e8f8fb70645c4a348c4581cc588564612f64586caeb6b052` | 24,265,414 |

With content materialized, `astropy.io.fits.open` succeeds: `specz_compilation_COSMOS_DR1.1_unique.fits` carries a 261,975-row binary table and `_all.fits` a 482,579-row binary table. The earlier on-box blocker (row count "not obtainable", pointer instead of FITS) is resolved.

**Tag-versus-HEAD provenance.** The checkout carries a tag `DR1.1`, which in this clone resolves as a lightweight ref to commit `a634a9ed5c1c17ea2629b2326e4dc99f235d8027`, dated 2025-10-31T01:50:32Z ("finalized DR1.1 for release. 138 total programs included in this release"). The manifest pins HEAD `1924f5d0`, which sits **two commits past the tag**; both intervening commits (`1c40d27` DOI badge in README, `1924f5d` SFR typo fix in the CIGALE README) touch no LFS-tracked path, so the seven data files are identical at tag and pinned HEAD. Whether the manifest should pin the tag rather than the branch tip is an open operator question, noted in spec P2R-02 for the record.

**Materialization side effects (finding, recorded not absorbed).** P2R-01 hashed 29 files under the checkout's `.git/` alongside the 52 worktree files. The materialization event necessarily mutated git machinery, and a full re-hash of all 74 non-re-pinned root-2 rows (2026-08-17, this spec) shows exactly two drifted rows, both bookkeeping: `.git/config` (git-lfs filter section) and `.git/index` (smudge checkout). Neither is data; both retain their P2R-01 pin in the CSV by this spec's freeze (exactly seven rows change), so a future whole-root re-hash will report these two as mismatches — that is this recorded finding, not corruption. Additionally 22 unmanifested files now exist under `.git/` (7 `.git/lfs/objects/<oid>` content-store files — one per materialized file, each named by the verified oid — plus 11 `.git/lfs/tmp/*` transfer temporaries and 4 `git lfs install` hooks). Every worktree data file outside the seven is byte-identical to its P2R-01 pin.

**Naming caution.** The compilation's data files are named `..._COSMOS_DR1.1_...`: that `DR1.1` is the spectroscopic compilation's own release version and is **unrelated to COSMOS-Web v1.1**. Two different "1.1" versions appear on adjacent manifest rows; do not conflate them.

---

## 3. Holdings Shape (top-level)

103 files: 10 master/per-extension catalog FITS + AGN-DESI cross-id FITS, PDFz pickle, LePhare SEDs HDF5, 20 JWST star-mask FITS + 1 DS9 region file, 20 detection images + README, arXiv paper source (LaTeX + 29 figures), column-description text, flag-construction PNG, flowchart PNG, LSS supplement (catalog + readme), group supplements (groups, memberships).

Disk-hygiene observations recorded for the operator (no action taken; raw root is immutable): none, the holdings directory contains no redundant archives or stray downloads at manifest time.
