## Task: Interior READMEs + Dual-Audience Script Commenting

Mode: Code

---

### Objective

All directories with content get interior READMEs following the project's documentation standards. The two ETL scripts receive dual-audience comments and proper script headers. When complete, any developer or AI agent landing in any directory can orient immediately.

---

### Prerequisites

```bash
cd /opt/repos/cosmos2025-anomalies && git pull
```

---

### Scope

**Modify:**
- `src/etl/extract_catalog.py` — add dual-audience comments and script header
- `src/etl/verify_catalog.py` — add dual-audience comments and script header

**Create:**
- `src/etl/README.md`
- `src/README.md`
- `configs/README.md`
- `spec/README.md`
- `work-logs/README.md`

**Reference (do not modify content, only read for context):**
- `AGENTS.md` — project conventions, repo structure
- `docs/README.md` — example of an existing interior README
- All files in directories receiving READMEs (to describe them accurately)

---

### Deliverables & Validation

1. **Interior READMEs (5 files)**

   Each README follows this pattern:
   - YAML frontmatter (title, description, status, tags)
   - H1 title matching directory purpose
   - 1-2 sentence description of what this directory contains and why
   - File inventory table (filename, description) for current contents
   - Link to parent README one level up

   Specific READMEs:

   - [ ] `src/README.md` — describes the source code directory, links to `src/etl/`, `src/features/`, `src/detection/`, `src/utils/`
   - [ ] `src/etl/README.md` — describes the ETL pipeline scripts. Lists extract_catalog.py, verify_catalog.py, create_schema.sql, profile_master_catalog.py with one-line descriptions. Notes that ETL is Phase 1 complete.
   - [ ] `configs/README.md` — describes the configuration directory. Lists data_paths.yaml. Notes the credential loading pattern (dotenv from /opt/agents/.env).
   - [ ] `spec/README.md` — describes the agent execution prompts directory. Lists all spec files. Notes these are structured prompts for KC/OpenCode/Codex.
   - [ ] `work-logs/README.md` — describes the work log directory. Lists existing logs. Notes the naming convention (worklog-YYYY-MM-DD-topic.md).

2. **Dual-audience commenting on `src/etl/extract_catalog.py`**

   Dual-audience means two layers:
   - **Operator comments** (brief, what-it-does): inline comments a sysadmin or data engineer can scan
   - **Developer comments** (why, edge cases): docstrings and block comments explaining design decisions

   - [ ] Module-level docstring updated with: purpose, usage, dependencies, output locations, unit conventions
   - [ ] Each function has a proper docstring (purpose, args, returns, side effects)
   - [ ] Sentinel conversion logic has comments explaining why each sentinel value exists
   - [ ] The PHOT_SKIP_PREFIXES list has a comment explaining what's being skipped and why
   - [ ] The id injection pattern has a comment explaining why (extensions lack id column)
   - [ ] The ssfr_cigale derivation has a comment noting it's not in the original catalog
   - [ ] The COPY FROM column reordering has a comment explaining why it's needed
   - [ ] No code changes — comments only

3. **Dual-audience commenting on `src/etl/verify_catalog.py`**

   - [ ] Module-level docstring updated with: purpose, usage, output files, what "PASS" means
   - [ ] Unit validation section has comments explaining the log10 vs linear distinction
   - [ ] O1 readiness section has comments explaining what the thresholds mean scientifically
   - [ ] The COSMOS field boundary constants have a comment citing the source
   - [ ] No code changes — comments only

---

### Constraints

- Do not modify any code logic, only add comments and docstrings
- Do not modify any existing README files (docs/README.md, shared/README.md)
- Interior READMEs should be concise (under 50 lines each)
- Follow existing YAML frontmatter conventions visible in other project files
- Comment style: `#` for inline, `"""` for docstrings, no block `/* */`

---

**Environment:**
- ML01 bare metal
- Repository: `/opt/repos/cosmos2025-anomalies/`
- Context: `AGENTS.md` at repo root
