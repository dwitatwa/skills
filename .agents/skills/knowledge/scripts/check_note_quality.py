#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


TYPE_TO_DIR = {
    "literature": "literature",
    "permanent": "permanent",
    "structure": "structure",
    "open-question": "open-questions",
    "source": "source-notes",
}

TYPE_RULES = {
    "literature": {
        "required_sections": [
            "Claim or idea",
            "Evidence or excerpt",
            "Why it matters",
            "Candidate links",
        ],
        "main_section": "Claim or idea",
        "main_word_limit": 160,
        "requires_source_refs": True,
    },
    "permanent": {
        "required_sections": [
            "Idea",
            "Why it matters",
            "Link context",
            "Provenance",
        ],
        "main_section": "Idea",
        "main_word_limit": 160,
        "requires_source_refs": False,
    },
    "structure": {
        "required_sections": [
            "Cluster purpose",
            "Entry points",
            "Related questions",
        ],
        "main_section": "Cluster purpose",
        "main_word_limit": 120,
        "requires_source_refs": False,
    },
    "open-question": {
        "required_sections": [
            "Why this is unresolved",
            "Current hypotheses",
            "Next evidence to seek",
        ],
        "main_section": "Why this is unresolved",
        "main_word_limit": 160,
        "requires_source_refs": False,
    },
    "source": {
        "required_sections": [
            "Source details",
            "Why this source matters",
            "Downstream notes",
        ],
        "main_section": "Why this source matters",
        "main_word_limit": 160,
        "requires_source_refs": True,
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check note-quality heuristics for a repo-local .knowledge workspace."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Parent directory that contains .knowledge (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write the validation summary as JSON to stdout",
    )
    return parser.parse_args()


def parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, text

    end = text.find("\n---\n", 4)
    if end == -1:
      return None, text

    raw = text[4:end]
    body = text[end + 5 :]
    data = {}
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
        if value == "[]":
            data[key] = []
            current_key = key
        elif value == "":
            data[key] = []
            current_key = key
        else:
            data[key] = value.strip("'\"")
            current_key = key
    return data, body


def parse_sections(body: str):
    h1 = []
    sections = {}
    current = None
    for line in body.splitlines():
        if line.startswith("# "):
            h1.append(line[2:].strip())
            current = None
            continue
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return h1, {key: "\n".join(value).strip() for key, value in sections.items()}


def word_count(text: str):
    return len(re.findall(r"\b\w+\b", text))


def contains_placeholder(text: str):
    return bool(re.search(r"<[^>\n]+>", text))


def check_link_reason(section_text: str):
    return "[[" in section_text and "because" in section_text


def check_dash_reason(section_text: str):
    return "[[" in section_text and " - " in section_text


def evaluate_note(path: Path, knowledge_dir: Path):
    errors = []
    warnings = []
    text = path.read_text()
    frontmatter, body = parse_frontmatter(text)
    if frontmatter is None:
        return {
            "path": str(path),
            "type": None,
            "errors": ["Missing or malformed frontmatter."],
            "warnings": [],
            "passed": False,
            "score": 0,
        }

    note_type = frontmatter.get("type")
    if note_type not in TYPE_RULES:
        errors.append(f"Unsupported or missing note type: {note_type!r}.")
        note_type = None

    h1, sections = parse_sections(body)
    if len(h1) != 1:
        errors.append("Note should contain exactly one H1 heading.")
    if contains_placeholder(text):
        errors.append("Note still contains template placeholder text.")

    for key in ("id", "type", "title", "created"):
        if not frontmatter.get(key):
            errors.append(f"Missing required frontmatter field: {key}.")

    if note_type:
        expected_dir = TYPE_TO_DIR[note_type]
        actual_dir = path.parent.name
        if actual_dir != expected_dir:
            errors.append(
                f"Note type {note_type!r} should live in {expected_dir!r}, found {actual_dir!r}."
            )

        rules = TYPE_RULES[note_type]
        for section in rules["required_sections"]:
            if section not in sections:
                errors.append(f"Missing required section: {section}.")

        main_section = rules["main_section"]
        if main_section in sections:
            main_words = word_count(sections[main_section])
            if main_words == 0:
                errors.append(f"Main section {main_section!r} is empty.")
            elif main_words > rules["main_word_limit"]:
                errors.append(
                    f"Main section {main_section!r} is too long for an atomic note ({main_words} words > {rules['main_word_limit']})."
                )

        source_refs = frontmatter.get("source_refs", [])
        if isinstance(source_refs, str):
            source_refs = [source_refs]
        if rules["requires_source_refs"] and not source_refs:
            errors.append("Note requires non-empty source_refs for provenance.")

        if note_type == "literature" and "Candidate links" in sections:
            if not check_link_reason(sections["Candidate links"]):
                errors.append("Candidate links should include a linked note and a `because` reason.")
        if note_type == "permanent":
            if "Link context" in sections and not check_link_reason(sections["Link context"]):
                errors.append("Link context should include a linked note and a `because` reason.")
            if "Provenance" in sections and not sections["Provenance"].strip() and not source_refs:
                warnings.append("Permanent note has an empty provenance section and no source_refs; ensure it is an original thought.")
        if note_type == "structure" and "Entry points" in sections:
            if not check_dash_reason(sections["Entry points"]):
                errors.append("Entry points should include linked notes with short reasons.")
        if note_type == "source" and "Downstream notes" in sections:
            if not check_dash_reason(sections["Downstream notes"]):
                errors.append("Downstream notes should include linked notes with short reasons.")

    score = max(0, 100 - (20 * len(errors)) - (5 * len(warnings)))
    return {
        "path": str(path),
        "type": note_type,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
        "score": score,
    }


def main():
    args = parse_args()
    target_root = Path(args.path).resolve()
    if not target_root.is_dir():
        print(f"error: target path does not exist or is not a directory: {target_root}", file=sys.stderr)
        return 2

    knowledge_dir = target_root / ".knowledge"
    notes_root = knowledge_dir / "knowledge"
    if not notes_root.is_dir():
        print(f"error: missing knowledge directory: {notes_root}", file=sys.stderr)
        return 2

    note_paths = sorted(notes_root.rglob("*.md"))
    results = [evaluate_note(path, knowledge_dir) for path in note_paths]
    valid = all(item["passed"] for item in results)
    summary = {
        "knowledge_dir": str(knowledge_dir),
        "note_count": len(results),
        "notes": results,
        "valid": valid,
        "error_count": sum(len(item["errors"]) for item in results),
        "warning_count": sum(len(item["warnings"]) for item in results),
        "mean_score": round(sum(item["score"] for item in results) / len(results), 2) if results else 0,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"knowledge_dir={summary['knowledge_dir']}")
        print(f"note_count={summary['note_count']}")
        print(f"valid={'true' if summary['valid'] else 'false'}")
        print(f"error_count={summary['error_count']}")
        print(f"warning_count={summary['warning_count']}")
        print(f"mean_score={summary['mean_score']}")
        for item in results:
            print(f"note={item['path']}")
            print(f"passed={'true' if item['passed'] else 'false'}")
            for error in item["errors"]:
                print(f"error={error}")
            for warning in item["warnings"]:
                print(f"warning={warning}")

    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
