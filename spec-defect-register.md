<!--
---
title: "Spec Defect Register"
description: "Record of authored defects discovered during spec execution and their remediation"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-17"
version: "1.0"
status: "Active"
tags:
  - type: register
  - domain: defects
related_documents:
  - "[AGENTS.md](../AGENTS.md)"
  - "[Spec P2R-02](../spec/2026-08-16-cosmos2025-spec-p2r-02-manifest-amendment.md)"
---
-->

# Spec Defect Register

This register records authored defects discovered during spec execution. Each entry carries an ID, attribution, description, and remediation. Defects are not deleted; they remain as a historical record.

---

## Registered Defects

### D-2026-08-17-001: Mutable `.git/**` included in provenance boundary

**Attribution:** Spec author (VintageDon)

**Spec:** P2R-02 (Manifest Re-pin and Readiness Review Amendment)

**Description:** The v1.1 manifest included 29 files under the checkout's `.git/` directory (config, index, hooks, LFS store, temporaries) alongside the 52 worktree artifacts. Git machinery is mutable transport layer, not data. P2R-02 froze exactly seven changed rows (the materialized LFS files), which prevented correcting the boundary without violating the spec's scope constraint.

**Remediation:** P2R-02A gate A1.2 excluded `.git/**` from the manifest boundary by regenerating the speczcompilation section from the worktree-only inventory, validated all 52 retained rows against disk, and rewrote manifest §1/§2 to state the durable boundary explicitly. The validator now rejects any row containing `/.git/` or starting `.git/`.

---

### D-2026-08-17-002: Annotated tag asserted without verification

**Attribution:** Spec author (VintageDon)

**Spec:** P2R-02 (Manifest Re-pin and Readiness Review Amendment)

**Description:** The spec's scope section asserted "annotated tag `DR1.1` dated 2025-10-31" as a provenance fact. Gate 2.2 verified the tag but did not verify its object type. The live checkout's `DR1.1` ref resolves as a lightweight tag (object type `commit`, no tag object), which is a materially different provenance anchor for downstream consumers who inspect the ref type.

**Remediation:** P2R-02A gate A1.1 explicitly checked the object type (`git for-each-ref` → `commit`), confirmed it lightweight, and gate A1.2 recorded the observed type in manifest §2. The spec's defect-register entry records that the assertion was unverified and the amendment corrected it.

---

### D-2026-08-17-003: Lifecycle template misalignment

**Attribution:** Spec author (VintageDon)

**Spec:** P2R-02 (Manifest Re-pin and Readiness Review Amendment)

**Description:** The P2R-02 worklog frontmatter and closeout trailer duplicated stale lifecycle rules (path naming, `spec_ref` handling, UTC run window placeholder, attestation trailer format) instead of deferring to the current `spec-closeout` skill and central worklog template. This caused the central registry entry to use an incorrect worklog path and the closeout attestation to reference a spec path that no longer matched the central queue practice.

**Remediation:** P2R-02A gate A1.4 renamed the worklog to the spec-mirrored filename (`2026-08-16-cosmos2025-worklog-p2r-02-manifest-amendment.md`), migrated frontmatter to the current template (added `spec_ref`, corrected key names), populated the original runtime record from the operator-captured panel without changing counter semantics, and repaired the registry row to the renamed worklog and combined amendment outcome. The bad `Spec:` trailer on commit `0f3e31d` was not rewritten (recorded as part of this defect); the amendment closeout supplies the correct resolving attestation additively.

---