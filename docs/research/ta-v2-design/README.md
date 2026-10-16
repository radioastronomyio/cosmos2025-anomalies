<!--
---
title: "T_A v2 Design"
description: "Proposed scientific design contract for the T_A v2 cross-code disagreement features: input contract, feature contract, scientific design, evaluation protocol, synthetic validation, and review surface"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-05"
version: "1.0"
status: "Active - proposed, pending approval"
tags:
  - type: directory-readme
  - domain: astronomy
  - domain: sed-fitting
  - domain: feature-engineering
related_documents:
  - "[P2R-05 Review and S5 answers](../specz-science-p2r05/review.md)"
  - "[Unit Conventions](../../reference/unit-conventions.md)"
  - "[Project State](../../project-state.md)"
---
-->

# T_A v2 Design (P2R-06)

Everything in this directory is a **proposed design contract** for the T_A v2
feature unit. Nothing here is adopted, fitted, installed, or released. Every
scientific choice carries `proposed_not_adopted`; the approval surface is the
closed question set TA2-Q01 through TA2-Q06 in [review.md](review.md), which
only Don answers. Implementation, fitting, database installation, production
scoring, and publication all await a later named approval.

## Contents

| Path | Content | Gate |
|---|---|---|
| [input-contract.md](input-contract.md) | S5 decision binding, interface inclusions/exclusions, inherited identities, explicit populations, and the per-field source-semantics inventory | 6.1 |
| [input-identity.json](input-identity.json) | Machine-readable identity record (pins, digests, locators) for the design boundary | 6.1 |
| [feature-contract.yaml](feature-contract.yaml) | Machine-readable proposed outputs: grains, formulas, states, precedence, reason codes, permitted fitters, forbidden dependencies | 6.2 |
| [scientific-design.md](scientific-design.md) | Rationale, alternatives, and limits for every scientific choice in the feature contract | 6.2 |
| [fixtures.json](fixtures.json) | Synthetic-only fixture corpus with expected results and named mutation controls | 6.3 |
| [validation-results.json](validation-results.json) | Recorded validator results: case IDs, expected/observed behaviour, hashes, exit codes | 6.3 |
| [evaluation-protocol.md](evaluation-protocol.md) | Preregistered development/validation/holdout plan, split-use rules, sensitivity plan, uncertainty plan | 6.4 |
| [review.md](review.md) | The review surface: findings and closed questions TA2-Q01 through TA2-Q06 | 6.4 |

## Standing rules for this directory

- No observed T_A values are fitted, ranked, or reported; every illustrative
  number is labelled synthetic.
- The three frozen inputs (the ~0.24 dex conditional mass offset, the
  censoring-dominated SFR ranking, the dimensionally incoherent historical
  `chi2_ratio`) are design inputs, never re-diagnosed or re-voted.
- A secure spectroscopic redshift is never treated as stellar-mass or SFR
  truth, and the separate labelled diagnostic population has no path into
  primary fitting.
- The sealed P2R-05 product and every source table are read-only inputs.
