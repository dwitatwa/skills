# Example Retrieval Workflow

Use this reference when the user wants to find what the `.knowledge` workspace already knows about a topic.

## Retrieval default

1. Search existing notes before creating new ones.
2. Read the top matching notes, not just the first filename hit.
3. Answer in natural prose first, then cite the note files you used.
4. Distinguish between:
   - supported claims from existing notes
   - weakly supported inferences
   - missing knowledge
5. If the user wants the gap captured, add an open-question note or create new source and literature notes from fresh evidence.

## Example

User intent:

```text
What do we already know about atomic notes in this repo?
```

Suggested workflow:

1. Run the search helper against `.knowledge`.
2. Read the top results for the topic.
3. Answer with the core idea in normal explanatory language and cite the note paths you used afterward.
4. If the notes conflict or look incomplete, say so explicitly.

Example answer shape:

```text
Atomic notes are useful because they keep one idea clear enough to be reused in different contexts. The strongest material connects atomicity with better linking and better long-term reuse, rather than treating it as a formatting preference.

There is still an open boundary question, though: it is not fully settled when a note should actually be split. That part is still unresolved rather than finished knowledge.

Sources used:
- knowledge/permanent/202604071045-atomic-notes-improve-reuse.md
- knowledge/literature/202604071015-atomic-notes-enable-linking.md
- knowledge/open-questions/202604071120-when-should-a-note-be-split.md
```

## Retrieval rule of thumb

- Search `knowledge/` first for content questions.
- Search `rules/` only when the user is asking how the knowledge system should behave.
- Do not invent facts that are not supported by the notes you read.
- Prefer explanation-first, evidence-second answers unless the user explicitly asks for raw note listings.
- Prefer direct answers over meta commentary about the note system.
- When citing notes, prefer short paths relative to the `.knowledge` root over absolute machine-specific paths.
