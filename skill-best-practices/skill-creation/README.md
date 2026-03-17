# Skill Creation Instructions

Use these files when an LLM needs to create or improve a skill.

## Scope

This directory distills guidance from:

- https://agentskills.io/skill-creation/best-practices
- https://agentskills.io/skill-creation/optimizing-descriptions
- https://agentskills.io/skill-creation/evaluating-skills
- https://agentskills.io/skill-creation/using-scripts

## Workflow

When creating a skill, follow this order:

1. Read `01-best-practices.md` and draft the skill from real, project-specific knowledge.
2. Write the frontmatter description using `02-description-optimization.md`.
3. If the skill needs scripts, design them with `04-using-scripts.md`.
4. Create evals and iterate with `03-evaluating-skills.md`.

## Minimum standards

- Start from real workflows, corrections, incident history, or project artifacts.
- Keep `SKILL.md` focused on the instructions the agent needs every time.
- Put bulky detail into `references/`, `assets/`, or `scripts/`, and tell the agent exactly when to load them.
- Prefer defaults over long option lists.
- Prefer reusable procedures over one-off answers.
- Include gotchas, validation steps, and output templates where they materially reduce mistakes.
- Treat description quality and output quality as separate problems; evaluate both.

## Recommended directory shape

```text
my-skill/
├── SKILL.md
├── references/
├── assets/
├── scripts/
└── evals/
    ├── evals.json
    └── files/
```

## File guide

- `01-best-practices.md`: how to scope, structure, and calibrate a skill.
- `02-description-optimization.md`: how to make the description trigger correctly.
- `03-evaluating-skills.md`: how to run baseline-vs-skill evals and iterate.
- `04-using-scripts.md`: how to bundle commands and scripts for agent use.
