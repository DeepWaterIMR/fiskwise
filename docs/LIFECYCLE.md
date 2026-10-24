# Lifecycle implementation

The three short user requests in README/AGENTS.md select the four `skills/fiskwise-*/SKILL.md` agent instructions; `fiskwise-workflow` handles research routing. The user never needs the technical commands below. Python's standard-library helper performs **only** repository/agent/config operations. It never installs R packages, system software or databases. An agent coordinates the separate runtime checks and specialist entry points; a successful helper command alone does not mean runtime setup is complete.

## Bootstrap and use

Read the repository and preview before applying. With an existing clone:

```sh
python3 scripts/fiskwise.py install
python3 scripts/fiskwise.py install --apply
python3 scripts/check_runtime.py
Rscript scripts/manage_r_packages.R
```

Install reuses canonical/legacy pack configs and sibling checkouts or clones missing core packs. It registers wise-writing then wise-presentations and Fiskwise, using links with a copy fallback. `--agent` selects a documented [agent discovery profile](AGENT-SUPPORT.md); without it the helper detects configured coding agents. Shared targets are registered once; BAIT knowledge aliases remain compatible across all three historical roots. `--include BAIT`, `--include index-wise`, or `--include spict-wise` registers optional packs with their dependencies. `--adopt-existing` explicitly brings all available local packs under coordination. `--no-clone` is useful offline. Never use it to claim an existing database was created by Fiskwise.

On systems without Python, an agent can use native filesystem tools: clone/reuse the core repositories; enumerate their inventory `skill_roots`; skip forwarding metadata; back up an existing exact skill registration; link/copy only canonical directories to the active host’s documented discovery directory in [AGENT-SUPPORT.md](AGENT-SUPPORT.md). Preserve unrelated files. Record the same schema below with fingerprints and backups before registering; append only the managed marker block, preserving other instructions. If the agent cannot implement fingerprints/atomic registry writes reliably, install core skill files with explicit adoption and defer lifecycle automation until Python is available. Missing R never prevents skill bootstrap. Windows uses directory copies when symlinks are unavailable.

## Registry and consent

`~/.fiskwise/config.json` schema version 1 stores:

- `components`: path, created/adopted origin, version/date/revision, optional `pinned` flag.
- `registrations`: exact path, owner, kind, created/adopted origin, prior fingerprint and backup, source, installed fingerprint. Links are fingerprinted by their target; copies by file contents.
- `consent.r_packages`: null/false/true, with time recorded. `consent allow` requires explicit user permission; `consent revoke` withdraws it.
- `config_resources` and `hook_config`: component configuration backups/previous state. These are retained on uninstall so standalone packs remain usable.
- `databases`: existing/adopted or token-based newly created provenance. Unknown provenance is never removal permission.
- `history`: installation/update/removal audit trail. No raw research data or credentials.

All CLI previews are read-only. Package checks are read-only by default. System tools always require their own approval. R installs/updates require saved consent plus an explicit apply, honor disabling controls and project libraries/pins, and use only a writable existing user library. Quarto CLI is distinct from the R package `quarto`.

## Updates

```sh
python3 scripts/fiskwise.py update
python3 scripts/fiskwise.py update --apply
```

Only registered installed components are updated in dependency order. Local modifications, detached/pinned states, ahead/divergent branches and unavailable remotes are preserved/reported. The current upstream and branch remain selected. Pack-specific post-install/setup is performed through its update skill in managed mode. Check shared runtime dependencies once. Database refresh is never part of software update.

## Reversible uninstall

```sh
python3 scripts/fiskwise.py uninstall
# After the user approves this exact preview:
python3 scripts/fiskwise.py uninstall --apply --confirm PREVIEW_DIGEST
```

Adopted entries are retained by default; separately preview `--include-adopted` to detach them and restore previous registrations. Changed entries or missing/modified backups are retained. Managed instruction blocks are restored independently of surrounding text. The audit registry, component config files/backups, clones, version hooks, R packages and research projects remain. Source skill directories are never deleted.

For an explicitly authorized new BAIT database, call `database-begin /absolute/new.duckdb` **before** BAIT creates it; call `database-complete TOKEN --bait-verified` only after BAIT verifies its connection. A pending token alone proves nothing. Record existing databases as adopted; never manufacture a token retrospectively.

Database removal needs a separate `database-preview PATH`, user approval of exact path, size and recovery destination, then `database-remove PATH --confirm DIGEST`. The helper fails closed on unknown provenance, symlinks, WALs, open writers or unprovable closure. It uses macOS Trash or Windows Recycle Bin. Else obtain explicit approval for `--quarantine /same/filesystem/directory`. Associated files are retained, not implicitly removed. No tests use real Biotic data.

## Versioning

Follow [VERSIONING.md](VERSIONING.md) for all ecosystem commits, including R packages.
Knowledge packs use VERSION; R packages use DESCRIPTION Version/Date. Every ordinary
commit increments patch and date; minor/major changes require an explicit user request
and a one-command `FISKWISE_VERSION_BUMP=minor|major`. Installation/update enables the
repository hooks while preserving unrelated custom configuration. Website builds read
VERSION and never modify it; no automatic tags/releases are created.

The R helper needs `jsonlite` to read the registry. If absent, the agent must first
verify saved consent through native JSON/file tools and bootstrap that one dependency
into the chosen existing user library; otherwise report the package check incomplete.
Successful applied checks record installed R versions and GitHub SHAs in `r_packages`.
Explicit per-package pins can be recorded in the registry's `r_package_pins` map
(package name to pin/reason); the helper excludes them, including dependency updates.
Do not run concurrent registry writers. Re-run checks after any interrupted package job.

Maintain the standalone presentation helper with `python3 scripts/sync_package_helper.py`
(check-only) or its reviewed `--apply` mode. Index/SPiCT scaffolds copy the canonical
helper at generation time. Explicit package pins currently stop the automatic R apply
job for manual dependency review; check-only mode still reports unpinned packages.
