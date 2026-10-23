# Fiskwise migration ledger — 23 October 2026

## Repository identity

| Original | Canonical | Original commit |
|---|---|---|
| academic-writing | [wise-writing](https://github.com/DeepWaterIMR/wise-writing) | `3e7e940` |
| presentation-template | [wise-presentations](https://github.com/DeepWaterIMR/wise-presentations) | `fec7621` |
| index-template | [index-wise](https://github.com/DeepWaterIMR/index-wise) | `2e9ecf7` |
| spict-template | [spict-wise](https://github.com/DeepWaterIMR/spict-wise) | `ec7ae69` |
| BAIT | [BAIT](https://github.com/DeepWaterIMR/BAIT) | `e96ae01` |

The four renamed repositories retain their repository IDs and history. `fiskwise` is a new
public hub; `gadget-wise` is a new empty public repository. Existing component licenses
were not changed. New hub code and original brand assets use the MIT license.

## Local migration

Checkouts remain siblings under the existing AI-packages workspace, with folder names
matching the canonical repositories above. Git remotes use the canonical HTTPS URLs.
Private machine paths and backup snapshots are kept outside this public repository.

The local migration preserves legacy config files and compatible keys, adds canonical
config locations, repairs BAIT knowledge links, and installs pack-owned skills as links
into Claude's `~/.claude/skills` and Codex's `~/.agents/skills`. Retired copies and changed
configuration files are backed up. Unrelated skills and historical research projects stay
in place. Current global routing and Codex workspace paths follow the new names.

## Publication and validation

Publication results, release commits, live URL checks, and old Pages URL behavior are
recorded below after deployment. No data analysis, model refit, or database refresh is part
of this migration.

| Component | Rebranding commit |
|---|---|
| BAIT | [110c773](https://github.com/DeepWaterIMR/BAIT/commit/110c773) |
| wise-writing | [7a710f7](https://github.com/DeepWaterIMR/wise-writing/commit/7a710f7) |
| wise-presentations | [7ec1d3d](https://github.com/DeepWaterIMR/wise-presentations/commit/7ec1d3d) |
| index-wise | [d6c63ca](https://github.com/DeepWaterIMR/index-wise/commit/d6c63ca) |
| spict-wise | [fa06bdf](https://github.com/DeepWaterIMR/spict-wise/commit/fa06bdf) |

Passed locally: writing skill validation; index scaffold validation with config precedence
and fallback cases; SPiCT scaffold and isolated migration tests; presentation helper, skill,
and installer tests; presentation lint, Pages build, and four browser tests; BAIT's four-page
documentation render; hub coverage/link/SVG checks, isolated local-migration tests, and six
desktop/mobile/narrow browser tests. The small hub browser suite runs serially to avoid
transient localhost request contention. No checks were bypassed to accept failed assets.

The hub uses HTML/CSS rather than Quarto, following the implementation-stage design choice.
R package documentation sites were linked, not rethemed. Historical notes and generated
research projects were preserved. Current index-pack memory-sync source paths were repaired
without running synchronization or rewriting historical destinations.

## Final component revisions and live checks

| Component | Final migration revision |
|---|---|
| BAIT | [ea6125f](https://github.com/DeepWaterIMR/BAIT/commit/ea6125f) |
| wise-writing | [41977e5](https://github.com/DeepWaterIMR/wise-writing/commit/41977e5) |
| wise-presentations | [3dc5d95](https://github.com/DeepWaterIMR/wise-presentations/commit/3dc5d95) |
| index-wise | [04578ab](https://github.com/DeepWaterIMR/index-wise/commit/04578ab) |
| spict-wise | [b286ec7](https://github.com/DeepWaterIMR/spict-wise/commit/b286ec7) |

Initial hub publication: [c90f84c](https://github.com/DeepWaterIMR/fiskwise/commit/c90f84c).
The final component revisions above include consistent ecosystem routing and safe updates
for global skill links. The four executable Unix sync examples were each tested twice in
isolated homes with conflicting copies, legacy symlinks, and unrelated skills. Windows
examples received static review; Windows execution was not available on this Mac.

All three Pages deployment workflows completed successfully. Live HTTP checks returned
200 for [Fiskwise](https://deepwaterimr.github.io/fiskwise/), its shared membership badge,
[BAIT](https://deepwaterimr.github.io/BAIT/), and
[wise-presentations](https://deepwaterimr.github.io/wise-presentations/). Both linked R
package documentation sites also returned 200. The old
`https://deepwaterimr.github.io/presentation-template/` URL returned **404**, so external
links to that website must be updated explicitly; no old-name repository was recreated.

`gadget-wise` is public, reports size zero, and its commits API returns HTTP 409 for an empty
repository. It has no README, commits, or workflows. A repeat local migration dry run reports
no changes. Initial and final repository IDs match, and all six working checkouts are clean
after publication. Existing licenses and scientific APIs were preserved.

## Lifecycle standardization — 23 October 2026

This release adds Fiskwise **0.1.0**, its four coordinator skills, an ownership registry,
revocable managed-package permission, recoverable removal, automatic version stamping,
and the dedicated HTML/CSS getting-started guide. No release tags are created.

| Component | Standardization revision | Version |
|---|---|---|
| wise-writing | [39ab957](https://github.com/DeepWaterIMR/wise-writing/commit/39ab957) | 0.1.20 |
| BAIT shared ownership | [5e4fdb4](https://github.com/DeepWaterIMR/BAIT/commit/5e4fdb4) | 0.2.15 |
| BAIT documentation | [e4bb57c](https://github.com/DeepWaterIMR/BAIT/commit/e4bb57c) | 0.2.16 |
| index-wise | [90edf09](https://github.com/DeepWaterIMR/index-wise/commit/90edf09) | existing 0.2.0 |
| spict-wise | [ebf660b](https://github.com/DeepWaterIMR/spict-wise/commit/ebf660b) | existing 0.2.0 |
| wise-presentations shared loader | [3750511](https://github.com/DeepWaterIMR/wise-presentations/commit/3750511) | revision-based pack |
| wise-presentations documentation | [4785388](https://github.com/DeepWaterIMR/wise-presentations/commit/4785388) | website package 0.1.0 |
| Fiskwise | commit containing this ledger section | 0.1.0 |

Checkouts retain their canonical sibling paths in the AI-packages workspace. Home-only
records contain exact paths, backups and revisions. Claude/Codex canonical registrations
now point shared reporting/package skills to wise-writing, with BAIT forwarding pointers
excluded. Existing components and database are adopted; R-package permission remains
unset. No R/system packages were installed, no real Biotic data was read, and no historical
research projects or memory histories were changed.

Validation: 32 isolated Python tests (including R fixture tests when R/jsonlite are
available); writing's 15-skill validator and package-policy/scaffold tests; index and
SPiCT scaffold checks; presentation skill/helper/installer checks, lint, Pages build and
4 browser tests; BAIT's four-page Quarto render; hub build/link/asset/version checks and
9 desktop/mobile/narrow browser tests. Runtime services are mocked in tests. Version tests
cover ordinary/manual bumps, merge/rebase skips and unstaged README preservation; site
tests confirm builds leave VERSION and page sources unchanged.

Publication targets: [Fiskwise](https://deepwaterimr.github.io/fiskwise/),
[getting started](https://deepwaterimr.github.io/fiskwise/getting-started.html),
[BAIT](https://deepwaterimr.github.io/BAIT/getting-started.html), and
[wise-presentations](https://deepwaterimr.github.io/wise-presentations/). Dependency
commits publish first, then Fiskwise, then the two pack documentation updates.

Platform limits: Windows link-copy fallback and refusal paths are tested synthetically
on macOS; native Windows Recycle Bin and compiler detection need a Windows runner. Database
recovery tests use synthetic files and explicit same-filesystem quarantine, never a real
Biotic database. macOS Trash removal is not exercised against user data. Explicit R pins
stop automatic package apply for manual dependency review; missing/offline metadata is
reported as unknown. System tool installation remains an agent-guided, separately approved
operation. See [lifecycle contracts](docs/LIFECYCLE.md) and [project migration](MIGRATION.md).
