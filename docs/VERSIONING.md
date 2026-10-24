# Fiskwise version policy

This policy applies to every maintained Fiskwise knowledge pack and R package. Third-party dependencies retain their upstream versions; never modify installed R libraries to apply this policy.

- Every ordinary authored commit increments **patch by exactly 0.0.1** and stamps the
  current update date. For example, `0.2.7` becomes `0.2.8`.
- **Minor (`+0.1`) and major (`+1`) increments happen only when the user explicitly
  requests them.** Agents must never select them autonomously based on change size,
  breaking changes, a release convention, or a planned feature.
- Knowledge packs store `version: x.y.z` and `date: YYYY-MM-DD` in root `VERSION`.
  R packages use root `DESCRIPTION`: `Version: x.y.z` and `Date: YYYY-MM-DD`.
  DESCRIPTION is authoritative if both files exist. Do not add VERSION to an R package.
- Merge/rebase replay retains existing stamps, as agreed in the ecosystem migration;
  it does not increment versions a second time while combining/replaying old work.
- Do not create Git tags, GitHub releases, or CRAN submissions automatically.

## Before a commit

Use the repository's `.githooks/pre-commit`. Fiskwise installation enables the existing
pack hooks when no custom hook configuration would be displaced. Update the shared hook
with the maintainer synchronization tool below; do not create independent implementations.

Stage the intended VERSION/DESCRIPTION changes before committing. The hook refuses to
sweep unstaged metadata into a commit, especially unrelated R package dependencies or
attribution fields. It modifies only the version and date, preserving other DCF fields.
A clean or already-staged README version marker is mirrored; an unstaged README is left
alone. Do not bypass the hook with `--no-verify` to avoid the version policy.

An ordinary commit needs no special flag:

```sh
git commit -m 'Describe the change'
```

**Only after an explicit user request**, the agent sets the scope for that one command:

```sh
FISKWISE_VERSION_BUMP=minor git commit -m 'User-requested minor version'
FISKWISE_VERSION_BUMP=major git commit -m 'User-requested major version'
```

In PowerShell, set `$env:FISKWISE_VERSION_BUMP` for the commit and restore/remove it
immediately afterwards. Do not leave a minor/major scope exported for later commits.
Minor resets patch to zero; major resets minor and patch to zero. The hook accepts a
pre-staged expected version exactly once, rejects an unrequested manual minor/major
change, and is idempotent when retried before the commit succeeds. The environment flag
records the requested scope; it cannot itself determine whether the human requested it.
That judgment remains part of the agent instructions.

The hook needs Git and standard POSIX shell utilities (including those supplied with
Git for Windows), not R or Python. Its date follows the author's local timezone; agents
should use the user's timezone when the execution host differs.

## Shared implementation and local activation

The canonical hook is Fiskwise's `.githooks/pre-commit`. Each repository carries a
self-contained copy and its MIT notice; component licenses remain unchanged. This works
for standalone packs and R checkouts without needing the Fiskwise repository at commit time.

Maintainers can check all available sibling source checkouts, including an optional
R-package checkout directory:

```sh
python3 scripts/sync_versioning.py --enable
# Apply the reviewed synchronization and enable hooks without replacing custom hooks:
python3 scripts/sync_versioning.py --apply --enable
```

The tool skips missing/planned packages and installed R libraries. It does not clone or
initialize a repository. It preserves unknown repository hooks, a custom `core.hooksPath`,
and unrelated default Git hooks, reporting manual integration when necessary. Git hook
activation is local configuration and must be repeated in a new clone. Global agent
instructions therefore also require checking hook activation before committing.

A previously unversioned knowledge pack adopts its already-declared package/site version;
if none exists, initialize at `0.0.1`. The first versioned commit establishes that baseline.
Empty/planned gadget-wise and ggSurveyPlots inherit the policy when development starts;
this policy does not create commits or metadata in their placeholders.

## Validation

Tests use temporary Git repositories, synthetic DESCRIPTION files, and isolated homes.
They cover ordinary, explicitly requested minor/major, first and retried commits; date
stamping; LF/CRLF and other DCF fields; unstaged metadata/README preservation; merge/rebase
replay; and safe synchronization alongside custom hooks. No R package installation,
scientific model run, or real database is required for these checks.
