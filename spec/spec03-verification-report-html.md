## Task: Phase 1 Verification Report with Charts

Mode: Code

---

### Objective

The verification script at `src/etl/verify_catalog.py` is expanded to produce a self-contained HTML report at `docs/phase1-verification-report.html` with embedded matplotlib charts (base64 PNG) alongside the existing tabular checks. The report serves as the Phase 1 milestone artifact: a professional, portable document that validates the ETL and provides the first look at O1 science readiness. The existing markdown report (`docs/verification-report.md`) continues to be generated as before.

---

### Prerequisites

```bash
cd /opt/repos/cosmos2025-anomalies && git pull
source /opt/agents/venv/bin/activate
pip install matplotlib  # if not already installed
```

The `cosmos2025` database is loaded and verified. All 7 tables exist in the `catalog` schema on psql01.

---

### Scope

Modify:
- `src/etl/verify_catalog.py` — add HTML report generation alongside existing markdown output

Create:
- `docs/phase1-verification-report.html` — the generated report (gitignored or committed, operator's choice)

Reference (do not modify):
- `AGENTS.md` — project context, unit reference
- `configs/data_paths.yaml` — DB credentials and paths
- `docs/verification-report.md` — existing markdown report (keep generating this too)

---

### Deliverables & Validation

1. HTML report generation added to verify_catalog.py
   - [ ] `write_html_report()` function generates a single self-contained HTML file
   - [ ] All charts are embedded as base64 PNG (no external files)
   - [ ] CSS is inline (no external stylesheets)
   - [ ] Both markdown and HTML reports are generated on each run
   - [ ] Script still prints summary to stdout

2. Report structure (HTML)
   - [ ] Header: project name, generation timestamp, database info, overall pass/fail summary
   - [ ] Unit reference table (LePhare=log10, CIGALE=linear) prominently displayed
   - [ ] All existing check sections rendered as styled tables (same data as markdown report)
   - [ ] Charts section with embedded figures (see chart list below)
   - [ ] Clean, professional CSS: readable fonts, alternating row colors, status icons, responsive layout
   - [ ] No JavaScript required (static HTML)

3. Charts to include (matplotlib, embedded as base64)

   a. Cross-code mass comparison scatter
   - [ ] X-axis: log10(cigale.mass), Y-axis: lephare.mass_med
   - [ ] 1:1 line overlaid
   - [ ] Color-coded by warn_flag (0 vs non-zero)
   - [ ] Subsample if needed for performance (random 50k points)
   - [ ] Title: "LePhare vs CIGALE Stellar Mass"

   b. Δlog M★ histogram
   - [ ] Histogram of (mass_med - LOG10(mass)) for dual-valid sources
   - [ ] Vertical lines at ±0.3 and ±0.5 dex thresholds
   - [ ] Annotate count in each tail region
   - [ ] Clip x-axis to [-3, 3] to exclude zombie fits (note clipped count)
   - [ ] Title: "Cross-Code Stellar Mass Disagreement"

   c. Δlog SFR histogram
   - [ ] Same format as mass histogram
   - [ ] Vertical lines at ±0.5 and ±1.0 dex thresholds
   - [ ] Clip x-axis to [-5, 5]
   - [ ] Title: "Cross-Code SFR Disagreement"

   d. warn_flag distribution bar chart
   - [ ] Horizontal bar chart of source counts per warn_flag value
   - [ ] Percentage labels on bars
   - [ ] Title: "Quality Flag Distribution"

   e. LePhare type classification pie chart
   - [ ] Galaxy / Star / QSO proportions
   - [ ] Title: "LePhare Source Classification"

   f. CIGALE mass vs chi2_red_best_fit scatter
   - [ ] X-axis: LOG10(mass), Y-axis: LOG10(chi2_red_best_fit)
   - [ ] Helps visualize where zombie fits cluster
   - [ ] Subsample for performance
   - [ ] Title: "CIGALE Fit Quality vs Stellar Mass"

   g. Redshift distribution (lephare.zfinal)
   - [ ] Histogram of zfinal for galaxies (type=0, warn_flag=0)
   - [ ] Bin width ~0.1
   - [ ] Title: "Photometric Redshift Distribution (Clean Galaxies)"

   h. Sky coverage plot
   - [ ] RA vs Dec scatter of all sources
   - [ ] Color-coded by warn_flag or density
   - [ ] Subsample for performance
   - [ ] Title: "COSMOS-Web DR1 Sky Coverage"

4. CSS styling
   - [ ] Professional, minimal design (no frameworks, inline CSS only)
   - [ ] Dark header bar with project name and timestamp
   - [ ] White content area with max-width ~1100px, centered
   - [ ] Tables: alternating row colors, left-aligned text, fixed-width status column
   - [ ] Status icons: ✅ ❌ ⚠️ ℹ️ rendered in table cells
   - [ ] Charts: centered, max-width 800px, subtle border/shadow
   - [ ] Section headers with subtle bottom borders
   - [ ] Print-friendly (no dark backgrounds in print media query)

---

### Constraints

- Charts use matplotlib with `Agg` backend (no display). Save to BytesIO, base64 encode, embed as `<img src="data:image/png;base64,...">`.
- Subsample large datasets (>50k points) for scatter plots to keep file size reasonable and rendering fast. Use random seed for reproducibility.
- All database queries should use the same connection pattern as the existing script (load_config, get_db_connection).
- Keep the existing `run_checks()` and `write_report()` functions intact. Add new functions for chart generation and HTML output.
- Do not introduce any external dependencies beyond matplotlib (already needed).
- The HTML file should be under 10MB total.

---

Environment:
- ML01 bare metal, Python venv at `/opt/agents/venv/`
- Repository: `/opt/repos/cosmos2025-anomalies/`
- Data: cosmos2025 database on psql01 (10.25.20.8)
- Credentials: `/opt/agents/.env`
- Context: `AGENTS.md` at repo root
