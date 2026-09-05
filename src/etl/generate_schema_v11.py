#!/usr/bin/env python3
"""
Script Name  : generate_schema_v11.py
Description  : Generate the ETL v2 PostgreSQL source-mirror schema
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Generates source/schema mirror DDL solely from the sealed v1.1 dictionary and
the versioned provenance-table contract in this module. The SQL artifact is
generated-only; use ``--check`` to reject byte drift instead of editing it.

Usage
-----
    python src/etl/generate_schema_v11.py [--check]

Examples
--------
    python src/etl/generate_schema_v11.py
        Rebuilds the configured schema_v11.sql artifact.

    python src/etl/generate_schema_v11.py --check
        Proves byte-identical regeneration from sealed inputs.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
MIRROR_TABLE_ORDER = (
    "photometry_primary",
    "photometry_aper",
    "lephare",
    "cigale",
    "ml_morpho",
    "bulge_disk",
    "galight_morph",
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
    "specz_compilation_unique",
    "specz_compilation_all",
)
MASTER_EXTENSION_TABLES = MIRROR_TABLE_ORDER[1:7]
PROVENANCE_CONTRACT_VERSION = "1.0.1"


@dataclass(frozen=True)
class ProvenanceField:
    """One importable field in the fixed Gate 3.6 provenance contract."""

    name: str
    sql_type: str
    nullable: bool
    comment: str
    primary_key: bool = False
    check_expression: str = ""


PROVENANCE_CONTRACT = (
    ProvenanceField(
        "table_name",
        "text",
        False,
        "Mirror table identity; one provenance row is permitted per loaded table.",
        primary_key=True,
    ),
    ProvenanceField(
        "source_file",
        "text",
        False,
        "Source artifact file name used for this table load.",
    ),
    ProvenanceField(
        "source_path",
        "text",
        False,
        "Configured source artifact path used for this table load.",
    ),
    ProvenanceField(
        "manifest_sha256",
        "text",
        False,
        "Manifest-pinned lowercase SHA-256 digest for the source artifact.",
        check_expression="{column} ~ '^[0-9a-f]{64}$'",
    ),
    ProvenanceField(
        "observed_sha256",
        "text",
        False,
        "Lowercase SHA-256 digest observed from the source artifact at load time.",
        check_expression="{column} ~ '^[0-9a-f]{64}$'",
    ),
    ProvenanceField(
        "source_rows",
        "bigint",
        False,
        "Source row count observed before the table load.",
        check_expression="{column} >= 0",
    ),
    ProvenanceField(
        "loaded_rows",
        "bigint",
        False,
        "Rows committed to the mirror table by the load.",
        check_expression="{column} >= 0",
    ),
    ProvenanceField(
        "load_timestamp",
        "timestamp with time zone",
        False,
        "Timestamp of the provenance-registration transaction performed after "
        "mirror load verification; not the historical table-load commit timestamp.",
    ),
    ProvenanceField(
        "manifest_ref",
        "text",
        False,
        "Repository-relative or configured reference to the source manifest.",
    ),
    ProvenanceField(
        "manifest_ref_sha256",
        "text",
        False,
        "Lowercase SHA-256 digest of the referenced manifest artifact.",
        check_expression="{column} ~ '^[0-9a-f]{64}$'",
    ),
    ProvenanceField(
        "catalog_version",
        "text",
        False,
        "Catalog release label represented by the loaded table.",
    ),
    ProvenanceField(
        "supplement_version",
        "text",
        False,
        "Explicit supplement release label or load-time not-applicable marker.",
    ),
    ProvenanceField(
        "notes",
        "text",
        True,
        "Optional load-specific provenance notes; no science-derived values.",
    ),
)


@dataclass(frozen=True)
class ColumnContract:
    """One mirror column copied directly from a sealed dictionary row."""

    table: str
    name: str
    sql_type: str
    element_count: int
    origin: str
    row: dict[str, str]


@dataclass(frozen=True)
class CheckContract:
    """A deterministic named PostgreSQL CHECK constraint."""

    table: str
    name: str
    expression: str


@dataclass(frozen=True)
class TableConstraint:
    """One authorized table-level master-key constraint."""

    kind: str
    columns: tuple[str, ...]
    name: str
    references: tuple[str, tuple[str, ...]] | None = None


@dataclass(frozen=True)
class ColumnComment:
    """One generated mirror-column comment and its escaped SQL statement."""

    table: str
    column: str
    text: str
    sql: str


# =============================================================================
# Contract helpers
# =============================================================================


def quote_identifier(value: str) -> str:
    """Quote one PostgreSQL identifier without relying on input validation."""
    return '"' + value.replace('"', '""') + '"'


def sql_literal(value: str) -> str:
    """Serialize arbitrary source prose as one PostgreSQL string literal."""
    return "'" + value.replace("'", "''") + "'"


def constraint_name(kind: str, table: str, column: str = "") -> str:
    """Return a deterministic unique identifier within PostgreSQL's 63 bytes."""
    raw = re.sub(r"[^a-z0-9_]+", "_", f"{table}_{column}_{kind}".lower()).strip("_")
    if not raw or not re.match(r"[a-z_]", raw):
        raw = "constraint_" + raw
    digest = hashlib.sha256(f"{kind}\0{table}\0{column}".encode()).hexdigest()[:12]
    suffix = f"_{digest}"
    prefix_bytes = raw.encode("utf-8")[: 63 - len(suffix)]
    prefix = prefix_bytes.decode("utf-8", errors="ignore").rstrip("_")
    return prefix + suffix


def read_dictionary(path: Path) -> list[dict[str, str]]:
    """Read the sealed CSV without changing row or field order."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_schema_contract(
    rows: list[dict[str, str]],
) -> dict[str, tuple[ColumnContract, ...]]:
    """Validate and group the exact sealed mirror boundary in DDL order."""
    if len(rows) != 1_448:
        raise ValueError(
            f"sealed dictionary row count mismatch: expected 1448, found {len(rows)}"
        )
    observed_tables = {row["target_table"] for row in rows}
    if observed_tables != set(MIRROR_TABLE_ORDER):
        raise ValueError(
            "sealed dictionary table boundary mismatch: "
            f"found {sorted(observed_tables)}"
        )
    schema: dict[str, tuple[ColumnContract, ...]] = {}
    for table in MIRROR_TABLE_ORDER:
        table_rows = [row for row in rows if row["target_table"] == table]
        identifiers = [row["target_identifier"] for row in table_rows]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"duplicate target identifier in {table}")
        schema[table] = tuple(
            ColumnContract(
                table=table,
                name=row["target_identifier"],
                sql_type=row["target_type"],
                element_count=int(row["element_count"]),
                origin=row["column_origin"],
                row=row,
            )
            for row in table_rows
        )
    return schema


def array_check_contract(rows: list[dict[str, str]]) -> tuple[CheckContract, ...]:
    """Build one nullable-safe one-dimensional exact-length check per SQL array."""
    checks: list[CheckContract] = []
    for row in rows:
        if not row["target_type"].endswith("[]"):
            continue
        table = row["target_table"]
        column = row["target_identifier"]
        quoted = quote_identifier(column)
        checks.append(
            CheckContract(
                table=table,
                name=constraint_name("array_shape_check", table, column),
                expression=(
                    f"{quoted} IS NULL OR "
                    f"(array_ndims({quoted}) = 1 AND "
                    f"cardinality({quoted}) = {int(row['element_count'])})"
                ),
            )
        )
    if len(checks) != 166 or len({check.name for check in checks}) != len(checks):
        raise ValueError("array check count or name-collision mismatch")
    return tuple(checks)


def table_constraint_contract(
    rows: list[dict[str, str]],
) -> dict[str, tuple[TableConstraint, ...]]:
    """Return only the authorized master primary, unique, and foreign keys."""
    build_schema_contract(rows)
    constraints: dict[str, tuple[TableConstraint, ...]] = {
        table: () for table in MIRROR_TABLE_ORDER
    }
    constraints["photometry_primary"] = (
        TableConstraint(
            "primary_key",
            ("id",),
            constraint_name("primary_key", "photometry_primary", "id"),
        ),
        TableConstraint(
            "unique",
            ("source_row",),
            constraint_name("unique", "photometry_primary", "source_row"),
        ),
    )
    for table in MASTER_EXTENSION_TABLES:
        constraints[table] = (
            TableConstraint(
                "primary_key",
                ("source_row",),
                constraint_name("primary_key", table, "source_row"),
            ),
            TableConstraint(
                "unique",
                ("id",),
                constraint_name("unique", table, "id"),
            ),
            TableConstraint(
                "foreign_key",
                ("id",),
                constraint_name("foreign_key", table, "id"),
                ("photometry_primary", ("id",)),
            ),
        )
    # P2R-04 gate 4.3: Id_specz is the measurement-level primary key because
    # gate 4.1 measured 482,579 distinct values over 482,579 rows in the
    # pinned artifact. No other key is invented for this table.
    constraints["specz_compilation_all"] = (
        TableConstraint(
            "primary_key",
            ("id_specz",),
            constraint_name("primary_key", "specz_compilation_all", "id_specz"),
        ),
    )
    return constraints


def _provenance_text(source: str, locator: str, digest: str) -> str:
    """Preserve evidence separation when a semantic field is not applicable."""
    if source or locator or digest:
        return f"source={source}; locator={locator}; sha256={digest}"
    return "[not applicable]"


def _comment_text(row: dict[str, str]) -> str:
    """Build a separated evidence comment without inventing upstream prose."""
    description = row["description_text"] or "[undocumented upstream]"
    semantic_note = row["semantic_note"] or "[not documented]"
    documented_evidence = row["documented_sentinel_evidence_text"] or "[none]"
    return "\n".join(
        (
            f"Description: {description}",
            f"Description status: {row['description_status']}",
            "Description provenance: "
            + _provenance_text(
                row["description_source"],
                row["description_locator"],
                row["description_source_sha256"],
            ),
            f"Unit: {row['unit']}",
            "Unit provenance: "
            + _provenance_text(
                row["unit_source"],
                row["unit_locator"],
                row["unit_source_sha256"],
            ),
            f"Semantic note: {semantic_note}",
            "Semantic-note provenance: "
            + _provenance_text(
                row["semantic_note_source"],
                row["semantic_note_locator"],
                row["semantic_note_source_sha256"],
            ),
            "Null/profile facts: "
            f"has_fits_mask={row['has_fits_mask']}; has_nan={row['has_nan']}; "
            f"profile={row['profile_json']}",
            "Documented sentinel evidence: finite values are retained source values; "
            f"values={row['documented_sentinel_values_json']}; "
            f"evidence={documented_evidence}; provenance="
            + _provenance_text(
                row["documented_sentinel_source"],
                row["documented_sentinel_locator"],
                row["documented_sentinel_source_sha256"],
            ),
            "Candidate observations: finite retained source values, not null-conversion "
            f"directives; values={row['candidate_sentinel_values_json']}",
        )
    )


def column_comment_contract(
    rows: list[dict[str, str]],
) -> tuple[ColumnComment, ...]:
    """Generate exactly one evidence-preserving comment per mirror column."""
    build_schema_contract(rows)
    comments: list[ColumnComment] = []
    for row in rows:
        table = row["target_table"]
        column = row["target_identifier"]
        text = _comment_text(row)
        comments.append(
            ColumnComment(
                table,
                column,
                text,
                "COMMENT ON COLUMN "
                f'"source".{quote_identifier(table)}.{quote_identifier(column)} '
                f"IS {sql_literal(text)};",
            )
        )
    return tuple(comments)


def _required_mirror_column(table: str, column: str) -> bool:
    """Express only nullability implied by the authorized master key contract."""
    return (table == "photometry_primary" and column in {"id", "source_row"}) or (
        table in MASTER_EXTENSION_TABLES and column in {"id", "source_row"}
    )


def _render_table_constraint(item: TableConstraint) -> str:
    """Render one named table constraint."""
    columns = ", ".join(quote_identifier(column) for column in item.columns)
    prefix = f"CONSTRAINT {quote_identifier(item.name)} "
    if item.kind == "primary_key":
        return f"{prefix}PRIMARY KEY ({columns})"
    if item.kind == "unique":
        return f"{prefix}UNIQUE ({columns})"
    if item.kind == "foreign_key" and item.references is not None:
        ref_table, ref_columns = item.references
        rendered_refs = ", ".join(quote_identifier(column) for column in ref_columns)
        return (
            f"{prefix}FOREIGN KEY ({columns}) REFERENCES "
            f'"source".{quote_identifier(ref_table)} ({rendered_refs})'
        )
    raise ValueError(f"unsupported table constraint kind: {item.kind}")


# =============================================================================
# SQL generation
# =============================================================================


def generate_sql(rows: list[dict[str, str]]) -> str:
    """Generate deterministic PostgreSQL DDL from the two authorized contracts."""
    schema = build_schema_contract(rows)
    table_constraints = table_constraint_contract(rows)
    checks_by_table: dict[str, list[CheckContract]] = {
        table: [] for table in MIRROR_TABLE_ORDER
    }
    for check in array_check_contract(rows):
        checks_by_table[check.table].append(check)

    lines = [
        "-- Generated by src/etl/generate_schema_v11.py; DO NOT EDIT.",
        "-- Inputs: sealed columns-v11.csv and provenance contract "
        f"{PROVENANCE_CONTRACT_VERSION}.",
        "",
        'CREATE SCHEMA "source";',
        "",
    ]
    for table, columns in schema.items():
        definitions: list[str] = []
        for column in columns:
            nullability = (
                " NOT NULL" if _required_mirror_column(table, column.name) else ""
            )
            definitions.append(
                f"    {quote_identifier(column.name)} {column.sql_type}{nullability}"
            )
        definitions.extend(
            "    " + _render_table_constraint(item) for item in table_constraints[table]
        )
        definitions.extend(
            "    "
            + f"CONSTRAINT {quote_identifier(check.name)} CHECK ({check.expression})"
            for check in checks_by_table[table]
        )
        lines.append(f'CREATE TABLE "source".{quote_identifier(table)} (')
        lines.append(",\n".join(definitions))
        lines.extend((");", ""))

    provenance_definitions: list[str] = []
    for field in PROVENANCE_CONTRACT:
        nullability = "" if field.nullable else " NOT NULL"
        provenance_definitions.append(
            f"    {quote_identifier(field.name)} {field.sql_type}{nullability}"
        )
    provenance_definitions.append(
        "    CONSTRAINT "
        + quote_identifier(constraint_name("primary_key", "provenance", "table_name"))
        + f" PRIMARY KEY ({quote_identifier('table_name')})"
    )
    for field in PROVENANCE_CONTRACT:
        if not field.check_expression:
            continue
        expression = field.check_expression.replace(
            "{column}", quote_identifier(field.name)
        )
        provenance_definitions.append(
            "    CONSTRAINT "
            + quote_identifier(constraint_name("check", "provenance", field.name))
            + f" CHECK ({expression})"
        )
    lines.append('CREATE TABLE "source"."provenance" (')
    lines.append(",\n".join(provenance_definitions))
    lines.extend((");", ""))

    lines.extend(comment.sql for comment in column_comment_contract(rows))
    for field in PROVENANCE_CONTRACT:
        lines.append(
            'COMMENT ON COLUMN "source"."provenance".'
            f"{quote_identifier(field.name)} IS {sql_literal(field.comment)};"
        )
    lines.append("")
    return "\n".join(lines)


def write_or_check(
    rows: list[dict[str, str]], output_path: Path, *, check: bool
) -> None:
    """Write generated bytes or prove an existing artifact is byte-identical."""
    generated = generate_sql(rows).encode("utf-8")
    if check:
        if not output_path.exists() or output_path.read_bytes() != generated:
            raise ValueError(f"generated SQL differs at {output_path}")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(generated)


def configured_paths(config_path: Path) -> tuple[Path, Path]:
    """Resolve both generator paths from the repository configuration."""
    config = yaml.safe_load(config_path.read_text())
    try:
        dictionary_path = Path(config["dictionary"]["columns_v11"])
        output_path = Path(config["dictionary"]["schema_v11_sql"])
    except (KeyError, TypeError) as exc:
        raise ValueError("missing dictionary DDL path configuration") from exc
    return dictionary_path, output_path


def main() -> None:
    """Generate or byte-check the configured schema artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    dictionary_path, output_path = configured_paths(args.config)
    rows = read_dictionary(dictionary_path)
    try:
        write_or_check(rows, output_path, check=args.check)
    except ValueError as exc:
        raise SystemExit(f"schema v1.1 generation check FAILED: {exc}") from exc
    action = "checked" if args.check else "wrote"
    print(
        f"schema v1.1 {action}: 12 mirrors, 1448 mirror columns, "
        f"166 array checks, 13 provenance columns at {output_path}"
    )


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
