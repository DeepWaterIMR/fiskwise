---
name: fiskwise-workflow
description: Coordinate Fiskwise fisheries research and route work to the specialist knowledge packs. Use when the user asks to use Fiskwise, combine its packs, or conduct Fiskwise research.
---

# Fiskwise research workflow

Read the root `packages.json` inventory and relevant pack's AGENTS.md. Follow the user's scientific question and project requirements. For Fiskwise research, use R and tidyverse for analysis, Quarto for executable reports, ggOceanMaps for ocean mapping, and ggFishPlots for supported life-history figures. Reuse relevant ecosystem packages rather than inventing parallel implementations. Preserve project version pins and confidentiality.

Always read wise-writing's `r-code-style` before creating or editing R code. Use its `r-package-setup` for package declarations and its `quarto-reporting` and `academic-conventions` for reproducible reports. Apply guidance to edited code; do not reformat whole repositories. Website and maintenance work use appropriate existing tools.

## Ownership

- wise-writing owns writing, document conventions, code quality, package loading, reporting, and toolchain assistance.
- wise-presentations owns slide planning, layouts, rendering, and review.
- BAIT owns Biotic privacy, database setup/refresh, access and domain methods. Read its AGENTS.md and relevant skills; keep raw data local.
- index-wise owns sdmTMB indices; spict-wise owns SPiCT assessments. Install them on demand through their existing install skills. gadget-wise and ggSurveyPlots remain planned.
- Fiskwise owns routing, software lifecycle, consent and installation records. Do not duplicate specialist procedures here. All packs remain usable independently; existing skill IDs remain stable.

Delegate substantial bounded tasks to cheaper available models only when the expected **total** cost is lower, including context transfer, coordination, repeated work and review. Keep small or context-heavy tasks with the lead. Do not delegate merely to demonstrate delegation.

Missing components go through `fiskwise-install`; software changes through `fiskwise-update`. Do not install packages without saved permission. Database refreshes are separate. Generic knowledge/template-free modes are deferred.
