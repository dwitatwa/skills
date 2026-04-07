# Example Update Log Workflow

Use this reference when the user wants to update `.knowledge` after a merge, a refactor, or any other repo change and keep a readable audit trail.

## Logging default

1. Inspect the repo change.
2. Find the affected notes in `.knowledge`.
3. Update the notes or add new ones.
4. Append one log entry that explains what changed and why.
5. Cite the updated note paths and the repo source that triggered the update.

## Example

User intent:

```text
Update the authentication knowledge after the latest merge and keep a log entry.
```

Suggested workflow:

1. Search `.knowledge` for authentication notes.
2. Inspect the merged code, docs, or commit that changed the behavior.
3. Update the affected notes.
4. Write a log entry that records:
   - what changed
   - why it changed
   - which notes were updated
   - which repo source triggered the update
   - any follow-up gaps

Example log tail:

```text
Summary:
Authentication knowledge was updated to reflect the new session refresh flow and middleware ordering.

Changed notes:
- knowledge/permanent/authentication-session-refresh.md
- knowledge/structure/authentication.md

Repo sources:
- docs/auth/session-refresh.md
- src/auth/middleware.ts

Follow-ups:
- Confirm whether the mobile client uses the same refresh policy.
```

## Logging rule of thumb

- Create one log entry per coherent update event.
- Prefer one clear summary over a noisy changelog dump.
- Keep log paths relative to the `.knowledge` root.
