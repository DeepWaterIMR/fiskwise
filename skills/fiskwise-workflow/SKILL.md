---
name: fiskwise-workflow
description: Coordinate Fiskwise fisheries research and route work to the specialist knowledge packs. Use when the user asks to use Fiskwise, combine its packs, or conduct Fiskwise research.
---

# Fiskwise research workflow

Resolve the Fiskwise repository through `~/.fiskwise/config.json` → `components.fiskwise.path` when this skill is registered as a copy. Read that root’s `packages.json` inventory and relevant pack's AGENTS.md. Follow the user's scientific question and project requirements. For Fiskwise research, use R and tidyverse for analysis, Quarto for executable reports, ggOceanMaps for ocean mapping, and ggFishPlots for supported life-history figures. Reuse relevant ecosystem packages rather than inventing parallel implementations. Preserve project version pins and confidentiality.

Always read wise-writing's `r-code-style` before creating or editing R code. Use its `r-package-setup` for package declarations and its `quarto-reporting` and `academic-conventions` for reproducible reports. Apply guidance to edited code; do not reformat whole repositories. Website and maintenance work use appropriate existing tools.

## Ownership

- wise-writing owns writing, document conventions, code quality, package loading, reporting, and toolchain assistance.
- wise-presentations owns slide planning, layouts, rendering, and review.
- BAIT owns Biotic privacy, database setup/refresh, access and domain methods. Read its AGENTS.md and relevant skills; keep raw data local.
- index-wise owns sdmTMB indices; spict-wise owns SPiCT assessments; gadget-wise owns gadget3 models (structure, data-loops, fitting, diagnostics, projections, model reports). Install them on demand through their existing install skills. ggSurveyPlots remains planned.
- Fiskwise owns routing, software lifecycle, consent and installation records. Do not duplicate specialist procedures here. All packs remain usable independently; existing skill IDs remain stable.

## Typical chains

| Goal | Packs, in order |
|---|---|
| Survey index for an assessment | BAIT (or own data) → index-wise → assessment-index hand-off → spict-wise or gadget-wise |
| Assessment chapter and advice | spict-wise or gadget-wise → wise-writing (`academic-assessment-report`, `academic-advice-sheet`) → wise-presentations |
| Biotic analysis report | BAIT → wise-writing (`academic-data-report`) → wise-presentations |

Settle each hand-off (files, units, provenance) before starting the next pack.

Delegate substantial bounded tasks to cheaper available models only when the expected **total** cost is lower, including context transfer, coordination, repeated work and review. Keep small or context-heavy tasks with the lead. Do not delegate merely to demonstrate delegation.

Missing components go through `fiskwise-install`; software changes through `fiskwise-update`. Do not install packages without saved permission. Database refreshes are separate. For questions about an existing model or index outside a scaffolded project, use `gadget-model`, `index-sdmtmb` or `spict-model`.

## Commits to Fiskwise repositories

Only when committing to a maintained Fiskwise repository, follow the [version policy](https://github.com/DeepWaterIMR/fiskwise/blob/main/docs/VERSIONING.md).
