# Coding-agent discovery and short prompts

The user interface is identical in every host:

```text
install https://github.com/DeepWaterIMR/fiskwise
update Fiskwise
uninstall Fiskwise
```

These are natural-language requests routed to the matching Fiskwise skill, not shell
commands or a special command parser built into every product. First installation reads
this repository's README/AGENTS.md and loads `skills/fiskwise-install/SKILL.md` directly.
After registration, the host discovers SKILL.md metadata and loads the matching workflow.
Where supported, a small managed global instruction block also maps the exact requests
to their full source paths. No long prompt or manual script selection is required.

## Default global locations

The helper detects existing configuration directories and registers canonical skill
sources in the documented locations below. Shared roots are deduplicated. The active
agent can select its own profile internally if it has not created configuration yet.
It must not ask the user to pick directory names or flags.

| Coding agent | Helper profile | Skill directory | Additional routing instructions |
|---|---|---|---|
| Claude Code | `claude` | `~/.claude/skills` | `~/.claude/CLAUDE.md` |
| Codex | `codex` | `~/.agents/skills` | `~/.codex/AGENTS.md` |
| Antigravity app/IDE | `antigravity` | `~/.gemini/config/skills` | `~/.gemini/GEMINI.md` |
| Antigravity CLI | `antigravity-cli` | `~/.gemini/antigravity-cli/skills` | `~/.gemini/GEMINI.md` |
| Mistral Vibe Code | `vibe` (`mistral` alias) | `~/.agents/skills` | Native skill discovery |
| Gemini CLI | `gemini` | `~/.agents/skills` | `~/.gemini/GEMINI.md` |
| Cursor | `cursor` | `~/.agents/skills` | Native skill discovery; preserve User Rules |
| GitHub Copilot CLI | `copilot` | `~/.copilot/skills` | `~/.copilot/copilot-instructions.md` |
| OpenCode | `opencode` | `~/.agents/skills` | `~/.config/opencode/AGENTS.md` |
| Windsurf Cascade | `windsurf` | `~/.codeium/windsurf/skills` | Native skill discovery |
| Devin local CLI/desktop | `devin` | `~/.config/devin/skills` | Native skill discovery |
| Cline | `cline` | `~/.cline/skills` | Native skill discovery |
| Roo Code | `roo` | `~/.agents/skills` | Native skill discovery |
| Other Agent Skills hosts | `portable` | `~/.agents/skills` | Verify this directory is supported first |

Mistral Vibe Code, Gemini CLI, Cursor, Roo Code and OpenCode document the shared directory; adding
another native copy is unnecessary. Antigravity IDE and CLI need their distinct global
locations. Legacy Antigravity IDE `~/.gemini/antigravity/skills` is supported by the host
but is not the target for new installations. Do not manufacture a global AGENTS.md path
for an agent whose documentation does not define one.

The matrix describes default user paths, not every custom configuration. Before
registration, inspect the active host's explicit skill directory/configuration overrides
(e.g. Copilot's `COPILOT_HOME`, OpenCode's XDG configuration, custom Vibe `skill_paths`).
If a supported default is disabled, register via the host's documented mechanism using
native tools, preserve its settings, and record ownership. The deterministic helper
only permits the default allowlisted paths above; do not widen removal permissions to
an arbitrary custom directory. Report a custom-path registration as separately managed
until safe support has been implemented. Check for conflicting same-name skills in
higher-priority project/custom paths; preserve modified or ambiguous entries and report
shadowing rather than claiming the new skill is active.

## Bootstrap and lifecycle contracts

- The short install request authorizes ordinary clone/registration work. Continue through
  the full install skill: core packs, runtime discovery, saved package consent, package
  checks/setup, IMR/BAIT offer and the completion report. Copying files is only stage one.
- Identify the repository through `~/.fiskwise/config.json` → `components.fiskwise.path`.
  Copied skill directories are not repositories; do not resolve repository docs/scripts
  relative to the copy. Internal skill assets stay inside their skill folder.
- Register all four Fiskwise skills and canonical component skills; skip forwarding
  compatibility entries. Back up prior registrations and retain their ownership origin.
- Verify the host's skill list (and origin where shown). Some clients need a skill reload
  or a new session. Do not promise that cached sessions reload automatically.
- Updates refresh recorded copies/links and matching managed instruction blocks across
  registered agents. Modified entries remain untouched. Re-run the filesystem registration
  stage after adding another agent, without repeating runtime setup needlessly.
- Uninstall previews cover every registered agent. Confirmation, ownership checks and
  separate database approval remain mandatory regardless of the short user prompt.
- Link sources where permitted; use the tested directory-copy fallback otherwise. Never
  rewrite product settings, authentication, chats or unrelated user rules.

A local coding agent needs repository access and permission to read/write files and run
commands. Browser-only chat, Mistral Work, locked-down environments and disabled skill
tools do not acquire local installation capability merely by receiving a URL. Hosts with
no verified discovery mechanism can follow AGENTS.md explicitly in a checkout, but the
installer must report that cross-project automatic discovery has not been established.

## Primary documentation

Checked 24 October 2026. The paths are implemented and tested with synthetic homes;
that is not an end-to-end execution test in every proprietary client.

- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)
- [Antigravity skills by surface](https://www.antigravity.google/docs/skills?tab=ide)
- [Antigravity global rules](https://antigravity.google/docs/commands/learn)
- [Mistral Vibe Code skills](https://docs.mistral.ai/vibe/code/cli/skills)
- [Gemini CLI skills and discovery aliases](https://geminicli.com/docs/cli/skills/)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Copilot CLI configuration](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)
- [OpenCode skills](https://docs.opencode.ai/docs/skills/) and [global rules](https://docs.opencode.ai/docs/rules/)

- [Windsurf/Cascade skills](https://docs.windsurf.com/windsurf/cascade/skills) (current documentation redirects to Devin desktop/Cascade)
- [Cline skills](https://docs.cline.bot/customization/skills)
- [Roo Code skills](https://docs.roocode.com/features/skills)
