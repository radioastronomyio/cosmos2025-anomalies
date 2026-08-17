#!/usr/bin/env python3
"""
Script Name  : load_dictionary.py
Description  : Build and validate the COSMOS-Web v1.1 semantic load dictionary
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Builds the structural and semantic load dictionary for the seven COSMOS-Web
master extensions, three supplement tables, and the unique
spectroscopic-redshift table. Source, semantic-evidence, and output paths come
from configs/data_paths.yaml. The builder reads sources and evidence only and
never connects to PostgreSQL.

Usage
-----
    python src/etl/load_dictionary.py [--check]

Examples
--------
    python src/etl/load_dictionary.py
        Rebuilds the configured dictionary CSV from live source headers.

    python src/etl/load_dictionary.py --check
        Validates that the committed CSV matches a fresh in-memory build.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import hashlib
import io
import re
from collections import Counter
from pathlib import Path

import yaml
from astropy.io import fits

# =============================================================================
# Configuration
# =============================================================================

# PostgreSQL Appendix C classifies these as reserved. Prefixing them avoids
# future parser-context differences without requiring a database connection.
POSTGRESQL_RESERVED_WORDS = {
    "all",
    "analyse",
    "analyze",
    "and",
    "any",
    "array",
    "as",
    "asc",
    "asymmetric",
    "authorization",
    "binary",
    "both",
    "case",
    "cast",
    "check",
    "collate",
    "collation",
    "column",
    "concurrently",
    "constraint",
    "create",
    "cross",
    "current_catalog",
    "current_date",
    "current_role",
    "current_schema",
    "current_time",
    "current_timestamp",
    "current_user",
    "default",
    "deferrable",
    "desc",
    "distinct",
    "do",
    "else",
    "end",
    "except",
    "false",
    "fetch",
    "for",
    "foreign",
    "freeze",
    "from",
    "full",
    "grant",
    "group",
    "having",
    "ilike",
    "in",
    "initially",
    "inner",
    "intersect",
    "into",
    "is",
    "isnull",
    "join",
    "lateral",
    "leading",
    "left",
    "like",
    "limit",
    "localtime",
    "localtimestamp",
    "natural",
    "not",
    "notnull",
    "null",
    "offset",
    "on",
    "only",
    "or",
    "order",
    "outer",
    "overlaps",
    "placing",
    "primary",
    "references",
    "returning",
    "right",
    "select",
    "session_user",
    "similar",
    "some",
    "symmetric",
    "system_user",
    "table",
    "tablesample",
    "then",
    "to",
    "trailing",
    "true",
    "union",
    "unique",
    "user",
    "using",
    "variadic",
    "verbose",
    "when",
    "where",
    "window",
    "with",
}

MASTER_SOURCES = (
    ("photom_primary", "photometry_primary"),
    ("lephare", "lephare"),
    ("photom_secondary", "photometry_aper"),
    ("cigale", "cigale"),
    ("ml_morph", "ml_morpho"),
    ("bulgedisk", "bulge_disk"),
    ("galight_morph", "galight_morph"),
)
TEXT_TYPE_MAPPING = {
    "text integer": "bigint",
    "text decimal": "double precision",
    "text string": "text",
}
PRIOR_MASTER_TFIELDS = 1_349
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
CSV_FIELDS = (
    "source_family",
    "source_file",
    "source_locator",
    "source_column",
    "source_type",
    "element_count",
    "target_table",
    "target_identifier",
    "target_type",
    "column_origin",
    "description_text",
    "description_source",
    "description_locator",
    "description_source_sha256",
    "description_status",
    "unit",
    "unit_source",
    "unit_locator",
    "unit_source_sha256",
    "semantic_note",
    "semantic_note_source",
    "semantic_note_locator",
    "semantic_note_source_sha256",
    "profile_json",
    "has_fits_mask",
    "has_nan",
    "documented_sentinel_values_json",
    "documented_sentinel_evidence_text",
    "documented_sentinel_source",
    "documented_sentinel_locator",
    "documented_sentinel_source_sha256",
    "candidate_sentinel_values_json",
)
SEMANTIC_FIELDS = CSV_FIELDS[10:23]
ALLOWED_DESCRIPTION_STATUSES = {
    "verified",
    "pattern_expanded",
    "undocumented_upstream",
    "project_derived",
}
EXPECTED_SEMANTIC_HASHES = {
    "master_descriptions": "3e7dde1db9d541ce8593b12cbf0690130422e746ce7db78cc238f27ed724366b",
    "yang_v1_pdf": "f4d369c1f3c093dc5990895ac7f95ceecead318339e9fe1b8b823fb51675f0bc",
    "lss_readme": "e40402a510cad8e3d7069de759514090a16602ea7eb5f46715d13d64d1487e97",
    "specz_root_readme": "1aee693918c3e8deb8ac9ce273468a37935987f53f2903eb47420dcfbfe90a23",
    "specz_schema_readme": "43992cf6a30d5893d9421dd1d0b837e1f8dc4975a92e8372ba8cb3b7be78d0c1",
    "unit_conventions": "8a4d3a724ba435fe5668260e50be45c41f067214567a8723d27d004d3df9ca4a",
}
DETAILED_DESCRIPTION_SECTIONS = {
    "1": "photometry_primary",
    "2": "lephare",
    "3": "photometry_aper",
    "4": "cigale",
    "5": "ml_morpho",
    "6": "bulge_disk",
}
EXPLICIT_DESCRIPTION_UNITS = {
    "microJy",
    "AB mag",
    "Myr",
    "1/yr",
    "deg",
    "Msol",
    "Msol yr-1",
    "yr-1",
    "dimensionless",
    "M_sol",
    "M_sol/yr",
    "yr",
    "degrees",
    "dex/Myr",
}
YANG_REFERENCE = "Yang et al. 2026, arXiv:2606.14869v1"

# Table 1 contains 51 per-filter patterns. The bulge+disk error block is
# intentionally asymmetric: neither component has an nsersic error pattern.
GALIGHT_PATTERNS = (
    (
        "rearc_xxx_sersic",
        "Half-light radius (arcsecond) of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "arcsecond",
    ),
    (
        "nsersic_xxx_sersic",
        "Sérsic index of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "phi_xxx_sersic",
        "Position angle of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "qratio_xxx_sersic",
        "Axis ratio of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "mag_xxx_sersic",
        "Magnitude of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "rearc_xxx_sersic_err",
        "Half-light radius err (arcsecond) of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "arcsecond",
    ),
    (
        "nsersic_xxx_sersic_err",
        "Sérsic index err of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "phi_xxx_sersic_err",
        "Position angle err of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "qratio_xxx_sersic_err",
        "Axis ratio err of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "mag_xxx_sersic_err",
        "Magnitude err of Sérsic model in xxx filter",
        "single_sersic",
        19,
        "unknown",
    ),
    (
        "rearc_bulge_xxx_bd",
        "Half-light radius (arcsecond) of bulge component in xxx filter",
        "bulge_disk_parameters",
        19,
        "arcsecond",
    ),
    (
        "nsersic_bulge_xxx_bd",
        "Sérsic index of bulge component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "phi_bulge_xxx_bd",
        "Position angle of bulge component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "qratio_bulge_xxx_bd",
        "Axis ratio of bulge component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "mag_bulge_xxx_bd",
        "Magnitude of bulge component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "rearc_disk_xxx_bd",
        "Half-light radius (arcsecond) of disk component in xxx filter",
        "bulge_disk_parameters",
        19,
        "arcsecond",
    ),
    (
        "nsersic_disk_xxx_bd",
        "Sérsic index of disk component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "phi_disk_xxx_bd",
        "Position angle of disk component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "qratio_disk_xxx_bd",
        "Axis ratio of disk component in xxx filter",
        "bulge_disk_parameters",
        19,
        "unknown",
    ),
    (
        "mag_disk_xxx_bd",
        "Magnitude of disk component in xxx filter",
        "bulge_disk_parameters",
        20,
        "unknown",
    ),
    (
        "rearc_bulge_xxx_bd_err",
        "Half-light radius err (arcsecond) of bulge component in xxx filter",
        "bulge_disk_errors",
        20,
        "arcsecond",
    ),
    (
        "phi_bulge_xxx_bd_err",
        "Position angle of err bulge component in xxx filter",
        "bulge_disk_errors",
        20,
        "unknown",
    ),
    (
        "qratio_bulge_xxx_bd_err",
        "Axis ratio err of bulge component in xxx filter",
        "bulge_disk_errors",
        20,
        "unknown",
    ),
    (
        "mag_bulge_xxx_bd_err",
        "Magnitude err of bulge component in xxx filter",
        "bulge_disk_errors",
        20,
        "unknown",
    ),
    (
        "rearc_disk_xxx_bd_err",
        "Half-light radius err (arcsecond) of disk component in xxx filter",
        "bulge_disk_errors",
        20,
        "arcsecond",
    ),
    (
        "phi_disk_xxx_bd_err",
        "Position angle err of disk component in xxx filter",
        "bulge_disk_errors",
        20,
        "unknown",
    ),
    (
        "qratio_disk_xxx_bd_err",
        "Axis ratio err of disk component in xxx filter",
        "bulge_disk_errors",
        20,
        "unknown",
    ),
    (
        "mag_disk_xxx_bd_err",
        "Magnitude err of disk component in xxx filter",
        "bulge_disk_errors",
        20,
        "unknown",
    ),
    (
        "rearc_host_xxx_ps",
        "Half-light radius of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "nsersic_host_xxx_ps",
        "Sérsic index of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "phi_host_xxx_ps",
        "Position angle of extended component extended in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "qratio_host_xxx_ps",
        "Axis ratio of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "mag_host_xxx_ps",
        "Magnitude of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "p2t_flux_ratio_xxx_ps",
        "Point to total flux ratio in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "rearc_host_xxx_ps_err",
        "Half-light radius err (arcsecond) of extended component in xxx filter",
        "point_source",
        20,
        "arcsecond",
    ),
    (
        "nsersic_host_xxx_ps_err",
        "Sérsic index err of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "phi_host_xxx_ps_err",
        "Position angle err of extended component extended in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "qratio_host_xxx_ps_err",
        "Axis ratio err of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "mag_host_xxx_ps_err",
        "Magnitude err of extended component in xxx filter",
        "point_source",
        20,
        "unknown",
    ),
    (
        "bic_xxx_sersic",
        "Bayesian information criterion of Sérsic model",
        "fit_statistics",
        20,
        "unknown",
    ),
    (
        "reduced_Chisq_xxx_sersic",
        "Reduced χ² of Sérsic model",
        "fit_statistics",
        20,
        "unknown",
    ),
    (
        "bic_list_xxx_bd",
        "Bayesian information criterion of Bulge+Disk model",
        "fit_statistics",
        20,
        "unknown",
    ),
    (
        "reduced_Chisq_list_xxx_bd",
        "Reduced χ² of Bulge+Disk model",
        "fit_statistics",
        20,
        "unknown",
    ),
    (
        "bic_list_xxx_ps",
        "Bayesian information criterion of Point+Extended model",
        "fit_statistics",
        20,
        "unknown",
    ),
    (
        "reduced_Chisq_list_xxx_ps",
        "Reduced χ² of Point+Extended model",
        "fit_statistics",
        20,
        "unknown",
    ),
    ("asymmetry_xxx", "Asymmetry in xxx filter", "statmorph", 20, "unknown"),
    ("smoothness_xxx", "Smoothness in xxx filter", "statmorph", 20, "unknown"),
    (
        "concentration_xxx",
        "Concentration in xxx filter",
        "statmorph",
        20,
        "unknown",
    ),
    ("gini_xxx", "Gini in xxx filter", "statmorph", 20, "unknown"),
    ("m20_xxx", "M20 in xxx filter", "statmorph", 20, "unknown"),
    ("cas_flag_xxx", "Statmorph quality flag", "statmorph", 20, "unknown"),
)

# =============================================================================
# Functions
# =============================================================================


def canonicalize_description(text: str) -> str:
    """Trim a source block and collapse each whitespace run to one space."""
    return re.sub(r"\s+", " ", text).strip()


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 from the exact live evidence artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _semantic_source_context(
    config: dict[str, object],
) -> tuple[dict[str, Path], dict[str, str]]:
    """Resolve configured semantic sources and verify their frozen digests."""
    configured = config.get("semantic_sources")
    if not isinstance(configured, dict):
        raise ValueError("Missing semantic_sources configuration")
    paths = {key: Path(str(value)) for key, value in configured.items()}
    hashes: dict[str, str] = {}
    for key, path in paths.items():
        observed = _sha256_file(path)
        expected = EXPECTED_SEMANTIC_HASHES.get(key)
        if expected is not None and observed != expected:
            raise ValueError(
                f"Semantic source hash mismatch for {key}: "
                f"expected {expected}, observed {observed}"
            )
        hashes[key] = observed
    return paths, hashes


def _description_unit(description: str) -> str:
    """Return only an explicit controlled bracketed unit from source prose."""
    bracketed = re.findall(r"\[([^\]]+)\]", description)
    for candidate in reversed(bracketed):
        if candidate in EXPLICIT_DESCRIPTION_UNITS:
            return candidate
    return "unknown"


def _parse_detailed_descriptions(
    path: Path,
) -> dict[tuple[str, str], dict[str, str]]:
    """Parse exact two-column blocks from the pinned master description file."""
    definitions: dict[tuple[str, str], dict[str, str]] = {}
    target_table: str | None = None
    section_number = ""
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        heading = re.match(r"^([1-6]):\s", line)
        if heading is not None:
            section_number = heading.group(1)
            target_table = DETAILED_DESCRIPTION_SECTIONS[section_number]
            continue
        if target_table is None or "\t" not in line:
            continue
        source_column, source_block = line.split("\t", 1)
        if source_column == "Column Name":
            continue
        key = (target_table, source_column)
        if key in definitions:
            raise ValueError(f"Duplicate detailed description: {key}")
        description = canonicalize_description(source_block)
        definitions[key] = {
            "description": description,
            "locator": (f"section {section_number}, line {line_number}, Description"),
            "unit": _description_unit(description),
        }
    return definitions


def _parse_lss_descriptions(path: Path) -> dict[str, dict[str, str]]:
    """Parse the four exact OVERDENSITY field definitions and units."""
    lines = path.read_text().splitlines()
    section_start = lines.index("Byte-by-byte Description of file: OVERDENSITY")
    start = (
        lines.index("Bytes   Format Units  Label          Explanations", section_start)
        + 2
    )
    definitions: dict[str, dict[str, str]] = {}
    current: dict[str, str | int] | None = None
    row_pattern = re.compile(
        r"^\s*\d+\s*-\s*\d+\s+\S+\s+(?P<unit>\S+)\s+"
        r"(?P<label>\S+)\s{2,}(?P<description>.*)$"
    )
    for zero_index in range(start, len(lines)):
        line = lines[zero_index]
        if line.startswith("---"):
            break
        match = row_pattern.match(line)
        if match is not None:
            if current is not None:
                definitions[str(current["label"])] = {
                    "description": canonicalize_description(
                        str(current["description"])
                    ),
                    "locator": (
                        "OVERDENSITY, lines "
                        f"{current['start']}-{current['end']}, Explanations"
                        if current["start"] != current["end"]
                        else (f"OVERDENSITY, line {current['start']}, Explanations")
                    ),
                    "unit": str(current["unit"]),
                    "unit_locator": (f"OVERDENSITY, line {current['start']}, Units"),
                }
            current = {
                "label": match.group("label"),
                "description": match.group("description"),
                "unit": match.group("unit"),
                "start": zero_index + 1,
                "end": zero_index + 1,
            }
        elif current is not None and line.strip():
            current["description"] = f"{current['description']} {line.strip()}"
            current["end"] = zero_index + 1
    if current is not None:
        definitions[str(current["label"])] = {
            "description": canonicalize_description(str(current["description"])),
            "locator": (
                f"OVERDENSITY, lines {current['start']}-{current['end']}, Explanations"
                if current["start"] != current["end"]
                else f"OVERDENSITY, line {current['start']}, Explanations"
            ),
            "unit": str(current["unit"]),
            "unit_locator": f"OVERDENSITY, line {current['start']}, Units",
        }
    if set(definitions) != {"id", "RA", "Dec", "density_excess"}:
        raise ValueError(f"OVERDENSITY description set mismatch: {sorted(definitions)}")
    return definitions


def _specz_descriptions(
    root_readme: Path, schema_readme: Path
) -> dict[str, dict[str, str]]:
    """Return only native spec-z fields with exact repository definitions."""
    root_lines = root_readme.read_text().splitlines()
    schema_lines = schema_readme.read_text().splitlines()
    return {
        "flag": {
            "description": canonicalize_description("\n".join(root_lines[59:70])),
            "locator": "Quality Assessment Flagging System, lines 60-70",
            "source_key": "specz_root_readme",
        },
        "Confidence_level": {
            "description": canonicalize_description("\n".join(root_lines[61:70])),
            "locator": "Quality Assessment Flagging System, lines 62-70",
            "source_key": "specz_root_readme",
        },
        "survey": {
            "description": canonicalize_description(schema_lines[5]),
            "locator": "List of Surveys, line 6",
            "source_key": "specz_schema_readme",
        },
    }


def _galight_definitions() -> dict[str, dict[str, str | int]]:
    """Expand exact Yang Table 1 patterns across the four live filters."""
    definitions: dict[str, dict[str, str | int]] = {}
    for filter_name in ("F115W", "F150W", "F277W", "F444W"):
        source_filter = filter_name.lower()
        for pattern, description, category, page, unit in GALIGHT_PATTERNS:
            source_column = pattern.replace("xxx", source_filter)
            definitions[source_column] = {
                "description": canonicalize_description(description),
                "locator": (
                    f"Table 1 p.{page}; pattern={pattern}; "
                    f"filter={filter_name}; category={category}"
                ),
                "unit": unit,
                "category": category,
            }
    if len(definitions) != 204:
        raise ValueError(f"GALIGHT expansion mismatch: {len(definitions)} rows")
    return definitions


def _blank_semantics() -> dict[str, str]:
    """Return explicit empty semantic fields for one dictionary row."""
    return {
        "description_text": "",
        "description_source": "",
        "description_locator": "",
        "description_source_sha256": "",
        "description_status": "undocumented_upstream",
        "unit": "unknown",
        "unit_source": "",
        "unit_locator": "",
        "unit_source_sha256": "",
        "semantic_note": "",
        "semantic_note_source": "",
        "semantic_note_locator": "",
        "semantic_note_source_sha256": "",
    }


def _set_description(
    row: dict[str, str | int],
    *,
    text: str,
    source: str,
    locator: str,
    source_hash: str,
    status: str,
    unit: str = "unknown",
    unit_locator: str | None = None,
) -> None:
    """Set one independently evidenced description and optional unit."""
    row.update(
        {
            "description_text": canonicalize_description(text),
            "description_source": source,
            "description_locator": locator,
            "description_source_sha256": source_hash,
            "description_status": status,
            "unit": unit,
        }
    )
    if unit != "unknown":
        row.update(
            {
                "unit_source": source,
                "unit_locator": unit_locator or locator,
                "unit_source_sha256": source_hash,
            }
        )


def _enrich_semantics(
    rows: list[dict[str, str | int]], config: dict[str, object]
) -> dict[str, object]:
    """Apply the frozen semantic-source precedence to every dictionary row."""
    paths, hashes = _semantic_source_context(config)
    detailed = _parse_detailed_descriptions(paths["master_descriptions"])
    lss = _parse_lss_descriptions(paths["lss_readme"])
    specz = _specz_descriptions(
        paths["specz_root_readme"], paths["specz_schema_readme"]
    )
    galight = _galight_definitions()

    galight_categories: Counter[str] = Counter()
    for row in rows:
        row.update(_blank_semantics())
        origin = str(row["column_origin"])
        target_table = str(row["target_table"])
        source_column = str(row["source_column"])

        if origin != "source_native":
            if origin == "source_row_metadata":
                description = (
                    "Zero-based source row ordinal for preserving source order "
                    "and aligning injected identifiers within the master catalog."
                )
                locator = "Deliverable 1, relational metadata, line 149"
            else:
                description = (
                    "Primary photometry source identifier copied to this extension "
                    "at the same zero-based source_row."
                )
                locator = "Deliverable 1, relational metadata, line 150"
            _set_description(
                row,
                text=description,
                source=str(paths["etl_v2_spec"]),
                locator=locator,
                source_hash=hashes["etl_v2_spec"],
                status="project_derived",
            )
            continue

        if target_table == "galight_morph":
            definition = galight.get(source_column)
            if definition is None:
                raise ValueError(f"Missing GALIGHT Table 1 pattern: {source_column}")
            _set_description(
                row,
                text=str(definition["description"]),
                source=YANG_REFERENCE,
                locator=str(definition["locator"]),
                source_hash=hashes["yang_v1_pdf"],
                status="pattern_expanded",
                unit=str(definition["unit"]),
            )
            galight_categories[str(definition["category"])] += 1
        elif str(row["source_family"]) == "master_catalog":
            definition = detailed.get((target_table, source_column))
            if definition is not None:
                _set_description(
                    row,
                    text=definition["description"],
                    source=str(paths["master_descriptions"]),
                    locator=definition["locator"],
                    source_hash=hashes["master_descriptions"],
                    status="verified",
                    unit=definition["unit"],
                )
        elif target_table == "lss_overdensity":
            definition = lss[source_column]
            lss_unit = definition["unit"]
            _set_description(
                row,
                text=definition["description"],
                source=str(paths["lss_readme"]),
                locator=definition["locator"],
                source_hash=hashes["lss_readme"],
                status="verified",
                unit=lss_unit if lss_unit != "---" else "unknown",
                unit_locator=definition["unit_locator"],
            )
        elif target_table == "specz_compilation" and source_column in specz:
            definition = specz[source_column]
            source_key = definition["source_key"]
            _set_description(
                row,
                text=definition["description"],
                source=str(paths[source_key]),
                locator=definition["locator"],
                source_hash=hashes[source_key],
                status="verified",
            )

    unit_source = str(paths["unit_conventions"])
    unit_hash = hashes["unit_conventions"]
    lephare_columns = {
        "mass_l68",
        "mass_med",
        "mass_u68",
        "sfr_l68",
        "sfr_med",
        "sfr_u68",
        "ssfr_l68",
        "ssfr_med",
        "ssfr_u68",
    }
    cigale_columns = {
        "mass",
        "mass_err",
        "sfr_inst",
        "sfr_inst_err",
        "sfr_100myr",
        "sfr_100myr_err",
    }
    for row in rows:
        target_table = str(row["target_table"])
        source_column = str(row["source_column"])
        if target_table == "lephare" and source_column in lephare_columns:
            row.update(
                {
                    "semantic_note": (
                        "LePhare mass, SFR, and sSFR values and their l68/u68 "
                        "quantiles are in log10 space."
                    ),
                    "semantic_note_source": unit_source,
                    "semantic_note_locator": (
                        "section 1, Parameter Spaces table, line 29"
                    ),
                    "semantic_note_source_sha256": unit_hash,
                }
            )
        elif target_table == "cigale" and source_column in cigale_columns:
            row.update(
                {
                    "semantic_note": (
                        "CIGALE mass and SFR values and their errors are in "
                        "linear space."
                    ),
                    "semantic_note_source": unit_source,
                    "semantic_note_locator": (
                        "section 1, Parameter Spaces table, line 30"
                    ),
                    "semantic_note_source_sha256": unit_hash,
                }
            )

    return {
        "semantic_source_hashes": hashes,
        "galight_category_counts": dict(galight_categories),
    }


def sanitize_identifier(source_name: str) -> str:
    """
    Convert a source column name to the frozen PostgreSQL identifier form.

    Parameters
    ----------
    source_name : str
        Exact source column name.

    Returns
    -------
    str
        Lowercase identifier with punctuation runs replaced and required
        ``c_`` prefixing applied.
    """
    identifier = re.sub(r"[^a-z0-9_]+", "_", source_name.lower())
    if not re.match(r"^[a-z_]", identifier) or identifier in POSTGRESQL_RESERVED_WORDS:
        identifier = f"c_{identifier}"
    return identifier


def fits_type_mapping(source_type: str) -> tuple[str, int]:
    """
    Map one FITS binary-table TFORM to a PostgreSQL type and element count.

    Parameters
    ----------
    source_type : str
        Exact FITS TFORM string from the source column definition.

    Returns
    -------
    tuple[str, int]
        PostgreSQL type and structural element count.

    Raises
    ------
    ValueError
        If the format is outside the gate's lossless mapping contract.
    """
    match = re.fullmatch(r"(?P<count>[1-9][0-9]*)?(?P<code>[ADEIJKL])", source_type)
    if match is None:
        raise ValueError(f"Unsupported FITS type: {source_type}")

    count = int(match.group("count") or "1")
    code = match.group("code")
    scalar_types = {
        "D": "double precision",
        "E": "real",
        "K": "bigint",
        "J": "integer",
        "I": "smallint",
        "L": "boolean",
    }
    if code == "A":
        return "text", count
    if count > 1:
        if code not in {"D", "E"}:
            raise ValueError(f"Unsupported FITS vector type: {source_type}")
        return f"{scalar_types[code]}[]", count
    return scalar_types[code], 1


def validate_dictionary(rows: list[dict[str, str | int]]) -> None:
    """
    Validate dictionary rows and halt on the first structural defect.

    Parameters
    ----------
    rows : list[dict[str, str | int]]
        Unified dictionary rows.

    Raises
    ------
    ValueError
        If a row violates the lossless mapping contract.
    """
    identifiers: dict[tuple[str, str], str] = {}
    native_sources: set[tuple[str, str, str, str]] = set()
    for row in rows:
        required_values = (
            "source_family",
            "source_file",
            "source_locator",
            "source_column",
            "source_type",
            "target_table",
            "target_identifier",
            "target_type",
            "column_origin",
        )
        empty_fields = [
            name for name in required_values if not str(row.get(name, "")).strip()
        ]
        if empty_fields:
            raise ValueError(f"Empty required field(s): {', '.join(empty_fields)}")

        target_identifier = str(row["target_identifier"])
        if len(target_identifier.encode("utf-8")) > 63:
            raise ValueError(
                f"Identifier over 63 bytes: {row['target_table']}.{target_identifier}"
            )
        if re.fullmatch(r"[a-z_][a-z0-9_]*", target_identifier) is None:
            raise ValueError(f"Invalid target identifier: {target_identifier}")
        if target_identifier in POSTGRESQL_RESERVED_WORDS:
            raise ValueError(f"Reserved target identifier: {target_identifier}")
        key = (str(row["target_table"]), str(row["target_identifier"]))
        prior = identifiers.get(key)
        if prior is not None:
            raise ValueError(
                "Identifier collision: "
                f"{key[0]}.{key[1]} maps from both {prior!r} and "
                f"{row['source_column']!r}"
            )
        identifiers[key] = str(row["source_column"])

        if row["column_origin"] != "source_native":
            continue
        native_key = (
            str(row["source_family"]),
            str(row["source_file"]),
            str(row["source_locator"]),
            str(row["source_column"]),
        )
        if native_key in native_sources:
            raise ValueError(f"Duplicate native source field: {native_key}")
        native_sources.add(native_key)

        expected_identifier = sanitize_identifier(str(row["source_column"]))
        if target_identifier != expected_identifier:
            raise ValueError(
                "Identifier mapping mismatch: "
                f"{row['source_column']!r} must map to {expected_identifier!r}"
            )
        source_type = str(row["source_type"])
        if source_type in TEXT_TYPE_MAPPING:
            expected_type = TEXT_TYPE_MAPPING[source_type]
            expected_count = 1
        else:
            expected_type, expected_count = fits_type_mapping(source_type)
        if (
            row["target_type"] != expected_type
            or int(row["element_count"]) != expected_count
        ):
            raise ValueError(
                "Type mapping mismatch: "
                f"{row['target_table']}.{row['source_column']} "
                f"{source_type} must map to {expected_type} with "
                f"element_count {expected_count}"
            )


def validate_semantics(rows: list[dict[str, str | int]]) -> None:
    """Validate the full Gate 3.2 semantic and provenance contract."""
    required_fields = set(SEMANTIC_FIELDS)
    statuses: Counter[str] = Counter()
    project_rows = 0
    semantic_notes = 0
    for row in rows:
        missing = required_fields - row.keys()
        if missing:
            raise ValueError(f"Missing semantic field(s): {sorted(missing)}")
        if any("\n" in str(value) or "\r" in str(value) for value in row.values()):
            raise ValueError(
                "Embedded newline in dictionary row: "
                f"{row['target_table']}.{row['source_column']}"
            )

        status = str(row["description_status"])
        if status not in ALLOWED_DESCRIPTION_STATUSES:
            raise ValueError(f"Invalid description status: {status}")
        statuses[status] += 1
        if status in {"verified", "pattern_expanded"}:
            if not str(row["description_text"]):
                raise ValueError("Sourced description must be non-empty")
            provenance = (
                str(row["description_source"]),
                str(row["description_locator"]),
                str(row["description_source_sha256"]),
            )
            if (
                not all(provenance)
                or re.fullmatch(r"[0-9a-f]{64}", provenance[2]) is None
            ):
                raise ValueError("Description provenance incomplete")
        elif status == "undocumented_upstream":
            if str(row["description_text"]):
                raise ValueError("Undocumented description must be empty")
            if str(row["unit"]) != "unknown" and not str(row["unit_source"]):
                raise ValueError("Undocumented unit requires separate evidence")
        else:
            project_rows += 1
            if row["column_origin"] == "source_native":
                raise ValueError("Project-derived status on native row")
            if not str(row["description_text"]):
                raise ValueError("Project-derived description must be non-empty")

        if str(row["unit"]) != "unknown":
            unit_provenance = (
                str(row["unit_source"]),
                str(row["unit_locator"]),
                str(row["unit_source_sha256"]),
            )
            if (
                not all(unit_provenance)
                or re.fullmatch(r"[0-9a-f]{64}", unit_provenance[2]) is None
            ):
                raise ValueError("Unit provenance incomplete")

        semantic_note = str(row["semantic_note"])
        if semantic_note:
            semantic_notes += 1
            note_provenance = (
                str(row["semantic_note_source"]),
                str(row["semantic_note_locator"]),
                str(row["semantic_note_source_sha256"]),
            )
            if (
                not all(note_provenance)
                or re.fullmatch(r"[0-9a-f]{64}", note_provenance[2]) is None
            ):
                raise ValueError("Semantic-note provenance incomplete")
            description = str(row["description_text"])
            if "log10 space" in description or "linear space" in description:
                raise ValueError("Semantic note composed into source description")

    galight = {
        str(row["source_column"])
        for row in rows
        if row["target_table"] == "galight_morph"
        and row["column_origin"] == "source_native"
    }
    expected_galight = set(_galight_definitions())
    if galight != expected_galight:
        raise ValueError(
            "GALIGHT pattern set mismatch: "
            f"expected {len(expected_galight)}, observed {len(galight)}"
        )
    if any(
        row["target_table"] == "galight_morph"
        and row["column_origin"] == "source_native"
        and row["description_status"] != "pattern_expanded"
        for row in rows
    ):
        raise ValueError("GALIGHT native row lacks pattern-expanded status")

    expected_statuses = {
        "verified": 1_150,
        "pattern_expanded": 204,
        "undocumented_upstream": 49,
        "project_derived": 13,
    }
    if dict(statuses) != expected_statuses:
        raise ValueError(
            f"Description status count mismatch: expected {expected_statuses}, "
            f"observed {dict(statuses)}"
        )
    if project_rows != 13:
        raise ValueError(f"Project-derived row count mismatch: {project_rows}")
    if semantic_notes != 15:
        raise ValueError(f"Semantic-note count mismatch: {semantic_notes}")

    for name in ("ebv_stars", "ebv_stars_err"):
        matches = [
            row
            for row in rows
            if row["target_table"] == "cigale" and row["source_column"] == name
        ]
        if len(matches) != 1 or matches[0]["description_status"] != (
            "undocumented_upstream"
        ):
            raise ValueError(f"CIGALE undocumented field mismatch: {name}")


def _table_hdu(
    path: Path, extname: str | None = None
) -> tuple[fits.HDUList, fits.BinTableHDU]:
    """Open one FITS source and return its sole or named table HDU context."""
    hdul = fits.open(path, memmap=True, lazy_load_hdus=True)
    if extname is not None:
        return hdul, hdul[extname]
    tables = [hdu for hdu in hdul if getattr(hdu, "columns", None) is not None]
    if len(tables) != 1:
        hdul.close()
        raise ValueError(f"Expected one table HDU in {path}, found {len(tables)}")
    return hdul, tables[0]


def _fits_rows(
    path: Path,
    source_family: str,
    target_table: str,
    extname: str | None = None,
) -> tuple[list[dict[str, str | int]], str, int]:
    """Build native rows from an exact FITS table column definition."""
    hdul, hdu = _table_hdu(path, extname)
    try:
        hdu_index = hdul.index_of(hdu)
        hdu_name = str(hdu.header.get("EXTNAME", "")).strip()
        locator = f"HDU {hdu_index}" + (f" [{hdu_name}]" if hdu_name else "")
        tfields = int(hdu.header.get("TFIELDS", -1))
        columns = list(hdu.columns)
        if len(columns) != tfields:
            raise ValueError(
                f"TFIELDS reconciliation failed for {path}: "
                f"header={tfields}, columns={len(columns)}"
            )
        rows = []
        for column in columns:
            source_type = str(column.format)
            target_type, element_count = fits_type_mapping(source_type)
            rows.append(
                {
                    "source_family": source_family,
                    "source_file": str(path),
                    "source_locator": locator,
                    "source_column": str(column.name),
                    "source_type": source_type,
                    "element_count": element_count,
                    "target_table": target_table,
                    "target_identifier": sanitize_identifier(str(column.name)),
                    "target_type": target_type,
                    "column_origin": "source_native",
                }
            )
        return rows, locator, tfields
    finally:
        hdul.close()


def _infer_text_types(path: Path) -> tuple[list[str], list[str]]:
    """Read a whitespace table and infer its structural scalar token types."""
    with path.open() as handle:
        header = handle.readline().split()
        if not header:
            raise ValueError(f"Missing text-table header: {path}")
        kinds = ["text integer"] * len(header)
        for line_number, line in enumerate(handle, start=2):
            if not line.strip():
                continue
            values = line.split()
            if len(values) != len(header):
                raise ValueError(
                    f"Text-table width mismatch in {path} line {line_number}: "
                    f"expected {len(header)}, found {len(values)}"
                )
            for index, value in enumerate(values):
                if kinds[index] == "text string":
                    continue
                if re.fullmatch(r"[+-]?[0-9]+", value):
                    continue
                try:
                    float(value)
                except ValueError:
                    kinds[index] = "text string"
                else:
                    kinds[index] = "text decimal"
    return header, kinds


def _text_rows(
    path: Path,
    source_family: str,
    target_table: str,
) -> tuple[list[dict[str, str | int]], str]:
    """Build native rows from a whitespace-delimited text table."""
    names, source_types = _infer_text_types(path)
    locator = "text table, header line 1"
    rows = []
    for name, source_type in zip(names, source_types, strict=True):
        rows.append(
            {
                "source_family": source_family,
                "source_file": str(path),
                "source_locator": locator,
                "source_column": name,
                "source_type": source_type,
                "element_count": 1,
                "target_table": target_table,
                "target_identifier": sanitize_identifier(name),
                "target_type": TEXT_TYPE_MAPPING[source_type],
                "column_origin": "source_native",
            }
        )
    return rows, locator


def build_dictionary(
    config_path: Path,
) -> tuple[list[dict[str, str | int]], dict[str, object]]:
    """
    Build and validate the full dictionary from configured live structures.

    Parameters
    ----------
    config_path : Path
        YAML configuration containing all source paths.

    Returns
    -------
    tuple[list[dict[str, str | int]], dict[str, object]]
        Dictionary rows and structural reconciliation evidence.
    """
    config = yaml.safe_load(config_path.read_text())
    rows: list[dict[str, str | int]] = []
    native_counts: dict[str, int] = {}
    master_context: dict[str, tuple[Path, str]] = {}
    master_tfields_total = 0

    for config_key, target_table in MASTER_SOURCES:
        path = Path(config["catalogs"][config_key])
        native, locator, tfields = _fits_rows(
            path,
            source_family="master_catalog",
            target_table=target_table,
        )
        rows.extend(native)
        native_counts[target_table] = len(native)
        master_context[target_table] = (path, locator)
        master_tfields_total += tfields

    native_master_ids = {
        row["target_table"]
        for row in rows
        if row["source_family"] == "master_catalog"
        and row["column_origin"] == "source_native"
        and str(row["source_column"]).lower() == "id"
    }
    if native_master_ids != {"photometry_primary"}:
        raise ValueError(
            "Native master id inventory mismatch: "
            f"expected photometry_primary only, found {sorted(native_master_ids)}"
        )

    primary_path, primary_locator = master_context["photometry_primary"]
    for _, target_table in MASTER_SOURCES:
        path, locator = master_context[target_table]
        rows.append(
            {
                "source_family": "master_catalog",
                "source_file": str(path),
                "source_locator": locator,
                "source_column": "source_row",
                "source_type": "generated zero-based row ordinal",
                "element_count": 1,
                "target_table": target_table,
                "target_identifier": "source_row",
                "target_type": "bigint",
                "column_origin": "source_row_metadata",
            }
        )
        if target_table != "photometry_primary":
            rows.append(
                {
                    "source_family": "master_catalog",
                    "source_file": str(primary_path),
                    "source_locator": primary_locator,
                    "source_column": "id",
                    "source_type": "K",
                    "element_count": 1,
                    "target_table": target_table,
                    "target_identifier": "id",
                    "target_type": "bigint",
                    "column_origin": "id_injected",
                }
            )

    lss_path = Path(config["supplementary"]["lss_overdensity"])
    native, _, _ = _fits_rows(
        lss_path,
        source_family="hatamnia_lss",
        target_table="lss_overdensity",
        extname="OVERDENSITY",
    )
    rows.extend(native)
    native_counts["lss_overdensity"] = len(native)

    text_sources = (
        ("group_catalog_groups", "toni_groups", "galaxy_groups"),
        (
            "group_catalog_memberships",
            "toni_memberships",
            "galaxy_group_memberships",
        ),
    )
    for config_key, source_family, target_table in text_sources:
        native, _ = _text_rows(
            Path(config["supplementary"][config_key]),
            source_family=source_family,
            target_table=target_table,
        )
        rows.extend(native)
        native_counts[target_table] = len(native)

    specz_path = Path(config["specz"]["unique_fits"])
    native, _, _ = _fits_rows(
        specz_path,
        source_family="specz_compilation",
        target_table="specz_compilation",
    )
    rows.extend(native)
    native_counts["specz_compilation"] = len(native)

    validate_dictionary(rows)
    semantic_evidence = _enrich_semantics(rows, config)
    validate_semantics(rows)
    origin_counts = Counter(str(row["column_origin"]) for row in rows)
    if origin_counts["source_row_metadata"] != 7 or origin_counts["id_injected"] != 6:
        raise ValueError(f"Metadata row count mismatch: {dict(origin_counts)}")

    vectors = [
        {
            "target_table": row["target_table"],
            "source_column": row["source_column"],
            "source_type": row["source_type"],
            "element_count": row["element_count"],
            "target_type": row["target_type"],
        }
        for row in rows
        if row["column_origin"] == "source_native"
        and str(row["target_type"]).endswith("[]")
    ]
    evidence: dict[str, object] = {
        "native_counts": native_counts,
        "master_tfields_total": master_tfields_total,
        "master_prior_expectation": PRIOR_MASTER_TFIELDS,
        "master_prior_difference": master_tfields_total - PRIOR_MASTER_TFIELDS,
        "native_total": origin_counts["source_native"],
        "origin_counts": dict(origin_counts),
        "vectors": vectors,
        "description_status_counts": dict(
            Counter(str(row["description_status"]) for row in rows)
        ),
        "semantic_note_count": sum(bool(row["semantic_note"]) for row in rows),
        **semantic_evidence,
    }
    return rows, evidence


def dictionary_csv_text(rows: list[dict[str, str | int]]) -> str:
    """Serialize dictionary rows with stable field and line ordering."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def write_dictionary(rows: list[dict[str, str | int]], output_path: Path) -> None:
    """Write a validated dictionary to its configured repository path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dictionary_csv_text(rows))


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Build or reproducibility-check the configured dictionary CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="path to data_paths.yaml",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare a fresh build with the configured CSV",
    )
    parser.add_argument(
        "--semantic-only",
        action="store_true",
        help="build only the Gate 3.2 semantic prefix for focused diagnostics",
    )
    args = parser.parse_args()

    if not args.semantic_only:
        if __package__:
            from . import profile_values
        else:
            import profile_values

        profile_values.main()
        return

    config = yaml.safe_load(args.config.read_text())
    output_path = Path(config["dictionary"]["columns_v11"])
    rows, evidence = build_dictionary(args.config)
    regenerated = dictionary_csv_text(rows)

    if args.check:
        if not output_path.exists():
            raise SystemExit(f"dictionary check FAILED: missing {output_path}")
        if output_path.read_text() != regenerated:
            raise SystemExit(
                f"dictionary check FAILED: content differs at {output_path}"
            )
        print(f"dictionary check PASSED: {len(rows)} rows reproduce byte-identical")
        return

    write_dictionary(rows, output_path)
    vector_counts = Counter(
        (str(vector["source_type"]), int(vector["element_count"]))
        for vector in evidence["vectors"]
    )
    print(f"dictionary rows: {len(rows)}")
    print(f"native rows: {evidence['native_total']}")
    print(
        "master TFIELDS: "
        f"{evidence['master_tfields_total']} "
        f"(prior {evidence['master_prior_expectation']}, "
        f"difference {evidence['master_prior_difference']:+d})"
    )
    print(f"vector counts: {dict(vector_counts)}")
    print(f"wrote: {output_path}")


if __name__ == "__main__":
    main()
