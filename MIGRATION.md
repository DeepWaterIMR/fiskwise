# Moving to Fiskwise

| Previous repository | Canonical repository |
|---|---|
| academic-writing | [wise-writing](https://github.com/DeepWaterIMR/wise-writing) |
| presentation-template | [wise-presentations](https://github.com/DeepWaterIMR/wise-presentations) |
| index-template | [index-wise](https://github.com/DeepWaterIMR/index-wise) |
| spict-template | [spict-wise](https://github.com/DeepWaterIMR/spict-wise) |
| BAIT | [BAIT](https://github.com/DeepWaterIMR/BAIT) — unchanged |

Repositories were renamed in place. Their history, issues, and releases stay with them.
Update Git remotes to the canonical URL rather than depending on redirects:

```sh
git remote set-url origin https://github.com/DeepWaterIMR/wise-writing.git
```

Rename the clone folder if desired, then update its saved installation path. New installs
use `~/.wise-writing/config.json`, `~/.index-wise/config.json`, and
`~/.spict-wise/config.json`; scaffolds also accept the old config locations. Existing
`academic_writing_path`, `index_template_path`, and `spict_template_path` keys, R function
arguments, environment variables, and skill IDs remain compatible.

## Agent installations

Use `~/.claude/skills` for Claude and `~/.agents/skills` for Codex. Sync only the selected
pack's own skills. Back up customized copies first, and retire duplicate pack-owned copies
from `~/.codex/skills` after verifying the canonical installation. Leave unrelated skills
alone. Refresh the agent session if its skill catalog still shows the previous metadata.

For the full ecosystem on a machine with sibling clones, the reviewed local migration
helper supports a dry run and backs up changed files outside Git:

```sh
python3 fiskwise/scripts/migrate_local.py --workspace /path/to/AI-packages
python3 fiskwise/scripts/migrate_local.py --workspace /path/to/AI-packages --apply
```

It repairs saved clone paths, config aliases, knowledge links, owned skill installations,
and current agent routing. It does not read the Biotic database or modify research projects.

## Existing research projects

Existing generated projects are not rewritten automatically. Keep their pinned methods,
scientific settings, and historical notes. Review a migration in the project's own Git
diff: update its pointers and template-source URLs, check that the installed pack resolves,
and run its existing validation. Rebranding alone is not a reason to refit a model.

The presentation website is now at
[wise-presentations](https://deepwaterimr.github.io/wise-presentations/). GitHub repository
redirects do not guarantee redirects for GitHub Pages sites; update published website links
explicitly. See the migration ledger for the observed old-URL behavior.

## Shared skills and lifecycle (0.1.0)

`r-package-setup` and `quarto-reporting` now belong to wise-writing, preserving their
skill IDs. BAIT's former paths are forwarding pointers; register only the canonical
wise-writing directories. `r-code-style` is shared by all Fiskwise research R work.
Fiskwise coordinates install/update/uninstall; packs retain standalone entry points.
Existing local resources are adopted unless creation provenance was recorded beforehand.

Existing research projects are unchanged. To adopt the new package-loading policy in a
project, review its pins/renv setup first, compare its `R/0_setup.R` with a newly generated
project, copy wise-writing's `project-template/R/package_setup.R` into `R/`, and source it
through the existing project's package declarations. Preserve analysis-specific packages
and settings. Disable unattended installation by default; explicitly authorize missing
packages per run. Do not blindly replace a research project's setup script or outputs.
