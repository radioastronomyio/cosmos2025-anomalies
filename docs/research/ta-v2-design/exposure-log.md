<!--
---
title: "T_A v2 Exposure Log"
description: "Design-stage data-exposure record for the proposed T_A v2 design: pre-partition diagnostics history, the 2026-10-16 coordinator queries transcribed verbatim, the prospective development-only query rule, and the single A1.5 development-only support count (P2R-06a gates A1.1/A1.5)"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-16"
version: "1.0"
status: "Active - proposed, pending approval"
tags:
  - type: report
  - domain: astronomy
  - domain: sed-fitting
  - domain: spectroscopy
  - tech: python
  - tech: postgresql
related_documents:
  - "[T_A v2 README](README.md)"
  - "[Evaluation Protocol](evaluation-protocol.md)"
  - "[Amendment spec P2R-06a](../../../spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06a-ta-v2-design-repairs.md)"
---
-->

# T_A v2 Exposure Log (P2R-06a Gate A1.1)

Status: `proposed_not_adopted`. This record discloses every data exposure
that touched or could have touched the design of the proposed T_A v2
contract. It creates no science, runs no query, and changes no frozen
input. It exists so the evaluation protocol and the review surface can
state truthfully what the future holdout assessment is and is not.

**What this log establishes:** the T_A v2 design was informed by
full-catalog summaries that contained holdout-tile information
(section 2), and by earlier diagnostics whose exact overlap with today's
partitions is unverified (section 1). No designated one-time evaluation
of a frozen T_A model has run. This log does **not** support a claim that
no outcome-derived holdout information was ever seen, and no protocol or
review claim in this directory may assert an unexposed holdout or zero
historical outcome-derived exposure. The eventual holdout assessment, when
separately authorized, is therefore **not an untouched test of
feature-family selection**; TA2-Q08 puts that qualified acceptance to Don.

## 1. Pre-partition diagnostics (coordinator-reported history)

Two analysis sessions predate the P2R-05 partition freeze. Predating the
partitions does not prove exact overlap with today's holdout sources,
particularly across the v1/v1.1 mirror boundary: the 2026-07-10 session
ran against the v1 `cosmos2025` baseline before the v1.1 mirror existed,
and tile-level or source-level overlap with the current holdout tiles
(A1, A7, B3, B7) was never computed. Historical observations can still
have influenced design choices (center family, covariate set, the forced
high-redshift boundary), so an untouched-holdout claim is not available
for them either. These are coordinator-reported prior findings, not
frozen inputs; neither was rerun, and per-tile membership was not
inferred. Neither result appears in `docs/project-state.md`; promoting
either to a frozen input is Don's decision, not this unit's.

### 1.1 Frozen project-state inputs (tracked, restated)

The May report `docs/phase2-tension-diagnostic-report.md` and
`docs/project-state.md` section 1 carry the three frozen design inputs
(the ~0.24 dex conditional cross-code mass offset with
`sigma_sys_mass` = 0.1 dex; the censoring-dominated SFR tension ranking
with bulk `t_sfr_100` mean 0.302 / std 0.980; the dimensionally
incoherent historical `chi2_ratio`). These are tracked documents with
recorded identities in `input-identity.json`; their coverage of the
catalog predates the partitions and is part of this disclosure by
reference. They are design drivers, not tests, and are not re-derived.

### 1.2 2026-07-10 session, v1 `cosmos2025` baseline (before the v1.1 mirror)

Coordinator-reported, not reproduced in this unit. Locator: coordinator
session record; the underlying v1 baseline is the read-only
`cosmos2025.catalog` described in the repository instructions. Exact
source/version pinning for the session is unavailable beyond the v1
baseline itself; exact overlap with the current holdout is unknown.

- A conditional median Delta log M surface over 6 by 6 redshift and
  mean-mass bins ranged from about -0.07 to -0.34 dex, with the mass
  trend reversing above z of about 5.5.
- The top 1,000 sources by absolute `t_sfr_100` were 75.5%
  LePhare-quiescent.
- LePhare sSFR non-additivity had median 0.002 dex and absolute value
  below 0.02 for 70.6% of sources, with its tail concentrated in
  quiescent sources.

### 1.3 2026-09-01 session

Coordinator-reported, not reproduced in this unit. Locator: coordinator
session record; same v1-plane construction as section 1.2. Exact overlap
with the current holdout is unknown.

- Means over the same plane confirmed a mass-slope reversal, not a sign
  reversal: every cell was negative (CIGALE heavier).
- The ~0.24 dex headline offset is a weighted average dominated by
  227,632 sources at z below 1 and mean log mass below 8.5; at mean log
  mass above 9.5 and z below 2 the offset was about 0.05 dex.
- Those means compared LePhare `mass_med` with the CIGALE posterior mean.

Design influence of sections 1.2-1.3: the reported slope reversal is the
labelled prior finding behind the proposed forced z = 5.5 bin boundary
(feature contract, `kind: declared_domain`); the offset structure
motivated the conditional center family. The reversal was **not**
reproduced in this unit and is not evidence of a physical discontinuity
or of adequate resolution at the boundary (see the feature contract's
declared rationale and TA2-Q02).

## 2. 2026-10-16 coordinator queries (CQ1 to CQ8)

Executed by Claude through MetaMCP on `cosmos2025_v11`, under an
administrator role (read-only by the MCP's query validator, not by
database role; cutover pending), on 2026-10-16 between about 16:00 and
17:55 EDT, in this order. None carries a partition predicate, so CQ1 to
CQ6 covered all 20 tiles. Queries rejected by the MCP validator before
execution, and one connection reset, returned no data and are omitted.

**These are coordinator-reported executions, transcribed verbatim, not
independently rerun evidence.** The SQL and result text below are
reproduced byte-for-byte from the amendment spec's Appendix A; the
evidence labels and qualifications are this record's own text and are
not part of the transcription.

**CQ1.** POP-MASS error validity and non-type-0 counts. Motivated:
demoting R3 to a consistency defect; sizing R8.

```sql
SELECT count(*) FILTER (WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0) AS t0_both_mass,
       count(*) FILTER (WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND c.mass_err IS NULL) AS t0_mass_no_err,
       count(*) FILTER (WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND c.mass_err < 0) AS t0_mass_neg_err,
       count(*) FILTER (WHERE c.mass <= 0) AS cig_mass_nonpos,
       count(*) FILTER (WHERE l.type <> 0 AND l.mass_med > -99 AND c.mass > 0) AS non_t0_both_mass
FROM source.lephare l JOIN source.cigale c USING (id)
```

Result: t0_both_mass 634845; t0_mass_no_err 0; t0_mass_neg_err 0; cig_mass_nonpos 10; non_t0_both_mass 8927.

**CQ2.** LePhare internal sSFR non-additivity (single code; now a
contract context output, so in scope of the A1.1 rule). Motivated:
decision 1.

```sql
SELECT count(*) AS n,
       avg(l.ssfr_med - l.sfr_med + l.mass_med) AS mean_gap,
       min(l.ssfr_med - l.sfr_med + l.mass_med) AS min_gap,
       max(l.ssfr_med - l.sfr_med + l.mass_med) AS max_gap,
       count(*) FILTER (WHERE l.ssfr_med - l.sfr_med + l.mass_med > 0.1 OR l.ssfr_med - l.sfr_med + l.mass_med < -0.1) AS n_gt_0p1,
       count(*) FILTER (WHERE l.ssfr_med - l.sfr_med + l.mass_med > 0.3 OR l.ssfr_med - l.sfr_med + l.mass_med < -0.3) AS n_gt_0p3,
       count(*) FILTER (WHERE l.ssfr_med - l.sfr_med + l.mass_med > 1.0 OR l.ssfr_med - l.sfr_med + l.mass_med < -1.0) AS n_gt_1
FROM source.lephare l
WHERE l.type = 0 AND l.mass_med > -99 AND l.sfr_med > -99 AND l.ssfr_med > -99
```

Result: n 758304; mean_gap -0.014821081650630638; min_gap -9.786629999999999; max_gap 0.6097099999999993; n_gt_0p1 29190; n_gt_0p3 7795; n_gt_1 1693.

**CQ3.** Redshift tail counts in the eligible mass population
(covariate). Motivated: decision 3.

```sql
SELECT count(*) AS n,
       count(*) FILTER (WHERE l.zpdf_med > 3) AS z_gt_3,
       count(*) FILTER (WHERE l.zpdf_med > 4) AS z_gt_4,
       count(*) FILTER (WHERE l.zpdf_med > 5.5) AS z_gt_5p5
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0
```

Result: n 634845; z_gt_3 84987; z_gt_4 48348; z_gt_5p5 14535.

**CQ4.** Mean mass disagreement by redshift band (both codes in one
expression). Motivated: decision 3 and context for an external review
prompt.

```sql
SELECT CASE WHEN l.zpdf_med < 1 THEN 'a_z<1' WHEN l.zpdf_med < 3 THEN 'b_1-3' WHEN l.zpdf_med < 5.5 THEN 'c_3-5.5' ELSE 'd_>5.5' END AS zband,
       count(*) AS n,
       avg(l.mass_med - log(c.mass)) AS mean_delta,
       count(*) FILTER (WHERE l.mass_med - log(c.mass) < 0) AS n_cigale_heavier
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND l.zpdf_med > -99
GROUP BY 1 ORDER BY 1
```

Result: a_z<1: n 269343, mean_delta -0.22115061968651317, n_cigale_heavier 249694. b_1-3: n 280508, -0.19862994052347577, 261400. c_3-5.5: n 70459, -0.2329780864428954, 67117. d_>5.5: n 14535, -0.22515061379263632, 13312.

**CQ5.** Mass and SFR (100 Myr) disagreement moments (both codes in one
expression). Motivated: decision 4.

```sql
SELECT current_database() AS db, current_user AS usr, count(*) AS n,
       avg(l.mass_med - log(c.mass)) AS mx,
       avg(l.sfr_med - log(c.sfr_100myr)) AS my,
       avg((l.mass_med - log(c.mass)) * (l.mass_med - log(c.mass))) AS mxx,
       avg((l.sfr_med - log(c.sfr_100myr)) * (l.sfr_med - log(c.sfr_100myr))) AS myy,
       avg((l.mass_med - log(c.mass)) * (l.sfr_med - log(c.sfr_100myr))) AS mxy
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND l.sfr_med > -99 AND c.sfr_100myr > 0
```

Result: db cosmos2025_v11; usr (administrator role, name withheld from this record); n 634845; mx -0.2126040622179253; my 0.07966464083861906; mxx 0.07514243165144985; myy 0.2059919964282771; mxy -0.040510298296032046. Derived by the coordinator: standard deviations 0.173 dex (mass) and 0.447 dex (SFR), correlation about -0.305. Uncentered, with the censored-SFR regime included.

**CQ6.** LePhare zero-width and reversed quantiles in the eligible mass
population (single code). Motivated: sizing the A1.3 guard.

```sql
SELECT count(*) AS n,
       count(*) FILTER (WHERE l.mass_l68 = l.mass_med OR l.mass_u68 = l.mass_med) AS mass_zero_side,
       count(*) FILTER (WHERE l.mass_l68 > l.mass_med OR l.mass_u68 < l.mass_med) AS mass_reversed,
       count(*) FILTER (WHERE l.sfr_med > -99 AND (l.sfr_l68 = l.sfr_med OR l.sfr_u68 = l.sfr_med)) AS sfr_zero_side,
       count(*) FILTER (WHERE l.sfr_med > -99 AND (l.sfr_l68 > l.sfr_med OR l.sfr_u68 < l.sfr_med)) AS sfr_reversed
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0
```

Result: n 634845; mass_zero_side 0; mass_reversed 0; sfr_zero_side 0; sfr_reversed 0.

**CQ7.** Partition table columns (metadata). Motivated: naming the A1.1
rule.

```sql
SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'analysis' AND table_name = 'specz_p2r05_splits' ORDER BY ordinal_position
```

Result: run_id text; catalog_id bigint; native_tile text; assigned_split text; split_version text; split_salt text; valid_tile_domain_member boolean; unassigned boolean.

**CQ8.** Partition sizes (metadata, no estimates). Motivated: stating
holdout coverage.

```sql
SELECT s.assigned_split, count(*) AS n, count(DISTINCT s.native_tile) AS tiles FROM analysis.specz_p2r05_splits s GROUP BY 1 ORDER BY 1
```

Result: development 476137 (12 tiles); holdout 160158 (4 tiles); validation 147721 (4 tiles).

### 2.1 What these counts are and are not

- **No partition exclusion.** CQ1 to CQ6 carry no split predicate; the
  coordinator reports all-tile coverage. They are full-catalog summaries
  containing holdout information, and the design (decisions 1-4) was
  informed by them. That is the exposure this log discloses.
- **CQ8 states whole partition sizes, not per-query membership.**
  160,158 is the full holdout partition; it is **not** the CQ2/CQ5
  eligible holdout denominator, and no count of qualifying holdout
  sources was produced for any earlier query.
- **CQ2 and CQ5 use different populations.** CQ2 used 758,304
  single-code (LePhare-only) sources; CQ5 used 634,845 sources under its
  distinct both-code predicates. Their broad `> -99`/positivity filters
  are **not** the repaired contract's domain/state predicates and must
  not be reinterpreted as exact contract eligibility.
- **CQ6's zero counts do not establish absence of missing or non-finite
  quantiles**, only that no zero-width or reversed pair exists among the
  compared finite values. The A1.3 directional-width guard is fail-closed
  protection, not a correction for observed data.
- **CQ5's derived correlation (about -0.30, uncentered, censored regime
  included) is neither a parameter nor a bound for anything in the
  contract** (A1.7 constraint; stated again in the evaluation protocol).
- No query in this section was rerun in this unit, and none may be rerun
  to "refresh" this record: the exposure is recorded once, and repeating
  it widens it.

## 3. Prospective query rule (development-only by default)

This rule binds all prospective exploratory queries by coordinators,
reviewers and executors from the adoption of this record forward.

1. **Default partition.** Any exploratory query that computes a T_A
   contract output (including context outputs such as
   `ctx_lp_ssfr_nonadditivity_dex`) or combines estimates from both codes
   uses **development tiles only**. This is the default for exploration
   and for all future fitting.
2. **Exact join and run binding.** The query joins source tables to the
   sealed partition table by `catalog_id` and binds the exact inherited
   `run_id` recorded in `input-identity.json`
   (`1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c`),
   with `analysis.specz_p2r05_splits.assigned_split = 'development'`.
   Unqualified runs are not joined; rows with missing assignments are not
   accepted.
3. **Permitted exceptions, each separately authorized.** A later named
   implementation unit may evaluate already-frozen choices on validation
   tiles, and a separately authorized one-time final evaluation may use
   the holdout, strictly under the S5 protocol. Neither exception
   authorizes new exploratory choices or fitting on those partitions, and
   neither permits a reroll.
4. **Design-influencing counts are logged.** Covariate-only and
   single-code validity counts that influence design (the class of CQ3
   and CQ6) are logged here when they occur. Logging them does not waive
   the amendment's source-read boundary: within P2R-06a the only
   permitted database read is the optional A1.5 development-only support
   count under its stated constraints.

## 4. A1.5 optional development-only support count (executed once)

The single database read P2R-06a authorizes was executed on 2026-10-16 by
the amendment executor through the analyst handoff
(`internal-files/cosmos2025-v11.env`, role `cosmos2025_v11_ro`), under
these constraints, all satisfied:

- **Role/session verification (read-only, no source estimates returned):**
  `current_user` = `cosmos2025_v11_ro` on database `cosmos2025_v11`;
  `rolsuper` f, `rolcreatedb` f; `has_table_privilege`:
  `source.lephare` SELECT t, INSERT f, UPDATE f;
  `analysis.specz_p2r05_splits` SELECT t, INSERT f. The session parameter
  `transaction_read_only` reported `off`; read-only is enforced by role
  privileges, not by the session parameter. No write was attempted.
- **Assignment integrity:** 0 `catalog_id` appears more than once under
  run `1e604a81...` with `assigned_split = 'development'`; the join
  binds `s.catalog_id = l.id`, the exact `run_id`, and
  `assigned_split = 'development'` only.
- **Declared-before-query fixed audit bins** (these are not fitted
  quantile cells; real-data quantile edges remain outside P2R-06a):
  redshift [null], [0,1), [1,3), [3,5.5), [5.5,8), [8,inf); magnitude
  [null], [0,21), [21,24), [24,27), [27,50), [50,inf).
- **Predicates:** the exact repaired `POP-MASS` point/error conditions
  only — `l.type = 0`, `l.mass_med BETWEEN -20.0 AND 15.0` (declared
  LePhare log domain), `c.mass > 0`, `c.mass_err IS NOT NULL AND
  c.mass_err >= 0`. Mass and error columns appear only inside these
  single-code validity predicates; no SFR selection, no cross-code
  arithmetic, no estimates, averages, or quantiles are returned; the
  sole aggregate is `count(DISTINCT l.id)`.

```sql
SELECT CASE WHEN l.zpdf_med IS NULL THEN '0_znull'
            WHEN l.zpdf_med < 1 THEN 'a_z0-1'
            WHEN l.zpdf_med < 3 THEN 'b_z1-3'
            WHEN l.zpdf_med < 5.5 THEN 'c_z3-5.5'
            WHEN l.zpdf_med < 8 THEN 'd_z5.5-8'
            ELSE 'e_z8+' END AS zband,
       CASE WHEN p.mag_auto_f444w IS NULL THEN '0_mnull'
            WHEN p.mag_auto_f444w < 21 THEN '1_m<21'
            WHEN p.mag_auto_f444w < 24 THEN '2_m21-24'
            WHEN p.mag_auto_f444w < 27 THEN '3_m24-27'
            WHEN p.mag_auto_f444w < 50 THEN '4_m27-50'
            ELSE '5_m50+' END AS magband,
       count(DISTINCT l.id) AS n
FROM source.lephare l
JOIN source.cigale c ON c.id = l.id
JOIN source.photometry_primary p ON p.id = l.id
JOIN analysis.specz_p2r05_splits s ON s.catalog_id = l.id
WHERE s.run_id = '1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c'
  AND s.assigned_split = 'development'
  AND l.type = 0
  AND l.mass_med >= -20.0 AND l.mass_med <= 15.0
  AND c.mass > 0
  AND c.mass_err IS NOT NULL AND c.mass_err >= 0
GROUP BY 1, 2 ORDER BY 1, 2;
```

Result (development split only, distinct catalog IDs):

```text
a_z0-1|0_mnull|2883        b_z1-3|0_mnull|1183       c_z3-5.5|0_mnull|1629     d_z5.5-8|0_mnull|265      e_z8+|0_mnull|129
a_z0-1|1_m<21|3425         b_z1-3|1_m<21|2694        c_z3-5.5|1_m<21|40        d_z5.5-8|1_m<21|0         e_z8+|1_m<21|0
a_z0-1|2_m21-24|13784      b_z1-3|2_m21-24|26323     c_z3-5.5|2_m21-24|3474    d_z5.5-8|2_m21-24|98      e_z8+|2_m21-24|23
a_z0-1|3_m24-27|57835      b_z1-3|3_m24-27|94633     c_z3-5.5|3_m24-27|23024   d_z5.5-8|3_m24-27|3005    e_z8+|3_m24-27|492
a_z0-1|4_m27-50|85346      b_z1-3|4_m27-50|48092     c_z3-5.5|4_m27-50|14985   d_z5.5-8|4_m27-50|3913    e_z8+|4_m27-50|1032
```

(Zeros for absent row combinations: `d_z5.5-8|1_m<21` and `e_z8+|1_m<21`
returned no rows.) These are coarse audit-bin counts with no influence on
any bin edge or threshold in this unit. **Actual fitted-cell support
remains unknown until P2R-07** whether or not this count ran: the audit
bins are not the development quantile cells, and the sparse [5.5,8) band
(98 sources in m21-24) already shows that per-cell support above the
forced edge will be an evaluation-time concern, not a design-time fact.

## 5. Consequences recorded elsewhere

- `evaluation-protocol.md` links this record and states that design was
  informed by full-catalog summaries containing holdout information; the
  eventual holdout assessment is disclosed as not an untouched test of
  feature-family selection, and future parameters are fitted on
  development only.
- `review.md` carries TA2-Q08, which asks Don to accept the documented
  design-stage exposure and the qualified future holdout claim, with
  development-only exploration/fitting, separately authorized
  protocol-bound validation/final evaluation, and no reroll. No
  designated one-time evaluation of a frozen T_A model has run as of
  this record.
