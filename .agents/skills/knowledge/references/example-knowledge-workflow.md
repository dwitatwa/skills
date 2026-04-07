# Example Knowledge Workflow

Use this reference when you need a worked example of how a `.knowledge` workspace should evolve from one source into linked notes.

## Scenario

The user saves an article about the Zettelkasten method and wants the `.knowledge` folder to preserve the source, extract a few ideas, and keep the system maintainable.

## Example flow

1. Preserve the raw input in `sources/`.
2. Create a `source note` that describes why the source matters.
3. Create one or more `literature notes` for source-linked ideas.
4. Promote the durable idea into a `permanent note`.
5. Add or update a `structure note` that acts as the entry point to the note cluster.
6. If something remains unresolved, capture it in an `open-question note`.
7. Add or update rules only if the workflow needs a durable convention, template, or maintenance policy.

## Example paths

```text
.knowledge/
  sources/
    inbox/
      zettelkasten-introduction.md
  knowledge/
    source-notes/
      202604071000-zettelkasten-introduction.md
    literature/
      202604071015-atomic-notes-enable-linking.md
    permanent/
      202604071045-atomic-notes-improve-reuse.md
    structure/
      202604071100-note-making.md
    open-questions/
      202604071120-when-should-a-note-be-split.md
  rules/
    linking.md
    provenance.md
```

## What each file is doing

- `sources/inbox/zettelkasten-introduction.md` preserves the original captured material.
- `knowledge/source-notes/...` connects the raw source to the downstream notes.
- `knowledge/literature/...` captures one source-linked idea in the user's own words.
- `knowledge/permanent/...` states a durable idea that can outlive the source.
- `knowledge/structure/...` becomes the entry point for the cluster.
- `knowledge/open-questions/...` preserves uncertainty instead of forcing closure.
- `rules/*.md` keeps the system coherent across future notes.

## Rule of thumb

If the file exists to preserve evidence, keep it in `sources/`.
If the file exists to express understanding, keep it in `knowledge/`.
If the file exists to govern how future notes should be created or maintained, keep it in `rules/`.
