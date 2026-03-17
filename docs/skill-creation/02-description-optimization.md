# Optimizing Skill Descriptions

Use this when writing or revising the `description` field in `SKILL.md` frontmatter.

## Goal

The description is the primary trigger signal for whether the agent loads the skill. A weak description causes missed triggers. A broad description causes false triggers.

## Writing rules

- Write in imperative form: `Use this skill when...`
- Describe user intent, not the implementation details of the skill.
- Be explicit about adjacent cases where the skill is still useful, even if the user does not name the domain directly.
- Stay concise. Keep the description under the 1024-character limit.

## What a good description includes

- The kind of user task this skill helps with.
- The file types, domains, or workflows it covers.
- The outputs or transformations it is responsible for.
- Boundary hints when the skill should not be used for neighboring tasks.

## Description template

```md
description: >
  Use this skill when the user needs to [primary outcome] for
  [relevant inputs, domains, or workflows]. It is appropriate for
  tasks such as [task family A], [task family B], and [task family C],
  including cases where the user describes the need indirectly rather
  than naming the domain explicitly. Do not use it for [nearby but
  different task class].
```

## Build a trigger eval set

Create about 20 labeled queries:

- 8 to 10 `should_trigger`
- 8 to 10 `should_not_trigger`

Vary the queries across:

- Formal vs casual phrasing.
- Explicit vs implicit mentions of the domain.
- Short vs context-heavy prompts.
- Single-step vs multi-step requests.
- Clean spelling vs typos and abbreviations.

## Write realistic trigger queries

Include:

- File paths.
- Personal or business context.
- Concrete field names, formats, and data hints.
- Realistic ambiguity.

Weak negatives:

- Prompts that are obviously unrelated.

Strong negatives:

- Near-miss prompts that share vocabulary but need a different skill.

## Measure trigger rate

- Run each query multiple times. Three runs is a reasonable starting point.
- Record whether the skill triggered on each run.
- Compute `trigger_rate = triggers / runs`.

Default pass criteria:

- `should_trigger`: pass if trigger rate is greater than 0.5
- `should_not_trigger`: pass if trigger rate is less than 0.5

## Avoid overfitting

Split the eval set:

- Train set: about 60%
- Validation set: about 40%

Rules:

- Keep the positive and negative mix balanced in both sets.
- Use only train failures to drive changes.
- Keep validation results out of the revision prompt.
- Keep the split fixed across iterations.

## Optimization loop

1. Evaluate the current description on train and validation sets.
2. Inspect train failures only.
3. Revise the description at the concept level.
4. Re-run the same split.
5. Keep the version with the best validation pass rate.

## How to revise correctly

If should-trigger cases fail:

- The description is probably too narrow.
- Broaden the task framing or add clearer intent cues.

If should-not-trigger cases fail:

- The description is probably too broad.
- Clarify the boundary of the skill or state what it does not cover.

Do not fix failures by copying keywords from bad examples into the description. Generalize the underlying concept instead.

If progress stalls:

- Try a different structure, not just minor wording edits.

## Final checks

- Description is under 1024 characters.
- It triggers on manual spot checks.
- It performs well on fresh queries that were never used during optimization.
