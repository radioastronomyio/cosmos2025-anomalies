"""Phase driver for the P2R-05 build pipeline (staging outputs only).

Phases map to gates: ``--phase build`` (5.4) writes the measurement audit
and pre-split source summaries; ``--phase finalize`` (5.5) freezes the tile
map, finalizes eligibility, and computes the three product content digests;
``--phase identity`` prints the deterministic run identity for inspection.
Installation to the database lives in ``install.py`` and consumes only the
verified staging artifacts this driver produces.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.specz_science import build as ss_build  # noqa: E402
from src.features.specz_science import canonical as ss_canonical  # noqa: E402
from src.features.specz_science import config as ss_config  # noqa: E402
from src.features.specz_science import policy as ss_policy  # noqa: E402
from src.features.specz_science import splits as ss_splits  # noqa: E402
from src.features.specz_science import verify as ssv  # noqa: E402


def resolve_run_identity(paths: ss_config.SpeczSciencePaths) -> dict[str, object]:
    """Deterministic identity over policy, snapshot, and implementation."""
    snapshot_manifest = json.loads(
        (paths.snapshot_dir / "manifest.json").read_text(encoding="utf-8")
    )
    identity = ss_canonical.build_run_identity(
        policy_digest=ss_policy.policy_semantic_digest(paths.policy_path),
        snapshot_manifest_digest=ss_canonical.digest_bytes(
            (paths.snapshot_dir / "manifest.json").read_bytes()
        ),
        snapshot_file_digests={
            item["table"]: item["sha256"] for item in snapshot_manifest["files"]
        },
        implementation=ss_canonical.implementation_digest(Path(__file__).parent),
    )
    return identity


def phase_build(paths: ss_config.SpeczSciencePaths, policy) -> dict[str, object]:
    """Gate 5.4: measurement audit and pre-split source summaries."""
    data = ssv.load_snapshot_data(paths=paths)
    identity = resolve_run_identity(paths)
    run_id = ss_canonical.run_id_from_identity(identity)
    out_dir = paths.staging_dir / "products"
    out_dir.mkdir(parents=True, exist_ok=True)
    sentinel = int(
        dict(policy)["association"]["no_association_sentinel"]
    )
    measurements_digest, measurement_rows = ss_canonical.write_jsonl(
        out_dir / "measurements.jsonl",
        ss_build.build_measurement_records(data, run_id=run_id, no_association_sentinel=sentinel),
    )
    sources_digest, source_rows = ss_canonical.write_jsonl(
        out_dir / "sources-presplit.jsonl",
        ss_build.build_source_records(data, run_id=run_id),
    )
    summary = {
        "phase": "build",
        "run_id": run_id,
        "measurement_rows": measurement_rows,
        "source_rows": source_rows,
        "measurements_digest": measurements_digest,
        "sources_presplit_digest": sources_digest,
        "catalog_ids": len(data.catalog_ids),
        "all_entry_ids": len(data.all_by_id),
        "unresolved_identifier_entries": sum(
            1
            for entry in data.all_entries
            if entry.id_cosmos25 is not None
            and entry.id_cosmos25 != sentinel
            and entry.id_cosmos25 not in data.catalog_ids
        ),
    }
    (out_dir / "build-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def phase_finalize(paths: ss_config.SpeczSciencePaths, policy) -> dict[str, object]:
    """Gate 5.5: tile map, finalized eligibility, content digests.

    Regenerates the measurement audit in the same pass so every product
    file carries one run identity: the implementation digest covers the
    verifier modules too, and a build executed before a verifier change
    must not ship under a stale identity.
    """
    data = ssv.load_snapshot_data(paths=paths)
    identity = resolve_run_identity(paths)
    run_id = ss_canonical.run_id_from_identity(identity)
    mapping = ss_splits.tile_map(policy)
    if ss_splits.canonical_tile_map_digest(mapping) != ss_splits.canonical_tile_map_digest(
        ss_splits.tile_map(policy)
    ):
        raise SystemExit("finalize FAILED: tile map not deterministic")
    unassigned_label = dict(policy)["splits"]["unassigned_label"]
    salt = dict(policy)["splits"]["salt"]
    sentinel = int(dict(policy)["association"]["no_association_sentinel"])
    out_dir = paths.staging_dir / "products"
    out_dir.mkdir(parents=True, exist_ok=True)

    measurements_digest, measurement_rows = ss_canonical.write_jsonl(
        out_dir / "measurements.jsonl",
        ss_build.build_measurement_records(
            data, run_id=run_id, no_association_sentinel=sentinel
        ),
    )
    unassigned = 0

    def finalized_records():
        nonlocal unassigned
        for record in ss_build.build_source_records(data, run_id=run_id):
            assigned = ss_splits.assign_tile(
                mapping, data.catalog[record["catalog_id"]].tile
            )
            if assigned == unassigned_label:
                unassigned += 1
            yield ss_build.finalize_eligibility(record, assigned, unassigned_label)

    sources_digest, source_rows = ss_canonical.write_jsonl(
        out_dir / "sources.jsonl", finalized_records()
    )
    splits_digest, split_rows = ss_canonical.write_jsonl(
        out_dir / "splits.jsonl",
        ss_build.build_split_records(
            data, run_id=run_id, tile_mapping=mapping, unassigned_label=unassigned_label, salt=salt
        ),
    )
    if unassigned != 0:
        raise SystemExit(
            f"finalize FAILED: {unassigned} unassigned sources; partition "
            "completion halted for investigation (P-06)"
        )
    content = ss_canonical.content_digest_document(
        measurements=measurements_digest,
        sources=sources_digest,
        splits=splits_digest,
        measurement_rows=measurement_rows,
        source_rows=source_rows,
        split_rows=split_rows,
    )
    summary = {
        "phase": "finalize",
        "run_id": run_id,
        "tile_map": dict(sorted(mapping.items())),
        "tile_map_canonical_digest": ss_splits.canonical_tile_map_digest(mapping),
        "unassigned_sources": unassigned,
        "content_digests": content,
        "eligibility_counts": _eligibility_counts(out_dir / "sources.jsonl"),
    }
    (out_dir / "finalize-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def _eligibility_counts(path: Path) -> dict[str, int]:
    counts = {
        "eligibility_primary_galaxy": 0,
        "eligibility_separate_validation": 0,
        "both_true": 0,
    }
    for record in ss_canonical.read_jsonl(path):
        primary = record["eligibility_primary_galaxy"]
        separate = record["eligibility_separate_validation"]
        counts["eligibility_primary_galaxy"] += bool(primary)
        counts["eligibility_separate_validation"] += bool(separate)
        counts["both_true"] += bool(primary and separate)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("identity", "build", "finalize"), required=True)
    args = parser.parse_args()
    paths = ss_config.resolve_paths()
    policy = ss_policy.load_frozen_policy(paths.policy_path)
    if args.phase == "identity":
        identity = resolve_run_identity(paths)
        print(
            json.dumps(
                {
                    "run_id": ss_canonical.run_id_from_identity(identity),
                    "identity": identity,
                },
                indent=2,
            )
        )
        return
    if args.phase == "build":
        summary = phase_build(paths, policy)
    else:
        summary = phase_finalize(paths, policy)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
