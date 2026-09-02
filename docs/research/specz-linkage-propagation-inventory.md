<!--
---
title: "Spec-z Linkage Propagation Inventory"
description: "P2R-04b gate A2.1: every artifact carrying a separation statistic produced by the defective P2R-04 pairing code, with locator, current text, prior digest, and in-scope disposition"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-02"
version: "1.0"
status: "Active"
tags:
  - type: research
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Spec-z Linkage Evidence](specz-linkage-evidence.md)"
  - "[Schema v1.1](../reference/schema-v11.md)"
  - "[P2R-04 Worklog](../../work-logs/2026-08-31-cosmos2025-worklog-p2r-04-specz-linkage-correction.md)"
  - "[P2R-04b Worklog](../../work-logs/2026-08-31-cosmos2025-worklog-p2r-04b-seal-and-propagation-repair.md)"
---
-->

# Spec-z Linkage Propagation Inventory

Gate A2.1 of spec P2R-04b. A correction is scoped by where the defective
output went, not by where the defect was found. This document traces every
artifact carrying a separation statistic produced by the defective P2R-04
gate 4.1 pairing code, so that the gate A2.2 regeneration diff and the gate
A2.3 comment application are bounded in advance by an enumeration rather
than by an assumption.

This gate changes no pre-existing file and no database object. It adds this
document and the P2R-04b worklog checkpoint.

---

## 1. What was superseded, and by what

The P2R-04 gate 4.1 verifier paired a stored `id_specz_khostovan25` value
with the catalog row whose `id` equalled that value, rather than with the
catalog row that carried the value. Every separation statistic it produced
therefore described the wrong population on the wrong coordinate basis. Gate
A1.2 of P2R-04a corrected the pairing; gate A1.3 reconciled the resulting
distributions; gate A1.4 corrected the review surface.

The corrected verifier is `src/etl/verify_specz_linkage_v11.py`. At gate A2.1
its SHA-256 was
`2db4890d5f1923db3debeb11b83f13fc99a393f2013daf0f2ed9523865596d81`; gate
A2.5 restored the catalog identifier lookup and it is now
`e55f2a44f4ec1dd89f5dae8ec89757afe972ddead288ead6f94d330625594466`.
The seal pinned at gate A2.2 is the second value, and the guard restoration
changed no observed statistic: every evidence subdocument, including the
compilation-crossmatch control at canonical digest
`9a22f4b61bc3214875b0e0377aa3c2d2b068830b69956c58a5aeaff6de085cdc`, is
byte-identical across the change. Its observed distributions, reproduced
fresh against the pinned FITS artifacts and the read-only mirror, are:

| Population | Coordinate basis | n | min | median | p90 | p99 | max |
|---|---|---:|---:|---:|---:|---:|---:|
| All links (every non-sentinel stored link) | catalog `photometry_primary.ra/dec` to `specz_compilation_all.ra_corrected/dec_corrected` | 37,219 | 0.00490" | 4,054.34" | 5,956.72" | 7,219.43" | 9,085.02" |
| Resolving subset | catalog `photometry_primary.ra/dec` to `specz_compilation_unique.ra_corrected/dec_corrected` | 24,364 | 0.00604" | 4,245.57" | 6,061.36" | 7,379.07" | 9,085.02" |
| Compilation crossmatch (control, unchanged) | `specz_compilation_all.ra_corrected/dec_corrected` to catalog `photometry_primary.ra/dec` at `Id_COSMOS25` | 92,359 | 0.00013" | 0.0840" | 0.2322" | 0.6381" | 0.9983" |

The superseded values, and what each was:

| Superseded value | What it was | Superseded by |
|---|---|---|
| 4,467.3" | Defective-path median, defective pairing, resolving subset | 4,054.34" (all links) and 4,245.57" (resolving subset) |
| 45.59" | Defective-path minimum, same computation | 0.00490" (all links) and 0.00604" (resolving subset) |
| 6,047.6" | Defective-path p90, same computation | 5,956.72" (all links) and 6,061.36" (resolving subset) |
| 7,121.9" | Defective-path p99, same computation | 7,219.43" (all links) and 7,379.07" (resolving subset) |
| 8,727.4" | Defective-path maximum, same computation | 9,085.02" (both populations) |
| 4,300.4" | Diagnostic variant, all values at measurement level, defective pairing | Subsumed by the corrected all-links result |
| 1,351.6" | Diagnostic variant, stored `ra_COSMOS25` basis over 3,141 rows, defective pairing | Subsumed by the corrected all-links result |

The compilation-crossmatch control never used the defective pairing and is
byte-unchanged. No count in the propagated semantic note is superseded:
24,364 of 37,219, the stored range 223 to 165,312, and the compilation range
1 to 487,666 all reproduce exactly.

---

## 2. Search method

Both surfaces were searched exhaustively rather than sampled, and both
searches are reproducible from this repository.

### 2.1 Repository tree

`git grep` over the tracked tree at `4f98e49`, once per superseded value in
both comma-grouped and bare forms, plus a phrase search on the semantic note
and on the sealed verifier digest that binds it:

```bash
for v in "4,467.3" "4467.3" "4,300.4" "4300.4" "1,351.6" "1351.6" \
         "45.59" "8,727.4" "8727.4" "6,047.6" "6047.6" "7,121.9" "7121.9"; do
  git grep -n -F "$v" -- .
done
git grep -n -F "Does not resolve against the held DR1.1" -- .
git grep -n -F "field-scale" -- .
git grep -n -F "46a7b8274d1459a875eb2319dc02c4069bf48a47965657add5d808b33d30c650" -- .
```

A bare-digit sweep (`4467`, `8727`, `6047`, `7121`) was run as a control. Its
only additional hits are coincidental digit runs inside profile JSON payloads
in `data/dictionary/columns-v11.csv`, which are value-distribution facts and
not separation statistics. The comma-grouped forms are the discriminating
searches because every rendered separation statistic in this repository is
comma-grouped.

Untracked and ignored paths were excluded deliberately: `staging/` is
gitignored evidence, regenerated on demand, and is not an artifact anyone
reads as fact.

### 2.2 `pg_description`

Every column comment under schema `source` was read in one read-only session
and searched for the same tokens, then captured with a per-comment SHA-256
for the gate A2.3 reversal and byte-unchanged assertions:

```sql
SELECT c.relname, a.attname, a.attnum, d.description
FROM pg_description d
JOIN pg_class c ON c.oid = d.objoid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.objsubid
WHERE n.nspname = 'source' AND d.objsubid > 0
ORDER BY c.relname, a.attnum;
```

Observed: 1,461 column comments, matching the startup prerequisite. Capture
manifest digest (SHA-256 over `locator<TAB>comment_sha256` lines, sorted by
locator): `f4f4892fb07bceb4581304d7663bb47867760827b12f0840db319aea301e7c2e`.
The capture itself is written to the gitignored
`staging/a21-pg-description-capture.json`; its digest above is the tracked
anchor.

Session identity: database `cosmos2025_v11`, current and session user
`clusteradmin_pg01`, `default_transaction_read_only=on` and
`transaction_read_only=on` set at connection time. The analyst role
`cosmos2025_v11_ro` was attempted first and refused by `pg_hba.conf` for host
10.25.20.10, which is the pending operator infrastructure action recorded in
`AGENTS.md`, not a change in this unit.

---

## 3. Occurrence inventory

Twelve occurrences across seven artifacts. Prior digest is the whole-file
SHA-256 at `4f98e49` for repository files, and the comment SHA-256 for the
database.

| # | Artifact | Locator | Current text | Prior digest | In scope |
|---|---|---|---|---|---|
| 1 | `src/etl/load_dictionary.py` | line 1074, `_enrich_semantics` literal | `"separation of 4,467.3 arcsec and stored values "` | `8e79a0b7c69c65486cae4f03f1c5825c667f3a0ea12fca8a19fe68091b22900f` | Yes, A2.2 |
| 2 | `src/etl/load_dictionary.py` | line 224, `EXPECTED_SEMANTIC_HASHES["specz_linkage_gate41"]` | `46a7b8274d1459a875eb2319dc02c4069bf48a47965657add5d808b33d30c650` | same file | Yes, A2.2 |
| 3 | `data/dictionary/columns-v11.csv` | line 5, `semantic_note` field | `...field-scale median separation of 4,467.3 arcsec...` | `a20457c8c5c1785ebce0442a17c1fa06bdef9c1300c199d21776f7c0d22cfcd5` | Yes, A2.2 (regenerated) |
| 4 | `data/dictionary/columns-v11.csv` | line 5, `semantic_note_source_sha256` field | `46a7b827...c650` | same file | Yes, A2.2 (regenerated) |
| 5 | `src/etl/schema_v11.sql` | line 1734, `COMMENT ON COLUMN "source"."photometry_primary"."id_specz_khostovan25"` | `Semantic note: ...4,467.3 arcsec...` | `592ba562ec8ae1040f3bd52ca4fefdc6cb3e7a53bdbd20004e36c9b7c1b2581d` | Yes, A2.2 (regenerated) |
| 6 | `src/etl/schema_v11.sql` | line 1735, same statement | `sha256=46a7b827...c650` | same file | Yes, A2.2 (regenerated) |
| 7 | `src/etl/conformance_cases_v11.py` | line 129, case `0004:photometry_primary.id_specz_khostovan25` | `'separation of 4,467.3 arcsec and stored values spanning 223-165,312 against Id_specz '` | `524b83786f8827ead7d58c5daf8764569037f027e3cadfedb1cdddfcb9c6f0dd` | Yes, A2.2 (regenerated) |
| 8 | `src/etl/conformance_cases_v11.py` | line 137, same case | `'sha256=46a7b827...c650\n'` | same file | Yes, A2.2 (regenerated) |
| 9 | `docs/reference/schema-v11.md` | line 317, `photometry_primary.id_specz_khostovan25` row | `...field-scale median separation of 4,467.3 arcsec...` | `e4b467b045a385f09bb03827ff200597608d7a213351f148d6ee843388f09b05` | Yes, A2.2 (regenerated) |
| 10 | `docs/reference/schema-v11.md` | line 317, same row | `sha256=46a7b827...c650` | same file | Yes, A2.2 (regenerated) |
| 11 | Live database | `source.photometry_primary.id_specz_khostovan25` comment | see §4 | `2fd8394b6397c0b4321e5a3dc0ffd4d340f91696f8d58832a8ba5ec8e5132e18` | Yes, A2.3 |
| 12 | `spec/spec-defect-register.md` (central) | SD-068 body | `4,467.3 arcsec`, `4,300.4 arcsec`, `1,351.6 arcsec`, and the "did not reproduce on any recoverable basis" claim | `ff4e1153540afcc929d8807a07a1b8fe7bd8ddd663a79473a103fd9cd370a066` | Yes, A2.6 |

Occurrences 1 and 2 are the two authored edits. Occurrences 3 through 10 are
derived: they must arrive by regeneration, never by hand. Occurrence 11 is
the propagated database comment, applied through the comment contract.
Occurrence 12 is a register correction, not a regeneration.

### 3.1 Note on Modify scope for occurrence 1

The P2R-04b Modify list admits `src/etl/load_dictionary.py` "restricted to
the `specz_linkage_gate41` seal entry." Occurrence 1 is the semantic-note
literal that the `specz_linkage_gate41` seal binds: its
`semantic_note_source` is that verifier, its `semantic_note_source_sha256`
is that seal's value, and it is the only dictionary content the seal
governs. Reading the restriction to exclude it would make gate A2.2
unexecutable, because its own validation requires that "corrected statistics
in the regenerated semantic notes name their population and coordinate
basis," which no regeneration can produce while the literal is frozen. The
restriction is read as bounding the edit to the seal entry and the note that
seal binds, and to nothing else in a 56 KB module. No other line of
`load_dictionary.py` changes.

---

## 4. Database columns enumerated for gate A2.3

Exactly one column comment under `source` carries a superseded value. The set
is closed:

| Relation | Column | Prior comment SHA-256 | Prior length (bytes) |
|---|---|---|---|
| `source.photometry_primary` | `id_specz_khostovan25` | `2fd8394b6397c0b4321e5a3dc0ffd4d340f91696f8d58832a8ba5ec8e5132e18` | 2,114 |

The two lines of that comment which change, verbatim as they stand before
gate A2.3:

```text
Semantic note: Does not resolve against the held DR1.1 spec-z compilation: 24,364 of 37,219 distinct non-sentinel values resolve by Id_specz, with a field-scale median separation of 4,467.3 arcsec and stored values spanning 223-165,312 against Id_specz 1-487,666. Join through specz Id_COSMOS25 instead. Mirrored as shipped; no repair. Evidence: gate 4.1 command src/etl/verify_specz_linkage_v11.py; review surface docs/research/specz-linkage-evidence.md.
Semantic-note provenance: source=/opt/agents/repos/cosmos2025-anomalies/src/etl/verify_specz_linkage_v11.py; locator=PRIORS contract and main() establishments 3-4 (defective-path geometry; value-range incompatibility); sha256=46a7b8274d1459a875eb2319dc02c4069bf48a47965657add5d808b33d30c650
```

The other eight lines of that comment (description, description status,
description provenance, unit, unit provenance, null/profile facts,
documented sentinel evidence, candidate observations) are unchanged, and the
remaining 1,460 column comments are unchanged. Gate A2.3 asserts both
directions against the capture named in §2.2.

Reversal: the prior comment text is recoverable in full from
`staging/a21-pg-description-capture.json` and, independently, from
`src/etl/schema_v11.sql` at commit `4f98e49` line 1734. Restoring it is a
replay of a captured statement, not a reconstruction.

---

## 5. Dictionary rows enumerated for gate A2.2

One row. Its key under the dictionary's own identity contract
(`target_table` plus `target_identifier`, equivalently `source_family` plus
`source_file` plus `source_column`):

| Field | Value |
|---|---|
| `target_table` | `photometry_primary` |
| `target_identifier` | `id_specz_khostovan25` |
| `source_family` | `master_catalog` |
| `source_file` | `/mnt/nvme01/cosmos-web-dr1-catalog/COSMOSWeb_mastercatalog_v1.1_photom_primary.fits` |
| `source_locator` | `HDU 1 [PHOTOMETRY HOTCOLD AND SE++]` |
| `source_column` | `id_specz_khostovan25` |
| `column_origin` | `source_native` |
| CSV line at `4f98e49` | 5 |

Fields that change on that row, and only these two:

| Field | Prior value | Prior field SHA-256 |
|---|---|---|
| `semantic_note` | the §4 semantic-note text | `9a5d49afe3f0949c7583afd60e00ed9c4ac7d0193bc652167ad4ff9a9a232a06` |
| `semantic_note_source_sha256` | `46a7b8274d1459a875eb2319dc02c4069bf48a47965657add5d808b33d30c650` | n/a, the value is itself a digest |

`description_text`, `description_source`, `description_locator`,
`description_source_sha256`, and `description_status` do not change:
upstream's description is what upstream said, and the project finding lives
in the semantic note. `semantic_note_source` and `semantic_note_locator` do
not change: the source file and the locator within it are the same. The
`profile_json`, sentinel, and mask fields do not change: no profiling input
moved.

Row count stays at 1,448. No row is added or removed.

---

## 6. Derived artifacts predicted to change at gate A2.2

The gate A2.2 diff is bounded by this list. A regenerated artifact differing
anywhere outside it halts the gate as evidence that this inventory was
incomplete.

| Artifact | Regeneration command | Predicted diff |
|---|---|---|
| `data/dictionary/columns-v11.csv` | `python src/etl/load_dictionary.py` | line 5 only, fields `semantic_note` and `semantic_note_source_sha256` |
| `docs/reference/sentinel-candidates-v11.md` | same command, same run | none; predicted byte-identical |
| `src/etl/schema_v11.sql` | `python src/etl/generate_schema_v11.py` | the `id_specz_khostovan25` `COMMENT ON COLUMN` statement only |
| `src/etl/conformance_cases_v11.py` | `python src/etl/generate_conformance_v11.py` | case `0004:photometry_primary.id_specz_khostovan25` only |
| `docs/reference/schema-v11.md` | `python src/etl/generate_schema_docs_v11.py` | the `0004:photometry_primary.id_specz_khostovan25` row only |

`docs/reference/sentinel-candidates-v11.md` is listed because the dictionary
build writes it in the same run and its byte-identity is asserted by the same
check. It carries no semantic-note content and is predicted unchanged;
predicting "no change" is still a prediction the gate tests.

The comment contract helper that gate A2.3 must route through is
`column_comment_contract()` in `src/etl/generate_schema_v11.py` at line 405.
The spec's expected entry-point name is confirmed correct.

---

## 7. Closed records: inventoried, out of scope

A superseded number inside a sealed historical record stays. The record is
what was believed at the time, and revising it would collapse two executions
into one account.

| Artifact | Locator | Occurrence | Why out of scope |
|---|---|---|---|
| `work-logs/2026-08-31-cosmos2025-worklog-p2r-04-specz-linkage-correction.md` | line 122 | prior-versus-observed table row, `4,467.3" (n=24,364)` | Sealed worklog of a closed unit. P2R-04b's do-not-touch list names it explicitly. Digest `fe992b655cf1cc31a378a5ceb520e09f563a748bbe3a87683d308efb6f864aad` is asserted unchanged at A2.7. |
| same | lines 149 to 150 | full defective distribution: `min 45.59", median 4,467.3", p90 6,047.6", p99 7,121.9", max 8,727.4"` | same |
| same | lines 160 to 167 | F-06 narrative and the `4,300.4"` / `1,351.6"` diagnostic variants | same |
| same | line 550 | F-06 issue reference | same |
| `spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md` (both archive positions) | Prior Observations table | `median 4,054 arcsec` | Archived spec, write-once. The value is a prior the spec authored, not an output of the defective code, and the corrected computation reproduces it. Digest `a3bbdcdb933a7aac62d51e6b3ed1188b8e0f0adb8f8e2ea8abf003c5e9d7c5c8` at both positions. |
| `work-logs/2026-08-31-cosmos2025-worklog-p2r-04a-evidence-layer-correction.md` | gate A1.2 checkpoint | corrected distributions, quoted as observed | Not superseded. Recorded here so the sweep is complete. Sealed at A2.7 with a status change only. |

The central defect register is deliberately not on this list. SD-068 is an
open record in an active register, not a sealed historical one, and its claim
is disproved rather than merely dated. It is occurrence 12 in §3 and is
corrected in place at gate A2.6.

---

## 8. Searches that returned nothing

Recorded so that the absence is evidence rather than an omission.

| Surface | Searched for | Result |
|---|---|---|
| `docs/research/specz-linkage-evidence.md` | all seven superseded values | none; gate A1.4 already corrected the review surface |
| `docs/research/etl-v2-verification.md` | all seven superseded values | none; the P2R-03 surface predates the spec-z linkage work |
| `docs/reference/sentinel-candidates-v11.md` | `4,467.3`, `46a7b827` | none |
| `data/dictionary/README.md` | superseded values, sealed digest, `specz_linkage_gate41` | none |
| `README.md`, `AGENTS.md`, `docs/project-state.md` | all seven superseded values | none |
| `tests/` | all seven superseded values, sealed digest, semantic-note phrase | none; no test pins the note text or its digest |
| `pg_description` under `source` | all seven superseded values | one hit, occurrence 11; the other 1,460 comments are clean |
| `pg_description` outside `source` | n/a | no other schema in `cosmos2025_v11` carries mirror comments; `analysis` does not exist |
| tracked tree | `4,300.4`, `1,351.6` in any artifact other than the P2R-04 worklog and SD-068 | none |

---

## 9. Verification performed at this gate

| Check | Result |
|---|---|
| Every superseded value located with a locator, or shown to return none | 12 occurrences located, 7 negative searches recorded (§3, §8) |
| In-scope artifacts distinguished from closed records with a stated reason | §3 and §7 |
| Database columns enumerated exactly, with prior text and digest captured | §4, one column, digest `2fd8394b...` |
| Dictionary rows enumerated exactly by row key | §5, one row, `photometry_primary.id_specz_khostovan25` |
| Search method recorded, reproducible, covering both surfaces | §2 |
| Only the inventory document and the worklog added or changed | asserted by `git diff --stat` against `4f98e49` in the worklog |
| Zero database objects changed | read-only session, identity and enforcement recorded in §2.2 and the worklog |
