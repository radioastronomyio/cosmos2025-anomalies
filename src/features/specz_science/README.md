# specz_science — Spectroscopic Association and Eligibility Product (P2R-05)

Builders, policy validation, verification, and installation interfaces for
spec P2R-05: the source-level spectroscopy product in
`cosmos2025_v11.analysis`. Science policy is frozen in
`configs/specz_science_policy_v1.yaml` and validated by
[`policy.py`](policy.py); no default or override may change it.

## Module map

| Module | Purpose |
|---|---|
| `policy.py` | Frozen policy loading, strict structural/domain validation, flag→confidence mapping |
| `config.py` | Repository paths, fixed analyst credential handoff, read-only analyst connections |
| `preflight.py` | Gate 5.1 access verification, pin comparison, source/v1 before-state |
| `snapshot.py` | Consistent read-only capture of the build's consumed inputs |
| `canonical.py` | Canonical serialization, content digests, deterministic run identity |
| `build.py` | Measurement audit and source summary construction (P-01 through P-05) |
| `splits.py` | P-06 frozen SHA-256 tile partitions |
| `install.py` | Bounded bootstrap of the four `analysis.specz_p2r05_*` tables |
| `verify.py` | Independent reductions for gates 5.3 and 5.7 |
| `coverage.py` | P-07 diagnostics and the three fixed sensitivity variants |

## Boundaries

- Runtime extraction and installed-product verification use the fixed
  analyst contract (`PGSQL01_COSMOS2025_V11_*`, connection-time read-only).
  Administrative credentials appear only through the scoped Doppler runtime
  for the bounded inherited-verification and bootstrap purposes named in the
  spec.
- The `source` schema and the v1 database are read inputs; this package
  never writes them.
- All products carry `pending_scientific_adoption`; nothing here creates a
  consumer alias or marks adoption.
