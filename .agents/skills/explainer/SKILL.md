---
name: explainer
description: Use this skill when the user needs to explain an existing set of file changes in the workspace and produce the result as a browser-friendly HTML handoff with the relevant changed code included, such as for staged changes, unstaged edits, a patch, a diff, or recent modifications across one or more files. It supports requests to summarize what changed, walk through the edits, explain only the staged diff, explain why certain files were touched, or write a review-ready change summary page from current changes. Do not use it for implementing changes, reviewing them for bugs, or writing generic documentation that is not tied to an actual change set.
---

# Explainer

Explain existing file changes from the clearest available baseline and write the result to a self-contained HTML file that is comfortable to read in a browser without turning it into a code review or a line-by-line diff dump.

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
   - use the user-provided HTML path when one is given
   - otherwise, write into a default `explain/` folder in the working tree root with a descriptive name such as `explain/staged-change-explanation.html`, `explain/unstaged-change-explanation.html`, or `explain/change-explanation.html`
   - create the `explain/` folder if it does not exist
   - if that default file already exists and the user did not ask to overwrite it, create a nearby unique name instead of replacing the existing file silently
9. Write the explanation as one self-contained HTML document with inline CSS. Add inline JavaScript only when it materially improves navigation or review comfort, such as collapsible sections for long diffs.
10. Structure the page with a readable title, summary, scope or baseline used, `User-Visible Behavior`, `File Groups And Rationale`, and verification context when available.
11. Put the changed code inside those narrative sections, not in a separate catch-all code section:
   - place behavior-relevant hunks under `User-Visible Behavior`
   - place file-specific hunks or snippets under `File Groups And Rationale`
12. For each changed file or file group, include the relevant code that changed:
   - prefer HTML `<pre><code>` blocks that preserve diff formatting for modified tracked files
   - use language-labeled code blocks or clearly titled code sections for new files or when a focused snippet is clearer than raw diff format
   - keep enough surrounding context for a reviewer to understand the change, but do not dump an entire large file when only one hunk matters
13. Add a short explanation for each code block:
   - explain what that specific hunk or snippet changes
   - say why that block matters to behavior, flow, config, or tests when the reason is supported by the diff or surrounding context
   - keep the explanation attached to the block it describes so reviewers do not need to infer which prose belongs to which snippet
14. Make the HTML comfortable to read directly in a browser:
   - use clean typography and spacing
   - visually separate added, removed, and unchanged lines
   - keep long code blocks horizontally scrollable
   - make section headings and file labels easy to scan
15. Cite concrete file references when they help the explanation. Use the changed file paths and current line numbers where possible.
16. After writing the file, give the user a short chat response that says where the HTML file was saved and what it covers.

## Output guidance

- The primary result is an HTML file, not only a chat reply.
- Lead with a short summary of what the change set accomplishes.
- Use `User-Visible Behavior` for externally observable changes and include the most relevant changed code directly in that section.
- Use `File Groups And Rationale` for grouped file explanations and include the supporting changed code directly under each file or file group.
- Add a short block-specific explanation immediately before or after each code block so the reviewer can understand that exact snippet without reading the whole file first.
- Keep the HTML self-contained so it can be opened directly in a browser without extra assets.
- Use inline CSS by default. Add inline JavaScript only when it clearly improves review ergonomics.
- Prefer plain language over diff jargon, but keep key identifiers and file references intact.
- If the change set is mixed or noisy, say which parts are clearly related and which parts appear separate.
- Use a compact structure like:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Change Explanation</title>
    <style>
      /* Inline styles for layout, typography, and diff readability */
    </style>
  </head>
  <body>
    <main>
      <section>
        <h1>Change Explanation</h1>
      </section>

      <section>
        <h2>Summary</h2>
      </section>

      <section>
        <h2>Scope And Baseline</h2>
      </section>

      <section>
        <h2>User-Visible Behavior</h2>
        <p>The user-facing effect of the change.</p>
        <p><strong>Why this block matters:</strong> This hunk changes the visible behavior by rejecting empty values earlier.</p>
        <pre><code>- old behavior line
+ new behavior line</code></pre>
      </section>

      <section>
        <h2>File Groups And Rationale</h2>
        <article>
          <h3>path/to/file.ts</h3>
          <p>This block moves the guard clause higher so the rest of the function only runs on valid input.</p>
          <pre><code>- old line
+ new line</code></pre>
        </article>
      </section>

      <section>
        <h2>Verification</h2>
      </section>
    </main>
  </body>
</html>
```

## Gotchas

- Do not assume the latest diff is the right baseline if the user referenced a specific commit, branch, or patch file.
- Untracked files have no git diff against `HEAD`; explain them from their contents and purpose.
- A request to "explain the changes" is not the same as "review the changes".
- If there are no relevant changes, say so plainly and avoid writing an empty HTML report unless the user asked for one.
- For very large diffs, include the most review-relevant hunks and state that the HTML page captures focused excerpts rather than the entire patch.
