---
name: knowledge
description: Use this skill when the user needs to create, repair, query, update, or standardize a repo-local `.knowledge` folder as a personal second-brain workspace. It supports bootstrapping a three-layer knowledge system from design docs, research notes, or project memory, with `sources`, `knowledge`, and `rules` layers plus Zettelkasten-style templates for literature, permanent, structure, open-question, and source notes. Use it when the user asks for a second brain, knowledge vault, note system, durable project memory in files, wants to find what the repo already knows about a topic from `.knowledge`, or wants to keep a log of knowledge changes after repo updates or merges. Do not use it for generic documentation sites, wiki content, or app features unrelated to a `.knowledge` workspace.
---

# Knowledge

Create or refresh a repo-local `.knowledge` folder that keeps raw material, linked knowledge, and maintenance rules separate.

Read `references/knowledge-model.md` before making changes.
Read `references/zettelkasten-rules.md` when you need to adjust note templates, IDs, link conventions, or provenance rules.
Read `references/example-knowledge-workflow.md` when you need a compact example of how sources, notes, and rules should connect.
Read `references/example-knowledge-files.md` when you need concrete starter file examples for `rules/` or `knowledge/`.
Read `references/example-retrieval-workflow.md` when the user wants to find or answer from existing knowledge instead of creating new notes first.
Read `references/example-update-log-workflow.md` when the user wants to update `.knowledge` after repo changes and keep a log entry.

## Default workflow

1. Inspect the target repo for an existing `.knowledge` folder, the user's intent, and any user-provided concept docs.
2. If the user is asking what the repo already knows about a topic, run `python3 scripts/search_knowledge.py --path "$TARGET_ROOT" --query "$QUERY" --json` before creating anything new. Use `--include-rules` only when the question is about how the knowledge system should behave. Use `--include-logs` when the user is asking about change history or past knowledge updates.
3. Read the top search results and answer the topic directly in natural, user-facing prose. Do not frame the response with phrases like "the knowledge base says" or "the current notes suggest" unless the user explicitly asks about the notes themselves. Lead with the knowledge itself, not the file list. Use file references as support after the explanation. Mention uncertainty only when it materially changes the answer. If the notes are insufficient, say so explicitly.
4. Preserve existing notes and raw sources. Never delete or rewrite user-authored knowledge files just to reapply the scaffold.
5. If the user wants creation, repair, or refresh work, run `bash scripts/init_knowledge.sh --path "$TARGET_ROOT"` to create the base folder. Use `--dry-run` first if `.knowledge` already exists. Use `--force-managed` only when you need to refresh the starter files owned by this skill. Use `--json` when the result will be checked by scripts or evals.
6. If the user supplied a design doc, reconcile the generated starter files with that doc after scaffolding.
7. Keep the layer boundary explicit:
   - `sources/` stores raw inputs and evidence.
   - `knowledge/` stores linked notes.
   - `rules/` stores templates and maintenance rules.
8. Prefer timestamp note IDs for digital notes. Keep one main idea per knowledge note, write in the user's own words, and keep provenance visible.
9. Seed structure notes as entry points, not as rigid taxonomy pages. Use links and link context to connect notes across topics.
10. Run `bash scripts/check_knowledge.sh --path "$TARGET_ROOT"` after scaffolding or repair work. Use `--json` when the result will be checked by scripts or evals.
11. If the repo already contains knowledge notes or you add sample notes, run `python3 scripts/check_note_quality.py --path "$TARGET_ROOT"` to check atomicity, provenance, and link-context heuristics. Use `--json` for scripted grading.
12. If `OPENAI_API_KEY` is available and semantic note quality matters, run `python3 scripts/judge_note_semantics_openai.py --path "$TARGET_ROOT" --json` to get an LLM-judged pass/fail signal for note coherence, provenance clarity, and reusable-knowledge quality.
13. If you update notes after a merge, refactor, or other repo change, append a log entry with `python3 scripts/write_knowledge_log.py --path "$TARGET_ROOT" --title "$TITLE" --summary "$SUMMARY" --changed-note "knowledge/..." --repo-source "path/in/repo" --json`. Use repeated `--changed-note`, `--repo-source`, and `--follow-up` flags as needed.
14. Mention any places where the user's design doc forced a deviation from the default model.

## Retrieval Style

- For retrieval questions, sound like a knowledgeable assistant, not a filesystem report.
- Start with a short direct explanation of the topic itself.
- Mention uncertainty and gaps naturally in the explanation instead of dumping a rigid template.
- Add note references after the explanation or in a short "Sources used" tail section.
- Prefer short note paths relative to the `.knowledge` root, such as `knowledge/permanent/...` or `rules/provenance.md`, instead of long absolute filesystem paths.
- Only foreground raw paths when the user explicitly asks where the knowledge came from.
- Avoid meta phrases about notes, files, or the knowledge base unless they are needed for honesty or the user asked for provenance.

## Available scripts

- `scripts/init_knowledge.sh` - scaffold or refresh the managed `.knowledge` folder structure and starter files.
- `scripts/search_knowledge.py` - search existing `.knowledge` notes and optionally rules for a topic before creating new knowledge.
- `scripts/write_knowledge_log.py` - append a timestamped knowledge-update log entry after merges or note revisions.
- `scripts/check_knowledge.sh` - validate that a repo-local `.knowledge` workspace still has the managed core structure.
- `scripts/check_note_quality.py` - grade note-quality heuristics for atomicity, provenance, and link context.
- `scripts/judge_note_semantics_openai.py` - use an OpenAI model as an optional semantic judge for note quality.
