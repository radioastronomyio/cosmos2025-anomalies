## Codex Review: COSMOS2025 Phase 1 Pre-Commit Audit

### Context

This is a pre-commit review of the COSMOS2025 anomaly detection repository at the end of Phase 1 (ETL pipeline complete). The repository contains a pipeline that extracts the COSMOS-Web DR1 photometric catalog (784,016 astronomical sources) from FITS format, loads it into PostgreSQL, and verifies data integrity. Phase 2 (feature engineering for anomaly detection) has not started.

Read `AGENTS.md` first for full project context, then `ROADMAP.md` for the science strategy.

---

### Review Scope

Perform two reviews: a **structural review** of the repository and a **science review** of the ETL verification results.

---

### Part 1: Structural Review

Check the repository against its own documented conventions (from AGENTS.md and the documentation standards).

**a. Documentation completeness:**
- Does every directory with content have an interior README?
- Do all Markdown files have YAML frontmatter?
- Are there any stale or orphaned files (files referenced nowhere, files that reference deleted content)?
- Is the `docs/` directory organized logically?

**b. Code quality:**
- Do `src/etl/extract_catalog.py` and `src/etl/verify_catalog.py` have proper module docstrings, function docstrings, and inline comments?
- Are there any hardcoded paths that should use `configs/data_paths.yaml`?
- Are there any hardcoded credentials?
- Is error handling adequate (especially for DB connections and file I/O)?
- Is the code style consistent?

**c. Configuration:**
- Does `configs/data_paths.yaml` cover all data paths referenced in the scripts?
- Are there any path references in code that aren't in the config?

**d. Consistency:**
- Does `AGENTS.md` accurately reflect the current repository state?
- Does `README.md` accurately reflect the current project status?
- Does `ROADMAP.md` need updates given Phase 1 completion?
- Are the work logs consistent with the actual artifacts in the repo?

**e. Git hygiene:**
- Are there files that should be gitignored but aren't (generated reports, parquet files, cache directories)?
- Is `.gitignore` adequate?

---

### Part 2: Science Review

Review `docs/verification-report.md` (or `docs/phase1-verification-report.html` if it exists) and the verification script for scientific correctness.

**a. Unit handling:**
- The verification report documents that LePhare physical parameters (mass_med, sfr_med, ssfr_med) are in log10 space while CIGALE parameters (mass, sfr_inst, ssfr_cigale) are in linear space. Verify this is handled correctly in all cross-code comparison queries in `src/etl/verify_catalog.py`.
- Check whether the derived column `ssfr_cigale` (computed as `sfr_inst / mass` in the ETL) is in the correct units (linear yr⁻¹).
- Confirm the column documentation in `docs/reference/columns-lephare-photometrric-redshifts.txt` and `docs/reference/columns-cigale-physical-parameters.txt` supports the unit assignments.

**b. Sentinel conversion:**
- Review sentinel values (-999, -99, 999999) against `docs/reference/quality-flags.txt` and the column schema files.
- Verify that the ETL script converts all documented sentinels and does not convert values that are legitimate data (e.g., `wht_*` columns where 0.0 means "no coverage" and should be preserved).

**c. Verification completeness:**
- Are there important data quality checks missing from the verification script?
- Are the O1 readiness thresholds (0.3 dex mass, 0.5 dex SFR) scientifically reasonable for this dataset?
- The CIGALE NULL rate is 24.9% vs the ~16% cited in the catalog paper. Is this discrepancy addressed or explained?

**d. Cross-table integrity:**
- The supplementary catalogs (LSS overdensity, galaxy groups) join to the master catalog on `id`. Verify the join keys are correct and the coverage fractions (20.9% for LSS, 46.5% for group memberships) are plausible.

---

### Output Format

Produce a review document organized by the sections above. For each finding:
- **Severity**: Critical / Warning / Note / Good
- **Location**: File and line number (or section)
- **Finding**: What you observed
- **Recommendation**: What should change (if anything)

End with a summary: is the repository ready for Phase 2, or are there blockers?

---

### Files to Examine

Priority order:
1. `AGENTS.md` — project context (read first)
2. `ROADMAP.md` — science strategy
3. `src/etl/extract_catalog.py` — ETL pipeline
4. `src/etl/verify_catalog.py` — verification script
5. `docs/verification-report.md` — verification results
6. `configs/data_paths.yaml` — path configuration
7. `src/etl/create_schema.sql` — database DDL
8. `docs/reference/columns-lephare-photometrric-redshifts.txt` — LePhare column docs
9. `docs/reference/columns-cigale-physical-parameters.txt` — CIGALE column docs
10. `docs/reference/quality-flags.txt` — flag definitions
11. `docs/research/etl-pipeline-one-pager.md` — ETL specification
12. `README.md` — project overview
13. `work-logs/` — session logs
14. All interior READMEs
