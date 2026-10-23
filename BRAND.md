# Fiskwise visual identity

Use **Fiskwise** in prose and `fiskwise` in repository names and URLs. BAIT keeps its name.
The FISK expansion is **Fisheries Intelligence Skill Kit**. Describe the tools as
researcher-led knowledge packs, not trained models or autonomous scientific authorities.

## Shared assets

- Navy `#123047`: primary ink, identity, dark panels.
- Teal `#087F8C`: links and actions; white text on teal passes WCAG AA for normal text.
- Off-white `#F7FAFC`: page background; white cards with restrained borders.
- Typography: the local Aptos / Segoe UI / Helvetica Neue / Arial system stack.
- `assets/wordmark.svg`, `mark.svg`, `mark-light.svg`, `favicon.svg`: primary marks.
- `assets/icons/`: nine component icons; accent colors distinguish knowledge packs.
- `assets/part-of-fiskwise.svg`: ecosystem membership, not certification or endorsement.

Use the SVG wordmark on light surfaces and the light mark on navy. Preserve proportions,
keep nearby space clear, and provide accessible text for linked marks. A logo does not
authorize use of the institute's separate identity or imply institutional endorsement.

```md
[![Part of Fiskwise](https://deepwaterimr.github.io/fiskwise/assets/part-of-fiskwise.svg)](https://deepwaterimr.github.io/fiskwise/)
```

Use build, license, or release badges only if they link to the real workflow, license, or
release for that component. A planned pack must never look installable or released.

## Synchronizing existing sites

Place the repositories side by side, then run:

```sh
python3 fiskwise/scripts/sync_brand.py
```

The script copies canonical tokens and SVGs to BAIT's Quarto documentation assets and
wise-presentations' public brand directory. Stack-specific layout rules stay in those
sites. Review and commit the resulting changes in each repository. Copies are versioned,
so a hub deployment never silently changes another published site's theme.

Do not apply website styles to scientific figures, Word templates, or presentation slides.
Retain their scientific layout and accessibility contracts.
