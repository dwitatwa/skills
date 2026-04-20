---
name: explainer
description: Use this skill when the user needs to explain an existing set of file changes in the workspace and produce the result as a Markdown handoff, such as for staged changes, unstaged edits, a patch, a diff, or recent modifications across one or more files. It supports requests to summarize what changed, walk through the edits, explain only the staged diff, explain why certain files were touched, or write a clear change summary file from current changes. Do not use it for implementing changes, reviewing them for bugs, or writing generic documentation that is not tied to an actual change set.
---

# Explainer

Explain existing file changes from the clearest available baseline and write the result to a Markdown file without turning it into a code review or a line-by-line diff dump.

## Default workflow

1. Identify the scope first. If the user names files, commits, or a diff source, stay within that boundary. If the user means "the changes you just made", prioritize the files touched in the current turn. Otherwise, prefer the current workspace changes relative to `HEAD`.
2. Establish the baseline before describing anything. Prefer the most specific comparison the user gave. If none was given, use `git status --short` plus `git diff --stat` to see the shape of the change set, then inspect file-level diffs with `git diff -- <path>` or `git diff --cached -- <path>` as needed. If git is unavailable or the files are outside a repo, compare the provided files, patches, or current contents directly and say what baseline you are using.
3. Separate change types before explaining them:
   - modified tracked files
   - staged versus unstaged edits
   - new untracked files
   - deletions or renames
4. Read the actual diff before summarizing. For new files, read the file contents and explain what was introduced. For deleted files, use the diff or previous revision to explain what was removed.
5. Explain the changes in layers:
   - start with the user-visible or system-level outcome
   - then describe each file or file group by role
   - call out the important symbols, data flow, behavior, config, or tests that changed
6. Explain rationale only when it is supported by the diff, surrounding code, commit message, comments, tests, or prior conversation. If you are inferring intent, say that explicitly instead of presenting guesswork as fact.
7. Keep the boundary clear:
   - do not drift into bug review unless the user asked for review
   - do not propose rewrites unless the user asked how to improve it
   - do not narrate every changed line when a higher-level explanation is clearer
8. Choose the output path before writing:
   - use the user-provided Markdown path when one is given
   - otherwise, write into a default `explain/` folder in the working tree root with a descriptive name such as `explain/staged-change-explanation.md`, `explain/unstaged-change-explanation.md`, or `explain/change-explanation.md`
   - create the `explain/` folder if it does not exist
   - if that default file already exists and the user did not ask to overwrite it, create a nearby unique name instead of replacing the existing file silently
9. Write the explanation as Markdown. Include a short title, a summary, the scope or baseline used, grouped file explanations, and verification context when available.
10. Cite concrete file references when they help the explanation. Use the changed file paths and current line numbers where possible.
11. After writing the file, give the user a short chat response that says where the Markdown file was saved and what it covers.

## Output guidance

- The primary result is a Markdown file, not only a chat reply.
- Lead with a short summary of what the change set accomplishes.
- Group related files together when they serve one feature or fix.
- Prefer plain language over diff jargon, but keep key identifiers and file references intact.
- If the change set is mixed or noisy, say which parts are clearly related and which parts appear separate.
- Use a compact structure like:

```md
# Change Explanation

## Summary

## Scope And Baseline

## Changed Files

## Verification
```

## Gotchas

- Do not assume the latest diff is the right baseline if the user referenced a specific commit, branch, or patch file.
- Untracked files have no git diff against `HEAD`; explain them from their contents and purpose.
- A request to "explain the changes" is not the same as "review the changes".
- If there are no relevant changes, say so plainly and avoid writing an empty Markdown report unless the user asked for one.
