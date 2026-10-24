"""Exercise the POSIX version hook in throwaway Git repositories."""
from datetime import date
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks/pre-commit"


class VersionHookTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = (Path(self.temp.name) / "fixture").resolve()
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / ".githooks").mkdir()
        shutil.copy2(HOOK, self.repo / ".githooks/pre-commit")
        (self.repo / "VERSION").write_text("version: 1.4.7\ndate: 2000-01-01\n")
        (self.repo / "README.md").write_text(
            "# Fixture\n\n<!-- version -->\n**Version 1.4.7** (2000-01-01)\n<!-- /version -->\n"
        )
        (self.repo / "source.txt").write_text("first\n")
        self.git("add", ".")
        self.git("-c", "core.hooksPath=.githooks", "commit", "-m", "baseline")
        self.git("config", "core.hooksPath", ".githooks")

    def git(self, *args, check=True, env=None):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=check,
                              capture_output=True, text=True, env=env)

    def commit_change(self, message, bump=None):
        self.git("add", "source.txt")
        env = None
        if bump:
            import os
            env = os.environ.copy()
            env["FISKWISE_VERSION_BUMP"] = bump
        return self.git("commit", "-m", message, env=env)

    def add_description_baseline(self, text):
        (self.repo / "DESCRIPTION").write_text(text)
        self.git("add", "DESCRIPTION")
        # Establish a pre-existing package file without invoking the hook.
        self.git("-c", "core.hooksPath=/dev/null", "commit", "-m", "add package metadata")

    def test_ordinary_commit_increments_patch_and_stamps_readme(self):
        (self.repo / "source.txt").write_text("second\n")
        self.commit_change("ordinary")
        version = (self.repo / "VERSION").read_text()
        readme = (self.repo / "README.md").read_text()
        self.assertRegex(version, r"^version: 1\.4\.8\ndate: \d{4}-\d{2}-\d{2}\n$")
        self.assertIn("**Version 1.4.8**", readme)
        self.assertNotIn("2000-01-01", readme)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_stamping_preserves_existing_file_permissions(self):
        for name in ("VERSION", "README.md"):
            (self.repo / name).chmod(0o755)
        self.git("add", "VERSION", "README.md")
        (self.repo / "source.txt").write_text("permission check\n")
        self.commit_change("preserve modes")
        for name in ("VERSION", "README.md"):
            self.assertEqual((self.repo / name).stat().st_mode & 0o777, 0o755)

    def test_explicit_minor_and_major_bumps(self):
        for bump, expected in (("minor", "1.5.0"), ("major", "2.0.0")):
            with self.subTest(bump=bump):
                # Use a separate fixture per bump so each starts from 1.4.7.
                repo = VersionHookTest()
                repo.setUp()
                try:
                    (repo.repo / "source.txt").write_text("release\n")
                    result = repo.commit_change("explicit release", bump=bump)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertRegex((repo.repo / "VERSION").read_text(),
                                     rf"^version: {expected.replace('.', r'\.') }\ndate: \d{{4}}-\d{{2}}-\d{{2}}\n$")
                finally:
                    repo.doCleanups()

    def test_minor_bump_without_explicit_flag_is_rejected(self):
        (self.repo / "VERSION").write_text("version: 1.5.0\ndate: 2000-01-01\n")
        self.git("add", "VERSION", "source.txt")
        result = self.git("commit", "-m", "unrequested minor release", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / "VERSION").read_text(), "version: 1.5.0\ndate: 2000-01-01\n")
        self.assertIn("version: 1.4.7", self.git("show", "HEAD:VERSION").stdout)

    def test_manually_preincremented_expected_patch_is_accepted_once(self):
        (self.repo / "VERSION").write_text("version: 1.4.8\ndate: 2000-01-01\n")
        (self.repo / "source.txt").write_text("preincremented\n")
        self.git("add", "VERSION", "source.txt")
        result = self.git("commit", "-m", "preincremented patch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex((self.repo / "VERSION").read_text(),
                         r"^version: 1\.4\.8\ndate: \d{4}-\d{2}-\d{2}\n$")

    def test_first_commit_retains_initial_version(self):
        first = (Path(self.temp.name) / "first-commit").resolve()
        first.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(first)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(first), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(first), "config", "user.email", "test@example.invalid"], check=True)
        (first / ".githooks").mkdir()
        shutil.copy2(HOOK, first / ".githooks/pre-commit")
        (first / "VERSION").write_text("version: 0.7.3\ndate: 2000-01-01\n")
        (first / "source.txt").write_text("first\n")
        subprocess.run(["git", "-C", str(first), "add", "."], check=True)
        result = subprocess.run(["git", "-C", str(first), "-c", "core.hooksPath=.githooks",
                                 "commit", "-m", "first"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex((first / "VERSION").read_text(),
                         r"^version: 0\.7\.3\ndate: \d{4}-\d{2}-\d{2}\n$")

    def test_unstaged_version_blocks_before_hook_mutation(self):
        (self.repo / "source.txt").write_text("staged source\n")
        self.git("add", "source.txt")
        before_version = (self.repo / "VERSION").read_bytes()
        before_readme = (self.repo / "README.md").read_bytes()
        (self.repo / "VERSION").write_text("version: 8.8.8\ndate: 2000-01-01\n")
        result = self.git("commit", "-m", "reject unstaged version", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / "VERSION").read_text(), "version: 8.8.8\ndate: 2000-01-01\n")
        self.assertEqual((self.repo / "README.md").read_bytes(), before_readme)
        self.assertIn(" M VERSION", self.git("status", "--porcelain").stdout)
        self.assertIn("version: 1.4.7", self.git("show", "HEAD:VERSION").stdout)
        self.assertNotEqual(before_version, (self.repo / "VERSION").read_bytes())

    def test_unstaged_description_blocks_without_staging_its_change(self):
        self.add_description_baseline(
            "Package: fixture\nVersion: 1.4.7\nTitle: Original\n"
            "Description: Example package.\nLicense: MIT\n"
        )
        original = (self.repo / "DESCRIPTION").read_text()
        (self.repo / "DESCRIPTION").write_text(original.replace("Title: Original", "Title: User edit"))
        (self.repo / "source.txt").write_text("staged source\n")
        self.git("add", "source.txt")
        result = self.git("commit", "-m", "reject unstaged description", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / "DESCRIPTION").read_text(),
                         original.replace("Title: Original", "Title: User edit"))
        self.assertIn(" M DESCRIPTION", self.git("status", "--porcelain").stdout)
        self.assertEqual(self.git("show", "HEAD:DESCRIPTION").stdout, original)

    def test_description_priority_preservation_date_insertion_and_crlf(self):
        description = (
            "Package: fixture\r\nVersion: 2.3.9\r\nTitle: Fixture package\r\n"
            "Authors@R: person(\"A\", \"User\", role = c(\"aut\", \"cre\"))\r\n"
            "Description: First line\r\n    continued line\r\nLicense: MIT\r\n"
        )
        self.add_description_baseline(description)
        (self.repo / "source.txt").write_text("package release\n")
        self.commit_change("package patch")
        result = (self.repo / "DESCRIPTION").read_text()
        self.assertIn("Version: 2.3.10\n", result)
        self.assertIn(f"Date: {date.today().isoformat()}\n", result)
        self.assertIn("Title: Fixture package\n", result)
        self.assertIn("Authors@R: person(\"A\", \"User\", role = c(\"aut\", \"cre\"))\n", result)
        self.assertIn("Description: First line\n    continued line\n", result)
        self.assertIn("License: MIT\n", result)
        self.assertNotIn("Version: 1.4.8", result)

    def test_repeated_hook_runs_are_idempotent(self):
        (self.repo / "source.txt").write_text("twice\n")
        self.git("add", "source.txt")
        hook = self.repo / ".githooks/pre-commit"
        for _ in range(2):
            result = subprocess.run([str(hook)], cwd=self.repo, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        version_after_hook = (self.repo / "VERSION").read_text()
        self.assertRegex(version_after_hook, r"^version: 1\.4\.8\ndate: \d{4}-\d{2}-\d{2}\n$")
        result = self.git("commit", "-m", "idempotent")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "VERSION").read_text(), version_after_hook)

    def test_merge_and_rebase_replay_markers_skip_stamping(self):
        before = (self.repo / "VERSION").read_text()
        git_dir = Path(self.git("rev-parse", "--git-dir").stdout.strip())
        if not git_dir.is_absolute():
            git_dir = self.repo / git_dir
        for marker in [git_dir / "MERGE_HEAD", git_dir / "rebase-merge", git_dir / "rebase-apply"]:
            if marker.name == "MERGE_HEAD":
                marker.write_text(self.git("rev-parse", "HEAD").stdout)
            else:
                marker.mkdir()
            result = subprocess.run([str(self.repo / ".githooks/pre-commit")], cwd=self.repo,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((self.repo / "VERSION").read_text(), before)
            if marker.is_dir():
                marker.rmdir()
            else:
                marker.unlink()

    def test_unstaged_readme_edit_is_not_swept_into_commit(self):
        original = (self.repo / "README.md").read_text()
        changed_readme = original + "\nUnstaged user note.\n"
        (self.repo / "README.md").write_text(changed_readme)
        (self.repo / "source.txt").write_text("source changed\n")
        self.commit_change("leave README edit unstaged")
        self.assertEqual((self.repo / "README.md").read_text(), changed_readme)
        self.assertRegex((self.repo / "VERSION").read_text(),
                         r"^version: 1\.4\.8\ndate: \d{4}-\d{2}-\d{2}\n$")
        self.assertIn(" M README.md", self.git("status", "--porcelain").stdout)
        self.assertNotIn("**Version 1.4.8**", self.git("show", "HEAD:README.md").stdout)


if __name__ == "__main__":
    unittest.main()
