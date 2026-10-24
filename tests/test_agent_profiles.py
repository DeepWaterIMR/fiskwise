"""Isolated coverage for native agent skill and instruction registrations."""
from pathlib import Path
import importlib.util
import json
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agent_lifecycle", ROOT / "scripts/lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)
Manager = lifecycle.Manager
PROFILES = lifecycle.PROFILES
canonical = lifecycle.canonical


class AgentProfilesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.home = (base / "home").resolve()
        self.workspace = (base / "packs").resolve()
        self.root = self.workspace / "fiskwise"
        self.home.mkdir()
        self.root.mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("fixture root\n")
        (self.root / "packages.json").write_text(json.dumps([
            {"name": "fiskwise", "kind": "knowledge", "status": "available",
             "core": True, "dependencies": [], "skill_roots": ["skills"]}
        ]))
        # Copy just the canonical skill files into the synthetic checkout. This
        # keeps installs hermetic while letting metadata changes be tested.
        for name in ("fiskwise-install", "fiskwise-update", "fiskwise-uninstall", "fiskwise-workflow"):
            source = ROOT / "skills" / name / "SKILL.md"
            target = self.root / "skills" / name / "SKILL.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text())
        self.manager = self.new_manager()

    def new_manager(self):
        return Manager(workspace=self.workspace, home=self.home, root=self.root)

    def test_each_profile_installs_at_its_documented_target(self):
        for profile in PROFILES:
            with self.subTest(profile=profile):
                home = self.home / profile
                home.mkdir()
                manager = Manager(workspace=self.workspace, home=home, root=self.root)
                state = manager.install(selected=[profile], allow_clone=False)
                skill_root = home / PROFILES[profile]["skills"]
                self.assertTrue(skill_root.is_dir())
                for name in ("fiskwise-install", "fiskwise-update", "fiskwise-uninstall", "fiskwise-workflow"):
                    self.assertTrue((skill_root / name / "SKILL.md").is_file(), name)
                instruction = PROFILES[profile]["instructions"]
                if instruction:
                    self.assertTrue((home / instruction).is_file(), instruction)
                else:
                    self.assertFalse(any(r["kind"] == "block" for r in state["registrations"]))
                registered_roots = {Path(r["path"]).parent for r in state["registrations"] if r["kind"] == "skill"}
                self.assertEqual(registered_roots, {skill_root})

    def test_install_metadata_covers_short_lifecycle_requests(self):
        expected = {
            "fiskwise-install": ("install", "https://github.com/DeepWaterIMR/fiskwise"),
            "fiskwise-update": ("update", "Fiskwise"),
            "fiskwise-uninstall": ("uninstall", "Fiskwise"),
        }
        for skill, fragments in expected.items():
            with self.subTest(skill=skill):
                text = (self.root / "skills" / skill / "SKILL.md").read_text()
                frontmatter = text.split("---", 2)[1]
                description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
                self.assertIsNotNone(description, skill)
                metadata = description.group(1).lower()
                for fragment in fragments:
                    self.assertIn(fragment.lower(), metadata)

    def test_shared_targets_are_deduplicated_and_mistral_alias_is_native(self):
        manager = self.new_manager()
        selected = ["codex", "vibe", "gemini", "cursor", "mistral"]
        agents = manager.agents(selected)
        self.assertEqual(agents.count("vibe"), 1)
        self.assertEqual(canonical("mistral"), "vibe")
        targets = manager.skill_targets(agents)
        self.assertEqual(len(targets), len(set(targets)))
        self.assertEqual(targets.count(self.home / ".agents/skills"), 1)
        self.assertEqual(manager.instruction_targets(agents).count(self.home / ".gemini/GEMINI.md"), 1)

    def test_autodetection_and_unknown_home_fall_back_to_portable(self):
        self.assertEqual(self.manager.agents(), ["portable"])
        (self.home / ".vibe").mkdir()
        self.assertEqual(self.manager.agents(), ["vibe"])
        (self.home / ".cursor").mkdir()
        self.assertEqual(set(self.manager.agents()), {"vibe", "cursor"})

    def test_copy_fallback_and_update_refreshes_only_unmodified_registration(self):
        state = self.manager.install(selected=["cursor"], allow_clone=False, prefer_copy=True)
        target = self.home / ".agents/skills/fiskwise-update"
        self.assertTrue(target.is_dir())
        self.assertFalse(target.is_symlink())
        self.assertTrue(any(r["path"] == str(target) for r in state["registrations"]))

        source = self.root / "skills/fiskwise-update/SKILL.md"
        source.write_text(source.read_text().replace("Update installed Fiskwise software", "Refreshed update procedure"))
        results = self.manager.update(apply=True)
        self.assertIn("Refreshed update procedure", (target / "SKILL.md").read_text())
        self.assertFalse(any(r.get("status") == "remote-check-unavailable" for r in results))

        (target / "SKILL.md").write_text("user edit\n")
        source.write_text(source.read_text().replace("Refreshed update procedure", "Second refresh"))
        results = self.manager.update(apply=True)
        self.assertEqual((target / "SKILL.md").read_text(), "user edit\n")
        self.assertTrue(any(r.get("status") == "modified-registration-preserved" for r in results))

    def test_uninstall_removes_created_profile_entries_but_keeps_safety_roots(self):
        selected = list(PROFILES)
        self.manager.install(selected=selected, allow_clone=False)
        managed = [Path(r["path"]) for r in self.manager.state["registrations"] if r["kind"] == "skill"]
        instruction_files = [Path(r["path"]) for r in self.manager.state["registrations"] if r["kind"] == "block"]
        unrelated = self.home / ".agents/skills/unrelated-skill"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("leave me\n")
        plan = self.manager.removal_plan()
        self.assertEqual({Path(r["path"]) for r in plan["remove"]}, set(managed + instruction_files))
        self.manager.uninstall(plan["confirmation"])
        self.assertFalse(self.manager.state["enabled"])
        self.assertTrue(self.root.is_dir())
        self.assertTrue(unrelated.is_dir())
        self.assertEqual((unrelated / "SKILL.md").read_text(), "leave me\n")
        self.assertTrue(all(not path.exists() and not path.is_symlink() for path in managed))
        self.assertTrue(all("<!-- fiskwise-managed:start -->" not in path.read_text() for path in instruction_files))

    def test_arbitrary_registry_roots_under_new_profiles_are_refused(self):
        invalid = self.home / ".antigravity"
        invalid.mkdir()
        self.manager.state["registrations"] = [{
            "path": str(invalid), "owner": "fiskwise", "kind": "skill",
            "origin": "created", "installed": lifecycle.fingerprint(invalid),
        }]
        plan = self.manager.removal_plan()
        self.assertFalse(plan["remove"])
        self.assertEqual(plan["preserve"][0]["path"], str(invalid))
        self.assertTrue(invalid.is_dir())


if __name__ == "__main__":
    unittest.main()
