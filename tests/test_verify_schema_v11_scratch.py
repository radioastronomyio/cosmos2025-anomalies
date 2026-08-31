#!/usr/bin/env python3
"""
Script Name  : test_verify_schema_v11_scratch.py
Description  : Test safe disposable database verification for ETL v2 DDL
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-17
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Exercises Gate 3.6 scratch-name guards, environment-only connection
resolution, and sealed catalog conformance mutations without authenticating.
The live database lifecycle is run only by the dedicated Doppler-backed CLI.

Usage
-----
    pytest tests/test_verify_schema_v11_scratch.py -v
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "etl" / "verify_schema_v11_scratch.py"
DICTIONARY_PATH = REPO_ROOT / "data" / "dictionary" / "columns-v11.csv"


# =============================================================================
# Test utilities
# =============================================================================


def _module():
    """Load production only after test start so missing code is a RED failure."""
    assert MODULE_PATH.exists(), "Gate 3.6 scratch verifier module is missing"
    spec = importlib.util.spec_from_file_location(
        "verify_schema_v11_scratch", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows() -> list[dict[str, str]]:
    """Read sealed expectations independently of production helpers."""
    with DICTIONARY_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# =============================================================================
# Scratch safety and mutation contracts
# =============================================================================


def test_generated_scratch_name_is_narrow_random_and_valid() -> None:
    """A fixed, target, or out-of-prefix database name must never be accepted."""
    module = _module()
    first = module.generate_scratch_name(pid=1234, token="a" * 16)
    second = module.generate_scratch_name(pid=1234, token="b" * 16)
    assert first == "cosmos2025_v11_scratch_1234_" + "a" * 16
    assert first != second
    assert module.validate_scratch_name(first) == first
    assert len(first.encode("utf-8")) <= 63


@pytest.mark.parametrize(
    "database_name",
    [
        "cosmos2025",
        "cosmos2025_v11",
        "postgres",
        "cosmos2025_v11_scratch_",
        "cosmos2025_v11_scratch_bad-name",
        "cosmos2025_v11_scratch_1234_aaaaaaaaaaaaaaaa_extra",
    ],
)
def test_scratch_name_guard_rejects_every_non_generated_target(
    database_name: str,
) -> None:
    """Relaxing the exact generated-name grammar must expose protected names."""
    module = _module()
    with pytest.raises(ValueError, match="refusing unsafe scratch database name"):
        module.validate_scratch_name(database_name)


def test_connection_settings_use_only_configured_environment_names(
    tmp_path: Path,
) -> None:
    """Literal credentials or a protected maintenance database must be rejected."""
    module = _module()
    config = {
        "database": {
            "host_env": "TEST_ADMIN_HOST",
            "port_env": "TEST_ADMIN_PORT",
            "user_env": "TEST_ADMIN_USER",
            "password_env": "TEST_ADMIN_PASSWORD",
            "maintenance_database": "postgres",
            "scratch_prefix": "cosmos2025_v11_scratch_",
        }
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    environment = {
        "TEST_ADMIN_HOST": "db-alias",
        "TEST_ADMIN_PORT": "5432",
        "TEST_ADMIN_USER": "admin",
        "TEST_ADMIN_PASSWORD": "top-secret-test-value",
    }
    settings = module.resolve_connection_settings(path, environment)
    assert settings.host == "db-alias"
    assert settings.port == 5432
    assert settings.user == "admin"
    assert settings.password == "top-secret-test-value"
    assert settings.maintenance_database == "postgres"

    del environment["TEST_ADMIN_PASSWORD"]
    with pytest.raises(ValueError) as error:
        module.resolve_connection_settings(path, environment)
    assert "TEST_ADMIN_PASSWORD" in str(error.value)
    assert "top-secret-test-value" not in str(error.value)


@pytest.mark.parametrize("maintenance_database", ["cosmos2025", "cosmos2025_v11"])
def test_protected_database_cannot_be_used_for_maintenance(
    tmp_path: Path, maintenance_database: str
) -> None:
    """A config edit must not route admin commands through either protected target."""
    module = _module()
    config = {
        "database": {
            "host_env": "H",
            "port_env": "P",
            "user_env": "U",
            "password_env": "W",
            "maintenance_database": maintenance_database,
            "scratch_prefix": "cosmos2025_v11_scratch_",
        }
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="protected maintenance database"):
        module.resolve_connection_settings(
            path, {"H": "host", "P": "5432", "U": "user", "W": "secret"}
        )


def test_sealed_column_comparison_is_bidirectional_and_ordered() -> None:
    """A missing, extra, reordered, or remapped column must fail conformance."""
    module = _module()
    expected = module.expected_mirror_columns(_rows())
    assert len(expected) == 1_448
    module.compare_mirror_columns(expected, expected)

    mutations = {
        "removed": expected[:-1],
        "extra": expected + (("specz_compilation_unique", "invented", "text", 33),),
        "reordered": expected[:-2] + (expected[-1], expected[-2]),
        "remapped": expected[:-1]
        + ((expected[-1][0], expected[-1][1], "text", expected[-1][3]),),
    }
    for label, observed in mutations.items():
        with pytest.raises(ValueError, match="mirror column conformance mismatch"):
            module.compare_mirror_columns(expected, observed)
        assert re.fullmatch(r"[a-z]+", label)


def test_one_row_removed_dictionary_mutation_cannot_pass_conformance() -> None:
    """A 1,415-column valid-looking mirror must fail against the sealed 1,416 rows."""
    module = _module()
    sealed = module.expected_mirror_columns(_rows())
    one_row_removed = sealed[:-1]
    with pytest.raises(ValueError, match="expected 1448, observed 1447"):
        module.compare_mirror_columns(sealed, one_row_removed)


def test_cleanup_query_is_prefix_scoped_and_reports_zero_only() -> None:
    """Cleanup proof must never broaden from the exact configured scratch prefix."""
    module = _module()
    query, parameter = module.scratch_inventory_query("cosmos2025_v11_scratch_")
    assert "datname LIKE" in query
    assert "ESCAPE '!'" in query
    assert parameter == "cosmos2025!_v11!_scratch!_%"
    assert "cosmos2025_v11" not in query
