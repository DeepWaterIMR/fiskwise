"""Exercise the version hook in throwaway Git repositories."""
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

    def git(self, *args, check=True):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=check,
                              capture_output=True, text=True)

    def commit_change(self, message):
        self.git("add", "source.txt")
        self.git("commit", "-m", message)

    def test_ordinary_commit_increments_patch_and_stamps_readme(self):
        (self.repo / "source.txt").write_text("second\n")
        self.commit_change("ordinary")
        version = (self.repo / "VERSION").read_text()
        readme = (self.repo / "README.md").read_text()
        self.assertRegex(version, r"^version: 1\.4\.8\ndate: \d{4}-\d{2}-\d{2}\n$")
        self.assertIn("**Version 1.4.8**", readme)
        self.assertNotIn("2000-01-01", readme)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_manual_version_bump_is_kept_and_date_refreshes(self):
        (self.repo / "VERSION").write_text("version: 2.0.0\ndate: 2000-01-01\n")
        (self.repo / "source.txt").write_text("manual bump\n")
        self.git("add", "VERSION", "source.txt")
        self.git("commit", "-m", "manual release")
        self.assertRegex((self.repo / "VERSION").read_text(),
                         r"^version: 2\.0\.0\ndate: \d{4}-\d{2}-\d{2}\n$")
        self.assertIn("**Version 2.0.0**", (self.repo / "README.md").read_text())

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
