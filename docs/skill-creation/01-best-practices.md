# Best Practices For Creating Skills

Use this as the core instruction set when drafting `SKILL.md`.

## 1. Start from real expertise

- Do not generate a skill from generic model knowledge alone.
- Ground the skill in real execution traces, runbooks, code review feedback, bug fixes, schemas, config files, and failure cases.
- A good source is a real task you completed with an agent where you had to provide corrections, preferences, or project-specific context.

Extract and preserve:

- The steps that actually worked.
- Corrections you had to make.
- Project-specific constraints and conventions.
- Expected inputs and outputs.
- Edge cases the agent missed on its own.

## 2. Refine with real execution

- Treat the first draft as provisional.
- Run the skill on real tasks and inspect traces, not just final output.
- Record false positives, missed cases, wasted steps, and instructions the agent followed even when they did not apply.
- After each round, cut unnecessary instructions and tighten ambiguous ones.

## 3. Spend context carefully

- Every token in `SKILL.md` competes with the rest of the agent context.
- Keep only what the agent is likely to get wrong without the skill.
- Omit generic explanations the base model already knows.

Use this filter for every section:

- Keep it if it adds project-specific knowledge, domain-specific procedure, tool choice, non-obvious edge case, or output constraint.
- Cut it if it only explains common concepts or repeats obvious best practices.

## 4. Scope the skill as one coherent unit

- Make the skill cover one unit of work that composes cleanly with other skills.
- Avoid skills so narrow that several must load together for one task.
- Avoid skills so broad that triggering becomes ambiguous.

Good pattern:

- A skill handles one workflow end to end, such as analyzing a specific file type and formatting the result.

Bad pattern:

- A skill mixes unrelated work, such as data querying, infra administration, and deployment policy.

## 5. Aim for moderate detail

- Prefer concise stepwise guidance with a working example.
- Do not try to encode every possible edge case into the main file.
- If the skill grows large, keep `SKILL.md` to the always-needed core and move extra detail out to support files.

## 6. Use progressive disclosure

- Keep `SKILL.md` as the default instructions the agent should always read.
- Move bulky material into `references/`, `assets/`, or similar folders.
- Tell the agent exactly when to open each file.

Good:

- Read `references/api-errors.md` if the API returns a non-200 response.

Bad:

- See `references/` for more details.

## 7. Match control to fragility

- Be flexible where multiple approaches are acceptable.
- Be strict where order, consistency, or safety matters.
- Explain why a rule exists when possible; models follow purpose-driven instructions better than arbitrary rules.

Use flexible guidance for:

- Review checklists.
- Heuristic analysis.
- Situations with multiple valid approaches.

Use prescriptive guidance for:

- Fragile commands.
- Destructive operations.
- Required sequences.
- Cases where consistency matters more than creativity.

## 8. Provide defaults, not menus

- Pick one default tool, library, or workflow.
- Mention alternatives only as fallbacks or for specific conditions.
- Do not present a long list of equally weighted options unless the skill genuinely requires selection logic.

## 9. Prefer procedures over one-off answers

- Teach the agent how to solve the class of problems.
- Do not bake in an answer that only works for one example.
- Specific details are fine when they generalize as reusable rules.

## 10. Include high-value instruction patterns

### Gotchas

Keep a short gotchas section in `SKILL.md` for non-obvious facts the agent will likely miss, especially if the agent will not know when to load a reference file.

Good gotchas include:

- Schema quirks.
- Naming mismatches across systems.
- Misleading health checks.
- Required filters.
- Environment-specific failure modes.

When you correct a repeated mistake, add it here.

### Output templates

- Give a concrete template when output format matters.
- Keep short templates inline.
- Move long or conditional templates into `assets/` and reference them when needed.

### Checklists

- Use checklists for multi-step workflows with dependencies.
- Make progress visible.
- Name the concrete command or file involved in each step.

### Validation loops

- Instruct the agent to do work, run validation, fix issues, and repeat until validation passes.
- Validation can be a script, a checklist, or a reference document.

### Plan-validate-execute

For batch or destructive workflows:

1. Build an intermediate plan or mapping.
2. Validate it against a source of truth.
3. Fix errors.
4. Execute only after validation passes.

This is especially useful when a small mistake can corrupt downstream results.

## 11. Bundle repeated logic into scripts

- If the agent keeps reinventing the same helper logic across tasks, move that logic into `scripts/`.
- Prefer a tested script over repeated ad hoc command construction.

## Drafting checklist

- Is the skill grounded in real project knowledge?
- Does each section teach something the agent would likely miss otherwise?
- Is the scope a coherent unit of work?
- Are defaults and fallbacks clear?
- Are fragile steps explicit?
- Are gotchas, templates, and validators included where needed?
- Are bulky details deferred to support files with explicit load conditions?
