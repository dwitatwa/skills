#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Search a repo-local .knowledge workspace for relevant notes."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Parent directory that contains .knowledge (default: current directory)",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search query to match against note paths, titles, headings, and content",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results to return (default: 5)",
    )
    parser.add_argument(
        "--include-rules",
        action="store_true",
        help="Also search .knowledge/rules for process and governance questions",
    )
    parser.add_argument(
        "--include-logs",
        action="store_true",
        help="Also search .knowledge/logs for update history questions",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write the search results as JSON to stdout",
    )
    return parser.parse_args()


def extract_frontmatter_title(text: str):
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    raw = text[4:end]
    body = text[end + 5 :]
    title = ""
    for line in raw.splitlines():
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip("'\"")
            break
    return title, body


def extract_h1(body: str):
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def tokenize(query: str):
    return [token for token in re.findall(r"[a-z0-9]+", query.lower()) if len(token) > 1]


def score_file(path: Path, knowledge_dir: Path, query: str, tokens):
    text = path.read_text()
    lower = text.lower()
    rel = str(path.relative_to(knowledge_dir))
    rel_lower = rel.lower()
    title, body = extract_frontmatter_title(text)
    h1 = extract_h1(body)
    title_lower = title.lower()
    h1_lower = h1.lower()
    phrase = query.lower().strip()

    score = 0
    if phrase:
        if phrase in rel_lower:
            score += 20
        if phrase in title_lower:
            score += 18
        if phrase in h1_lower:
            score += 16
        if phrase in lower:
            score += 10

    for token in tokens:
        score += rel_lower.count(token) * 8
        score += title_lower.count(token) * 7
        score += h1_lower.count(token) * 6
        score += lower.count(token)

    if score == 0:
        return None

    snippets = []
    for line in text.splitlines():
        line_lower = line.lower()
        if phrase and phrase in line_lower:
            snippets.append(line.strip())
        elif any(token in line_lower for token in tokens):
            snippets.append(line.strip())
        if len(snippets) == 3:
            break

    note_type = ""
    for line in text.splitlines():
        if line.startswith("type:"):
            note_type = line.split(":", 1)[1].strip().strip("'\"")
            break

    return {
        "path": rel,
        "score": score,
        "title": title or h1 or path.stem,
        "note_type": note_type,
        "snippets": snippets,
    }


def main():
    args = parse_args()
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: target path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    knowledge_dir = root / ".knowledge"
    knowledge_root = knowledge_dir / "knowledge"
    rules_root = knowledge_dir / "rules"
    logs_root = knowledge_dir / "logs"

    search_roots = []
    if knowledge_root.is_dir():
        search_roots.append(knowledge_root)
    if args.include_rules and rules_root.is_dir():
        search_roots.append(rules_root)
    if args.include_logs and logs_root.is_dir():
        search_roots.append(logs_root)

    if not search_roots:
        print(f"error: no searchable .knowledge directories found under {knowledge_dir}", file=sys.stderr)
        return 2

    tokens = tokenize(args.query)
    results = []
    for search_root in search_roots:
        for path in sorted(search_root.rglob("*.md")):
            item = score_file(path, knowledge_dir, args.query, tokens)
            if item:
                results.append(item)

    results.sort(key=lambda item: (-item["score"], item["path"]))
    results = results[: args.limit]

    summary = {
        "knowledge_dir": str(knowledge_dir),
        "query": args.query,
        "include_rules": args.include_rules,
        "include_logs": args.include_logs,
        "total_matches": len(results),
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"knowledge_dir={summary['knowledge_dir']}")
        print(f"query={summary['query']}")
        print(f"include_rules={'true' if args.include_rules else 'false'}")
        print(f"include_logs={'true' if args.include_logs else 'false'}")
        print(f"total_matches={summary['total_matches']}")
        for item in results:
            print(f"path={item['path']}")
            print(f"score={item['score']}")
            print(f"title={item['title']}")
            if item["note_type"]:
                print(f"type={item['note_type']}")
            for snippet in item["snippets"]:
                print(f"snippet={snippet}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
