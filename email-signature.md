# Email Signature & Defaults

## Default send address
- **From:** whichever of Brando's accounts the agent already has signed in: the client's mail connector if it has one, otherwise SMTP from `brandojazz@gmail.com` (or a configured alias such as `brando.science@gmail.com`). Never hold an email for a particular sender address.
- **Every outgoing email:** explicitly BCC `brando.science@gmail.com`, `brando9@stanford.edu`, `brandojazz@gmail.com` and `brando@vals.ai`. Include all four even if an address is the sender or already in To; deduplicate only within BCC. This applies to every agent, project, external email and internal notification, with no project substitutions (Brando, 10-16-2026).
- **Primary recipients:** preserve intended addressees and collaborators' requested copies. Internal notifications use `To: brando.science@gmail.com`; existing notification triggers remain unchanged.
- **Visible copies:** CC requires an explicit request for that message and does not replace the four BCC entries unless Brando explicitly says so. Omit the former CC reply note; BCC does not automatically include recipients on later replies. Do not resend old emails merely to apply this policy. See Trigger Rule 26.
- **Alias:** `brando9@cs.stanford.edu` is a Brando alias, but automation should follow `~/agents-config/INDEX_RULES.md` Trigger Rule 26 for routing.

## Voice rules for emails sent as Brando

- Write in first person as Brando. Never narrate about Brando in third person from Brando's own email account, e.g. never write "Brando approved this" or "Brando would like" when the message is from Brando.
- Be concise, friendly, and direct. Prefer plain sentences a human would actually send over assistant-y scaffolding.
- Avoid chatbot tells: "I hope this email finds you well", "as an AI", "approved this straightforward request", over-explaining why the email is being sent, or describing the approval workflow.
- If approval context is needed, translate it into first-person intent: "Could you please...", "I'm good with this plan", "Thanks, that works for me."
- Before sending, do a quick self-read: if the sentence would be weird for Brando to say himself, rewrite it.

## Drafted-with sign-off

End every email sent as Brando to other people with the line `Brando (drafted with <agent>)`, where `<agent>` is the agent that actually drafted it: `Brando (drafted with Claude)` from Claude, `Brando (drafted with Codex)` from Codex, and so on (Antigravity, Grok, …), then the signature below. Brando uses many agents and is happy to say so; this line is not a chatbot tell (Brando, 10-09-2026).

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
