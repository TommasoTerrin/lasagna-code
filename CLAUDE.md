@AGENTS.md

# Claude Code specifics

The rules above live in `AGENTS.md`. The notes below apply to Claude Code only
and override the OpenCode-specific parts of `AGENTS.md`.

- At the start of every conversation, load the `using-superpowers` skill with
  the `Skill` tool before any other response or action, and follow it.
- `superpowers:<name>` means the skill `<name>` in `.claude/skills/`.
- Ignore the "Tool mapping (OpenCode V2)" section of `AGENTS.md`. For
  subagents and todos, use Claude Code's native tools (the `Agent` tool and
  the built-in todo list).
