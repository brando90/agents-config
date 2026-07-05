# CoDaPO — EN Twitter / X Thread (gold-standard example)

**TLDR:** The reference X-thread example for `write-tweet-thread.md`, supplied verbatim by Brando on 2026-07-04 (source: collaborator Google Doc). Structure: hook → GRPO inefficiency → diagnosis → method → components → results → generalization → open source.

**Provenance:** pasted by Brando into the Claude Code session of 2026-07-04; original lives in a collaborator Google Doc (docs.google.com/document/d/1TIxqrC8MKu63cOt_BZNf8R14JISHmhxvGv-lArRGqZI). Content below unmodified.

---

> Requirement: each tweet ≤ 280 characters.
> Links: GitHub live; arXiv = `arxiv.org/abs/2606.07950`.
> Author @-handles intentionally omitted for now.

---

1/8: Overview 🚀

Excited to share our new paper: The Easy, the Hard, and the Learnable: Confidence and Difficulty-Adaptive Policy Optimization for LLM Reasoning. RL with verifiable rewards treats easy, hard & learnable questions alike. We show why that wastes compute and how to fix it. 🧵

---

2/8: Why GRPO can be inefficient 🔍

We track GRPO's training dynamics and find 3 recurring patterns:
1️⃣ Confidence inflation (entropy collapse, worse calibration)
2️⃣ Advantage contraction (positive signals vanish as accuracy increases)
3️⃣ Hierarchical convergence (easy saturates, hard stays stuck)

---

3/8: The diagnosis 🧠

1️⃣Uniform sampling + near-uniform weighting misallocates compute.
2️⃣Solved questions keep getting updates that only inflate confidence.
3️⃣Truly hard questions are discovery-limited: with small rollout groups, a single correct trajectory is rarely even sampled.

---

4/8: Meet CoDaPO 💡

A simple, data-centric method that plugs into GRPO-style RL. It scores each question with two free signals from rollouts—confidence (mean token likelihood) & difficulty (group error rate)—into a bounded value v = c·(1−4(d−½)²) used to reweight & resample.

---

5/8: Three components ⚙️

🔧 CoDaWeighting: per-question value concentrates gradients on the "learnable band"
🎯 CoDaSampling: resample top-K high-value questions → boosts discovery of rare correct rollouts
🔁 CoDaLearning: value-weighted, two-stage update (coverage + focus)

---

6/8: Results 📊

Across 12 benchmarks, CoDaPO consistently beats GRPO, DAPO, Dr.GRPO & GPG under the SAME compute budget.
On Qwen2.5-Math-1.5B: MATH500 30.6%→71.5%, OlympiadBench (OOD) 18.8%→36.2%, 7-bench avg 16.6%→41.3%.

---

7/8: Generalization 🌐

Gains transfer beyond math:
📈 MMLU/GPQA/HumanEval avg 32.6%→40.0% over GRPO
💻 Coding (HumanEval/TACO/LiveCodeBench) 50.1%→53.9%
🔢 AIME25 Pass@128 → 53.3%
And it scales: works on Llama-3.2-1B up to Qwen2.5-14B. Zero extra inference cost.

---

8/8: Open source 🤝

CoDaPO is a drop-in upgrade for GRPO/DAPO/GPG—no KL term, bounded weights, stable training.
📄 Paper: arxiv.org/abs/2606.07950
🐙 Code: github.com/tmlr-group/CoDaPO
Accepted at ICML 2026. We'd love your feedback & contributions!
