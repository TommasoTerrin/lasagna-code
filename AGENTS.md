# Agent Instructions

## Skills bootstrap

At the start of every conversation, load the `using-superpowers` skill with the
`skill` tool (`id: "using-superpowers"`) before any other response or action,
and follow it.

The project skills live in `.claude/skills/` (a vendored subset of
Superpowers v7.0.2, see `.claude/skills/THIRD_PARTY_NOTICES.md`). When a skill
refers to `superpowers:<name>`, it means the skill `<name>`: load it with the
`skill` tool using the bare id (`superpowers:brainstorming` → `id: "brainstorming"`).

## Tool mapping (OpenCode V2)

Skills speak in actions rather than naming any one runtime's tools. This
mapping applies to OpenCode only (V2, 2.0.4 or later); Claude Code uses its own
native tools (see `CLAUDE.md`). In OpenCode they map to these tools:

- "Create a todo" → V2 has no todo tool of any kind; track the plan in a
  markdown file (or the harness's plan facility) instead.
- `Subagent (general-purpose):` template → OpenCode's `subagent` tool with
  `agent: "general"` (or `"explore"`); pass `sessionID` to continue a previous
  subagent.
- "Invoke a skill" → OpenCode's native `skill` tool with the bare skill id
  (`superpowers:brainstorming` → `id: "brainstorming"`).
- "Read a file" → `read`.
- "Create, edit, or delete files" → use `patch` with `patchText` when
  available; otherwise use `write` to create or overwrite files, `edit` for
  targeted changes, and `shell` for deletion.
- "Run a shell command" → `shell` (`command`, `workdir`, `timeout`,
  `background`).
- "Search file contents" / "find files by name" → `grep`, `glob`.
- "Fetch a URL" → `webfetch`.
- "Search the web" → `websearch`.

In short, V2 renamed `task` → `subagent` (the agent name moved from
`subagent_type` to `agent`, and continuation happens by re-invoking with
`sessionID`), `apply_patch` → `patch`, and `bash` → `shell`, and it dropped the
todo tool entirely. The available mutation tools depend on the selected model:
`patch` is available for selected GPT model IDs, while other models use `write`
and `edit`.

## Project rules

- All code, code comments, and documentation are written in English.
- The README exists in two languages: `README.md` (English) and `README.it.md`
  (Italian). Any change to one must be reflected in the other in the same
  change, so the two stay aligned.
