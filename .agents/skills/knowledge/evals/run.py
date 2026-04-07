#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run reusable evals for the $knowledge skill."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Directory for iteration outputs (default: /tmp/knowledge-evals)",
    )
    return parser.parse_args()


def next_iteration_dir(workspace_root: Path) -> Path:
    workspace_root.mkdir(parents=True, exist_ok=True)
    existing = []
    for child in workspace_root.iterdir():
        if child.is_dir() and child.name.startswith("iteration-"):
            suffix = child.name.split("-", 1)[1]
            if suffix.isdigit():
                existing.append(int(suffix))
    return workspace_root / f"iteration-{max(existing, default=0) + 1}"


def run_cmd(cmd, cwd: Path):
    started = time.time()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    duration_ms = int((time.time() - started) * 1000)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_ms": duration_ms,
    }


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def assert_exists(path: Path, message: str):
    return {
        "assertion": message,
        "pass": path.exists(),
        "evidence": str(path),
    }


def assert_equal(actual, expected, message: str):
    return {
        "assertion": message,
        "pass": actual == expected,
        "evidence": {"actual": actual, "expected": expected},
    }


def result_payload(assertions=None, skipped=False, skip_reason=None):
    return {
        "assertions": assertions or [],
        "skipped": skipped,
        "skip_reason": skip_reason,
    }


def grade_fresh_scaffold(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    result = run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    validation = run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "check_knowledge.sh"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "validation.json").write_text(validation["stdout"])
    (case_dir / "with_skill" / "validation.stderr.log").write_text(validation["stderr"])
    validation_summary = json.loads(validation["stdout"])
    assertions = [
        assert_equal(result["returncode"], 0, "The scaffold command exits successfully."),
        assert_exists(repo_dir / ".knowledge", "The .knowledge root is created under the target repo."),
        assert_exists(repo_dir / ".knowledge" / "sources", "The sources layer exists."),
        assert_exists(repo_dir / ".knowledge" / "knowledge", "The knowledge layer exists."),
        assert_exists(repo_dir / ".knowledge" / "rules", "The rules layer exists."),
        assert_exists(
            repo_dir / ".knowledge" / "knowledge" / "structure" / "0000-home.md",
            "The structure home note exists.",
        ),
        assert_exists(
            repo_dir / ".knowledge" / "rules" / "templates" / "literature-note.md",
            "The literature note template exists.",
        ),
        assert_exists(
            repo_dir / ".knowledge" / "rules" / "templates" / "permanent-note.md",
            "The permanent note template exists.",
        ),
        assert_exists(
            repo_dir / ".knowledge" / "rules" / "templates" / "structure-note.md",
            "The structure note template exists.",
        ),
        assert_exists(
            repo_dir / ".knowledge" / "rules" / "templates" / "open-question-note.md",
            "The open-question note template exists.",
        ),
        assert_exists(
            repo_dir / ".knowledge" / "rules" / "templates" / "source-note.md",
            "The source note template exists.",
        ),
        assert_equal(summary["mode"], "apply", "The script summary reports apply mode."),
        {
            "assertion": "The script summary reports non-zero created directories.",
            "pass": summary["created_dirs"] > 0,
            "evidence": summary["created_dirs"],
        },
        {
            "assertion": "The validator accepts the generated workspace.",
            "pass": validation["returncode"] == 0 and validation_summary["valid"] is True,
            "evidence": validation_summary,
        },
    ]
    return result_payload(assertions)


def grade_preserve_existing(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
        ],
        cwd=skill_root,
    )

    user_note = repo_dir / ".knowledge" / "knowledge" / "permanent" / "202604071300-user-note.md"
    user_note.write_text("# User Note\n\nThis should survive refreshes.\n")
    managed_readme = repo_dir / ".knowledge" / "README.md"
    managed_readme.write_text("# Customized README\n\nKeep this version without force.\n")
    custom_rule = repo_dir / ".knowledge" / "rules" / "custom.md"
    custom_rule.write_text("# Custom Rule\n\nUser-authored rule.\n")

    before_user = user_note.read_text()
    before_readme = managed_readme.read_text()
    before_custom = custom_rule.read_text()

    result = run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    assertions = [
        assert_equal(result["returncode"], 0, "The refresh command exits successfully."),
        assert_equal(user_note.read_text(), before_user, "A pre-existing user-authored permanent note remains unchanged."),
        assert_equal(managed_readme.read_text(), before_readme, "A customized managed file remains unchanged without --force-managed."),
        assert_equal(custom_rule.read_text(), before_custom, "A custom rule file remains unchanged."),
        assert_equal(summary["mode"], "apply", "The script summary reports apply mode."),
        {
            "assertion": "The script summary reports skipped files.",
            "pass": summary["skipped_files"] > 0,
            "evidence": summary["skipped_files"],
        },
    ]
    return result_payload(assertions)


def grade_force_managed_refresh(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
        ],
        cwd=skill_root,
    )

    user_note = repo_dir / ".knowledge" / "knowledge" / "permanent" / "202604071300-user-note.md"
    user_note.write_text("# User Note\n\nThis should survive refreshes.\n")
    managed_readme = repo_dir / ".knowledge" / "README.md"
    managed_readme.write_text("# Customized README\n\nReset this with force.\n")
    before_user = user_note.read_text()

    result = run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
            "--force-managed",
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    default_readme_prefix = "# .knowledge"
    assertions = [
        assert_equal(result["returncode"], 0, "The forced refresh command exits successfully."),
        {
            "assertion": "A customized managed file is rewritten to the default content when --force-managed is used.",
            "pass": managed_readme.read_text().startswith(default_readme_prefix),
            "evidence": managed_readme.read_text().splitlines()[:2],
        },
        assert_equal(user_note.read_text(), before_user, "A user-authored permanent note remains unchanged after the forced refresh."),
        assert_equal(summary["mode"], "apply", "The script summary reports apply mode."),
        {
            "assertion": "The script summary reports written files.",
            "pass": summary["written_files"] > 0,
            "evidence": summary["written_files"],
        },
    ]
    return result_payload(assertions)


def grade_validator_detects_damage(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
        ],
        cwd=skill_root,
    )

    missing_file = repo_dir / ".knowledge" / "rules" / "templates" / "source-note.md"
    missing_file.unlink()

    result = run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "check_knowledge.sh"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    missing_path = str(missing_file)
    assertions = [
        {
            "assertion": "The validator exits non-zero for a damaged workspace.",
            "pass": result["returncode"] != 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The validator reports the missing managed file.",
            "pass": missing_path in summary["missing_files"],
            "evidence": summary["missing_files"],
        },
        {
            "assertion": "The validator summary marks the workspace invalid.",
            "pass": summary["valid"] is False,
            "evidence": summary["valid"],
        },
    ]
    return result_payload(assertions)


def copy_fixture(src: Path, dst: Path):
    shutil.copytree(src, dst, dirs_exist_ok=True)


def grade_quality_good_examples(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    fixture_dir = skill_root / "evals" / "files" / "quality-good"
    copy_fixture(fixture_dir, repo_dir)

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "check_note_quality.py"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    assertions = [
        {
            "assertion": "The note-quality checker exits successfully for the good examples.",
            "pass": result["returncode"] == 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The note-quality summary marks the note set valid.",
            "pass": summary["valid"] is True,
            "evidence": summary["valid"],
        },
        {
            "assertion": "The note-quality summary reports five checked notes.",
            "pass": summary["note_count"] == 5,
            "evidence": summary["note_count"],
        },
        {
            "assertion": "The mean quality score is at least 90.",
            "pass": summary["mean_score"] >= 90,
            "evidence": summary["mean_score"],
        },
    ]
    return result_payload(assertions)


def grade_quality_detects_bad_note(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    fixture_dir = skill_root / "evals" / "files" / "quality-bad"
    copy_fixture(fixture_dir, repo_dir)

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "check_note_quality.py"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    note = summary["notes"][0]
    error_text = "\n".join(note["errors"])
    assertions = [
        {
            "assertion": "The note-quality checker exits non-zero for the bad note.",
            "pass": result["returncode"] != 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The note-quality summary marks the note set invalid.",
            "pass": summary["valid"] is False,
            "evidence": summary["valid"],
        },
        {
            "assertion": "The bad note reports an atomicity error.",
            "pass": "too long for an atomic note" in error_text,
            "evidence": note["errors"],
        },
        {
            "assertion": "The bad note reports a link-context or provenance error.",
            "pass": ("Link context should include" in error_text) or ("Missing required section: Provenance." in error_text),
            "evidence": note["errors"],
        },
    ]
    return result_payload(assertions)


def grade_search_finds_relevant_notes(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    fixture_dir = skill_root / "evals" / "files" / "quality-good"
    copy_fixture(fixture_dir, repo_dir)

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "search_knowledge.py"),
            "--path",
            str(repo_dir),
            "--query",
            "atomic notes",
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    top = summary["results"][0] if summary["results"] else {}
    assertions = [
        {
            "assertion": "The search helper exits successfully for a relevant query.",
            "pass": result["returncode"] == 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The search helper returns at least two matches.",
            "pass": summary["total_matches"] >= 2,
            "evidence": summary["total_matches"],
        },
        {
            "assertion": "The top result path contains the atomic-notes topic.",
            "pass": "atomic-notes" in top.get("path", ""),
            "evidence": top.get("path"),
        },
        {
            "assertion": "The top result includes at least one snippet.",
            "pass": len(top.get("snippets", [])) > 0,
            "evidence": top.get("snippets", []),
        },
    ]
    return result_payload(assertions)


def grade_search_can_include_rules(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(
        [
            "bash",
            str(skill_root / "scripts" / "init_knowledge.sh"),
            "--path",
            str(repo_dir),
        ],
        cwd=skill_root,
    )

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "search_knowledge.py"),
            "--path",
            str(repo_dir),
            "--query",
            "provenance",
            "--include-rules",
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    result_paths = [item["path"] for item in summary["results"]]
    assertions = [
        {
            "assertion": "The search helper exits successfully when include-rules is enabled.",
            "pass": result["returncode"] == 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The results contain the provenance rule file.",
            "pass": any(path.endswith(".knowledge/rules/provenance.md") for path in result_paths),
            "evidence": result_paths,
        },
    ]
    return result_payload(assertions)


def grade_search_handles_no_match(skill_root: Path, case_dir: Path):
    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    fixture_dir = skill_root / "evals" / "files" / "quality-good"
    copy_fixture(fixture_dir, repo_dir)

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "search_knowledge.py"),
            "--path",
            str(repo_dir),
            "--query",
            "quantum entanglement",
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    assertions = [
        {
            "assertion": "The search helper exits successfully for an unknown query.",
            "pass": result["returncode"] == 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The search helper returns zero matches.",
            "pass": summary["total_matches"] == 0,
            "evidence": summary["total_matches"],
        },
    ]
    return result_payload(assertions)


def grade_retrieval_style_guidance(skill_root: Path, case_dir: Path):
    skill_text = (skill_root / "SKILL.md").read_text()
    retrieval_ref = (skill_root / "references" / "example-retrieval-workflow.md").read_text()

    assertions = [
        {
            "assertion": "The skill instructions require direct natural prose for retrieval answers.",
            "pass": "answer the topic directly in natural, user-facing prose" in skill_text,
            "evidence": "answer the topic directly in natural, user-facing prose",
        },
        {
            "assertion": "The skill instructions explicitly avoid meta phrases about the notes or knowledge base.",
            "pass": 'Do not frame the response with phrases like "the knowledge base says" or "the current notes suggest"' in skill_text,
            "evidence": 'Do not frame the response with phrases like "the knowledge base says" or "the current notes suggest"',
        },
        {
            "assertion": "The retrieval example uses a Sources used section.",
            "pass": "Sources used:" in retrieval_ref,
            "evidence": "Sources used:",
        },
        {
            "assertion": "The retrieval example cites knowledge/ or rules/ paths instead of .knowledge/ paths.",
            "pass": ("- knowledge/" in retrieval_ref or "- rules/" in retrieval_ref) and ".knowledge/" not in retrieval_ref,
            "evidence": [line for line in retrieval_ref.splitlines() if line.startswith("- ")][:5],
        },
    ]

    write_json(
        case_dir / "with_skill" / "grading.json",
        {
            "id": "retrieval_style_guidance",
            "prompt": "Use $knowledge to answer from stored knowledge in natural prose and cite note files relative to the .knowledge root.",
            "expected_output": "The skill instructions and retrieval example both enforce natural prose, avoid stiff note-system phrasing, and use .knowledge-root-relative source paths.",
            "assertions": assertions,
            "skipped": False,
            "skip_reason": None,
            "passed": all(item["pass"] for item in assertions),
        },
    )

    return result_payload(assertions)


def grade_llm_judge_good_examples(skill_root: Path, case_dir: Path):
    if not os.environ.get("OPENAI_API_KEY"):
        return result_payload(skipped=True, skip_reason="OPENAI_API_KEY is not set.")

    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    fixture_dir = skill_root / "evals" / "files" / "quality-good"
    copy_fixture(fixture_dir, repo_dir)

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "judge_note_semantics_openai.py"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    assertions = [
        {
            "assertion": "The OpenAI judge exits successfully for the good examples.",
            "pass": result["returncode"] == 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The OpenAI judge marks the note set valid.",
            "pass": summary["valid"] is True,
            "evidence": summary["valid"],
        },
        {
            "assertion": "The OpenAI judge reports five checked notes.",
            "pass": summary["note_count"] == 5,
            "evidence": summary["note_count"],
        },
        {
            "assertion": "The OpenAI judge mean score is at least 4.0.",
            "pass": summary["mean_score"] >= 4.0,
            "evidence": summary["mean_score"],
        },
    ]
    return result_payload(assertions)


def grade_llm_judge_bad_note(skill_root: Path, case_dir: Path):
    if not os.environ.get("OPENAI_API_KEY"):
        return result_payload(skipped=True, skip_reason="OPENAI_API_KEY is not set.")

    repo_dir = case_dir / "with_skill" / "outputs" / "repo"
    fixture_dir = skill_root / "evals" / "files" / "quality-bad"
    copy_fixture(fixture_dir, repo_dir)

    result = run_cmd(
        [
            "python3",
            str(skill_root / "scripts" / "judge_note_semantics_openai.py"),
            "--path",
            str(repo_dir),
            "--json",
        ],
        cwd=skill_root,
    )
    (case_dir / "with_skill" / "stdout.json").write_text(result["stdout"])
    (case_dir / "with_skill" / "stderr.log").write_text(result["stderr"])
    write_json(case_dir / "with_skill" / "timing.json", {"duration_ms": result["duration_ms"]})

    summary = json.loads(result["stdout"])
    issues = summary["notes"][0]["issues"] if summary["notes"] else []
    assertions = [
        {
            "assertion": "The OpenAI judge exits non-zero for the bad note.",
            "pass": result["returncode"] != 0,
            "evidence": result["returncode"],
        },
        {
            "assertion": "The OpenAI judge marks the note set invalid.",
            "pass": summary["valid"] is False,
            "evidence": summary["valid"],
        },
        {
            "assertion": "The OpenAI judge reports at least one issue for the bad note.",
            "pass": len(issues) > 0,
            "evidence": issues,
        },
    ]
    return result_payload(assertions)


def main():
    args = parse_args()
    eval_root = Path(__file__).resolve().parent
    skill_root = eval_root.parent
    workspace_root = args.workspace or Path("/tmp/knowledge-evals")
    iteration_dir = next_iteration_dir(workspace_root)
    iteration_dir.mkdir(parents=True, exist_ok=False)

    eval_spec = json.loads((eval_root / "evals.json").read_text())
    trigger_spec = json.loads((eval_root / "triggers.json").read_text())

    benchmark = {
        "skill_name": eval_spec["skill_name"],
        "iteration": iteration_dir.name,
        "cases": [],
        "trigger_pack": {
            "status": "prepared",
            "should_trigger": len(trigger_spec["should_trigger"]),
            "should_not_trigger": len(trigger_spec["should_not_trigger"]),
        },
    }

    graders = {
        "fresh_scaffold": grade_fresh_scaffold,
        "preserve_existing": grade_preserve_existing,
        "force_managed_refresh": grade_force_managed_refresh,
        "validator_detects_damage": grade_validator_detects_damage,
        "quality_good_examples": grade_quality_good_examples,
        "quality_detects_bad_note": grade_quality_detects_bad_note,
        "search_finds_relevant_notes": grade_search_finds_relevant_notes,
        "search_can_include_rules": grade_search_can_include_rules,
        "search_handles_no_match": grade_search_handles_no_match,
        "retrieval_style_guidance": grade_retrieval_style_guidance,
        "llm_judge_good_examples": grade_llm_judge_good_examples,
        "llm_judge_bad_note": grade_llm_judge_bad_note,
    }

    passed_cases = 0
    executed_cases = 0
    skipped_cases = 0

    for case in eval_spec["evals"]:
        case_dir = iteration_dir / case["id"]
        case_dir.mkdir(parents=True, exist_ok=False)
        result = graders[case["id"]](skill_root, case_dir)
        assertions = result["assertions"]
        skipped = result["skipped"]
        passed = all(item["pass"] for item in assertions) if assertions else skipped
        if skipped:
            skipped_cases += 1
        else:
            executed_cases += 1
            if passed:
                passed_cases += 1

        grading = {
            "id": case["id"],
            "prompt": case["prompt"],
            "expected_output": case["expected_output"],
            "assertions": assertions,
            "skipped": skipped,
            "skip_reason": result["skip_reason"],
            "passed": passed,
        }
        write_json(case_dir / "with_skill" / "grading.json", grading)
        benchmark["cases"].append(
            {
                "id": case["id"],
                "status": "skipped" if skipped else ("passed" if passed else "failed"),
                "passed": passed,
                "assertion_pass_rate": (
                    sum(1 for item in assertions if item["pass"]) / len(assertions)
                    if assertions
                    else None
                ),
            }
        )

    benchmark["executed_cases"] = executed_cases
    benchmark["skipped_cases"] = skipped_cases
    benchmark["pass_rate"] = (passed_cases / executed_cases) if executed_cases else 1.0
    write_json(iteration_dir / "benchmark.json", benchmark)
    print(iteration_dir)

    if passed_cases != executed_cases:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
