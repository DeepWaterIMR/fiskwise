# Fiskwise

For `install https://github.com/DeepWaterIMR/fiskwise`, `update Fiskwise`, or
`uninstall Fiskwise`, read [AGENTS.md](AGENTS.md) and run its matching lifecycle skill.
The short request is sufficient; do not ask for a longer prompt.

Read [AGENTS.md](AGENTS.md) for the shared ecosystem and website-maintenance contract.
Use the existing skill IDs listed there; repository names changed, scientific methods did not.

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
