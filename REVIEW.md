# REVIEW.md

Repository review policy for `cosmos2025-anomalies`. This project mirrors the COSMOS-Web DR1.1 photometric catalog into PostgreSQL and computes cross-code SED-fitting tension metrics over it. Scientific correctness and provenance integrity outrank everything else here, including style and convention.

## What matters in this repository

- **The source mirror is lossless.** `cosmos2025_v11.source` holds every native field of the twelve mirrors (eleven release/supplement artifacts plus the measurement-level spec-z compilation), each with its own provenance registration. Any change that drops, renames, flattens, or derives a column in the mirror is a correctness failure. Derived and cleaned representations belong in the `analysis` schema, never in `source`.
- **Source fidelity and derived eligibility are different contracts.** Only FITS masks and NaN become SQL NULL. Finite sentinel values (999, -99, and similar) are stored unchanged in `source`, and code that converts a finite value to NULL there, or filters on one as if it were missing data, is a critical finding. The derived `analysis` layer is different: an approved policy may reject a value for eligibility (for example, a non-positive spec-z) while the native value remains untouched and unrelabelled in `source` and in the measurement audit. Review findings must name which contract a change touches.
- **Never compose a description or a unit.** Column semantics are transcribed from a cited upstream source with a locator and SHA-256, or marked `undocumented_upstream` / `unknown`. A plausible-looking description inferred from a column name is worse than a visible gap.
- **Provenance has no undo.** Changes to `docs/reference/data-manifest-v1.1.{csv,md}`, the CIGALE SED digest sidecar, `data/dictionary/columns-v11.csv`, or `source.provenance` replace a reviewed pin with an unreviewed one. Every artifact derived against the old pin silently becomes unreproducible. Treat any diff touching these as high-risk regardless of size.
- **The dictionary is the spine.** DDL, database comments, schema documentation, and conformance tests are generated from `data/dictionary/columns-v11.csv`. Hand-editing a generated artifact decouples the database from the dictionary and defeats the conformance gates. Flag hand edits to generated artifacts as critical.
- **`cosmos2025` (v1) is read-only.** Upstream replaced the v1 downloads in place, so the v1 database cannot be rebuilt. Any DDL or DML targeting it is a critical finding.
- **Join direction is load-bearing, and the held releases fix it.** The one verified association path from the spec-z compilation into the catalog is the compilation's own `Id_COSMOS25` crossmatch into `photometry_primary.id` (zero-separation coordinate identity, verified); associate compilation rows through `id_cosmos25 = photometry_primary.id` only. The catalog's `id_specz_khostovan25` does **not** resolve against the held DR1.1 compilation (measured field-scale separations; see `docs/research/specz-linkage-evidence.md`) and must not be used as a join key. `Id_specz` identifies a compilation entry; `Id_COSMOS25` associates it with a catalog source; neither is an array position — use identifier lookup with uniqueness and membership checks, never row position. A join written in the wrong direction produces a plausible number that is silently wrong; flag any cross-catalog join whose direction is not stated.
- **Grain is load-bearing.** The compilation ships two surfaces at different grains: `_unique` (one shipped representative row per compilation source, equal to `_all` at Priority 1 in the held release) and `_all` (every measurement). A `_unique` row is neither proof of uniqueness at COSMOS2025-source grain nor proof that other measurements agree; conflict diagnostics must consider all qualifying `_all` measurements. State the surface and denominator behind every count.
- **Unit conventions are asymmetric.** LePhare physical parameters are log10; CIGALE parameters are linear. Cross-code comparison is `lephare_log10_value - LOG10(cigale_linear_value)`. A comparison that omits the conversion is a scientific correctness bug that will pass every structural test.

## Severity calibration

- **Critical:** loss of source fidelity; null-by-inference; composed semantics; writes to the v1 database or to `/mnt/nvme01` holdings; unreviewed manifest, dictionary, or provenance changes; hand-edited generated artifacts; credentials in code, config, logs, or committed files; a cross-code comparison missing the log/linear conversion.
- **Warning:** missing or weakened test coverage on a changed code path; a new column or table without dictionary provenance; recovery or error-handling logic that discards validated work; unbounded retry loops; a cross-catalog join with unstated direction; queries without a bound on a 784k-row or larger table; documentation that contradicts `docs/project-state.md`.
- **Do not flag:** formatting already enforced by Ruff or the formatter; pre-existing Ruff findings in unchanged Phase 1 and inspection files; the retained finite sentinel values themselves, which are deliberate; frontmatter style in worklogs, which follows the central lifecycle template rather than the repo checker.

## Verification expectations

- Schema or dictionary changes need regenerated DDL, regenerated conformance cases, and evidence that generator byte-identity checks pass. Reviewing the generated diff alone is insufficient; the generator input is the change.
- New or modified ETL logic needs a test that asserts an observable value outcome, not just that the code runs. Sentinel handling, array element ordering, and type casts each need explicit cases.
- Database changes need a stated reversal, and the reversal must distinguish the phase before a validated load from the phase after it. A recovery path that drops loaded and verified data is a design defect, not a safe default.
- Any claim of row counts, column counts, or match rates in documentation needs a query or worklog line that produced it. Numbers restated from a previous document are not evidence.
- Long-running operations should report elapsed time and peak RSS. This project runs multi-hour loads against enterprise NVMe; silent cost is a review concern.

## Reviewing large generated changes

This repository produces exhaustive generated evidence: conformance case modules, DDL, schema documentation, and verification surfaces routinely run to tens of thousands of lines. Do not line-review generated artifacts as if they were handwritten code. Review the generator, its inputs, its invariants, and its tests, then spot-check the output for conformance to those invariants. Where a change spans many gates, partition the review by gate or by domain rather than treating the whole diff as one unit; each commit is a self-contained unit with a matching worklog checkpoint.

## Security and operational concerns

- Cluster-admin credentials are bootstrap-only. Runtime access uses the `PGSQL01_COSMOS2025_V11_*` variables and the read-only `cosmos2025_v11_ro` role.
- The credential handoff at `internal-files/cosmos2025-v11.env` is gitignored and mode 0600. Flag anything that would commit it, print its contents, or copy values into tracked config.
- Never flag or reproduce a secret value in review output itself.

## Review summary style

Lead with the highest-severity finding and its concrete consequence for the data or the science, not with a count of issues. Prefer small explicit fixes over broad refactors; this repository favors narrow, reversible changes with evidence attached. Where a finding is a judgment call rather than a defect, say so and state the trade rather than asserting a rule.
