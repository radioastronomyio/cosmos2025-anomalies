-- =============================================================================
-- COSMOS2025 Anomaly Detection — PostgreSQL Schema DDL
-- =============================================================================
-- Database: cosmos2025 on psql01 (10.25.20.8)
-- Schema:   catalog
--
-- Source:    COSMOS-Web DR1 Master Catalog (Shuntov et al. 2025)
--           + Hatamnia et al. 2025 LSS overdensity catalog
--           + Toni et al. 2025 galaxy group catalog
--
-- Notes:
--   - All FITS column hyphens sanitized to underscores for PostgreSQL
--   - Extensions 3 (SE++APER) and 6 (B+D) skipped entirely (Phase 2)
--   - Sentinel values (-999, -99, 999999) converted to NULL during ETL
--   - All tables join on id (from Extension 1, row-aligned across extensions)
--
-- Generated: 2026-03-15
-- =============================================================================

-- Create dedicated database (run as superuser, then connect to it)
-- CREATE DATABASE cosmos2025;

-- Connect to cosmos2025 before running the rest
-- \c cosmos2025

CREATE SCHEMA IF NOT EXISTS catalog;

-- =============================================================================
-- TABLE 1: photometry_core
-- Source: Extension 1 (PHOTOMETRY HOTCOLD AND SE++)
-- Rows: 784,016
-- Columns: ~158 (scalar only — array columns and flux_model/flux_err skipped)
-- =============================================================================

CREATE TABLE catalog.photometry_core (

    -- Identity & position
    id                          BIGINT PRIMARY KEY,
    segment_id                  BIGINT,
    tile                        VARCHAR(4),
    id_specz_khostovan25        BIGINT,         -- -999 sentinel → NULL
    ra                          DOUBLE PRECISION NOT NULL,
    dec                         DOUBLE PRECISION NOT NULL,
    x_image                     DOUBLE PRECISION,
    y_image                     DOUBLE PRECISION,
    a_image                     DOUBLE PRECISION,
    b_image                     DOUBLE PRECISION,
    theta_image                 DOUBLE PRECISION,
    theta_world                 DOUBLE PRECISION,

    -- Detection statistics
    chi2_max                    DOUBLE PRECISION,
    mode                        VARCHAR(4),     -- 'cold' or 'hot'
    fwhm                        DOUBLE PRECISION,
    seg_area                    DOUBLE PRECISION,

    -- Per-band scalar photometry: HST F814W
    snr_hst_f814w               DOUBLE PRECISION,
    wht_hst_f814w               DOUBLE PRECISION,   -- 0.0 = no coverage (preserve)
    flux_auto_hst_f814w         DOUBLE PRECISION,
    flux_err_auto_hst_f814w     DOUBLE PRECISION,
    mag_auto_hst_f814w          DOUBLE PRECISION,

    -- Per-band scalar photometry: JWST F115W
    snr_f115w                   DOUBLE PRECISION,
    wht_f115w                   DOUBLE PRECISION,
    flux_auto_f115w             DOUBLE PRECISION,
    flux_err_auto_f115w         DOUBLE PRECISION,
    mag_auto_f115w              DOUBLE PRECISION,

    -- Per-band scalar photometry: JWST F150W
    snr_f150w                   DOUBLE PRECISION,
    wht_f150w                   DOUBLE PRECISION,
    flux_auto_f150w             DOUBLE PRECISION,
    flux_err_auto_f150w         DOUBLE PRECISION,
    mag_auto_f150w              DOUBLE PRECISION,

    -- Per-band scalar photometry: JWST F277W
    snr_f277w                   DOUBLE PRECISION,
    wht_f277w                   DOUBLE PRECISION,
    flux_auto_f277w             DOUBLE PRECISION,
    flux_err_auto_f277w         DOUBLE PRECISION,
    mag_auto_f277w              DOUBLE PRECISION,

    -- Per-band scalar photometry: JWST F444W
    snr_f444w                   DOUBLE PRECISION,
    wht_f444w                   DOUBLE PRECISION,
    flux_auto_f444w             DOUBLE PRECISION,
    flux_err_auto_f444w         DOUBLE PRECISION,
    mag_auto_f444w              DOUBLE PRECISION,

    -- Per-band scalar photometry: JWST F770W (MIRI — 55% zero-weight)
    snr_f770w                   DOUBLE PRECISION,
    wht_f770w                   DOUBLE PRECISION,
    flux_auto_f770w             DOUBLE PRECISION,
    flux_err_auto_f770w         DOUBLE PRECISION,
    mag_auto_f770w              DOUBLE PRECISION,

    -- Compactness & surface brightness
    c_f444w                     DOUBLE PRECISION,
    mu_max_hst_f814w            DOUBLE PRECISION,
    mu_max_f115w                DOUBLE PRECISION,
    mu_max_f150w                DOUBLE PRECISION,
    mu_max_f277w                DOUBLE PRECISION,
    mu_max_f444w                DOUBLE PRECISION,
    mu_max_f770w                DOUBLE PRECISION,

    -- Kron aperture parameters
    kron_rad                    DOUBLE PRECISION,
    kron1_a                     DOUBLE PRECISION,
    kron1_b                     DOUBLE PRECISION,
    kron1_area                  DOUBLE PRECISION,
    kron2_a                     DOUBLE PRECISION,
    kron2_b                     DOUBLE PRECISION,
    kron2_area                  DOUBLE PRECISION,
    kron_corr                   DOUBLE PRECISION,
    kron_f444w_psf_corr         DOUBLE PRECISION,
    kron_f770w_psf_corr         DOUBLE PRECISION,
    kron_f770w_ap_corr          DOUBLE PRECISION,

    -- Sérsic model structural parameters
    ra_model                    DOUBLE PRECISION,
    dec_model                   DOUBLE PRECISION,
    radius_sersic               DOUBLE PRECISION,
    radius_sersic_err           DOUBLE PRECISION,
    axratio_sersic              DOUBLE PRECISION,
    axratio_sersic_err          DOUBLE PRECISION,
    sersic                      DOUBLE PRECISION,
    sersic_err                  DOUBLE PRECISION,
    angle_sersic                DOUBLE PRECISION,
    angle_sersic_err            DOUBLE PRECISION,
    e1                          DOUBLE PRECISION,
    e1_err                      DOUBLE PRECISION,
    e2                          DOUBLE PRECISION,
    e2_err                      DOUBLE PRECISION,
    fmf_chi2                    DOUBLE PRECISION,
    group_id                    BIGINT,

    -- Flags
    flag_star                   BOOLEAN,
    flag_star_hsc               SMALLINT,
    flag_blend                  BOOLEAN,
    warn_flag                   BIGINT NOT NULL,

    -- Sérsic model magnitudes (37 bands) — hyphens sanitized to underscores
    mag_model_f115w             DOUBLE PRECISION,
    mag_model_f150w             DOUBLE PRECISION,
    mag_model_f277w             DOUBLE PRECISION,
    mag_model_f444w             DOUBLE PRECISION,
    mag_model_hst_f814w         DOUBLE PRECISION,
    mag_model_f770w             DOUBLE PRECISION,
    mag_model_cfht_u            DOUBLE PRECISION,
    mag_model_hsc_g             DOUBLE PRECISION,
    mag_model_hsc_r             DOUBLE PRECISION,
    mag_model_hsc_i             DOUBLE PRECISION,
    mag_model_hsc_z             DOUBLE PRECISION,
    mag_model_hsc_y             DOUBLE PRECISION,
    mag_model_hsc_nb0816        DOUBLE PRECISION,
    mag_model_hsc_nb0921        DOUBLE PRECISION,
    mag_model_hsc_nb1010        DOUBLE PRECISION,
    mag_model_uvista_y          DOUBLE PRECISION,
    mag_model_uvista_j          DOUBLE PRECISION,
    mag_model_uvista_h          DOUBLE PRECISION,
    mag_model_uvista_ks         DOUBLE PRECISION,
    mag_model_uvista_nb118      DOUBLE PRECISION,
    mag_model_sc_ia484          DOUBLE PRECISION,
    mag_model_sc_ia527          DOUBLE PRECISION,
    mag_model_sc_ia624          DOUBLE PRECISION,
    mag_model_sc_ia679          DOUBLE PRECISION,
    mag_model_sc_ia738          DOUBLE PRECISION,
    mag_model_sc_ia767          DOUBLE PRECISION,
    mag_model_sc_ib427          DOUBLE PRECISION,
    mag_model_sc_ib505          DOUBLE PRECISION,
    mag_model_sc_ib574          DOUBLE PRECISION,
    mag_model_sc_ib709          DOUBLE PRECISION,
    mag_model_sc_ib827          DOUBLE PRECISION,
    mag_model_sc_nb711          DOUBLE PRECISION,
    mag_model_sc_nb816          DOUBLE PRECISION,
    mag_model_irac_ch1          DOUBLE PRECISION,
    mag_model_irac_ch2          DOUBLE PRECISION,
    mag_model_irac_ch3          DOUBLE PRECISION,
    mag_model_irac_ch4          DOUBLE PRECISION,

    -- Sérsic model magnitude errors (37 bands) — -999 sentinel → NULL
    mag_err_model_f115w         DOUBLE PRECISION,
    mag_err_model_f150w         DOUBLE PRECISION,
    mag_err_model_f277w         DOUBLE PRECISION,
    mag_err_model_f444w         DOUBLE PRECISION,
    mag_err_model_hst_f814w     DOUBLE PRECISION,
    mag_err_model_f770w         DOUBLE PRECISION,
    mag_err_model_cfht_u        DOUBLE PRECISION,
    mag_err_model_hsc_g         DOUBLE PRECISION,
    mag_err_model_hsc_r         DOUBLE PRECISION,
    mag_err_model_hsc_i         DOUBLE PRECISION,
    mag_err_model_hsc_z         DOUBLE PRECISION,
    mag_err_model_hsc_y         DOUBLE PRECISION,
    mag_err_model_hsc_nb0816    DOUBLE PRECISION,
    mag_err_model_hsc_nb0921    DOUBLE PRECISION,
    mag_err_model_hsc_nb1010    DOUBLE PRECISION,
    mag_err_model_uvista_y      DOUBLE PRECISION,
    mag_err_model_uvista_j      DOUBLE PRECISION,
    mag_err_model_uvista_h      DOUBLE PRECISION,
    mag_err_model_uvista_ks     DOUBLE PRECISION,
    mag_err_model_uvista_nb118  DOUBLE PRECISION,
    mag_err_model_sc_ia484      DOUBLE PRECISION,
    mag_err_model_sc_ia527      DOUBLE PRECISION,
    mag_err_model_sc_ia624      DOUBLE PRECISION,
    mag_err_model_sc_ia679      DOUBLE PRECISION,
    mag_err_model_sc_ia738      DOUBLE PRECISION,
    mag_err_model_sc_ia767      DOUBLE PRECISION,
    mag_err_model_sc_ib427      DOUBLE PRECISION,
    mag_err_model_sc_ib505      DOUBLE PRECISION,
    mag_err_model_sc_ib574      DOUBLE PRECISION,
    mag_err_model_sc_ib709      DOUBLE PRECISION,
    mag_err_model_sc_ib827      DOUBLE PRECISION,
    mag_err_model_sc_nb711      DOUBLE PRECISION,
    mag_err_model_sc_nb816      DOUBLE PRECISION,
    mag_err_model_irac_ch1      DOUBLE PRECISION,
    mag_err_model_irac_ch2      DOUBLE PRECISION,
    mag_err_model_irac_ch3      DOUBLE PRECISION,
    mag_err_model_irac_ch4      DOUBLE PRECISION
);

-- =============================================================================
-- TABLE 2: lephare
-- Source: Extension 2 (LEPHARE) — all 43 columns + id injected from Ext 1
-- Rows: 784,016
-- Key sentinel: zfinal = -99 → NULL, mod_minchi2_phys = -99 → NULL
-- =============================================================================

CREATE TABLE catalog.lephare (
    id                          BIGINT PRIMARY KEY REFERENCES catalog.photometry_core(id),

    -- Redshift estimates
    zfinal                      DOUBLE PRECISION,   -- -99 sentinel → NULL
    zpdf_med                    DOUBLE PRECISION,
    zpdf_l68                    DOUBLE PRECISION,
    zpdf_u68                    DOUBLE PRECISION,
    zchi2                       DOUBLE PRECISION,
    chi2_best                   DOUBLE PRECISION,
    nbfilt                      BIGINT,

    -- Classification
    type                        BIGINT,             -- 0=galaxy, 1=star, 2=QSO
    zp_agn                      DOUBLE PRECISION,
    chi2_agn                    DOUBLE PRECISION,
    mod_agn                     DOUBLE PRECISION,
    mod_star                    DOUBLE PRECISION,
    chi_star                    DOUBLE PRECISION,

    -- Best-fit physical parameters
    mod_minchi2_phys            BIGINT,             -- -99 sentinel → NULL
    ebv_minchi2                 DOUBLE PRECISION,
    law_minchi2                 BIGINT,             -- -999 sentinel → NULL

    -- Age estimates
    age_minchi2                 DOUBLE PRECISION,
    age_l68                     DOUBLE PRECISION,
    age_med                     DOUBLE PRECISION,
    age_u68                     DOUBLE PRECISION,

    -- Stellar mass estimates
    mass_minchi2                DOUBLE PRECISION,
    mass_l68                    DOUBLE PRECISION,
    mass_med                    DOUBLE PRECISION,
    mass_u68                    DOUBLE PRECISION,

    -- Star formation rate
    sfr_minchi2                 DOUBLE PRECISION,
    sfr_l68                     DOUBLE PRECISION,
    sfr_med                     DOUBLE PRECISION,
    sfr_u68                     DOUBLE PRECISION,

    -- Specific SFR
    ssfr_minchi2                DOUBLE PRECISION,
    ssfr_l68                    DOUBLE PRECISION,
    ssfr_med                    DOUBLE PRECISION,
    ssfr_u68                    DOUBLE PRECISION,

    -- Luminosities & absolute magnitudes
    l_nuv                       DOUBLE PRECISION,
    l_r                         DOUBLE PRECISION,
    l_k                         DOUBLE PRECISION,
    mabs_nuv                    DOUBLE PRECISION,
    mabs_r                      DOUBLE PRECISION,
    mabs_j                      DOUBLE PRECISION,
    mabs_k                      DOUBLE PRECISION,

    -- Cross-match flags
    flag_chandra                DOUBLE PRECISION,

    -- Space-based photo-z (subset with HST/JWST only)
    zpdf_med_space              DOUBLE PRECISION,
    zpdf_l68_space              DOUBLE PRECISION,
    zpdf_u68_space              DOUBLE PRECISION
);

-- =============================================================================
-- TABLE 3: cigale
-- Source: Extension 4 (CIGALE) — all 54 columns + id injected from Ext 1
--         + 1 derived column (ssfr_cigale)
-- Rows: 784,016
-- Note: 16.1% NaN across all columns (sources CIGALE couldn't fit)
-- =============================================================================

CREATE TABLE catalog.cigale (
    id                          BIGINT PRIMARY KEY REFERENCES catalog.photometry_core(id),

    -- Formation age
    age_form                    DOUBLE PRECISION,
    age_form_err                DOUBLE PRECISION,

    -- SFR-mass vector
    sfr_mass_vector_dir         DOUBLE PRECISION,
    sfr_mass_vector_dir_err     DOUBLE PRECISION,
    sfr_mass_vector_norm        DOUBLE PRECISION,
    sfr_mass_vector_norm_err    DOUBLE PRECISION,

    -- Non-parametric SFH: SFR in 9 time bins
    sfh_sfr_bin1                DOUBLE PRECISION,
    sfh_sfr_bin1_err            DOUBLE PRECISION,
    sfh_sfr_bin2                DOUBLE PRECISION,
    sfh_sfr_bin2_err            DOUBLE PRECISION,
    sfh_sfr_bin3                DOUBLE PRECISION,
    sfh_sfr_bin3_err            DOUBLE PRECISION,
    sfh_sfr_bin4                DOUBLE PRECISION,
    sfh_sfr_bin4_err            DOUBLE PRECISION,
    sfh_sfr_bin5                DOUBLE PRECISION,
    sfh_sfr_bin5_err            DOUBLE PRECISION,
    sfh_sfr_bin6                DOUBLE PRECISION,
    sfh_sfr_bin6_err            DOUBLE PRECISION,
    sfh_sfr_bin7                DOUBLE PRECISION,
    sfh_sfr_bin7_err            DOUBLE PRECISION,
    sfh_sfr_bin8                DOUBLE PRECISION,
    sfh_sfr_bin8_err            DOUBLE PRECISION,
    sfh_sfr_bin9                DOUBLE PRECISION,
    sfh_sfr_bin9_err            DOUBLE PRECISION,

    -- Non-parametric SFH: time bin edges (9 bins)
    sfh_time_bin1               DOUBLE PRECISION,
    sfh_time_bin1_err           DOUBLE PRECISION,
    sfh_time_bin2               DOUBLE PRECISION,
    sfh_time_bin2_err           DOUBLE PRECISION,
    sfh_time_bin3               DOUBLE PRECISION,
    sfh_time_bin3_err           DOUBLE PRECISION,
    sfh_time_bin4               DOUBLE PRECISION,
    sfh_time_bin4_err           DOUBLE PRECISION,
    sfh_time_bin5               DOUBLE PRECISION,
    sfh_time_bin5_err           DOUBLE PRECISION,
    sfh_time_bin6               DOUBLE PRECISION,
    sfh_time_bin6_err           DOUBLE PRECISION,
    sfh_time_bin7               DOUBLE PRECISION,
    sfh_time_bin7_err           DOUBLE PRECISION,
    sfh_time_bin8               DOUBLE PRECISION,
    sfh_time_bin8_err           DOUBLE PRECISION,
    sfh_time_bin9               DOUBLE PRECISION,
    sfh_time_bin9_err           DOUBLE PRECISION,

    -- Metallicity
    metallicity                 DOUBLE PRECISION,
    metallicity_err             DOUBLE PRECISION,

    -- Integrated SFH
    sfh_integrated              DOUBLE PRECISION,
    sfh_integrated_err          DOUBLE PRECISION,

    -- Instantaneous & 100Myr-averaged SFR
    sfr_inst                    DOUBLE PRECISION,
    sfr_inst_err                DOUBLE PRECISION,
    sfr_100myr                  DOUBLE PRECISION,
    sfr_100myr_err              DOUBLE PRECISION,

    -- Stellar mass
    mass                        DOUBLE PRECISION,
    mass_err                    DOUBLE PRECISION,

    -- Fit quality
    chi2_best_fit               DOUBLE PRECISION,
    chi2_red_best_fit           DOUBLE PRECISION,

    -- Derived: sSFR = sfr_inst / mass (computed during ETL, NULL if mass=0/NaN)
    ssfr_cigale                 DOUBLE PRECISION
);

-- =============================================================================
-- TABLE 4: morphology
-- Source: Extension 5 (ML-MORPHO) — subset of 150 columns + id from Ext 1
-- Rows: 784,016
-- Note: ~38.8% NaN in f150w columns (sources too faint for morphology)
-- Sentinel: morph_flag = 999999 → NULL
-- =============================================================================

CREATE TABLE catalog.morphology (
    id                          BIGINT PRIMARY KEY REFERENCES catalog.photometry_core(id),

    -- Mean class probabilities: F150W band
    sph_f150w_mean              DOUBLE PRECISION,
    disk_f150w_mean             DOUBLE PRECISION,
    irr_f150w_mean              DOUBLE PRECISION,
    bd_f150w_mean               DOUBLE PRECISION,

    -- Std deviations: F150W band
    sph_f150w_std               DOUBLE PRECISION,
    disk_f150w_std              DOUBLE PRECISION,
    irr_f150w_std               DOUBLE PRECISION,
    bd_f150w_std                DOUBLE PRECISION,

    -- Mean class probabilities: F277W band
    sph_f277w_mean              DOUBLE PRECISION,
    disk_f277w_mean             DOUBLE PRECISION,
    irr_f277w_mean              DOUBLE PRECISION,
    bd_f277w_mean               DOUBLE PRECISION,

    -- Std deviations: F277W band
    sph_f277w_std               DOUBLE PRECISION,
    disk_f277w_std              DOUBLE PRECISION,
    irr_f277w_std               DOUBLE PRECISION,
    bd_f277w_std                DOUBLE PRECISION,

    -- Mean class probabilities: F444W band
    sph_f444w_mean              DOUBLE PRECISION,
    disk_f444w_mean             DOUBLE PRECISION,
    irr_f444w_mean              DOUBLE PRECISION,
    bd_f444w_mean               DOUBLE PRECISION,

    -- Std deviations: F444W band
    sph_f444w_std               DOUBLE PRECISION,
    disk_f444w_std              DOUBLE PRECISION,
    irr_f444w_std               DOUBLE PRECISION,
    bd_f444w_std                DOUBLE PRECISION,

    -- Morphological flags (999999 sentinel → NULL)
    morph_flag_f150w            BIGINT,
    morph_flag_f277w            BIGINT,
    morph_flag_f444w            BIGINT,

    -- Delta metrics (classification confidence)
    delta_f150w                 DOUBLE PRECISION,
    delta_f277w                 DOUBLE PRECISION,
    delta_f444w                 DOUBLE PRECISION
);

-- =============================================================================
-- TABLE 5: lss_overdensity
-- Source: Hatamnia et al. 2025 — OVERDENSITY extension
-- Rows: ~164,155 (subset with robust photo-z)
-- Join: id matches photometry_core.id
-- =============================================================================

CREATE TABLE catalog.lss_overdensity (
    id                          BIGINT PRIMARY KEY,
    ra                          DOUBLE PRECISION,
    dec                         DOUBLE PRECISION,
    density_excess              DOUBLE PRECISION NOT NULL  -- 1 + delta
);

-- =============================================================================
-- TABLE 6: galaxy_groups
-- Source: Toni et al. 2025 — group catalog (groups file)
-- Rows: ~1,678 groups
-- =============================================================================

CREATE TABLE catalog.galaxy_groups (
    group_id                    INTEGER PRIMARY KEY,
    ra                          DOUBLE PRECISION NOT NULL,
    dec                         DOUBLE PRECISION NOT NULL,
    z                           DOUBLE PRECISION NOT NULL,
    sn                          DOUBLE PRECISION,
    sn_nocl                     DOUBLE PRECISION,
    amp                         DOUBLE PRECISION,
    mskfrc                      DOUBLE PRECISION,
    lambda                      DOUBLE PRECISION,       -- richness
    lambda_star                 DOUBLE PRECISION,
    detection_flag              INTEGER,
    n_spec                      INTEGER,                -- -99 sentinel → NULL
    zphys_sigm                  DOUBLE PRECISION,
    zphys_sigp                  DOUBLE PRECISION
);

-- =============================================================================
-- TABLE 7: galaxy_group_memberships
-- Source: Toni et al. 2025 — membership catalog (memberships file)
-- Rows: many-to-many (galaxy ↔ group associations with probabilities)
-- =============================================================================

CREATE TABLE catalog.galaxy_group_memberships (
    galid                       BIGINT NOT NULL,        -- source id (matches photometry_core.id)
    field_prob                  DOUBLE PRECISION,       -- probability of being a field galaxy
    group_id                    INTEGER NOT NULL,       -- references galaxy_groups.group_id
    assoc_prob                  DOUBLE PRECISION,       -- probability of association with this group
    PRIMARY KEY (galid, group_id)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Photometry core: spatial, quality, star exclusion
CREATE INDEX idx_phot_radec ON catalog.photometry_core (ra, dec);
CREATE INDEX idx_phot_warn_flag ON catalog.photometry_core (warn_flag);
CREATE INDEX idx_phot_flag_star ON catalog.photometry_core (flag_star);

-- LePhare: redshift slicing, mass binning
CREATE INDEX idx_lephare_zfinal ON catalog.lephare (zfinal);
CREATE INDEX idx_lephare_mass_med ON catalog.lephare (mass_med);

-- CIGALE: mass for cross-code comparison (O1)
CREATE INDEX idx_cigale_mass ON catalog.cigale (mass);

-- Morphology: class selection, uncertainty filtering
CREATE INDEX idx_morph_flag_f444w ON catalog.morphology (morph_flag_f444w);
CREATE INDEX idx_morph_delta_f444w ON catalog.morphology (delta_f444w);

-- LSS: spatial for cross-matching
CREATE INDEX idx_lss_radec ON catalog.lss_overdensity (ra, dec);
CREATE INDEX idx_lss_density ON catalog.lss_overdensity (density_excess);

-- Groups: lookup by group, lookup by galaxy
CREATE INDEX idx_groups_z ON catalog.galaxy_groups (z);
CREATE INDEX idx_memberships_galid ON catalog.galaxy_group_memberships (galid);
CREATE INDEX idx_memberships_group ON catalog.galaxy_group_memberships (group_id);

-- =============================================================================
-- COMMENTS (table-level documentation)
-- =============================================================================

COMMENT ON SCHEMA catalog IS 'COSMOS-Web DR1 catalog tables for anomaly detection project';

COMMENT ON TABLE catalog.photometry_core IS 'Extension 1: 37-band photometry, Sérsic models, detection params, flags. 784,016 sources.';
COMMENT ON TABLE catalog.lephare IS 'Extension 2: LePhare SED fitting — photo-z, stellar mass, SFR, classification. 784,016 sources.';
COMMENT ON TABLE catalog.cigale IS 'Extension 4: CIGALE non-parametric SFH — 9-bin SFR, mass, metallicity. 784,016 sources (16.1% NaN = unfittable).';
COMMENT ON TABLE catalog.morphology IS 'Extension 5: ML morphological classification — sph/disk/irr/bd probabilities in 3 NIRCam bands. 784,016 sources.';
COMMENT ON TABLE catalog.lss_overdensity IS 'Hatamnia et al. 2025: per-object overdensity (1+delta) from KDE density field. ~164k sources with robust photo-z.';
COMMENT ON TABLE catalog.galaxy_groups IS 'Toni et al. 2025: galaxy group catalog — 1,678 groups to z=3.7.';
COMMENT ON TABLE catalog.galaxy_group_memberships IS 'Toni et al. 2025: galaxy-group membership associations with probabilistic assignments.';

COMMENT ON COLUMN catalog.photometry_core.warn_flag IS 'Quality flag: 0=most secure (694,341 sources), 1-6=increasing concern. See quality-flags.txt.';
COMMENT ON COLUMN catalog.photometry_core.flag_star IS 'Star flag from SE++ stellar locus classification.';
COMMENT ON COLUMN catalog.photometry_core.wht_hst_f814w IS 'Weight map value. 0.0 = no coverage for this band (informative, not missing).';
COMMENT ON COLUMN catalog.lephare.zfinal IS 'Final photo-z. Original -99 sentinels converted to NULL.';
COMMENT ON COLUMN catalog.lephare.type IS 'Source classification: 0=galaxy, 1=star, 2=QSO.';
COMMENT ON COLUMN catalog.cigale.ssfr_cigale IS 'Derived: sfr_inst / mass. NULL if mass=0 or NaN. Not in original catalog.';
COMMENT ON COLUMN catalog.morphology.morph_flag_f444w IS 'Morphology quality: 0=secure, 1-3=degraded, original 999999→NULL (no classification).';
COMMENT ON COLUMN catalog.lss_overdensity.density_excess IS 'Overdensity = 1 + delta. Values >1 are overdense, <1 are underdense.';
COMMENT ON COLUMN catalog.galaxy_group_memberships.assoc_prob IS 'Probability that this galaxy is associated with this group.';
COMMENT ON COLUMN catalog.galaxy_group_memberships.field_prob IS 'Probability that this galaxy is a field galaxy (not in any group).';
