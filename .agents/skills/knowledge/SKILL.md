---
name: knowledge
description: Use this skill when the user needs to create, repair, or standardize a repo-local `.knowledge` folder as a personal second-brain workspace. It supports bootstrapping a three-layer knowledge system from design docs, research notes, or project memory, with `sources`, `knowledge`, and `rules` layers plus Zettelkasten-style templates for literature, permanent, structure, open-question, and source notes. Use it when the user asks for a second brain, knowledge vault, note system, or durable project memory in files. Do not use it for generic documentation sites, wiki content, or app features unrelated to a `.knowledge` workspace.
---

# Knowledge

Create or refresh a repo-local `.knowledge` folder that keeps raw material, linked knowledge, and maintenance rules separate.

Read `references/knowledge-model.md` before making changes.
Read `references/zettelkasten-rules.md` when you need to adjust note templates, IDs, link conventions, or provenance rules.
Read `references/example-knowledge-workflow.md` when you need a compact example of how sources, notes, and rules should connect.
Read `references/example-knowledge-files.md` when you need concrete starter file examples for `rules/` or `knowledge/`.

## Default workflow

1. Inspect the target repo for an existing `.knowledge` folder and any user-provided concept docs.
2. Preserve existing notes and raw sources. Never delete or rewrite user-authored knowledge files just to reapply the scaffold.
3. Run `bash scripts/init_knowledge.sh --path "$TARGET_ROOT"` to create the base folder. Use `--dry-run` first if `.knowledge` already exists. Use `--force-managed` only when you need to refresh the starter files owned by this skill.
4. If the user supplied a design doc, reconcile the generated starter files with that doc after scaffolding.
5. Keep the layer boundary explicit:
   - `sources/` stores raw inputs and evidence.
   - `knowledge/` stores linked notes.
   - `rules/` stores templates and maintenance rules.
6. Prefer timestamp note IDs for digital notes. Keep one main idea per knowledge note, write in the user's own words, and keep provenance visible.
7. Seed structure notes as entry points, not as rigid taxonomy pages. Use links and link context to connect notes across topics.
8. After scaffolding, verify the resulting tree and mention any places where the user's design doc forced a deviation from the default model.

## Available scripts

- `scripts/init_knowledge.sh` - scaffold or refresh the managed `.knowledge` folder structure and starter files.
