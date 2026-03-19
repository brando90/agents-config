# Conventions: General Coding

<!-- TODO: owner skeptical of AI-generated conventions, needs manual curation -->

Language-agnostic coding conventions for all projects.

---

## Commit Messages

Format: imperative mood, 1-2 sentences, focus on "why" not "what."

```
Add retry logic for flaky API calls during batch scoring

Fix off-by-one in pagination that skipped the last page
```

Do not:
- Start with "Updated", "Changed", "Modified" (use imperative: "Update", "Change", "Fix")
- Write vague messages like "fix bug" or "update code"
- Include file lists in the message (the diff shows that)

Co-authorship: when an AI agent writes the commit, append:
```
Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## Branch Naming

```
<type>/<short-description>
```

Types: `feat/`, `fix/`, `exp/` (experiment), `refactor/`, `docs/`, `chore/`

Examples:
- `feat/add-tvdmi-scoring`
- `fix/correlation-nan-handling`
- `exp/04-gold-ref-judges`

---

## Pull Requests

- Title: under 70 characters, describes the change
- Body: use the template below
- One logical change per PR. Don't bundle unrelated work.

```markdown
## Summary
<1-3 bullet points>

## Test plan
- [ ] <how to verify this works>
```

---

## Code Style

- Match the existing style of the file you're editing. Don't reformat surrounding code.
- Don't add docstrings, comments, or type annotations to code you didn't change.
- Only add comments where the logic isn't self-evident.
- Avoid over-engineering: don't add abstractions, feature flags, or configurability beyond what's needed.

---

## Secrets

- Never commit API keys, tokens, passwords, or private IPs.
- Use environment variables or files in gitignored directories (`~/keys/`, `machine/private/`).
- If you accidentally commit a secret: rotate the key immediately, then force-push to remove it from history.
