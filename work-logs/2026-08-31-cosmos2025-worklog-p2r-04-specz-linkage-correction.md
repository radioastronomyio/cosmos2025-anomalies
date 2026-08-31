<!--
---
title: "Worklog: Spec-z Linkage Correction and Measurement-Level Mirror (P2R-04)"
description: "Mirrors the measurement-level spec-z compilation, corrects the catalog-to-compilation join path, annotates the defective upstream identifier, and characterizes recovery populations and selection bias"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: astronomy
  - domain: data-engineering
related_documents:
  - "spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md"
  - "docs/research/specz-linkage-evidence.md"
  - "docs/research/etl-v2-verification.md"
---
-->

---
title: "Worklog: Spec-z Linkage Correction and Measurement-Level Mirror (P2R-04)"
description: "Mirrors the measurement-level spec-z compilation, corrects the join path, annotates the defective identifier, characterizes recovery populations"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: [astronomy, data-engineering]
# --- Runtime Context (required) ---
agent: glm
runtime: Kilo CLI
runtime_version: unreported
model: kilo/zai-coding/glm-5.3
hostname: ml01
spec_ref: spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md
repo: cosmos2025-anomalies
category: astronomy
duration_seconds: null
# --- Token Usage and Cost ---
token_usage_source: "unavailable"
tokens_total:
tokens_input:
tokens_cached:
tokens_output:
tokens_reasoning:
cost_basis:
cost_usd:
priced_date:
# --- Linkage ---
related_documents:
  - "docs/research/specz-linkage-evidence.md"
  - "docs/research/etl-v2-verification.md"
---

# Worklog: Spec-z Linkage Correction and Measurement-Level Mirror (P2R-04)

## Startup preflight (spec-startup)

Skill resolution: lifecycle skills resolved from
`/opt/agents/repos/local-agent-skills/skills/` (`spec-startup`, `spec-closeout`);
`spec-closeout` carries the ML01 identity (astronomy-coding-bot co-author
trailer, `/opt/agents/repos/work-logs/work-registry.csv` registry path).

Environment observed at startup, not authored:

| Item | Observed value |
|------|----------------|
| Shared venv | `/opt/agents/venv/bin/python` (Python 3.12.3), auto-active |
| Packages | astropy 7.2.0, psycopg2 2.9.11, numpy 2.4.3, PyYAML present |
| Doppler scope in use | `ml01/dev`, read from `configs/data_paths.yaml` and confirmed live; this spec names no config (SD-056 in P2R-03 corrected an authored `prd`) |
| Admin variable names | `PGSQL01_HOST`, `PGSQL01_PORT`, `PGSQL01_ADMIN_USER`, `PGSQL01_ADMIN_PASSWORD` (from `configs/data_paths.yaml`) |

Spec startup prerequisites:

| Prerequisite | Result |
|---|---|
| `main` contains P2R-03 merge | Pass: `e65242a` "merge P2R-03: ETL v2 lossless mirror of COSMOS-Web v1.1" |
| `spec/2026-08/` holds three archived specs | Pass: P2R-01, P2R-02, P2R-03 |
| `cosmos2025_v11.source` twelve relations, counts equal `source.provenance` | Pass: 11 mirrors + `provenance`; all eleven live counts equal provenance `loaded_rows` |
| `docs/research/etl-v2-verification.md` present | Pass |
| speczcompilation checkout clean at pinned HEAD | Pass: worktree clean at `1924f5d0ee6c221b820035c8d3cd7302c02532b0` |
| `..._all.fits` manifest row freshly reproduced | Pass: SHA-256 `30675493d98014b23900d41fbcdd6157f5fc64962be22755a6077658d3068fd3`, 129,343,680 bytes |
| `..._unique.fits` manifest row freshly reproduced | Pass: SHA-256 `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99`, 70,223,040 bytes |

Principal preflight: the connecting identity is `clusteradmin_pg01`, which is
exactly the role named in the single `source`-schema default-privilege entry
(`cosmos2025_v11_ro=r/clusteradmin_pg01`). New tables created by this identity
inherit the analyst SELECT grant; the grant landing after creation is verified
at gate 4.5 rather than assumed.

Branch: `task/4-specz-linkage-correction` off `main`, base commit
`e65242a7802422cc86ed47d96945e2a86e0b27a3`. Worktree clean at branch creation.
Manifest CSV SHA-256 observed this session:
`5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e`.

---

## Gate checkpoints

### Gate 4.1 — Reproduce the linkage evidence

Committed script: `src/etl/verify_specz_linkage_v11.py` (read-only: one
`default_transaction_read_only=on` transaction; no database writes; no linkage
inferred, repaired, or materialized). Evidence JSON (gitignored staging):
`staging/specz-linkage-g41-evidence.json`. The investigation probe's output was
not consulted; its sentinel rules were read for comparability and re-derived
independently in the script.

Prior-observation reproduction (prior | observed | agree):

| Observation | Prior | Observed | Agree |
|---|---:|---:|---|
| Non-sentinel `id_specz_khostovan25` values, all distinct | 37,219 | 37,219 (distinct == count) | Yes |
| Resolving against galaxy-level by `Id_specz` | 24,364 | 24,364 | Yes |
| Not resolving | 12,855 | 12,855 | Yes |
| Range of stored link values | 223–165,312 | 223–165,312 | Yes |
| Compilation `Id_specz` range, measurement level | 1–487,666 | 1–487,666 | Yes |
| Measurement rows; galaxy rows | 482,579; 261,975 | 482,579; 261,975 | Yes |
| Galaxy set == measurement rows at `Priority = 1` | full equality | full equality (see below) | Yes |
| `ra_COSMOS25`/`dec_COSMOS25` vs mirror at that id | zero, all rows | zero, all rows (max 0.0 both surfaces) | Yes |
| Compilation crossmatch separation | median 0.084", ceiling 0.998" | median 0.0840", max 0.9983" (n=92,359) | Yes |
| Defective-path separation median | 4,054" | 4,467.3" (n=24,364) | **No — finding F-06** |
| Distinct sources, galaxy level | 45,007 | 45,007 | Yes |
| Distinct sources, measurement level | 46,039 | 46,039 | Yes |
| Usable non-sentinel redshift sources, galaxy level | 39,165 | 39,165 (rule: finite `specz > -90`) | Yes |
| Catalog-flagged absent from galaxy surface | 3,062 | 3,062 | Yes |
| Catalog-flagged absent from measurement surface | 2,378 | 2,378 | Yes |
| Multiply-named catalog sources, galaxy level | 185 groups / 371 rows | 185 / 371 | Yes |

Establishments:

1. **Identifier semantics.** `Id_specz` is unique at measurement level
   (482,579 distinct of 482,579) and galaxy level (261,975 of 261,975). Both
   artifacts carry 32 columns with identical names. The galaxy-level table
   equals the measurement-level rows at `Priority = 1` by column-set equality
   and positional per-column value equality including mask equality (NaN-aware
   for floats); no keyed fallback was needed.
2. **Namespace validity.** Separation between stored `ra_COSMOS25`/
   `dec_COSMOS25` and `photometry_primary.ra`/`dec` at `Id_COSMOS25`:
   min/median/p90/p99/max all exactly 0.0 arcsec at both surfaces
   (measurement: n=92,359 of 482,579; galaxy: n=45,193 of 261,975). Excluded
   rows: 390,220 (measurement) and 216,782 (galaxy) for sentinel `Id_COSMOS25`
   (-999); zero rows excluded for invalid coordinates after a valid id.
3. **Defective-path geometry.** Compilation crossmatch (measurement rows with
   valid id and valid corrected coordinates vs the catalog source):
   min 0.00013", median 0.0840", p90 0.2322", p99 0.6381", max 0.9983"
   (n=92,359; excluded 390,220 sentinel-id rows). Defective path (24,364
   resolving stored values joined to galaxy-level `Id_specz`, corrected
   coordinates): min 45.59", median 4,467.3", p90 6,047.6", p99 7,121.9",
   max 8,727.4". One crossmatch, one broken pointer.
4. **Value-range incompatibility.** Stored link values span 223–165,312
   against the compilation's `Id_specz` span 1–487,666: 33.85% of the range;
   zero stored values exceed the compilation maximum.

Mutation test: perturbing one stored `ra_COSMOS25` by +0.5 arcsec in a scratch
copy yields a reported separation of 0.49977" — the zero is measured, not
structural.

Finding F-06 (prior disagreement, does not halt): the defective-path median
prior of 4,054" was not reproducible exactly. Observed 4,467.3" on the stated
basis (resolving values, galaxy-level corrected coordinates). Diagnostic
variants: unique/original coordinates 4,467.3" (identical to corrected on this
subset); all 37,219 values against measurement-level corrected coordinates
4,300.4"; unique-table stored `ra_COSMOS25` basis covers only 3,141 rows
(median 1,351.6") because galaxy-level `-999` coordinate sentinels dominate.
The prior's precise basis is not reconstructible; the qualitative conclusion
(field-scale ~1.2 deg median versus sub-arcsecond crossmatch) holds under
every variant.

No linkage was inferred, repaired, or written. Gate 4.1 commit: see SHA table
at close.
