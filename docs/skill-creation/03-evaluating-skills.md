# Evaluating Skill Output Quality

Use this to test whether a skill actually improves output quality, not just whether it triggers.

## 1. Start with a small eval set

Each test case should include:

- `prompt`: a realistic user request
- `expected_output`: a human-readable description of success
- `files`: optional input files
- `assertions`: add these after the first run, once you know what to check

Recommended initial size:

- Start with 2 to 3 test cases.
- Expand after you learn from the first results.

## 2. Author `evals/evals.json`

Use a structure like this:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic prompt here",
      "expected_output": "Describe what success looks like",
      "files": ["evals/files/input.dat"],
      "assertions": [
        "Specific, observable, verifiable condition"
      ]
    }
  ]
}
```

Prompt design rules:

- Make them realistic.
- Vary phrasing and detail.
- Include file paths, context, and domain details.
- Include at least one edge case.

## 3. Compare with a baseline

Run every eval at least twice:

- `with_skill`
- `without_skill`

If you are improving an existing skill, use the previous version as the baseline instead of no skill.

## 4. Keep each run isolated

- Use a fresh session or subagent per run.
- Do not let prior context leak into the run.
- Provide only the skill path, prompt, input files, and output directory.

## 5. Organize a workspace by iteration

Recommended shape:

```text
my-skill/
├── SKILL.md
└── evals/
    └── evals.json

my-skill-workspace/
└── iteration-1/
    ├── eval-case-a/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json
    │   │   └── grading.json
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json
```

## 6. Capture timing and token cost

For each run, save:

```json
{
  "total_tokens": 12345,
  "duration_ms": 23456
}
```

This lets you judge quality gain against latency and context cost.

## 7. Write assertions after the first run

Good assertions are:

- Specific
- Observable
- Verifiable
- Robust to wording variation

Good examples:

- The output file is valid JSON.
- The chart has labeled axes.
- The report includes at least 3 recommendations.

Bad examples:

- The output is good.
- The output uses one exact phrase.

## 8. Grade with evidence

For each assertion:

- Mark pass or fail.
- Record concrete evidence from the output.

Use scripts for mechanical checks when possible:

- file existence
- JSON validity
- dimensions
- counts
- schema validation

Use LLM grading for qualitative checks that still have specific criteria.

## 9. Aggregate results

Compute summary stats per configuration:

- pass rate
- average tokens
- average duration
- delta between configurations

Interpretation:

- A skill that adds modest cost and materially improves pass rate is likely worth keeping.
- A skill that adds heavy cost for marginal gain may need simplification or removal.

## 10. Look for patterns, not just averages

Review assertions that:

- Always pass in both configs: probably not measuring skill value.
- Always fail in both configs: probably broken, too hard, or irrelevant.
- Pass only with the skill: these reveal where the skill adds value.
- Flake across runs: instructions may be ambiguous, or the eval may be unstable.

Also inspect time and token outliers by reading execution traces.

## 11. Add human review

Assertion grading is not enough. Review the actual outputs and save concrete human feedback, such as:

- missing labels
- wrong ordering
- poor structure
- technically correct but unhelpful output

Feedback should be actionable, not vague.

## 12. Use the full iteration loop

For each iteration:

1. Run all evals against the baseline and the current skill.
2. Grade outputs and save evidence.
3. Aggregate benchmarks.
4. Review outputs as a human.
5. Give the current `SKILL.md`, failed assertions, human feedback, and execution traces to an LLM.
6. Ask for broad, general improvements, not patches tailored to single prompts.
7. Apply the changes.
8. Re-run all evals in a new `iteration-N/` directory.

## 13. Revision principles for the LLM

When asking an LLM to improve a skill, require it to:

- Generalize from failures instead of overfitting to examples.
- Keep the skill lean; remove instructions that cause wasted work.
- Explain the reason behind instructions where useful.
- Bundle repeated helper logic into scripts when traces show the model recreating it often.

## Stop criteria

Stop iterating when:

- results are good enough for the use case
- human feedback is consistently empty
- additional changes are not producing meaningful improvement
