#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Scaffold a repo-local `.knowledge` folder for the three-layer second-brain model.

Usage:
  bash scripts/init_knowledge.sh [--path DIR] [--force-managed] [--dry-run] [--json]

Options:
  --path DIR        Parent directory that will contain `.knowledge` (default: current directory)
  --force-managed   Rewrite starter files owned by this script
  --dry-run         Print planned changes without writing files
  --json            Write the final summary as JSON to stdout
  --help            Show this help

Examples:
  bash scripts/init_knowledge.sh
  bash scripts/init_knowledge.sh --path /repo/root --dry-run
  bash scripts/init_knowledge.sh --path /repo/root --force-managed
  bash scripts/init_knowledge.sh --path /repo/root --json
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

target_root="."
force_managed=0
dry_run=0
json_output=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      [[ $# -ge 2 ]] || {
        printf 'error: --path requires a value\n' >&2
        exit 2
      }
      target_root="$2"
      shift 2
      ;;
    --force-managed)
      force_managed=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --json)
      json_output=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$target_root" ]]; then
  printf 'error: target path does not exist or is not a directory: %s\n' "$target_root" >&2
  exit 2
fi

target_root="$(cd "$target_root" && pwd -P)"
knowledge_dir="$target_root/.knowledge"

created_dirs=0
written_files=0
skipped_files=0
declare -A planned_dirs=()

ensure_dir() {
  local path="$1"

  if [[ -d "$path" ]]; then
    return 0
  fi

  if [[ "$dry_run" -eq 1 && -n "${planned_dirs[$path]:-}" ]]; then
    return 0
  fi

  if [[ "$dry_run" -eq 1 ]]; then
    planned_dirs["$path"]=1
    log "would create dir $path"
  else
    mkdir -p "$path"
    log "created dir $path"
  fi
  created_dirs=$((created_dirs + 1))
}

write_managed_file() {
  local path="$1"
  local tmp
  local existed=0

  tmp="$(mktemp)"
  cat >"$tmp"

  if [[ -e "$path" ]]; then
    existed=1
    if [[ "$force_managed" -eq 0 ]]; then
      log "skip file $path"
      rm -f "$tmp"
      skipped_files=$((skipped_files + 1))
      return 0
    fi
  fi

  ensure_dir "$(dirname "$path")"

  if [[ "$dry_run" -eq 1 ]]; then
    if [[ "$existed" -eq 1 ]]; then
      log "would rewrite $path"
    else
      log "would write $path"
    fi
    rm -f "$tmp"
    written_files=$((written_files + 1))
    return 0
  fi

  if [[ "$existed" -eq 1 ]] && cmp -s "$tmp" "$path"; then
    log "unchanged $path"
    rm -f "$tmp"
    skipped_files=$((skipped_files + 1))
    return 0
  fi

  mv "$tmp" "$path"
  if [[ "$existed" -eq 1 ]]; then
    log "rewrote $path"
  else
    log "wrote $path"
  fi
  written_files=$((written_files + 1))
}

dirs=(
  "$knowledge_dir"
  "$knowledge_dir/logs"
  "$knowledge_dir/sources"
  "$knowledge_dir/sources/inbox"
  "$knowledge_dir/sources/archive"
  "$knowledge_dir/sources/attachments"
  "$knowledge_dir/knowledge"
  "$knowledge_dir/knowledge/literature"
  "$knowledge_dir/knowledge/permanent"
  "$knowledge_dir/knowledge/structure"
  "$knowledge_dir/knowledge/open-questions"
  "$knowledge_dir/knowledge/source-notes"
  "$knowledge_dir/rules"
  "$knowledge_dir/rules/templates"
)

for dir in "${dirs[@]}"; do
  ensure_dir "$dir"
done

write_managed_file "$knowledge_dir/README.md" <<'EOF'
# .knowledge

This workspace separates capture, linked knowledge, maintenance rules, and update history.

## Layers

- `sources/` preserves raw inputs and evidence.
- `knowledge/` holds linked notes and evolving insight.
- `rules/` holds the templates and conventions that keep the system coherent.
- `logs/` records meaningful knowledge updates over time.

## Entry point

Start in `knowledge/structure/0000-home.md` and expand from there with links, not with a rigid topic tree.
EOF

write_managed_file "$knowledge_dir/logs/README.md" <<'EOF'
# Logs

This folder records meaningful updates to the `.knowledge` workspace.

## Use logs for

- merges that change existing knowledge
- note revisions triggered by code or docs updates
- resolved questions or important new gaps

Each log entry should say what changed, why it changed, which notes were touched, and what repo source triggered the update.
EOF

write_managed_file "$knowledge_dir/rules/README.md" <<'EOF'
# Rules

These files define how the `.knowledge` workspace stays consistent over time.

## Defaults

- Digital note filenames should start with a timestamp ID: `YYYYMMDDHHMM-slug.md`
- The note's `id` field should match the timestamp prefix
- Use one main idea per note
- Keep source provenance visible
- Add link context whenever you connect notes

Use the templates in `templates/` as starting points, not as mandatory final formats.
EOF

write_managed_file "$knowledge_dir/rules/linking.md" <<'EOF'
# Linking Rules

- Link new notes to existing notes when there is a real conceptual relationship.
- State the reason for the link in plain language.
- Use structure notes to map clusters and provide entry points.
- Do not depend on folders alone to represent relationships.
EOF

write_managed_file "$knowledge_dir/rules/provenance.md" <<'EOF'
# Provenance Rules

- Raw files stay in `sources/`.
- Source-derived ideas should reference a source note, source file path, or citekey.
- Original thoughts do not need invented citations. Leave provenance empty when the note is genuinely your own.
- Quotes can appear inside a note, but the note should still be written in your own words.
EOF

write_managed_file "$knowledge_dir/rules/maintenance.md" <<'EOF'
# Maintenance Rules

- Add missing links when a note becomes isolated.
- Split large multi-idea notes into smaller notes when they become hard to reuse.
- Promote stable ideas from literature notes into permanent notes.
- Update structure notes when a cluster grows or changes shape.
- Preserve uncertainty in `open-questions/` instead of forcing premature conclusions.
- Write a log entry in `logs/` after meaningful repo-driven knowledge updates.
EOF

write_managed_file "$knowledge_dir/rules/change-log.md" <<'EOF'
# Change Log Rules

- Create one log entry per coherent knowledge update event.
- Use log entries for merge-driven note revisions, resolved questions, and important new gaps.
- Keep changed note paths relative to `.knowledge`.
- Record the repo source that triggered the update whenever possible.
- Prefer short readable summaries over noisy change dumps.
EOF

write_managed_file "$knowledge_dir/rules/templates/literature-note.md" <<'EOF'
---
id: <YYYYMMDDHHMM>
type: literature
title: <title>
created: <YYYY-MM-DD>
source_refs:
  - <source-note-or-citekey>
links: []
---

# <title>

## Claim or idea

<Summarize one source-linked idea in your own words.>

## Evidence or excerpt

<Add the relevant passage, locator, or observation.>

## Why it matters

<Explain why this idea deserves promotion or linking.>

## Candidate links

- `[[<note-id>]]` because <reason>
EOF

write_managed_file "$knowledge_dir/rules/templates/permanent-note.md" <<'EOF'
---
id: <YYYYMMDDHHMM>
type: permanent
title: <title>
created: <YYYY-MM-DD>
source_refs: []
links: []
---

# <title>

## Idea

<State one durable idea in your own words.>

## Why it matters

<Explain the consequence, implication, or use.>

## Link context

- `[[<note-id>]]` because <reason>

## Provenance

- <source note, citekey, or leave blank if original>
EOF

write_managed_file "$knowledge_dir/rules/templates/structure-note.md" <<'EOF'
---
id: <YYYYMMDDHHMM>
type: structure
title: <title>
created: <YYYY-MM-DD>
source_refs: []
links: []
---

# <title>

## Cluster purpose

<Explain what this map is helping you navigate.>

## Entry points

- `[[<note-id>]]` - <why start here>

## Related questions

- <open question or tension>
EOF

write_managed_file "$knowledge_dir/rules/templates/open-question-note.md" <<'EOF'
---
id: <YYYYMMDDHHMM>
type: open-question
title: <question>
created: <YYYY-MM-DD>
source_refs: []
links: []
---

# <question>

## Why this is unresolved

<Describe the tension, ambiguity, or missing evidence.>

## Current hypotheses

- <hypothesis>

## Next evidence to seek

- <source, experiment, or note to create>
EOF

write_managed_file "$knowledge_dir/rules/templates/source-note.md" <<'EOF'
---
id: <YYYYMMDDHHMM>
type: source
title: <source title>
created: <YYYY-MM-DD>
source_refs:
  - <file path or citekey>
links: []
---

# <source title>

## Source details

- Author:
- Date:
- Path or URL:

## Why this source matters

<Describe why you expect to reuse this source.>

## Downstream notes

- `[[<note-id>]]` - <relationship>
EOF

write_managed_file "$knowledge_dir/knowledge/structure/0000-home.md" <<'EOF'
---
id: 0000-home
type: structure
title: Knowledge Home
created: scaffolded
source_refs: []
links: []
---

# Knowledge Home

Use this note as the entry point into the knowledge layer.

## Current clusters

- Add the first durable note in a cluster here.
- Replace folder-based grouping with note-to-note links as patterns emerge.

## Entry points

- `../literature/` for source-linked extraction notes
- `../permanent/` for durable ideas
- `../open-questions/` for unresolved tensions
- `../source-notes/` for reusable source references

## Next actions

- Create a source note for each durable source.
- Promote stable ideas from literature notes into permanent notes.
- Add link context whenever you connect notes.
EOF

mode="$([[ "$dry_run" -eq 1 ]] && printf 'dry-run' || printf 'apply')"

if [[ "$json_output" -eq 1 ]]; then
  MODE="$mode" \
  KNOWLEDGE_DIR="$knowledge_dir" \
  CREATED_DIRS="$created_dirs" \
  WRITTEN_FILES="$written_files" \
  SKIPPED_FILES="$skipped_files" \
  python3 - <<'PY'
import json
import os

print(
    json.dumps(
        {
            "mode": os.environ["MODE"],
            "knowledge_dir": os.environ["KNOWLEDGE_DIR"],
            "created_dirs": int(os.environ["CREATED_DIRS"]),
            "written_files": int(os.environ["WRITTEN_FILES"]),
            "skipped_files": int(os.environ["SKIPPED_FILES"]),
        },
        indent=2,
        sort_keys=True,
    )
)
PY
else
  printf 'mode=%s\n' "$mode"
  printf 'knowledge_dir=%s\n' "$knowledge_dir"
  printf 'created_dirs=%s\n' "$created_dirs"
  printf 'written_files=%s\n' "$written_files"
  printf 'skipped_files=%s\n' "$skipped_files"
fi
