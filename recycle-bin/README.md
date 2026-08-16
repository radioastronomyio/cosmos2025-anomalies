<!--
---
title: "Recycle"
description: "Agent trash can for files deemed unnecessary"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-15"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: documentation
---
-->

# Recycle

Agent trash can. This directory receives files that an agent has determined are unnecessary for the project. Its contents are gitignored; only this README is tracked.

**Agents never delete files.** When an agent determines a file is unnecessary, it moves the file here and documents the reason in the table below. The human reviews this directory during QC and either permanently deletes the files or restores them to their original location.

This convention exists because agents sometimes misjudge what's needed. A deleted file requires re-creation from memory or template; a recycled file requires a move command. The cost asymmetry favors recycling.

---

## 1. Recycled Files

| File | Original Location | Reason | Date |
|------|--------------------|--------|------|
| — | — | Empty at repository onboarding | 2026-08-15 |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [AGENTS.md](../AGENTS.md) | Documents the recycle convention |

---

## 5. Rules

**Agents must never recycle:**

- Anything in `internal-files/` (human's source materials)
- Templates in `docs/documentation-standards/` (reused for future documents)
- Licenses, CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md (standard repo furniture)
- AGENTS.md, README.md (agent context and project identity)

**Agents may recycle with justification:**

- Script header templates for languages not in the project's tech stack
- Gitignore sections for technologies not in use (but prefer commenting out over removing)
- Utility scripts the project won't use (e.g., `shared/generate_tree.py`)
