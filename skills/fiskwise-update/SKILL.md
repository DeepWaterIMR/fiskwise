---
name: fiskwise-update
description: Update Fiskwise and its installed knowledge packs and managed R packages when the user says update Fiskwise or update the Fiskwise ecosystem. Keep database refreshes separate.
---

# Update installed Fiskwise software

The user only needs `update Fiskwise` (case-insensitive).
Run the full workflow below; do not ask for longer prompts or user-run scripts.
Resolve the local Fiskwise repository from `~/.fiskwise/config.json` →
`components.fiskwise.path`, or the checkout you are currently reading. If this is a
first install from GitHub, reuse a valid existing checkout or clone the canonical
repository to a sensible user-owned location (not a drive root). Read its AGENTS.md.
Read `docs/LIFECYCLE.md` and `docs/AGENT-SUPPORT.md` **relative to that repository**;
run helper scripts there by absolute path. A copied skill's directory is not the
repository root. Do not rely on `../../docs` from a registered copy.


Use the repository lifecycle documentation above. Inspect the registry and show the update plan with `python3 scripts/fiskwise.py update`. Apply with `--apply` when software update is requested. Update installed packs only, once in dependency order, preserving selected branches, version pins, dirty or diverged checkouts. Missing/unavailable repositories must be reported, not replaced silently.

Delegate any specialist post-update setup to the pack's existing update entry point in **managed mode**, avoiding recursive ecosystem updates and repeated prerequisite updates. Refresh canonical agent registrations only when fingerprints still match; preserve user-modified copies. Record version plus Git revision in the report.

Read saved revocable R-package permission before running `scripts/manage_r_packages.R --apply`. Check managed CRAN packages, tidyverse components, required dependencies and installed GitHub revisions. Do not update the entire user library. Honor renv, pins, development refs, and disabling controls such as `R_AW_INSTALL_MISSING=false`. A declined permission or offline service leaves a clearly reported incomplete runtime update. Use `consent revoke` to withdraw permission immediately.

Refresh registrations across all recorded agent profiles, including native Antigravity
and Copilot paths and copy-only installations. Keep the managed short-command routing
blocks current when their fingerprints match. If the lifecycle helper itself was updated,
reload its entry point in a fresh process before subsequent setup. If the user has added
another coding agent since setup, register that host through the install skill's filesystem
stage without repeating package/runtime work unnecessarily.

Check R and Quarto CLI through `academic-toolchain-setup`; ask before system changes. Newly generated code defaults to no automatic package installation. Leave existing research projects unchanged. Never refresh the Biotic database as a side effect of software updates; offer BAIT's separate data-refresh workflow only when appropriate.


When maintaining source repositories, follow `docs/VERSIONING.md`: every ordinary
commit increments patch by 0.0.1 and the update date. R packages use DESCRIPTION;
knowledge packs use VERSION. Minor/major changes require the user's explicit request.
A software update does not authorize a minor/major version decision or a release.
