"""Test version-hook synchronization in isolated source checkouts."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("versioning_sync", ROOT / "scripts/sync_versioning.py")
versioning_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versioning_sync)
sync_repository = versioning_sync.sync_repository
enable_hook = versioning_sync.enable_hook


class VersioningSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def repo(self, name):
        path = self.base / name
        path.mkdir(parents=True)
        subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
        return path

    def test_sync_installs_canonical_hook_and_license_repeatably(self):
        repo = self.repo("knowledge-pack")
        metadata = "version: 1.2.3\ndate: 2020-01-01\n"
        (repo / "VERSION").write_text(metadata)

        check = sync_repository(repo, "knowledge", apply=False)
        self.assertEqual(check["status"], "sync-needed")
        self.assertFalse((repo / ".githooks/pre-commit").exists())
        self.assertFalse((repo / ".githooks/fiskwise-version.LICENSE").exists())
        self.assertEqual((repo / "VERSION").read_text(), metadata)

        applied = sync_repository(repo, "knowledge", apply=True)
        hook = repo / ".githooks/pre-commit"
        notice = repo / ".githooks/fiskwise-version.LICENSE"
        self.assertEqual(applied["status"], "synchronized")
        self.assertEqual(hook.read_bytes(), (ROOT / ".githooks/pre-commit").read_bytes())
        self.assertEqual(notice.read_bytes(), (ROOT / "LICENSE").read_bytes())
        self.assertTrue(os.access(hook, os.X_OK))
        first_contents = (hook.read_bytes(), notice.read_bytes())

        repeated = sync_repository(repo, "knowledge", apply=True)
        self.assertEqual(repeated["status"], "synchronized")
        self.assertEqual((hook.read_bytes(), notice.read_bytes()), first_contents)
        self.assertEqual((repo / "VERSION").read_text(), metadata)

    def test_r_package_sync_leaves_description_and_package_license_untouched(self):
        repo = self.repo("r-package")
        description = (
            "Package: fixture\nVersion: 0.5.2\nTitle: Example package\n"
            "Description: Example package metadata.\nLicense: GPL-3\n"
        )
        package_license = "Package license text owned by the package.\n"
        (repo / "DESCRIPTION").write_text(description)
        (repo / "LICENSE").write_text(package_license)

        result = sync_repository(repo, "r", apply=True)

        self.assertEqual(result["status"], "synchronized")
        self.assertEqual((repo / "DESCRIPTION").read_text(), description)
        self.assertEqual((repo / "LICENSE").read_text(), package_license)
        self.assertEqual((repo / ".githooks/fiskwise-version.LICENSE").read_bytes(),
                         (ROOT / "LICENSE").read_bytes())

    def test_missing_knowledge_version_adopts_website_version(self):
        repo = self.repo("website-pack")
        package = repo / "website/package.json"
        package.parent.mkdir()
        package.write_text(json.dumps({"name": "fixture", "version": "2.6.4"}))

        preview = sync_repository(repo, "knowledge", apply=False)
        self.assertEqual(preview["initial_version"], "2.6.4")
        self.assertFalse((repo / "VERSION").exists())
        self.assertEqual(preview["status"], "sync-needed")

        applied = sync_repository(repo, "knowledge", apply=True)
        self.assertEqual(applied["initial_version"], "2.6.4")
        self.assertEqual((repo / "VERSION").read_text(),
                         f"version: 2.6.4\ndate: {versioning_sync.datetime.date.today().isoformat()}\n")

    def test_custom_repository_hook_is_preserved(self):
        repo = self.repo("custom-hook")
        (repo / "VERSION").write_text("version: 1.0.0\ndate: 2020-01-01\n")
        hook = repo / ".githooks/pre-commit"
        hook.parent.mkdir()
        custom = b"#!/bin/sh\necho custom hook\n"
        hook.write_bytes(custom)

        result = sync_repository(repo, "knowledge", apply=True)

        self.assertEqual(result["status"], "custom repository hook preserved; manual integration required")
        self.assertEqual(hook.read_bytes(), custom)
        self.assertFalse((repo / ".githooks/fiskwise-version.LICENSE").exists())

    def test_custom_core_hookspath_is_preserved_when_enabling(self):
        repo = self.repo("custom-hookspath")
        (repo / "VERSION").write_text("version: 1.0.0\ndate: 2020-01-01\n")
        custom_dir = repo / ".custom-hooks"
        custom_dir.mkdir()
        self.git(repo, "config", "core.hooksPath", ".custom-hooks")

        result = sync_repository(repo, "knowledge", apply=True, enable=True)

        self.assertEqual(result["git_hook"], "custom hooksPath preserved; integrate the version hook before committing")
        self.assertEqual(self.git(repo, "config", "--get", "core.hooksPath"), ".custom-hooks")
        self.assertTrue((repo / ".githooks/pre-commit").is_file())

    def test_custom_default_precommit_is_preserved(self):
        repo = self.repo("default-hook")
        (repo / "VERSION").write_text("version: 1.0.0\ndate: 2020-01-01\n")
        default_hook = repo / ".git/hooks/pre-commit"
        custom = b"#!/bin/sh\necho default custom hook\n"
        default_hook.write_bytes(custom)

        result = sync_repository(repo, "knowledge", apply=True, enable=True)

        self.assertEqual(result["git_hook"], "custom default pre-commit preserved; integrate the version hook before committing")
        self.assertEqual(default_hook.read_bytes(), custom)
        self.assertEqual(self.git(repo, "config", "--get", "core.hooksPath", check=False), "")
        self.assertTrue((repo / ".githooks/pre-commit").is_file())

    def test_check_only_does_not_change_files_or_git_config(self):
        repo = self.repo("check-only")
        (repo / "VERSION").write_text("version: 3.1.9\ndate: 2020-01-01\n")
        before = {str(path.relative_to(repo)): path.read_bytes()
                  for path in repo.rglob("*") if path.is_file() and ".git" not in path.parts}
        result = sync_repository(repo, "knowledge", apply=False, enable=True)
        after = {str(path.relative_to(repo)): path.read_bytes()
                 for path in repo.rglob("*") if path.is_file() and ".git" not in path.parts}

        self.assertEqual(result["status"], "sync-needed")
        self.assertEqual(result["git_hook"], "version hook missing or custom; preserve and review")
        self.assertEqual(after, before)
        self.assertEqual(self.git(repo, "config", "--get", "core.hooksPath", check=False), "")

    def git(self, repo, *args, check=True):
        result = subprocess.run(["git", "-C", str(repo), *args], check=check,
                                capture_output=True, text=True)
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
