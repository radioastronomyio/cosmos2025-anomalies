<!--
---
title: "Upstream Incompatibility Report Draft (Local, Unsent)"
description: "Reproducible local report of the held catalog/spec-z mismatch; S5-Q05 authorized transmission on 2026-10-05, the channel awaits Don's choice, and the report remains unsent"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-05"
version: "1.2"
status: "Draft - Local and Unsent; Transmission Authorized, Channel Pending"
tags:
  - type: research
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Spec-z Linkage Evidence](../specz-linkage-evidence.md)"
  - "[P2R-05 Review](review.md)"
---
-->

# Draft Report: carried spec-z identifiers do not reliably identify the same source in the held DR1.1 compilation

**Status: LOCAL DRAFT, NOT SENT.** S5-Q05 authorized transmission on
2026-10-05. Don has not chosen a channel, so this report remains unsent. It
concerns the held release pair below and does not assess newer releases or
identify the cause of the mismatch.

## Artifacts tested

The COSMOS-Web catalog version v1.1 and the spectroscopic compilation release
DR1.1 are independent version labels.

| Artifact | Rows used | Bytes | SHA-256 of complete FITS file |
|---|---:|---:|---|
| `COSMOSWeb_mastercatalog_v1.1.fits`, photometry-primary extension | 784,016 | 10,282,628,160 | `92bd5904677360f0bc9d26db3ac5f606f4c49ec64544eea1eb980220d744e712` |
| `specz_compilation_COSMOS_DR1.1_unique.fits` | 261,975 | 70,223,040 | `6ffd1145ed9caeba6c16f8e4267415682562b1a37549ac07a070ba5eb6336e99` |
| `specz_compilation_COSMOS_DR1.1_all.fits` | 482,579 | 129,343,680 | `30675493d98014b23900d41fbcdd6157f5fc64962be22755a6077658d3068fd3` |

Compilation checkout: `1924f5d0ee6c221b820035c8d3cd7302c02532b0`.
The held lightweight release ref `DR1.1` points to
`a634a9ed5c1c17ea2629b2326e4dc99f235d8027`. Only `README.md` and
`sed_fitting/cigale/README.md` differ between that release commit and the
checkout; the compilation data are the same. The full hashes above are
existing provenance pins from the held manifest, not hashes of new downloads.
The errata verification rechecked the local refs and FITS pointer identities;
it did not rehash the full raw FITS files or retarget the checkout.

For the claimed column semantics, the held
`cosmosweb-dr1-detailed-column-descriptions.txt` has SHA-256
`3e7dde1db9d541ce8593b12cbf0690130422e746ce7db78cc238f27ed724366b`.
Its photometry-primary description of `id_specz_khostovan25` says:
“Unique ID of the source corresponding to the Id_specz of the Khostovan
et al. (2025) spec-z compilation. -999 if no specz match”.

## Measured behavior and denominators

The first test deliberately looks up each catalog-carried
`id_specz_khostovan25` in the compilation's `Id_specz`. This tests the
claimed link, using identifier equality rather than row position. The second
test uses the compilation's own `Id_COSMOS25` crossmatch to catalog `id`.
The different joins answer different questions.

| Carried-link lookup | Count |
|---|---:|
| Catalog sources carrying a non-null, non-`-999` link | 37,219 |
| Distinct carried identifiers | 37,219 |
| Numeric matches in galaxy-level `_unique` | 24,364 |
| Missing from `_unique` | 12,855 |
| Numeric matches in measurement-level `_all` | 37,219 |
| `_all` matches whose `Id_COSMOS25` equals the source carrying the link | 227 |

Thus every carried value numerically resolves in `_all`, while only 227 of
37,219 (0.610 percent) point to a row whose crossmatch names that same catalog
source. The mismatch concerns correspondence between identifiers in these
held releases; numeric resolution alone is insufficient. The 227 agreements
are retained, without assuming why they occur. Carried values span 223 to
165,312; `_all.Id_specz` spans 1 to 487,666. The carried range width is
33.853 percent of the compilation range width, which does not establish a
release lineage.

All angular statistics below are in arcseconds and use measurement rows,
without imposing a redshift-quality cut or a maximum-separation filter.
Repeated measurements of a catalog source remain separate rows.

| Join and coordinate comparison | Rows | Minimum | Median | p90 | p99 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Carried link → `_all.Id_specz`; `ra_corrected/dec_corrected` versus carrier catalog `ra/dec` | 37,219 | 0.0048956903 | 4,054.3415558937 | 5,956.7226823118 | 7,219.4326342492 | 9,085.0188938083 |
| `_all.Id_COSMOS25` → catalog `id`; stored `ra_cosmos25/dec_cosmos25` versus catalog `ra/dec` | 92,359 | 0 | 0 | 0 | 0 | 0 |
| `_all.Id_COSMOS25` → catalog `id`; `ra_corrected/dec_corrected` versus catalog `ra/dec` | 92,359 | 0.0001297301 | 0.0840481119 | 0.2321556410 | 0.6381234841 | 0.9983350391 |

Stored COSMOS25 coordinates equal the catalog coordinates in all 92,359
associated measurement rows. That is coordinate identity, not an independent
astrometric accuracy measurement. The nonzero sub-arcsecond distribution
belongs to the corrected measurement coordinates. The carried-link geometry
is field-scale overall; the table does not claim every carried link is wrong
or every corrected association is astrophysically correct.

## Portable query definitions

These SELECT-only PostgreSQL queries specify the complete reductions. Table
names refer to faithful mirrors of the three pinned FITS surfaces, with
lowercase column names. Upstream can substitute its corresponding table
names or implement the same joins and calculations directly on those FITS
files. No installed P2R-05 analysis table is required. FITS masks/NaN are SQL
NULL; finite sentinels, including `-999`, remain stored values.

First confirm identifier uniqueness before interpreting joins (Q0):

```sql
SELECT 'catalog' AS surface, count(*) AS rows, count(DISTINCT id) AS distinct_ids
FROM source.photometry_primary
UNION ALL
SELECT 'unique', count(*), count(DISTINCT id_specz)
FROM source.specz_compilation_unique
UNION ALL
SELECT 'all', count(*), count(DISTINCT id_specz)
FROM source.specz_compilation_all;
```

Expected rows and distinct IDs are equal for each surface: catalog 784,016,
unique 261,975, all 482,579. Then count the carried-link resolutions and
source correspondences (Q1):

```sql
WITH linked AS (
    SELECT id, id_specz_khostovan25 AS link
    FROM source.photometry_primary
    WHERE id_specz_khostovan25 IS NOT NULL AND id_specz_khostovan25 <> -999
)
SELECT count(*) AS carriers,
       count(DISTINCT l.link) AS distinct_links,
       count(u.id_specz) AS resolves_unique,
       count(*) FILTER (WHERE u.id_specz IS NULL) AS absent_unique,
       count(a.id_specz) AS resolves_all,
       count(*) FILTER (WHERE a.id_cosmos25 = l.id) AS same_catalog_source,
       min(l.link) AS carried_min, max(l.link) AS carried_max,
       (SELECT min(id_specz) FROM source.specz_compilation_all) AS all_min,
       (SELECT max(id_specz) FROM source.specz_compilation_all) AS all_max
FROM linked l
LEFT JOIN source.specz_compilation_unique u ON u.id_specz = l.link
LEFT JOIN source.specz_compilation_all a ON a.id_specz = l.link;
```

For the three coordinate comparisons, use a spherical haversine separation
with roundoff clamped to [0,1] and linear-interpolated percentiles (Q2).
`pair_rows` and `compared_rows` expose any excluded coordinates; on this hold
they agree in all three comparisons, so no row is removed by the coordinate
domain check. In particular, no angular-radius selection is applied.

```sql
WITH pairs AS (
    SELECT 'carried_corrected' AS comparison,
           p.ra AS ra1, p.dec AS dec1, a.ra_corrected AS ra2, a.dec_corrected AS dec2
    FROM source.photometry_primary p
    JOIN source.specz_compilation_all a ON a.id_specz = p.id_specz_khostovan25
    WHERE p.id_specz_khostovan25 IS NOT NULL AND p.id_specz_khostovan25 <> -999
    UNION ALL
    SELECT 'crossmatch_stored', p.ra, p.dec, a.ra_cosmos25, a.dec_cosmos25
    FROM source.specz_compilation_all a
    JOIN source.photometry_primary p ON p.id = a.id_cosmos25
    UNION ALL
    SELECT 'crossmatch_corrected', p.ra, p.dec, a.ra_corrected, a.dec_corrected
    FROM source.specz_compilation_all a
    JOIN source.photometry_primary p ON p.id = a.id_cosmos25
), totals AS (
    SELECT comparison, count(*) AS pair_rows FROM pairs GROUP BY comparison
), valid AS (
    SELECT * FROM pairs
    WHERE ra1 >= 0 AND ra1 < 360 AND ra2 >= 0 AND ra2 < 360
      AND dec1 BETWEEN -90 AND 90 AND dec2 BETWEEN -90 AND 90
), distances AS (
    SELECT comparison,
           3600 * degrees(2 * asin(sqrt(least(1.0, greatest(0.0,
               power(sin(radians(dec2 - dec1) / 2), 2)
               + cos(radians(dec1)) * cos(radians(dec2))
               * power(sin(radians(ra2 - ra1) / 2), 2)
           ))))) AS arcsec
    FROM valid
)
SELECT d.comparison, t.pair_rows, count(*) AS compared_rows,
       min(arcsec) AS minimum,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY arcsec) AS median,
       percentile_cont(0.9) WITHIN GROUP (ORDER BY arcsec) AS p90,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY arcsec) AS p99,
       max(arcsec) AS maximum
FROM distances d JOIN totals t USING (comparison)
GROUP BY d.comparison, t.pair_rows ORDER BY d.comparison;
```

## Output-safe reproduction in this repository

The report above is self-contained for an upstream recipient. Local reviewers
can run its exact SQL blocks without modifying the sealed evidence. From the
repository root, the following command uses the existing read-only analyst
handoff, writes only within errata staging, and records both SQL and results.
Use a new output filename if retaining more than one rerun. It requires the
existing environment; do not install or rebuild anything.

```bash
/opt/agents/venv/bin/python -B - <<'PY'
import json
import re
from pathlib import Path
from src.features.specz_science.config import connect_analyst

document = Path('docs/research/specz-science-p2r05/upstream-report-draft.md')
output = Path('staging/2026-10-04-astra-p2r05-errata/upstream-query-rerun.json')
queries = re.findall(r'```sql\n(.*?)\n```', document.read_text(), re.S)
connection, _ = connect_analyst()
try:
    assert connection.execute("SELECT current_setting('transaction_read_only')").fetchone()[0] == 'on'
    results = []
    for number, query in enumerate(queries):
        cursor = connection.execute(query)
        columns = [column.name for column in cursor.description]
        results.append({'query_id': f'Q{number}', 'sql': query,
                        'rows': [dict(zip(columns, row)) for row in cursor.fetchall()]})
finally:
    connection.close()
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('x', encoding='utf-8') as handle:
    json.dump(results, handle, indent=2)
    handle.write('\n')
print(output)
PY
```

## Working hypothesis (explicitly unconfirmed)

One possible explanation is that the catalog column was populated against
an earlier compilation release whose `Id_specz` values changed by DR1.1.
Other namespace or construction mismatches could produce this behavior.
We hold no artifact defining a release-to-release mapping; the value range
and failed source correspondences cannot identify the cause. “Renumbering”
remains a hypothesis, not a finding or an attribution of fault.

## Suggested question for upstream

Could you confirm which compilation release `id_specz_khostovan25` was
populated against and whether an identifier mapping to DR1.1 exists? If the
intended correspondence differs from the description quoted above, could you
clarify how users of this held release pair should interpret the column?

## What we did locally (no upstream action implied)

We preserve the shipped column in our mirror. For P2R-05 association we use
the compilation's `Id_COSMOS25` into catalog `id`, without repairing the
carried identifiers, rematching coordinates, or inferring release mappings.
This is a local workaround for the held release pair, not an upstream fix.

## Local drafting errata (2026-10-04, AR-F05)

1. Separated `_unique` numeric resolution (24,364/37,219) from `_all`
   resolution (37,219/37,219) and retained the 227 same-source correspondences.
2. Attributed zero coordinate identity to stored COSMOS25 coordinates and
   the nonzero sub-arcsecond statistics to corrected measurement coordinates.
3. Described the deliberately defective carried-link join separately from
   the compilation crossmatch join.
4. Expanded the full release pins and checkout identity, included exact
   aggregate SQL and counts, and replaced legacy commands that write to old
   evidence locations with explicit output-safe reproduction.

No message, upload or upstream report has been transmitted. S5-Q05 authorized
transmission on 2026-10-05; Don retains the channel choice.
