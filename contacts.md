# Contact Resolution
**TLDR:** Use `~/ultimate-utils/py_src/uutils/collaborators.py` as the canonical local roster for collaborator identity and email lookup. If a person is missing there, infer from Gmail history only when the match is clear, then update the roster instead of relying on memory.

## Canonical Source

Primary file: `~/ultimate-utils/py_src/uutils/collaborators.py`

Use it before sending email, CC'ing someone, mentioning them on GitHub, or assigning a PR:

```python
from uutils.collaborators import resolve, by_email, by_name, by_github

rec = resolve("Patrick Yu")
emails = rec["emails"]
```

The same repo also exposes `email_collaborator(...)` in `~/ultimate-utils/py_src/uutils/emailing.py`, which resolves the contact and sends through SMTP.

## Email Send Lookup Order

1. Resolve the recipient through `uutils.collaborators.resolve(...)`.
2. If unresolved, search Gmail/Sent history for the exact name, GitHub handle, or institutionally likely address.
3. If Gmail gives one clear match, use it and add the contact to `uutils.collaborators.py` in the same work session.
4. If there are multiple plausible matches, ask Brando one concise clarification question before sending.

## Brando Addresses

When sending any email on Brando's behalf or to Brando, apply the routing rule from `INDEX_RULES.md` Trigger Rule 26:

- Internal agent notifications to Brando go to `brando.science@gmail.com` with no CC by default.
- External emails sent on Brando's behalf CC `brando.science@gmail.com` for auditability.
- Add `brando9@stanford.edu` only when a Stanford/academic record is useful.
- Do not CC `brandojazz@gmail.com` unless Brando explicitly asks.

Also recognize `brando9@cs.stanford.edu`, `brando90@mit.edu`, `miranda9@illinois.edu`, `miranda9@ibm.com`, and `miranebr@amazon.com` as Brando aliases in the collaborator registry.

## Maintenance Rule

If an agent learns a durable collaborator email from Gmail or direct user instruction, update `~/ultimate-utils/py_src/uutils/collaborators.py` instead of leaving it in chat history. Then mention the update in the final response and, for non-trivial edits, run the usual repo QA/commit flow.
