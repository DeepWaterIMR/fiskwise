"""Local Fiskwise ownership registry and reversible skill lifecycle. No research data reads."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
BEGIN, END = '<!-- fiskwise-managed:start -->', '<!-- fiskwise-managed:end -->'

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def fingerprint(path):
    path = Path(path)
    if path.is_symlink():
        return {'kind': 'link', 'target': str(path.readlink())}
    if path.is_file():
        return {'kind': 'file', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    if path.is_dir():
        entries = {}
        for item in sorted(path.rglob('*')):
            if item.is_symlink() or item.is_file():
                entries[str(item.relative_to(path))] = fingerprint(item)
        return {'kind': 'directory', 'sha256': digest(entries)}
    return None

def block(text):
    if BEGIN not in text and END not in text:
        return None
    if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(END) < text.index(BEGIN):
        raise ValueError('Ambiguous Fiskwise instruction markers; preserve the file for review.')
    return BEGIN + text.split(BEGIN, 1)[1].split(END, 1)[0] + END

def replace_block(text, replacement):
    old = block(text)
    if old:
        return text.replace(old, replacement or '', 1)
    return text.rstrip() + '\n\n' + replacement + '\n' if replacement else text

def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()

def pack_version(path):
    result = {'version': None, 'date': None, 'revision': None}
    file = Path(path) / 'VERSION'
    if file.exists():
        for key in ['version', 'date']:
            match = re.search(r'^' + key + r':\s*(\S+)', file.read_text(), re.M)
            if match:
                result[key] = match[1]
    if (Path(path) / '.git').exists():
        result['revision'] = git(path, 'rev-parse', 'HEAD')
    return result

class Manager:
    def __init__(self, workspace=None, home=None, root=None):
        self.root = Path(root or ROOT).resolve()
        self.workspace = Path(workspace or self.root.parent).resolve()
        self.home = Path(home or Path.home()).resolve()
        self.state_dir = self.home / '.fiskwise'
        self.state_file = self.state_dir / 'config.json'
        self.inventory = {p['name']: p for p in json.loads((self.root / 'packages.json').read_text())}
        self.state = json.loads(self.state_file.read_text()) if self.state_file.exists() else {
            'schema_version': 1, 'enabled': True, 'components': {}, 'registrations': [],
            'consent': {'r_packages': None}, 'databases': [], 'history': []}
        if self.state.get('schema_version') != 1:
            raise ValueError('Unsupported registry schema; no changes made.')

    def save(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.state_file.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.state, indent=2) + '\n')
        os.replace(temporary, self.state_file)
        if os.name != 'nt':
            self.state_file.chmod(0o600)

    def backup(self, path):
        path = Path(path)
        if fingerprint(path) is None:
            return None
        relative = path.relative_to(self.home)
        dest = self.state_dir / 'backups' / uuid.uuid4().hex / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            dest.symlink_to(path.readlink(), target_is_directory=path.is_dir())
        elif path.is_dir():
            shutil.copytree(path, dest, symlinks=True)
        else:
            shutil.copy2(path, dest)
        return str(dest)

    def ordered(self, include=(), installed=False, adopt=False):
        requested = (list(self.state['components']) if installed else
                     [n for n, p in self.inventory.items() if p['kind'] == 'knowledge' and p.get('core')])
        requested = [n for n in requested if n != 'fiskwise'] + list(include)
        if adopt:
            for n, p in self.inventory.items():
                if p['kind'] == 'knowledge' and p['status'] == 'available' and (self.workspace / n / 'AGENTS.md').exists():
                    requested.append(n)
        visiting, done, order = set(), set(), []
        def visit(name):
            if name in done:
                return
            if name not in self.inventory or self.inventory[name]['kind'] != 'knowledge':
                raise ValueError(f'Unknown knowledge pack: {name}')
            p = self.inventory[name]
            if p['status'] != 'available':
                raise ValueError(f'{name} is planned; no installable pack exists.')
            if name in visiting:
                raise ValueError('Cyclic component dependencies')
            visiting.add(name)
            for dependency in p.get('dependencies', []):
                visit(dependency)
            visiting.remove(name)
            done.add(name)
            order.append(name)
        for name in requested:
            visit(name)
        return ['fiskwise'] + order

    def location(self, name):
        if name == 'fiskwise':
            return self.root
        existing = self.state['components'].get(name, {}).get('path')
        if existing and (Path(existing) / 'AGENTS.md').exists():
            return Path(existing).resolve()
        configs = {'wise-writing': ('.wise-writing', '.academic-writing', 'academic_writing_path'),
                   'index-wise': ('.index-wise', '.index-template', 'index_template_path'),
                   'spict-wise': ('.spict-wise', '.spict-template', 'spict_template_path'),
                   'BAIT': ('.bait', '.bait', 'bait_path')}
        if name in configs:
            canonical, legacy, key = configs[name]
            for directory in dict.fromkeys([canonical, legacy]):
                file = self.home / directory / 'config.json'
                if file.exists():
                    candidate = json.loads(file.read_text()).get(key)
                    if candidate and (Path(candidate).expanduser() / 'AGENTS.md').exists():
                        return Path(candidate).expanduser().resolve()
        return self.workspace / name

    def agents(self, selected=None):
        if selected:
            if not set(selected) <= {'claude', 'codex'}:
                raise ValueError('Supported agents: claude, codex')
            return list(dict.fromkeys(selected))
        found = []
        if (self.home / '.claude').exists():
            found.append('claude')
        if (self.home / '.codex').exists() or (self.home / '.agents').exists() or not found:
            found.append('codex')
        return found

    def sources(self, names):
        result = {}
        for name in names:
            roots = ['skills'] if name == 'fiskwise' else self.inventory[name].get('skill_roots', [])
            forwarded = [] if name == 'fiskwise' else self.inventory[name].get('forwarded_skills', [])
            for directory in roots:
                parent = self.location(name) / directory
                if not parent.exists():
                    continue
                for path in sorted(parent.iterdir()):
                    if not (path / 'SKILL.md').exists() or path.name in forwarded:
                        continue
                    source = (path / 'SKILL.md').read_text()
                    if re.search(r'^\s*forwarding:\s*true\s*$', source, re.M):
                        continue
                    skill = re.search(r'^name:\s*["\']?([^\n"\']+)', source, re.M)
                    if not skill or skill[1].strip() != path.name:
                        raise ValueError(f'Skill ID/folder mismatch: {path}')
                    if path.name in result:
                        raise ValueError(f'Duplicate canonical skill owner: {path.name}')
                    result[path.name] = (name, path)
        return result

    def hook_text(self):
        return f'''{BEGIN}
## Fiskwise research workflow

For scientific R work using Fiskwise or its packs, read the installed
`fiskwise-workflow` skill at {self.root / 'skills/fiskwise-workflow/SKILL.md'}.
Use R/tidyverse, Quarto reports, and relevant ecosystem packages. Always use
wise-writing's `r-code-style` for new or edited R code. Website/maintenance tooling
is task-appropriate. Delegate only when estimated total cost is lower after
context, coordination, repeated work, and review; keep small/context-heavy work local.
Scientific methods remain with their specialist packs. Follow BAIT for IMR Biotic
data and keep raw data local. Package-install consent is recorded in
{self.state_file}; system software and database downloads need their own approval.
{END}'''

    def install_plan(self, include=(), selected=None, adopt=False):
        names = self.ordered(include, adopt=adopt)
        actions = []
        for name in names:
            path = self.location(name)
            if not path.exists():
                actions.append({'action': 'clone', 'component': name, 'path': str(path),
                                'repo': self.inventory[name]['repo']})
        for skill, (owner, source) in self.sources(names).items():
            for agent in self.agents(selected):
                target = self.home / ('.claude/skills' if agent == 'claude' else '.agents/skills') / skill
                desired = {'kind': 'link', 'target': str(source)}
                if fingerprint(target) != desired:
                    actions.append({'action': 'register', 'owner': owner, 'skill': skill,
                                    'path': str(target), 'source': str(source), 'existing': fingerprint(target) is not None, 'replacement': 'back up prior registration before replacing'})
        return {'components': names, 'actions': actions, 'r_packages': self.state['consent'].get('r_packages'),
                'note': 'Skill/config operations only. R/system installation and database downloads are separate.'}

    def register_link(self, target, source, owner, update=False, prefer_copy=False):
        target, source = Path(target), Path(source)
        if not target.parent.resolve().is_relative_to(self.home):
            raise ValueError(f'Agent directory resolves outside selected home; preserve for review: {target}')
        record = next((r for r in self.state['registrations'] if r['path'] == str(target)), None)
        current = fingerprint(target)
        managed_copy = bool(record and record.get('source') == str(source) and current == record.get('installed') and current is not None and current.get('kind') == 'directory')
        if record and current != record['installed'] and not (record.get('pending') and (current is None or current == {'kind': 'link', 'target': str(source)})):
            raise ValueError(f'Modified registration preserved: {target}')
        if not record:
            record = {'path': str(target), 'owner': owner, 'kind': 'skill',
                      'origin': 'adopted' if current else 'created',
                      'previous': current, 'backup': self.backup(target)}
        record.update(source=str(source), installed=current, pending=True)
        if record not in self.state['registrations']:
            self.state['registrations'].append(record)
        self.save()
        desired = {'kind': 'link', 'target': str(source)}
        if current != desired and not managed_copy:
            if current:
                if target.is_symlink() or target.is_file():
                    target.unlink()
                else:
                    shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                if prefer_copy:
                    raise OSError('Use copy fallback')
                target.symlink_to(source, target_is_directory=True)
            except OSError:
                shutil.copytree(source, target, symlinks=False)
        elif update and current and current['kind'] == 'directory':
            # A managed copy can be refreshed only after its recorded fingerprint matched.
            shutil.rmtree(target)
            shutil.copytree(source, target)
        record.update(source=str(source), installed=fingerprint(target), pending=False)
        if record not in self.state['registrations']:
            self.state['registrations'].append(record)
        self.save()

    def register_block(self, target):
        target = Path(target)
        if target.is_symlink() or not target.parent.resolve().is_relative_to(self.home):
            raise ValueError(f'Instruction file resolves outside its registered location: {target}')
        text = target.read_text() if target.exists() else ''
        old = block(text)
        record = next((r for r in self.state['registrations'] if r['path'] == str(target)), None)
        if record and digest(old) != record['installed']:
            raise ValueError(f'Modified instruction block preserved: {target}')
        if not record:
            record = {'path': str(target), 'owner': 'fiskwise', 'kind': 'block',
                      'origin': 'adopted' if old else 'created', 'previous': old,
                      'backup': self.backup(target)}
        desired = self.hook_text()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(replace_block(text, desired))
        record['installed'] = digest(desired)
        if record not in self.state['registrations']:
            self.state['registrations'].append(record)
        self.save()

    def install(self, include=(), selected=None, adopt=False, allow_clone=True, prefer_copy=False):
        names = self.ordered(include, adopt=adopt)
        for name in names:
            path = self.location(name)
            created = not path.exists()
            if created:
                if not allow_clone:
                    raise ValueError(f'Missing pack checkout: {path}')
                path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(['git', 'clone', self.inventory[name]['repo'], str(path)], check=True)
            if not (path / 'AGENTS.md').exists():
                raise ValueError(f'Invalid pack checkout: {path}')
            old = self.state['components'].get(name, {})
            self.state['components'][name] = dict(old, path=str(path), origin=old.get('origin', 'created' if created else 'adopted'), **pack_version(path))
            self.save()
        for skill, (owner, source) in self.sources(names).items():
            for agent in self.agents(selected):
                target = self.home / ('.claude/skills' if agent == 'claude' else '.agents/skills') / skill
                self.register_link(target, source, owner, prefer_copy=prefer_copy)
        for agent in self.agents(selected):
            self.register_block(self.home / ('.claude/CLAUDE.md' if agent == 'claude' else '.codex/AGENTS.md'))
        self.component_configs(names)
        bait_config = self.home / '.bait/config.json'
        if 'BAIT' in names and bait_config.exists():
            database = json.loads(bait_config.read_text()).get('bes_db_path')
            if database and not any(d['path'] == database for d in self.state['databases']):
                self.state['databases'].append({'path': database, 'origin': 'adopted', 'state': 'unverified', 'note': 'Pre-existing config; no data accessed.'})
        if 'BAIT' in names:
            for directory in ['.claude', '.agents', '.codex']:
                target = self.home / directory / 'knowledge'
                self.register_link(target, self.location('BAIT') / 'knowledge', 'BAIT', prefer_copy=prefer_copy)
        if (self.root / '.git').exists():
            hooks = subprocess.run(['git', '-C', str(self.root), 'config', '--get', 'core.hooksPath'], capture_output=True, text=True)
            if not hooks.stdout.strip() or hooks.stdout.strip() == '.githooks':
                self.state.setdefault('hook_config', {'previous': hooks.stdout.strip() or None, 'installed': '.githooks', 'path': str(self.root)})
                subprocess.run(['git', '-C', str(self.root), 'config', 'core.hooksPath', '.githooks'], check=True)
            else:
                self.state['hook_note'] = 'Existing custom hooks retained; integrate .githooks/pre-commit manually.'
        self.state['enabled'] = True
        self.state['history'].append({'operation': 'install', 'at': stamp(), 'components': names})
        self.save()
        return self.state

    def component_configs(self, names):
        configs = {'wise-writing': ('.wise-writing', '.academic-writing', 'academic_writing_path'),
                   'index-wise': ('.index-wise', '.index-template', 'index_template_path'),
                   'spict-wise': ('.spict-wise', '.spict-template', 'spict_template_path'),
                   'BAIT': ('.bait', '.bait', 'bait_path')}
        for name in names:
            if name not in configs:
                continue
            canonical, legacy, key = configs[name]
            merged = {}
            for directory in dict.fromkeys([legacy, canonical]):
                path = self.home / directory / 'config.json'
                if path.exists():
                    merged.update(json.loads(path.read_text()))
            merged.update({key: str(self.location(name)), 'skills_synced_to': ['~/.claude/skills', '~/.agents/skills']})
            for directory in dict.fromkeys([canonical, legacy]):
                path = self.home / directory / 'config.json'
                content = json.dumps(merged, indent=2) + '\n'
                if not path.exists() or path.read_text() != content:
                    prior = fingerprint(path)
                    backup = self.backup(path)
                    self.state.setdefault('config_resources', []).append({'path': str(path), 'origin': 'adopted' if prior else 'created', 'previous': prior, 'backup': backup, 'installed': {'kind': 'file', 'sha256': hashlib.sha256(content.encode()).hexdigest()}, 'uninstall': 'retained component configuration'})
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)

    def set_consent(self, allowed):
        self.state['consent']['r_packages'] = allowed
        self.state['consent']['recorded_at'] = stamp()
        self.save()

    def update(self, apply=False):
        results = []
        for name in self.ordered(installed=True):
            if name not in self.state['components']:
                continue
            p = self.state['components'][name]
            path = Path(p['path'])
            item = {'component': name, 'path': str(path), 'status': 'unavailable'}
            results.append(item)
            if not (path / '.git').exists():
                continue
            if git(path, 'status', '--porcelain'):
                item['status'] = 'local-changes-preserved'
                continue
            branch = subprocess.run(['git', '-C', str(path), 'symbolic-ref', '-q', '--short', 'HEAD'], capture_output=True, text=True)
            if p.get('pinned') or branch.returncode != 0:
                item['status'] = 'pinned-preserved'
                continue
            if not apply:
                item['status'] = 'eligible; remote check runs with --apply'
                continue
            try:
                # Refresh the configured upstream, preserving the current branch/ref.
                git(path, 'fetch', '--quiet')
                upstream = git(path, 'rev-parse', '--abbrev-ref', '@{upstream}')
                ahead, behind = map(int, git(path, 'rev-list', '--left-right', '--count', f'HEAD...{upstream}').split())
                if ahead:
                    item['status'] = 'ahead-or-diverged-preserved'
                    continue
                if behind:
                    git(path, 'merge', '--ff-only', upstream)
                item['status'] = 'updated' if behind else 'current'
                p.update(pack_version(path))
            except subprocess.CalledProcessError:
                item['status'] = 'remote-check-unavailable'
        if apply:
            # Refresh only unchanged managed registrations; do not replace customized copies.
            owners = list(self.state['components'])
            for skill, (owner, source) in self.sources(owners).items():
                for reg in [r for r in list(self.state['registrations']) if r['owner'] == owner and Path(r['path']).name == skill and r['kind'] == 'skill']:
                    try:
                        self.register_link(reg['path'], source, owner, update=True)
                    except ValueError as error:
                        results.append({'status': 'modified-registration-preserved', 'detail': str(error)})
            self.state['history'].append({'operation': 'update', 'at': stamp(), 'results': results})
            self.save()
        return results

    def removal_plan(self, include_adopted=False):
        items, preserved = [], []
        for reg in self.state['registrations']:
            path = Path(reg['path'])
            # Only exact recorded entries inside supported user agent locations are eligible.
            relative = path.relative_to(self.home) if path.is_relative_to(self.home) else None
            parts = relative.parts if relative else ()
            allowed = (reg['kind'] == 'block' and parts in [('.claude', 'CLAUDE.md'), ('.codex', 'AGENTS.md')]) or (
                reg['kind'] == 'skill' and len(parts) == 3 and parts[0] in ['.claude', '.agents', '.codex'] and
                parts[1] == 'skills' and re.fullmatch(r'[a-z0-9][a-z0-9-]*', parts[2])) or (
                reg['kind'] == 'skill' and reg['owner'] == 'BAIT' and len(parts) == 2 and
                parts[0] in ['.claude', '.agents', '.codex'] and parts[1] == 'knowledge')
            allowed = allowed and path.parent.resolve().is_relative_to(self.home) and not (reg['kind'] == 'block' and path.is_symlink())
            previous = reg.get('backup')
            if allowed and reg['kind'] != 'block' and reg.get('previous'):
                backup = Path(previous) if previous else None
                if not backup or not backup.absolute().is_relative_to(self.state_dir / 'backups') or fingerprint(backup) != reg['previous']:
                    preserved.append({'path': str(path), 'reason': 'prior registration backup missing or changed'})
                    continue
            if not allowed:
                preserved.append({'path': str(path), 'reason': 'outside registered agent roots'})
                continue
            current = digest(block(path.read_text())) if reg['kind'] == 'block' and path.exists() else fingerprint(path)
            if current != reg['installed']:
                preserved.append({'path': str(path), 'reason': 'modified or missing'})
            elif reg['origin'] == 'adopted' and not include_adopted:
                preserved.append({'path': str(path), 'reason': 'pre-existing/adopted'})
            else:
                items.append(dict(reg))
        plan = {'remove': items, 'preserve': preserved, 'database': 'retained; separate confirmation required', 'retained': ['component configs and their backups', 'repositories and version-hook configuration', 'R, Quarto, R packages, research projects', 'registry audit trail']}
        plan['confirmation'] = digest(plan)[:16]
        return plan

    def uninstall(self, confirmation, include_adopted=False):
        plan = self.removal_plan(include_adopted)
        if not confirmation or confirmation != plan['confirmation']:
            raise ValueError('No matching confirmation. Show the current preview and obtain user approval first.')
        for reg in plan['remove']:
            path = Path(reg['path'])
            if reg['kind'] == 'block':
                path.write_text(replace_block(path.read_text(), reg['previous']))
            else:
                self.backup(path)
                if path.is_symlink() or path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
                previous = reg.get('backup')
                if previous and (Path(previous).exists() or Path(previous).is_symlink()):
                    backup = Path(previous)
                    if backup.is_symlink():
                        path.symlink_to(backup.readlink(), target_is_directory=True)
                    elif backup.is_dir():
                        shutil.copytree(backup, path, symlinks=True)
                    else:
                        shutil.copy2(backup, path)
            self.state['registrations'].remove(reg)
            self.save()
        self.state['enabled'] = False
        self.state['history'].append({'operation': 'uninstall', 'at': stamp(), 'removed': [r['path'] for r in plan['remove']]})
        self.save()
        return plan

    def database_begin(self, path):
        original = Path(path).expanduser()
        if not original.is_absolute() or original.is_symlink():
            raise ValueError('Creation needs an absolute non-symlink path.')
        path = original.resolve()
        if path.exists() or path == path.parent or path.suffix != '.duckdb':
            raise ValueError('Creation provenance requires an absent, explicit .duckdb file path.')
        token = uuid.uuid4().hex
        self.state['databases'].append({'path': str(path), 'origin': 'fiskwise', 'state': 'pending',
                                        'absent_before': True, 'token': token, 'started_at': stamp()})
        self.save()
        return token

    def database_complete(self, token, verified=False):
        record = next((d for d in self.state['databases'] if d.get('token') == token and d['state'] == 'pending'), None)
        if not record or not verified or not Path(record['path']).is_file():
            raise ValueError('Require the original creation token, completed file, and successful BAIT verification.')
        info = Path(record['path']).stat()
        record.update(state='verified', verified_at=stamp(), device=info.st_dev, inode=info.st_ino)
        self.save()

    def database_plan(self, path):
        original = Path(path).expanduser()
        if original.is_symlink():
            raise ValueError('Symlink database paths are preserved.')
        path = original.resolve()
        record = next((d for d in self.state['databases'] if d['path'] == str(path)), None)
        if not record or record.get('origin') != 'fiskwise' or not record.get('absent_before') or record.get('state') != 'verified':
            raise ValueError('Database is pre-existing, unverified, or has unknown provenance; retain it.')
        if not path.is_file() or path.is_symlink():
            raise ValueError('Database missing or replaced by a symlink; preserve for review.')
        stat = path.stat()
        if (record.get('device'), record.get('inode')) != (stat.st_dev, stat.st_ino):
            raise ValueError('Database identity changed since verified creation; preserve for BAIT review.')
        plan = {'path': str(path), 'size_bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                'device': stat.st_dev, 'inode': stat.st_ino, 'method': 'recoverable removal'}
        plan['confirmation'] = digest(plan)[:16]
        return plan

    @staticmethod
    def database_closed(path):
        if Path(str(path) + '.wal').exists():
            return False
        if os.name == 'nt':
            code = '$f=[IO.File]::Open($env:FISKWISE_DB_TARGET,"Open","Read","None");$f.Dispose()'
            result = subprocess.run(['powershell', '-NoProfile', '-Command', code], env=dict(os.environ, FISKWISE_DB_TARGET=str(path)), capture_output=True)
            return result.returncode == 0
        lsof = shutil.which('lsof')
        if not lsof:
            return False  # Cannot prove closure; do not guess.
        result = subprocess.run([lsof, '-t', '--', str(path)], capture_output=True, text=True)
        return result.returncode == 1 and not result.stdout.strip()

    def database_remove(self, path, confirmation, quarantine=None):
        plan = self.database_plan(path)
        if confirmation != plan['confirmation']:
            raise ValueError('Separate current database confirmation is required.')
        path = Path(plan['path'])
        if not self.database_closed(path):
            raise ValueError('Database may be open, has a WAL, or closure cannot be verified; no removal.')
        if quarantine:
            destination = Path(quarantine).expanduser().resolve()
            destination.mkdir(parents=True, exist_ok=True)
            if destination.stat().st_dev != path.stat().st_dev:
                raise ValueError('Quarantine must be on the same filesystem.')
        elif sys.platform == 'darwin':
            destination = self.home / '.Trash'
            destination.mkdir(exist_ok=True)
        elif os.name == 'nt':
            code = 'Add-Type -AssemblyName Microsoft.VisualBasic;[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($env:FISKWISE_DB_TARGET,"OnlyErrorDialogs","SendToRecycleBin")'
            subprocess.run(['powershell', '-NoProfile', '-Command', code], env=dict(os.environ, FISKWISE_DB_TARGET=str(path)), check=True)
            destination = None
        else:
            raise ValueError('OS Trash is unavailable here; offer an explicitly selected same-filesystem quarantine.')
        if destination:
            target = destination / (path.name + '.' + uuid.uuid4().hex[:8])
            os.replace(path, target)
            result = str(target)
        else:
            result = 'Windows Recycle Bin'
        record = next(d for d in self.state['databases'] if d['path'] == str(path))
        record.update(state='removed', removal_destination=result, removed_at=stamp())
        self.save()
        return {'removed': str(path), 'recoverable_at': result, 'associated_files': 'retained; not implicitly selected'}
