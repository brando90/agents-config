# Conventions: Agent Prompt Builder Rules

<!-- TODO: owner has additional ideas to add -->

Meta-rules for writing effective agent instruction files (CLAUDE.md, agents.md, experiment prompts).

---

## Structure

A good agent prompt has four sections, in this order:

1. **Context** — What is this project? What are you doing? One paragraph max.
2. **Constraints** — Hard rules the agent must follow. Non-negotiable. Keep this short and high-signal.
3. **Task** — What specifically to do. Concrete steps, file paths, commands.
4. **Output** — What the deliverable looks like. File names, formats, where to save.

---

## Rules for Writing Prompts

### Be concrete, not abstract
Bad: "Write good code."
Good: "Use `fire.Fire()` for CLI argument parsing. Save output to `expt_results/scores.csv`."

### Include file paths
Agents work with files. Give them exact paths, not descriptions.
Bad: "Put it in the results folder."
Good: "Save to `experiments/04_exp/expt_results/correlation_summary.json`."

### Specify what NOT to do
Agents are eager. Tell them what to skip.
Example: "Do not refactor surrounding code. Do not add docstrings to unchanged functions. Do not create new files unless explicitly required."

### Use constraints, not suggestions
Bad: "It would be nice if you used the latest model."
Good: "Always use Claude Opus 4.6 or GPT-5.4+. Never use deprecated models (GPT-4o, GPT-4.5)."

### Include examples
Show the format you want. Agents match patterns.
```
Output your score on the LAST line in exactly this format:
JUDGE_SCORE: 3
```

### Link to reference docs
If the agent needs to understand an external system (Harbor, W&B, etc.), provide a URL. This reduces hallucination.
```
Harbor framework docs: https://harborframework.com/
```

---

## When to Use Opus vs Sonnet

| Use Case | Model | Why |
|:---------|:------|:----|
| Architecture decisions | Opus | Needs deep reasoning about trade-offs |
| Experiment design | Opus | Complex multi-step planning |
| Writing prompts for other agents | Opus | Meta-cognitive task |
| Code review | Opus | Needs to reason about correctness |
| Straightforward edits | Sonnet | Faster, cheaper, sufficient for mechanical changes |
| Renaming, reformatting | Sonnet | No deep reasoning needed |
| Running established patterns | Sonnet | Following existing conventions |
| Bulk file operations | Sonnet | Repetitive, well-defined tasks |

Default to Opus when uncertain. The cost of using a weaker model on a complex task is higher than the cost of using a stronger model on a simple task.

---

## Anti-Patterns

- **Wall of text with no structure.** Use headers, code blocks, and tables. Agents parse structured text better than prose.
- **Contradictory instructions.** "Use Harbor for everything" + "Make direct API calls for speed." Pick one.
- **Assuming context.** The agent starts fresh each session. Include file paths, not "the file we were working on."
- **Mixing tasks.** One prompt, one task. Don't ask the agent to "fix the bug and also refactor the tests and update the docs."
- **Vague output format.** "Give me the results" → the agent will pick a format you don't want. Specify CSV columns, JSON structure, markdown table format.
