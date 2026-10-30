---
name: fiskwise-uninstall
description: Preview and, only after explicit confirmation, remove recorded Fiskwise agent registrations. Use when the user asks to uninstall, remove, or detach Fiskwise. Preserve adopted installations and research projects.
---

# Confirmed uninstall

The user only needs `uninstall Fiskwise` (case-insensitive).
Run the full workflow below; do not ask for longer prompts or user-run scripts.
Resolve the local Fiskwise repository from `~/.fiskwise/config.json` →
`components.fiskwise.path`, or the checkout you are currently reading. If neither
exists, report that Fiskwise is not installed and stop; do not clone. Read its AGENTS.md.
Read `docs/LIFECYCLE.md` and `docs/AGENT-SUPPORT.md` **relative to that repository**;
run helper scripts there by absolute path. A copied skill's directory is not the
repository root. Do not rely on `../../docs` from a registered copy.


Use the repository lifecycle documentation above. First run `python3 scripts/fiskwise.py uninstall` and show exact paths to remove and preserve. **Ask for confirmation before any removal.** Use the digest from that approved current preview with `uninstall --apply --confirm DIGEST`. If entries change, show the new preview and obtain fresh approval.

Process all recorded agent profiles, not only the currently active agent.

Default removal covers only Fiskwise-created registered skills and managed instruction blocks with matching ownership fingerprints. Preserve modified/ambiguous entries, unrelated instructions and adopted/pre-existing registrations. Offer adopted detachment separately with a new `--include-adopted` preview; restore backed-up prior registrations. Unlink skills without deleting source repositories. Retain R, Quarto, R packages and research projects.

A database is a separate choice. Offer removal only with verified registry proof of Fiskwise-coordinated creation. Unknown or existing databases, including this machine's prior installation, are adopted and retained. Show `database-preview PATH` including exact path and byte size. Explain the chosen OS Trash/recovery destination and list any associated files individually. Obtain **separate explicit confirmation** and require writers to close. Then use `database-remove PATH --confirm DIGEST`. No WAL or unverified lock state is acceptable. Never stop a writer automatically.

Use OS Trash/Recycle Bin. If unavailable, offer a user-selected same-filesystem quarantine and obtain approval for that destination. Never permanently delete a database or silently fall back to deletion. Associated files are retained by the helper; separately listed files require their own provenance, closure and approved recoverable action.

Report removed/restored/preserved entries, recovery paths and remaining local clones/configuration. Retain the registry audit trail; do not claim adopted resources were created by Fiskwise.
