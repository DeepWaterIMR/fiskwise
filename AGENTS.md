# Fiskwise

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
