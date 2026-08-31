#!/usr/bin/env python3
"""
Script Name  : bootstrap_v11.py
Description  : Guard and verify the persistent ETL v2 master mirror
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Implements the Gate 3.7 fixed-target guards, lossless FITS-to-PostgreSQL COPY
conversion, deterministic v1 fingerprinting, analyst-role contract, and exact
credential handoff. The create/load and read-only verification entry points are
defined below these testable contracts.

Usage
-----
    doppler run --project ml01 --config dev -- \
      python src/etl/bootstrap_v11.py --create-load
    doppler run --project ml01 --config dev -- \
      python src/etl/bootstrap_v11.py --verify-only
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
import re
import secrets
import stat
import string
import subprocess
import sys
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd
import psycopg
import yaml
from astropy.io import fits
from psycopg import sql

# Direct execution starts with src/etl on sys.path. Add the repository root so
# package imports behave the same under the CLI and pytest.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import generate_schema_v11, verify_schema_v11_scratch  # noqa: E402
from src.etl import verify_source_fidelity  # noqa: E402
from src.etl.generate_schema_v11 import quote_identifier  # noqa: E402

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"
BASELINE_DATABASE = "cosmos2025"
TARGET_DATABASE = "cosmos2025_v11"
ANALYST_ROLE = "cosmos2025_v11_ro"
EXPECTED_HANDOFF_PATH = REPO_ROOT / "internal-files" / "cosmos2025-v11.env"
MASTER_TABLES = (
    "photometry_primary",
    "photometry_aper",
    "lephare",
    "cigale",
    "ml_morpho",
    "bulge_disk",
    "galight_morph",
)
UNLOADED_TABLES = (
    "lss_overdensity",
    "galaxy_groups",
    "galaxy_group_memberships",
    "specz_compilation",
    "provenance",
)
HANDOFF_NAMES = (
    "PGSQL01_HOST",
    "PGSQL01_PORT",
    "PGSQL01_COSMOS2025_V11_DB",
    "PGSQL01_COSMOS2025_V11_USER",
    "PGSQL01_COSMOS2025_V11_PASSWORD",
)
COPY_NULL_MARKER = "__COSMOS2025_V11_SQL_NULL__"
SECRET_KEYS = frozenset(
    {
        "password",
        "secret",
        "analyst_secret",
        "admin_password",
        "PGSQL01_COSMOS2025_V11_PASSWORD",
    }
)
LIFECYCLE_STAGES = frozenset(
    {
        "validate_retained_load",
        "create_database",
        "execute_reviewed_ddl",
        "load_master_tables",
        "create_role",
        "verify_role",
        "verify_admin",
        "verify_analyst",
        "verify_default_privileges",
        "write_handoff",
        "read_handoff",
        "verify_v1_fingerprint",
        "verify_handoff_git",
    }
)
POST_SEAL_FAILURE_STAGES = frozenset(
    {
        "create_role",
        "verify_role",
        "verify_admin",
        "verify_analyst",
        "verify_default_privileges",
        "write_handoff",
        "read_handoff",
        "verify_v1_fingerprint",
        "verify_handoff_git",
    }
)
POST_LOAD_SUCCESS_STAGES = (
    "verify_role",
    "verify_admin",
    "analyst_matrix_before_handoff",
    "verify_default_privileges",
    "write_handoff",
    "analyst_matrix_after_handoff",
    "verify_v1_fingerprint",
    "verify_handoff_git",
)


# =============================================================================
# Evidence types
# =============================================================================


@dataclass(frozen=True)
class Settings:
    """Resolved config and environment values for the fixed Gate 3.7 target."""

    host: str
    port: int
    user: str
    password: str
    maintenance_database: str
    baseline_database: str
    target_database: str
    analyst_role: str
    handoff_path: Path
    dictionary_path: Path
    ddl_path: Path
    manifest_path: Path
    copy_batch_rows: int
    minimum_database_free_bytes: int
    repo_root: Path
    config_path: Path


@dataclass(frozen=True)
class CreatedResources:
    """Resources owned by the current non-idempotent process."""

    database: bool = False
    role: bool = False
    handoff: bool = False


@dataclass(frozen=True)
class Fingerprint:
    """Canonical structured content and its SHA-256 digest."""

    content: bytes
    sha256: str


@dataclass(frozen=True)
class MatrixOperation:
    """One analyst permission check and its expected outcome."""

    statement: str
    allowed: bool


@dataclass(frozen=True)
class DatabaseCapacity:
    """Fresh byte capacity reported by the PostgreSQL data volume."""

    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent_used: int


@dataclass(frozen=True)
class RoleObservation:
    """Security attributes, memberships, and ownership held by the analyst."""

    login: bool
    superuser: bool
    create_database: bool
    create_role: bool
    inherit: bool
    replication: bool
    bypass_rls: bool
    scram_credential_present: bool
    memberships: int
    owned_objects: int


@dataclass(frozen=True)
class HandoffGitEvidence:
    """Secret-free Git and output checks for the ignored handoff."""

    ignored: bool
    tracked: bool
    secret_in_tracked: bool
    secret_in_staged: bool
    secret_in_captured_outputs: bool


@dataclass(frozen=True)
class TableLoadEvidence:
    """Source-integrity and transactional row evidence for one master table."""

    table: str
    source_rows: int
    loaded_rows: int
    declared_bytes: int
    observed_bytes: int
    declared_sha256: str
    observed_sha256: str
    elapsed_seconds: float
    committed: bool


class LifecycleFailure(RuntimeError):
    """A pre-redacted lifecycle diagnostic safe for direct CLI display."""


@dataclass(frozen=True)
class RolePasswordPlan:
    """Secret-free role SQL plus the sole parameterized secret boundary."""

    create_sql: str
    set_config_sql: str
    set_config_parameters: tuple[str]
    apply_sql: str


@dataclass(frozen=True)
class AnalystVerificationPlan:
    """Operator-approved admin-session impersonation boundary for analyst checks."""

    authenticated_user: str
    effective_user: str
    set_authorization_sql: str
    reset_authorization_sql: str
    direct_network_auth_exercised: bool


# =============================================================================
# Fixed-target and cleanup guards
# =============================================================================


def resolve_settings(
    config_path: Path, environment: Mapping[str, str] = os.environ
) -> Settings:
    """Resolve config-selected environment variables and fixed Gate 3.7 names."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        database = config["database"]
        handoff = config["handoff"]
        etl_v2 = config["etl_v2"]
        env_names = {
            key: str(database[key])
            for key in ("host_env", "port_env", "user_env", "password_env")
        }
        baseline = str(database["database_name"])
        target = str(database["target_database"])
        role = str(database["analyst_role"])
        maintenance = str(database["maintenance_database"])
        handoff_path = Path(handoff["cosmos2025_v11_env"])
        dictionary_path = Path(config["dictionary"]["columns_v11"])
        ddl_path = Path(config["dictionary"]["schema_v11_sql"])
        manifest_path = Path(config["provenance"]["source_manifest_v11"])
        copy_batch_rows = int(etl_v2["copy_batch_rows"])
        minimum_database_free_bytes = int(etl_v2["minimum_database_free_bytes"])
        repo_root = Path(config["repo_root"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("missing Gate 3.7 configuration") from exc
    fixed = (baseline, target, role)
    if fixed != (BASELINE_DATABASE, TARGET_DATABASE, ANALYST_ROLE):
        raise ValueError(f"fixed Gate 3.7 target mismatch: {fixed!r}")
    if maintenance in {BASELINE_DATABASE, TARGET_DATABASE}:
        raise ValueError("fixed Gate 3.7 target cannot be the maintenance database")
    expected_handoff = repo_root / "internal-files" / "cosmos2025-v11.env"
    if handoff_path != expected_handoff:
        raise ValueError("fixed Gate 3.7 target handoff path mismatch")
    if copy_batch_rows < 1 or minimum_database_free_bytes < 1:
        raise ValueError("Gate 3.7 positive capacity/batch configuration required")
    missing = [name for name in env_names.values() if not environment.get(name)]
    if missing:
        raise ValueError(f"missing injected database environment variables: {missing}")
    try:
        port = int(environment[env_names["port_env"]])
    except ValueError as exc:
        raise ValueError(
            f"invalid port in environment variable {env_names['port_env']}"
        ) from exc
    return Settings(
        host=environment[env_names["host_env"]],
        port=port,
        user=environment[env_names["user_env"]],
        password=environment[env_names["password_env"]],
        maintenance_database=maintenance,
        baseline_database=baseline,
        target_database=target,
        analyst_role=role,
        handoff_path=handoff_path,
        dictionary_path=dictionary_path,
        ddl_path=ddl_path,
        manifest_path=manifest_path,
        copy_batch_rows=copy_batch_rows,
        minimum_database_free_bytes=minimum_database_free_bytes,
        repo_root=repo_root,
        config_path=config_path,
    )


def assert_targets_absent(
    *, database_names: set[str], role_names: set[str], handoff_path: Path
) -> None:
    """Halt before mutation if any non-idempotent Gate 3.7 target exists."""
    if TARGET_DATABASE in database_names:
        raise ValueError("target database already exists")
    if ANALYST_ROLE in role_names:
        raise ValueError("target role already exists")
    if handoff_path.exists() or handoff_path.is_symlink():
        raise ValueError("handoff already exists")


def assert_finalize_admin_targets(
    *, database_names: set[str], role_names: set[str], handoff_path: Path
) -> None:
    """Accept only an exact retained database with incomplete admin artifacts."""
    if TARGET_DATABASE not in database_names:
        raise ValueError("retained target database is absent")
    if ANALYST_ROLE in role_names:
        raise ValueError("analyst role already exists")
    if handoff_path.exists() or handoff_path.is_symlink():
        raise ValueError("handoff already exists")


def validate_cleanup_target(
    kind: str, name: str, *, expected_handoff: Path = EXPECTED_HANDOFF_PATH
) -> str:
    """Validate one exact cleanup target without accepting prefixes or aliases."""
    expected = {
        "database": TARGET_DATABASE,
        "role": ANALYST_ROLE,
        "handoff": str(expected_handoff),
    }
    if kind not in expected or name != expected[kind]:
        raise ValueError(f"refusing unsafe cleanup target: {kind} {name!r}")
    return name


def cleanup_plan(created: CreatedResources) -> tuple[str, ...]:
    """Return reverse-order cleanup steps only for resources this run created."""
    plan: list[str] = []
    if created.handoff:
        plan.append("handoff")
    if created.database:
        plan.append("database")
    if created.role:
        plan.append("role")
    return tuple(plan)


def parse_database_capacity(output: str) -> DatabaseCapacity:
    """Parse the fixed server-side ``df`` capacity probe."""
    match = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s*", output)
    if match is None:
        raise ValueError("database capacity probe returned malformed output")
    total, used, available, percent = (int(value) for value in match.groups())
    if total <= 0 or used < 0 or available < 0 or not 0 <= percent <= 100:
        raise ValueError("database capacity probe returned invalid values")
    return DatabaseCapacity(total, used, available, percent)


def require_database_capacity(
    evidence: DatabaseCapacity, *, minimum_available_bytes: int
) -> None:
    """Halt before creation when database-volume free space is insufficient."""
    if evidence.available_bytes < minimum_available_bytes:
        raise ValueError(
            "database volume capacity below minimum: "
            f"available={evidence.available_bytes}, "
            f"required={minimum_available_bytes}"
        )


# =============================================================================
# Source-to-COPY conversion
# =============================================================================


def source_scalar(value: Any, *, masked: bool) -> Any:
    """Apply only FITS-mask and IEEE-NaN null conversion to one scalar."""
    if masked:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def source_array(values: Sequence[Any], *, mask: Sequence[bool] | None) -> list[Any]:
    """Convert a one-dimensional fixed array with element-level NULL states."""
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"source array must be one-dimensional: {array.shape}")
    if mask is None:
        mask_array = np.zeros(array.shape, dtype=bool)
    else:
        mask_array = np.asarray(mask, dtype=bool)
        if mask_array.shape != array.shape:
            raise ValueError("source array mask shape mismatch")
    return [
        source_scalar(value, masked=bool(masked))
        for value, masked in zip(array, mask_array, strict=True)
    ]


def copy_scalar_literal(value: Any) -> str:
    """Return one PostgreSQL COPY-compatible scalar literal before text escaping."""
    converted = source_scalar(value, masked=False)
    if converted is None:
        return r"\N"
    if isinstance(converted, bool):
        return "t" if converted else "f"
    if isinstance(converted, float):
        if math.isinf(converted):
            return "Infinity" if converted > 0 else "-Infinity"
        return repr(converted)
    return str(converted)


def postgres_array_literal(values: Sequence[Any]) -> str:
    """Serialize one-dimensional values as a PostgreSQL array input literal."""
    fields: list[str] = []
    for value in values:
        if value is None:
            fields.append("NULL")
            continue
        literal = copy_scalar_literal(value)
        if isinstance(value, (str, bytes, np.str_, np.bytes_)):
            literal = literal.replace("\\", "\\\\").replace('"', '\\"')
            fields.append(f'"{literal}"')
        else:
            fields.append(literal)
    return "{" + ",".join(fields) + "}"


def copy_text_field(value: Any) -> str:
    """Escape one scalar/array literal for PostgreSQL text COPY."""
    if value is None:
        return r"\N"
    if isinstance(value, (list, tuple)):
        text = postgres_array_literal(value)
    else:
        text = copy_scalar_literal(value)
    return (
        text.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def build_copy_row(
    dictionary_rows: Sequence[Mapping[str, str]],
    *,
    native_values: Mapping[str, Any],
    source_row: int,
    primary_id: int,
) -> bytes:
    """Build one COPY row in sealed dictionary order with declared metadata only."""
    values: list[Any] = []
    for row in dictionary_rows:
        origin = row["column_origin"]
        if origin == "source_native":
            values.append(native_values[row["source_column"]])
        elif origin == "source_row_metadata":
            values.append(source_row)
        elif origin == "id_injected":
            values.append(primary_id)
        else:
            raise ValueError(f"unsupported dictionary column origin: {origin!r}")
    return ("\t".join(copy_text_field(value) for value in values) + "\n").encode(
        "utf-8"
    )


def copy_statement(table: str, columns: Sequence[str]) -> str:
    """Build a data-free COPY statement from validated dictionary identifiers."""
    if table not in MASTER_TABLES:
        raise ValueError(f"refusing COPY outside Gate 3.7 master tables: {table!r}")
    column_sql = ", ".join(quote_identifier(column) for column in columns)
    return (
        f"COPY {quote_identifier('source')}.{quote_identifier(table)} "
        f"({column_sql}) FROM STDIN WITH "
        f"(FORMAT csv, DELIMITER E'\\t', NULL '{COPY_NULL_MARKER}')"
    )


def serialize_copy_frame(
    rows: Sequence[Sequence[Any]], *, columns: Sequence[str]
) -> bytes:
    """Serialize one bounded frame with PostgreSQL CSV quoting and explicit NULL."""
    frame = pd.DataFrame.from_records(rows, columns=list(columns))
    buffer = io.StringIO(newline="")
    frame.to_csv(
        buffer,
        sep="\t",
        header=False,
        index=False,
        na_rep=COPY_NULL_MARKER,
        lineterminator="\n",
    )
    return buffer.getvalue().encode("utf-8")


def native_values_at(
    dictionary_rows: Sequence[Mapping[str, str]],
    *,
    columns: Mapping[str, np.ndarray],
    fits_nulls: Mapping[str, Any],
    index: int,
) -> dict[str, Any]:
    """Convert only native dictionary fields for one source ordinal."""
    converted: dict[str, Any] = {}
    for row in dictionary_rows:
        if row["column_origin"] != "source_native":
            continue
        name = row["source_column"]
        value = columns[name][index]
        null_value = fits_nulls.get(name)
        if row["target_type"].endswith("[]"):
            raw_array = np.asarray(value)
            mask = None if null_value is None else np.equal(raw_array, null_value)
            converted[name] = source_array(raw_array, mask=mask)
        else:
            masked = bool(null_value is not None and value == null_value)
            converted[name] = source_scalar(value, masked=masked)
    return converted


def _format_float_values(values: np.ndarray) -> np.ndarray:
    """Vectorize round-trip-safe PostgreSQL float literals."""
    array = np.asarray(values)
    precision = 9 if array.dtype.itemsize <= 4 else 17
    rendered = np.char.mod(f"%.{precision}g", array)
    rendered = np.asarray(rendered, dtype=object)
    rendered[np.isposinf(array)] = "Infinity"
    rendered[np.isneginf(array)] = "-Infinity"
    rendered[np.isnan(array)] = None
    negative_zero = (array == 0) & np.signbit(array)
    rendered[negative_zero] = "-0.0"
    return rendered


def format_native_chunk(
    row: Mapping[str, str], values: np.ndarray, *, fits_null: Any | None
) -> np.ndarray:
    """Format one native FITS column for a bounded vectorized COPY frame."""
    array = np.asarray(values)
    target_type = row["target_type"]
    if target_type.endswith("[]"):
        if array.ndim != 2:
            raise ValueError(f"vector COPY source shape mismatch: {array.shape}")
        base_type = target_type.removesuffix("[]")
        if base_type not in {
            "real",
            "double precision",
            "smallint",
            "integer",
            "bigint",
        }:
            raise ValueError(f"unsupported vector COPY type: {target_type}")
        if array.dtype.kind == "f":
            elements = _format_float_values(array)
            element_nulls = np.isnan(array)
        else:
            elements = np.asarray(np.char.mod("%d", array), dtype=object)
            element_nulls = np.zeros(array.shape, dtype=bool)
        if fits_null is not None:
            fits_mask = np.equal(array, fits_null)
            elements[fits_mask] = None
            element_nulls |= fits_mask
        text_elements = elements.astype(str)
        text_elements[element_nulls] = "NULL"
        rendered = np.full(array.shape[0], "{", dtype=str)
        for element_index in range(array.shape[1]):
            if element_index:
                rendered = np.char.add(rendered, ",")
            rendered = np.char.add(rendered, text_elements[:, element_index])
        return np.asarray(np.char.add(rendered, "}"), dtype=object)
    if array.ndim != 1:
        raise ValueError(f"scalar COPY source shape mismatch: {array.shape}")
    if target_type in {"real", "double precision"}:
        rendered = _format_float_values(array)
    elif target_type in {"smallint", "integer", "bigint"}:
        rendered = np.asarray(np.char.mod("%d", array), dtype=object)
    elif target_type == "boolean":
        rendered = np.asarray(np.where(array, "t", "f"), dtype=object)
    elif target_type == "text":
        if array.dtype.kind == "S":
            rendered = np.asarray(np.char.decode(array, "utf-8"), dtype=object)
        else:
            rendered = np.asarray(array.astype(str), dtype=object)
        if np.any(rendered == COPY_NULL_MARKER):
            raise ValueError("source text collides with configured COPY NULL marker")
    else:
        raise ValueError(f"unsupported scalar COPY type: {target_type}")
    if fits_null is not None:
        rendered[np.equal(array, fits_null)] = None
    return rendered


# =============================================================================
# Deterministic v1 fingerprint
# =============================================================================


def serialize_fingerprint(value: Mapping[str, Any]) -> Fingerprint:
    """Canonicalize schema/table ordering and hash compact UTF-8 JSON bytes."""
    canonical = {
        "database_owner": value["database_owner"],
        "schemas": sorted(value["schemas"], key=lambda item: item["name"]),
        "tables": sorted(
            value["tables"], key=lambda item: (item["schema"], item["table"])
        ),
    }
    content = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return Fingerprint(content=content, sha256=hashlib.sha256(content).hexdigest())


def require_fingerprint_identity(before: Fingerprint, after: Fingerprint) -> None:
    """Require byte-identical structured v1 content and SHA-256."""
    if before.content != after.content or before.sha256 != after.sha256:
        raise ValueError(
            f"v1 fingerprint changed: before={before.sha256}, after={after.sha256}"
        )


# =============================================================================
# Analyst role and handoff contracts
# =============================================================================


def role_statements(bootstrap_owner: str) -> tuple[str, ...]:
    """Return the exact non-password role and privilege SQL contract."""
    owner = quote_identifier(bootstrap_owner)
    analyst = quote_identifier(ANALYST_ROLE)
    target = quote_identifier(TARGET_DATABASE)
    source = quote_identifier("source")
    public_schema = quote_identifier("public")
    return (
        f"CREATE ROLE {analyst} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN",
        f"REVOKE ALL PRIVILEGES ON DATABASE {target} FROM PUBLIC",
        f"REVOKE ALL ON SCHEMA {source} FROM PUBLIC",
        f"REVOKE ALL ON SCHEMA {public_schema} FROM PUBLIC",
        f"GRANT CONNECT ON DATABASE {target} TO {analyst}",
        f"GRANT USAGE ON SCHEMA {source} TO {analyst}",
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {source} TO {analyst}",
        f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {source} "
        "REVOKE ALL ON TABLES FROM PUBLIC",
        f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {source} "
        f"GRANT SELECT ON TABLES TO {analyst}",
    )


def retained_role_reversal_statements(bootstrap_owner: str) -> tuple[str, ...]:
    """Revoke only Gate 3.7 grants before dropping a role from retained data."""
    owner = quote_identifier(bootstrap_owner)
    analyst = quote_identifier(ANALYST_ROLE)
    target = quote_identifier(TARGET_DATABASE)
    source = quote_identifier("source")
    return (
        f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {source} "
        f"REVOKE SELECT ON TABLES FROM {analyst}",
        f"REVOKE SELECT ON ALL TABLES IN SCHEMA {source} FROM {analyst}",
        f"REVOKE USAGE ON SCHEMA {source} FROM {analyst}",
        f"REVOKE CONNECT ON DATABASE {target} FROM {analyst}",
    )


def role_password_plan(role: str, analyst_secret: str) -> RolePasswordPlan:
    """Keep the password out of PostgreSQL utility SQL and client-visible text."""
    if role != ANALYST_ROLE:
        raise ValueError(f"fixed Gate 3.7 target role mismatch: {role!r}")
    if not re.fullmatch(r"[A-Za-z0-9_-]{48,}", analyst_secret):
        raise ValueError("analyst secret violates the shell-safe strength contract")
    setting = "cosmos2025_v11.analyst_password"
    create_sql = (
        f"CREATE ROLE {quote_identifier(role)} NOSUPERUSER NOCREATEDB "
        "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS LOGIN"
    )
    set_config_sql = f"SELECT pg_catalog.set_config('{setting}', %s, true)"
    apply_sql = (
        "DO $gate_3_7$ BEGIN "
        "EXECUTE pg_catalog.format('ALTER ROLE %I PASSWORD %L', "
        f"'{role}', pg_catalog.current_setting('{setting}')); "
        "END $gate_3_7$"
    )
    return RolePasswordPlan(
        create_sql=create_sql,
        set_config_sql=set_config_sql,
        set_config_parameters=(analyst_secret,),
        apply_sql=apply_sql,
    )


def analyst_verification_plan(
    authenticated_user: str, effective_user: str
) -> AnalystVerificationPlan:
    """Build the fixed secret-free admin-session impersonation contract."""
    if not authenticated_user or effective_user != ANALYST_ROLE:
        raise ValueError("analyst verification identity mismatch")
    return AnalystVerificationPlan(
        authenticated_user=authenticated_user,
        effective_user=effective_user,
        set_authorization_sql=(
            f"SET SESSION AUTHORIZATION {quote_identifier(effective_user)}"
        ),
        reset_authorization_sql="RESET SESSION AUTHORIZATION",
        direct_network_auth_exercised=False,
    )


def permission_matrix(bootstrap_owner: str) -> OrderedDict[str, MatrixOperation]:
    """Return the fixed analyst positive and adversarial permission matrix."""
    owner = quote_identifier(bootstrap_owner)
    return OrderedDict(
        (
            (
                "select",
                MatrixOperation(
                    'SELECT count(*) FROM "source"."photometry_primary"', True
                ),
            ),
            (
                "insert",
                MatrixOperation(
                    'INSERT INTO "source"."photometry_primary" DEFAULT VALUES',
                    False,
                ),
            ),
            (
                "update",
                MatrixOperation(
                    'UPDATE "source"."photometry_primary" SET "id" = "id" WHERE false',
                    False,
                ),
            ),
            (
                "delete",
                MatrixOperation(
                    'DELETE FROM "source"."photometry_primary" WHERE false', False
                ),
            ),
            (
                "create_schema",
                MatrixOperation('CREATE SCHEMA "gate_3_7_forbidden"', False),
            ),
            (
                "create_source_table",
                MatrixOperation(
                    'CREATE TABLE "source"."gate_3_7_forbidden" (id integer)',
                    False,
                ),
            ),
            (
                "create_public_table",
                MatrixOperation(
                    'CREATE TABLE "public"."gate_3_7_forbidden" (id integer)',
                    False,
                ),
            ),
            (
                "create_temp_table",
                MatrixOperation(
                    'CREATE TEMPORARY TABLE "gate_3_7_forbidden" (id integer)',
                    False,
                ),
            ),
            (
                "alter",
                MatrixOperation(
                    'ALTER TABLE "source"."photometry_primary" ADD COLUMN '
                    '"gate_3_7_forbidden" integer',
                    False,
                ),
            ),
            (
                "truncate",
                MatrixOperation('TRUNCATE "source"."photometry_primary"', False),
            ),
            (
                "grant",
                MatrixOperation(
                    f"GRANT {owner} TO {quote_identifier(ANALYST_ROLE)}", False
                ),
            ),
            (
                "set_admin_role",
                MatrixOperation(f"SET ROLE {owner}", False),
            ),
        )
    )


def generate_analyst_secret(length: int = 64) -> str:
    """Generate an in-memory shell-safe analyst credential."""
    if length < 48:
        raise ValueError("analyst secret must contain at least 48 characters")
    alphabet = string.ascii_letters + string.digits + "_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def handoff_values(
    *, host: str, port: int, analyst_secret: str
) -> OrderedDict[str, str]:
    """Build the exact ordered five-variable operator handoff."""
    return OrderedDict(
        (
            ("PGSQL01_HOST", host),
            ("PGSQL01_PORT", str(port)),
            ("PGSQL01_COSMOS2025_V11_DB", TARGET_DATABASE),
            ("PGSQL01_COSMOS2025_V11_USER", ANALYST_ROLE),
            ("PGSQL01_COSMOS2025_V11_PASSWORD", analyst_secret),
        )
    )


def write_handoff_exclusive(path: Path, values: Mapping[str, str]) -> None:
    """Create the exact handoff exclusively and reverse interrupted writes."""
    if tuple(values) != HANDOFF_NAMES:
        raise ValueError("handoff variable-name set/order mismatch")
    content = "".join(f"{name}={values[name]}\n" for name in HANDOFF_NAMES)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    created_identity = os.fstat(descriptor)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
            descriptor = -1
        try:
            observed = path.lstat()
            if (
                stat.S_ISREG(observed.st_mode)
                and not stat.S_ISLNK(observed.st_mode)
                and observed.st_dev == created_identity.st_dev
                and observed.st_ino == created_identity.st_ino
            ):
                path.unlink()
            if path.exists() or path.is_symlink():
                raise RuntimeError("interrupted handoff cleanup failed")
        except FileNotFoundError:
            pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def validate_handoff_file(path: Path) -> OrderedDict[str, str]:
    """Read and validate handoff metadata without emitting its values."""
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("handoff must have mode 0600")
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != len(HANDOFF_NAMES):
        raise ValueError("handoff must contain exactly five lines")
    parsed: OrderedDict[str, str] = OrderedDict()
    for line in lines:
        if "=" not in line:
            raise ValueError("handoff line has no assignment")
        name, value = line.split("=", 1)
        if name in parsed:
            raise ValueError("handoff contains a duplicate variable")
        parsed[name] = value
    if tuple(parsed) != HANDOFF_NAMES:
        raise ValueError("handoff variable-name set/order mismatch")
    if parsed["PGSQL01_COSMOS2025_V11_DB"] != TARGET_DATABASE:
        raise ValueError("handoff target database mismatch")
    if parsed["PGSQL01_COSMOS2025_V11_USER"] != ANALYST_ROLE:
        raise ValueError("handoff analyst role mismatch")
    if not parsed["PGSQL01_COSMOS2025_V11_PASSWORD"]:
        raise ValueError("handoff analyst secret is empty")
    return parsed


def public_summary(value: Any) -> Any:
    """Recursively remove secret-bearing keys before output serialization."""
    if isinstance(value, Mapping):
        return {
            key: public_summary(nested)
            for key, nested in value.items()
            if key not in SECRET_KEYS
            and "password" not in key.lower()
            and "secret" not in key.lower()
        }
    if isinstance(value, (list, tuple)):
        return [public_summary(item) for item in value]
    return value


def validate_role_observation(observed: RoleObservation) -> None:
    """Require the analyst's exact attributes, zero memberships, and zero ownership."""
    expected = RoleObservation(
        login=True,
        superuser=False,
        create_database=False,
        create_role=False,
        inherit=False,
        replication=False,
        bypass_rls=False,
        scram_credential_present=True,
        memberships=0,
        owned_objects=0,
    )
    if observed != expected:
        raise ValueError(f"analyst role contract mismatch: {observed!r}")


def validate_handoff_git_evidence(observed: HandoffGitEvidence) -> None:
    """Require ignored/untracked handoff state and no secret-bearing output."""
    expected = HandoffGitEvidence(
        ignored=True,
        tracked=False,
        secret_in_tracked=False,
        secret_in_staged=False,
        secret_in_captured_outputs=False,
    )
    if observed != expected:
        raise ValueError(f"handoff Git/secret contract mismatch: {observed!r}")


def execution_phases(mode: str) -> tuple[str, ...]:
    """Return the explicit phase boundary for create/load or read-only verification."""
    phases = {
        "create-load": (
            "final_preflight",
            "create_database",
            "execute_reviewed_ddl",
            "load_master_tables",
            "create_role",
            "verify_admin",
            "write_handoff",
            "verify_analyst",
            "verify_v1_fingerprint",
            "verify_handoff_git",
        ),
        "verify-only": (
            "read_handoff",
            "verify_admin",
            "verify_analyst",
            "verify_v1_fingerprint",
            "verify_handoff_git",
        ),
        "finalize-admin": (
            "validate_retained_load",
            "create_role",
            "verify_admin",
            "write_handoff",
            "verify_analyst",
            "verify_v1_fingerprint",
            "verify_handoff_git",
        ),
    }
    try:
        return phases[mode]
    except KeyError as exc:
        raise ValueError(f"unsupported execution mode: {mode!r}") from exc


def post_load_stage_marker(stage: str) -> str:
    """Return one fixed secret-free live success marker."""
    if stage not in POST_LOAD_SUCCESS_STAGES:
        raise ValueError("unsupported post-load stage")
    return f"stage_completed: {stage}"


def validate_table_load_evidence(observed: TableLoadEvidence) -> None:
    """Require exact source pin, committed count, and positive elapsed evidence."""
    valid = (
        observed.table in MASTER_TABLES
        and observed.source_rows == observed.loaded_rows
        and observed.declared_bytes == observed.observed_bytes
        and observed.declared_sha256 == observed.observed_sha256
        and re.fullmatch(r"[0-9a-f]{64}", observed.observed_sha256) is not None
        and observed.elapsed_seconds >= 0
        and observed.committed
    )
    if not valid:
        raise ValueError(f"table load evidence mismatch: {observed!r}")


def seal_completed_loads(loads: Sequence[TableLoadEvidence]) -> bool:
    """Cross the retained-data boundary only for seven ordered exact commits."""
    if tuple(item.table for item in loads) != MASTER_TABLES:
        raise ValueError("sealed load boundary mismatch")
    try:
        for item in loads:
            validate_table_load_evidence(item)
    except ValueError:
        raise ValueError("sealed load boundary mismatch") from None
    return True


def validate_id_alignment(
    *,
    rows: int,
    nonnull_ids: int,
    distinct_ids: int,
    primary_matches: int,
    fk_violations: int,
) -> None:
    """Require complete unique injected IDs matching primary at each ordinal."""
    if (nonnull_ids, distinct_ids, primary_matches, fk_violations) != (
        rows,
        rows,
        rows,
        0,
    ):
        raise ValueError("injected ID invariant mismatch")


def validate_array_observation(
    *,
    rows: int,
    wrong_shape: int,
    target_null_elements: int,
    expected_source_null_elements: int,
) -> None:
    """Require all non-NULL arrays shaped correctly and exact NULL element counts."""
    if (
        rows < 0
        or wrong_shape != 0
        or target_null_elements != expected_source_null_elements
    ):
        raise ValueError("array invariant mismatch")


# =============================================================================
# Live connection, fingerprint, and preflight helpers
# =============================================================================


def _connect(
    settings: Settings,
    database: str,
    *,
    user: str | None = None,
    password: str | None = None,
) -> psycopg.Connection:
    """Connect with keyword parameters so credentials never enter a URI or log."""
    if database not in {
        settings.maintenance_database,
        settings.baseline_database,
        settings.target_database,
    }:
        raise ValueError(f"refusing connection to unconfigured database: {database!r}")
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user if user is None else user,
        password=settings.password if password is None else password,
        dbname=database,
    )


def capture_v1_fingerprint(settings: Settings) -> Fingerprint:
    """Capture exact user schemas, tables, owners, and counts read-only."""
    with _connect(settings, settings.baseline_database) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        owner = connection.execute(
            """
            SELECT pg_catalog.pg_get_userbyid(datdba)
            FROM pg_catalog.pg_database
            WHERE datname = current_database()
            """
        ).fetchone()[0]
        schema_rows = connection.execute(
            """
            SELECT n.nspname, pg_catalog.pg_get_userbyid(n.nspowner)
            FROM pg_catalog.pg_namespace AS n
            WHERE n.nspname <> 'information_schema'
              AND n.nspname !~ '^pg_'
            ORDER BY n.nspname
            """
        ).fetchall()
        table_rows = connection.execute(
            """
            SELECT n.nspname, c.relname, pg_catalog.pg_get_userbyid(c.relowner)
            FROM pg_catalog.pg_class AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname <> 'information_schema'
              AND n.nspname !~ '^pg_'
            ORDER BY n.nspname, c.relname
            """
        ).fetchall()
        tables: list[dict[str, Any]] = []
        for schema_name, table_name, table_owner in table_rows:
            count = connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier(schema_name), sql.Identifier(table_name)
                )
            ).fetchone()[0]
            tables.append(
                {
                    "schema": schema_name,
                    "table": table_name,
                    "owner": table_owner,
                    "rows": count,
                }
            )
        connection.rollback()
    return serialize_fingerprint(
        {
            "database_owner": owner,
            "schemas": [
                {"name": name, "owner": schema_owner}
                for name, schema_owner in schema_rows
            ],
            "tables": tables,
        }
    )


def _probe_database_capacity(connection: psycopg.Connection) -> DatabaseCapacity:
    """Read byte capacity from the PostgreSQL server's current data volume."""
    connection.execute(
        "CREATE TEMP TABLE gate_3_7_capacity_probe(line text) ON COMMIT DROP"
    )
    connection.execute(
        "COPY gate_3_7_capacity_probe FROM PROGRAM "
        "'df -B1 --output=size,used,avail,pcent . | tail -1'"
    )
    output = connection.execute("SELECT line FROM gate_3_7_capacity_probe").fetchone()[
        0
    ]
    evidence = parse_database_capacity(output)
    connection.rollback()
    return evidence


def _database_role_inventory(
    connection: psycopg.Connection,
) -> tuple[set[str], set[str]]:
    """Read only the baseline/target database and target-role name boundary."""
    databases = {
        row[0]
        for row in connection.execute(
            "SELECT datname FROM pg_database WHERE datname = ANY(%s)",
            ([BASELINE_DATABASE, TARGET_DATABASE],),
        ).fetchall()
    }
    roles = {
        row[0]
        for row in connection.execute(
            "SELECT rolname FROM pg_roles WHERE rolname = %s", (ANALYST_ROLE,)
        ).fetchall()
    }
    return databases, roles


def _assert_live_absence(connection: psycopg.Connection, settings: Settings) -> None:
    """Recheck all three non-idempotent targets at the live maintenance boundary."""
    databases, roles = _database_role_inventory(connection)
    if BASELINE_DATABASE not in databases:
        raise ValueError("v1 baseline database is unexpectedly absent")
    assert_targets_absent(
        database_names=databases,
        role_names=roles,
        handoff_path=settings.handoff_path,
    )


def _read_dictionary(settings: Settings) -> list[dict[str, str]]:
    """Read and validate the sealed dictionary plus reviewed DDL identity."""
    rows = generate_schema_v11.read_dictionary(settings.dictionary_path)
    generate_schema_v11.build_schema_contract(rows)
    generate_schema_v11.write_or_check(rows, settings.ddl_path, check=True)
    return rows


def reviewed_ddl_payload(
    rows: Sequence[dict[str, str]], ddl_path: Path
) -> tuple[bytes, str]:
    """Return the single reviewed DDL buffer and its SHA-256 identity."""
    expected = generate_schema_v11.generate_sql(list(rows)).encode("utf-8")
    observed = ddl_path.read_bytes()
    if observed != expected:
        raise ValueError("generated SQL differs from sealed inputs")
    return observed, hashlib.sha256(observed).hexdigest()


def _manifest_contract(settings: Settings) -> verify_source_fidelity.ManifestContract:
    """Parse the exact two-root manifest boundary for per-table fresh pins."""
    config = yaml.safe_load(settings.config_path.read_text(encoding="utf-8"))
    expected = {
        str(
            Path(config["data_root"])
        ): verify_source_fidelity.EXPECTED_MANIFEST_ROOT_COUNTS[0],
        str(Path(config["specz"]["compilation_root"])): (
            verify_source_fidelity.EXPECTED_MANIFEST_ROOT_COUNTS[1]
        ),
    }
    return verify_source_fidelity.parse_manifest_contract(
        settings.manifest_path, expected
    )


def final_preflight(settings: Settings) -> dict[str, Any]:
    """Run fresh source, DDL, v1 fingerprint, capacity, and absence checks."""
    rows = _read_dictionary(settings)
    ddl_payload, ddl_sha256 = reviewed_ddl_payload(rows, settings.ddl_path)
    source_evidence = verify_source_fidelity.run_gate_3_5(settings.config_path)
    before = capture_v1_fingerprint(settings)
    with _connect(settings, settings.maintenance_database) as maintenance:
        version = maintenance.execute("SHOW server_version").fetchone()[0]
        capacity = _probe_database_capacity(maintenance)
        require_database_capacity(
            capacity,
            minimum_available_bytes=settings.minimum_database_free_bytes,
        )
        _assert_live_absence(maintenance, settings)
        maintenance.rollback()
    return {
        "dictionary_rows": len(rows),
        "ddl_payload": ddl_payload,
        "ddl_sha256": ddl_sha256,
        "source_integrity_status": source_evidence["status"],
        "source_integrity_inputs": source_evidence["consumed_manifest_input_count"],
        "v1_fingerprint": before,
        "v1_table_count": len(json.loads(before.content)["tables"]),
        "postgresql_version": version,
        "capacity": capacity,
    }


# =============================================================================
# Transactional master-table load
# =============================================================================


def _table_dictionary_rows(
    rows: Sequence[dict[str, str]], table: str
) -> list[dict[str, str]]:
    """Select one master table in sealed CSV order and validate its source path."""
    selected = [row for row in rows if row["target_table"] == table]
    if not selected:
        raise ValueError(f"missing dictionary rows for {table}")
    sources = {
        row["source_file"]
        for row in selected
        if row["column_origin"] == "source_native"
    }
    if len(sources) != 1:
        raise ValueError(f"master source-file boundary mismatch for {table}")
    return selected


def _fits_nulls(hdu: fits.BinTableHDU) -> dict[str, Any]:
    """Return only declared FITS TNULL values keyed by exact source name."""
    return {
        column.name: column.null for column in hdu.columns if column.null is not None
    }


def _serialize_table_chunk(
    table_rows: Sequence[dict[str, str]],
    *,
    columns: Mapping[str, np.ndarray],
    fits_nulls: Mapping[str, Any],
    start: int,
    stop: int,
    primary_ids: np.ndarray,
) -> bytes:
    """Build one bounded columnar CSV frame in exact dictionary order."""
    formatted: OrderedDict[str, Any] = OrderedDict()
    for row in table_rows:
        origin = row["column_origin"]
        target = row["target_identifier"]
        if origin == "source_native":
            source = row["source_column"]
            formatted[target] = format_native_chunk(
                row, columns[source][start:stop], fits_null=fits_nulls.get(source)
            )
        elif origin == "source_row_metadata":
            formatted[target] = np.arange(start, stop, dtype=np.int64)
        elif origin == "id_injected":
            formatted[target] = primary_ids[start:stop]
        else:
            raise ValueError(f"unsupported dictionary column origin: {origin!r}")
    frame = pd.DataFrame(
        formatted, columns=[row["target_identifier"] for row in table_rows]
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
    return buffer.getvalue().encode("utf-8")


def _load_master_table(
    connection: psycopg.Connection,
    settings: Settings,
    rows: Sequence[dict[str, str]],
    table: str,
    manifest: verify_source_fidelity.ManifestContract,
    primary_ids: np.ndarray | None,
) -> tuple[TableLoadEvidence, np.ndarray]:
    """Fresh-pin and transactionally stream one complete standalone FITS table."""
    table_rows = _table_dictionary_rows(rows, table)
    source_path = Path(
        next(
            row["source_file"]
            for row in table_rows
            if row["column_origin"] == "source_native"
        )
    )
    pin = verify_source_fidelity.pin_manifest_input(table, source_path, manifest)
    started = time.monotonic()
    committed = False
    source_rows = 0
    ids = primary_ids
    try:
        with fits.open(source_path, memmap=True) as hdul:
            table_hdus = [hdu for hdu in hdul if isinstance(hdu, fits.BinTableHDU)]
            if len(table_hdus) != 1:
                raise ValueError(f"expected one binary table in {source_path}")
            hdu = table_hdus[0]
            data = hdu.data
            source_rows = len(data)
            columns = {
                row["source_column"]: data[row["source_column"]]
                for row in table_rows
                if row["column_origin"] == "source_native"
            }
            nulls = _fits_nulls(hdu)
            if table == "photometry_primary":
                ids = np.asarray(columns["id"], dtype=np.int64).copy()
            if ids is None or len(ids) != source_rows:
                raise ValueError(f"primary-ID population mismatch before {table}")
            statement = copy_statement(
                table, [row["target_identifier"] for row in table_rows]
            )
            with connection.cursor().copy(statement) as copy:
                for start in range(0, source_rows, settings.copy_batch_rows):
                    stop = min(start + settings.copy_batch_rows, source_rows)
                    copy.write(
                        _serialize_table_chunk(
                            table_rows,
                            columns=columns,
                            fits_nulls=nulls,
                            start=start,
                            stop=stop,
                            primary_ids=ids,
                        )
                    )
        loaded_rows = connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(table)
            )
        ).fetchone()[0]
        if loaded_rows != source_rows:
            raise ValueError(
                f"transactional table count mismatch for {table}: "
                f"source={source_rows}, target={loaded_rows}"
            )
        connection.commit()
        committed = True
    except Exception:
        connection.rollback()
        raise
    evidence = TableLoadEvidence(
        table=table,
        source_rows=source_rows,
        loaded_rows=source_rows,
        declared_bytes=pin.declared_bytes,
        observed_bytes=pin.observed_bytes,
        declared_sha256=pin.declared_sha256,
        observed_sha256=pin.observed_sha256,
        elapsed_seconds=time.monotonic() - started,
        committed=committed,
    )
    validate_table_load_evidence(evidence)
    return evidence, ids


# =============================================================================
# Target catalog and lossless-value verification
# =============================================================================


def _profile_null_count(row: Mapping[str, str]) -> int:
    """Return the sealed FITS-mask plus NaN count for one native field."""
    profile = json.loads(row["profile_json"])
    return sum(
        int(item.get("fits_mask_count", 0)) + int(item.get("nan_count", 0))
        for item in profile["profiles"]
    )


def _verify_null_counts(
    connection: psycopg.Connection,
    table: str,
    table_rows: Sequence[dict[str, str]],
) -> int:
    """Compare scalar NULL populations to sealed source mask/NaN profiles."""
    scalar_rows = [row for row in table_rows if not row["target_type"].endswith("[]")]
    if not scalar_rows:
        return 0
    expressions = [
        sql.SQL("count(*) FILTER (WHERE {} IS NULL)").format(
            sql.Identifier(row["target_identifier"])
        )
        for row in scalar_rows
    ]
    statement = sql.SQL("SELECT {} FROM {}.{}").format(
        sql.SQL(", ").join(expressions),
        sql.Identifier("source"),
        sql.Identifier(table),
    )
    observed = connection.execute(statement).fetchone()
    expected = tuple(
        _profile_null_count(row) if row["column_origin"] == "source_native" else 0
        for row in scalar_rows
    )
    if tuple(observed) != expected:
        mismatch = next(
            index
            for index, pair in enumerate(zip(observed, expected, strict=True))
            if pair[0] != pair[1]
        )
        raise ValueError(
            f"target NULL count mismatch for {table}."
            f"{scalar_rows[mismatch]['target_identifier']}"
        )
    return sum(expected)


def _verify_arrays(
    connection: psycopg.Connection,
    table: str,
    table_rows: Sequence[dict[str, str]],
    row_count: int,
) -> dict[str, int]:
    """Verify all loaded arrays over every row and exact element NULL totals."""
    arrays = [row for row in table_rows if row["target_type"].endswith("[]")]
    if not arrays:
        return {"columns": 0, "null_elements": 0}
    expressions: list[sql.Composed] = []
    for row in arrays:
        column = sql.Identifier(row["target_identifier"])
        expressions.extend(
            (
                sql.SQL(
                    "count(*) FILTER (WHERE {0} IS NOT NULL AND "
                    "(array_ndims({0}) <> 1 OR cardinality({0}) <> {1}))"
                ).format(column, sql.Literal(int(row["element_count"]))),
                sql.SQL(
                    "coalesce(sum(cardinality({0}) - "
                    "cardinality(array_remove({0}, NULL))), 0)"
                ).format(column),
            )
        )
    observed = connection.execute(
        sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(expressions),
            sql.Identifier("source"),
            sql.Identifier(table),
        )
    ).fetchone()
    total_nulls = 0
    for index, row in enumerate(arrays):
        expected_nulls = _profile_null_count(row)
        wrong_shape = observed[index * 2]
        target_nulls = observed[index * 2 + 1]
        validate_array_observation(
            rows=row_count,
            wrong_shape=wrong_shape,
            target_null_elements=target_nulls,
            expected_source_null_elements=expected_nulls,
        )
        total_nulls += expected_nulls
    return {"columns": len(arrays), "null_elements": total_nulls}


def _documented_sentinel_expectations(
    row: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Recover exact documented-sentinel counts from the sealed source profile."""
    values = json.loads(row["documented_sentinel_values_json"])
    if not values:
        return []
    profile = json.loads(row["profile_json"])
    expectations: list[dict[str, Any]] = []
    for value in values:
        for scalar in profile["profiles"]:
            count = next(
                (
                    int(item["count"])
                    for item in scalar["top_values"]
                    if item["value"] == value
                ),
                None,
            )
            if count is None:
                raise ValueError("documented sentinel count absent from sealed profile")
            expectations.append(
                {"value": value, "count": count, "index": scalar["index"]}
            )
    return expectations


def _verify_sentinels(
    connection: psycopg.Connection,
    table: str,
    table_rows: Sequence[dict[str, str]],
) -> int:
    """Require all documented/candidate finite sentinels to remain non-NULL."""
    checks: list[tuple[sql.Composed, Any, int]] = []
    for row in table_rows:
        if row["column_origin"] != "source_native":
            continue
        observations = json.loads(row["candidate_sentinel_values_json"])
        observations.extend(_documented_sentinel_expectations(row))
        for item in observations:
            column = sql.Identifier(row["target_identifier"])
            if item["index"] is None:
                expression = sql.SQL("count(*) FILTER (WHERE {} = %s)").format(column)
            else:
                expression = sql.SQL("count(*) FILTER (WHERE {}[{}] = %s)").format(
                    column, sql.Literal(int(item["index"]) + 1)
                )
            checks.append((expression, item["value"], int(item["count"])))
    if not checks:
        return 0
    observed = connection.execute(
        sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(item[0] for item in checks),
            sql.Identifier("source"),
            sql.Identifier(table),
        ),
        tuple(item[1] for item in checks),
    ).fetchone()
    expected = tuple(item[2] for item in checks)
    if tuple(observed) != expected:
        raise ValueError(f"finite sentinel preservation mismatch for {table}")
    return len(checks)


def _role_observation(connection: psycopg.Connection) -> RoleObservation:
    """Inspect analyst attributes, memberships, and target ownership."""
    attributes = connection.execute(
        """
        SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolinherit,
               rolreplication, rolbypassrls,
               rolpassword IS NOT NULL
                 AND rolpassword LIKE 'SCRAM-SHA-256$%%'
        FROM pg_authid WHERE rolname = %s
        """,
        (ANALYST_ROLE,),
    ).fetchone()
    if attributes is None:
        raise ValueError("analyst role is absent")
    memberships = connection.execute(
        """
        SELECT count(*)
        FROM pg_auth_members AS m
        JOIN pg_roles AS member_role ON member_role.oid = m.member
        JOIN pg_roles AS granted_role ON granted_role.oid = m.roleid
        WHERE member_role.rolname = %s OR granted_role.rolname = %s
        """,
        (ANALYST_ROLE, ANALYST_ROLE),
    ).fetchone()[0]
    owned = connection.execute(
        """
        SELECT
          (SELECT count(*) FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba
           WHERE r.rolname=%s)
          +
          (SELECT count(*) FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
           WHERE r.rolname=%s)
          +
          (SELECT count(*) FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner
           WHERE r.rolname=%s)
        """,
        (ANALYST_ROLE, ANALYST_ROLE, ANALYST_ROLE),
    ).fetchone()[0]
    return RoleObservation(*attributes, memberships=memberships, owned_objects=owned)


def verify_target_admin(
    settings: Settings,
    rows: Sequence[dict[str, str]],
    *,
    exercise_wrong_array: bool,
) -> dict[str, Any]:
    """Run complete owner/count/column/key/array/sentinel/role verification."""
    expected_counts: dict[str, int] = {}
    null_totals: dict[str, int] = {}
    array_totals: dict[str, dict[str, int]] = {}
    sentinel_checks: dict[str, int] = {}
    id_tables = 0
    with _connect(settings, settings.target_database) as connection:
        structure = verify_schema_v11_scratch._verify_objects_and_columns(
            connection, list(rows)
        )
        owner_row = connection.execute(
            """
            SELECT
              (SELECT pg_get_userbyid(datdba) FROM pg_database
               WHERE datname=current_database()),
              (SELECT pg_get_userbyid(nspowner) FROM pg_namespace
               WHERE nspname='source'),
              (SELECT pg_get_userbyid(nspowner) FROM pg_namespace
               WHERE nspname='public'),
              (SELECT count(*) FROM pg_class c
               JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='source' AND c.relkind='r'
                 AND pg_get_userbyid(c.relowner) <> %s),
              (SELECT count(*) FROM pg_class c
               JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='source' AND c.relkind='r'
                 AND pg_get_userbyid(c.relowner) = %s)
            """,
            (settings.user, ANALYST_ROLE),
        ).fetchone()
        if (
            owner_row[0] != settings.user
            or owner_row[1] != settings.user
            or owner_row[2] == ANALYST_ROLE
            or owner_row[3] != 0
            or owner_row[4] != 0
        ):
            raise ValueError("database/schema/table ownership contract mismatch")
        for table in MASTER_TABLES:
            table_rows = _table_dictionary_rows(rows, table)
            source_rows = json.loads(table_rows[0]["profile_json"])["profiles"][0][
                "row_count"
            ]
            count = connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
            if count != source_rows:
                raise ValueError(
                    f"master target/source count mismatch for {table}: {count}/{source_rows}"
                )
            expected_counts[table] = count
            stats = connection.execute(
                sql.SQL(
                    "SELECT count(*), count(DISTINCT source_row), min(source_row), "
                    "max(source_row), count(*) FILTER (WHERE source_row IS NULL) "
                    "FROM {}.{}"
                ).format(sql.Identifier("source"), sql.Identifier(table))
            ).fetchone()
            validate_source_row_stats(stats, expected_rows=count)
            null_totals[table] = _verify_null_counts(connection, table, table_rows)
            array_totals[table] = _verify_arrays(connection, table, table_rows, count)
            sentinel_checks[table] = _verify_sentinels(connection, table, table_rows)
            if table == "photometry_primary":
                primary_id_stats = connection.execute(
                    """
                    SELECT count(*), count(id), count(DISTINCT id)
                    FROM source.photometry_primary
                    """
                ).fetchone()
                validate_id_alignment(
                    rows=primary_id_stats[0],
                    nonnull_ids=primary_id_stats[1],
                    distinct_ids=primary_id_stats[2],
                    primary_matches=primary_id_stats[0],
                    fk_violations=0,
                )
            else:
                alignment = connection.execute(
                    sql.SQL(
                        "SELECT count(*), count(e.id), count(DISTINCT e.id), "
                        "count(p.id), count(*) FILTER (WHERE p.id IS NULL) "
                        "FROM {}.{} AS e LEFT JOIN {}.{} AS p "
                        "ON p.source_row=e.source_row AND p.id=e.id"
                    ).format(
                        sql.Identifier("source"),
                        sql.Identifier(table),
                        sql.Identifier("source"),
                        sql.Identifier("photometry_primary"),
                    )
                ).fetchone()
                validate_id_alignment(
                    rows=alignment[0],
                    nonnull_ids=alignment[1],
                    distinct_ids=alignment[2],
                    primary_matches=alignment[3],
                    fk_violations=alignment[4],
                )
                id_tables += 1
        unloaded = {
            table: connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
            for table in UNLOADED_TABLES
        }
        validate_unloaded_counts(unloaded)
        role = _role_observation(connection)
        validate_role_observation(role)
        wrong_array = "not_exercised"
        if exercise_wrong_array:
            wrong_array = verify_schema_v11_scratch._wrong_array_mutation(
                connection, list(rows)
            )
        size = connection.execute(
            "SELECT pg_database_size(current_database())"
        ).fetchone()[0]
        connection.rollback()
    if sum(item["columns"] for item in array_totals.values()) != 166:
        raise ValueError("loaded array column boundary mismatch")
    return {
        "structure": structure,
        "counts": expected_counts,
        "unloaded_counts": unloaded,
        "source_row_tables": len(expected_counts),
        "injected_id_tables": id_tables,
        "null_counts": null_totals,
        "arrays": array_totals,
        "sentinel_checks": sentinel_checks,
        "wrong_array_rejected_by": wrong_array,
        "database_size_bytes": size,
        "owners": {
            "database": owner_row[0],
            "source_schema": owner_row[1],
            "public_schema": owner_row[2],
            "source_tables": owner_row[1],
            "analyst_owned": 0,
        },
        "analyst_role": asdict(role),
    }


# =============================================================================
# Analyst matrix, default privileges, and handoff evidence
# =============================================================================


@contextmanager
def _impersonated_analyst(
    settings: Settings,
) -> Iterator[psycopg.Connection]:
    """Use the allowed admin connection while executing as the analyst role."""
    with _connect(settings, settings.target_database) as connection:
        authenticated = connection.execute("SELECT current_user").fetchone()[0]
        if authenticated != settings.user:
            raise ValueError("analyst verification admin identity mismatch")
        plan = analyst_verification_plan(authenticated, ANALYST_ROLE)
        connection.execute(plan.set_authorization_sql)
        connection.commit()
        observed = connection.execute("SELECT session_user, current_user").fetchone()
        if observed != (ANALYST_ROLE, ANALYST_ROLE):
            raise ValueError("analyst session authorization mismatch")
        try:
            yield connection
        finally:
            connection.rollback()
            connection.execute(plan.reset_authorization_sql)
            connection.commit()
            restored = connection.execute(
                "SELECT session_user, current_user"
            ).fetchone()
            connection.rollback()
            if restored != (settings.user, settings.user):
                raise RuntimeError("admin session authorization reset failed")


def _target_snapshot(connection: psycopg.Connection) -> tuple[int, tuple[str, ...]]:
    """Capture total master rows and exact source object names around a matrix."""
    total = sum(
        connection.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("source"), sql.Identifier(table)
            )
        ).fetchone()[0]
        for table in MASTER_TABLES
    )
    objects = tuple(
        row[0]
        for row in connection.execute(
            """
            SELECT c.relname FROM pg_class c
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='source' AND c.relkind='r'
            ORDER BY c.relname
            """
        ).fetchall()
    )
    return total, objects


def verify_analyst_matrix(
    settings: Settings, *, expected_primary_rows: int = 784_016
) -> dict[str, Any]:
    """Impersonate analyst and require one positive plus eleven denied operations."""
    if expected_primary_rows < 0:
        raise ValueError("analyst expected row count is invalid")
    results: OrderedDict[str, str] = OrderedDict()
    with _impersonated_analyst(settings) as connection:
        before = _target_snapshot(connection)
        connection.rollback()
        for name, operation in permission_matrix(settings.user).items():
            try:
                cursor = connection.execute(operation.statement)
                if not operation.allowed:
                    connection.rollback()
                    raise ValueError(f"analyst operation unexpectedly allowed: {name}")
                count = cursor.fetchone()[0]
                if count != expected_primary_rows:
                    raise ValueError(f"analyst SELECT count mismatch: {count}")
                results[name] = "allowed"
                connection.rollback()
            except psycopg.errors.InsufficientPrivilege as exc:
                connection.rollback()
                if operation.allowed or exc.sqlstate != "42501":
                    raise ValueError(
                        f"analyst operation had unintended privilege result: {name}"
                    ) from exc
                results[name] = "denied_42501"
        after = _target_snapshot(connection)
        connection.rollback()
    if after != before:
        raise ValueError("analyst permission matrix changed target objects or rows")
    return {
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
        "positive": sum(value == "allowed" for value in results.values()),
        "negative": sum(value == "denied_42501" for value in results.values()),
        "results": results,
        "unchanged": True,
    }


def verify_default_privileges(settings: Settings) -> dict[str, Any]:
    """Create one owner proof table, verify SELECT/no-write, and remove it."""
    proof = "gate_3_7_default_privilege_proof"
    if not re.fullmatch(r"gate_3_7_default_privilege_proof", proof):
        raise ValueError("refusing unsafe default-privilege proof name")
    created = False
    with _connect(settings, settings.target_database) as owner:
        exists = owner.execute(
            """
            SELECT EXISTS (
              SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
              WHERE n.nspname='source' AND c.relname=%s
            )
            """,
            (proof,),
        ).fetchone()[0]
        if exists:
            raise ValueError("default-privilege proof object already exists")
        try:
            owner.execute(
                sql.SQL("CREATE TABLE {}.{} (id integer)").format(
                    sql.Identifier("source"), sql.Identifier(proof)
                )
            )
            owner.execute(
                sql.SQL("INSERT INTO {}.{} VALUES (1)").format(
                    sql.Identifier("source"), sql.Identifier(proof)
                )
            )
            owner.commit()
            created = True
            with _impersonated_analyst(settings) as analyst:
                selected = analyst.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier("source"), sql.Identifier(proof)
                    )
                ).fetchone()[0]
                analyst.rollback()
                try:
                    analyst.execute(
                        sql.SQL("INSERT INTO {}.{} VALUES (2)").format(
                            sql.Identifier("source"), sql.Identifier(proof)
                        )
                    )
                except psycopg.errors.InsufficientPrivilege as exc:
                    analyst.rollback()
                    if exc.sqlstate != "42501":
                        raise
                else:
                    analyst.rollback()
                    raise ValueError("default privileges granted analyst write")
                if selected != 1:
                    raise ValueError("default privileges proof SELECT mismatch")
        finally:
            if created:
                owner.execute(
                    sql.SQL("DROP TABLE {}.{}").format(
                        sql.Identifier("source"), sql.Identifier(proof)
                    )
                )
                owner.commit()
                created = False
            remaining = owner.execute(
                """
                SELECT count(*) FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='source' AND c.relname=%s
                """,
                (proof,),
            ).fetchone()[0]
            owner.rollback()
            if remaining:
                raise ValueError("default-privilege proof cleanup failed")
    return {
        "transport": "admin_session_authorization",
        "direct_network_auth_exercised": False,
        "select_allowed": True,
        "write_denied_42501": True,
        "remaining": 0,
    }


def _git_run(
    settings: Settings, arguments: Sequence[str]
) -> subprocess.CompletedProcess:
    """Run one fixed Git inspection without shell interpolation."""
    return subprocess.run(
        ["git", *arguments],
        cwd=settings.repo_root,
        capture_output=True,
        check=False,
    )


def verify_handoff_git(
    settings: Settings, *, analyst_secret: str, captured_outputs: Sequence[bytes] = ()
) -> HandoffGitEvidence:
    """Verify ignored/untracked state and scan tracked/staged/output bytes in-process."""
    relative = settings.handoff_path.relative_to(settings.repo_root)
    ignore = _git_run(settings, ["check-ignore", "-v", "--", str(relative)])
    tracked_exact = _git_run(
        settings, ["ls-files", "--error-unmatch", "--", str(relative)]
    )
    tracked_list = _git_run(settings, ["ls-files", "-z"])
    staged = _git_run(settings, ["diff", "--cached", "--binary"])
    status = _git_run(settings, ["status", "--porcelain=v1"])
    if tracked_list.returncode != 0 or staged.returncode != 0 or status.returncode != 0:
        raise ValueError("Git handoff inspection command failed")
    secret_bytes = analyst_secret.encode("utf-8")
    secret_in_tracked = False
    for path_bytes in tracked_list.stdout.split(b"\0"):
        if not path_bytes:
            continue
        tracked_path = settings.repo_root / os.fsdecode(path_bytes)
        if tracked_path.is_file() and secret_bytes in tracked_path.read_bytes():
            secret_in_tracked = True
            break
    command_outputs = (
        ignore.stdout,
        ignore.stderr,
        tracked_exact.stdout,
        tracked_exact.stderr,
        status.stdout,
        status.stderr,
        *captured_outputs,
    )
    evidence = HandoffGitEvidence(
        ignored=ignore.returncode == 0,
        tracked=tracked_exact.returncode == 0,
        secret_in_tracked=secret_in_tracked,
        secret_in_staged=secret_bytes in staged.stdout or secret_bytes in staged.stderr,
        secret_in_captured_outputs=any(
            secret_bytes in output for output in command_outputs
        ),
    )
    validate_handoff_git_evidence(evidence)
    return evidence


def read_handoff_for_verification(settings: Settings) -> OrderedDict[str, str]:
    """Read the exact configured ignored handoff without printing its content."""
    if (
        settings.handoff_path
        != settings.repo_root / "internal-files/cosmos2025-v11.env"
    ):
        raise ValueError("fixed Gate 3.7 target handoff path mismatch")
    values = validate_handoff_file(settings.handoff_path)
    if values["PGSQL01_HOST"] != settings.host:
        raise ValueError("handoff host mismatch")
    if values["PGSQL01_PORT"] != str(settings.port):
        raise ValueError("handoff port mismatch")
    if values["PGSQL01_COSMOS2025_V11_PASSWORD"] == settings.password:
        raise ValueError("analyst secret equals admin credential")
    return values


def _verify_privilege_contract(connection: psycopg.Connection) -> dict[str, Any]:
    """Require exact analyst database/schema/current-table capabilities."""
    database_privileges = connection.execute(
        """
        SELECT has_database_privilege(%s, current_database(), 'CONNECT'),
               has_database_privilege(%s, current_database(), 'CREATE'),
               has_database_privilege(%s, current_database(), 'TEMPORARY')
        """,
        (ANALYST_ROLE, ANALYST_ROLE, ANALYST_ROLE),
    ).fetchone()
    schema_privileges = connection.execute(
        """
        SELECT has_schema_privilege(%s, 'source', 'USAGE'),
               has_schema_privilege(%s, 'source', 'CREATE'),
               has_schema_privilege(%s, 'public', 'USAGE'),
               has_schema_privilege(%s, 'public', 'CREATE')
        """,
        (ANALYST_ROLE,) * 4,
    ).fetchone()
    table_privileges = connection.execute(
        """
        SELECT bool_and(has_table_privilege(%s, c.oid, 'SELECT')),
               bool_or(
                 has_table_privilege(%s, c.oid, 'INSERT') OR
                 has_table_privilege(%s, c.oid, 'UPDATE') OR
                 has_table_privilege(%s, c.oid, 'DELETE') OR
                 has_table_privilege(%s, c.oid, 'TRUNCATE') OR
                 has_table_privilege(%s, c.oid, 'REFERENCES') OR
                 has_table_privilege(%s, c.oid, 'TRIGGER')
               )
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='source' AND c.relkind='r'
        """,
        (ANALYST_ROLE,) * 7,
    ).fetchone()
    public_database = connection.execute(
        """
        SELECT count(*) FROM pg_database d,
             LATERAL aclexplode(coalesce(d.datacl, acldefault('d', d.datdba))) a
        WHERE d.datname=current_database() AND a.grantee=0
        """
    ).fetchone()[0]
    public_schemas = connection.execute(
        """
        SELECT count(*) FROM pg_namespace n,
             LATERAL aclexplode(coalesce(n.nspacl, acldefault('n', n.nspowner))) a
        WHERE n.nspname IN ('source','public') AND a.grantee=0
        """
    ).fetchone()[0]
    if (
        tuple(database_privileges) != (True, False, False)
        or tuple(schema_privileges) != (True, False, False, False)
        or tuple(table_privileges) != (True, False)
        or public_database != 0
        or public_schemas != 0
    ):
        raise ValueError("analyst/public privilege contract mismatch")
    return {
        "database": {"connect": True, "create": False, "temporary": False},
        "source_schema": {"usage": True, "create": False},
        "public_schema": {"usage": False, "create": False},
        "current_tables": {"select": True, "write_or_ddl": False},
        "public_database_acl_entries": 0,
        "public_schema_acl_entries": 0,
    }


def _create_analyst_role(
    connection: psycopg.Connection, settings: Settings, *, analyst_secret: str
) -> None:
    """Create the fixed analyst login and exact grants using an in-memory password."""
    plan = role_password_plan(ANALYST_ROLE, analyst_secret)
    connection.execute(plan.create_sql)
    connection.execute(plan.set_config_sql, plan.set_config_parameters)
    connection.execute(plan.apply_sql)
    for statement in role_statements(settings.user)[1:]:
        connection.execute(statement)
    connection.commit()


# =============================================================================
# Guarded reversal and complete lifecycle
# =============================================================================


def cleanup_created_resources(
    settings: Settings, created: CreatedResources
) -> tuple[str, ...]:
    """Reverse only exact resources marked as created by the current process."""
    completed: list[str] = []
    if created.handoff:
        validate_cleanup_target(
            "handoff",
            str(settings.handoff_path),
            expected_handoff=settings.handoff_path,
        )
        if not settings.handoff_path.exists():
            raise RuntimeError("handoff cleanup failed: created file is absent")
        metadata = settings.handoff_path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError("handoff cleanup failed: target is not a regular file")
        settings.handoff_path.unlink()
        if settings.handoff_path.exists():
            raise RuntimeError("handoff cleanup failed: file remains")
        completed.append("handoff")
    if created.role and not created.database:
        with _connect(settings, settings.target_database) as target:
            for statement in retained_role_reversal_statements(settings.user):
                target.execute(statement)
            target.commit()
    with _connect(settings, settings.maintenance_database) as maintenance:
        maintenance.autocommit = True
        if created.database:
            validate_cleanup_target("database", TARGET_DATABASE)
            present = maintenance.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=%s)",
                (TARGET_DATABASE,),
            ).fetchone()[0]
            if not present:
                raise RuntimeError("database cleanup failed: created target is absent")
            maintenance.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname=%s AND pid <> pg_backend_pid()",
                (TARGET_DATABASE,),
            )
            maintenance.execute(
                sql.SQL("DROP DATABASE {}").format(sql.Identifier(TARGET_DATABASE))
            )
            completed.append("database")
        if created.role:
            validate_cleanup_target("role", ANALYST_ROLE)
            present = maintenance.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)",
                (ANALYST_ROLE,),
            ).fetchone()[0]
            if not present:
                raise RuntimeError("role cleanup failed: created target is absent")
            maintenance.execute(
                sql.SQL("DROP ROLE {}").format(sql.Identifier(ANALYST_ROLE))
            )
            completed.append("role")
        databases, roles = _database_role_inventory(maintenance)
        if created.database and TARGET_DATABASE in databases:
            raise RuntimeError("database cleanup failed: target remains")
        if created.role and ANALYST_ROLE in roles:
            raise RuntimeError("role cleanup failed: target remains")
    return tuple(completed)


def _safe_exception_metadata(error: BaseException) -> tuple[str, str]:
    """Return identifier-only exception metadata without inspecting its message."""
    error_class = type(error).__name__
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", error_class):
        error_class = "Exception"
    try:
        candidate = getattr(error, "sqlstate", None)
    except BaseException:
        candidate = None
    sqlstate = candidate if isinstance(candidate, str) else "none"
    if not re.fullmatch(r"[0-9A-Z]{5}", sqlstate):
        sqlstate = "none"
    return error_class, sqlstate


def build_lifecycle_failure_after_cleanup(
    settings: Settings,
    created: CreatedResources,
    *,
    stage: str,
    error: BaseException,
    loads_sealed: bool = False,
) -> LifecycleFailure:
    """Clean exact owned resources and build message-free staged failure evidence."""
    if stage not in LIFECYCLE_STAGES:
        stage = "unknown"
    retain_database = loads_sealed and stage in POST_SEAL_FAILURE_STAGES
    cleanup_created = replace(created, database=False) if retain_database else created
    retained_resources = ("database",) if retain_database else ()
    retained_summary = ",".join(retained_resources) or "none"
    try:
        reversed_resources = cleanup_created_resources(settings, cleanup_created)
    except BaseException as cleanup_error:
        error_class, sqlstate = _safe_exception_metadata(cleanup_error)
        return LifecycleFailure(
            "Gate 3.7 failed: stage=cleanup "
            f"exception={error_class} sqlstate={sqlstate} "
            f"cleanup_failed=true original_stage={stage} "
            f"retained={retained_summary}"
        )
    allowed = {"database", "role", "handoff"}
    if any(item not in allowed for item in reversed_resources):
        return LifecycleFailure(
            "Gate 3.7 failed: stage=cleanup exception=RuntimeError "
            f"sqlstate=none cleanup_failed=true original_stage={stage} "
            f"retained={retained_summary}"
        )
    error_class, sqlstate = _safe_exception_metadata(error)
    reversed_summary = ",".join(reversed_resources) or "none"
    return LifecycleFailure(
        f"Gate 3.7 failed: stage={stage} exception={error_class} "
        f"sqlstate={sqlstate} reversed={reversed_summary} "
        f"retained={retained_summary}"
    )


def _assert_finalize_admin_live_boundary(settings: Settings) -> None:
    """Recheck exact retained/absent resources before admin-only mutation."""
    with _connect(settings, settings.maintenance_database) as maintenance:
        databases, roles = _database_role_inventory(maintenance)
        assert_finalize_admin_targets(
            database_names=databases,
            role_names=roles,
            handoff_path=settings.handoff_path,
        )
        maintenance.rollback()


def expected_retained_column_contract(
    rows: Sequence[dict[str, str]],
) -> tuple[tuple[str, str, bool], ...]:
    """Return exact source-column nullability in catalog inspection order."""
    schema = generate_schema_v11.build_schema_contract(list(rows))
    expected: list[tuple[str, int, str, bool]] = []
    for table, columns in schema.items():
        for ordinal, column in enumerate(columns, start=1):
            required = generate_schema_v11._required_mirror_column(table, column.name)
            expected.append((table, ordinal, column.name, required))
    for ordinal, field in enumerate(generate_schema_v11.PROVENANCE_CONTRACT, start=1):
        expected.append(("provenance", ordinal, field.name, not field.nullable))
    return tuple(
        (table, column, required)
        for table, _ordinal, column, required in sorted(expected)
    )


def _normalize_check_expression(expression: str) -> str:
    """Normalize only PostgreSQL's harmless rendering of reviewed checks."""
    without_text_casts = expression.replace("::text", "")
    without_safe_quotes = re.sub(r'"([a-z_][a-z0-9_]*)"', r"\1", without_text_casts)
    normalized = re.sub(r"\s+", " ", without_safe_quotes).strip()
    if " OR (array_ndims(" in normalized and normalized.endswith(")"):
        normalized = normalized.replace(" OR (array_ndims(", " OR array_ndims(", 1)
        normalized = normalized[:-1]
    return normalized


def expected_retained_constraint_contract(
    rows: Sequence[dict[str, str]],
) -> tuple[
    tuple[
        str,
        str,
        str,
        tuple[str, ...],
        str | None,
        str | None,
        tuple[str, ...],
        str | None,
        bool,
    ],
    ...,
]:
    """Return exact key, reference, CHECK-expression, and validation metadata."""
    expected: list[
        tuple[
            str,
            str,
            str,
            tuple[str, ...],
            str | None,
            str | None,
            tuple[str, ...],
            str | None,
            bool,
        ]
    ] = []
    type_codes = {"primary_key": "p", "unique": "u", "foreign_key": "f"}
    for table, constraints in generate_schema_v11.table_constraint_contract(
        list(rows)
    ).items():
        for item in constraints:
            reference_schema: str | None = None
            reference_table: str | None = None
            reference_columns: tuple[str, ...] = ()
            if item.references is not None:
                reference_schema = "source"
                reference_table, reference_columns = item.references
            expected.append(
                (
                    table,
                    item.name,
                    type_codes[item.kind],
                    item.columns,
                    reference_schema,
                    reference_table,
                    reference_columns,
                    None,
                    True,
                )
            )
    for check in generate_schema_v11.array_check_contract(list(rows)):
        column = next(
            row["target_identifier"]
            for row in rows
            if row["target_table"] == check.table
            and generate_schema_v11.constraint_name(
                "array_shape_check", check.table, row["target_identifier"]
            )
            == check.name
        )
        expected.append(
            (
                check.table,
                check.name,
                "c",
                (column,),
                None,
                None,
                (),
                _normalize_check_expression(check.expression),
                True,
            )
        )
    provenance_pk = generate_schema_v11.constraint_name(
        "primary_key", "provenance", "table_name"
    )
    expected.append(
        (
            "provenance",
            provenance_pk,
            "p",
            ("table_name",),
            None,
            None,
            (),
            None,
            True,
        )
    )
    for field in generate_schema_v11.PROVENANCE_CONTRACT:
        if not field.check_expression:
            continue
        expected.append(
            (
                "provenance",
                generate_schema_v11.constraint_name("check", "provenance", field.name),
                "c",
                (field.name,),
                None,
                None,
                (),
                _normalize_check_expression(
                    field.check_expression.replace("{column}", field.name)
                ),
                True,
            )
        )
    return tuple(sorted(expected, key=lambda item: (item[0], item[1])))


def verify_exact_retained_schema(
    connection: psycopg.Connection, rows: Sequence[dict[str, str]]
) -> dict[str, int]:
    """Reject same-named nullability or constraint-definition drift."""
    observed_columns = tuple(
        connection.execute(
            """
            SELECT c.relname, a.attname, a.attnotnull
            FROM pg_catalog.pg_attribute AS a
            JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = 'source' AND c.relkind = 'r'
              AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY c.relname, a.attnum
            """
        ).fetchall()
    )
    expected_columns = expected_retained_column_contract(rows)
    if observed_columns != expected_columns:
        raise ValueError("retained schema column nullability mismatch")

    observed_rows = connection.execute(
        """
        SELECT c.relname, con.conname, con.contype,
               ARRAY(
                 SELECT a.attname
                 FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, position)
                 JOIN pg_catalog.pg_attribute AS a
                   ON a.attrelid=con.conrelid AND a.attnum=key.attnum
                 ORDER BY key.position
               ),
               rn.nspname, rc.relname,
               ARRAY(
                 SELECT a.attname
                 FROM unnest(con.confkey) WITH ORDINALITY AS key(attnum, position)
                 JOIN pg_catalog.pg_attribute AS a
                   ON a.attrelid=con.confrelid AND a.attnum=key.attnum
                 ORDER BY key.position
               ),
               CASE WHEN con.contype='c'
                 THEN pg_catalog.pg_get_expr(con.conbin, con.conrelid, true)
                 ELSE NULL
               END,
               con.convalidated
        FROM pg_catalog.pg_constraint AS con
        JOIN pg_catalog.pg_class AS c ON c.oid=con.conrelid
        JOIN pg_catalog.pg_namespace AS n ON n.oid=c.relnamespace
        LEFT JOIN pg_catalog.pg_class AS rc ON rc.oid=con.confrelid
        LEFT JOIN pg_catalog.pg_namespace AS rn ON rn.oid=rc.relnamespace
        WHERE n.nspname='source'
        ORDER BY c.relname, con.conname
        """
    ).fetchall()
    observed_constraints = tuple(
        (
            table,
            name,
            kind,
            tuple(columns or ()),
            reference_schema,
            reference_table,
            tuple(reference_columns or ()),
            _normalize_check_expression(expression) if expression is not None else None,
            validated,
        )
        for (
            table,
            name,
            kind,
            columns,
            reference_schema,
            reference_table,
            reference_columns,
            expression,
            validated,
        ) in observed_rows
    )
    expected_constraints = expected_retained_constraint_contract(rows)
    if observed_constraints != expected_constraints:
        raise ValueError("retained schema constraint definition mismatch")
    return {
        "column_nullability": len(observed_columns),
        "constraint_definitions": len(observed_constraints),
    }


def validate_retained_load(
    settings: Settings, rows: Sequence[dict[str, str]]
) -> dict[str, Any]:
    """Validate the sealed retained database without FITS or COPY access."""
    counts: dict[str, int] = {}
    id_tables = 0
    with _connect(settings, settings.target_database) as connection:
        structure = verify_schema_v11_scratch._verify_objects_and_columns(
            connection, list(rows)
        )
        structure.update(verify_exact_retained_schema(connection, rows))
        owner_row = connection.execute(
            """
            SELECT
              (SELECT pg_get_userbyid(datdba) FROM pg_database
               WHERE datname=current_database()),
              (SELECT pg_get_userbyid(nspowner) FROM pg_namespace
               WHERE nspname='source'),
              (SELECT pg_get_userbyid(nspowner) FROM pg_namespace
               WHERE nspname='public'),
              (SELECT count(*) FROM pg_class c
               JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='source' AND c.relkind='r'
                 AND pg_get_userbyid(c.relowner) <> %s),
              (SELECT count(*) FROM pg_class c
               JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='source' AND c.relkind='r'
                 AND pg_get_userbyid(c.relowner) = %s)
            """,
            (settings.user, ANALYST_ROLE),
        ).fetchone()
        if (
            owner_row[0] != settings.user
            or owner_row[1] != settings.user
            or owner_row[2] == ANALYST_ROLE
            or owner_row[3] != 0
            or owner_row[4] != 0
        ):
            raise ValueError("retained load ownership contract mismatch")
        for table in MASTER_TABLES:
            table_rows = _table_dictionary_rows(rows, table)
            expected = int(
                json.loads(table_rows[0]["profile_json"])["profiles"][0]["row_count"]
            )
            count = connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
            if count != expected:
                raise ValueError("retained load master count mismatch")
            counts[table] = count
            stats = connection.execute(
                sql.SQL(
                    "SELECT count(*), count(DISTINCT source_row), "
                    "min(source_row), max(source_row), "
                    "count(*) FILTER (WHERE source_row IS NULL) FROM {}.{}"
                ).format(sql.Identifier("source"), sql.Identifier(table))
            ).fetchone()
            validate_source_row_stats(stats, expected_rows=count)
            if table == "photometry_primary":
                alignment = connection.execute(
                    """
                    SELECT count(*), count(id), count(DISTINCT id)
                    FROM source.photometry_primary
                    """
                ).fetchone()
                validate_id_alignment(
                    rows=alignment[0],
                    nonnull_ids=alignment[1],
                    distinct_ids=alignment[2],
                    primary_matches=alignment[0],
                    fk_violations=0,
                )
            else:
                alignment = connection.execute(
                    sql.SQL(
                        "SELECT count(*), count(e.id), count(DISTINCT e.id), "
                        "count(p.id), count(*) FILTER (WHERE p.id IS NULL) "
                        "FROM {}.{} AS e LEFT JOIN {}.{} AS p "
                        "ON p.source_row=e.source_row AND p.id=e.id"
                    ).format(
                        sql.Identifier("source"),
                        sql.Identifier(table),
                        sql.Identifier("source"),
                        sql.Identifier("photometry_primary"),
                    )
                ).fetchone()
                validate_id_alignment(
                    rows=alignment[0],
                    nonnull_ids=alignment[1],
                    distinct_ids=alignment[2],
                    primary_matches=alignment[3],
                    fk_violations=alignment[4],
                )
                id_tables += 1
        unloaded = {
            table: connection.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier("source"), sql.Identifier(table)
                )
            ).fetchone()[0]
            for table in UNLOADED_TABLES
        }
        validate_unloaded_counts(unloaded)
        size = connection.execute(
            "SELECT pg_database_size(current_database())"
        ).fetchone()[0]
        connection.rollback()
    if structure["array_checks"] != 166:
        raise ValueError("retained load array constraint mismatch")
    return {
        "structure": structure,
        "counts": counts,
        "unloaded_counts": unloaded,
        "source_row_tables": len(counts),
        "injected_id_tables": id_tables,
        "database_size_bytes": size,
        "owners": {
            "database": owner_row[0],
            "source_schema": owner_row[1],
            "public_schema": owner_row[2],
            "analyst_owned": 0,
        },
    }


def run_create_load(settings: Settings) -> dict[str, Any]:
    """Run the one non-idempotent Gate 3.7 persistent lifecycle."""
    execution_phases("create-load")
    preflight = final_preflight(settings)
    rows = _read_dictionary(settings)
    manifest = _manifest_contract(settings)
    before: Fingerprint = preflight["v1_fingerprint"]
    created = CreatedResources()
    analyst_secret = generate_analyst_secret()
    if analyst_secret == settings.password:
        raise ValueError("generated analyst secret equals admin credential")
    loads: list[TableLoadEvidence] = []
    first_matrix: dict[str, Any] = {}
    second_matrix: dict[str, Any] = {}
    default_privileges: dict[str, Any] = {}
    admin_verification: dict[str, Any] = {}
    handoff_evidence: HandoffGitEvidence | None = None
    loads_sealed = False
    stage = "create_database"
    try:
        with _connect(settings, settings.maintenance_database) as maintenance:
            maintenance.autocommit = True
            _assert_live_absence(maintenance, settings)
            maintenance.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings.target_database)
                )
            )
            created = replace(created, database=True)
        with _connect(settings, settings.target_database) as target:
            stage = "execute_reviewed_ddl"
            target.execute(preflight["ddl_payload"].decode("utf-8"))
            target.commit()
            verify_schema_v11_scratch._verify_objects_and_columns(target, rows)
            target.rollback()
            primary_ids: np.ndarray | None = None
            stage = "load_master_tables"
            for table in MASTER_TABLES:
                print(f"table_load_started: {table}", flush=True)
                evidence, primary_ids = _load_master_table(
                    target,
                    settings,
                    rows,
                    table,
                    manifest,
                    primary_ids,
                )
                loads.append(evidence)
                print(
                    f"table_load_completed: {table} rows={evidence.loaded_rows} "
                    f"elapsed_seconds={evidence.elapsed_seconds:.3f}",
                    flush=True,
                )
            loads_sealed = seal_completed_loads(loads)
            stage = "create_role"
            _create_analyst_role(target, settings, analyst_secret=analyst_secret)
            created = replace(created, role=True)
            stage = "verify_role"
            role = _role_observation(target)
            validate_role_observation(role)
            _verify_privilege_contract(target)
            target.rollback()
            print(post_load_stage_marker("verify_role"), flush=True)
        stage = "verify_admin"
        admin_verification = verify_target_admin(
            settings, rows, exercise_wrong_array=True
        )
        print(post_load_stage_marker("verify_admin"), flush=True)
        stage = "verify_analyst"
        first_matrix = verify_analyst_matrix(
            settings,
            expected_primary_rows=admin_verification["counts"]["photometry_primary"],
        )
        print(post_load_stage_marker("analyst_matrix_before_handoff"), flush=True)
        stage = "verify_default_privileges"
        default_privileges = verify_default_privileges(settings)
        print(post_load_stage_marker("verify_default_privileges"), flush=True)
        values = handoff_values(
            host=settings.host, port=settings.port, analyst_secret=analyst_secret
        )
        stage = "write_handoff"
        write_handoff_exclusive(settings.handoff_path, values)
        created = replace(created, handoff=True)
        print(post_load_stage_marker("write_handoff"), flush=True)
        stage = "read_handoff"
        read_handoff_for_verification(settings)
        stage = "verify_analyst"
        second_matrix = verify_analyst_matrix(
            settings,
            expected_primary_rows=admin_verification["counts"]["photometry_primary"],
        )
        print(post_load_stage_marker("analyst_matrix_after_handoff"), flush=True)
        stage = "verify_v1_fingerprint"
        after = capture_v1_fingerprint(settings)
        require_fingerprint_identity(before, after)
        print(post_load_stage_marker("verify_v1_fingerprint"), flush=True)
        stage = "verify_handoff_git"
        handoff_evidence = verify_handoff_git(settings, analyst_secret=analyst_secret)
        print(post_load_stage_marker("verify_handoff_git"), flush=True)
    except BaseException as exc:
        raise build_lifecycle_failure_after_cleanup(
            settings,
            created,
            stage=stage,
            error=exc,
            loads_sealed=loads_sealed,
        ) from None
    return {
        "mode": "create-load",
        "status": "passed",
        "postgresql_version": preflight["postgresql_version"],
        "capacity": asdict(preflight["capacity"]),
        "ddl_sha256": preflight["ddl_sha256"],
        "v1_before_sha256": before.sha256,
        "v1_after_sha256": after.sha256,
        "v1_fingerprint_equal": True,
        "v1_table_count": preflight["v1_table_count"],
        "loads": [asdict(item) for item in loads],
        "admin_verification": admin_verification,
        "analyst_matrix_before_handoff": first_matrix,
        "analyst_matrix_after_handoff": second_matrix,
        "default_privileges": default_privileges,
        "handoff": {
            "path": str(settings.handoff_path),
            "mode": "0600",
            "variable_names": list(HANDOFF_NAMES),
            "ignored": handoff_evidence.ignored,
            "tracked": handoff_evidence.tracked,
        },
        "created_resources_retained": ["database", "role", "handoff"],
        "analyst_verification_transport": "admin_session_authorization",
        "direct_analyst_network_auth_exercised": False,
        "pending_operator_action": "add direct analyst HBA coverage for ML01",
        "secret_exposure": 0,
    }


def run_verify_only(settings: Settings) -> dict[str, Any]:
    """Run separate post-handoff verification without create/load or cleanup."""
    execution_phases("verify-only")
    rows = _read_dictionary(settings)
    before = capture_v1_fingerprint(settings)
    parsed = read_handoff_for_verification(settings)
    analyst_secret = parsed["PGSQL01_COSMOS2025_V11_PASSWORD"]
    admin = verify_target_admin(settings, rows, exercise_wrong_array=False)
    matrix = verify_analyst_matrix(
        settings, expected_primary_rows=admin["counts"]["photometry_primary"]
    )
    after = capture_v1_fingerprint(settings)
    require_fingerprint_identity(before, after)
    git_evidence = verify_handoff_git(settings, analyst_secret=analyst_secret)
    return {
        "mode": "verify-only",
        "status": "passed",
        "v1_before_sha256": before.sha256,
        "v1_after_sha256": after.sha256,
        "v1_fingerprint_equal": True,
        "admin_verification": admin,
        "analyst_matrix": matrix,
        "analyst_verification_transport": "admin_session_authorization",
        "direct_analyst_network_auth_exercised": False,
        "pending_operator_action": "add direct analyst HBA coverage for ML01",
        "handoff": {
            "path": str(settings.handoff_path),
            "mode": "0600",
            "variable_names": list(HANDOFF_NAMES),
            "ignored": git_evidence.ignored,
            "tracked": git_evidence.tracked,
        },
        "secret_exposure": 0,
    }


def run_finalize_admin(settings: Settings) -> dict[str, Any]:
    """Finalize exact retained loads without source reads, COPY, or DB creation."""
    execution_phases("finalize-admin")
    created = CreatedResources()
    loads_sealed = False
    stage = "validate_retained_load"
    try:
        _assert_finalize_admin_live_boundary(settings)
        rows = _read_dictionary(settings)
        before = capture_v1_fingerprint(settings)
        retained_load = validate_retained_load(settings, rows)
        loads_sealed = True
        analyst_secret = generate_analyst_secret()
        if analyst_secret == settings.password:
            raise ValueError("generated analyst secret equals admin credential")
        stage = "create_role"
        with _connect(settings, settings.target_database) as target:
            _create_analyst_role(target, settings, analyst_secret=analyst_secret)
            created = replace(created, role=True)
            stage = "verify_role"
            role = _role_observation(target)
            validate_role_observation(role)
            _verify_privilege_contract(target)
            target.rollback()
            print(post_load_stage_marker("verify_role"), flush=True)
        stage = "verify_admin"
        admin = verify_target_admin(settings, rows, exercise_wrong_array=False)
        print(post_load_stage_marker("verify_admin"), flush=True)
        stage = "verify_analyst"
        first_matrix = verify_analyst_matrix(
            settings,
            expected_primary_rows=admin["counts"]["photometry_primary"],
        )
        print(post_load_stage_marker("analyst_matrix_before_handoff"), flush=True)
        stage = "verify_default_privileges"
        defaults = verify_default_privileges(settings)
        print(post_load_stage_marker("verify_default_privileges"), flush=True)
        values = handoff_values(
            host=settings.host,
            port=settings.port,
            analyst_secret=analyst_secret,
        )
        stage = "write_handoff"
        write_handoff_exclusive(settings.handoff_path, values)
        created = replace(created, handoff=True)
        print(post_load_stage_marker("write_handoff"), flush=True)
        stage = "read_handoff"
        read_handoff_for_verification(settings)
        stage = "verify_analyst"
        second_matrix = verify_analyst_matrix(
            settings,
            expected_primary_rows=admin["counts"]["photometry_primary"],
        )
        print(post_load_stage_marker("analyst_matrix_after_handoff"), flush=True)
        stage = "verify_v1_fingerprint"
        after = capture_v1_fingerprint(settings)
        require_fingerprint_identity(before, after)
        print(post_load_stage_marker("verify_v1_fingerprint"), flush=True)
        stage = "verify_handoff_git"
        git_evidence = verify_handoff_git(settings, analyst_secret=analyst_secret)
        print(post_load_stage_marker("verify_handoff_git"), flush=True)
    except BaseException as exc:
        raise build_lifecycle_failure_after_cleanup(
            settings,
            created,
            stage=stage,
            error=exc,
            loads_sealed=loads_sealed,
        ) from None
    return {
        "mode": "finalize-admin",
        "status": "passed",
        "retained_load_validation": retained_load,
        "admin_verification": admin,
        "analyst_matrix_before_handoff": first_matrix,
        "analyst_matrix_after_handoff": second_matrix,
        "default_privileges": defaults,
        "v1_before_sha256": before.sha256,
        "v1_after_sha256": after.sha256,
        "v1_fingerprint_equal": True,
        "handoff": {
            "path": str(settings.handoff_path),
            "mode": "0600",
            "variable_names": list(HANDOFF_NAMES),
            "ignored": git_evidence.ignored,
            "tracked": git_evidence.tracked,
        },
        "created_resources_retained": ["role", "handoff"],
        "existing_resources_retained": ["database"],
        "analyst_verification_transport": "admin_session_authorization",
        "direct_analyst_network_auth_exercised": False,
        "pending_operator_action": "add direct analyst HBA coverage for ML01",
        "source_reads": 0,
        "copy_operations": 0,
        "secret_exposure": 0,
    }


def main() -> None:
    """Dispatch create/load, admin finalization, or post-load verification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--create-load", action="store_true")
    modes.add_argument("--finalize-admin", action="store_true")
    modes.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        settings = resolve_settings(args.config)
        if args.create_load:
            result = run_create_load(settings)
        elif args.finalize_admin:
            result = run_finalize_admin(settings)
        else:
            result = run_verify_only(settings)
    except BaseException as exc:
        if isinstance(exc, LifecycleFailure):
            diagnostic = str(exc)
        else:
            error_class, sqlstate = _safe_exception_metadata(exc)
            diagnostic = f"exception={error_class} sqlstate={sqlstate}"
        raise SystemExit(f"Gate 3.7 FAILED: {diagnostic}") from None
    print(json.dumps(public_summary(result), indent=2, sort_keys=True))


# =============================================================================
# Verification invariants
# =============================================================================


def validate_source_row_stats(
    observed: tuple[int, int, int | None, int | None, int], *, expected_rows: int
) -> None:
    """Enforce count/distinct/min/max/null source-row invariants."""
    count, distinct, minimum, maximum, nulls = observed
    expected_maximum = expected_rows - 1 if expected_rows else None
    if observed != (expected_rows, expected_rows, 0, expected_maximum, 0):
        raise ValueError(
            "source_row invariant mismatch: "
            f"expected {(expected_rows, expected_rows, 0, expected_maximum, 0)}, "
            f"observed {(count, distinct, minimum, maximum, nulls)}"
        )


def validate_unloaded_counts(counts: Mapping[str, int]) -> None:
    """Require the exact four supplement/spec-z mirrors and provenance to be empty."""
    if set(counts) != set(UNLOADED_TABLES):
        raise ValueError("unloaded table boundary mismatch")
    nonempty = {name: count for name, count in counts.items() if count != 0}
    if nonempty:
        raise ValueError(f"unloaded table is nonempty: {sorted(nonempty)}")


# =============================================================================
# Entry Point
# =============================================================================


if __name__ == "__main__":
    main()
