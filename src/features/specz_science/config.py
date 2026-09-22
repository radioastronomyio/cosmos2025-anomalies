"""Repository configuration and database connections for the P2R-05 build.

Science policy lives in ``configs/specz_science_policy_v1.yaml`` and is never
read here. This module resolves implementation paths from
``configs/data_paths.yaml``, loads the fixed analyst credential handoff by
name only, and opens analyst connections with connection-time read-only
enforcement as the runtime contract requires. Credential values are never
logged, returned in evidence, or written to tracked files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import psycopg
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "data_paths.yaml"

ANALYST_DB_ENV = "PGSQL01_COSMOS2025_V11_DB"
ANALYST_USER_ENV = "PGSQL01_COSMOS2025_V11_USER"
ANALYST_PASSWORD_ENV = "PGSQL01_COSMOS2025_V11_PASSWORD"
HOST_ENV = "PGSQL01_HOST"
PORT_ENV = "PGSQL01_PORT"

READ_ONLY_OPTION = "-c default_transaction_read_only=on"


@dataclass(frozen=True)
class SpeczSciencePaths:
    """Resolved implementation paths for the spec-z science surface."""

    policy_path: Path
    staging_dir: Path
    evidence_dir: Path
    analyst_env_handoff: Path
    snapshot_dir: Path
    target_database: str
    analysis_schema: str
    product_tables: tuple[str, ...]
    snapshot_batch_rows: int
    install_batch_rows: int


def resolve_paths(config_path: Path | None = None) -> SpeczSciencePaths:
    """Resolve the ``specz_science`` section of the repository configuration."""
    resolved = config_path if config_path is not None else DEFAULT_CONFIG_PATH
    config = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    section = config["specz_science"]
    return SpeczSciencePaths(
        policy_path=Path(section["policy_path"]),
        staging_dir=Path(section["staging_dir"]),
        evidence_dir=Path(section["evidence_dir"]),
        analyst_env_handoff=Path(section["analyst_env_handoff"]),
        snapshot_dir=Path(section["snapshot_dir"]),
        target_database=str(section["target_database"]),
        analysis_schema=str(section["analysis_schema"]),
        product_tables=tuple(str(name) for name in section["product_tables"]),
        snapshot_batch_rows=int(section["snapshot_batch_rows"]),
        install_batch_rows=int(section["install_batch_rows"]),
    )


def load_analyst_environment(
    handoff: Path | None = None, paths: SpeczSciencePaths | None = None
) -> dict[str, str]:
    """Load the fixed analyst handoff names into a private mapping.

    Existing process environment values win over the handoff file so the
    scoped Doppler runtime can supply the same names. Values never enter the
    returned evidence of any caller; this function returns credentials only
    for immediate connection use.
    """
    if paths is None and handoff is None:
        paths = resolve_paths()
    source = handoff if handoff is not None else paths.analyst_env_handoff  # type: ignore[union-attr]
    values = {
        key: value
        for key, value in (
            line.split("=", 1) for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#") and "=" in line
        )
    }
    merged = {
        ANALYST_DB_ENV: os.environ.get(ANALYST_DB_ENV, values.get(ANALYST_DB_ENV, "")),
        ANALYST_USER_ENV: os.environ.get(
            ANALYST_USER_ENV, values.get(ANALYST_USER_ENV, "")
        ),
        ANALYST_PASSWORD_ENV: os.environ.get(
            ANALYST_PASSWORD_ENV, values.get(ANALYST_PASSWORD_ENV, "")
        ),
        HOST_ENV: os.environ.get(HOST_ENV, values.get(HOST_ENV, "")),
        PORT_ENV: os.environ.get(PORT_ENV, values.get(PORT_ENV, "")),
    }
    missing = sorted(name for name, value in merged.items() if not value)
    if missing:
        raise RuntimeError(
            f"analyst handoff incomplete: missing {missing} "
            f"(expected in {source})"
        )
    return merged


@dataclass(frozen=True)
class AnalystIdentity:
    """Connection coordinates for the fixed analyst contract (no secrets)."""

    host: str
    port: str
    database: str
    user: str


def connect_analyst(
    environment: dict[str, str] | None = None,
    *,
    handoff: Path | None = None,
    paths: SpeczSciencePaths | None = None,
) -> tuple[psycopg.Connection, AnalystIdentity]:
    """Open an analyst connection with connection-time read-only enforcement.

    Returns the connection and a secret-free identity record for evidence.
    The ``options`` parameter sets ``default_transaction_read_only=on`` at
    connection time, which the runtime contract requires independently of
    effective table privileges.
    """
    env = environment if environment is not None else load_analyst_environment(
        handoff=handoff, paths=paths
    )
    identity = AnalystIdentity(
        host=env[HOST_ENV],
        port=env[PORT_ENV],
        database=env[ANALYST_DB_ENV],
        user=env[ANALYST_USER_ENV],
    )
    connection = psycopg.connect(
        host=env[HOST_ENV],
        port=int(env[PORT_ENV]),
        dbname=env[ANALYST_DB_ENV],
        user=env[ANALYST_USER_ENV],
        password=env[ANALYST_PASSWORD_ENV],
        options=READ_ONLY_OPTION,
    )
    return connection, identity
