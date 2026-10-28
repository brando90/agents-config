---
name: review-paper
description: "Review an ML paper the way Brando does: judge whether it matters and is good evidence, name the experiments that would move the score, and write a kind but direct review. Use when asked to review, referee or give feedback on a paper (ICLR, NeurIPS, ICML, TMLR, workshop) or to draft a reviewer response."
---

# review-paper: Brando's way of reviewing an ML paper

**TLDR:** Read for the main claim, check the evidence claim by claim, name the one experiment that would change your mind, split major from minor issues, be kind but direct, and give a score with a confidence and what would raise it. Brando's own chat advice (10-20-2026) is the source; his words win over this file.

## When to use this skill

Brando, or someone he is helping (a student, a collaborator), has a paper to review: an ICLR (International Conference on Learning Representations), NeurIPS, ICML or TMLR submission, a workshop paper, or a draft a friend wants feedback on. Typical prompts:

> Review this paper (PDF / OpenReview link / path). Use the review-paper skill.
> I brain-dumped my thoughts on this paper, turn them into a professional review.

Inputs: the paper (link, path or PDF), the venue and its review form if known, and optionally Brando's raw notes. Do not block if some are missing. If there are no notes from Brando, you write a first review from the paper and label it as a draft for him.

## Philosophy (Brando's, keep it)

1. **Novelty is what venues want, so it matters most as a reviewer. Practicality is underappreciated, and Brando weights it more.** Novel alone is trivial: "I can count the quarters in my drawer and no one knows that, but who cares." Ask: do I actually think this matters? Is it good evidence?
2. **Independent judgment first.** A good reviewer has read many good papers and knows what it takes. Measure the paper against that, not against a rubric.
3. **Negative or imperfect results in the appendix, instead of hidden, are a green flag.** Say so in the review when you see it.
4. **It should be easy to understand, so writing matters.** AI helps writing, but to Brando AI-polished prose often makes a paper harder to read. Flag prose that is smooth but empty.
5. **Professional, kind but direct. Review the paper, not the people.**
6. **Authors will try to get accepted no matter what: their career depends on it.** So give them incentives to improve the work. The paper will very likely be accepted somewhere (even a workshop, even arXiv), so make it better. Tell them which experiments you want to see in order to shift your score, and if they run them, raise the score. Brando often does.
7. **Escalate broken promises.** If an author agrees to a change (for example toning down the title) and the camera-ready ignores it, escalate to the area chair or program chairs. This is rare. Do not threaten it in the first review.
8. **Brain-dump, then polish.** Brando often reads the paper, brain-dumps raw opinions, and has AI draft a professional version, because his raw take can be too opinionated. When doing that step: keep his claims and his strength of opinion, soften only the tone, add no new claims, and keep the result short and plain.

## Step by step (about 2-3 hours per paper; timebox it)

1. **Read once for the main claim, then write the summary in 3 lines.** If you cannot, that is already feedback for the authors (the paper is unclear).
2. **Check the evidence claim by claim.** For each claim ask: does the evidence actually support it? Look for held-out tests, baselines (strong and fairly tuned), seeds, error bars or confidence intervals, ablations, and whether the metric measures the claim. Overclaiming is the number one issue: compare the title, abstract and conclusion with what the tables show.
3. **Ask: what one experiment would change my mind?** Write it into the review. It is the most useful thing authors get. Make it concrete (which data, which baseline, which comparison) and feasible in a rebuttal window.
4. **Split into major and minor issues.** Major means it could flip the decision. Minor means typos, clarity, formatting, missing citations. Keep minor issues short, one line each.
5. **Be kind but direct.** Name what is good first and mean it. State problems plainly, with the evidence. No sarcasm, no guessing at motives.
6. **Give the score, your confidence in it, and what would raise it.** Example: "Score 5, confidence 3. I would go to 6 if the baseline is retuned and the result holds across 3 seeds."
7. **Check the tone and clarity.** Read the review as the author would. Cut the opinionated edges that do not help them improve the paper.

## Output template

```
Summary (3 lines): what the paper claims, how it tests it, what it finds.

What I like: 1-3 specific points (including honest negative results if present).

Major issues (could flip my decision):
1. <issue> - <evidence from the paper> - <what would fix it>
2. ...

The experiment that would change my mind: <one concrete experiment>.

Minor issues: <short bullets>

Score: <n>, confidence: <n>. Would raise it if: <specific things>.
```

Match the venue's own form fields if it has them (ICLR asks for summary, strengths, weaknesses, questions, rating, confidence). Read the official reviewer guide on the venue site first; for ICLR it is short and worth 5 minutes.

## Rules for the agent using this skill

- Do not invent facts about the paper. Quote the table, figure or section you rely on.
- Do not run code or experiments for a review unless Brando asks. Say which check you did not do.
- Do not paste confidential submission text into public places. Reviews of unpublished submissions stay private.
- Keep the review short enough to read in a few minutes. Plain words, no filler, no "delve" or "robust framework".
- Never submit a review on a venue site for Brando. Return the draft; he submits.
