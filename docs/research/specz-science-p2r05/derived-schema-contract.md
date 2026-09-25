<!--
---
title: "P2R-05 Derived Schema Contract"
description: "Physical field names and meanings of the derived (non-native) columns in the four analysis.specz_p2r05_* product tables, separated from the sealed source dictionary"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: astronomy
  - domain: spectroscopy
  - tech: postgresql
related_documents:
  - "[P2R-05 README](README.md)"
  - "[P2R-05 Review](review.md)"
---
-->

# P2R-05 Derived Schema Contract

The sealed source dictionary (`data/dictionary/columns-v11.csv`) is not
extended by this product. Native compilation fields are copied into the
measurement audit with a `native_` prefix and their original names and
types; everything below is derived under policy `p2r05-specz-policy-v1`
and lives only in `cosmos2025_v11.analysis`. Physical types: `text`,
`bigint`, `integer`, `double precision`, `boolean`, `jsonb`.

## `analysis.specz_p2r05_runs` (key: `run_id`)

| Column | Meaning |
|---|---|
| `policy_id`, `policy_semantic_digest`, `spec_version`, `spec_sha256` | Approved policy identity and the authorizing spec bytes |
| `snapshot_manifest_digest`, `snapshot_file_digests` | Captured input identity (per-file SHA-256 of the four snapshot CSVs) |
| `implementation` | SHA-256 of build-affecting module bytes plus Python/psycopg/platform versions |
| `measurements_content_sha256`, `sources_content_sha256`, `splits_content_sha256` | Canonical content digests over the three product record sets (this metadata row is outside those domains) |
| `measurement_rows`, `source_rows`, `split_rows` | Row counts |
| `tile_map`, `tile_map_canonical_digest` | The frozen P-06 map and its digest |
| `product_state` | `pending_scientific_adoption` until the operator answers S5-Q01..Q05 |
| `mechanical_seal_at`, `mechanical_seal_evidence` | Gate 5.7 seal timestamp and evidence document |
| `created_at`, `installed_by` | Operational metadata |

## `analysis.specz_p2r05_measurements` (key: `run_id, id_specz`)

Native block: `native_id_original` (text), `native_ra_*`/`native_dec_*` and
`native_specz`, `native_photoz` (double precision), and the integer fields
`native_priority`, `native_flag`, `native_confidence_level`, `native_survey`,
`native_compilation_year`, `native_public_or_private`,
`native_id_cos20_classic`, `native_id_cos20_farmer`, `native_id_cosmos25`,
`native_id_cosmos15`, `native_id_cosmos09`, `native_photoz_type`,
`native_groupid`, `native_groupsize`. These are copies, not repairs;
finite sentinels remain values and only FITS masks/NaN are SQL NULL.

| Derived column | Type | Meaning |
|---|---|---|
| `association_status` | text | `associated` / `no_association_sentinel` / `unresolved_identifier` (a non-null id absent from the catalog is a contract discrepancy) |
| `resolved_catalog_id` | bigint, null | `photometry_primary.id` when associated |
| `is_unique_member` | boolean | `id_specz` present in `_unique` |
| `numeric_valid_z` | boolean | P-02 numeric validity |
| `z_invalid_reason` | text, null | `z_missing` / `z_non_finite` / `z_non_positive` |
| `flag_category` | text | `recognized_measured` / `non_measured` (flags 0/10) / `unrecognized` / `flag_missing` |
| `confidence_in_domain` | boolean | confidence in [0,100] |
| `flag_confidence_mapping_consistent` | boolean, null | agreement with the documented flag→confidence mapping; null when the flag admits none |
| `secure_measurement` | boolean | full P-02 secure conjunction |
| `secure_block_reasons` | jsonb | every failed secure conjunct for this entry |

## `analysis.specz_p2r05_sources` (key: `run_id, catalog_id`)

| Column | Meaning |
|---|---|
| `association_resolved` | any corrected-path entry exists for this source |
| `population_a`, `population_b` | A: `_all` entries but no `_unique` entries; B: more than one `_unique` entry |
| `unique_entry_count`, `all_entry_count`, `numeric_valid_all_count`, `secure_all_count` | entry tallies under each predicate |
| `preferred_id_specz`, `preferred_reported_z`, `preferred_flag`, `preferred_confidence` | the P-03 selection; z is copied, never averaged |
| `preferred_tie`, `preferred_tied_ids` | whether the winning confidence was shared, and the full tie list |
| `preferred_entry_is_secure` | the selected entry satisfies P-02 |
| `unique_numeric_conflict`, `secure_all_conflict`, `other_measurement_disagreement` | the three independent P-04 flags |
| `conflict_witnesses` | jsonb object with the threshold and per-flag witness lists; each witness carries both `id_specz` values, raw z, flag, confidence, and the absolute difference, resolving to exact audited entries |
| `corroboration_status` | `singly_supported` / `multiply_supported` / `conflicting` / `not_assessable` |
| `lephare_type`, `classification_label` | carried photometric type and its label (`galaxy`/`star`/`qso`/`unknown_*`) |
| `broad_line_reported`, `broad_line_entry_ids`, `broad_line_confidences` | P-05 broad-line evidence with supporting entries |
| `photometric_qso` | `lephare.type = 2`, independent of broad-line evidence |
| `flag_star_mask_overlap`, `flag_blend`, `native_tile` | diagnostic context, never classification |
| `eligibility_primary_galaxy`, `eligibility_separate_validation` | finalized P-05 + P-06 booleans; mutually exclusive |
| `eligibility_basis_primary_pre_split`, `eligibility_basis_validation_pre_split` | the same conjunctions before the split gate (audit of the 5.4/5.5 phasing) |
| `assigned_split` | the source's P-06 partition |
| `exclusion_reasons` | jsonb array; overlapping, never collapsed |

## `analysis.specz_p2r05_splits` (key: `run_id, catalog_id`)

| Column | Meaning |
|---|---|
| `native_tile` | the source's native tile, unmodified |
| `assigned_split` | `development` / `validation` / `holdout` / `unassigned` |
| `split_version`, `split_salt` | `p2r05-spatial-v1` and the frozen salt |
| `valid_tile_domain_member`, `unassigned` | domain membership and the explicit unassigned state |

## Row ordering and digests

Canonical product order is `(run_id, id_specz)` for measurements and
`(run_id, catalog_id)` for sources and splits. Content digests are SHA-256
over canonical JSONL with sorted keys; storage paths, batch sizes, and
operational timestamps are outside the digest domains.
