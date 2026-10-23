---
name: fiskwise-update
description: Update Fiskwise and its installed knowledge packs and managed R packages when the user says update Fiskwise or update the Fiskwise ecosystem. Keep database refreshes separate.
---

# Update installed Fiskwise software

Read `../../docs/LIFECYCLE.md`. Inspect the registry and show the update plan with `python3 scripts/fiskwise.py update`. Apply with `--apply` when software update is requested. Update installed packs only, once in dependency order, preserving selected branches, version pins, dirty or diverged checkouts. Missing/unavailable repositories must be reported, not replaced silently.

Delegate any specialist post-update setup to the pack's existing update entry point in **managed mode**, avoiding recursive ecosystem updates and repeated prerequisite updates. Refresh canonical agent registrations only when fingerprints still match; preserve user-modified copies. Record version plus Git revision in the report.

Read saved revocable R-package permission before running `scripts/manage_r_packages.R --apply`. Check managed CRAN packages, tidyverse components, required dependencies and installed GitHub revisions. Do not update the entire user library. Honor renv, pins, development refs, and disabling controls such as `R_AW_INSTALL_MISSING=false`. A declined permission or offline service leaves a clearly reported incomplete runtime update. Use `consent revoke` to withdraw permission immediately.

Check R and Quarto CLI through `academic-toolchain-setup`; ask before system changes. Newly generated code defaults to no automatic package installation. Leave existing research projects unchanged. Never refresh the Biotic database as a side effect of software updates; offer BAIT's separate data-refresh workflow only when appropriate.
