# Using Scripts In Skills

Use this when a skill needs executable helpers or command-line workflows.

## 1. Decide between one-off commands and bundled scripts

Use a one-off command when:

- an existing tool already solves the problem
- the command is short and stable
- dependency resolution can happen at runtime

Common one-off runners:

- `uvx`
- `pipx`
- `npx`
- `bunx`
- `deno run`
- `go run`

Rules:

- Pin versions for reproducibility.
- State runtime prerequisites in `SKILL.md`.
- If the command becomes complex or error-prone, replace it with a bundled script.

## 2. Reference scripts with relative paths

List bundled scripts in `SKILL.md` and invoke them using paths relative to the skill root.

Example:

```md
## Available scripts

- `scripts/validate.sh` - validate configuration files
- `scripts/process.py` - transform input data
```

```bash
bash scripts/validate.sh "$INPUT_FILE"
python3 scripts/process.py --input results.json
```

## 3. Prefer self-contained scripts

When possible, make scripts runnable without a separate manual install step.

For Python, prefer inline dependency metadata so the agent can run the script directly with `uv run`.

Example pattern:

```python
# /// script
# dependencies = [
#   "beautifulsoup4>=4.12,<5",
# ]
# requires-python = ">=3.11"
# ///
```

## 4. Design scripts for agent execution

Agents run in non-interactive shells. Design accordingly.

### Hard requirements

- Never require TTY prompts.
- Accept all inputs through flags, environment variables, or stdin.
- Fail fast with a clear message when required arguments are missing.

### `--help` requirements

Every reusable script should provide concise `--help` output that includes:

- purpose
- usage
- flags
- defaults
- short examples

### Error-message requirements

Error messages should tell the agent:

- what failed
- what was expected
- what value was received, if relevant
- what to try next

### Output requirements

- Put structured data on stdout.
- Put logs, warnings, and diagnostics on stderr.
- Prefer JSON, CSV, or TSV over free-form text.

## 5. Safety and reliability guidelines

- Idempotency: retries should be safe where possible.
- Input constraints: reject ambiguous input rather than guessing.
- Dry runs: destructive scripts should offer a `--dry-run` mode.
- Safe defaults: require explicit confirmation flags for risky actions when appropriate.
- Exit codes: use meaningful, documented exit codes.
- Output size: default to summaries or file output if results may be large.

## 6. When to extract logic into a script

Bundle a script when:

- the agent keeps recreating the same helper logic
- a command needs several flags or careful quoting
- validation is easier as code than as prose
- the workflow benefits from deterministic behavior

## Script authoring checklist

- Is the interface non-interactive?
- Does `--help` explain usage clearly?
- Are dependencies declared or otherwise explicit?
- Is the output structured and composable?
- Are errors specific and actionable?
- Is the script safe to retry?
- Is there a dry-run or validation mode for risky operations?
