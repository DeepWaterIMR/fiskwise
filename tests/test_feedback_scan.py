"""Check the deterministic sanitisation floor for agent-drafted reports."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import feedback_scan  # noqa: E402


def rules(text):
    return {f.rule for f in feedback_scan.scan_text(text)}


class FeedbackScanTest(unittest.TestCase):
    def test_template_is_clean(self):
        template = ROOT / "skills/fiskwise-feedback/issue-template.md"
        self.assertEqual(feedback_scan.scan_text(template.read_text()), [])

    def test_generic_report_is_clean(self):
        text = (
            "The scaffold sourced `R/helpers.R` by a relative path, so rendering from\n"
            "`reports/` failed. Use `here::here()`. Version 1.2.3 (2026-11-04).\n"
            "Contact: someone@example.invalid\n"
        )
        self.assertEqual(rules(text), set())

    def test_personal_paths(self):
        self.assertIn("personal-path", rules("Error in /Users/jdoe/project/x.R"))
        self.assertIn("personal-path", rules(r"C:\Users\jdoe\Documents"))
        self.assertIn("personal-path", rules("/home/jdoe/.fiskwise"))

    def test_credentials(self):
        self.assertIn("credential", rules("ghp_" + "a" * 36))
        self.assertIn("credential", rules("key sk-ant-" + "x" * 30))
        self.assertIn("credential-assignment", rules("password = hunter2secret"))
        self.assertNotIn("credential-assignment", rules("token: <your token>"))

    def test_email_and_hosts(self):
        self.assertIn("email", rules("Mail me at person@institute.no"))
        self.assertNotIn("email", rules("noreply@anthropic.com"))
        self.assertIn("internal-host", rules("db at server01.imr.no"))
        self.assertIn("ip-address", rules("connect 10.1.2.3"))
        self.assertNotIn("ip-address", rules("localhost 127.0.0.1"))

    def test_coordinates(self):
        self.assertIn("coordinates", rules("station at 70.12345, 19.98765"))
        self.assertIn("coordinates", rules("70° 12' N"))
        self.assertNotIn("coordinates", rules("version 1.2.3"))

    def test_data_tables(self):
        table = "| a | b | c |\n|---|---|---|\n" + "| 1 | 2 | 3 |\n" * 12
        self.assertIn("data-table", rules(table))
        short = "| a | b |\n|---|---|\n| 1 | 2 |\n"
        self.assertNotIn("data-table", rules(short))
        csv = "\n".join(f"{i},{i * 2.5},{i + 7}" for i in range(10))
        self.assertIn("data-rows", rules(csv))
        self.assertIn("tibble-print", rules("# A tibble: 120 x 6"))

    def test_masks_secret_in_output(self):
        secret = "ghp_" + "b" * 36
        finding = feedback_scan.scan_text(secret)[0]
        self.assertNotIn(secret, str(finding))

    def test_cli_exit_codes(self):
        script = ROOT / "scripts/feedback_scan.py"
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.md"
            dirty = Path(tmp) / "dirty.md"
            clean.write_text("A generic description.\n")
            dirty.write_text("See /Users/jdoe/x\n")
            run = lambda p: subprocess.run([sys.executable, str(script), str(p)],
                                           capture_output=True, text=True).returncode
            self.assertEqual(run(clean), 0)
            self.assertEqual(run(dirty), 1)
            self.assertEqual(run(Path(tmp) / "missing.md"), 2)


if __name__ == "__main__":
    unittest.main()
