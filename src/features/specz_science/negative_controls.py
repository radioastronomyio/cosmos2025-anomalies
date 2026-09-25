"""Gate 5.7 negative controls: six tampers, each rejected on its invariant.

One guarded scratch database per control. Each control installs the real
staging artifacts with exactly one tamper applied and then runs the
independent comparison (never the builders) expecting the intended
invariant to fail: a removed exclusion category, an altered source
association, a promoted population-A entry, an erased secure conflict, a
changed tied preferred entry, and a source moved between splits. A control
passes only when the tamper is caught and the intended check names it.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import install as ssi  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402
from check_installed_independent import independent_tile_map  # noqa: E402

ADMIN_ENV_NAMES = (
    "PGSQL01_HOST",
    "PGSQL01_PORT",
    "PGSQL01_ADMIN_USER",
    "PGSQL01_ADMIN_PASSWORD",
)


def admin_params() -> dict[str, object]:
    return {
        "host": os.environ["PGSQL01_HOST"],
        "port": int(os.environ["PGSQL01_PORT"]),
        "user": os.environ["PGSQL01_ADMIN_USER"],
        "password": os.environ["PGSQL01_ADMIN_PASSWORD"],
    }


def scratch_name() -> str:
    from src.etl import verify_schema_v11_scratch as scratch

    return scratch.validate_scratch_name(scratch.generate_scratch_name())


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(
                json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            )


def prepare(tmp: Path) -> Path:
    products = tmp / "products"
    products.mkdir(parents=True, exist_ok=True)
    for name in ("measurements.jsonl", "sources.jsonl", "splits.jsonl", "finalize-summary.json"):
        shutil.copy(
            REPO_ROOT / "staging/derived/specz-p2r05/products" / name, products / name
        )
    return products


def run_control(
    name: str,
    tamper,
    *,
    expect_substring: str,
    data: ssv.SnapshotData,
    preferred,
    flags,
    tile_mapping,
    run_id: str,
) -> dict[str, object]:
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="p2r05-control-"))
    products = prepare(tmp)
    tamper(products, data)
    database = scratch_name()
    with psycopg.connect(dbname="postgres", **admin_params()) as server:  # type: ignore[arg-type]
        server.autocommit = True
        server.execute(f'CREATE DATABASE "{database}"')
    caught = None
    checked = 0
    try:
        with psycopg.connect(dbname=database, **admin_params()) as connection:  # type: ignore[arg-type]
            metadata = ssi.run_metadata_from_staging(ss_config.resolve_paths())
            ssi.install(
                connection, products_dir=products, run_metadata=metadata
            )
            # Independent comparison, streaming the installed rows.
            for record in ssi._stream_installed(
                connection,
                ssi.SOURCES,
                run_id,
                "run_id, catalog_id",
                ssi._expected_columns(ssi.SOURCES),
            ):
                checked += 1
                source_id = record["catalog_id"]
                independent_entry = preferred.get(source_id)
                expected_preferred = (
                    independent_entry.id_specz if independent_entry else None
                )
                if record["preferred_id_specz"] != expected_preferred:
                    caught = f"preferred {record['preferred_id_specz']} != {expected_preferred} at source {source_id}"
                    break
                flag = flags.get(source_id, {})
                for flag_name in (
                    "unique_numeric_conflict",
                    "secure_all_conflict",
                    "other_measurement_disagreement",
                ):
                    if bool(record[flag_name]) is not bool(flag.get(flag_name)):
                        caught = f"flag {flag_name} at source {source_id}"
                        break
                if caught:
                    break
                tile = data.catalog[source_id].tile
                expected_split = tile_mapping.get(tile, "unassigned")
                if record["assigned_split"] != expected_split:
                    caught = f"split {record['assigned_split']} != {expected_split} at source {source_id}"
                    break
                expected_reasons = independent_reasons_local(
                    data, preferred, flags, tile_mapping, source_id
                )
                if sorted(record["exclusion_reasons"]) != expected_reasons:
                    caught = f"reasons at source {source_id}: {sorted(record['exclusion_reasons'])} != {expected_reasons}"
                    break
            if caught is None:
                for record in ssi._stream_installed(
                    connection,
                    ssi.MEASUREMENTS,
                    run_id,
                    "run_id, id_specz",
                    ssi._expected_columns(ssi.MEASUREMENTS),
                ):
                    checked += 1
                    entry = data.all_by_id[record["id_specz"]]
                    expected_status = (
                        "no_association_sentinel"
                        if entry.id_cosmos25 is None or entry.id_cosmos25 == -999
                        else "associated"
                        if entry.id_cosmos25 in data.catalog_ids
                        else "unresolved_identifier"
                    )
                    if record["association_status"] != expected_status:
                        caught = f"association {record['association_status']} != {expected_status} at entry {record['id_specz']}"
                        break
                    expected_resolved = (
                        entry.id_cosmos25 if expected_status == "associated" else None
                    )
                    if record["resolved_catalog_id"] != expected_resolved:
                        caught = f"resolved id {record['resolved_catalog_id']} != {expected_resolved} at entry {record['id_specz']}"
                        break
                    if bool(record["secure_measurement"]) is not ssv.entry_is_secure(entry):
                        caught = f"secure at entry {record['id_specz']}"
                        break
    finally:
        with psycopg.connect(dbname="postgres", **admin_params()) as server:  # type: ignore[arg-type]
            server.autocommit = True
            server.execute(f'DROP DATABASE IF EXISTS "{database}"')
        shutil.rmtree(tmp, ignore_errors=True)
    if caught is None:
        raise SystemExit(f"control {name}: TAMPER NOT CAUGHT")
    if expect_substring not in caught:
        raise SystemExit(
            f"control {name}: caught on wrong invariant: {caught!r} "
            f"(expected {expect_substring!r})"
        )
    return {"control": name, "caught": caught, "rows_checked": checked}


def independent_reasons_local(data, preferred, flags, tile_mapping, source_id) -> list[str]:
    from check_installed_independent import independent_reasons

    entry = preferred.get(source_id)
    flag = flags.get(source_id, {})
    tile = data.catalog[source_id].tile
    return independent_reasons(
        unique_entries=data.unique_groups.get(source_id, []),
        all_entries=data.all_groups.get(source_id, []),
        preferred=entry,
        unique_conflict=bool(flag.get("unique_numeric_conflict")),
        secure_conflict=bool(flag.get("secure_all_conflict")),
        lephare_type=data.lephare_type.get(source_id),
        assigned_split=tile_mapping.get(tile, "unassigned"),
    )


def tamper_remove_category(products: Path, data) -> None:
    path = products / "sources.jsonl"
    records = load_jsonl(path)
    for record in records:
        reasons = record["exclusion_reasons"]
        if "no_broad_line_or_photometric_qso_evidence" in reasons:
            record["exclusion_reasons"] = [
                reason
                for reason in reasons
                if reason != "no_broad_line_or_photometric_qso_evidence"
            ]
            target = record["catalog_id"]
            break
    else:
        raise SystemExit("control fixture: no source with the target reason")
    write_jsonl(path, records)
    print(f"  tamper: removed reason category from source {target}")


def tamper_association(products: Path, data) -> None:
    path = products / "measurements.jsonl"
    records = load_jsonl(path)
    for record in records:
        if record["association_status"] == "associated":
            record["resolved_catalog_id"] = (
                record["resolved_catalog_id"] + 1
            )
            target = record["id_specz"]
            break
    else:
        raise SystemExit("control fixture: no associated measurement")
    write_jsonl(path, records)
    print(f"  tamper: altered resolved catalog id of entry {target}")


def tamper_promote_a_entry(products: Path, data) -> None:
    path = products / "sources.jsonl"
    records = load_jsonl(path)
    a_entries = None
    for record in records:
        if record["population_a"]:
            a_entries = [
                entry for entry in data.all_groups.get(record["catalog_id"], [])
            ]
            if a_entries:
                record["preferred_id_specz"] = a_entries[0].id_specz
                record["preferred_reported_z"] = a_entries[0].specz
                record["population_a"] = False
                target = record["catalog_id"]
                break
    else:
        raise SystemExit("control fixture: no population A source")
    write_jsonl(path, records)
    print(f"  tamper: promoted an _all entry to preferred for A source {target}")


def tamper_erase_conflict(products: Path, data) -> None:
    path = products / "sources.jsonl"
    records = load_jsonl(path)
    for record in records:
        if record["secure_all_conflict"]:
            record["secure_all_conflict"] = False
            record["conflict_witnesses"]["secure_all"] = []
            target = record["catalog_id"]
            break
    else:
        raise SystemExit("control fixture: no secure conflict source")
    write_jsonl(path, records)
    print(f"  tamper: erased secure conflict at source {target}")


def tamper_tied_preferred(products: Path, data) -> None:
    path = products / "sources.jsonl"
    records = load_jsonl(path)
    for record in records:
        if record["preferred_tie"] and len(record["preferred_tied_ids"]) >= 2:
            tied = record["preferred_tied_ids"]
            higher = max(tied)
            if record["preferred_id_specz"] != higher:
                entry = data.unique_by_id[higher]
                record["preferred_id_specz"] = higher
                record["preferred_reported_z"] = entry.specz
                record["preferred_flag"] = entry.flag
                record["preferred_confidence"] = entry.confidence_level
                target = record["catalog_id"]
                break
    else:
        raise SystemExit("control fixture: no tied preferred source")
    write_jsonl(path, records)
    print(f"  tamper: switched tied preferred entry at source {target}")


def tamper_move_split(products: Path, data) -> None:
    path = products / "sources.jsonl"
    records = load_jsonl(path)
    for record in records:
        if record["assigned_split"] == "development":
            record["assigned_split"] = "holdout"
            target = record["catalog_id"]
            break
    else:
        raise SystemExit("control fixture: no development source")
    write_jsonl(path, records)
    print(f"  tamper: moved source {target} to holdout")


def main() -> None:
    if not all(os.environ.get(name) for name in ADMIN_ENV_NAMES):
        raise SystemExit("negative controls require the scoped Doppler admin environment")
    paths = ss_config.resolve_paths()
    data = ssv.load_snapshot_data(paths=paths)
    preferred = ssv.preferred_entry_independent(data)
    flags = ssv.conflict_flags_independent(data)
    tile_mapping = independent_tile_map()
    finalize = json.loads(
        (paths.staging_dir / "products" / "finalize-summary.json").read_text(encoding="utf-8")
    )
    run_id = finalize["run_id"]
    controls = [
        ("remove_category", tamper_remove_category, "reasons at source"),
        ("alter_association", tamper_association, "resolved id"),
        ("promote_a_entry", tamper_promote_a_entry, "preferred"),
        ("erase_secure_conflict", tamper_erase_conflict, "flag secure_all_conflict"),
        ("change_tied_preferred", tamper_tied_preferred, "preferred"),
        ("move_between_splits", tamper_move_split, "split"),
    ]
    results = []
    for name, tamper, expect in controls:
        print(f"control {name}:", flush=True)
        results.append(
            run_control(
                name,
                tamper,
                expect_substring=expect,
                data=data,
                preferred=preferred,
                flags=flags,
                tile_mapping=tile_mapping,
                run_id=run_id,
            )
        )
    print(json.dumps({"controls": results}, indent=2))
    output = paths.staging_dir / "negative-controls-5-7.json"
    output.write_text(json.dumps({"controls": results}, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(output)}, indent=2))


if __name__ == "__main__":
    main()
