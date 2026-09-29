# ml-research-practice.md — Expect-then-verify ML research skill

**TLDR:** Before you run any ML experiment, evaluation or judge study, write down what every measurement should read, including the score of an agent that follows your instructions *exactly*. Then look at the raw outputs, run controls, and treat every gap between expected and observed as a bug until you can explain it. The lessons are Rylan Schaeffer's CS229 lecture (02-19-2025), turned into checks. They are hardened against the VeriBench `sorry`-mandate defect Amy Lu found in 08-2026, which none of these checks were in place to catch.

## References (origin)

- Source lecture: Rylan Schaeffer, Stanford CS229 guest lecture on ML advice, 02-19-2025: <https://www.youtube.com/watch?v=sl55buSIJPA&list=PLB3sDpSRdrOs7Ea9wIgWqKOsFNWJehlvK&index=12&t=1031s>. A linked transcript is in [`assets/rylan_schaeffer_cs229_ml_advice_02-19-2025_transcript.md`](assets/rylan_schaeffer_cs229_ml_advice_02-19-2025_transcript.md); the verbatim YouTube copy and its generator stay in `brando90/veribench` (private), `docs/research_skills/01_rs_ml_research_skill_file/`.
- Lecture slides ("ML Advice", 84 slides): <https://docs.google.com/presentation/d/1kTg6SSm4TRbogwz18_CtanJftYsj8Khx6W8UJQbQgYI/edit?usp=sharing>. [`assets/rylan_schaeffer_cs229_ml_advice_02-19-2025_slide_index.md`](assets/rylan_schaeffer_cs229_ml_advice_02-19-2025_slide_index.md) maps every slide to its sources, its moment in the talk and the step below. It also lists the lessons that appear only in the slides.
- Sources behind each step, as cited on the slides:

  | Step | Sources |
  |---|---|
  | 1, 6: understand your measurements | GPT-3, Brown et al. 2020, <https://arxiv.org/abs/2005.14165>; Ganguli et al. 2022, <https://arxiv.org/abs/2202.07785>; Wei et al. 2022, <https://arxiv.org/abs/2206.07682>; the talk's metric reanalysis, Schaeffer, Miranda and Koyejo 2023, <https://arxiv.org/abs/2304.15004> |
  | 3: leaky abstractions | Karpathy, "Yes you should understand backprop", 2016, <https://karpathy.medium.com/yes-you-should-understand-backprop-e2f06eab496b>; Adept on silent data corruption, <https://web.archive.org/web/20230920160929/https://www.adept.ai/blog/sherlock-sdc> |
  | 5: look at your data | CLIP, Radford et al. 2021, <https://arxiv.org/abs/2103.00020>; Hernandez et al. 2022 on repeated data, <https://arxiv.org/abs/2205.10487>; critical batch size, McCandlish et al. 2018, <https://arxiv.org/abs/1812.06162> |
  | 7: optimize toward the right thing | Ouyang et al. 2022, <https://arxiv.org/abs/2203.02155>; Gao et al. 2023, <https://arxiv.org/abs/2210.10760>; Lilian Weng, "Reward Hacking in Reinforcement Learning", 2024, <https://lilianweng.github.io/posts/2024-11-28-reward-hacking/>; Goodhart's law, <https://en.wikipedia.org/wiki/Goodhart%27s_law> |
  | 8: report distributions, not the best run | Agarwal et al. 2021, "Deep Reinforcement Learning at the Edge of the Statistical Precipice", <https://arxiv.org/abs/2108.13264> |
  | 10: hill-climb the right hills | Anton Osika's tweet of 10-22-2024 recalling Jonas Adler on AlphaFold (slide 28); Sutton, "The Bitter Lesson", 2019, <http://www.incompleteideas.net/IncIdeas/BitterLesson.html> |
- Motivating failure: `brando90/veribench`, `research_archive/experiments/70_fixing_judge_sepc_amy_spotted_mistake/ISSUE_MAP.md` (Amy Lu, 08-18-2026) and `experiments/101_neurips_te1_judge_validation_audit/README.md`.
- Sibling skill: [`llm-judge-recipe.md`](llm-judge-recipe.md) (Karpathy's recipe applied to building and validating LLM judges).

## When to use this skill

Load it whenever you:
- design, launch or interpret an experiment, benchmark evaluation, agent evaluation, LLM-judge or reward-model study;
- change a prompt, harness, scaffold, scorer, parser, judge or dataset that feeds a reported number;
- write a results table, a scoreboard row, or a paper claim;
- see a number that is surprising, "interesting", too good, too bad, or suspiciously stable.

## The one question that would have caught Amy's bug

Rylan at [16:55](https://www.youtube.com/watch?v=sl55buSIJPA&t=1015s):

> "when I say understand your measurements, I mean ask yourself what is the behavior that you should expect? And then ask whether or not what comes out is what you should expect."

**What happened.** VeriBench's gold-file authoring convention let reference theorems end in `sorry`. The plan had specialized provers fill proofs in a later stage. That convention was copied into the *solver* prompt, which told agents to write `theorem … := sorry` and called a compiling file a success. The scorer, correctly, gave proof credit (IC_proofs, then IC₂/IC_pp) only to theorems proved without `sorry`.

- **Expected:** an agent that obeys the prompt scores IC_proofs = 0. Amy reproduced exactly that on an obedient run.
- **Observed:** the published NeurIPS 2026 table showed clearly nonzero values: Codex 0.237, Claude Code 0.114, and the single-call baseline 0.282. The baseline's one-shot example happened to be fully proved.
- **What the nonzero number actually measured:** how often each agent *disobeyed* its own instructions, which correlates with capability. It also mixed in systems that had been given different instructions. It looked like agents "genuinely attempting the task" and was read that way.

**The check that catches it before any run:** "what does an agent that follows our prompt exactly score?" If the answer isn't the best achievable score, the instructions and the metric contradict each other, and the experiment can't measure what it claims. **The check that catches it after the run:** "why isn't IC_proofs zero?" Brando asked Amy exactly this on 08-19-2026, after publication. Asking it the day the first number arrived would have cost minutes.

## Procedure (in order; each step names the lecture lesson behind it)

### 1. Write the measurement contract before anything runs (understand your measurements; pre-register)

For every metric you will report, commit a table with its one-line definition, the exact code path that computes it, its range, and **predicted values** under:
- **(a) oracle:** the gold or reference submission;
- **(b) intended behaviour:** a competent solver doing what you hope;
- **(c) literal compliance:** a submission that follows the delivered instructions word for word, including every example and "you may" clause;
- **(d) degenerate submissions:** empty, copy the input, a vacuous claim (`theorem t : True`), everything left as a placeholder, restating the implementation;
- **(e) your baselines.**

Decision rules:
- **(c) below the best achievable score:** instructions and metric disagree; fix before running.
- **(d) scoring well:** the metric is gameable; add controls or guards before running.
- **You cannot predict a value at all:** you don't understand the measurement yet; stop and read the code.

Rylan at [50:11](https://www.youtube.com/watch?v=sl55buSIJPA&t=3011s): "you would want to pre-register your prediction … Commit it. Now I'm going to go run the experiment and see how well my prediction works."

### 2. Check the delivered instructions against the metric (two audiences, one prompt)

- Read the prompts the harness actually delivers: the rendered task instruction, scaffold text, one-shot examples, repair and continuation messages. Templates and version stamps are not enough.
- For each instruction, ask: does following it lower any reported score? Does any example demonstrate something the metric penalizes? Does the stated success criterion differ from the metric?
- Keep audience-specific conventions out of solver prompts: authoring rules for references, grader rubrics, internal plans such as "provers fill the placeholders later". Amy's bug was exactly this leak.
- Give every compared system equivalent instructions and examples, or report the difference as a confound.

### 3. Trace one example end to end, by hand (ML abstractions are leaky)

Follow one item from the prompt as delivered → transcript → captured output file (hash) → extractor → the scorer branch taken → judge prompt and parsed response → the aggregate cell. Check that each hop's input is the previous hop's output, byte for byte.

- **Why:** ML pipelines fail without errors. Rylan at [41:46](https://www.youtube.com/watch?v=sl55buSIJPA&t=2506s): "there are no errors. The tensors were all appropriately shaped. Losses were computed. They went down. Everything seemed fine." A healthy-looking curve is the scariest one ([51:58](https://www.youtube.com/watch?v=sl55buSIJPA&t=3118s)): "it looks like nothing is wrong, but we don't actually know that."
- At [1:01:19](https://www.youtube.com/watch?v=sl55buSIJPA&t=3679s): "in ML you need to know everything and you need to be comfortable debugging everywhere."

### 4. Run controls on a small smoke set before scaling (be paranoid; one risk at a time)

On 1–5 items, the following must each land where step 1 predicted:
- a positive control (gold scores near the maximum);
- negative controls (empty, vacuous and shuffled score near zero);
- the literal-compliance submission;
- a known-bad submission.

Only then scale up. Change one thing at a time ([1:08:38](https://www.youtube.com/watch?v=sl55buSIJPA&t=4118s): "take one risk at a time").

### 5. Look at your data, across the whole score range (look at your data)

Rylan at [7:40](https://www.youtube.com/watch?v=sl55buSIJPA&t=460s) calls this "the fundamentally most important thing about any machine learning … Look at your data."
- After every run, read raw outputs stratified by score: zeros, perfect scores, the middle, the top scorers and the outliers. Keep reading until the mixture of behaviours is clear; 20–30 stratified examples is a typical minimum.
- Count behaviours explicitly, for example: share of theorems left as placeholders, share with attempted proofs, share that restate the implementation.
- Build the tooling to look quickly: Jason Wei's point at [11:04](https://www.youtube.com/watch?v=sl55buSIJPA&t=664s).
- Decide how much evidence is enough like a critical batch size ([1:16:01](https://www.youtube.com/watch?v=sl55buSIJPA&t=4561s)): collect until the direction is clear, not forever.

### 6. Compare observed with expected; every mismatch is a bug until explained (don't fool yourself)

- Put the step-1 table next to the results. Any gap beyond noise, in either direction, stops interpretation until you can name the mechanism.
- Rylan at [41:31](https://www.youtube.com/watch?v=sl55buSIJPA&t=2491s): "if things are too good to be true, it's because you screwed up." The same holds for results that are too bad, too flat, or too consistent.
- Check whether the *form* of the metric makes the pattern. His emergence example ([17:12](https://www.youtube.com/watch?v=sl55buSIJPA&t=1032s) to [26:53](https://www.youtube.com/watch?v=sl55buSIJPA&t=1613s)) shows how: all-or-nothing accuracy over L tokens behaves like pᴸ and manufactures sudden jumps. Thresholds, geometric means, conjunctive scores, multiplication by a zero factor and a judge's coarse score levels do the same. "Based on the metric you choose, you should understand, you should expect what sort of outcomes are reasonable."

### 7. Assume every metric will be gamed (optimize toward the right thing)

A measure that becomes a target stops measuring well (Goodhart; [32:54](https://www.youtube.com/watch?v=sl55buSIJPA&t=1974s)). Inspect the top scorers for hacks: hyphenated "one-word" answers, emoji-only replies, trivial or restated theorems, compiler-trusting tactics, custom axioms, deleted claims. Optimize toward what you care about, not the proxy.

### 8. Don't change the hill because you dislike the result (climbing the wrong hills)

In the 2048 story ([38:12](https://www.youtube.com/watch?v=sl55buSIJPA&t=2292s)): "In this case, they didn't like the result. So they changed the task that we were doing."
- Keep honest zeros and failed cells in the denominator.
- Report distributions over repeats, not the best run (deep RL at the edge of the statistical precipice, [42:08](https://www.youtube.com/watch?v=sl55buSIJPA&t=2528s)).
- If the task, prompt, scorer or budget must change, make it a new, versioned condition and say why. Never retrofit it onto the old numbers.

### 9. Use consistency as your debugger (be paranoid)

Rylan at [1:08:17](https://www.youtube.com/watch?v=sl55buSIJPA&t=4097s): "probably the best debugger is consistency … something should equal itself."
- The same input should get the same score.
- Recompute every table from raw artifacts.
- Two implementations should agree.
- Mappings should be one-to-one; assert it. VeriBench once collapsed 24 of 28 security units onto 4 references.
- Hashes should bind every artifact to the number it produced.

### 10. Move fast on the right hill (iteration velocity; hill-climb the right hills)

"Iteration velocity is the best predictor of success" ([1:07:25](https://www.youtube.com/watch?v=sl55buSIJPA&t=4045s)). The AlphaFold habit ([34:04](https://www.youtube.com/watch?v=sl55buSIJPA&t=2044s)): "find something wrong, find a bottleneck, fix it, repeat." Small, fast, checked iterations beat large unchecked ones. The checks above are what make speed safe.

## Measurement-contract template (commit before running; fill "observed" after)

| Metric | Code path | Oracle | Intended | Literal compliance | Degenerate (empty / vacuous / all-placeholder) | Baseline | Observed | Match? | Explanation if not |
|---|---|---|---|---|---|---|---|---|---|
| e.g. IC_proofs | `scripts/scsc/run_real_eval.py` | 1.0 | ≈ 0.9 | **0 if the prompt says "use `sorry`"** | 0 / 1.0 on its own trivial theorem / 0 | … | 0.237 | **No** | agents disobeyed the prompt; the metric measured disobedience |

## Red flags that stop a run or a claim

- The literal-compliance prediction is below the best achievable score.
- A metric is nonzero where the instructions imply zero, or the reverse.
- Compared systems saw different instructions, examples or budgets.
- A control lands outside its predicted range.
- A factor sits at the same value for everyone, at 1.0 or at 0.
- A score distribution collapses onto a few values. VeriBench's NeurIPS coverage judge put 85–87% of tasks at exactly 0.1, much of it probably a parser artifact.
- The judge's inputs differ from what the humans rated. VeriBench's judges saw a later reference snapshot than the raters on 9 of 25 tasks.
- A result rests on a subset, with missing or failed cells quietly dropped.
- You cannot explain a number in one sentence from the raw outputs.

## Worked examples from VeriBench (what each check would have caught)

| Failure | Check that catches it | Cost of missing it |
|---|---|---|
| Solver prompt mandated `sorry` while IC_proofs zeroes it (Amy Lu, 08-2026) | Steps 1–2: literal compliance predicts 0; the prompt contradicts the metric | Published proof and aggregate scores confounded by disobedience; agents re-run under a corrected prompt |
| NeurIPS coverage judge: 85–87% of task scores exactly 0.1; a loose parser mapped prose answers to "1/10" | Step 6: look at the score distribution; step 3: trace one parse | Coverage numbers that meant little, read as "frontier agents are unsaturated" |
| Judges fed a 09-03 reference snapshot while raters saw April–May references (9 of 25 tasks differ) | Step 3: diff the exact judge input against the rater input | Weeks of negative judge-validation studies (experiments 75, 83, 92, 92c) that were confounded from the start |
| Security units collapsed onto 4 references by a prefix match | Step 9: assert one-to-one mappings | Wrong references for most security tasks until fixed |

## Checklist (paste into an experiment's README or protocol)

- [ ] Measurement contract committed (oracle / intended / literal-compliance / degenerate / baseline predictions).
- [ ] Delivered prompts read for every system; no instruction lowers a score; systems comparable.
- [ ] One item traced end to end, byte for byte.
- [ ] Controls pass on a smoke set, including the literal-compliance submission.
- [ ] Raw outputs read across the score range; behaviours counted.
- [ ] Observed matches predicted, or every gap has a named mechanism.
- [ ] Top scorers inspected for hacks.
- [ ] No task, prompt or scorer changed to rescue a result; changes are new, labeled conditions.
- [ ] Consistency checks pass (recompute from raw, one-to-one mappings, hashes).

TL;DR: Predict every metric first, including the score of perfect instruction-following, then look at the outputs and treat any gap as a bug. That single habit, "what should I expect, and is that what came out?", would have caught the `sorry`-mandate defect before it reached a paper.
