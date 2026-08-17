<!--
---
title: "Tagging Strategy Guide"
description: "Controlled vocabulary for document classification in cosmos2025-anomalies"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: guide
  - domain: documentation
related_documents:
  - "[Primary README Template](primary-readme-template.md)"
  - "[Interior README Template](interior-readme-template.md)"
  - "[General KB Template](general-kb-template.md)"
  - "[Worklog README Template](worklog-readme-template.md)"
  - "[One-Pager Template](one-pager-template.md)"
  - "[Project Brief Template](project-brief-template.md)"
---
-->

# Tagging Strategy Guide

## 1. Purpose

This guide defines the controlled tag vocabulary for this repository, `cosmos2025-anomalies`. Consistent tagging enables human navigation and RAG system retrieval. The domain vocabulary below is authoritative: every domain tag used in any tracked file's frontmatter appears here, and additions require an entry here first.

---

## 2. Why Controlled Vocabulary

Uncontrolled tagging leads to synonyms fragmenting search (`database` vs `db` vs `databases`), inconsistent granularity (`postgres` vs `relational-database`), and tag proliferation that reduces signal. A controlled vocabulary defines allowed values upfront, ensuring consistency across contributors and time.

---

## 3. Tag Categories

Each category answers a different question about the document. Keep categories orthogonal; each captures a distinct dimension.

| Category | Question Answered | Required |
|----------|-------------------|----------|
| `type` | What kind of document is this? | Yes |
| `domain` | What subject area? | Yes |
| `status` | What's the lifecycle state? | Recommended |
| `tech` | What technologies involved? | When applicable |
| `framework` | What compliance framework? | When applicable |

---

## 4. Domain Tags

Domain tags are project-specific. Replace this section with your project's vocabulary.

### Building Your Domain Vocabulary

1. **Inventory content types.** What kinds of content does this repository contain? Group by function, not format.
2. **Define 5-12 domain values.** Cover your content without excessive overlap.
3. **Write boundary definitions.** One sentence per tag clarifying what belongs and what doesn't.

### Project Domain Vocabulary

The binding vocabulary for this repository. Boundary definitions clarify what belongs; when a document spans two domains, tag the primary function and multi-value only when genuinely split.

```yaml
domain:
  - astronomy           # Catalog science content: photometry, morphology, physical parameters, survey data products
  - cosmos-web          # COSMOS-Web survey specifics: DR1/v1.1 releases, tiles, holdings, release-level questions
  - anomaly-detection   # Outlier science: tension metrics, detection methods, candidate populations
  - data-engineering    # Data movement and structure: ETL design, manifests, structural profiles, database load
  - etl                 # The src/etl pipeline and its extraction/load mechanics specifically
  - feature-engineering # Derived feature computation (src/features): tension scalars, analysis-ready datasets
  - data-science        # Cross-cutting analysis, statistics, and ML methodology
  - spectroscopy        # Spectroscopic redshift compilations and spec-z join policy
  - sed-fitting         # LePhare/CIGALE SED-fitting outputs, parameters, and cross-code comparison
  - configuration       # configs/ wiring: data paths, environment contracts, credential injection
  - infrastructure      # Compute hosts, storage, database servers, environments
  - documentation       # Templates, standards, and meta-content about the repository itself
  - source-code         # src/ code organization and module structure
  - testing             # tests/ contents and validation procedures
  - work-logs           # Session worklogs in work-logs/
  - agent-specs         # Work specs in spec/
  - repository-audit    # Repo conformance, review, and audit documents
```

This vocabulary exceeds the 5-12 guidance deliberately: the repository predates the tagging standard, and coverage of every tag already in frontmatter use is a hard requirement. New domains follow the governance procedure in section 10.

### Boundary Rules

- If a document spans two domains, use the primary one. Multi-value only when genuinely split.
- Define clear boundaries between similar domains (e.g., `deployment` is standing up a service; `infrastructure` is the VM it runs on).

---

## 5. Type Tags

| Tag | Use For |
|-----|---------|
| `project-root` | Repository root README |
| `directory-readme` | Interior README for any directory |
| `worklog` | Work log entries and milestone documentation |
| `brief` | Project brief: build, engagement, or advisory slant |
| `one-pager` | Ideation capture (portable context unit for AI handoffs) |
| `guide` | Step-by-step procedures and how-to documents |
| `reference` | Lookup information: inventories, schemas, API docs |
| `specification` | Service specs, deployment definitions, formal requirements |
| `report` | Analysis, findings, audit results, summaries |
| `runbook` | Operational procedures for incident response or maintenance |
| `policy` | Governance policies: commitments and principles |
| `procedure` | SOPs: how activities are carried out |
| `review` | Audit and review findings about the repository or its products (e.g. pre-commit code review) |
| `roadmap` | The repository ROADMAP: planned phases, milestones, sequencing |

---

## 6. Status Tags

| Tag | Description |
|-----|-------------|
| `draft` | In development, not yet complete |
| `active` | Current, maintained, approved |
| `under-review` | Scheduled or triggered review in progress |
| `deprecated` | Superseded, avoid for new work |
| `archived` | Historical reference only |

---

## 7. Tech Tags

Use canonical names, lowercase, hyphenated. Build this list as your project's stack takes shape. Check for existing coverage before adding new tags.

```yaml
# This repository's technology stack
tech:
  - python
  - postgresql
  - astropy
  - pandas
  - numpy
  - psycopg2
  - scikit-learn
  - jwst
  - gpu
  - neo4j
  - kubernetes
```

---

## 8. Framework Tags

Compliance and governance framework references. Use only when a document directly implements or maps to a framework control. Skip this section entirely if your project doesn't involve compliance work.

This repository has no compliance component. The table below is intentionally empty; future documents that map to a framework add the row here first.

| Tag | Framework |
|-----|-----------|
| — | — |

---

## 9. Implementation

### Standard Frontmatter

```yaml
<!--
---
title: "Document Title"
description: "What this document covers"
author: "VintageDon (https://github.com/vintagedon/)"
date: "YYYY-MM-DD"
version: "1.0"
status: "Active"
tags:
  - type: guide
  - domain: astronomy
  - tech: python
related_documents:
  - "[Related Doc](path/to/doc.md)"
---
-->
```

### Conventions

- Use lowercase, hyphenated values (`ci-cd` not `CI/CD` or `cicd`)
- Tech tags use canonical names
- One value per line for readability, or array syntax for multi-value
- `related_documents` links use relative paths within the repo

---

## 10. Maintaining the Vocabulary

### Adding New Tags

1. Check if an existing tag covers the concept
2. If not, add the new tag with a boundary definition to this document
3. Backfill existing documents if the new tag applies retroactively

### Governance

- This document is the authoritative source for allowed tag values
- Prefer broader tags over proliferating specific ones
- Review additions for overlap with existing tags

---

## 11. References

| Resource | Description |
|----------|-------------|
| [Primary README Template](primary-readme-template.md) | Shows tag usage in repository root READMEs |
| [Interior README Template](interior-readme-template.md) | Shows tag usage in directory READMEs |
| [General KB Template](general-kb-template.md) | Shows tag usage for standalone docs |
| [Worklog README Template](worklog-readme-template.md) | Shows tag usage for work log entries |
| [One-Pager Template](one-pager-template.md) | Shows tag usage for ideation documents |
| [Project Brief Template](project-brief-template.md) | Shows tag usage for project briefs |
