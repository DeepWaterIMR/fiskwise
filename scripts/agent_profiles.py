"""Documented default discovery locations. See docs/AGENT-SUPPORT.md for sources and scope.

Shared skill paths deliberately avoid adding extra copies for agents that support
~/.agents/skills. Instruction files are optional: native skill discovery also routes
short lifecycle requests. No product settings or chat histories are rewritten.
"""
from pathlib import Path
import re

PROFILES = {
    'claude': {'label': 'Claude Code', 'skills': '.claude/skills', 'instructions': '.claude/CLAUDE.md', 'detect': ['.claude']},
    'codex': {'label': 'Codex', 'skills': '.agents/skills', 'instructions': '.codex/AGENTS.md', 'detect': ['.codex']},
    'antigravity': {'label': 'Antigravity app/IDE', 'skills': '.gemini/config/skills', 'instructions': '.gemini/GEMINI.md', 'detect': ['.gemini/config', '.gemini/antigravity']},
    'antigravity-cli': {'label': 'Antigravity CLI', 'skills': '.gemini/antigravity-cli/skills', 'instructions': '.gemini/GEMINI.md', 'detect': ['.gemini/antigravity-cli']},
    'vibe': {'label': 'Mistral Vibe Code', 'skills': '.agents/skills', 'instructions': None, 'detect': ['.vibe']},
    'gemini': {'label': 'Gemini CLI', 'skills': '.agents/skills', 'instructions': '.gemini/GEMINI.md', 'detect': ['.gemini/settings.json', '.gemini/skills']},
    'cursor': {'label': 'Cursor', 'skills': '.agents/skills', 'instructions': None, 'detect': ['.cursor']},
    'copilot': {'label': 'GitHub Copilot CLI', 'skills': '.copilot/skills', 'instructions': '.copilot/copilot-instructions.md', 'detect': ['.copilot']},
    'opencode': {'label': 'OpenCode', 'skills': '.agents/skills', 'instructions': '.config/opencode/AGENTS.md', 'detect': ['.config/opencode']},
    'windsurf': {'label': 'Windsurf Cascade', 'skills': '.codeium/windsurf/skills', 'instructions': None, 'detect': ['.codeium/windsurf']},
    'devin': {'label': 'Devin local CLI/desktop', 'skills': '.config/devin/skills', 'instructions': None, 'detect': ['.config/devin']},
    'cline': {'label': 'Cline', 'skills': '.cline/skills', 'instructions': None, 'detect': ['.cline']},
    'roo': {'label': 'Roo Code', 'skills': '.agents/skills', 'instructions': None, 'detect': ['.roo']},
    'portable': {'label': 'Agent Skills compatible host', 'skills': '.agents/skills', 'instructions': None, 'detect': []},
}
ALIASES = {'claude-code': 'claude', 'mistral': 'vibe', 'mistral-vibe': 'vibe',
           'gemini-cli': 'gemini', 'copilot-cli': 'copilot'}


def canonical(name):
    name = ALIASES.get(name, name)
    if name not in PROFILES:
        raise ValueError('Supported agents: ' + ', '.join(PROFILES))
    return name


def registration_allowed(home, path, kind, owner):
    """Permit exact supported entries, never agent roots or arbitrary registry paths."""
    if not path.is_relative_to(home) or not path.parent.resolve().is_relative_to(home):
        return False
    relative = path.relative_to(home)
    if kind == 'block':
        return not path.is_symlink() and str(relative) in {
            str(Path(p['instructions'])) for p in PROFILES.values() if p['instructions']}
    if kind != 'skill':
        return False
    if re.fullmatch(r'[a-z0-9][a-z0-9-]*', path.name):
        roots = {home / p['skills'] for p in PROFILES.values()}
        # Previously registered Codex skills remain detachable after a migration.
        roots.add(home / '.codex/skills')
        if path.parent in roots:
            return True
    return owner == 'BAIT' and relative.parts in [
        ('.claude', 'knowledge'), ('.agents', 'knowledge'), ('.codex', 'knowledge')]
