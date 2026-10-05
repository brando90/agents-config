# Project background, citations, and credits

**Doc link:** <https://github.com/brando90/agents-config/blob/main/docs/reference/background.md>

**TLDR:** Preserved background from the earlier README: related projects,
citation records, and design credits. It is not part of the agent startup path.

The ecosystem comparisons and star counts below are historical context from
the earlier README, not freshly verified rankings or claims about another
project's current security. Follow current official documentation for tool use.
The paper discussion is retained with its observational caveat; it does not
claim this repository was experimentally evaluated.

## Related Work

The AI coding agent ecosystem is growing fast. Here's how `agents-config` relates to existing tools:

**Multi-Agent Orchestration** — [Ruflo](https://github.com/ruvnet/ruflo) (21.9K stars), [Agent Orchestrator](https://github.com/ComposioHQ/agent-orchestrator) (4.9K), [Emdash](https://github.com/generalaction/emdash) (2.8K), and [Gas Town](https://github.com/steveyegge/gastown) (12.6K) focus on *running* multiple agents — spawning, coordinating, and merging their work. `agents-config` is complementary: it standardizes the *documentation* agents read, not how they're orchestrated.

**Parallel Agent Execution** — [parallel-code](https://github.com/johannesjo/parallel-code) (387 stars) and [parallel-worktrees](https://github.com/SpillwaveSolutions/parallel-worktrees) run agents side-by-side in git worktrees. Our [`workflows/git-worktrees.md`](../../workflows/git-worktrees.md) describes the same pattern as portable documentation, including an example that combines worktrees with byobu.

**CLAUDE.md Templates & Best Practices** — [claude-code-templates](https://github.com/davila7/claude-code-templates) (23.2K stars), [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) (19K), [claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) (5.5K), and [claude-md-templates](https://github.com/abhishekray07/claude-md-templates) (95) provide example `CLAUDE.md` files and configurations. These are Claude-specific. `agents-config` is agent-agnostic (Layer 1 adapts per agent; Layers 2–3 are shared) and uses doc routing instead of a monolithic file.

**Curated Lists** — [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) (29.2K stars) and [awesome-claude-md](https://github.com/josix/awesome-claude-md) (159) catalog plugins, skills, and example configs across the ecosystem.

| Concern | Orchestration tools | Template repos | `agents-config` |
|:--------|:-------------------|:---------------|:-----------------|
| Runs agents | Yes | No | No |
| Provides agent docs | Sometimes | Yes (Claude-only) | Yes (agent-agnostic) |
| Scales past monolithic files | N/A | No | Yes (three-layer index) |
| Secrets stay out of repo | No | No | Yes (reference existing config files) |

---

## Citation

This repo is open source under the [Apache 2.0 License](../../LICENSE).

```bibtex
@misc{miranda2026agentconfig,
  author = {Brando Miranda and Claude (Anthropic) and Codex (OpenAI) and Cursor (Anysphere)},
  title = {Agent-Config: A Modular, Agent-Agnostic Documentation Architecture for Multi-Agent Coding Workflows},
  year = {2026},
  howpublished = {\url{https://github.com/brando90/agents-config}},
}
```

We list Claude (Anthropic), Codex (OpenAI), and Cursor (Anysphere) as co-authors because this system was designed collaboratively between human and AI agents. While AI co-authorship is not yet widely accepted in academic venues, we believe transparency about AI contributions is important and reflects the future of human-AI collaboration.

### Related paper by the author

**A Few Pages of Markdown: Committed AI Configuration and Lower Quality Cost after Coding-Agent Adoption.** Yegor Denisov-Blanch, Shyam Agarwal, Pavel Azaletskiy, Hao He, Rylan Schaeffer, Brando Miranda, Bogdan Vasilescu, Sanmi Koyejo. arXiv preprint arXiv:2608.25241, 2026. [[arXiv](https://arxiv.org/abs/2608.25241)] · [[Google Scholar](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=_NQJoBkAAAAJ&sortby=pubdate&citation_for_view=_NQJoBkAAAAJ:738O_yMBCRsC)]

Co-authored by this repo's author, this paper studies the same class of artifact `agents-config` provides: version-controlled configuration files that teams commit to their repositories to configure AI coding tools. It introduces RAMP (Repository AI Maturity Profile), a four-level cumulative maturity model running from behavioral rules and coding standards, through named agent definitions, to multi-agent orchestration, and applies it across 441 repositories. Among agent-first repositories, those *without* committed AI configuration show roughly twice the increase in cognitive complexity (+53% versus +27%); the authors note the maturity measure is observational and present the finding as hypothesis-generating. Its first author, Yegor Denisov-Blanch, is the same person credited in the Acknowledgments below.

The paper does not study or evaluate this repo — it is cited here as related work and as empirical context for the practice `agents-config` implements.

```bibtex
@misc{denisovblanch2026markdown,
  author = {Yegor Denisov-Blanch and Shyam Agarwal and Pavel Azaletskiy and Hao He and Rylan Schaeffer and Brando Miranda and Bogdan Vasilescu and Sanmi Koyejo},
  title = {A Few Pages of Markdown: Committed AI Configuration and Lower Quality Cost after Coding-Agent Adoption},
  year = {2026},
  eprint = {2608.25241},
  archivePrefix = {arXiv},
  primaryClass = {cs.SE},
  howpublished = {\url{https://arxiv.org/abs/2608.25241}},
}
```

---

## Acknowledgments

We thank [Yegor Denisov-Blanch](https://x.com/yegordb) for the original insight about modular, agent-agnostic documentation for multi-agent coding workflows, which inspired this project. (We plan to ask Yegor if he'd like to be listed as a co-author — pending his response.)
