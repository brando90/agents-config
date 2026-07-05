# CoDaPO — EN LinkedIn (gold-standard example)

**TLDR:** The reference LinkedIn example for `write-linkedin-post.md`, supplied verbatim by Brando on 2026-07-04. Structure: excitement + title + venue → all-author institutional credit → problem → diagnosis → ➡️ method components → exact-number results bullets → links + hashtags.

**Provenance:** pasted by Brando into the Claude Code session of 2026-07-04. Content below unmodified.

---

> Links: GitHub live; arXiv = `arxiv.org/abs/2606.07950`.

---

We are excited to share our new paper, accepted at ICML 2026: **"The Easy, the Hard, and the Learnable: Confidence and Difficulty-Adaptive Policy Optimization for LLM Reasoning"**!

This work is a collaboration led by researchers from the TMLR Group of Hong Kong Baptist University (Zhanke Zhou, Xiangyu Lu, Chentao Cao, Bo Han), together with collaborators from Stanford University (Brando Miranda, Sanmi Koyejo) and the Sydney AI Centre, The University of Sydney (Tongliang Liu).

RL with verifiable rewards can substantially improve LLM reasoning, yet standard GRPO-style training treats easy, hard, and learnable questions alike through uniform sampling and weighting—leading to inefficient compute allocation. We ask a simple question: under a fixed compute budget, which questions deserve more trials, and which updates deserve more emphasis?

**First, a diagnosis of GRPO's training dynamics.**
By tracking token log-probabilities, group-normalized advantages, and the induced update weights, we identify three recurring patterns:
- **Confidence inflation:** confidence concentrates near 100% for both correct and incorrect outputs, degrading calibration.
- **Advantage contraction:** as groups become more accurate, positive advantages shrink toward zero while rare failures carry large negatives.
- **Hierarchical convergence:** easy questions saturate quickly, while hard ones remain discovery-limited and improve slowly.

**Then, the method: CoDaPO.**
CoDaPO is a simple, data-centric method that plugs into standard RL objectives. It assigns each question a bounded value from two signals readily available in rollouts—confidence (mean token likelihood) and difficulty (group error rate)—and uses it in three complementary ways:

➡️ **CoDaWeighting** rescales policy-gradient updates, concentrating gradient mass on the "learnable band" of intermediate-difficulty questions.
➡️ **CoDaSampling** resamples the top-K high-value questions within each mini-batch, allocating more trials to increase the chance of discovering rare correct trajectories.
➡️ **CoDaLearning** applies a value-weighted, two-stage update that preserves broad coverage while focusing compute where learning potential is highest.

Crucially, both signals are already computed during GRPO—so CoDaPO adds **zero extra inference cost**, keeps training stable through bounded weights, and reallocates compute *within* the same budget rather than increasing it.

**Empirical Results**
Across twelve reasoning benchmarks, CoDaPO consistently outperforms GRPO, DAPO, Dr. GRPO, and GPG under comparable budgets:
- **Mathematics:** On Qwen2.5-Math-1.5B, MATH500 accuracy rises from 30.63% → 71.54%, OlympiadBench (out-of-domain) from 18.78% → 36.16%, and the 7-benchmark average from 16.55% → 41.30%.
- **Scaling:** Effective from Llama-3.2-1B-Instruct up to Qwen2.5-Math-7B (best average 46.67%) and Qwen2.5-14B-Instruct (45.61% → 47.32%).
- **Cross-domain generalization:** On MMLU / GPQA / HumanEval, average improves from 32.64% → 39.96% over GRPO.
- **Test-time scaling & code:** AIME25 Pass@128 reaches 53.33%; coding tasks improve from 50.09% → 53.85%.

CoDaPO is a drop-in upgrade: the same value-weighted rule consistently improves GRPO, DAPO, and GPG.

**Explore the work:**
- 📄 Paper: https://arxiv.org/abs/2606.07950
- 💻 GitHub: https://github.com/tmlr-group/CoDaPO

We welcome contributions and feedback!

#LLM #ReinforcementLearning #LLMReasoning #GRPO #MachineLearning #ICML2026 #AIResearch #OpenSource
