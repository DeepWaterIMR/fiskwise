#!/usr/bin/env python3
"""Check/synchronize the shared version hook in maintained source checkouts.

Read-only unless --apply. --enable also configures Git, preserving unrelated hooks.
Never visits installed R libraries, creates a repository, or changes a license.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LEGACY_HASHES = {
    '4be003819a742d5e186abe44d57f086f519fc17f4e954855c457429372327c83',
    '9e373f07cabfbe3760b2e9a9569f6a4b8fa15b7d2c428cb009b674e7f0d438f7',
}


def owned_hook(path):
    return path.is_file() and (hashlib.sha256(path.read_bytes()).hexdigest() in LEGACY_HASHES
        or path.read_text().startswith('#!/bin/sh\n# Fiskwise ecosystem version policy'))


def enable_hook(repo, apply=False):
    repo = Path(repo).resolve()
    hook = repo / '.githooks/pre-commit'
    if not owned_hook(hook):
        return 'version hook missing or custom; preserve and review'
    result = subprocess.run(['git', '-C', str(repo), 'config', '--get', 'core.hooksPath'], capture_output=True, text=True)
    configured = result.stdout.strip()
    if configured:
        actual = Path(configured).expanduser()
        actual = actual if actual.is_absolute() else repo / actual
        if actual.resolve() == hook.parent.resolve():
            return 'enabled'
        return 'custom hooksPath preserved; integrate the version hook before committing'
    raw = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--git-path', 'hooks/pre-commit'], text=True).strip()
    default = Path(raw) if Path(raw).is_absolute() else repo / raw
    if default.exists() and not owned_hook(default):
        return 'custom default pre-commit preserved; integrate the version hook before committing'
    if apply:
        subprocess.run(['git', '-C', str(repo), 'config', 'core.hooksPath', '.githooks'], check=True)
        return 'enabled'
    return 'enable-needed'


def sync_repository(repo, kind, apply=False, enable=False):
    repo = Path(repo).resolve()
    record = {'repo': repo.name, 'path': str(repo)}
    if not (repo / '.git').exists():
        return dict(record, status='source checkout unavailable; skipped')
    source = ROOT / '.githooks/pre-commit'
    target = repo / '.githooks/pre-commit'
    if target.is_symlink() or not target.parent.resolve().is_relative_to(repo):
        return dict(record, status='redirected hook preserved')
    if target.exists() and not owned_hook(target):
        return dict(record, status='custom repository hook preserved; manual integration required')
    license_source = ROOT / 'LICENSE'
    license_target = repo / '.githooks/fiskwise-version.LICENSE'
    if license_target.is_symlink() or (license_target.exists() and license_target.read_bytes() != license_source.read_bytes()):
        return dict(record, status='existing hook license preserved; manual review required')
    metadata = repo / ('DESCRIPTION' if kind == 'r' else 'VERSION')
    if not metadata.exists() and kind == 'r':
        return dict(record, status='DESCRIPTION missing; no changes made')
    if not metadata.exists():
        # Adopt a declared pack/site version, otherwise seed a new source at 0.0.1.
        package = repo / 'website/package.json'
        initial = json.loads(package.read_text()).get('version', '0.0.1') if package.exists() else '0.0.1'
        record['initial_version'] = initial
        if apply:
            metadata.write_text(f'version: {initial}\ndate: {datetime.date.today().isoformat()}\n')
    changed = not target.exists() or target.read_bytes() != source.read_bytes() or not license_target.exists()
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target != source:
            shutil.copy2(source, target)
        target.chmod(target.stat().st_mode | 0o111)
        if license_target != license_source:
            shutil.copy2(license_source, license_target)
    record['status'] = 'synchronized' if apply else 'sync-needed' if changed else 'current'
    if enable:
        record['git_hook'] = enable_hook(repo, apply=apply)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT.parent)
    parser.add_argument('--r-packages-root', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--enable', action='store_true')
    args = parser.parse_args()
    inventory = json.loads((ROOT / 'packages.json').read_text())
    records = [sync_repository(ROOT, 'knowledge', args.apply, args.enable)]
    for pack in inventory:
        if pack['status'] != 'available':
            continue
        candidates = [args.workspace / pack['name']]
        if pack['kind'] == 'r':
            candidates.append((args.r_packages_root or args.workspace.parent / 'R packages') / pack['name'])
        repo = next((p for p in candidates if (p / '.git').exists()), candidates[0])
        records.append(sync_repository(repo, pack['kind'], args.apply, args.enable))
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
