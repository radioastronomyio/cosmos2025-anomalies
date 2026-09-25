<!--
---
title: "Gate 5.3 Decision Evidence Reproduction"
description: "Independent reproduction of the P2R-05 prior table and the extension enumerations from the captured input snapshot, with surfaces, predicates, units, and denominators per quantity"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.0"
status: "Active"
tags:
  - type: research
  - domain: astronomy
  - domain: spectroscopy
  - domain: data-engineering
related_documents:
  - "[Spec-z Linkage Evidence](../specz-linkage-evidence.md)"
  - "[P2R-05 README](README.md)"
---
-->

# Gate 5.3: Decision Evidence Reproduction

Reduction command (run from the repository root):

```
python src/features/specz_science/verify.py
```

The command parses the captured input snapshot
(`staging/derived/specz-p2r05/input-snapshot/`, manifest SHA-256
`06b19654fc715106ba1f788b52e084df1e94043343517f2b8a49fd44abfff7a4`) and
writes the full JSON evidence to `staging/derived/specz-p2r05/priors-5-3.json`.
The reductions are independent of the P2R-04 generators and of the gate 5.4
builders: they restate each predicate locally over the snapshot.

## Prior table reproduction

Every prior from the spec's "Prior observations to reproduce" section and
the v0.2 review reconciliation reproduced exactly. Surfaces: catalog =
`photometry_primary` (784,016 rows), `_unique` =
`specz_compilation_unique` (261,975), `_all` = `specz_compilation_all`
(482,579). Denominators are distinct catalog sources unless a row says
entries.

| Observation (surface, predicate, denominator) | Prior | Reproduced |
|---|---:|---:|
| Catalog / `_unique` / `_all` rows (row counts) | 784,016 / 261,975 / 482,579 | identical |
| Native tiles: distinct documented labels / null-or-out-of-domain sources (catalog) | 20 / 0 | identical |
| Sources reached through `_unique` / `_all` (distinct valid `id_cosmos25` in catalog) | 45,007 / 46,039 | identical |
| Population A sources / entries / nonzero-Priority entries | 1,032 / 1,559 / 0 | identical |
| Population B sources / entries (sources named by >1 `_unique` entry) | 185 / 371 | identical |
| B under finite z > -90, tol 0.005: agreeing / disagreeing / one usable / zero usable (185 groups) | 75 / 57 / 48 / 5 | identical |
| B under positive finite z, same tolerance: 72 / 57 / 49 / 7 | identical | identical |
| Disagreeing B groups with tied highest confidence, either rule | 16 | identical |
| Distinct `_unique` sources under z > -90 / positive z / positive z and conf >= 95 | 39,165 / 37,722 / 20,100 | identical |
| Corrected-path `_unique` entries conf >= 95 and flags 13/14, no z filter (entries) | 327 | identical |
| `_unique`-reachable sources with >= 2 positive finite conf >= 95 entries in `_all` | 8,939 | identical |
| Same population spanning abs z difference > 0.005 | 656 | identical |
| Of those, sources with exactly one `_unique` entry | 649 | identical |
| Of those 649, Priority 1 entry meets positive-z/conf rule | 647 | identical |
| Defective-path median, all-links basis (37,219 sources; catalog ra/dec to carried link's `_all` ra_corrected/dec_corrected; arcsec) | 4,054.341555894 | 4,054.3415558937 |
| Qualified before photometric type (resolved, secure preferred, no veto, valid tile; distinct sources) | 19,419 | identical |
| That cross-tab: type 0 / 1 / 2 | 18,473 / 349 / 597 | identical |
| Broad-line reported within: type 0 / 1 / 2 | 71 / 2 / 188 | identical |

Provenance registrations: 12 rows confirmed by the gate 5.1 pin preflight
(`preflight-5-1-analyst-pins.json`), not recomputed here.

## Structural equalities and bounds

- **`_unique` equals `_all` at Priority 1**: full positional per-column
  equality across all 31 non-key native fields over 261,975 rows joined by
  `id_specz` lookup, including NULL/mask distinctions. Equal: yes.
- **Unrecognized-flag empirical bound** (per surface): flag 5 carries
  confidence 90 (`_unique` 2, `_all` 24 entries); flags 6 and 10 carry -99;
  flags -99/-3/-2/-1 and 0 carry confidence 0; -3 appears in `_all` only
  (3 entries). No unrecognized flag reaches confidence 95 in either
  surface. Flag 5 is the only unrecognized flag with positive confidence.
- **Quality-mapping consistency**: entries with numeric-valid z, flag in
  {3,4,13,14}, and confidence in [95,100] number 272,909 in `_all`; zero of
  them disagree with the documented flag/confidence mapping. The secure
  predicate's mapping requirement excludes nothing on this hold, and the
  stricter secure population is not a mapping-filtered subset.
- **Secure preferred population (baseline predicates, pre-split)**: 20,100
  resolved sources carry a secure preferred `_unique` entry; 681 of those
  are vetoed by a P-04 flag. The 20,100 availability figure equals the
  historical positive-z + conf>=95 availability count on this hold because
  every such preferred entry also satisfies the flag/mapping conditions.

## Hostile-fixture discriminators

`tests/test_specz_science_verify.py` exercises the reductions on synthetic
tables with shuffled, non-contiguous identifiers and values colliding
across identifier namespaces (a catalog id equal to an `id_specz` value).
A tampered `_unique` copy fails the equality check; a single-`_unique`
source with a conflicting secure Priority 0 alternative fires
`secure_all_conflict` while `unique_numeric_conflict` stays false;
population A's reduction carries the structural-zero statement and makes
no nearest-neighbour ownership claim; the 0.005 boundary behaves as
"difference strictly greater than the threshold is conflict", with the
float-boundary caveat documented in the test (no production pair sits
within ulps of the threshold; verified empirically over both B-group
rules).

## Discrepancies

None. All priors reproduced on first computation; no independent
recomputation was required.
