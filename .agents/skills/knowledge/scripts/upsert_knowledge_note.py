#!/usr/bin/env python3
import argparse
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path


NOTE_TYPES = {
    "literature": {
        "dir": "literature",
        "sections": [
            "Claim or idea",
            "Evidence or excerpt",
            "Why it matters",
            "Candidate links",
        ],
    },
    "permanent": {
        "dir": "permanent",
        "sections": [
            "Idea",
            "Why it matters",
            "Link context",
            "Provenance",
        ],
    },
    "structure": {
        "dir": "structure",
        "sections": [
            "Cluster purpose",
            "Entry points",
            "Related questions",
        ],
    },
    "open-question": {
        "dir": "open-questions",
        "sections": [
            "Why this is unresolved",
            "Current hypotheses",
            "Next evidence to seek",
        ],
    },
    "source": {
        "dir": "source-notes",
        "sections": [
            "Source details",
            "Why this source matters",
            "Downstream notes",
        ],
    },
}

DIR_TO_TYPE = {meta["dir"]: note_type for note_type, meta in NOTE_TYPES.items()}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create or update a .knowledge note without hand-editing the full markdown file."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Parent directory that contains .knowledge (default: current directory)",
    )
    parser.add_argument(
        "--note",
        help="Path relative to .knowledge for the note to update or create",
    )
    parser.add_argument(
        "--type",
        choices=sorted(NOTE_TYPES),
        help="Note type to create or enforce",
    )
    parser.add_argument("--title", help="Note title / H1 heading")
    parser.add_argument("--id", help="Stable note ID (default: current timestamp)")
    parser.add_argument("--slug", help="Slug to use in the filename when creating a note")
    parser.add_argument(
        "--created",
        help="Created date to store in frontmatter (default: today YYYY-MM-DD)",
    )
    parser.add_argument(
        "--source-ref",
        action="append",
        default=[],
        help="Replace source_refs with the provided value(s) (repeatable)",
    )
    parser.add_argument(
        "--add-source-ref",
        action="append",
        default=[],
        help="Append a source_ref if it is not already present (repeatable)",
    )
    parser.add_argument(
        "--link",
        action="append",
        default=[],
        help="Replace links with the provided value(s) (repeatable)",
    )
    parser.add_argument(
        "--add-link",
        action="append",
        default=[],
        help="Append a link if it is not already present (repeatable)",
    )
    parser.add_argument(
        "--set-section",
        action="append",
        default=[],
        help="Set or create a section with SECTION=TEXT (repeatable)",
    )
    parser.add_argument(
        "--append-section",
        action="append",
        default=[],
        help="Append TEXT to a section with SECTION=TEXT (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned result without writing the file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write the result as JSON to stdout",
    )
    return parser.parse_args()


def parse_key_value_assignments(items, flag_name):
    pairs = []
    for item in items:
        if "=" not in item:
            raise ValueError(f"{flag_name} expects SECTION=TEXT, got: {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{flag_name} requires a non-empty section name.")
        pairs.append((key, value.strip("\n")))
    return pairs


def parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        return OrderedDict(), text

    end = text.find("\n---\n", 4)
    if end == -1:
        return OrderedDict(), text

    raw = text[4:end]
    body = text[end + 5 :]
    data = OrderedDict()
    current_key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(line[4:].strip().strip("'\""))
            continue
        if line.startswith("- ") and current_key:
            data.setdefault(current_key, []).append(line[2:].strip().strip("'\""))
            continue
        if ":" not in line:
            current_key = None
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in ("", "[]"):
            data[key] = []
            current_key = key
        else:
            data[key] = value.strip("'\"")
            current_key = key
    return data, body


def parse_body(body: str):
    lines = body.strip("\n").splitlines() if body.strip("\n") else []
    h1 = ""
    preamble = []
    sections = OrderedDict()
    current_section = None

    if lines and lines[0].startswith("# "):
        h1 = lines[0][2:].strip()
        lines = lines[1:]

    for line in lines:
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections.setdefault(current_section, [])
            continue
        if current_section is None:
            preamble.append(line)
        else:
            sections[current_section].append(line)

    rendered_sections = OrderedDict()
    for name, content_lines in sections.items():
        rendered_sections[name] = "\n".join(content_lines).strip("\n")

    return h1, "\n".join(preamble).strip("\n"), rendered_sections


def dump_frontmatter(frontmatter):
    preferred = ["id", "type", "title", "created", "source_refs", "links"]
    ordered_keys = [key for key in preferred if key in frontmatter]
    ordered_keys.extend(key for key in frontmatter if key not in ordered_keys)

    lines = ["---"]
    for key in ordered_keys:
        value = frontmatter[key]
        if isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: []")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if value == "":
        return []
    return [value]


def merge_unique(existing, additions):
    seen = set()
    merged = []
    for item in existing + additions:
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def slugify(value: str):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "note"


def infer_type_from_note_path(note_path: Path):
    if len(note_path.parts) >= 2 and note_path.parts[0] == "knowledge":
        return DIR_TO_TYPE.get(note_path.parts[1])
    return None


def resolve_note_path(args, note_type, note_id, title):
    if args.note:
        note_path = Path(args.note)
        if note_path.parts and note_path.parts[0] == ".knowledge":
            note_path = Path(*note_path.parts[1:])
        return note_path

    filename = f"{note_id}-{args.slug or slugify(title)}.md"
    return Path("knowledge") / NOTE_TYPES[note_type]["dir"] / filename


def build_sections(note_type, existing_sections):
    sections = OrderedDict(existing_sections)
    for section_name in NOTE_TYPES[note_type]["sections"]:
        sections.setdefault(section_name, "")

    ordered = OrderedDict()
    for section_name in NOTE_TYPES[note_type]["sections"]:
        ordered[section_name] = sections.pop(section_name, "")
    for section_name, content in sections.items():
        ordered[section_name] = content
    return ordered


def render_note(title, preamble, sections, frontmatter):
    lines = [dump_frontmatter(frontmatter), "", f"# {title}", ""]

    if preamble:
        lines.extend(preamble.splitlines())
        lines.append("")

    items = list(sections.items())
    for index, (section_name, content) in enumerate(items):
        lines.append(f"## {section_name}")
        lines.append("")
        if content:
            lines.extend(content.splitlines())
        if index != len(items) - 1:
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    args = parse_args()

    try:
        set_sections = parse_key_value_assignments(args.set_section, "--set-section")
        append_sections = parse_key_value_assignments(args.append_section, "--append-section")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: target path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    knowledge_dir = root / ".knowledge"
    knowledge_root = knowledge_dir / "knowledge"
    if not knowledge_root.is_dir():
        print(f"error: missing knowledge directory: {knowledge_root}", file=sys.stderr)
        return 2

    now = datetime.now()
    note_id = args.id or now.strftime("%Y%m%d%H%M")
    created = args.created or now.strftime("%Y-%m-%d")

    existing_text = None
    existing_frontmatter = OrderedDict()
    existing_h1 = ""
    existing_preamble = ""
    existing_sections = OrderedDict()

    note_path_hint = Path(args.note) if args.note else None
    inferred_type = infer_type_from_note_path(note_path_hint) if note_path_hint else None

    note_type = args.type or inferred_type
    title = args.title

    if args.note:
        rel_note_path = resolve_note_path(args, note_type or "permanent", note_id, title or "note")
        absolute_note_path = knowledge_dir / rel_note_path
        if absolute_note_path.exists():
            existing_text = absolute_note_path.read_text()
            existing_frontmatter, body = parse_frontmatter(existing_text)
            existing_h1, existing_preamble, existing_sections = parse_body(body)
            note_type = args.type or existing_frontmatter.get("type") or inferred_type
            title = args.title or existing_frontmatter.get("title") or existing_h1 or absolute_note_path.stem
            note_id = args.id or str(existing_frontmatter.get("id") or note_id)
            created = args.created or str(existing_frontmatter.get("created") or created)
    else:
        if not note_type:
            print("error: --type is required when creating a new note without --note.", file=sys.stderr)
            return 2
        if not title:
            print("error: --title is required when creating a new note without --note.", file=sys.stderr)
            return 2
        rel_note_path = resolve_note_path(args, note_type, note_id, title)
        absolute_note_path = knowledge_dir / rel_note_path
        if absolute_note_path.exists():
            existing_text = absolute_note_path.read_text()
            existing_frontmatter, body = parse_frontmatter(existing_text)
            existing_h1, existing_preamble, existing_sections = parse_body(body)
            note_type = args.type or existing_frontmatter.get("type") or note_type
            title = args.title or existing_frontmatter.get("title") or existing_h1 or title
            note_id = args.id or str(existing_frontmatter.get("id") or note_id)
            created = args.created or str(existing_frontmatter.get("created") or created)

    if not note_type:
        print("error: could not determine note type; pass --type or use a note path under knowledge/<type-dir>/.", file=sys.stderr)
        return 2
    if note_type not in NOTE_TYPES:
        print(f"error: unsupported note type: {note_type}", file=sys.stderr)
        return 2
    if not title:
        print("error: could not determine title; pass --title or update an existing note with a title.", file=sys.stderr)
        return 2

    if not args.note:
        rel_note_path = resolve_note_path(args, note_type, note_id, title)
        absolute_note_path = knowledge_dir / rel_note_path

    frontmatter = OrderedDict(existing_frontmatter)
    frontmatter["id"] = note_id
    frontmatter["type"] = note_type
    frontmatter["title"] = title
    frontmatter["created"] = created

    existing_source_refs = normalize_list(frontmatter.get("source_refs"))
    existing_links = normalize_list(frontmatter.get("links"))
    frontmatter["source_refs"] = (
        args.source_ref if args.source_ref else merge_unique(existing_source_refs, args.add_source_ref)
    )
    frontmatter["links"] = args.link if args.link else merge_unique(existing_links, args.add_link)

    sections = build_sections(note_type, existing_sections)
    for section_name, content in set_sections:
        sections[section_name] = content
    for section_name, content in append_sections:
        current = sections.get(section_name, "")
        if current and content:
            sections[section_name] = current.rstrip() + "\n\n" + content
        elif content:
            sections[section_name] = content
        else:
            sections.setdefault(section_name, current)

    note_text = render_note(title, existing_preamble, sections, frontmatter)

    if not args.dry_run:
        absolute_note_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_note_path.write_text(note_text)

    existed_before = existing_text is not None
    changed = existing_text != note_text
    payload = {
        "knowledge_dir": str(knowledge_dir),
        "path": str(rel_note_path),
        "type": note_type,
        "title": title,
        "created_note": not existed_before,
        "updated_note": existed_before and changed,
        "unchanged": existed_before and not changed,
        "mode": "dry-run" if args.dry_run else "apply",
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key in (
            "mode",
            "path",
            "type",
            "title",
            "created_note",
            "updated_note",
            "unchanged",
        ):
            value = payload[key]
            if isinstance(value, bool):
                value = "true" if value else "false"
            print(f"{key}={value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
