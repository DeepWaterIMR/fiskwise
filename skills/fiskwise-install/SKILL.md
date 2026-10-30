---
name: fiskwise-install
description: Install or resume Fiskwise when the user says install https://github.com/DeepWaterIMR/fiskwise, install Fiskwise, or set up the Fiskwise ecosystem. Bootstrap core agent skills before checking R.
---

# Install Fiskwise

The user only needs `install https://github.com/DeepWaterIMR/fiskwise` (case-insensitive).
Run the full workflow below; do not ask for longer prompts or user-run scripts.
Resolve the local Fiskwise repository from `~/.fiskwise/config.json` →
`components.fiskwise.path`, or the checkout you are currently reading. If this is a
first install from GitHub, reuse a valid existing checkout or clone the canonical
repository to a sensible user-owned location (not a drive root). Read its AGENTS.md.
Read `docs/LIFECYCLE.md` and `docs/AGENT-SUPPORT.md` **relative to that repository**;
run helper scripts there by absolute path. A copied skill's directory is not the
repository root. Do not rely on `../../docs` from a registered copy.


For registry, CLI and native-file fallback contracts, use the repository documentation above. First obtain/reuse wise-writing, then register their canonical skills and the Fiskwise skills through filesystem operations. Missing R must never block this stage. Preserve pre-existing settings and registrations with backups; treat unknown resources as adopted. Do not register BAIT's forwarding stubs for `r-package-setup` or `quarto-reporting`.

1. Identify the current coding agent and other installed agents using the discovery profiles. Let the helper detect their configuration directories; if the active host has no configuration yet, include its `--agent` profile along with the detected profiles. The agent chooses these internal flags, not the user. Preview `python3 scripts/fiskwise.py install`, then apply the already-authorized ordinary skill setup with `--apply`; no extra permission round is needed just for clone/registration. Use existing checkouts/config aliases; clone only missing packs. Record versions and Git revisions. If Python is absent, perform the documented equivalent through native file tools. Do not require R for bootstrap.
2. Run the read-only `scripts/check_runtime.py`. Reuse wise-writing's `academic-toolchain-setup` for missing Git, R, Quarto CLI or compiler tools. Ask before system installs/upgrades. Resolve stable versions dynamically, excluding prereleases. Offer an R upgrade if older than the newest two stable x.y series or incompatible with dependencies; honor project pins. Report offline checks as unknown.
3. Ask whether the user permits installation and updates of managed R packages and necessary dependencies. Record explicit permission using `consent allow`; record refusal/revocation with `consent revoke`. Explain how to revoke. Refusal leaves skills installed and runtime incomplete. Do not interpret installation of skills as package consent.
4. Use `scripts/manage_r_packages.R` to check tidyverse and required writing packages plus GitHub ggOceanMaps and ggFishPlots. Apply only with saved permission, explicit apply, an existing writable user library, no active renv/pins and no disabling environment controls. Check Quarto CLI separately from R's `quarto` package. Ask for system-level Quarto upgrades; never install them silently.
5. Use known institutional context or lightweight computer configuration to suggest IMR affiliation. Ask when uncertain; never search email contents. Offer BAIT to IMR users and delegate to `bait-install`. Its privacy and database-download choices remain separate. Record an existing database as adopted. Only use the creation token protocol around a newly authorized BAIT setup; successful BAIT verification is required before marking it created.
6. Offer wise-presentations for presentations; install it when requested. Install index-wise/spict-wise/gadget-wise only when needed, through their install skills and dependency order.

Do not stop after the filesystem helper succeeds: it registers skills/configuration only.
Continue with runtime detection, required consent, R-package checks/setup, and the IMR/BAIT
choice. If the user declines a dependency, keep the skills and clearly report what remains.
Verify the active host can discover all Fiskwise skills and routes the three short
requests to them. Use the host's skill-list/reload facility where available; if it caches
skills until restart, explain the one-time reload instead of claiming it was live-tested.

Report installed pack versions/revisions, runtime checks, consent, skipped or incomplete steps, and the registry location. An interrupted setup can be rerun; never discard settings to force a clean install.
