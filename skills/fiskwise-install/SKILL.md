---
name: fiskwise-install
description: Install or resume Fiskwise when the user says install https://github.com/DeepWaterIMR/fiskwise, install Fiskwise, or set up the Fiskwise ecosystem. Bootstrap core agent skills before checking R.
---

# Install Fiskwise

Read `../../docs/LIFECYCLE.md` for registry, CLI and native-file fallback contracts. First obtain/reuse wise-writing and wise-presentations, then register their canonical skills and the four Fiskwise skills through filesystem operations. Missing R must never block this stage. Preserve pre-existing settings and registrations with backups; treat unknown resources as adopted. Do not register BAIT's forwarding stubs for `r-package-setup` or `quarto-reporting`.

1. Preview `python3 scripts/fiskwise.py install`, then apply the authorized skill setup with `--apply`. Use existing checkouts/config aliases; clone only missing packs. Record versions and Git revisions. If Python is absent, perform the documented equivalent through native file tools. Do not require R for bootstrap.
2. Run the read-only `scripts/check_runtime.py`. Reuse wise-writing's `academic-toolchain-setup` for missing Git, R, Quarto CLI or compiler tools. Ask before system installs/upgrades. Resolve stable versions dynamically, excluding prereleases. Offer an R upgrade if older than the newest two stable x.y series or incompatible with dependencies; honor project pins. Report offline checks as unknown.
3. Ask whether the user permits installation and updates of managed R packages and necessary dependencies. Record explicit permission using `consent allow`; record refusal/revocation with `consent revoke`. Explain how to revoke. Refusal leaves skills installed and runtime incomplete. Do not interpret installation of skills as package consent.
4. Use `scripts/manage_r_packages.R` to check tidyverse and required writing/presentation packages plus GitHub ggOceanMaps and ggFishPlots. Apply only with saved permission, explicit apply, an existing writable user library, no active renv/pins and no disabling environment controls. Check Quarto CLI separately from R's `quarto` package. Ask for system-level Quarto upgrades; never install them silently.
5. Use known institutional context or lightweight computer configuration to suggest IMR affiliation. Ask when uncertain; never search email contents. Offer BAIT to IMR users and delegate to `bait-install`. Its privacy and database-download choices remain separate. Record an existing database as adopted. Only use the creation token protocol around a newly authorized BAIT setup; successful BAIT verification is required before marking it created.
6. Install index-wise/spict-wise only when needed, through their install skills and dependency order. Do not install gadget-wise while empty.

Report installed pack versions/revisions, runtime checks, consent, skipped or incomplete steps, and the registry location. An interrupted setup can be rerun; never discard settings to force a clean install.
