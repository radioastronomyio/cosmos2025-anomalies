#!/usr/bin/env python3
"""
Script Name  : load_supplements_v11.py
Description  : Load and verify Gate 3.8 supplement and spec-z mirrors
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Loads the four dictionary-declared supplement and spec-z source artifacts into
their pre-existing empty ``source`` tables. The guarded lifecycle can reverse
only rows committed by this gate and never changes master tables, provenance,
the database, the analyst role, or the credential handoff.

Usage
-----
    doppler run --project ml01 --config dev -- \
      python src/etl/load_supplements_v11.py --load

    doppler run --project ml01 --config dev -- \
      python src/etl/load_supplements_v11.py --verify-only
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import io
import json
import re
import stat
import sys
from collections import Counter, OrderedDict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd
import psycopg
from psycopg import sql
import yaml
from astropy.io import fits

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import bootstrap_v11  # noqa: E402
from src.etl import verify_schema_v11_scratch  # noqa: E402
from src.etl import verify_source_fidelity  # noqa: E402
from src.etl.generate_schema_v11 import quote_identifier  # noqa: E402

# =============================================================================
# Configuration
# =============================================================================

GATE38_TABLES = (
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
    "specz_compilation",
)
GATE38_EMPTY_TABLES = (*GATE38_TABLES, "provenance")
EXPECTED_NATIVE_COLUMNS = {
    "lss_overdensity": 4,
    "galaxy_groups": 14,
    "galaxy_group_memberships": 4,
    "specz_compilation": 32,
}
QUALITY_DEFINITIONS = {
    "4": {"confidence_percent": 97, "description": "Very Reliable Redshift"},
    "3": {"confidence_percent": 95, "description": "Reliable Redshift"},
    "2": {
        "confidence_percent": 80,
        "description": "Moderate Detection of Emission Lines",
    },
    "1": {"confidence_percent": 50, "description": "Tentative Measurement"},
    "0": {"confidence_percent": None, "description": "No Measurement"},
    "9": {
        "confidence_percent": 85,
        "description": "Single Line Detection with Good S/N",
    },
    "+10": {
        "confidence_percent": None,
        "description": "Broad Line Feature (e.g., BL-AGN)",
    },
}
SPECZ_README_SHA256 = "1aee693918c3e8deb8ac9ce273468a37935987f53f2903eb47420dcfbfe90a23"
SUPPLEMENT_VERSION = "v1-release-on-v1.1-holdings"
COPY_NULL_MARKER = bootstrap_v11.COPY_NULL_MARKER
EXPECTED_SPECZ_FLAG_DISTRIBUTION = {
    -99: 67,
    -2: 1,
    -1: 1_794,
    0: 24_594,
    1: 18_526,
    2: 27_013,
    3: 7_217,
    4: 176_004,
    5: 2,
    6: 3,
    9: 2_326,
    10: 12,
    11: 17,
    12: 43,
    13: 59,
    14: 4_269,
    19: 28,
}
EXPECTED_PRIMARY_SPECZ_MATCHES = 24_364
EXPECTED_V1_FINGERPRINT = (
    "82fb7e09f21253f2e9b78e8232c43b737008aa4bfb44daf28640463bea82abe7"
)
GATE38_STAGES = frozenset(
    {
        "preflight",
        "load_lss_overdensity",
        "load_galaxy_groups",
        "load_galaxy_group_memberships",
        "load_specz_compilation",
        "grant_analyst_select",
        "verify_admin",
        "verify_analyst",
        "verify_v1_fingerprint",
        "validate_retained",
        "finalize_grants",
        "finalize_verify_admin",
        "finalize_verify_analyst",
    }
)
MASTER_TABLES = (
    "photometry_primary",
    "lephare",
    "photometry_aper",
    "cigale",
    "ml_morpho",
    "bulge_disk",
    "galight_morph",
)
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs/data_paths.yaml"


# =============================================================================
# Evidence types
# =============================================================================


@dataclass(frozen=True)
class Gate38Contract:
    """Exact config-selected source paths and dictionary-native table rows."""

    paths: dict[str, Path]
    tables: dict[str, tuple[dict[str, str], ...]]


@dataclass(frozen=True)
class SourceObservation:
    """Exact source row count and ordered native-column boundary."""

    row_count: int
    source_columns: tuple[str, ...]


@dataclass(frozen=True)
class TableLoadEvidence:
    """One source-pinned, exact-count, transactionally committed table load."""

    table: str
    source_rows: int
    loaded_rows: int
    declared_bytes: int
    observed_bytes: int
    declared_sha256: str
    observed_sha256: str
    committed: bool


@dataclass(frozen=True)
class RetainedGate38Contract:
    """Source-free retained-load expectations, injectable only for scratch proof."""

    rows: tuple[dict[str, str], ...]
    flag_distribution: Mapping[int, int]
    primary_specz_matches: int
    v1_fingerprint: str


class Gate38Failure(RuntimeError):
    """A redaction-safe Gate 3.8 failure after exact row reversal."""


# =============================================================================
# Contract functions
# =============================================================================


def resolve_gate38_contract(
    config_path: Path, rows: Sequence[dict[str, str]]
) -> Gate38Contract:
    """Resolve the four fixed sources and require complete native dictionary rows."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        paths = {
            "lss_overdensity": Path(config["supplementary"]["lss_overdensity"]),
            "galaxy_groups": Path(config["supplementary"]["group_catalog_groups"]),
            "galaxy_group_memberships": Path(
                config["supplementary"]["group_catalog_memberships"]
            ),
            "specz_compilation": Path(config["specz"]["unique_fits"]),
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("missing Gate 3.8 source path configuration") from exc
    tables: dict[str, tuple[dict[str, str], ...]] = {}
    for table in GATE38_TABLES:
        selected = tuple(row for row in rows if row["target_table"] == table)
        if len(selected) != EXPECTED_NATIVE_COLUMNS[table]:
            raise ValueError(f"Gate 3.8 fields must appear exactly once: {table}")
        if any(row["column_origin"] != "source_native" for row in selected):
            raise ValueError(f"Gate 3.8 metadata column is forbidden: {table}")
        source_names = tuple(row["source_column"] for row in selected)
        target_names = tuple(row["target_identifier"] for row in selected)
        if len(set(source_names)) != len(selected) or len(set(target_names)) != len(
            selected
        ):
            raise ValueError(f"Gate 3.8 fields must appear exactly once: {table}")
        if {Path(row["source_file"]) for row in selected} != {paths[table]}:
            raise ValueError(f"Gate 3.8 dictionary/config source mismatch: {table}")
        tables[table] = selected
    return Gate38Contract(paths=paths, tables=tables)


def assert_gate38_targets_empty(counts: Mapping[str, int]) -> None:
    """Require all four mirrors and provenance to be preflight-zero."""
    if set(counts) != set(GATE38_EMPTY_TABLES) or any(
        not isinstance(count, int) or count != 0 for count in counts.values()
    ):
        raise ValueError("Gate 3.8 targets are not exact preflight-zero state")


def quality_flag_definition_evidence(
    rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    """Validate and return the exact source-cited quality flag definitions."""
    matches = [
        row
        for row in rows
        if row["target_table"] == "specz_compilation"
        and row["target_identifier"] == "flag"
    ]
    if len(matches) != 1:
        raise ValueError("spec-z quality flag dictionary row mismatch")
    row = matches[0]
    expected_phrases = tuple(
        definition["description"] for definition in QUALITY_DEFINITIONS.values()
    )
    if (
        row["description_source"]
        != "/opt/agents/repos/reference-files/speczcompilation/README.md"
        or row["description_locator"]
        != "Quality Assessment Flagging System, lines 60-70"
        or row["description_source_sha256"] != SPECZ_README_SHA256
        or any(phrase not in row["description_text"] for phrase in expected_phrases)
    ):
        raise ValueError("spec-z quality flag definition evidence mismatch")
    return {
        "source": row["description_source"],
        "locator": row["description_locator"],
        "source_sha256": row["description_source_sha256"],
        "definitions": QUALITY_DEFINITIONS,
    }


def summarize_quality_flags(values: Sequence[int]) -> dict[str, Any]:
    """Tabulate every observed flag without filtering or policy labels."""
    distribution = dict(sorted(Counter(int(value) for value in values).items()))
    return {
        "distribution": distribution,
        "flags_3_or_4": distribution.get(3, 0) + distribution.get(4, 0),
        "flag_9": distribution.get(9, 0),
        "rows": sum(distribution.values()),
    }


def supplement_version_evidence() -> dict[str, str]:
    """Capture Gate 3.9 supplement-version values without inserting rows."""
    return {
        table: SUPPLEMENT_VERSION
        for table in GATE38_TABLES
        if table != "specz_compilation"
    }


def membership_group_relationship_evidence() -> dict[str, Any]:
    """Record why Gate 3.8 does not invent a Toni group foreign key."""
    return {
        "defined_by_pinned_source": False,
        "anti_join_exercised": False,
        "reason": "no pinned Toni source document defines ID as a group foreign key",
    }


def _source_column_boundary(
    rows: Sequence[Mapping[str, str]],
) -> tuple[str, ...]:
    """Return exact native source columns or reject metadata/duplicates."""
    if not rows or any(row["column_origin"] != "source_native" for row in rows):
        raise ValueError("Gate 3.8 COPY requires native dictionary rows")
    columns = tuple(row["source_column"] for row in rows)
    if len(set(columns)) != len(columns):
        raise ValueError("Gate 3.8 COPY requires native dictionary rows exactly once")
    return columns


def _matching_fits_hdu(
    hdul: fits.HDUList, rows: Sequence[Mapping[str, str]]
) -> fits.BinTableHDU:
    """Select the sole binary table matching the ordered dictionary columns."""
    expected = _source_column_boundary(rows)
    matches = [
        hdu
        for hdu in hdul
        if isinstance(hdu, fits.BinTableHDU) and tuple(hdu.columns.names) == expected
    ]
    if len(matches) != 1:
        raise ValueError("FITS source column boundary mismatch")
    return matches[0]


def inspect_fits_source(
    path: Path, rows: Sequence[Mapping[str, str]]
) -> SourceObservation:
    """Inspect one exact FITS table without retaining its data."""
    with fits.open(path, memmap=True) as hdul:
        hdu = _matching_fits_hdu(hdul, rows)
        return SourceObservation(len(hdu.data), tuple(hdu.columns.names))


def iter_fits_copy_frames(
    path: Path,
    rows: Sequence[Mapping[str, str]],
    *,
    batch_rows: int,
) -> Iterator[bytes]:
    """Yield bounded PostgreSQL CSV frames from one dictionary-exact FITS table."""
    if batch_rows < 1:
        raise ValueError("COPY batch rows must be positive")
    with fits.open(path, memmap=True) as hdul:
        hdu = _matching_fits_hdu(hdul, rows)
        data = hdu.data
        nulls = {
            column.name: column.null
            for column in hdu.columns
            if column.null is not None
        }
        columns = {row["source_column"]: data[row["source_column"]] for row in rows}
        for start in range(0, len(data), batch_rows):
            stop = min(start + batch_rows, len(data))
            formatted: OrderedDict[str, Any] = OrderedDict()
            for row in rows:
                source = row["source_column"]
                formatted[row["target_identifier"]] = bootstrap_v11.format_native_chunk(
                    row,
                    columns[source][start:stop],
                    fits_null=nulls.get(source),
                )
            frame = pd.DataFrame(
                formatted, columns=[row["target_identifier"] for row in rows]
            )
            buffer = io.StringIO(newline="")
            frame.to_csv(
                buffer,
                sep="\t",
                header=False,
                index=False,
                na_rep=COPY_NULL_MARKER,
                lineterminator="\n",
            )
            yield buffer.getvalue().encode("utf-8")


def _text_header(path: Path) -> tuple[str, ...]:
    """Return the first nonempty whitespace-delimited source header."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return tuple(line.split())
    raise ValueError("text source is empty")


def inspect_text_source(
    path: Path, rows: Sequence[Mapping[str, str]]
) -> SourceObservation:
    """Inspect an exact whitespace table and count nonempty data rows."""
    expected = _source_column_boundary(rows)
    header = _text_header(path)
    if header != expected:
        raise ValueError("text source column boundary mismatch")
    count = 0
    with path.open(encoding="utf-8") as handle:
        header_seen = False
        for line in handle:
            if not line.strip():
                continue
            if not header_seen:
                header_seen = True
                continue
            if len(line.split()) != len(expected):
                raise ValueError("text source row width mismatch")
            count += 1
    return SourceObservation(count, header)


def iter_text_copy_frames(
    path: Path,
    rows: Sequence[Mapping[str, str]],
    *,
    batch_rows: int,
) -> Iterator[bytes]:
    """Yield bounded exact-token COPY frames from one whitespace table."""
    if batch_rows < 1:
        raise ValueError("COPY batch rows must be positive")
    expected = _source_column_boundary(rows)
    if _text_header(path) != expected:
        raise ValueError("text source column boundary mismatch")
    frame: list[str] = []
    with path.open(encoding="utf-8") as handle:
        header_seen = False
        for line in handle:
            if not line.strip():
                continue
            if not header_seen:
                header_seen = True
                continue
            values = line.split()
            if len(values) != len(rows):
                raise ValueError("text source row width mismatch")
            rendered: list[str] = []
            for value, row in zip(values, rows, strict=True):
                if (
                    row["target_type"] in {"real", "double precision"}
                    and value.lower() == "nan"
                ):
                    rendered.append(COPY_NULL_MARKER)
                else:
                    if value == COPY_NULL_MARKER:
                        raise ValueError("source text collides with COPY NULL marker")
                    rendered.append(value)
            frame.append("\t".join(rendered) + "\n")
            if len(frame) == batch_rows:
                yield "".join(frame).encode("utf-8")
                frame = []
    if frame:
        yield "".join(frame).encode("utf-8")


def gate38_copy_statement(table: str, rows: Sequence[Mapping[str, str]]) -> str:
    """Build one data-free COPY statement inside the exact Gate 3.8 boundary."""
    if table not in GATE38_TABLES:
        raise ValueError(f"refusing COPY outside Gate 3.8: {table!r}")
    _source_column_boundary(rows)
    columns = tuple(row["target_identifier"] for row in rows)
    if len(set(columns)) != len(columns):
        raise ValueError("Gate 3.8 COPY requires native dictionary rows exactly once")
    column_sql = ", ".join(quote_identifier(column) for column in columns)
    return (
        f'COPY "source".{quote_identifier(table)} ({column_sql}) FROM STDIN WITH '
        f"(FORMAT csv, DELIMITER E'\\t', NULL '{COPY_NULL_MARKER}')"
    )


def validate_table_load_evidence(evidence: TableLoadEvidence) -> None:
    """Require exact source/pin/count identity and a completed transaction."""
    if (
        evidence.table not in GATE38_TABLES
        or evidence.source_rows < 0
        or evidence.loaded_rows != evidence.source_rows
        or evidence.declared_bytes != evidence.observed_bytes
        or evidence.declared_sha256 != evidence.observed_sha256
        or re.fullmatch(r"[0-9a-f]{64}", evidence.declared_sha256) is None
        or not evidence.committed
    ):
        raise ValueError("Gate 3.8 table load evidence mismatch")


def gate38_cleanup_plan(committed_tables: Sequence[str]) -> tuple[str, ...]:
    """Return reverse commit order inside the exact four-table row boundary."""
    if len(set(committed_tables)) != len(committed_tables) or any(
        table not in GATE38_TABLES for table in committed_tables
    ):
        raise ValueError("Gate 3.8 cleanup boundary mismatch")
    return tuple(reversed(committed_tables))


# =============================================================================
# Transaction and analyst lifecycle helpers
# =============================================================================


def load_gate38_table(
    connection: Any,
    table: str,
    path: Path,
    rows: Sequence[Mapping[str, str]],
    pin: Any,
    *,
    batch_rows: int,
) -> TableLoadEvidence:
    """Stream and commit one exact-count, source-pinned table transaction."""
    if table not in GATE38_TABLES:
        raise ValueError(f"refusing load outside Gate 3.8: {table!r}")
    if pin.declared_bytes != pin.observed_bytes or (
        pin.declared_sha256 != pin.observed_sha256
    ):
        raise ValueError("Gate 3.8 source pin mismatch")
    if table in {"galaxy_groups", "galaxy_group_memberships"}:
        observation = inspect_text_source(path, rows)
        frames = iter_text_copy_frames(path, rows, batch_rows=batch_rows)
    else:
        observation = inspect_fits_source(path, rows)
        frames = iter_fits_copy_frames(path, rows, batch_rows=batch_rows)
    try:
        with connection.cursor().copy(gate38_copy_statement(table, rows)) as copy:
            for frame in frames:
                copy.write(frame)
        loaded_rows = connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(table)
            )
        ).fetchone()[0]
        evidence = TableLoadEvidence(
            table=table,
            source_rows=observation.row_count,
            loaded_rows=loaded_rows,
            declared_bytes=pin.declared_bytes,
            observed_bytes=pin.observed_bytes,
            declared_sha256=pin.declared_sha256,
            observed_sha256=pin.observed_sha256,
            committed=True,
        )
        validate_table_load_evidence(evidence)
        connection.commit()
        return evidence
    except BaseException:
        connection.rollback()
        raise


def _connect_target(settings: bootstrap_v11.Settings) -> Any:
    """Open the configured target through the approved admin transport."""
    return bootstrap_v11._connect(settings, settings.target_database)


def cleanup_committed_gate38_rows(
    settings: bootstrap_v11.Settings, committed_tables: Sequence[str]
) -> tuple[str, ...]:
    """Reverse only tables committed from a preflight-zero Gate 3.8 run."""
    cleanup = gate38_cleanup_plan(committed_tables)
    with _connect_target(settings) as connection:
        for table in cleanup:
            connection.execute(
                sql.SQL("TRUNCATE {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            )
        connection.commit()
        counts = {
            table: connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
            for table in GATE38_EMPTY_TABLES
        }
    assert_gate38_targets_empty(counts)
    return cleanup


def build_gate38_failure_after_cleanup(
    settings: bootstrap_v11.Settings,
    committed_tables: Sequence[str],
    *,
    stage: str,
    error: BaseException,
    loads_sealed: bool = False,
    granted_tables: Sequence[str] = (),
    expected_counts: Mapping[str, int] | None = None,
) -> Gate38Failure:
    """Apply phase-aware cleanup and expose safe staged exception metadata."""
    safe_stage = stage if stage in GATE38_STAGES else "unknown"
    error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
    try:
        if loads_sealed:
            if expected_counts is None or set(expected_counts) != set(GATE38_TABLES):
                raise ValueError("sealed Gate 3.8 expected-count boundary mismatch")
            revoked_tables = revoke_gate38_select_grants(settings, granted_tables)
            validate_retained_gate38_counts(settings, expected_counts)
            retained_tables = tuple(GATE38_TABLES)
        else:
            reversed_tables = cleanup_committed_gate38_rows(settings, committed_tables)
    except BaseException as cleanup_error:
        cleanup_class, cleanup_sqlstate = bootstrap_v11._safe_exception_metadata(
            cleanup_error
        )
        return Gate38Failure(
            f"stage={safe_stage} exception={error_class} sqlstate={sqlstate} "
            "cleanup=failed "
            f"cleanup_exception={cleanup_class} "
            f"cleanup_sqlstate={cleanup_sqlstate}"
        )
    if loads_sealed:
        retained_text = ",".join(retained_tables)
        revoked_text = ",".join(revoked_tables) if revoked_tables else "none"
        return Gate38Failure(
            f"stage={safe_stage} exception={error_class} sqlstate={sqlstate} "
            f"retained={retained_text} revoked={revoked_text}"
        )
    reversed_text = ",".join(reversed_tables) if reversed_tables else "none"
    return Gate38Failure(
        f"stage={safe_stage} exception={error_class} sqlstate={sqlstate} "
        f"reversed={reversed_text}"
    )


@contextmanager
def _impersonated_analyst(
    settings: bootstrap_v11.Settings,
) -> Iterator[Any]:
    """Delegate to the Gate 3.7 operator-approved admin session transport."""
    with bootstrap_v11._impersonated_analyst(settings) as connection:
        yield connection


def _master_negative_matrix(settings: bootstrap_v11.Settings) -> dict[str, Any]:
    """Retain the complete Gate 3.7 positive/negative privilege matrix."""
    with _connect_target(settings) as connection:
        primary_rows = connection.execute(
            'SELECT count(*) FROM "source"."photometry_primary"'
        ).fetchone()[0]
        connection.rollback()
    return bootstrap_v11.verify_analyst_matrix(
        settings, expected_primary_rows=primary_rows
    )


def verify_gate38_analyst(
    settings: bootstrap_v11.Settings, expected_counts: Mapping[str, int]
) -> dict[str, Any]:
    """Require four new SELECTs and the unchanged full denial matrix."""
    if set(expected_counts) != set(GATE38_TABLES):
        raise ValueError("Gate 3.8 analyst count boundary mismatch")
    observed: dict[str, int] = {}
    with _impersonated_analyst(settings) as connection:
        for table in GATE38_TABLES:
            observed[table] = connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
        connection.rollback()
    if observed != dict(expected_counts):
        raise ValueError("Gate 3.8 analyst SELECT count mismatch")
    return {
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
        "supplement_selects": observed,
        "supplement_matrix": verify_gate38_table_denials(settings, expected_counts),
        "master_matrix": _master_negative_matrix(settings),
    }


def _gate38_denied_operations(table: str, admin_role: str) -> tuple[sql.Composed, ...]:
    """Build six harmless-if-rolled-back write/DDL probes for one table."""
    identifier = sql.Identifier("source", table)
    first_column = sql.Identifier(
        {
            "lss_overdensity": "id",
            "galaxy_groups": "id",
            "galaxy_group_memberships": "galid",
            "specz_compilation": "id_specz",
        }[table]
    )
    return (
        sql.SQL("INSERT INTO {} DEFAULT VALUES").format(identifier),
        sql.SQL("UPDATE {} SET {}={} WHERE false").format(
            identifier, first_column, first_column
        ),
        sql.SQL("DELETE FROM {} WHERE false").format(identifier),
        sql.SQL("TRUNCATE {}").format(identifier),
        sql.SQL("ALTER TABLE {} ADD COLUMN gate_3_8_forbidden integer").format(
            identifier
        ),
        sql.SQL("GRANT {} TO {}").format(
            sql.Identifier(admin_role),
            sql.Identifier(bootstrap_v11.ANALYST_ROLE),
        ),
    )


def verify_gate38_table_denials(
    settings: bootstrap_v11.Settings, expected_counts: Mapping[str, int]
) -> dict[str, Any]:
    """Prove SELECT and six denied write/DDL operations on every new table."""
    if set(expected_counts) != set(GATE38_TABLES):
        raise ValueError("Gate 3.8 denial count boundary mismatch")
    positive = 0
    negative = 0
    with _impersonated_analyst(settings) as connection:
        for table in GATE38_TABLES:
            count = connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
            connection.rollback()
            if count != expected_counts[table]:
                raise ValueError("Gate 3.8 analyst SELECT count mismatch")
            positive += 1
            for operation in _gate38_denied_operations(table, settings.user):
                try:
                    connection.execute(operation)
                except psycopg.errors.InsufficientPrivilege as error:
                    connection.rollback()
                    if error.sqlstate != "42501":
                        raise ValueError(
                            "Gate 3.8 analyst denial SQLSTATE mismatch"
                        ) from error
                    negative += 1
                else:
                    connection.rollback()
                    raise ValueError(
                        f"Gate 3.8 analyst operation unexpectedly allowed: {table}"
                    )
    return {"positive": positive, "negative": negative, "unchanged": True}


def validate_gate38_admin_observation(
    *,
    source_counts: Mapping[str, int],
    target_counts: Mapping[str, int],
    source_flags: Mapping[str, Any],
    target_flags: Mapping[str, Any],
    primary_specz_matches: int,
) -> dict[str, Any]:
    """Validate exact live/source equality while reporting, not forcing, priors."""
    if set(source_counts) != set(GATE38_TABLES):
        raise ValueError("Gate 3.8 source count boundary mismatch")
    expected_target = {**source_counts, "provenance": 0}
    if dict(target_counts) != expected_target:
        raise ValueError("Gate 3.8 target count mismatch")
    if dict(source_flags) != dict(target_flags):
        raise ValueError("Gate 3.8 quality flag mismatch")
    if source_flags.get("rows") != source_counts["specz_compilation"]:
        raise ValueError("Gate 3.8 quality flag row-count mismatch")
    if not isinstance(primary_specz_matches, int) or primary_specz_matches < 0:
        raise ValueError("Gate 3.8 primary/spec-z match count invalid")
    return {
        "counts": dict(source_counts),
        "provenance_rows": 0,
        "quality_flags": dict(target_flags),
        "primary_specz_matches": primary_specz_matches,
        "live_prior": 37_219,
        "discrepancy": primary_specz_matches - 37_219,
    }


def gate38_grant_statements() -> tuple[sql.Composed, ...]:
    """Return only the four authorized analyst SELECT grants."""
    return tuple(
        sql.SQL("GRANT SELECT ON TABLE {}.{} TO {}").format(
            sql.Identifier("source"),
            sql.Identifier(table),
            sql.Identifier(bootstrap_v11.ANALYST_ROLE),
        )
        for table in GATE38_TABLES
    )


def _gate38_select_statement(action: str, table: str) -> sql.Composed:
    """Build one exact per-table analyst SELECT grant or revocation."""
    if action not in {"GRANT", "REVOKE"} or table not in GATE38_TABLES:
        raise ValueError("Gate 3.8 SELECT ACL boundary mismatch")
    direction = sql.SQL("TO") if action == "GRANT" else sql.SQL("FROM")
    return sql.SQL("{} SELECT ON TABLE {}.{} {} {}").format(
        sql.SQL(action),
        sql.Identifier("source"),
        sql.Identifier(table),
        direction,
        sql.Identifier(bootstrap_v11.ANALYST_ROLE),
    )


def gate38_select_acl(settings: bootstrap_v11.Settings) -> dict[str, bool]:
    """Observe only analyst SELECT capability on the exact four tables."""
    with _connect_target(settings) as connection:
        observed = {
            table: connection.execute(
                """
                SELECT has_table_privilege(%s, c.oid, 'SELECT')
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='source' AND c.relname=%s AND c.relkind='r'
                """,
                (bootstrap_v11.ANALYST_ROLE, table),
            ).fetchone()
            for table in GATE38_TABLES
        }
        connection.rollback()
    if any(row is None for row in observed.values()):
        raise ValueError("Gate 3.8 SELECT ACL object boundary mismatch")
    return {table: bool(row[0]) for table, row in observed.items()}


def apply_gate38_select_grants(
    settings: bootstrap_v11.Settings, prior: Mapping[str, bool]
) -> tuple[str, ...]:
    """Grant only SELECT capabilities absent at the preflight boundary."""
    if set(prior) != set(GATE38_TABLES) or any(
        not isinstance(value, bool) for value in prior.values()
    ):
        raise ValueError("Gate 3.8 prior SELECT ACL boundary mismatch")
    applied = tuple(table for table in GATE38_TABLES if not prior[table])
    with _connect_target(settings) as connection:
        for table in applied:
            connection.execute(_gate38_select_statement("GRANT", table))
        connection.commit()
    return applied


def revoke_gate38_select_grants(
    settings: bootstrap_v11.Settings, tables: Sequence[str]
) -> tuple[str, ...]:
    """Revoke only SELECT grants proven absent before this Gate 3.8 run."""
    selected = tuple(tables)
    if (
        len(set(selected)) != len(selected)
        or any(table not in GATE38_TABLES for table in selected)
        or selected != tuple(table for table in GATE38_TABLES if table in selected)
    ):
        raise ValueError("Gate 3.8 SELECT revoke boundary mismatch")
    with _connect_target(settings) as connection:
        for table in selected:
            connection.execute(_gate38_select_statement("REVOKE", table))
        connection.commit()
    return selected


# =============================================================================
# Live preflight and verification
# =============================================================================


def _read_dictionary_rows(path: Path) -> list[dict[str, str]]:
    """Read the sealed CSV while preserving its reviewed row order."""
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fresh_gate38_pins(
    settings: bootstrap_v11.Settings, contract: Gate38Contract
) -> dict[str, verify_source_fidelity.InputEvidence]:
    """Freshly hash the exact four Gate 3.5 manifest inputs."""
    manifest = bootstrap_v11._manifest_contract(settings)
    return {
        table: verify_source_fidelity.pin_manifest_input(
            table, contract.paths[table], manifest
        )
        for table in GATE38_TABLES
    }


def _profile_row_count(rows: Sequence[Mapping[str, str]]) -> int:
    """Recover one table's source count from every sealed native profile."""
    counts = {
        int(profile["row_count"])
        for row in rows
        if row["column_origin"] == "source_native"
        for profile in json.loads(row["profile_json"])["profiles"]
    }
    if len(counts) != 1:
        raise ValueError("sealed dictionary source row-count mismatch")
    return counts.pop()


def _target_counts(connection: Any, tables: Sequence[str]) -> dict[str, int]:
    """Count an exact allowlist of source tables."""
    return {
        table: connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(table)
            )
        ).fetchone()[0]
        for table in tables
    }


def _master_invariants(
    connection: Any, rows: Sequence[dict[str, str]]
) -> dict[str, Any]:
    """Recheck all master counts, ordinals, IDs, and FK alignments read-only."""
    evidence: dict[str, Any] = {}
    primary_count = 0
    for table in MASTER_TABLES:
        table_rows = [row for row in rows if row["target_table"] == table]
        expected = _profile_row_count(table_rows)
        ordinal = connection.execute(
            sql.SQL(
                "SELECT count(*), count(DISTINCT source_row), min(source_row), "
                "max(source_row), count(*) FILTER (WHERE source_row IS NULL) "
                "FROM {}.{}"
            ).format(sql.Identifier("source"), sql.Identifier(table))
        ).fetchone()
        extrema = (0, expected - 1) if expected else (None, None)
        if ordinal != (expected, expected, *extrema, 0):
            raise ValueError(f"master ordinal invariant mismatch: {table}")
        if table == "photometry_primary":
            ids = connection.execute(
                "SELECT count(id), count(DISTINCT id), "
                "count(*) FILTER (WHERE id IS NULL) "
                'FROM "source"."photometry_primary"'
            ).fetchone()
            if ids != (expected, expected, 0):
                raise ValueError("primary ID invariant mismatch")
            primary_count = expected
        else:
            alignment = connection.execute(
                sql.SQL(
                    "SELECT count(e.id), count(DISTINCT e.id), "
                    "count(*) FILTER (WHERE e.id IS NULL), "
                    "count(*) FILTER (WHERE p.id IS NULL) "
                    "FROM {}.{} e LEFT JOIN {}.{} p "
                    "ON p.source_row=e.source_row AND p.id=e.id"
                ).format(
                    sql.Identifier("source"),
                    sql.Identifier(table),
                    sql.Identifier("source"),
                    sql.Identifier("photometry_primary"),
                )
            ).fetchone()
            if alignment != (expected, expected, 0, 0):
                raise ValueError(f"master injected-ID invariant mismatch: {table}")
        evidence[table] = {
            "rows": expected,
            "source_row_distinct": expected,
            "source_row_range": [0, expected - 1],
            "source_row_nulls": 0,
        }
    return {"tables": evidence, "primary_rows": primary_count}


def _source_observations(
    contract: Gate38Contract,
) -> dict[str, SourceObservation]:
    """Read exact source boundaries and counts before the target transaction."""
    return {
        table: (
            inspect_text_source(contract.paths[table], contract.tables[table])
            if table in {"galaxy_groups", "galaxy_group_memberships"}
            else inspect_fits_source(contract.paths[table], contract.tables[table])
        )
        for table in GATE38_TABLES
    }


def validate_source_observations(
    contract: Gate38Contract,
    observations: Mapping[str, SourceObservation],
) -> dict[str, int]:
    """Reconcile each physical source boundary to every sealed profile."""
    if set(observations) != set(GATE38_TABLES):
        raise ValueError("Gate 3.8 source observation boundary mismatch")
    counts: dict[str, int] = {}
    for table in GATE38_TABLES:
        observation = observations[table]
        expected_columns = tuple(row["source_column"] for row in contract.tables[table])
        if observation.source_columns != expected_columns:
            raise ValueError(f"Gate 3.8 source column mismatch: {table}")
        if observation.row_count != _profile_row_count(contract.tables[table]):
            raise ValueError(f"Gate 3.8 source/sealed profile mismatch: {table}")
        counts[table] = observation.row_count
    return counts


def verify_gate38_schema(
    connection: Any, rows: Sequence[dict[str, str]]
) -> dict[str, int]:
    """Require exact objects, columns, nullability, and constraint definitions."""
    structure = verify_schema_v11_scratch._verify_objects_and_columns(
        connection, list(rows)
    )
    structure.update(bootstrap_v11.verify_exact_retained_schema(connection, rows))
    return structure


def _source_quality_flags(
    contract: Gate38Contract,
) -> dict[str, Any]:
    """Tabulate the complete immutable spec-z flag population."""
    table = "specz_compilation"
    rows = contract.tables[table]
    flag_row = next(row for row in rows if row["target_identifier"] == "flag")
    with fits.open(contract.paths[table], memmap=True) as hdul:
        hdu = _matching_fits_hdu(hdul, rows)
        values = np.asarray(hdu.data[flag_row["source_column"]])
        return summarize_quality_flags(values.tolist())


def final_gate38_preflight(
    settings: bootstrap_v11.Settings,
) -> dict[str, Any]:
    """Recheck pins, schema, master identity, empty targets, role, handoff, and v1."""
    rows = bootstrap_v11._read_dictionary(settings)
    contract = resolve_gate38_contract(settings.config_path, rows)
    pins = fresh_gate38_pins(settings, contract)
    sources = _source_observations(contract)
    validate_source_observations(contract, sources)
    with _connect_target(settings) as connection:
        structure = verify_gate38_schema(connection, rows)
        empty_counts = _target_counts(connection, GATE38_EMPTY_TABLES)
        assert_gate38_targets_empty(empty_counts)
        masters = _master_invariants(connection, rows)
        role = bootstrap_v11._role_observation(connection)
        bootstrap_v11.validate_role_observation(role)
        connection.rollback()
    handoff = validate_retained_handoff_security(settings)
    v1 = bootstrap_v11.capture_v1_fingerprint(settings)
    select_acl = gate38_select_acl(settings)
    source_flags = _source_quality_flags(contract)
    if source_flags["rows"] != sources["specz_compilation"].row_count:
        raise ValueError("source spec-z flag population mismatch")
    return {
        "rows": rows,
        "contract": contract,
        "pins": pins,
        "sources": sources,
        "source_flags": source_flags,
        "structure": structure,
        "empty_counts": empty_counts,
        "masters": masters,
        "handoff": handoff,
        "select_acl": select_acl,
        "v1_fingerprint": v1,
    }


def grant_gate38_analyst_select(settings: bootstrap_v11.Settings) -> None:
    """Grant SELECT using four explicit statements and no wildcard surface."""
    with _connect_target(settings) as connection:
        for statement in gate38_grant_statements():
            connection.execute(statement)
        connection.commit()


def validate_retained_gate38_counts(
    settings: bootstrap_v11.Settings, expected_counts: Mapping[str, int]
) -> dict[str, int]:
    """Require the sealed four counts and provenance zero without source reads."""
    if set(expected_counts) != set(GATE38_TABLES):
        raise ValueError("retained Gate 3.8 count boundary mismatch")
    with _connect_target(settings) as connection:
        observed = _target_counts(connection, GATE38_EMPTY_TABLES)
        connection.rollback()
    if observed != {**expected_counts, "provenance": 0}:
        raise ValueError("retained Gate 3.8 count mismatch")
    return observed


def _quality_summary_from_distribution(
    distribution: Mapping[int, int],
) -> dict[str, Any]:
    """Build exact quality evidence from a complete sealed distribution."""
    normalized = dict(
        sorted((int(flag), int(count)) for flag, count in distribution.items())
    )
    return {
        "distribution": normalized,
        "flags_3_or_4": normalized.get(3, 0) + normalized.get(4, 0),
        "flag_9": normalized.get(9, 0),
        "rows": sum(normalized.values()),
    }


def _target_quality_flags(connection: Any) -> dict[str, Any]:
    """Read the complete retained target quality-flag distribution."""
    rows = connection.execute(
        'SELECT flag, count(*) FROM "source"."specz_compilation" '
        "GROUP BY flag ORDER BY flag"
    ).fetchall()
    return _quality_summary_from_distribution(dict(rows))


def validate_retained_gate38(
    settings: bootstrap_v11.Settings,
    *,
    rows: Sequence[dict[str, str]] | None = None,
    expected_flag_distribution: Mapping[int, int] = EXPECTED_SPECZ_FLAG_DISTRIBUTION,
    expected_primary_specz_matches: int = EXPECTED_PRIMARY_SPECZ_MATCHES,
    expected_v1_fingerprint: str = EXPECTED_V1_FINGERPRINT,
) -> dict[str, Any]:
    """Validate a sealed Gate 3.8 load without FITS, text-source, or COPY access."""
    dictionary_rows = (
        list(rows) if rows is not None else bootstrap_v11._read_dictionary(settings)
    )
    contract = resolve_gate38_contract(settings.config_path, dictionary_rows)
    expected_counts = {
        table: _profile_row_count(contract.tables[table]) for table in GATE38_TABLES
    }
    expected_flags = _quality_summary_from_distribution(expected_flag_distribution)
    if expected_flags["rows"] != expected_counts["specz_compilation"]:
        raise ValueError("sealed Gate 3.8 flag/count contract mismatch")
    with _connect_target(settings) as connection:
        structure = verify_gate38_schema(connection, dictionary_rows)
        counts = _target_counts(connection, GATE38_EMPTY_TABLES)
        if counts != {**expected_counts, "provenance": 0}:
            raise ValueError("retained Gate 3.8 count mismatch")
        masters = _master_invariants(connection, dictionary_rows)
        table_checks: dict[str, Any] = {}
        for table in GATE38_TABLES:
            table_rows = [
                row for row in dictionary_rows if row["target_table"] == table
            ]
            table_checks[table] = {
                "columns": len(table_rows),
                "nulls": bootstrap_v11._verify_null_counts(
                    connection, table, table_rows
                ),
                "arrays": bootstrap_v11._verify_arrays(
                    connection, table, table_rows, counts[table]
                ),
                "sentinel_checks": bootstrap_v11._verify_sentinels(
                    connection, table, table_rows
                ),
            }
        flags = _target_quality_flags(connection)
        if flags != expected_flags:
            raise ValueError("retained Gate 3.8 quality flag mismatch")
        matches = connection.execute(
            "SELECT count(*), count(DISTINCT p.id) "
            'FROM "source"."photometry_primary" p '
            'JOIN "source"."specz_compilation" s '
            "ON s.id_specz=p.id_specz_khostovan25"
        ).fetchone()
        if matches != (
            expected_primary_specz_matches,
            expected_primary_specz_matches,
        ):
            raise ValueError("retained Gate 3.8 primary/spec-z join mismatch")
        role = bootstrap_v11._role_observation(connection)
        bootstrap_v11.validate_role_observation(role)
        connection.rollback()
    handoff = validate_retained_handoff_security(settings)
    v1 = bootstrap_v11.capture_v1_fingerprint(settings)
    if v1.sha256 != expected_v1_fingerprint:
        raise ValueError("retained Gate 3.8 v1 fingerprint mismatch")
    return {
        "counts": expected_counts,
        "provenance_rows": 0,
        "structure": structure,
        "masters": masters,
        "table_checks": table_checks,
        "quality_flags": flags,
        "primary_specz_matches": matches[0],
        "role": asdict(role),
        "handoff": handoff,
        "v1_fingerprint": v1.sha256,
    }


def verify_retained_gate38_admin(
    settings: bootstrap_v11.Settings,
    contract: RetainedGate38Contract | None = None,
) -> dict[str, Any]:
    """Revalidate retained data plus the exact post-grant privilege contract."""
    retained = (
        validate_retained_gate38(settings)
        if contract is None
        else validate_retained_gate38(
            settings,
            rows=contract.rows,
            expected_flag_distribution=contract.flag_distribution,
            expected_primary_specz_matches=contract.primary_specz_matches,
            expected_v1_fingerprint=contract.v1_fingerprint,
        )
    )
    with _connect_target(settings) as connection:
        privileges = bootstrap_v11._verify_privilege_contract(connection)
        supplement_acl = _verify_gate38_acl(connection)
        connection.rollback()
    return {
        **retained,
        "privileges": privileges,
        "supplement_acl": supplement_acl,
    }


def validate_persistent_handoff_metadata(path: Path) -> dict[str, Any]:
    """Validate the exact handoff while returning no credential values."""
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("handoff is not an exact regular file")
    parsed = bootstrap_v11.validate_handoff_file(path)
    return {
        "regular": True,
        "mode": "0600",
        "variable_names": tuple(parsed),
        "values_rendered": False,
    }


def validate_retained_handoff_security(
    settings: bootstrap_v11.Settings,
) -> dict[str, Any]:
    """Validate config binding and secret separation, returning metadata only."""
    metadata = settings.handoff_path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("handoff is not an exact regular file")
    values = bootstrap_v11.read_handoff_for_verification(settings)
    return {
        "regular": True,
        "mode": "0600",
        "variable_names": tuple(values),
        "values_rendered": False,
        "configured_host": True,
        "configured_port": True,
        "analyst_admin_secrets_distinct": True,
    }


def verify_gate38_admin(
    settings: bootstrap_v11.Settings,
    rows: Sequence[dict[str, str]],
    source_counts: Mapping[str, int],
    source_flags: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify full structures, values-by-profile, flags, join, role, and objects."""
    with _connect_target(settings) as connection:
        structure = verify_gate38_schema(connection, rows)
        target_counts = _target_counts(connection, GATE38_EMPTY_TABLES)
        table_checks: dict[str, Any] = {}
        for table in GATE38_TABLES:
            table_rows = [row for row in rows if row["target_table"] == table]
            row_count = target_counts[table]
            table_checks[table] = {
                "columns": len(table_rows),
                "nulls": bootstrap_v11._verify_null_counts(
                    connection, table, table_rows
                ),
                "arrays": bootstrap_v11._verify_arrays(
                    connection, table, table_rows, row_count
                ),
                "sentinel_checks": bootstrap_v11._verify_sentinels(
                    connection, table, table_rows
                ),
            }
        flag_rows = connection.execute(
            'SELECT flag, count(*) FROM "source"."specz_compilation" '
            "GROUP BY flag ORDER BY flag"
        ).fetchall()
        target_flags = summarize_quality_flags(
            [flag for flag, count in flag_rows for _ in range(count)]
        )
        matches = connection.execute(
            "SELECT count(*), count(DISTINCT p.id) "
            'FROM "source"."photometry_primary" p '
            'JOIN "source"."specz_compilation" s '
            "ON s.id_specz=p.id_specz_khostovan25"
        ).fetchone()
        if matches[0] != matches[1]:
            raise ValueError("primary/spec-z join multiplicity mismatch")
        role = bootstrap_v11._role_observation(connection)
        bootstrap_v11.validate_role_observation(role)
        privileges = bootstrap_v11._verify_privilege_contract(connection)
        supplement_acl = _verify_gate38_acl(connection)
        connection.rollback()
    validated = validate_gate38_admin_observation(
        source_counts=source_counts,
        target_counts=target_counts,
        source_flags=source_flags,
        target_flags=target_flags,
        primary_specz_matches=matches[0],
    )
    return {
        **validated,
        "structure": structure,
        "table_checks": table_checks,
        "analyst_role": asdict(role),
        "privileges": privileges,
        "supplement_acl": supplement_acl,
        "join_materialized": False,
        "membership_group_relationship": membership_group_relationship_evidence(),
    }


def _verify_gate38_acl(connection: Any) -> dict[str, Any]:
    """Require SELECT-only ACLs on every Gate 3.8 table by OID."""
    evidence: dict[str, Any] = {}
    for table in GATE38_TABLES:
        observed = connection.execute(
            """
            SELECT has_table_privilege(%s, c.oid, 'SELECT'),
                   has_table_privilege(%s, c.oid, 'INSERT'),
                   has_table_privilege(%s, c.oid, 'UPDATE'),
                   has_table_privilege(%s, c.oid, 'DELETE'),
                   has_table_privilege(%s, c.oid, 'TRUNCATE'),
                   has_table_privilege(%s, c.oid, 'REFERENCES'),
                   has_table_privilege(%s, c.oid, 'TRIGGER')
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='source' AND c.relname=%s AND c.relkind='r'
            """,
            (bootstrap_v11.ANALYST_ROLE,) * 7 + (table,),
        ).fetchone()
        if observed is None or tuple(observed) != (
            True,
            False,
            False,
            False,
            False,
            False,
            False,
        ):
            raise ValueError(f"Gate 3.8 analyst ACL mismatch: {table}")
        evidence[table] = {"select": True, "write_or_ddl": False}
    return evidence


# =============================================================================
# Guarded load and CLI
# =============================================================================


def _safe_pin_evidence(pin: Any) -> dict[str, Any]:
    """Return pin identity without including paths or runtime credentials."""
    return {
        "declared_bytes": pin.declared_bytes,
        "observed_bytes": pin.observed_bytes,
        "declared_sha256": pin.declared_sha256,
        "observed_sha256": pin.observed_sha256,
    }


def run_gate38_load(settings: bootstrap_v11.Settings) -> dict[str, Any]:
    """Run four loads with pre-seal row cleanup and post-seal retention."""
    stage = "preflight"
    committed: list[str] = []
    loads_sealed = False
    granted_tables: tuple[str, ...] = ()
    source_counts: dict[str, int] | None = None
    try:
        preflight = final_gate38_preflight(settings)
        print("gate38_stage=preflight status=passed", flush=True)
        source_counts = {
            table: observation.row_count
            for table, observation in preflight["sources"].items()
        }
        load_evidence: dict[str, Any] = {}
        for table in GATE38_TABLES:
            stage = f"load_{table}"
            # Preflight proved every table zero, so early tracking makes both a
            # pre-commit rollback and a post-commit context failure safe.
            committed.append(table)
            with _connect_target(settings) as connection:
                evidence = load_gate38_table(
                    connection,
                    table,
                    preflight["contract"].paths[table],
                    preflight["contract"].tables[table],
                    preflight["pins"][table],
                    batch_rows=settings.copy_batch_rows,
                )
                if table == GATE38_TABLES[-1]:
                    loads_sealed = True
            load_evidence[table] = asdict(evidence)
            print(
                f"gate38_table={table} status=committed rows={evidence.loaded_rows}",
                flush=True,
            )
        stage = "grant_analyst_select"
        grant_candidates = tuple(
            table for table in GATE38_TABLES if not preflight["select_acl"][table]
        )
        granted_tables = grant_candidates
        applied_tables = apply_gate38_select_grants(settings, preflight["select_acl"])
        if applied_tables != grant_candidates:
            raise ValueError("Gate 3.8 applied SELECT grant boundary mismatch")
        print("gate38_stage=grant_analyst_select status=passed", flush=True)
        stage = "verify_admin"
        admin = verify_gate38_admin(
            settings,
            preflight["rows"],
            source_counts,
            preflight["source_flags"],
        )
        print("gate38_stage=verify_admin status=passed", flush=True)
        stage = "verify_analyst"
        analyst = verify_gate38_analyst(settings, source_counts)
        print("gate38_stage=verify_analyst status=passed", flush=True)
        stage = "verify_v1_fingerprint"
        after = bootstrap_v11.capture_v1_fingerprint(settings)
        if after.sha256 != preflight["v1_fingerprint"].sha256:
            raise ValueError("v1 fingerprint changed during Gate 3.8")
        print("gate38_stage=verify_v1_fingerprint status=passed", flush=True)
        return {
            "gate": "3.8",
            "status": "passed",
            "mode": "load",
            "source_pins": {
                table: _safe_pin_evidence(preflight["pins"][table])
                for table in GATE38_TABLES
            },
            "loads": load_evidence,
            "admin": admin,
            "analyst": analyst,
            "quality_definitions": quality_flag_definition_evidence(preflight["rows"]),
            "supplement_versions_for_gate_3_9": supplement_version_evidence(),
            "provenance_rows": 0,
            "v1_fingerprint": after.sha256,
        }
    except BaseException as error:
        raise build_gate38_failure_after_cleanup(
            settings,
            committed,
            stage=stage,
            error=error,
            loads_sealed=loads_sealed,
            granted_tables=granted_tables,
            expected_counts=source_counts,
        ) from None


def run_gate38_finalize_admin(
    settings: bootstrap_v11.Settings,
    contract: RetainedGate38Contract | None = None,
) -> dict[str, Any]:
    """Resume only administration/access over an exact retained sealed load."""
    stage = "validate_retained"
    granted_tables: tuple[str, ...] = ()
    try:
        retained = (
            validate_retained_gate38(settings)
            if contract is None
            else validate_retained_gate38(
                settings,
                rows=contract.rows,
                expected_flag_distribution=contract.flag_distribution,
                expected_primary_specz_matches=contract.primary_specz_matches,
                expected_v1_fingerprint=contract.v1_fingerprint,
            )
        )
    except BaseException as error:
        error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
        raise Gate38Failure(
            f"stage={stage} exception={error_class} sqlstate={sqlstate} "
            "retained=unvalidated revoked=none"
        ) from None
    expected_counts = retained["counts"]
    try:
        prior = gate38_select_acl(settings)
        candidates = tuple(table for table in GATE38_TABLES if not prior[table])
        stage = "finalize_grants"
        granted_tables = candidates
        applied_tables = apply_gate38_select_grants(settings, prior)
        if applied_tables != candidates:
            raise ValueError("Gate 3.8 finalize grant boundary mismatch")
        stage = "finalize_verify_admin"
        admin = verify_retained_gate38_admin(settings, contract)
        stage = "finalize_verify_analyst"
        analyst = verify_gate38_analyst(settings, expected_counts)
        return {
            "gate": "3.8",
            "status": "passed",
            "mode": "finalize-admin",
            "retained": retained,
            "admin": admin,
            "analyst": analyst,
            "applied_select_grants": list(granted_tables),
            "source_reads": 0,
            "copy_operations": 0,
            "truncate_operations": 0,
            "direct_network_auth_exercised": False,
        }
    except BaseException as error:
        raise build_gate38_failure_after_cleanup(
            settings,
            GATE38_TABLES,
            stage=stage,
            error=error,
            loads_sealed=True,
            granted_tables=granted_tables,
            expected_counts=expected_counts,
        ) from None


def run_gate38_verify_only(settings: bootstrap_v11.Settings) -> dict[str, Any]:
    """Re-read immutable sources and verify the retained Gate 3.8 target."""
    rows = bootstrap_v11._read_dictionary(settings)
    contract = resolve_gate38_contract(settings.config_path, rows)
    pins = fresh_gate38_pins(settings, contract)
    sources = _source_observations(contract)
    source_counts = validate_source_observations(contract, sources)
    source_flags = _source_quality_flags(contract)
    admin = verify_gate38_admin(settings, rows, source_counts, source_flags)
    analyst = verify_gate38_analyst(settings, source_counts)
    validate_retained_handoff_security(settings)
    v1 = bootstrap_v11.capture_v1_fingerprint(settings)
    return {
        "gate": "3.8",
        "status": "passed",
        "mode": "verify-only",
        "source_pins": {table: _safe_pin_evidence(pin) for table, pin in pins.items()},
        "admin": admin,
        "analyst": analyst,
        "quality_definitions": quality_flag_definition_evidence(rows),
        "supplement_versions_for_gate_3_9": supplement_version_evidence(),
        "provenance_rows": 0,
        "v1_fingerprint": v1.sha256,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the mutually exclusive persistent-load/read-only CLI modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--load", action="store_true")
    mode.add_argument("--finalize-admin", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Gate 3.8 without ever rendering unexpected exception messages."""
    try:
        arguments = parse_args(argv)
        settings = bootstrap_v11.resolve_settings(arguments.config)
        if arguments.load:
            result = run_gate38_load(settings)
        elif arguments.finalize_admin:
            result = run_gate38_finalize_admin(settings)
        else:
            result = run_gate38_verify_only(settings)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except Gate38Failure as error:
        print(str(error), file=sys.stderr)
        return 1
    except BaseException as error:
        error_class, sqlstate = bootstrap_v11._safe_exception_metadata(error)
        print(
            f"stage=cli exception={error_class} sqlstate={sqlstate}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
