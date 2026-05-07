# Brando Personal Blog Writing Guide
**TLDR:** Voice, structure, and editing guide for turning Brando's rough ideas into sharp personal blog posts. Use this with `~/agents-config/writing/blog/rules.md`; use `~/agents-config/writing/blog/write-blog-post.md` when executing a full draft or edit.

---

## Writing Persona

Write as Brando at his best: technically serious, high-agency, direct, personal, and willing to take a position. The voice is not detached research prose and not marketing copy. It is a working researcher thinking in public.

The best posts feel like this:

- A real question has been bothering Brando.
- The post names the worry without softening it.
- A technical idea reframes the worry.
- The personal context makes the argument more credible, not more sentimental.
- The ending returns to the original question with a cleaner view than the opening had.

The target is not "polished content." The target is a post that has taste, stakes, and compression.

## When To Load

Load this guide for Brando's personal site at `~/brandomiranda/`, especially when the user gives rough ideas, asks for the scalable oversight / agents-config blog style, or wants a draft revised in Brando's recent voice. Do not use this as the primary format for Stanford AI Lab / SAIL research blog posts; those use `~/agents-config/workflows/blog-posts.md` unless the user explicitly asks for a personal-site adaptation.

---

## What The Recent Posts Do Well

### Scalable Oversight Post

`~/brandomiranda/_posts/2026-04-22-formal-methods-scalable-oversight.md` is the anchor for philosophical research essays.

Reusable moves:

- Open from a live conversation, not an abstract topic.
- Name the worry charitably before disagreeing with the frame.
- Introduce a structural move: make checking smaller by separating the human-readable question from the mechanical proof.
- Let the post go one level weirder than expected, then earn it with an explicit caveat.
- Close with honest uncertainty rather than fake certainty.

Use this shape when the idea is about oversight, understanding, agents, formal methods, human judgment, values, or what cannot be outsourced.

### Agents-Config Post

`~/brandomiranda/_posts/2026-04-13-correctness-gated-multi-agent-workflow.md` is the anchor for project and workflow posts.

Reusable moves:

- Open with the operational question Brando had to solve.
- Explain why the problem matters in his own work.
- Name the artifact clearly.
- Describe the system in concrete layers.
- List daily operating practices with bold lead-ins.
- End by connecting the tool back to the research program.

Use this shape when the idea is a repo, workflow, paper system, tool, community, benchmark, or launch.

---

## From Idea Dump To Post

When Brando dumps raw thoughts, do not preserve the order. Extract the argument.

1. **Find the live question.** What is he actually trying to answer? Write it as a blunt question.
2. **Find the stance.** What does he believe that a smart reader might not already believe?
3. **Find the personal stake.** Why does this matter to him specifically? Research area, workflow, teaching, collaborators, frustration, or ambition.
4. **Find the structural move.** What reframing makes the post interesting? "The question is not X, it is Y" is often the spine.
5. **Find the proof objects.** Links, repos, papers, figures, anecdotes, examples, tools, named people, or specific technical mechanisms.
6. **Choose the genre.** Personal research essay, project/workflow post, research-teaching essay, or contrarian/hot-take essay.
7. **Write a spine before prose.** Title, TL;DR, one-sentence thesis, and section headings.
8. **Draft in Brando's voice.** Use first person, active verbs, concrete nouns, and the strongest version of the claim the evidence supports.
9. **Run the badass pass.** Cut generic lines, sharpen section claims, add one memorable compression line, and remove caveat fog.
10. **Run the trust pass.** Verify facts and links; mark anything unresolved with `[TODO: ...]`.

---

## Canonical Structures

### Worry To Structural Move

Best for conceptual essays.

1. **Opening:** A conversation, worry, or repeated failure mode.
2. **The worry:** Say why the worry is legitimate.
3. **The structural move:** Reframe the problem so it becomes tractable.
4. **The extension:** Push the idea further than the reader expects.
5. **The limits:** Say what remains hard or unknowable.
6. **The landing:** State what the original worry becomes now.

### Built Thing To Research Program

Best for tools, workflows, repos, communities, or systems.

1. **Opening:** A practical problem Brando had.
2. **Why it matters:** The cost of the problem in real work.
3. **What I built:** Name the artifact and link it.
4. **How it works:** Concrete layers, components, or daily workflow.
5. **What I learned:** 2-4 claims that generalize.
6. **What's next:** The research frontier opened by the artifact.
7. **Connection back:** Why this fits Brando's larger agenda.

### Teach The Principle

Best for CS197/research-method posts.

1. **Failure mode:** What smart students or researchers get wrong.
2. **Principle:** The rule that fixes the failure mode.
3. **Worked example:** Show the principle operating on a real paper/project.
4. **Practical rules:** Specific advice.
5. **Takeaways:** Short bullets if the post is instructional.

---

## Components

### Title

Prefer titles that contain the conceptual move:

- "Asking the Right Question: Formal Methods as Scalable Oversight"
- "What I Learned Building a Correctness-Gated Multi-Agent Workflow for Research"

Avoid bland topic labels:

- "Thoughts on AI Agents"
- "Formal Methods and Oversight"
- "My Workflow"

### TL;DR

The TL;DR is mandatory for recent-post style. It should be 2-3 sentences and answer:

- What is the central question or problem?
- What is Brando's answer?
- Why should the reader care?

The TL;DR can contain a memorable compression line. It should not read like a paper abstract.

### Opening

Start where the post starts emotionally or operationally:

- A lab conversation.
- A repeated failure mode.
- A tool Brando built because the current way broke.
- A student confusion that reveals a deeper principle.
- A claim Brando keeps returning to.

Avoid "In today's world," "Recently," "Artificial intelligence is changing everything," or generic field summaries.

### Technical Explanation

Compress technical ideas into the smallest faithful explanation. Define the term, state why it matters, and connect it to the post's central question.

Good pattern:

1. Name the object.
2. Say what it checks or changes.
3. Say what the human no longer has to do.
4. Say what the human still must do.

### Opinion And Uncertainty

Use opinion markers when they increase trust:

- "I think..."
- "I suspect..."
- "To me..."
- "I genuinely don't know."

Do not bury the stance under hedging stacks. One honest uncertainty beats five timid caveats.

### Endings

Endings should feel inevitable, not appended.

Good endings:

- Return to the opening worry with a sharper formulation.
- Connect a built artifact to a research direction.
- State the human part that remains.
- Give the reader a practical takeaway.

Weak endings:

- Generic optimism.
- A summary of every section.
- "Only time will tell."
- A sales pitch.

---

## Sentence-Level Style

- Prefer active voice.
- Use contractions when natural.
- Prefer concrete verbs: built, checked, noticed, failed, changed, split, asked.
- Use short declarative sentences after dense explanations.
- Let a paragraph contain one main turn.
- Use rhetorical contrast: "The question is not X. It is Y."
- Use repetition deliberately when it structures the argument.
- Keep CS197 shorthand out of reader-facing prose unless the post teaches that shorthand directly.

---

## Badass Pass

Run this after the first coherent draft:

1. **Quote test:** Which 2-3 lines would someone quote? If none exist, write sharper compression lines.
2. **Anyone test:** Could this paragraph appear in any AI blog? If yes, add Brando's specific stake, artifact, or view.
3. **Tour test:** Is any section merely listing facts? Turn it into a claim.
4. **Caveat test:** Does uncertainty clarify or weaken? Keep honest uncertainty; delete apologetic fog.
5. **Opening test:** Does the first paragraph begin at the actual tension? Cut setup until it does.
6. **Ending test:** Does the ending transform the opening? If it only summarizes, rewrite.

---

## Trust Pass

Before publishing or handing back a file:

- Verify all links resolve or mark them `[TODO: verify link]`.
- Verify dates, names, paper titles, repo names, author names, and numerical claims.
- Preserve Markdown and Jekyll frontmatter.
- Keep user-written untracked drafts unless explicitly told to overwrite them.
- If facts are missing, keep drafting but mark them with `[TODO: exact fact/source]`.

---

## Relationship To Other Writing Docs

- Use `~/agents-config/writing/blog/rules.md` as the compact checklist.
- Use `~/agents-config/writing/blog/write-blog-post.md` for full execution from rough ideas to draft.
- Use `~/agents-config/workflows/blog-posts.md` only for SAIL-style research lab blog posts; it has different structure and artifact expectations.
- Use `~/agents-config/writing/ml_research/ml_research_writing.md` when the work becomes a top-venue paper, not a personal blog post.
