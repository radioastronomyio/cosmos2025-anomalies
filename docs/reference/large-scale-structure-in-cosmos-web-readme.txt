Hatamnia et al 2025
================================================================================
Large-Scale Structure in COSMOS-Web: Tracing Galaxy Evolution in the Cosmic Web
up to z ~ 7 with the Largest JWST Survey
    Hossein Hatamnia, Bahram Mobasher, Sina Taamoli, Jeyhan S. Kartaltepe, Caitlin M. Casey, Hollis B. Akins, Malte Brinch, Nima Chartab, Andreas L. Faisst, Steven L. Finkelstein, Maximilien Franco, Finn Giddings, Ghassem Gozaliasl, Ali Hadi, Aryana Haghjoo, Santosh Harish, Olivier Ilbert, Pascale L. Jablonka, Shuowen Jin, Ali Ahmad Khostovan, Anton M. Koekemoer, Ronaldo Laishram, Daizhong Liu, Matteo Maturi, Henry Joy McCracken, Crystal L. Martin, Lauro Moscardini, Diana Scognamiglio, Marko Shuntov, Greta Toni, Alexander de la Vega, John R. Weaver, Lilan Yang,
    =
================================================================================
Keywords: large-scale structure of Universe; galaxies: evolution;
          galaxies: high-redshift; galaxies: clusters; methods: data analysis

Abstract:
  We reconstruct large-scale structure using the James Webb Space Telescope
  COSMOS-Web program to trace environmentally driven galaxy evolution up to z ~
  7. We apply a weighted kernel density estimation method to ~160,000 galaxies
  with robust photometric redshifts. Stellar mass correlates positively with
  density at all redshifts, most strongly for quiescent galaxies at z <= 2.5; at
  higher redshift (2.5 <= z <= 5.5) this trend appears mainly in extreme
  overdensities, consistent with early mass assembly in protoclusters. The star-
  formation rate shows a negative trend with density for quiescent systems at z
  <= 1.2 and reverses at z >= 1.8; star-forming galaxies show a mild positive
  correlation up to z ~ 5.5. Specific SFR is roughly flat for star-forming
  galaxies and declines with density for quiescent systems at z <= 1.2. Mass and
  environmental quenching efficiencies indicate mass-driven processes dominate
  at z >= 2.5, both effects are comparable for 0.8 <= z <= 2.5, and environment
  dominates for low-mass galaxies (M* <= 1e10 Msun) at z <= 0.8. COSMOS-Web
  provides deep photometric redshifts and reaches ~80% mass completeness at
  log10(M*/Msun) ~ 8.7 at z = 7.

Description:
  Description: The FITS file contains two binary tables (SLICES and POINTS), one
  per-object overdensity table (OVERDENSITY), and per-slice 2D density map
  images. SLICES lists the slice index, central redshift z, KDE bandwidth scale
  b, and the median slice density bg_dens. POINTS lists all galaxies per slice
  with RA and Dec in the sky frame, x and y in the internal rotated frame, the
  per-slice weight w, the adaptive kernel bandwidth adaptive_b, and the edge
  correction factor boundary_corr. OVERDENSITY provides one row per galaxy id
  with RA, Dec, and the per-object overdensity value density_excess, equal to 1
  + delta, computed from the KDE density field. The 2D density maps are stored
  as image HDUs: DENSITY_###, DENSITYCONTRAST_###, and DENSITYEXCESS_### in the
  sky frame aligned with RA and Dec; and DensityRotated_###,
  DensityContrastRotated_###, and DensityExcessRotated_### in the rotated frame.
  Each image HDU header includes SLICE, Z, B, BG_DENS, and IMTYPE. The primary
  header reports NSLICE and NOBJ.

File Summary:
--------------------------------------------------------------------------------
 FileName    Lrecl  Records  Explanations
--------------------------------------------------------------------------------
ReadMe          80        .  This file
SLICES          51      314  Per-slice metadata: index, z_center, bandwidth
                              scale, median density
POINTS         148  2188547  Per-slice source points with RA, Dec, weights,
                              adaptive bandwidth, boundary correction
OVERDENSITY     58   164155  Per-object overdensity table: COSMOS2025 id, RA,
                              Dec, and density_excess = 1 + delta
--------------------------------------------------------------------------------

Byte-by-byte Description of file: SLICES
--------------------------------------------------------------------------------
Bytes   Format Units  Label   Explanations
--------------------------------------------------------------------------------
 1- 3   I3     ---    slice    Slice index
 5- 9   F5.3   ---    z       [0.4/9.39] Slice center redshift
11-30   F20.18 ---    b       [0.0/0.13] Bandwidth scale used in the slice
32-51   F20.11 ---    bg_dens [40365.86/43961969.29] Median density in the slice

--------------------------------------------------------------------------------

Byte-by-byte Description of file: POINTS
--------------------------------------------------------------------------------
  Bytes   Format Units  Label         Explanations
--------------------------------------------------------------------------------
  1-  3   I3     ---    slice          Slice index
  5- 10   I6     ---    id             Source identifier
 12- 29   F18.14 deg    RA            [149.66/150.58] Right Ascension
 31- 48   F18.16 deg    Dec           [1.72/2.69] Declination
 50- 67   F18.14 deg    x             [139.82/140.53] X coordinate in rotated
                                      frame
 69- 86   F18.15 deg    y             [53.39/54.18] Y coordinate in rotated
                                      frame
 88-107   F20.18 ---    w             [0.05/1.0] Weight used in density
                                      estimation
109-129   F21.19 deg    adaptive_b    [0.0/0.23] Adaptive bandwidth per object
131-148   F18.16 ---    boundary_corr [0.99/3.79] Boundary correction factor

--------------------------------------------------------------------------------

Byte-by-byte Description of file: OVERDENSITY
--------------------------------------------------------------------------------
Bytes   Format Units  Label          Explanations
--------------------------------------------------------------------------------
 1- 6   I6     ---    id             [3/780605] Source identifier (matches
                                     POINTS.id)
 8-26   F19.14 deg    RA             [149.66/150.58]? Right Ascension
28-46   F19.16 deg    Dec            [1.72/2.69]? Declination
48-58   F11.8  ---    density_excess  Per-object overdensity 1 + delta

--------------------------------------------------------------------------------




Acknowledgements: Hossein Hatamnia, hossein.hatamnia@email.ucr.edu

================================================================================
     (prepared by author  / pyreadme )