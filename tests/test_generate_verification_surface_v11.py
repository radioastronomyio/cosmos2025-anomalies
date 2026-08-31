#!/usr/bin/env python3
"""
Script Name  : test_generate_verification_surface_v11.py
Description  : Test the offline ETL v2 verification-surface compiler
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-18
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies
"""

from __future__ import annotations

import ast
import csv
import os
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etl import generate_verification_surface_v11 as module  # noqa: E402
from src.etl import generate_conformance_v11  # noqa: E402
from src.etl import generate_schema_v11  # noqa: E402
from src.etl import load_dictionary  # noqa: E402

CONFIG_PATH = REPO_ROOT / "configs/data_paths.yaml"


def test_verification_surface_compiler_module_exists() -> None:
    """Gate 3.13 begins with an importable offline compiler."""
    assert (REPO_ROOT / "src/etl/generate_verification_surface_v11.py").is_file()


def test_historical_dictionary_spec_path_is_separate_from_archive_locator() -> None:
    """Closeout cannot rewrite the sealed dictionary's original provenance."""
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["semantic_sources"]["etl_v2_spec"] == (
        "/opt/agents/repos/spec/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
    )
    assert config["verification_surface"]["central_spec_archive"] == (
        "/opt/agents/repos/spec/2026-08/"
        "2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
    )


def test_exact_evidence_paths_resolve_under_repository() -> None:
    """Every evidence input and the one output must be repository-bound."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    assert paths.dictionary == REPO_ROOT / "data/dictionary/columns-v11.csv"
    assert paths.worklog == REPO_ROOT / (
        "work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md"
    )
    assert paths.output == REPO_ROOT / "docs/research/etl-v2-verification.md"
    assert paths.science_opportunities == REPO_ROOT / (
        "docs/research/science-opportunities.md"
    )
    assert paths.central_spec == Path(
        "/opt/agents/repos/spec/2026-08/"
        "2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
    )
    assert paths.central_spec_read == Path(
        "/opt/agents/repos/spec/2026-08-16-cosmos2025-spec-p2r-03-etl-v2-mirror.md"
    )


def test_central_spec_archive_transition_selects_exactly_one_regular_file(
    tmp_path: Path,
) -> None:
    """Pre-closeout active and post-closeout archive states are both exact."""
    active = tmp_path / "active.md"
    archive = tmp_path / "2026-08" / "archived.md"
    archive.parent.mkdir()

    active.write_bytes(b"sealed spec\n")
    assert module.select_central_spec_read_path(archive, active) == active

    active.rename(archive)
    assert module.select_central_spec_read_path(archive, active) == archive

    active.write_bytes(b"duplicate\n")
    with pytest.raises(ValueError, match="central spec lifecycle"):
        module.select_central_spec_read_path(archive, active)

    active.unlink()
    archive.unlink()
    with pytest.raises(ValueError, match="central spec lifecycle"):
        module.select_central_spec_read_path(archive, active)

    active.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="central spec lifecycle"):
        module.select_central_spec_read_path(archive, active)


def test_post_archive_simulation_keeps_all_four_checks_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Archive bytes preserve dictionary cells and every generated check."""
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    historical = Path(config["semantic_sources"]["etl_v2_spec"])
    simulated_active = tmp_path / "active" / historical.name
    simulated_archive = tmp_path / "2026-08" / historical.name
    simulated_archive.parent.mkdir()
    simulated_archive.write_bytes(historical.read_bytes())
    config_path = tmp_path / "data_paths.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    assert not simulated_active.exists()
    selected_archive = load_dictionary._select_etl_v2_spec_read_path(
        {"verification_surface": {"central_spec_archive": str(simulated_archive)}},
        simulated_active,
    )
    assert selected_archive[0] == simulated_archive
    monkeypatch.setattr(
        load_dictionary,
        "_select_etl_v2_spec_read_path",
        lambda _config, observed: (
            selected_archive
            if observed == historical
            else (_ for _ in ()).throw(AssertionError("historical locator drift"))
        ),
    )
    regenerated, _ = load_dictionary.build_dictionary(config_path)
    with Path(config["dictionary"]["columns_v11"]).open(
        newline="", encoding="utf-8"
    ) as handle:
        tracked = list(csv.DictReader(handle))
    semantic_fields = load_dictionary.CSV_FIELDS[:23]
    assert [
        {field: str(row[field]) for field in semantic_fields} for row in regenerated
    ] == [{field: row[field] for field in semantic_fields} for row in tracked]

    schema_rows = generate_schema_v11.read_dictionary(
        Path(config["dictionary"]["columns_v11"])
    )
    generate_schema_v11.write_or_check(
        schema_rows,
        Path(config["dictionary"]["schema_v11_sql"]),
        check=True,
    )
    conformance_rows = generate_conformance_v11._read_dictionary(
        Path(config["dictionary"]["columns_v11"])
    )
    generate_conformance_v11.write_or_check(
        conformance_rows,
        Path(config["dictionary"]["conformance_cases_v11"]),
        check=True,
    )

    monkeypatch.setattr(
        module,
        "select_central_spec_read_path",
        lambda _archive, _active: simulated_archive,
    )
    result = module.run_generation(config_path, check=True)
    assert result["status"] == "passed"
    assert result["mode"] == "check"


@pytest.mark.parametrize("field", ("columns_v11", "cumulative_worklog", "output"))
def test_evidence_paths_reject_redirects(
    tmp_path: Path, field: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A config edit cannot redirect sealed evidence or generated output."""
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    if field == "columns_v11":
        config["dictionary"][field] = str(tmp_path / "outside.csv")
    else:
        config["verification_surface"][field] = str(tmp_path / "outside.md")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="verification evidence path"):
        module.resolve_evidence_paths(path, repo_root=REPO_ROOT)


@pytest.mark.parametrize("kind", ("symlink", "dangling"))
def test_stable_reader_rejects_links(tmp_path: Path, kind: str) -> None:
    """Evidence reads cannot follow a final-path link."""
    target = tmp_path / "target"
    if kind == "symlink":
        target.write_bytes(b"tracked evidence\n")
    link = tmp_path / "evidence"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="regular tracked evidence"):
        module.read_stable_regular_bytes(link)


def test_dictionary_evidence_has_exact_distributions_and_appendices() -> None:
    """All Gate 3.13 dictionary claims derive from all 1,416 sealed rows."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    evidence = module.extract_dictionary_evidence(paths.dictionary)
    assert (
        evidence.row_count,
        evidence.native_count,
        evidence.metadata_count,
        evidence.master_native_count,
    ) == (1_416, 1_403, 13, 1_349)
    assert evidence.description_counts == {
        "verified": 1_150,
        "pattern_expanded": 204,
        "undocumented_upstream": 49,
        "project_derived": 13,
    }
    assert evidence.unit_counts == {"provenanced": 586, "unknown": 830}
    assert evidence.semantic_counts == {"provenanced": 15, "absent": 1_401}
    assert evidence.null_counts == {"none": 1_108, "nan": 305, "fits_mask": 3}
    assert (evidence.documented_fields, evidence.documented_values) == (1, 1)
    assert evidence.candidate_fields == 476
    assert len(evidence.gaps) == 49
    assert len(evidence.candidates) == 793
    assert Counter(item.value for item in evidence.candidates) == {
        -999: 451,
        999: 318,
        -99: 23,
        99: 1,
    }


def test_dictionary_mutation_breaks_seal(tmp_path: Path) -> None:
    """Even count-preserving evidence drift cannot enter the report."""
    rows = (REPO_ROOT / "data/dictionary/columns-v11.csv").read_text(encoding="utf-8")
    mutated = tmp_path / "columns-v11.csv"
    mutated.write_text(rows.replace("verified", "drifted", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="dictionary seal"):
        module.extract_dictionary_evidence(mutated)


def test_worklog_evidence_extracts_unique_numeric_anchors() -> None:
    """Operational claims come from tracked gate records, not spec assertions."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    evidence = module.extract_worklog_evidence(paths.worklog)
    assert evidence.values == {
        "manifest_rows": 155,
        "consumed_inputs": 16,
        "master_tables": 7,
        "master_rows": 784_016,
        "master_native_fields": 1_349,
        "fidelity_sample": 5_000,
        "fidelity_mismatches": 0,
        "schema_columns": 1_429,
        "constraints": 192,
        "arrays": 166,
        "reconciled_cases": 1_416,
        "sampled_records": 201_678,
        "row_column_comparisons": 28_063_492,
        "array_element_comparisons": 16_600_000,
        "value_mismatches": 0,
        "analyst_select_tables": 12,
        "analyst_denials": 72,
        "specz_rows": 261_975,
        "specz_join": 24_364,
        "specz_prior": 37_219,
        "specz_difference": -12_855,
        "flags_3_4": 183_221,
        "flag_9": 2_326,
        "master_matrix_selects": 1,
        "master_matrix_denials": 11,
        "supplement_matrix_selects": 4,
        "supplement_matrix_denials": 24,
        "role_attributes": 7,
        "role_memberships": 0,
        "role_ownership": 0,
        "handoff_mode": 600,
        "handoff_names": 5,
        "secret_values": 0,
        "admin_session_transport": 1,
        "direct_analyst_auth": 0,
        "hba_pending": 1,
        "analyst_role": 1,
    }
    assert len(evidence.provenance_rows) == 11
    assert len(evidence.quality_flags) == 17
    assert sum(evidence.quality_flags.values()) == 261_975
    assert evidence.v1_fingerprint == (
        "82fb7e09f21253f2e9b78e8232c43b737008aa4bfb44daf28640463bea82abe7"
    )
    assert all(item.source_locator.startswith("L") for item in evidence.sources)


def test_worklog_anchor_mutation_is_rejected(tmp_path: Path) -> None:
    """A missing unique runtime fact must halt instead of falling back to priors."""
    original = (
        REPO_ROOT / ("work-logs/2026-08-16-cosmos2025-worklog-p2r-03-etl-v2-mirror.md")
    ).read_text(encoding="utf-8")
    mutated = tmp_path / "worklog.md"
    mutated.write_text(
        original.replace("28,063,492 row-column comparisons", "missing fact", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="worklog evidence anchor"):
        module.extract_worklog_evidence(mutated)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("mode `0600`", "mode `0644`"),
        ("NOBYPASSRLS", "BYPASSRLS"),
        ("effective identity to `cosmos2025_v11_ro`", "effective identity to `drift`"),
        ("No value, password, password hash", "One value, password, password hash"),
        ("operator explicitly approved this transport", "transport not approved"),
    ),
)
def test_security_worklog_anchor_drift_is_rejected(
    tmp_path: Path, old: str, new: str
) -> None:
    path = REPO_ROOT / module.WORKLOG_RELATIVE
    mutated = tmp_path / "worklog.md"
    mutated.write_text(path.read_text().replace(old, new, 1))
    with pytest.raises(ValueError, match="worklog evidence anchor"):
        module.extract_worklog_evidence(mutated)


def test_cross_artifact_conformance_and_manifest_boundaries_reject_drift(
    tmp_path: Path,
) -> None:
    """Dictionary cases and provenance must join exact generated/manifest facts."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    dictionary = module.extract_dictionary_evidence(paths.dictionary)
    worklog = module.extract_worklog_evidence(paths.worklog)
    module.validate_conformance_projection(paths, dictionary)
    module.validate_manifest_boundary(paths, worklog)

    changed_dictionary = tmp_path / "columns.csv"
    changed_dictionary.write_text(
        paths.dictionary.read_text().replace(
            "HDU 1 [PHOTOMETRY HOTCOLD AND SE++]",
            "HDU 1 [DRIFT]",
            1,
        )
    )
    with pytest.raises(ValueError, match="conformance projection"):
        module.validate_conformance_projection(
            replace(paths, dictionary=changed_dictionary), dictionary
        )

    changed_manifest = tmp_path / "manifest.csv"
    changed_manifest.write_text(
        paths.manifest.read_text().replace(
            "878c318e22780b73742940c7b8807f2bbbe210ead51472706bbe0f43923e618f",
            "0" * 64,
            1,
        )
    )
    with pytest.raises(ValueError, match="manifest provenance"):
        module.validate_manifest_boundary(
            replace(paths, manifest=changed_manifest), worklog
        )


def _evidence_item() -> module.EvidenceItem:
    return module.EvidenceItem(
        label="sealed rows",
        value=1_416,
        source_path="data/dictionary/columns-v11.csv",
        source_locator="rows 2-1417",
    )


def _finding() -> module.Finding:
    return module.Finding(
        finding_id="V13-01",
        statement="The mirror contract contains 1,416 dictionary rows.",
        evidence=(_evidence_item(),),
        closed_question="Accept the 1,416-row mirror boundary? Yes/No.",
        recommendation="Accept the sealed mirror boundary.",
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ({"finding_id": "bad"}, "finding ID"),
        ({"statement": "No numeric observation."}, "numeric statement"),
        ({"statement": "Line one 1.\nLine two."}, "one-line statement"),
        ({"evidence": ()}, "evidence"),
        ({"closed_question": "Open question?"}, "Yes/No"),
        ({"recommendation": ""}, "recommendation"),
    ),
)
def test_finding_contract_rejects_invalid_shape(
    mutation: dict[str, object], message: str
) -> None:
    """Every finding is numeric, sourced, closed, and actionable."""
    with pytest.raises(ValueError, match=message):
        module.validate_findings((replace(_finding(), **mutation),))


def test_finding_contract_rejects_duplicate_ids_and_unsafe_evidence() -> None:
    """IDs are unique and evidence cannot contain untracked or secret text."""
    with pytest.raises(ValueError, match="duplicate finding ID"):
        module.validate_findings((_finding(), _finding()))
    unsafe = replace(
        _finding(),
        evidence=(replace(_evidence_item(), value="PGPASSWORD=secret"),),
    )
    with pytest.raises(ValueError, match="numeric evidence"):
        module.validate_findings((unsafe,))


def test_build_findings_covers_nine_verification_and_five_deferred_questions() -> None:
    """The approval surface has the exact governed finding/question inventory."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    findings = module.build_findings(
        module.extract_dictionary_evidence(paths.dictionary),
        module.extract_worklog_evidence(paths.worklog),
        module.extract_policy_evidence(paths),
    )
    module.validate_findings(findings)
    assert [item.finding_id for item in findings] == [
        *(f"V13-{index:02d}" for index in range(1, 10)),
        *(f"D13-{index:02d}" for index in range(1, 6)),
    ]
    deferred = findings[9:]
    assert all(item.deferred for item in deferred)
    assert all("Deferred to T_A v2" in item.recommendation for item in deferred)
    assert {
        "chi2_ratio",
        "SFR censoring",
        "analysis-sample",
        "spec-z calibration/validation",
        "morphology contextual features",
    } <= {item.topic for item in deferred}


def test_complete_appendices_validate_exact_order_and_counts() -> None:
    """All four appendices preserve every sealed/observed record in order."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    dictionary = module.extract_dictionary_evidence(paths.dictionary)
    worklog = module.extract_worklog_evidence(paths.worklog)
    module.validate_appendices(dictionary, worklog)
    assert (len(dictionary.gaps), len(dictionary.candidates)) == (49, 793)
    assert len(worklog.provenance_rows) == 11
    assert len(worklog.quality_flags) == 17
    assert sum(worklog.quality_flags.values()) == 261_975


@pytest.mark.parametrize(
    "mutation",
    (
        "gap_delete",
        "gap_duplicate",
        "gap_reorder",
        "gap_field",
        "candidate_delete",
        "candidate_duplicate",
        "candidate_reorder",
        "candidate_field",
        "provenance_delete",
        "provenance_duplicate",
        "provenance_reorder",
        "provenance_field",
        "flag_delete",
        "flag_add",
        "flag_reorder",
        "flag_redistribute",
    ),
)
def test_complete_appendices_reject_delete_duplicate_reorder_or_mutation(
    mutation: str,
) -> None:
    """A transcription change in any appendix halts report generation."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    dictionary = module.extract_dictionary_evidence(paths.dictionary)
    worklog = module.extract_worklog_evidence(paths.worklog)
    if mutation == "gap_delete":
        dictionary = replace(dictionary, gaps=dictionary.gaps[:-1])
    elif mutation == "gap_duplicate":
        dictionary = replace(dictionary, gaps=dictionary.gaps + (dictionary.gaps[0],))
    elif mutation == "gap_reorder":
        dictionary = replace(
            dictionary,
            gaps=(dictionary.gaps[1], dictionary.gaps[0]) + dictionary.gaps[2:],
        )
    elif mutation == "gap_field":
        dictionary = replace(
            dictionary,
            gaps=(replace(dictionary.gaps[0], source_column="drift"),)
            + dictionary.gaps[1:],
        )
    elif mutation == "candidate_delete":
        dictionary = replace(dictionary, candidates=dictionary.candidates[:-1])
    elif mutation == "candidate_duplicate":
        dictionary = replace(
            dictionary, candidates=dictionary.candidates + (dictionary.candidates[0],)
        )
    elif mutation == "candidate_reorder":
        dictionary = replace(
            dictionary,
            candidates=(dictionary.candidates[1], dictionary.candidates[0])
            + dictionary.candidates[2:],
        )
    elif mutation == "candidate_field":
        dictionary = replace(
            dictionary,
            candidates=(replace(dictionary.candidates[0], denominator=1),)
            + dictionary.candidates[1:],
        )
    elif mutation == "provenance_delete":
        worklog = replace(worklog, provenance_rows=worklog.provenance_rows[:-1])
    elif mutation == "provenance_duplicate":
        worklog = replace(
            worklog,
            provenance_rows=worklog.provenance_rows + (worklog.provenance_rows[0],),
        )
    elif mutation == "provenance_reorder":
        worklog = replace(
            worklog,
            provenance_rows=(worklog.provenance_rows[1], worklog.provenance_rows[0])
            + worklog.provenance_rows[2:],
        )
    elif mutation == "provenance_field":
        worklog = replace(
            worklog,
            provenance_rows=(replace(worklog.provenance_rows[0], load_xmin=1),)
            + worklog.provenance_rows[1:],
        )
    elif mutation == "flag_delete":
        worklog = replace(
            worklog, quality_flags=dict(list(worklog.quality_flags.items())[:-1])
        )
    elif mutation == "flag_add":
        worklog = replace(worklog, quality_flags={**worklog.quality_flags, 99: 0})
    elif mutation == "flag_reorder":
        worklog = replace(
            worklog, quality_flags=dict(reversed(worklog.quality_flags.items()))
        )
    else:
        changed = dict(worklog.quality_flags)
        changed[-99] += 1
        changed[-2] -= 1
        worklog = replace(worklog, quality_flags=changed)
    with pytest.raises(ValueError, match="appendix"):
        module.validate_appendices(dictionary, worklog)


def test_renderer_has_complete_markers_sources_and_blank_decisions() -> None:
    """The deterministic Markdown exposes complete evidence and no disposition."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    dictionary = module.extract_dictionary_evidence(paths.dictionary)
    worklog = module.extract_worklog_evidence(paths.worklog)
    policy = module.extract_policy_evidence(paths)
    findings = module.build_findings(dictionary, worklog, policy)
    decisions = module.operator_decisions()
    rendered = module.render_verification_report(
        findings, dictionary, worklog, policy, decisions
    ).decode("utf-8")
    assert rendered.count("<!-- finding:") == 14
    assert rendered.count("<!-- gap:") == 49
    assert rendered.count("<!-- candidate:") == 793
    assert rendered.count("<!-- provenance:") == 11
    assert rendered.count("<!-- flag:") == 17
    assert all(item.disposition == "" for item in decisions)
    assert "| MetaMCP redirect | Recommended |  |" in rendered
    assert "| T_A v2 dispatch | Recommended |  |" in rendered
    assert "cross-HDU ordinal contract" in rendered
    assert "nonmaterialized" in rendered
    assert "direct analyst network authentication was not exercised" in rendered
    assert "PGSQL01_COSMOS2025_V11_PASSWORD=" not in rendered
    assert rendered.startswith("<!--\n---\n")
    frontmatter = rendered.split("---\n", 2)[1]
    metadata = yaml.safe_load(frontmatter)
    assert metadata["status"] == "Draft"
    assert metadata["tags"][0] == {"type": "report"}


def test_operator_decisions_and_deferred_questions_cannot_be_self_approved() -> None:
    """Successful evidence never answers either operator decision or T_A policy."""
    decisions = module.operator_decisions()
    with pytest.raises(ValueError, match="operator disposition"):
        module.validate_operator_decisions(
            (replace(decisions[0], disposition="Yes"), decisions[1])
        )
    with pytest.raises(ValueError, match="deferred"):
        module.validate_findings((replace(_finding(), deferred=True),))


def test_finding_validator_binds_numbers_paths_and_all_text_surfaces() -> None:
    """Numbers require exact evidence and no surface can carry secret-like text."""
    with pytest.raises(ValueError, match="number lacks exact evidence"):
        module.validate_findings(
            (replace(_finding(), statement="The boundary has 999 rows."),)
        )
    outside = replace(_evidence_item(), source_path="outside/untracked")
    with pytest.raises(ValueError, match="locator"):
        module.validate_findings((replace(_finding(), evidence=(outside,)),))
    for field in ("statement", "closed_question", "recommendation"):
        with pytest.raises(ValueError, match="unsafe"):
            module.validate_findings(
                (replace(_finding(), **{field: "PGPASSWORD=secret 1 Yes/No."}),)
            )


def test_candidate_rendering_keeps_denominator_and_future_review_wording() -> None:
    """Candidate evidence is quantitative and never becomes a present cleaning rule."""
    paths = module.resolve_evidence_paths(CONFIG_PATH, repo_root=REPO_ROOT)
    dictionary = module.extract_dictionary_evidence(paths.dictionary)
    assert all(item.denominator > 0 for item in dictionary.candidates)
    rendered = module.render_verification_report(
        module.build_findings(
            dictionary,
            module.extract_worklog_evidence(paths.worklog),
            module.extract_policy_evidence(paths),
        ),
        dictionary,
        module.extract_worklog_evidence(paths.worklog),
        module.extract_policy_evidence(paths),
        module.operator_decisions(),
    ).decode()
    candidate_section = rendered.split("### Finite candidate observations", 1)[1].split(
        "### Dual-hash provenance", 1
    )[0]
    assert "Denominator" in candidate_section
    assert "future cleaning rule requires scientific review" in candidate_section
    assert "documented upstream" not in candidate_section
    findings = module.build_findings(
        dictionary,
        module.extract_worklog_evidence(paths.worklog),
        module.extract_policy_evidence(paths),
    )
    relabeled = replace(findings[2], recommendation="All 793 candidates are cleaned.")
    with pytest.raises(ValueError, match="relabels"):
        module.validate_findings(findings[:2] + (relabeled,) + findings[3:])


def test_atomic_writer_and_check_are_byte_exact(tmp_path: Path) -> None:
    """Default replacement and read-only check preserve exact generated bytes."""
    output = tmp_path / "report.md"
    output.write_bytes(b"old\n")
    module.write_report_atomic(output, b"new\n")
    assert output.read_bytes() == b"new\n"
    module.write_or_check(output, b"new\n", check=True)
    with pytest.raises(ValueError, match="byte identity"):
        module.write_or_check(output, b"different\n", check=True)
    assert output.read_bytes() == b"new\n"


def test_replace_success_then_raise_is_classified_exact_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An ambiguous replace return is classified without a second write."""
    output = tmp_path / "report.md"
    output.write_bytes(b"old\n")
    real_replace = os.replace

    def replace_then_raise(source: Path, destination: Path) -> None:
        real_replace(source, destination)
        raise RuntimeError("synthetic secret replacement failure")

    monkeypatch.setattr(module.os, "replace", replace_then_raise)
    with pytest.raises(module.ReportOutputRetainedError, match="retained exact"):
        module.write_report_atomic(output, b"new\n")
    assert output.read_bytes() == b"new\n"


@pytest.mark.parametrize(
    ("stage", "retained"),
    (
        ("write", False),
        ("flush", False),
        ("file_fsync", False),
        ("replace", False),
        ("replace_return", True),
        ("parent_fsync", True),
        ("post_read", True),
    ),
)
def test_atomic_writer_classifies_every_failure_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    retained: bool,
) -> None:
    """Every writer-stage failure has one exact output and cleanup state."""
    output = tmp_path / "report.md"
    output.write_bytes(b"reviewed-before\n")
    generated = b"generated-complete\n"
    real_fdopen = module.os.fdopen

    class FailingFile:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            self.handle.__enter__()
            return self

        def __exit__(self, exc_type, exc, traceback):
            return self.handle.__exit__(exc_type, exc, traceback)

        def write(self, data):
            if stage == "write":
                raise OSError("synthetic write failure")
            return self.handle.write(data)

        def flush(self):
            if stage == "flush":
                raise OSError("synthetic flush failure")
            return self.handle.flush()

        def fileno(self):
            return self.handle.fileno()

    monkeypatch.setattr(
        module.os,
        "fdopen",
        lambda descriptor, mode: FailingFile(real_fdopen(descriptor, mode)),
    )
    if stage == "replace":
        monkeypatch.setattr(
            module.os,
            "replace",
            lambda *_args: (_ for _ in ()).throw(OSError("replace")),
        )
    elif stage == "replace_return":
        real_replace = module.os.replace

        def replace_then_raise(source, destination):
            real_replace(source, destination)
            raise OSError("replace return")

        monkeypatch.setattr(module.os, "replace", replace_then_raise)
    elif stage in {"file_fsync", "parent_fsync"}:
        fsync_calls = 0

        def fail_fsync(_descriptor):
            nonlocal fsync_calls
            fsync_calls += 1
            wanted = 1 if stage == "file_fsync" else 2
            if fsync_calls == wanted:
                raise OSError("fsync")

        monkeypatch.setattr(module.os, "fsync", fail_fsync)
    elif stage == "post_read":
        real_read = module.read_stable_regular_bytes
        calls = 0

        def fail_first(path):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("post read")
            return real_read(path)

        monkeypatch.setattr(module, "read_stable_regular_bytes", fail_first)

    error = module.ReportOutputRetainedError if retained else OSError
    with pytest.raises(error):
        module.write_report_atomic(output, generated)
    assert output.read_bytes() == (generated if retained else b"reviewed-before\n")
    assert list(tmp_path.glob(".report.md.*.tmp")) == []


def test_atomic_writer_reports_unvalidated_when_classification_cannot_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "report.md"
    output.write_bytes(b"old\n")
    monkeypatch.setattr(module, "read_stable_regular_bytes", lambda _path: b"drift")
    with pytest.raises(module.ReportOutputUnvalidatedError):
        module.write_report_atomic(output, b"new\n")


def test_run_generation_is_offline_and_returns_allowlisted_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Orchestration compiles tracked evidence without DB or source holdings."""
    monkeypatch.setattr(module, "write_or_check", lambda *_args, **_kwargs: None)
    result = module.run_generation(CONFIG_PATH, check=False)
    assert result == {
        "mode": "generate",
        "status": "passed",
        "findings": 14,
        "gaps": 49,
        "candidates": 793,
        "provenance_rows": 11,
        "quality_flags": 17,
        "source_reads": 0,
        "database_queries": 0,
        "persistent_mutation": False,
        "dispositions_blank": True,
        "report_bytes": result["report_bytes"],
        "report_sha256": result["report_sha256"],
    }
    assert result["report_bytes"] > 100_000
    assert len(result["report_sha256"]) == 64


def test_cli_redacts_exception_text_and_success_output_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every CLI failure exposes only stage and exception class."""
    monkeypatch.setattr(
        module,
        "run_generation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("PGPASSWORD=do-not-render")
        ),
    )
    assert module.main([]) == 1
    captured = capsys.readouterr()
    assert "PGPASSWORD" not in captured.err
    assert "stage=generate exception=RuntimeError" in captured.err

    monkeypatch.setattr(module, "run_generation", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        module,
        "_emit_result",
        lambda _result: (_ for _ in ()).throw(BrokenPipeError("secret output")),
    )
    assert module.main([]) == 1
    captured = capsys.readouterr()
    assert "secret output" not in captured.err
    assert "exception=BrokenPipeError" in captured.err


def test_direct_help_and_entrypoint_at_physical_eof() -> None:
    """Direct help is evidence-free and main cannot run before definitions."""
    script = REPO_ROOT / "src/etl/generate_verification_surface_v11.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    tree = ast.parse(script.read_text(encoding="utf-8"))
    assert isinstance(tree.body[-1], ast.If)
    assert all(
        not isinstance(node, (ast.FunctionDef, ast.ClassDef))
        for node in tree.body[tree.body.index(tree.body[-1]) + 1 :]
    )


def test_compiler_call_graph_excludes_live_source_and_remote_capabilities() -> None:
    """The Gate 3.13 compiler is mechanically offline and tracked-only."""
    script = (REPO_ROOT / "src/etl/generate_verification_surface_v11.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(script)
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imported.intersection(
        {
            "astropy",
            "numpy",
            "pandas",
            "pyarrow",
            "psycopg",
            "subprocess",
        }
    )
    forbidden_text = (
        "astropy",
        "fits.open",
        "psycopg",
        "doppler",
        "subprocess",
        "/mnt/nvme01",
    )
    assert not [token for token in forbidden_text if token in script]
    sql_literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.lstrip()
        .upper()
        .startswith(
            ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "DROP ")
        )
    ]
    assert sql_literals == []
    assert "internal-files/cosmos2025-v11.env" in script
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "open"
        and any(
            isinstance(argument, ast.Constant)
            and argument.value == "internal-files/cosmos2025-v11.env"
            for argument in node.args
        )
        for node in ast.walk(tree)
    )
