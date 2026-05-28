# Email Signature & Defaults

## Default send address
- **From:** `brandojazz@gmail.com` by default for SMTP delivery unless a workflow explicitly sets a configured alias such as `brando.science@gmail.com`.
- **Internal agent notifications to Brando:** `To: brando.science@gmail.com`, no CC by default.
- **External emails sent on Brando's behalf:** CC `brando.science@gmail.com` for auditability; add `brando9@stanford.edu` only when a Stanford/academic record is useful; do not CC `brandojazz@gmail.com` unless Brando explicitly asks.
- **Alias:** `brando9@cs.stanford.edu` is a Brando alias, but automation should follow `~/agents-config/INDEX_RULES.md` Trigger Rule 26 for routing.

## Voice rules for emails sent as Brando

- Write in first person as Brando. Never narrate about Brando in third person from Brando's own email account, e.g. never write "Brando approved this" or "Brando would like" when the message is from Brando.
- Be concise, friendly, and direct. Prefer plain sentences a human would actually send over assistant-y scaffolding.
- Avoid chatbot tells: "I hope this email finds you well", "as an AI", "approved this straightforward request", over-explaining why the email is being sent, or describing the approval workflow.
- If approval context is needed, translate it into first-person intent: "Could you please...", "I'm good with this plan", "Thanks, that works for me."
- Before sending, do a quick self-read: if the sentence would be weird for Brando to say himself, rewrite it.

## Signature

Append this signature to every email sent on Brando's behalf:

```
-----
Brando Miranda
Ph.D. Student
Computer Science, Stanford University
EDGE Scholar, Stanford University
brando9@stanford.edu
website: https://brando90.github.io/brandomiranda/
```
