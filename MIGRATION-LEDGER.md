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
