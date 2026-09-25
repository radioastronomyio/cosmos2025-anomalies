<!--
---
title: "Research"
description: "Research-direction documents, pipeline design records, and review artifacts"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: astronomy
related_documents:
  - "[Science Opportunities](science-opportunities.md)"
  - "[ETL v2 Verification Surface](etl-v2-verification.md)"
---
-->

# Research

Research-direction and review artifacts: the selected science opportunities,
the generated ETL v2 verification surface, the v1 ETL design record, the
Phase 1 code review, and the v1.1 readiness review.

---

## 1. Contents

```
research/
├── science-opportunities.md          # O1/O5 selection (frozen input to T_A v2)
├── etl-v2-verification.md            # Evidence-generated operator decision surface
├── specz-linkage-evidence.md         # P2R-04 linkage review surface (disposed by P2R-05)
├── specz-linkage-propagation-inventory.md  # P2R-04b gate A2.1 propagation trace
├── specz-science-dispositions.md     # P2R-05 operator approval and decision record
├── specz-science-p2r05/              # P2R-05 evidence, coverage, review, tile map, upstream draft
├── v11-readiness-review.md           # ETL v2 approval surface (P2R-01)
├── etl-pipeline-one-pager.md         # v1 ETL design record (historical)
├── phase1-precommit-codex-review.md  # Phase 1 code review (historical)
└── README.md                         # This file
```

---

## 2. Files

| File | Description | Status |
|------|-------------|--------|
| [science-opportunities.md](science-opportunities.md) | O1 algorithmic disagreement (lead) and O5 contextual anomalies; deprioritization record | ✅ Active |
| [specz-linkage-evidence.md](specz-linkage-evidence.md) | P2R-04 spec-z linkage findings, recovery populations, selection function, and the deferred dispositions D-01..D-07 | ✅ Disposed by P2R-05 |
| [specz-science-dispositions.md](specz-science-dispositions.md) | Operator approval of P2R-05 v1.0 with P-01..P-09 frozen; D-01..D-07 linkage; policy/priors/adoption separation | ✅ Active |
| [specz-science-p2r05/](specz-science-p2r05/README.md) | P2R-05 run evidence: gate 5.3 reproduction, coverage and sensitivity, frozen tile map, review document with S5-Q01..Q05, local upstream draft | 📝 Adoption review pending |
| [specz-linkage-propagation-inventory.md](specz-linkage-propagation-inventory.md) | P2R-04b trace of every artifact carrying a separation statistic from the defective pairing code, with in-scope disposition | ✅ Active |
| [etl-v2-verification.md](etl-v2-verification.md) | Generated Gate 3.13 findings, complete evidence appendices, deferred questions, and blank operator dispositions | 📝 Draft |
| [v11-readiness-review.md](v11-readiness-review.md) | Findings and closed questions the operator answers to approve ETL v2 | ✅ Active |
| [etl-pipeline-one-pager.md](etl-pipeline-one-pager.md) | v1 ETL schema design and execution record | 🗄️ Archived |
| [phase1-precommit-codex-review.md](phase1-precommit-codex-review.md) | Codex review of the Phase 1 pipeline | 🗄️ Archived |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Documentation](../README.md) | Parent directory |
