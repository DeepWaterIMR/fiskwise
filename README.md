# Fiskwise — Agentic AI tools for fisheries science

<!-- version -->
**Version 0.1.11** (2026-10-30)
<!-- /version -->

[![Publish Fiskwise](https://github.com/DeepWaterIMR/fiskwise/actions/workflows/pages.yml/badge.svg)](https://github.com/DeepWaterIMR/fiskwise/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-087F8C.svg)](LICENSE)

**[Explore the Fiskwise website](https://deepwaterimr.github.io/fiskwise/)**

**For coding agents receiving an install/update/uninstall request:** read
[AGENTS.md](AGENTS.md), then execute its matching full lifecycle skill. A first-time
`install https://github.com/DeepWaterIMR/fiskwise` bootstraps the install skill directly
from this repository. The user does not need any additional prompt text.

Fiskwise brings together AI skills, scientific knowledge, and R tools to help researchers
conduct fisheries science with agents such as Claude Code and Codex. Its knowledge packs
guide data preparation, analysis, modelling, scientific writing, and presentation, with
researchers directing the work and evaluating the results.

The ecosystem builds on **R**, **tidyverse**, and **Quarto**. The name combines **FISK —
Fisheries Intelligence Skill Kit** with *wise*, and draws on the Scandinavian word *fisk*.
Developed at the Institute of Marine Research, Norway, its components can be used
independently or together. Raw confidential data must remain local.

## AI knowledge packs

| Pack | Purpose | Documentation |
|---|---|---|
| [wise-writing](https://github.com/DeepWaterIMR/wise-writing) | Scientific writing, reproducible documents, and review | Repository |
| [wise-presentations](https://github.com/DeepWaterIMR/wise-presentations) | Scientific presentation planning, creation, and visual review | [Learning hub](https://deepwaterimr.github.io/wise-presentations/) |
| [BAIT](https://github.com/DeepWaterIMR/BAIT) | Access, preparation, analysis, and visualization of IMR Biotic data | [Documentation](https://deepwaterimr.github.io/BAIT/) |
| [index-wise](https://github.com/DeepWaterIMR/index-wise) | Development, validation, and reporting of survey indices using sdmTMB | Repository |
| [spict-wise](https://github.com/DeepWaterIMR/spict-wise) | SPiCT stock assessments, diagnostics, sensitivity analyses, and advice | Repository |
| [gadget-wise](https://github.com/DeepWaterIMR/gadget-wise) | gadget3 fisheries and ecosystem models: structure, data, fitting, diagnostics, projections, and reports | Repository |

## R packages

| Package | Purpose |
|---|---|
| [ggOceanMaps](https://mikkovihtakari.github.io/ggOceanMaps/) | Ocean maps with bathymetry |
| [ggFishPlots](https://deepwaterimr.github.io/ggFishPlots/) | Fish life-history relationships |
| ggSurveyPlots — **planned** | Fisheries survey visualization |

## Start with your agent

```text
install https://github.com/DeepWaterIMR/fiskwise
```

Later, simply say `update Fiskwise` or `uninstall Fiskwise`. The agent loads the
matching workflow; no scripts or extra instructions are needed from you.

Use a local coding agent with repository and file/shell access: Claude Code, Codex,
Antigravity, Mistral Vibe Code, Gemini CLI, Cursor, Copilot CLI, or OpenCode.
The installer handles their [documented skill-discovery locations](docs/AGENT-SUPPORT.md).
Browser-only chat and hosts that cannot read/write local files cannot install local skills.

Core installation registers **wise-writing first**, even when
R is missing. Fiskwise then guides toolchain checks and asks for revocable permission
before installing/updating managed R packages (including ggOceanMaps and ggFishPlots).
R, Quarto CLI and system tools require separate approval. Declining package permission
keeps the skills usable and reports incomplete runtime setup. Presentations and method packs are installed
on demand; BAIT is offered to IMR users with its own privacy/database choices.

Use `Update Fiskwise` for installed software, or `Uninstall Fiskwise` for an
ownership-aware removal preview. Removal always requires confirmation; existing/adopted
installations and databases are preserved by default. Database refresh and removal
are separate choices. See [Getting started](https://deepwaterimr.github.io/fiskwise/getting-started.html)
and the [lifecycle implementation](docs/LIFECYCLE.md).

Fiskwise owns `fiskwise-workflow`, `fiskwise-install`, `fiskwise-update` and
`fiskwise-uninstall`, plus `fiskwise-check` for readiness and repair. wise-writing owns shared `r-code-style`, `r-package-setup` and
`quarto-reporting`; specialist methods stay in their packs. Fiskwise research uses R,
tidyverse and Quarto, with `r-code-style` for new/edited R code. Website/maintenance
work retains suitable tooling. Delegate only when total expected cost is lower,
including coordination and review. Packs remain independently usable.

Existing skill IDs
remain stable; see the [migration guide](MIGRATION.md). Cite the underlying methods and
software using each component's own citation instructions. This hub has no scholarly DOI.

## Website and shared theme

The hub uses hand-authored HTML/CSS, with no JavaScript framework or Quarto dependency.
The build uses only Python's standard library:

```sh
python3 scripts/build_site.py
python3 scripts/check_site.py
python3 -m unittest discover -s tests
python3 -m http.server 8080 --directory dist
```

GitHub Actions builds and publishes `dist/` to GitHub Pages. `packages.json` is the
component inventory. [BRAND.md](BRAND.md) documents the shared SVG assets, design tokens,
and synchronization with existing pack websites. Scientific document and slide themes
are maintained independently.

Optional responsive and keyboard browser checks use Playwright: run `npm ci`,
`npx playwright install chromium`, then `npm run test:browser` with the preview server
running. The site build and deployment do not require Node.js or Playwright.

[Contributing](CONTRIBUTING.md) · [Migration](MIGRATION.md) · [Brand assets](BRAND.md) ·
[Migration ledger](MIGRATION-LEDGER.md) · [Hub license](LICENSE)


## Ecosystem versioning

Every ordinary commit increments patch by **0.0.1** and records the update date.
Minor (`+0.1`) and major (`+1`) versions change only at the user's explicit request.
Knowledge packs use `VERSION`; R packages use DESCRIPTION `Version`/`Date`.
See the [shared version policy](docs/VERSIONING.md).
