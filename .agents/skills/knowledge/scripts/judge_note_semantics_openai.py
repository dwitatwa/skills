#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class NoteJudgment(BaseModel):
    path: str
    note_type: str
    single_clear_idea_score: int = Field(ge=1, le=5)
    own_words_score: int = Field(ge=1, le=5)
    provenance_clarity_score: int = Field(ge=1, le=5)
    link_quality_score: int = Field(ge=1, le=5)
    reusable_knowledge_score: int = Field(ge=1, le=5)
    strengths: List[str]
    issues: List[str]
    verdict: Literal["pass", "fail"]


class JudgeOutput(BaseModel):
    overall_summary: str
    notes: List[NoteJudgment]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Use an OpenAI model to judge semantic note quality in a .knowledge workspace."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Parent directory that contains .knowledge (default: current directory)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_LLM_JUDGE_MODEL", "gpt-4.1-mini"),
        help="Judge model to use (default: OPENAI_LLM_JUDGE_MODEL or gpt-4.1-mini)",
    )
    parser.add_argument(
        "--max-notes",
        type=int,
        default=20,
        help="Maximum number of notes to judge (default: 20)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write the judgment summary as JSON to stdout",
    )
    return parser.parse_args()


def load_notes(root: Path, max_notes: int):
    knowledge_root = root / ".knowledge" / "knowledge"
    if not knowledge_root.is_dir():
        raise FileNotFoundError(f"missing knowledge directory: {knowledge_root}")

    paths = sorted(knowledge_root.rglob("*.md"))
    selected = paths[:max_notes]
    items = []
    for path in selected:
        rel = path.relative_to(root)
        items.append(
            {
                "path": str(rel),
                "content": path.read_text(),
            }
        )
    return items


def render_prompt(notes):
    note_blocks = []
    for note in notes:
        note_blocks.append(
            f"PATH: {note['path']}\n"
            f"```md\n{note['content']}\n```"
        )

    rubric = """Evaluate each note as reusable knowledge, not just as formatted markdown.

Rubric:
- single_clear_idea_score: Does the note hold one main idea instead of collapsing multiple unrelated ideas together?
- own_words_score: Does the note read like original synthesis rather than copied or generic filler?
- provenance_clarity_score: Is the source or origin of the idea clear enough for the note type?
- link_quality_score: Do links and link reasons help the note connect meaningfully to other notes?
- reusable_knowledge_score: Would this note be useful as a future building block for thinking and writing?

Scoring:
- 5 = strong
- 4 = solid
- 3 = mixed
- 2 = weak
- 1 = poor

Pass criteria:
- Use verdict=pass only when the note is semantically reusable overall.
- Use verdict=fail when the note is bloated, vague, poorly grounded, poorly linked, or not meaningfully reusable.

Output rules:
- Be strict and concise.
- Keep strengths and issues concrete.
- Judge only the notes provided.
"""
    return rubric + "\n\nNotes:\n\n" + "\n\n".join(note_blocks)


def summarize(result: JudgeOutput, knowledge_dir: Path, model: str):
    notes = []
    for item in result.notes:
        mean_score = round(
            (
                item.single_clear_idea_score
                + item.own_words_score
                + item.provenance_clarity_score
                + item.link_quality_score
                + item.reusable_knowledge_score
            )
            / 5,
            2,
        )
        notes.append(
            {
                "path": item.path,
                "note_type": item.note_type,
                "single_clear_idea_score": item.single_clear_idea_score,
                "own_words_score": item.own_words_score,
                "provenance_clarity_score": item.provenance_clarity_score,
                "link_quality_score": item.link_quality_score,
                "reusable_knowledge_score": item.reusable_knowledge_score,
                "mean_score": mean_score,
                "strengths": item.strengths,
                "issues": item.issues,
                "passed": item.verdict == "pass",
            }
        )

    return {
        "knowledge_dir": str(knowledge_dir),
        "judge_model": model,
        "overall_summary": result.overall_summary,
        "note_count": len(notes),
        "notes": notes,
        "valid": all(item["passed"] for item in notes),
        "error_count": sum(1 for item in notes if not item["passed"]),
        "mean_score": round(sum(item["mean_score"] for item in notes) / len(notes), 2) if notes else 0,
    }


def main():
    args = parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("error: OPENAI_API_KEY is required for LLM semantic judging.", file=sys.stderr)
        return 2

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: target path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        notes = load_notes(root, args.max_notes)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    client = OpenAI()
    completion = client.chat.completions.parse(
        model=args.model,
        reasoning_effort="low",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a strict evaluator of Zettelkasten-style note quality.",
            },
            {
                "role": "user",
                "content": render_prompt(notes),
            },
        ],
        response_format=JudgeOutput,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        print("error: model returned no parsed output.", file=sys.stderr)
        return 1

    summary = summarize(parsed, root / ".knowledge", args.model)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"knowledge_dir={summary['knowledge_dir']}")
        print(f"judge_model={summary['judge_model']}")
        print(f"note_count={summary['note_count']}")
        print(f"valid={'true' if summary['valid'] else 'false'}")
        print(f"error_count={summary['error_count']}")
        print(f"mean_score={summary['mean_score']}")
        print(f"overall_summary={summary['overall_summary']}")
        for note in summary["notes"]:
            print(f"note={note['path']}")
            print(f"passed={'true' if note['passed'] else 'false'}")
            print(f"mean_score={note['mean_score']}")
            for issue in note["issues"]:
                print(f"issue={issue}")

    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
