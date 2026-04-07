# Knowledge Model

Use this reference when deciding what the scaffold should create.

## Default tree

```text
.knowledge/
  sources/
    inbox/
    archive/
    attachments/
  knowledge/
    literature/
    permanent/
    structure/
    open-questions/
    source-notes/
  rules/
    templates/
```

## Layer responsibilities

- `sources/` stores raw material in its original form. Preserve PDFs, web clippings, screenshots, transcripts, meeting notes, and other evidence here.
- `knowledge/` stores linked notes that express understanding, interpretation, reusable ideas, and open questions.
- `rules/` stores the conventions that keep the system coherent: note types, templates, linking rules, provenance rules, and maintenance guidance.

## Knowledge note types

- `literature/` holds concise source-linked extraction notes.
- `permanent/` holds durable single-idea notes written in the user's own words.
- `structure/` holds hub notes that point into a topic cluster and explain how the linked notes fit together.
- `open-questions/` holds unresolved tensions, contradictions, and research directions that should remain visible.
- `source-notes/` holds lightweight reference notes that connect raw source material to downstream notes.

## Default creation rules

- Capture first in `sources/`, interpret later in `knowledge/`.
- Keep rules separate from note content.
- If one file mixes evidence, interpretation, and governance, split it.
- Prefer creating a new permanent note when a durable idea emerges.
- Prefer updating or adding a structure note when a cluster of linked notes starts to form.
