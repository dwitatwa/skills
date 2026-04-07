# Example Knowledge Files

Use this reference when you need concrete examples of what good starter files in `rules/` and `knowledge/` should look like.

## Example rule file

Path:

```text
.knowledge/rules/linking.md
```

Content:

```md
# Linking Rules

- Link new notes to existing notes when there is a real conceptual relationship.
- State the reason for the link in plain language.
- Prefer direct note-to-note links over relying on folders or tags alone.
- Update structure notes when a cluster gains enough density to need an entry point.
```

## Example source note

Path:

```text
.knowledge/knowledge/source-notes/202604071000-zettelkasten-introduction.md
```

Content:

```md
---
id: 202604071000
type: source
title: Introduction to the Zettelkasten Method
created: 2026-04-07
source_refs:
  - ../sources/inbox/zettelkasten-introduction.md
links:
  - '[[202604071015]]'
  - '[[202604071045]]'
---

# Introduction to the Zettelkasten Method

## Source details

- Author: Sascha
- Path or URL: https://zettelkasten.de/introduction/

## Why this source matters

This source explains the digital Zettelkasten basics that shape the `.knowledge` scaffold: atomic notes, stable note IDs, provenance, and structure notes as entry points.

## Downstream notes

- `[[202604071015]]` - extracts the source-linked idea about atomic notes
- `[[202604071045]]` - promotes that idea into a durable rule for note design
```

## Example literature note

Path:

```text
.knowledge/knowledge/literature/202604071015-atomic-notes-enable-linking.md
```

Content:

```md
---
id: 202604071015
type: literature
title: Atomic notes enable precise linking
created: 2026-04-07
source_refs:
  - '[[202604071000]]'
links:
  - '[[202604071045]]'
---

# Atomic notes enable precise linking

## Claim or idea

When a note contains one main idea, it becomes easier to link that idea into multiple contexts without carrying unrelated material along with it.

## Evidence or excerpt

The Zettelkasten method treats the note as a small addressable unit and recommends keeping one thought per note whenever possible.

## Why it matters

This makes the knowledge layer more reusable than long summary pages.

## Candidate links

- `[[202604071045]]` because the reusable design principle should be preserved as a permanent note
```

## Example permanent note

Path:

```text
.knowledge/knowledge/permanent/202604071045-atomic-notes-improve-reuse.md
```

Content:

```md
---
id: 202604071045
type: permanent
title: Atomic notes improve knowledge reuse
created: 2026-04-07
source_refs:
  - '[[202604071000]]'
links:
  - '[[202604071015]]'
  - '[[202604071100]]'
---

# Atomic notes improve knowledge reuse

## Idea

Notes that hold one durable idea are easier to connect, compare, and reuse across projects than broad summary notes.

## Why it matters

This keeps the knowledge layer flexible and lets structure emerge from links instead of rigid hierarchy.

## Link context

- `[[202604071015]]` because the literature note is the immediate source-linked precursor
- `[[202604071100]]` because the note belongs in the note-making cluster

## Provenance

- Derived from `[[202604071000]]`
```

## Example structure note

Path:

```text
.knowledge/knowledge/structure/202604071100-note-making.md
```

Content:

```md
---
id: 202604071100
type: structure
title: Note Making
created: 2026-04-07
source_refs: []
links:
  - '[[202604071045]]'
  - '[[202604071120]]'
---

# Note Making

## Cluster purpose

This note maps ideas about how notes should be created, linked, and maintained.

## Entry points

- `[[202604071045]]` - start here for the rule about atomic note design

## Related questions

- `[[202604071120]]` - unresolved rule for when a note should be split
```

## Example open-question note

Path:

```text
.knowledge/knowledge/open-questions/202604071120-when-should-a-note-be-split.md
```

Content:

```md
---
id: 202604071120
type: open-question
title: When should a note be split?
created: 2026-04-07
source_refs:
  - '[[202604071000]]'
links:
  - '[[202604071100]]'
---

# When should a note be split?

## Why this is unresolved

Atomicity is a useful direction, but not every note should be split immediately. The cutoff between helpful compression and harmful aggregation still needs a clearer heuristic.

## Current hypotheses

- Split a note when it supports multiple independent links with different meanings.
- Keep a note intact when the ideas only make sense together.

## Next evidence to seek

- Review mature note clusters and compare reusable notes against bloated notes
```
