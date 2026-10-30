"""Backed-up local Fiskwise migration. Dry-run by default; never reads research data."""
from pathlib import Path
import argparse
import datetime
import json
import re
import shutil

RENAMES = {'academic-writing': 'wise-writing', 'presentation-template': 'wise-presentations',
           'index-template': 'index-wise', 'spict-template': 'spict-wise'}
CONFIGS = [('BAIT', '.bait', '.bait', 'bait_path'),
           ('wise-writing', '.wise-writing', '.academic-writing', 'academic_writing_path'),
           ('index-wise', '.index-wise', '.index-template', 'index_template_path'),
           ('spict-wise', '.spict-wise', '.spict-template', 'spict_template_path')]
BEGIN = '<!-- fiskwise-managed:start -->'
END = '<!-- fiskwise-managed:end -->'

class Migration:
    def __init__(self, workspace, home, backup, apply=False):
        self.workspace, self.home, self.backup, self.apply = workspace, home, backup, apply
        self.operations = []

    def save(self, path):
        if path.exists() or path.is_symlink():
            relative = path.relative_to(self.home)
            dest = self.backup / relative
            if dest.exists() or dest.is_symlink():
                return
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink():
                dest.symlink_to(path.readlink())
            elif path.is_dir():
                shutil.copytree(path, dest, symlinks=True)
            else:
                shutil.copy2(path, dest)

    def write(self, path, content):
        if path.exists() and path.read_text() == content:
            return
        self.operations.append('Write ' + str(path))
        if self.apply:
            self.save(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def managed_link(self, path, source, retire=False):
        exists = path.exists() or path.is_symlink()
        if retire and not exists:
            return
        if not retire and path.is_symlink() and path.resolve() == source.resolve():
            return
        self.operations.append(('Retire legacy copy ' if retire else 'Link ') + str(path))
        if self.apply:
            self.save(path)
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            if not retire:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(source, target_is_directory=True)

    def run(self):
        for pack, canonical, legacy, key in CONFIGS:
            location = self.workspace / pack
            if not (location / 'AGENTS.md').exists():
                raise ValueError(f'Missing pack checkout: {location}')
            merged = {}
            for directory in dict.fromkeys([legacy, canonical]):
                cfg = self.home / directory / 'config.json'
                if cfg.exists():
                    merged.update(json.loads(cfg.read_text()))
            merged[key] = str(location)
            destinations = merged.get('skills_synced_to', ['~/.claude/skills', '~/.agents/skills'])
            merged['skills_synced_to'] = list(dict.fromkeys(
                str(item).replace('~/.codex/skills', '~/.agents/skills').replace(
                    str(self.home / '.codex/skills'), str(self.home / '.agents/skills'))
                for item in destinations))
            for directory in dict.fromkeys([canonical, legacy]):
                self.write(self.home / directory / 'config.json', json.dumps(merged, indent=2) + '\n')

        owned = {}
        for pack in ['BAIT', 'wise-writing', 'index-wise', 'spict-wise', 'wise-presentations']:
            source = self.workspace / pack / ('skills' if pack != 'wise-presentations' else '.agents/skills')
            for skill in sorted(source.iterdir()):
                if skill.is_dir() and (skill / 'SKILL.md').exists():
                    if re.search(r'^\s*forwarding:\s*true\s*$', (skill / 'SKILL.md').read_text(), re.M):
                        continue
                    if skill.name in owned:
                        raise ValueError(f'Duplicate managed skill: {skill.name}')
                    owned[skill.name] = skill
        for name, source in owned.items():
            for agent in ['.claude', '.agents']:
                self.managed_link(self.home / agent / 'skills' / name, source)
            self.managed_link(self.home / '.codex/skills' / name, source, retire=True)
        for agent in ['.claude', '.agents', '.codex']:
            self.managed_link(self.home / agent / 'knowledge', self.workspace / 'BAIT/knowledge')

        lines = ['## Fiskwise ecosystem', '',
                 'Fiskwise is the umbrella for the fisheries-science knowledge packs.',
                 'Canonical repositories: DeepWaterIMR/fiskwise, wise-writing, wise-presentations,',
                 'BAIT, index-wise, spict-wise, gadget-wise.',
                 'Keep existing academic-*, biotic-*, index-*, spict-*, gadget-* and presentation skill IDs.',
                 'Use BAIT for IMR Biotic work; read its AGENTS.md and the relevant skills.',
                 'Prefer the database path recorded in ~/.bait/config.json; keep raw data local.',
                 'Local checkouts:']
        lines += [f'- {name}: {self.workspace / name}' for name in ['fiskwise', 'wise-writing',
                  'wise-presentations', 'BAIT', 'index-wise', 'spict-wise']]
        lines += ['', 'Installed skills: ~/.claude/skills (Claude), ~/.agents/skills (Codex).',
                  'Old repository names are migration aliases; use canonical names for new work.']
        block = BEGIN + '\n' + '\n'.join(lines) + '\n' + END
        for relative in ['.claude/CLAUDE.md', '.codex/AGENTS.md']:
            path = self.home / relative
            text = path.read_text() if path.exists() else ''
            if BEGIN in text:
                if END not in text:
                    raise ValueError(f'Incomplete managed block: {path}')
                before, rest = text.split(BEGIN, 1)
                _, after = rest.split(END, 1)
                text = before + block + after
            else:
                text = text.rstrip() + '\n\n' + block + '\n'
            self.write(path, text)

        config = self.home / '.codex/config.toml'
        if config.exists():
            text = config.read_text()
            for old, new in RENAMES.items():
                text = text.replace(str(self.workspace / old), str(self.workspace / new))
            self.write(config, text)
        return self.operations

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--backup-dir', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = args.backup_dir or args.home / '.fiskwise/backups' / stamp
    migration = Migration(args.workspace.resolve(), args.home.resolve(), backup, args.apply)
    operations = migration.run()
    print('\n'.join(operations) or 'Already migrated; no changes.')
    if args.apply:
        backup.mkdir(parents=True, exist_ok=True)
        (backup / 'operations.json').write_text(json.dumps(operations, indent=2))
        print('Backups:', backup)
    else:
        print('Dry run. Pass --apply to make these changes.')

if __name__ == '__main__':
    main()
