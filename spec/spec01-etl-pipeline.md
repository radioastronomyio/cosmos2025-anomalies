## Task: COSMOS2025 ETL Pipeline — FITS to PostgreSQL

Mode: Code

---

### Objective

The COSMOS-Web DR1 master catalog (784,016 sources, 8.4GB FITS file with 6 extensions) is extracted into 4 parquet files and loaded into PostgreSQL tables on psql01. When complete, `SELECT count(*) FROM catalog.photometry_core` returns 784,016, all four tables join cleanly on `id`, sentinel values have been converted to NULL, and verification queries confirm data integrity.

---

### Prerequisites (do this first)

1. **Pull latest repo changes:**
   ```bash
   cd /opt/repos/cosmos2025-anomalies && git pull
   ```

The `cosmos2025` database already exists on psql01 and the DDL (`src/etl/create_schema.sql`) has been executed. 7 tables exist in the `catalog` schema: photometry_core, lephare, cigale, morphology, lss_overdensity, galaxy_groups, galaxy_group_memberships. All tables are empty, waiting for data load.

---

### Scope

**Modify:**
- `src/etl/` — new ETL script(s)
- `/mnt/nvme02/cosmosweb2025-dr1/processed/parquet/` — output parquet files
- `/mnt/nvme02/cosmosweb2025-dr1/staging/` — temp workspace (if needed)
- `cosmos2025` database on psql01

**Reference (do not modify):**
- `AGENTS.md` — project context, data locations, conventions
- `configs/data_paths.yaml` — all file paths and DB credential env var names
- `src/etl/create_schema.sql` — DDL (already executed, use as column reference)
- `docs/research/etl-pipeline-one-pager.md` — full ETL specification
- `docs/reference/master-catalog-profile.md` — catalog structure and profiling results

---

### Deliverables & Validation

1. **Python ETL script at `src/etl/extract_catalog.py`**
   - [ ] Reads master catalog FITS from path in `configs/data_paths.yaml`
   - [ ] Opens FITS with `astropy.io.fits` using `memmap=True`
   - [ ] Loads DB credentials from `/opt/agents/.env` via `python-dotenv`
   - [ ] Loads data paths from `configs/data_paths.yaml` via `pyyaml`
   - [ ] Produces 4 parquet files in `/mnt/nvme02/cosmosweb2025-dr1/processed/parquet/`

2. **`photometry_core.parquet` — Extension 1 extraction**
   - [ ] Contains only scalar columns (no array columns like `flux_aper_*`, `mag_aper_*`)
   - [ ] Includes `id`, position, detection stats, per-band scalar photometry (snr, wht, flux_auto, flux_err_auto, mag_auto for 6 JWST+HST bands), compactness, Kron params, Sérsic params, flags, `mag_model_*` for all 37 bands
   - [ ] Excludes `flux_model_*`, `flux_err_uncal_model_*`, `flux_err_cal_model_*` band-repeated columns
   - [ ] All column hyphens replaced with underscores (e.g., `mag_model_hst-f814w` → `mag_model_hst_f814w`)
   - [ ] Sentinels `-999`, `-999.0` converted to NaN; `0.0` in `wht_*` columns preserved
   - [ ] Row count: 784,016

3. **`lephare.parquet` — Extension 2 extraction**
   - [ ] All 43 columns from Extension 2
   - [ ] `id` column injected from Extension 1 (by row position, not join)
   - [ ] Column name sanitization applied
   - [ ] Sentinels `-999`, `-99` converted to NaN
   - [ ] Row count: 784,016

4. **`cigale.parquet` — Extension 4 extraction**
   - [ ] All 54 columns from Extension 4
   - [ ] `id` column injected from Extension 1 (by row position)
   - [ ] Derived column `ssfr_cigale = sfr_inst / mass` computed (NaN where mass is 0 or NaN)
   - [ ] Column name sanitization applied
   - [ ] Sentinels `-999` converted to NaN; existing NaN preserved
   - [ ] Row count: 784,016

5. **`morphology.parquet` — Extension 5 extraction**
   - [ ] ~30 columns: mean/std class probabilities (3 bands × 4 classes × 2 = 24), morph_flag (3), delta (3), plus `id`
   - [ ] Skips all per-run probability columns (`sph_f444w_0`, `sph_f444w_1`, ..., etc.)
   - [ ] `id` column injected from Extension 1 (by row position)
   - [ ] Sentinels `999999` in morph_flag columns converted to NaN/None
   - [ ] Row count: 784,016

6. **PostgreSQL load (all 4 core tables)**
   - [ ] Each parquet loaded into its corresponding `catalog.*` table on psql01
   - [ ] Bulk load via `COPY` or psycopg2 bulk insert (not row-by-row INSERT)
   - [ ] `SELECT count(*) FROM catalog.photometry_core` returns 784,016
   - [ ] `SELECT count(*) FROM catalog.lephare` returns 784,016
   - [ ] `SELECT count(*) FROM catalog.cigale` returns 784,016
   - [ ] `SELECT count(*) FROM catalog.morphology` returns 784,016

7. **Supplementary catalog load**
   - [ ] `hatamnia_lss_v1.fits` loaded into `catalog.lss_overdensity` — check column mapping against DDL
   - [ ] `deep-galaxy-group-catalog-groups.txt` loaded into `catalog.galaxy_groups`
   - [ ] `deep-galaxy-group-catalog-memberships.txt` loaded into `catalog.galaxy_group_memberships`
   - [ ] Supplementary file paths read from `configs/data_paths.yaml`

8. **Verification queries pass**
   - [ ] All 4 core tables return 784,016 rows
   - [ ] `SELECT COUNT(*) FILTER (WHERE mass_med IS NULL) FROM catalog.lephare` returns > 0 (sentinels converted)
   - [ ] Cross-code join works: `SELECT l.id, l.mass_med, c.mass FROM catalog.lephare l JOIN catalog.cigale c ON l.id = c.id LIMIT 5` returns valid rows
   - [ ] No `-999` or `999999` values remain in any table (spot check key columns)

---

### Constraints

- Use `memmap=True` when opening the 8.4GB FITS file
- Column inclusion/exclusion lists are defined in the ETL one-pager — follow them exactly
- Do not modify raw data files under `/mnt/nvme02/cosmosweb2025-dr1/catalogs/` or `supplementary/`
- Do not modify any files outside `src/etl/` and the processed/staging output directories
- The group catalog files are pipe-delimited text files, not FITS — inspect headers before loading
- If a column in the FITS file doesn't match the DDL, log a warning and skip it rather than failing silently
- Create output directories (`processed/parquet/`, `processed/derived/`, `staging/`) if they don't exist

---

**Environment:**
- ML01 bare metal (5950X / 128G / A4000)
- Python environment: `/opt/agents/venv/` (activate before running)
- Required packages: `astropy`, `numpy`, `pyarrow`, `psycopg2-binary`, `python-dotenv`, `pyyaml`
- Install any missing packages into the venv
- Repository: `/opt/repos/cosmos2025-anomalies/`
- Data: `/mnt/nvme02/cosmosweb2025-dr1/`
- Credentials: `/opt/agents/.env`
- Context: `AGENTS.md` at repo root
