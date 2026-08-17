#!/usr/bin/env python3
"""
Script Name  : load_dictionary.py
Description  : Build and validate the COSMOS-Web v1.1 load dictionary
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Builds the structural load dictionary for the seven COSMOS-Web master
extensions, three supplement tables, and the unique spectroscopic-redshift
table. Source paths and the output path come from configs/data_paths.yaml.
The builder reads source structure only and never connects to PostgreSQL.

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
)

# =============================================================================
# Functions
# =============================================================================


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
    args = parser.parse_args()

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
