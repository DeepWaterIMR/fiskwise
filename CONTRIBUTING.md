# Contributing to Fiskwise

Use this repository for ecosystem navigation, shared branding, and migration documentation.
Propose scientific methods, templates, and skill improvements in the component that owns
them. `packages.json` records canonical names, repository owners, status, and destinations.

Before a website change, build and run the checks in the README, then inspect desktop and
mobile layouts. Test keyboard navigation and links. Keep planned items visibly marked.

Before a theme change, run the brand synchronization helper and validate the affected
documentation stacks. Preserve component-specific functionality and scientific templates.

Never commit raw confidential data, exact station positions, private paths, or credentials.
Scientific claims need primary evidence; do not invent validation, release status, or
endorsements. Respect each component's own license and contribution instructions.

Report broken ecosystem links here; report scientific or implementation issues in the
relevant pack. Human maintainers review changes and remain responsible for their release.

Lifecycle changes need isolated-home ownership/consent tests. Use synthetic databases,
local Git remotes and mocked release/package services; never real Biotic data or system
installs in tests. Run the Python suite, wise-writing package-policy checks and affected
scaffold/installer checks. Keep shared package-loading code in wise-writing and copy it
into generated projects so they stay self-contained. Update CHANGELOG.md for user-visible
changes. The installed pre-commit hook stamps VERSION/README; website builds only read it.

## Ecosystem commit versions

For every ordinary commit in a maintained Fiskwise repository, use the shared version
hook to increment patch by **0.0.1** and stamp the update date. Knowledge packs use
`VERSION`; R packages use DESCRIPTION `Version` and `Date`. Minor (`+0.1`) and major
(`+1`) increments require an **explicit user request**; never choose them autonomously.
Only then set `FISKWISE_VERSION_BUMP=minor|major` for that commit. Preserve custom hooks
and staged-file boundaries. Merge/rebase replay retains existing stamps; no automatic
tags/releases. See [the shared policy](https://github.com/DeepWaterIMR/fiskwise/blob/main/docs/VERSIONING.md).
