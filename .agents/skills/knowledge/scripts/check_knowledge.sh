#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Validate a repo-local `.knowledge` folder for the managed three-layer structure.

Usage:
  bash scripts/check_knowledge.sh [--path DIR] [--json]

Options:
  --path DIR   Parent directory that contains `.knowledge` (default: current directory)
  --json       Write the validation summary as JSON to stdout
  --help       Show this help

Examples:
  bash scripts/check_knowledge.sh
  bash scripts/check_knowledge.sh --path /repo/root
  bash scripts/check_knowledge.sh --path /repo/root --json
EOF
}

target_root="."
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

required_dirs=(
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

required_files=(
  "$knowledge_dir/README.md"
  "$knowledge_dir/logs/README.md"
  "$knowledge_dir/rules/README.md"
  "$knowledge_dir/rules/change-log.md"
  "$knowledge_dir/rules/linking.md"
  "$knowledge_dir/rules/provenance.md"
  "$knowledge_dir/rules/maintenance.md"
  "$knowledge_dir/rules/templates/literature-note.md"
  "$knowledge_dir/rules/templates/permanent-note.md"
  "$knowledge_dir/rules/templates/structure-note.md"
  "$knowledge_dir/rules/templates/open-question-note.md"
  "$knowledge_dir/rules/templates/source-note.md"
  "$knowledge_dir/knowledge/structure/0000-home.md"
)

missing_dirs=()
missing_files=()

for path in "${required_dirs[@]}"; do
  if [[ ! -d "$path" ]]; then
    missing_dirs+=("$path")
  fi
done

for path in "${required_files[@]}"; do
  if [[ ! -f "$path" ]]; then
    missing_files+=("$path")
  fi
done

valid=1
if (( ${#missing_dirs[@]} > 0 || ${#missing_files[@]} > 0 )); then
  valid=0
fi

if [[ "$json_output" -eq 1 ]]; then
  MISSING_DIRS="$(printf '%s\n' "${missing_dirs[@]:-}")" \
  MISSING_FILES="$(printf '%s\n' "${missing_files[@]:-}")" \
  VALID="$valid" \
  KNOWLEDGE_DIR="$knowledge_dir" \
  REQUIRED_DIR_COUNT="${#required_dirs[@]}" \
  REQUIRED_FILE_COUNT="${#required_files[@]}" \
  python3 - <<'PY'
import json
import os

def split_lines(value: str):
    return [line for line in value.splitlines() if line]

print(
    json.dumps(
        {
            "knowledge_dir": os.environ["KNOWLEDGE_DIR"],
            "missing_dirs": split_lines(os.environ["MISSING_DIRS"]),
            "missing_files": split_lines(os.environ["MISSING_FILES"]),
            "required_dir_count": int(os.environ["REQUIRED_DIR_COUNT"]),
            "required_file_count": int(os.environ["REQUIRED_FILE_COUNT"]),
            "valid": os.environ["VALID"] == "1",
        },
        indent=2,
        sort_keys=True,
    )
)
PY
else
  printf 'knowledge_dir=%s\n' "$knowledge_dir"
  printf 'valid=%s\n' "$([[ "$valid" -eq 1 ]] && printf 'true' || printf 'false')"
  printf 'required_dirs=%s\n' "${#required_dirs[@]}"
  printf 'required_files=%s\n' "${#required_files[@]}"
  for path in "${missing_dirs[@]}"; do
    printf 'missing_dir=%s\n' "$path"
  done
  for path in "${missing_files[@]}"; do
    printf 'missing_file=%s\n' "$path"
  done
fi

if [[ "$valid" -eq 1 ]]; then
  exit 0
fi
exit 1
