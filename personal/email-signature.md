# Email Signature & Defaults

## Default send address
- **From:** whichever of Brando's accounts the agent already has signed in: the client's mail connector if it has one, otherwise SMTP from `brandojazz@gmail.com` (or a configured alias such as `brando.science@gmail.com`). Never hold an email for a particular sender address.
- **Every outgoing email:** explicitly BCC `brando.science@gmail.com`, `brando9@stanford.edu`, `brandojazz@gmail.com` and `brando@vals.ai`. Include all four even if an address is the sender or already in To; deduplicate only within BCC. This applies to every agent, project, external email and internal notification, with no project substitutions (Brando, 10-16-2026).
- **Primary recipients:** preserve intended addressees and collaborators' requested copies. Internal notifications use `To: brando.science@gmail.com`; existing notification triggers remain unchanged.
- **Visible copies:** CC requires an explicit request for that message and does not replace the four BCC entries unless Brando explicitly says so. Omit the former CC reply note; BCC does not automatically include recipients on later replies. Do not resend old emails merely to apply this policy. See Trigger Rule 26.
- **Update, Brando, 10-27-2026:** BCC `brando.science@gmail.com`, `brandojazz@gmail.com` and `brando9@stanford.edu` on every email, and always CC his personal address (address still to be confirmed by him; see Trigger Rule 26). This supersedes the four-address BCC and the explicit-request CC lines above.
- **Alias:** `brando9@cs.stanford.edu` is a Brando alias, but automation should follow `~/agents-config/INDEX_RULES.md` Trigger Rule 26 for routing.

## Voice rules for emails sent as Brando

- Write in first person as Brando. Never narrate about Brando in third person from Brando's own email account, e.g. never write "Brando approved this" or "Brando would like" when the message is from Brando.
- Be concise, friendly, and direct. Prefer plain sentences a human would actually send over assistant-y scaffolding.
- Avoid chatbot tells: "I hope this email finds you well", "as an AI", "approved this straightforward request", over-explaining why the email is being sent, or describing the approval workflow.
- If approval context is needed, translate it into first-person intent: "Could you please...", "I'm good with this plan", "Thanks, that works for me."
- Before sending, do a quick self-read: if the sentence would be weird for Brando to say himself, rewrite it.

## Closing summary

Every drafted or sent email ends its substantive body with `TLDR-end: [proj: task]` and 1–2 sentences, following [Hard Rule 4](../rules/responses.md#hard-rule-4). State the outcome and any real decision/deadline; do not invent an action or deadline. Put the summary after any decisions, links or verification evidence and immediately before the drafted-with sign-off and signature. For internal notifications that omit a signature under Rule 70, it is the final body text.

Before sending, check that the closing summary is present, matches the final body and precedes any sign-off/signature. An opening status sentence does not replace it. Keep existing send triggers; do not resend old emails just to change their format.

## Research-result emails

_Trigger: an agent emails collaborators about experiment or research results._ Collaborators asked for these to be interpretable, with less jargon and a slide (Varun, relayed by Brando, 10-16-2026).

- **Takeaway first, in plain words.** The first 2-3 sentences say what was tested, what was found and why it matters for the project. A collaborator who missed the last few meetings should get the point from them alone.
- **No internal labels in the body.** Do not put experiment slugs, run IDs, branch or folder names (e.g. `the-difficulty-confound`) in the collaborator-facing body; describe the idea in words. Expand every acronym and define every term of art on first use (Hard Rule 10). The full experiment folder name that [Trigger Rule 54](../rules/responses.md#trigger-rule-54) requires goes in the linked doc or report, and in the `TLDR-end:` line, which Brando reads.
- **Short.** After the takeaway: at most 5 bullets of key numbers, each against its baseline and with its uncertainty (Hard Rule 11), then one line on the next step. Methods and extra tables go in the linked doc, not the body.
- **One summary slide when there are results.** Make a one-slide Google Slides deck: a title that states the finding, the key plot or table, a one-line caption. Share it by link ([Trigger Rule 68](../rules/services.md#trigger-rule-68)) and put the link right after the takeaway. No results, no slide.

## Drafted-with sign-off

End every email sent as Brando to other people with the line `Brando (drafted with <agent>)`, where `<agent>` is the agent that actually drafted it: `Brando (drafted with Claude)` from Claude, `Brando (drafted with Codex)` from Codex, and so on (Antigravity, Grok, …), then the signature below. Brando uses many agents and is happy to say so; this line is not a chatbot tell (Brando, 10-09-2026).

## Signature

Append this signature to emails sent on Brando's behalf; preserve Rule 70's signature-free internal notifications:

```
-----
Brando Miranda
Ph.D. Student
Computer Science, Stanford University
EDGE Scholar, Stanford University
brando9@stanford.edu
website: https://brando90.github.io/brandomiranda/
```
