---
name: fiskwise-check
description: Check Fiskwise readiness, diagnose missing skills or tools, or plan a repair when the user says check Fiskwise or repair Fiskwise. Inspect before changing anything.
---

# Check Fiskwise

Resolve the repository from `~/.fiskwise/config.json` → `components.fiskwise.path`,
or the checkout containing this skill. Run its scripts by resolved absolute paths.

1. Run `python3 scripts/fiskwise.py status` and `python3 scripts/check_runtime.py`.
   Inspect registered skills and their resources; missing R does not invalidate the skills.
2. Compare installed registrations with the source skill inventory. Verify copied skills
   resolve external resources through their pack configuration. Use the host's discovery
   facility when available; distinguish file checks from an actual host discovery test.
3. Report ready, missing, modified, retired or unknown items and the next useful action.
   Do not print private configuration values or database records into the report.
4. A check is read-only. For an explicit repair request, follow `fiskwise-install` to resume
   ordinary setup without replacing user modifications. Package/system/database consent
   rules still apply. For updates, follow `fiskwise-update`; never erase the registry to
   resolve a mismatch.
