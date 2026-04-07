#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Append a timestamped knowledge-update log entry under .knowledge/logs."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Parent directory that contains .knowledge (default: current directory)",
    )
    parser.add_argument("--title", required=True, help="Short title for the update event")
    parser.add_argument("--summary", required=True, help="Human-readable summary of what changed")
    parser.add_argument(
        "--changed-note",
        action="append",
        default=[],
        help="Path relative to .knowledge for a note or rule that changed (repeatable)",
    )
    parser.add_argument(
        "--repo-source",
        action="append",
        default=[],
        help="Repo path or other source that triggered the update (repeatable)",
    )
    parser.add_argument(
        "--follow-up",
        action="append",
        default=[],
        help="Open follow-up item to track later (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="Write the result as JSON to stdout")
    return parser.parse_args()


def slugify(value: str):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "update"


def write_list(lines):
    if not lines:
        return ["- none"]
    return [f"- {line}" for line in lines]


def main():
    args = parse_args()
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: target path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    knowledge_dir = root / ".knowledge"
    logs_dir = knowledge_dir / "logs"
    if not logs_dir.is_dir():
        print(f"error: missing logs directory: {logs_dir}", file=sys.stderr)
        return 2

    ts = datetime.now().strftime("%Y%m%d%H%M")
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    filename = f"{ts}-{slugify(args.title)}.md"
    path = logs_dir / filename
    rel_path = f"logs/{filename}"

    body = "\n".join(
        [
            "---",
            f"id: {ts}",
            "type: log",
            f"title: {args.title}",
            f"created: {created}",
            "changed_notes:",
            *[f"  - {item}" for item in args.changed_note],
            "repo_sources:",
            *[f"  - {item}" for item in args.repo_source],
            "follow_ups:",
            *[f"  - {item}" for item in args.follow_up],
            "---",
            "",
            f"# {args.title}",
            "",
            "## Summary",
            "",
            args.summary,
            "",
            "## Changed notes",
            "",
            *write_list(args.changed_note),
            "",
            "## Repo sources",
            "",
            *write_list(args.repo_source),
            "",
            "## Follow-ups",
            "",
            *write_list(args.follow_up),
            "",
        ]
    )
    path.write_text(body)

    payload = {
        "knowledge_dir": str(knowledge_dir),
        "path": rel_path,
        "title": args.title,
        "changed_note_count": len(args.changed_note),
        "repo_source_count": len(args.repo_source),
        "follow_up_count": len(args.follow_up),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"path={payload['path']}")
        print(f"title={payload['title']}")
        print(f"changed_note_count={payload['changed_note_count']}")
        print(f"repo_source_count={payload['repo_source_count']}")
        print(f"follow_up_count={payload['follow_up_count']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
