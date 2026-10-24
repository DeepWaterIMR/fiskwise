# Fiskwise

## Short lifecycle requests — start here

The complete user interface is (case-insensitive):

| User request | Read and execute |
|---|---|
| `install https://github.com/DeepWaterIMR/fiskwise` or `install Fiskwise` | [fiskwise-install](skills/fiskwise-install/SKILL.md) |
| `update Fiskwise` | [fiskwise-update](skills/fiskwise-update/SKILL.md) |
| `uninstall Fiskwise` | [fiskwise-uninstall](skills/fiskwise-uninstall/SKILL.md) |

The short request is sufficient. Do not ask the user to paste a longer prompt,
choose scripts, or register skills manually. On first install, read the install
skill from this repository even though it is not registered yet. Obtain a local
checkout if only the GitHub page is available, then follow that same skill.
Continue through the entire onboarding workflow; registering skill files alone
is not a completed installation. The install request authorizes ordinary clone and
registration steps. Ask only for required package/system/database permission or
missing information. Uninstall always needs the user's approved removal preview.

Use [agent support](docs/AGENT-SUPPORT.md) for the active host's discovery profile.
Register the installed coding agents without assuming every host reads CLAUDE.md.
Preserve canonical Fiskwise spelling, unrelated instructions, and the consent ledger.

Fiskwise is the umbrella for the DeepWaterIMR fisheries-science knowledge packs.
Read `packages.json` for canonical component names, destinations, and status.

- The public hub is hand-authored HTML/CSS in `site/`, built by `python3 scripts/build_site.py`.
- Run `python3 scripts/check_site.py` after building. Never edit `dist/` directly.
- Canonical shared brand assets live in `assets/`; run `python3 scripts/sync_brand.py`
  to copy them to the sibling BAIT and wise-presentations sites.
- BAIT retains its name and `biotic-*` skills. Existing `academic-*`, `index-*`,
  `spict-*`, and presentation skill IDs remain stable despite repository renames.
- Keep research data, personal paths, local migration backups, and credentials out of Git.
- Distinguish available components from planned ones. Do not invent readiness, validation,
  institutional endorsement, release badges, or scientific claims.
- GitHub Pages is the host. Do not register or publish a separate Sites-hosted project.

Source changes may be delegated by component; the lead handles integration and publication.

## Lifecycle ownership

Read `skills/fiskwise-workflow/SKILL.md` for Fiskwise research routing and shared
standards; always load wise-writing's `r-code-style` before editing R. Read the
matching fiskwise-install/update/uninstall skill for lifecycle work and
`docs/LIFECYCLE.md` for registry contracts. Skills bootstrap before R. Saved
revocable consent is required for managed R packages; system software and BAIT
data setup have separate choices. Preserve adopted resources and customizations.
Do not duplicate wise-writing reporting/package-loading implementations in packs.
Delegate only when expected total cost (including context and review) is lower.
Generic knowledge skills and template-free modes remain deferred.

## Ecosystem commit versions

For every ordinary commit in a maintained Fiskwise repository, use the shared version
hook to increment patch by **0.0.1** and stamp the update date. Knowledge packs use
`VERSION`; R packages use DESCRIPTION `Version` and `Date`. Minor (`+0.1`) and major
(`+1`) increments require an **explicit user request**; never choose them autonomously.
Only then set `FISKWISE_VERSION_BUMP=minor|major` for that commit. Preserve custom hooks
and staged-file boundaries. Merge/rebase replay retains existing stamps; no automatic
tags/releases. See [the shared policy](https://github.com/DeepWaterIMR/fiskwise/blob/main/docs/VERSIONING.md).
