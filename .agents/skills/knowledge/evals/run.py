#!/usr/bin/env python3
import argparse
import json
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
        help="Directory for iteration outputs (default: evals/workspace)",
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
    return assertions


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
    return assertions


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
    return assertions


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
    return assertions


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
    return assertions


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
    return assertions


def main():
    args = parse_args()
    eval_root = Path(__file__).resolve().parent
    skill_root = eval_root.parent
    workspace_root = args.workspace or (eval_root / "workspace")
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
    }

    passed_cases = 0

    for case in eval_spec["evals"]:
        case_dir = iteration_dir / case["id"]
        case_dir.mkdir(parents=True, exist_ok=False)
        assertions = graders[case["id"]](skill_root, case_dir)
        passed = all(item["pass"] for item in assertions)
        if passed:
            passed_cases += 1

        grading = {
            "id": case["id"],
            "prompt": case["prompt"],
            "expected_output": case["expected_output"],
            "assertions": assertions,
            "passed": passed,
        }
        write_json(case_dir / "with_skill" / "grading.json", grading)
        benchmark["cases"].append(
            {
                "id": case["id"],
                "passed": passed,
                "assertion_pass_rate": sum(1 for item in assertions if item["pass"]) / len(assertions),
            }
        )

    benchmark["pass_rate"] = passed_cases / len(eval_spec["evals"])
    write_json(iteration_dir / "benchmark.json", benchmark)
    print(iteration_dir)

    if passed_cases != len(eval_spec["evals"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
