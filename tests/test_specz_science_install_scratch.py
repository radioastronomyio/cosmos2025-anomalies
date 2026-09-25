"""Gate 5.6 scratch proofs: bootstrap contract, guards, reversibility.

On a disposable guarded-prefix database: the installer creates exactly the
declared tables with working keys and relationships, honors the analyst
grants, refuses a pre-existing same-named relation, leaves unrelated
objects untouched, retains work after an uncertain commit, and the down
operation removes only this run's rows and only newly created objects.
Production-sized content identity is proven on the real installation
separately. Requires the scoped Doppler admin environment; skips otherwise.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import install as ssi  # noqa: E402

ADMIN_ENV_NAMES = (
    "PGSQL01_HOST",
    "PGSQL01_PORT",
    "PGSQL01_ADMIN_USER",
    "PGSQL01_ADMIN_PASSWORD",
)


def _admin_environment_present() -> bool:
    return all(os.environ.get(name) for name in ADMIN_ENV_NAMES)


requires_admin = pytest.mark.skipif(
    not _admin_environment_present(),
    reason="scratch tests require the scoped Doppler admin environment",
)


class AdminDB:
    """Guarded scratch database lifecycle for one test."""

    def __init__(self) -> None:
        from src.etl import verify_schema_v11_scratch as scratch

        self.name = scratch.validate_scratch_name(scratch.generate_scratch_name())
        self.params = {
            "host": os.environ["PGSQL01_HOST"],
            "port": int(os.environ["PGSQL01_PORT"]),
            "user": os.environ["PGSQL01_ADMIN_USER"],
            "password": os.environ["PGSQL01_ADMIN_PASSWORD"],
        }

    def __enter__(self) -> psycopg.Connection:
        with psycopg.connect(dbname="postgres", **self.params) as server:
            server.autocommit = True
            server.execute(f'CREATE DATABASE "{self.name}"')
        self.connection = psycopg.connect(dbname=self.name, **self.params)
        return self.connection

    def __exit__(self, *exc) -> None:
        self.connection.close()
        with psycopg.connect(dbname="postgres", **self.params) as server:
            server.autocommit = True
            server.execute(f'DROP DATABASE IF EXISTS "{self.name}"')


def synthetic_products(tmp_path: Path) -> Path:
    """Small artifacts matching the real product schemas."""
    products = tmp_path / "products"
    products.mkdir()
    natives = {
        "id_original": "src-a",
        "ra_original": 150.0,
        "dec_original": 2.0,
        "ra_corrected": 150.0,
        "dec_corrected": 2.0,
        "priority": 1,
        "specz": 0.5,
        "flag": 4,
        "confidence_level": 97,
        "survey": 37,
        "compilation_year": 2019,
        "public_or_private": 1,
        "id_cos20_classic": None,
        "ra_cos20_classic": None,
        "dec_cos20_classic": None,
        "id_cos20_farmer": None,
        "ra_cos20_farmer": None,
        "dec_cos20_farmer": None,
        "id_cosmos25": 11,
        "ra_cosmos25": None,
        "dec_cosmos25": None,
        "id_cosmos15": None,
        "ra_cosmos15": None,
        "dec_cosmos15": None,
        "id_cosmos09": None,
        "ra_cosmos09": None,
        "dec_cosmos09": None,
        "photoz": None,
        "photoz_type": None,
        "groupid": None,
        "groupsize": None,
    }
    measurement = {
        "run_id": "run-x",
        "id_specz": 1,
        **{"native_" + name: value for name, value in natives.items()},
        "association_status": "associated",
        "resolved_catalog_id": 11,
        "is_unique_member": True,
        "numeric_valid_z": True,
        "z_invalid_reason": None,
        "flag_category": "recognized_measured",
        "confidence_in_domain": True,
        "flag_confidence_mapping_consistent": True,
        "secure_measurement": True,
        "secure_block_reasons": [],
    }
    source = {
        "run_id": "run-x",
        "catalog_id": 11,
        "association_resolved": True,
        "population_a": False,
        "population_b": False,
        "unique_entry_count": 1,
        "all_entry_count": 1,
        "numeric_valid_all_count": 1,
        "secure_all_count": 1,
        "preferred_id_specz": 1,
        "preferred_reported_z": 0.5,
        "preferred_flag": 4,
        "preferred_confidence": 97,
        "preferred_tie": False,
        "preferred_tied_ids": [1],
        "preferred_entry_is_secure": True,
        "unique_numeric_conflict": False,
        "secure_all_conflict": False,
        "other_measurement_disagreement": False,
        "conflict_witnesses": {"threshold": 0.005},
        "corroboration_status": "singly_supported",
        "lephare_type": 0,
        "classification_label": "galaxy",
        "broad_line_reported": False,
        "broad_line_entry_ids": [],
        "broad_line_confidences": [],
        "photometric_qso": False,
        "flag_star_mask_overlap": False,
        "flag_blend": False,
        "native_tile": "A1",
        "eligibility_primary_galaxy": True,
        "eligibility_separate_validation": False,
        "eligibility_basis_primary_pre_split": True,
        "eligibility_basis_validation_pre_split": False,
        "assigned_split": "holdout",
        "exclusion_reasons": [],
    }
    split = {
        "run_id": "run-x",
        "catalog_id": 11,
        "native_tile": "A1",
        "assigned_split": "holdout",
        "split_version": "p2r05-spatial-v1",
        "split_salt": "cosmos2025-p2r05-spatial-v1",
        "valid_tile_domain_member": True,
        "unassigned": False,
    }
    for name, record in (
        ("measurements.jsonl", measurement),
        ("sources.jsonl", source),
        ("splits.jsonl", split),
    ):
        (products / name).write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    return products


def run_metadata() -> dict:
    return {
        "run_id": "run-x",
        "policy_id": "p2r05-specz-policy-v1",
        "spec_version": "1.0",
        "spec_sha256": "0" * 64,
        "policy_semantic_digest": "0" * 64,
        "snapshot_manifest_digest": "0" * 64,
        "snapshot_file_digests": {},
        "implementation": {},
        "content_digests": {
            "measurements_content_sha256": "0" * 64,
            "sources_content_sha256": "0" * 64,
            "splits_content_sha256": "0" * 64,
            "measurement_rows": 1,
            "source_rows": 1,
            "split_rows": 1,
        },
        "tile_map_canonical_digest": "0" * 64,
        "tile_map": {},
        "created_at": "2026-09-22T00:00:00+00:00",
        "installed_by": "scratch-test",
    }


@requires_admin
def test_scratch_install_creates_declared_contract(tmp_path: Path) -> None:
    with AdminDB() as connection:
        result = ssi.install(
            connection, products_dir=synthetic_products(tmp_path), run_metadata=run_metadata()
        )
        assert result["installed"] is True
        # Declared relations and grants.
        relations = {
            row[0]
            for row in connection.execute(
                "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'analysis' AND c.relkind = 'r'"
            ).fetchall()
        }
        assert relations == set(ssi.PRODUCT_TABLES)
        for table in ssi.PRODUCT_TABLES:
            granted = connection.execute(
                "SELECT has_table_privilege(%s, %s, 'SELECT')",
                (ssi.ANALYST_ROLE, f'analysis."{table}"'),
            ).fetchone()[0]
            assert granted is True
        # Keys: duplicate primary key rejected.
        with pytest.raises(psycopg.errors.UniqueViolation):
            connection.execute(
                'INSERT INTO analysis.specz_p2r05_splits VALUES '
                "('run-x', 11, 'A1', 'holdout', 'v', 's', true, false)"
            )
            connection.commit()
        connection.rollback()
        # Relationship: orphan FK rejected.
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            connection.execute(
                'INSERT INTO analysis.specz_p2r05_splits VALUES '
                "('run-y', 99, 'A1', 'holdout', 'v', 's', true, false)"
            )
            connection.commit()
        connection.rollback()
        # Pending adoption state recorded.
        state = connection.execute(
            "SELECT product_state FROM analysis.specz_p2r05_runs WHERE run_id = 'run-x'"
        ).fetchone()[0]
        assert state == "pending_scientific_adoption"
        # Down removes only this run's rows and the newly created objects.
        teardown = ssi.down(
            connection, run_id="run-x", created_objects=(*ssi.PRODUCT_TABLES, "analysis")
        )
        assert teardown["removed_rows"][ssi.MEASUREMENTS] == 1
        assert teardown["schema_dropped"] is True
        remaining = connection.execute(
            "SELECT to_regnamespace('analysis') IS NOT NULL"
        ).fetchone()[0]
        assert remaining is False


@requires_admin
def test_scratch_preexisting_relation_stops_install(tmp_path: Path) -> None:
    with AdminDB() as connection:
        connection.execute("CREATE SCHEMA analysis")
        connection.execute(
            "CREATE TABLE analysis.specz_p2r05_runs (run_id text)"
        )
        connection.commit()
        with pytest.raises(SystemExit, match="does not"):
            ssi.install(
                connection,
                products_dir=synthetic_products(tmp_path),
                run_metadata=run_metadata(),
            )
        survivor = connection.execute(
            "SELECT count(*) FROM analysis.specz_p2r05_runs"
        ).fetchone()[0]
        assert survivor == 0  # untouched, no rows injected


@requires_admin
def test_scratch_unrelated_objects_inventoried_and_untouched(tmp_path: Path) -> None:
    with AdminDB() as connection:
        connection.execute("CREATE SCHEMA analysis")
        connection.execute("CREATE TABLE analysis.unrelated (x int)")
        connection.execute("INSERT INTO analysis.unrelated VALUES (7)")
        connection.commit()
        with pytest.raises(SystemExit, match="not a clean bootstrap"):
            ssi.install(
                connection,
                products_dir=synthetic_products(tmp_path),
                run_metadata=run_metadata(),
            )
        retained = connection.execute(
            "SELECT x FROM analysis.unrelated"
        ).fetchone()[0]
        assert retained == 7


@requires_admin
def test_scratch_repeat_install_is_nonmutating(tmp_path: Path) -> None:
    with AdminDB() as connection:
        products = synthetic_products(tmp_path)
        ssi.install(connection, products_dir=products, run_metadata=run_metadata())
        before = connection.execute(
            "SELECT count(*) FROM analysis.specz_p2r05_sources"
        ).fetchone()[0]
        result = ssi.install(
            connection, products_dir=products, run_metadata=run_metadata()
        )
        assert result["installed"] is False
        assert result["unchanged"] is True
        after = connection.execute(
            "SELECT count(*) FROM analysis.specz_p2r05_sources"
        ).fetchone()[0]
        assert after == before
        # Conflicting payload under the same run id fails before mutation.
        conflicting = run_metadata()
        conflicting["content_digests"] = {
            **conflicting["content_digests"],
            "sources_content_sha256": "1" * 64,
        }
        with pytest.raises(SystemExit, match="different content digests"):
            ssi.install(connection, products_dir=products, run_metadata=conflicting)
        survivors = connection.execute(
            "SELECT count(*) FROM analysis.specz_p2r05_sources"
        ).fetchone()[0]
        assert survivors == before


@requires_admin
def test_scratch_uncertain_commit_retains_installed_work(tmp_path: Path) -> None:
    class PostCommitRaiseProxy:
        def __init__(self, inner):
            self._inner = inner

        def execute(self, *a, **k):
            return self._inner.execute(*a, **k)

        def cursor(self):
            return self._inner.cursor()

        def commit(self):
            self._inner.commit()
            raise RuntimeError("client failure after server-side commit")

        def rollback(self):
            return self._inner.rollback()

    with AdminDB() as connection:
        with pytest.raises(RuntimeError, match="after server-side commit"):
            ssi.install(
                PostCommitRaiseProxy(connection),
                products_dir=synthetic_products(tmp_path),
                run_metadata=run_metadata(),
            )
        rows = connection.execute(
            "SELECT count(*) FROM analysis.specz_p2r05_measurements"
        ).fetchone()[0]
        assert rows == 1  # committed work retained, never cleaned up
        state = connection.execute(
            "SELECT product_state FROM analysis.specz_p2r05_runs"
        ).fetchone()[0]
        assert state == "pending_scientific_adoption"


@requires_admin
def test_scratch_precommit_failure_rolls_back(tmp_path: Path) -> None:
    with AdminDB() as connection:
        products = synthetic_products(tmp_path)
        # Declare a wrong expected count so the post-COPY verification fails
        # after the DDL and load but before the commit attempt.
        mismatched = run_metadata()
        mismatched["content_digests"] = {
            **mismatched["content_digests"],
            "measurement_rows": 2,
        }
        with pytest.raises(SystemExit, match="counts"):
            ssi.install(
                connection, products_dir=products, run_metadata=mismatched
            )
        connection.rollback()
        exists = connection.execute(
            "SELECT to_regnamespace('analysis') IS NOT NULL"
        ).fetchone()[0]
        assert exists is False, "rolled-back install must leave no schema"
