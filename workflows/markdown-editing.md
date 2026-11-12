# Markdown editing: formatted text, real files

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/markdown-editing.md>

**TLDR:** Brando wants to edit the actual `.md` file while it looks formatted, retaining normal file actions such as Save and Copy Path. A separate read-only preview or an exported document copy is not equivalent; stock Zed's checked release does not provide that editing mode, while Suzuri documents a Zed-based implementation.

## Persistent preference

Brando, 11-12-2026: "I want it to behave as the normal .md file opening but just looks nice."

- Keep the original file and path as the source of truth, including files in Git repositories.
- Render headings, emphasis, lists, links and tables in the editable document. Revealing Markdown syntax near the cursor is compatible with this goal.
- Retain ordinary editing, saving, undo and file actions, particularly **Copy Path** and **Copy Relative Path**.
- Treat source-plus-preview as a workaround, not completion of this request.
- Store adopted editor settings and installation instructions in agents-config so the setup is reproducible. Recording this preference alone does not enable an editor feature.

## Zed: checked 11-12-2026

**Installed release checked: 1.28.1.** Its rendered `Preview <filename>.md` tab is a separate view, not an editable formatted text buffer. Brando's source-tab menu includes **Copy Path** and **Copy Relative Path**; his preview-tab menu omits them and includes **Show Source** instead.

**Immediate path workaround:** right-click the preview tab, choose **Show Source**, then right-click the source tab and choose **Copy Path** or **Copy Relative Path**. This returns to source editing; it does not add formatted editing.

The official extension registry search found `markdown-oxide`, `markdown-snippets`, `markdownlint` and `sanemark-markdown-lsp`, but no extension implementing this live-editing mode. The documented extension interfaces do not offer a custom editor surface. Markdown language servers, snippets and themes are not a replacement for that missing capability.

Upstream's [request for combined formatted editing](https://github.com/zed-industries/zed/issues/21717) remains open. The [proposed Obsidian-style implementation](https://github.com/zed-industries/zed/pull/62593) was **closed without merging**; its `markdown_live_preview.enabled` setting is not a supported stock-Zed setting in the checked release.

Sources: [versioned preview implementation](https://github.com/zed-industries/zed/blob/v1.28.1/crates/markdown_preview/src/markdown_preview_view.rs), [versioned extension interfaces](https://github.com/zed-industries/zed/blob/v1.28.1/docs/src/extensions/developing-extensions.md), [official extension registry](https://github.com/zed-industries/extensions/blob/main/extensions.toml).

## Closest Zed-based option: Suzuri

[Suzuri](https://suzuri.ai/) is a separate editor derived from Zed, **not a Zed extension**. Its [upstream README](https://github.com/harrywang/suzuri/blob/main/README.md) describes in-place Markdown rendering with source revealed at the cursor, editable tables and ordinary local files, alongside Zed's code-editor features. The author of the unmerged proposal points to Suzuri in the linked Zed issue.

This is the closest documented match to the requested Zed workflow, but the project labels itself early and in active development. **It was not installed or locally tested during this investigation.** Before calling a setup complete, verify editing and saving the same file, both path-copy actions, undo, links and tables. Keep that verification distinct from reading the vendor's feature list.

## Claude Desktop: distinguish a document from a file preview

Current [Claude artifact documentation](https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them) and [Claude Docs documentation](https://support.claude.com/en/articles/16923645-get-started-with-claude-docs) describe directly editable Docs artifacts with Markdown export. Therefore, "Claude Desktop cannot edit formatted documents" would be too broad.

An editable Docs artifact and its exported `.md` are not evidence that a local-file preview edits the original repository file in place. Establish which surface is open—Chat, Cowork, Code, a file preview or a Docs artifact—before recommending a setting. A separate artifact/export workflow does not meet the original-file requirement above.

## Persistence and implementation boundary

- Shared preference: this workflow, linked from the assistant skill and the Zed guide.
- Existing Zed configuration: [`dotfiles/zed/settings.json`](../dotfiles/zed/settings.json) and [`dotfiles/zed/keymap.json`](../dotfiles/zed/keymap.json), applied through the [dotfiles installer](../dotfiles/README.md).
- Investigation outcome on 11-12-2026: documentation saved; no application installed, editor setting changed or live-editing capability enabled. Recheck current upstream support before implementing a later setup.
