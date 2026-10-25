"""Synthetic, isolated coverage for the local lifecycle manager.

These tests use temporary pack checkouts and homes. They never clone a remote,
install software, or inspect real user data.
"""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lifecycle", ROOT / "scripts/lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)
Manager = lifecycle.Manager


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = (self.base / "home").resolve()
        self.workspace = (self.base / "packs").resolve()
        self.source_root = self.workspace / "fiskwise"
        self.home.mkdir()
        self.source_root.mkdir(parents=True)
        (self.source_root / "AGENTS.md").write_text("fixture root\n")
        self.pack("wise-writing", core=True)
        self.pack("BAIT", dependencies=["wise-writing"])
        (self.workspace / "BAIT/knowledge").mkdir()
        inventory = [
            {"name": "wise-writing", "kind": "knowledge", "status": "available",
             "core": True, "dependencies": [], "skill_roots": ["skills"]},
            {"name": "BAIT", "kind": "knowledge", "status": "available",
             "core": False, "dependencies": ["wise-writing"], "skill_roots": ["skills"]},
        ]
        (self.source_root / "packages.json").write_text(json.dumps(inventory))
        self.manager = self.new_manager()

    def pack(self, name, core=False, dependencies=None):
        path = self.workspace / name
        skill = path / "skills" / ("writing-skill" if name == "wise-writing" else "biotic-skill")
        skill.mkdir(parents=True)
        (path / "AGENTS.md").write_text(f"{name} fixture\n")
        skill.joinpath("SKILL.md").write_text(
            f"---\nname: {skill.name}\ndescription: fixture\n---\n\nFixture instructions.\n"
        )
        return path

    def new_manager(self):
        return Manager(workspace=self.workspace, home=self.home, root=self.source_root)

    def git_repo(self, path, branch="main"):
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-b", branch, str(path)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.invalid"], check=True)
        (path / "tracked.txt").write_text("initial\n")
        subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(path), "commit", "-m", "initial"], check=True, capture_output=True)

    def attach_local_bare_remote(self, path, bare):
        subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", str(bare)], check=True)
        subprocess.run(["git", "-C", str(path), "push", "-u", "origin", "main"], check=True, capture_output=True)

    def advance_remote(self, bare, work):
        subprocess.run(["git", "clone", str(bare), str(work)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(work), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(work), "config", "user.email", "test@example.invalid"], check=True)
        (work / "remote.txt").write_text("remote advance\n")
        subprocess.run(["git", "-C", str(work), "add", "remote.txt"], check=True)
        subprocess.run(["git", "-C", str(work), "commit", "-m", "remote advance"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(work), "push", "origin", "main"], check=True, capture_output=True)

    def update_status(self, name, path, home):
        home.mkdir(parents=True, exist_ok=True)
        manager = Manager(workspace=self.workspace, home=home, root=self.source_root)
        manager.state["components"] = {"wise-writing": {"path": str(path)}}
        manager.save()
        result = manager.update(apply=True)
        return next(item["status"] for item in result if item["component"] == "wise-writing")

    def test_fresh_install_is_filesystem_only_and_repeatable(self):
        plan = self.manager.install_plan()
        self.assertEqual(plan["components"], ["fiskwise", "wise-writing"])
        self.assertIn("separate", plan["note"])
        self.assertIsNone(plan["r_packages"])
        self.manager.set_consent(False)
        state = self.manager.install(selected=["codex"], allow_clone=False)
        self.assertFalse(state["consent"]["r_packages"])
        self.assertEqual(set(state["components"]), {"fiskwise", "wise-writing"})
        installed = self.home / ".agents/skills/writing-skill"
        self.assertTrue(installed.is_symlink())
        self.assertEqual(installed.resolve(), (self.workspace / "wise-writing/skills/writing-skill").resolve())
        self.assertFalse((self.home / ".codex/skills").exists())
        registrations = list(state["registrations"])

        repeated = self.new_manager().install(selected=["codex"], allow_clone=False)
        self.assertEqual(repeated["registrations"], registrations)
        self.assertFalse(self.new_manager().install_plan(selected=["codex"])["actions"])

    def test_adopt_existing_checkout_and_copy_fallback(self):
        state = self.manager.install(include=["BAIT"], selected=["codex"], allow_clone=False, adopt=True,
                                     prefer_copy=True)
        self.assertEqual(set(state["components"]), {"fiskwise", "wise-writing", "BAIT"})
        self.assertEqual(state["components"]["BAIT"]["origin"], "adopted")
        copy = self.home / ".agents/skills/biotic-skill"
        self.assertTrue(copy.is_dir())
        self.assertFalse(copy.is_symlink())
        self.assertEqual((copy / "SKILL.md").read_text(),
                         (self.workspace / "BAIT/skills/biotic-skill/SKILL.md").read_text())

    def test_uninstall_refusal_modified_content_and_restore(self):
        target = self.home / ".agents/skills/writing-skill"
        target.parent.mkdir(parents=True)
        target.mkdir()
        (target / "personal.txt").write_text("preserve me\n")
        unrelated = self.home / ".agents/skills/unrelated"
        unrelated.mkdir()
        (unrelated / "SKILL.md").write_text("unrelated\n")
        self.manager.install(selected=["codex"], allow_clone=False)
        plan = self.manager.removal_plan(include_adopted=True)
        with self.assertRaisesRegex(ValueError, "confirmation"):
            self.manager.uninstall("wrong")
        self.assertTrue(target.is_symlink())
        self.assertTrue(unrelated.exists())
        self.manager.uninstall(plan["confirmation"], include_adopted=True)
        self.assertTrue(target.is_dir())
        self.assertFalse(target.is_symlink())
        self.assertEqual((target / "personal.txt").read_text(), "preserve me\n")
        self.assertEqual((unrelated / "SKILL.md").read_text(), "unrelated\n")

    def test_modified_owned_registration_and_user_block_are_preserved(self):
        self.manager.install(selected=["codex"], allow_clone=False)
        target = self.home / ".agents/skills/writing-skill"
        target.unlink()
        target.mkdir()
        (target / "SKILL.md").write_text("my changes\n")
        instructions = self.home / ".codex/AGENTS.md"
        text = instructions.read_text()
        instructions.write_text("user preface\n" + text + "user suffix\n")
        plan = self.manager.removal_plan()
        preserved = {item["path"] for item in plan["preserve"]}
        self.assertIn(str(target), preserved)
        self.assertNotIn(str(instructions), preserved)
        with self.assertRaisesRegex(ValueError, "confirmation"):
            self.manager.uninstall("stale-plan")
        self.assertEqual((target / "SKILL.md").read_text(), "my changes\n")
        self.assertTrue(instructions.read_text().startswith("user preface\n"))
        self.manager.uninstall(plan["confirmation"])
        self.assertIn("user preface", instructions.read_text())
        self.assertIn("user suffix", instructions.read_text())
        self.assertNotIn("<!-- fiskwise-managed:start -->", instructions.read_text())

    def test_adopted_skill_is_preserved_by_default_and_restorable_when_selected(self):
        target = self.home / ".agents/skills/writing-skill"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("preexisting customized skill\n")
        self.manager.install(selected=["codex"], allow_clone=False)
        plan = self.manager.removal_plan()
        self.assertTrue(any(item["path"] == str(target) for item in plan["preserve"]))
        self.manager.uninstall(plan["confirmation"])
        self.assertTrue(target.is_symlink())
        self.assertEqual((target / "SKILL.md").read_text(),
                         (self.workspace / "wise-writing/skills/writing-skill/SKILL.md").read_text())
        registration = next(r for r in self.manager.state["registrations"] if r["path"] == str(target))
        backup = Path(registration["backup"])
        self.assertEqual((backup / "SKILL.md").read_text(), "preexisting customized skill\n")

        detach = self.manager.removal_plan(include_adopted=True)
        self.assertTrue(any(item["path"] == str(target) for item in detach["remove"]))
        self.manager.uninstall(detach["confirmation"], include_adopted=True)
        self.assertTrue(target.is_dir())
        self.assertFalse(target.is_symlink())
        self.assertEqual((target / "SKILL.md").read_text(), "preexisting customized skill\n")

    def test_update_preserves_dirty_and_pinned_checkouts_without_remote_access(self):
        writing = self.workspace / "wise-writing"
        bait = self.workspace / "BAIT"
        self.git_repo(writing)
        self.git_repo(bait)
        (writing / "tracked.txt").write_text("local edit\n")
        subprocess.run(["git", "-C", str(bait), "checkout", "--detach", "HEAD"], check=True, capture_output=True)
        self.manager.state["components"] = {
            "fiskwise": {"path": str(self.source_root)},
            "wise-writing": {"path": str(writing)},
            "BAIT": {"path": str(bait)},
        }
        self.manager.save()
        with patch.object(lifecycle, "git", wraps=lifecycle.git) as git_mock:
            results = self.manager.update(apply=True)
        statuses = {item["component"]: item["status"] for item in results}
        self.assertEqual(statuses["wise-writing"], "local-changes-preserved")
        self.assertEqual(statuses["BAIT"], "pinned-preserved")
        self.assertNotIn("fetch", [call.args[1] for call in git_mock.call_args_list if len(call.args) > 1])

    def test_offline_fetch_is_reported_without_changing_checkout(self):
        writing = self.workspace / "wise-writing"
        self.git_repo(writing)
        self.manager.state["components"] = {"fiskwise": {"path": str(self.source_root)},
                                             "wise-writing": {"path": str(writing)}}
        self.manager.save()
        original = lifecycle.git

        def offline_git(path, *args):
            if args and args[0] == "fetch":
                raise subprocess.CalledProcessError(128, ["git", "fetch"], stderr="offline")
            return original(path, *args)

        with patch.object(lifecycle, "git", side_effect=offline_git):
            results = self.manager.update(apply=True)
        status = next(item["status"] for item in results if item["component"] == "wise-writing")
        self.assertEqual(status, "remote-check-unavailable")
        self.assertEqual(subprocess.check_output(["git", "-C", str(writing), "status", "--porcelain"], text=True), "")

    def test_local_bare_remote_current_fast_forward_and_divergence(self):
        cases = ("current", "fast-forward", "diverged")
        for case in cases:
            with self.subTest(case=case):
                root = self.base / case
                writing, bare = root / "wise-writing", root / "origin.git"
                self.git_repo(writing)
                self.attach_local_bare_remote(writing, bare)
                before = subprocess.check_output(["git", "-C", str(writing), "rev-parse", "HEAD"], text=True).strip()
                if case == "fast-forward":
                    self.advance_remote(bare, root / "contributor")
                    expected = "updated"
                elif case == "diverged":
                    (writing / "local.txt").write_text("local commit\n")
                    subprocess.run(["git", "-C", str(writing), "add", "local.txt"], check=True)
                    subprocess.run(["git", "-C", str(writing), "commit", "-m", "local divergence"],
                                   check=True, capture_output=True)
                    local_head = subprocess.check_output(["git", "-C", str(writing), "rev-parse", "HEAD"], text=True).strip()
                    self.advance_remote(bare, root / "contributor")
                    expected = "ahead-or-diverged-preserved"
                else:
                    expected = "current"
                status = self.update_status(case, writing, root / "home")
                self.assertEqual(status, expected)
                if case == "current":
                    self.assertEqual(subprocess.check_output(["git", "-C", str(writing), "rev-parse", "HEAD"], text=True).strip(), before)
                elif case == "fast-forward":
                    self.assertTrue((writing / "remote.txt").exists())
                else:
                    self.assertEqual(subprocess.check_output(["git", "-C", str(writing), "rev-parse", "HEAD"], text=True).strip(), local_head)
                    self.assertFalse((writing / "remote.txt").exists())

    def test_interrupted_link_registration_can_resume_without_clobbering_partial_copy(self):
        source = self.workspace / "wise-writing/skills/writing-skill"
        target = self.home / ".agents/skills/writing-skill"
        with patch.object(lifecycle.Path, "symlink_to", side_effect=OSError("simulated link failure")), \
                patch.object(lifecycle.shutil, "copytree", side_effect=OSError("simulated copy failure")):
            with self.assertRaisesRegex(OSError, "simulated copy failure"):
                self.manager.register_link(target, source, "wise-writing")
        pending = self.new_manager()
        record = next(r for r in pending.state["registrations"] if r["path"] == str(target))
        self.assertTrue(record["pending"])
        self.assertFalse(target.exists())
        pending.register_link(target, source, "wise-writing")
        self.assertTrue(target.is_symlink())
        self.assertFalse(next(r for r in pending.state["registrations"] if r["path"] == str(target))["pending"])

        partial = self.home / ".agents/skills/partial-skill"
        partial_source = self.workspace / "wise-writing/skills/writing-skill"
        original_copytree = lifecycle.shutil.copytree

        def partial_then_fail(src, dst, **kwargs):
            Path(dst).mkdir(parents=True)
            (Path(dst) / "partial.txt").write_text("incomplete\n")
            raise OSError("interrupted copy")

        with patch.object(lifecycle.Path, "symlink_to", side_effect=OSError("simulated link failure")), \
                patch.object(lifecycle.shutil, "copytree", side_effect=partial_then_fail):
            with self.assertRaisesRegex(OSError, "interrupted copy"):
                pending.register_link(partial, partial_source, "wise-writing")
        with self.assertRaisesRegex(ValueError, "Modified registration preserved"):
            self.new_manager().register_link(partial, partial_source, "wise-writing")
        self.assertEqual((partial / "partial.txt").read_text(), "incomplete\n")

    def test_copy_refresh_refuses_modified_managed_copy(self):
        self.manager.install(selected=["codex"], allow_clone=False, prefer_copy=True)
        target = self.home / ".agents/skills/writing-skill"
        self.assertFalse(target.is_symlink())
        (target / "SKILL.md").write_text("local customization\n")
        results = self.manager.update(apply=True)
        self.assertTrue(any(item["status"] == "modified-registration-preserved" for item in results))
        self.assertEqual((target / "SKILL.md").read_text(), "local customization\n")

    def test_update_adds_new_skills_refreshes_auxiliary_copies_and_preserves_collisions(self):
        self.manager.install(include=['BAIT'], selected=['cline'], allow_clone=False, prefer_copy=True)
        skill = self.workspace / 'wise-writing/skills/new-skill'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('---\nname: new-skill\ndescription: new\n---\n')
        knowledge = self.workspace / 'BAIT/knowledge/new.md'
        knowledge.write_text('updated knowledge')
        results = self.manager.update(apply=True)
        target = self.home / '.cline/skills/new-skill'
        self.assertEqual((target / 'SKILL.md').read_text(), (skill / 'SKILL.md').read_text())
        self.assertFalse(target.is_symlink())
        self.assertEqual((self.home / '.agents/knowledge/new.md').read_text(), 'updated knowledge')
        shutil.rmtree(skill)
        results = self.manager.update(apply=True)
        self.assertTrue(any(r['status'] == 'retired-registration-retained' and r['path'] == str(target) for r in results))
        self.assertTrue(target.exists())
        collision = self.workspace / 'wise-writing/skills/local-skill'
        collision.mkdir()
        (collision / 'SKILL.md').write_text('---\nname: local-skill\ndescription: new\n---\n')
        local = self.home / '.cline/skills/local-skill'
        local.mkdir()
        (local / 'SKILL.md').write_text('user skill')
        results = self.manager.update(apply=True)
        self.assertEqual((local / 'SKILL.md').read_text(), 'user skill')
        self.assertTrue(any(r['status'] == 'unmanaged-registration-preserved' for r in results))

    def test_duplicate_skill_ownership_is_rejected(self):
        duplicate = self.workspace / "BAIT/skills/writing-skill"
        duplicate.mkdir()
        (duplicate / "SKILL.md").write_text(
            "---\nname: writing-skill\ndescription: duplicate owner\n---\n\nDuplicate.\n"
        )
        with self.assertRaisesRegex(ValueError, "Duplicate canonical skill owner"):
            self.manager.sources(["wise-writing", "BAIT"])

    def test_uninstall_rejects_malicious_registry_path(self):
        outside = self.base / "outside" / "valuable"
        outside.mkdir(parents=True)
        (outside / "keep.txt").write_text("keep\n")
        self.manager.state["registrations"].append({
            "path": str(outside), "owner": "wise-writing", "kind": "skill", "origin": "created",
            "previous": None, "backup": None, "installed": lifecycle.fingerprint(outside),
        })
        self.manager.save()
        plan = self.manager.removal_plan()
        self.assertFalse(any(item["path"] == str(outside) for item in plan["remove"]))
        self.assertTrue(any(item["path"] == str(outside) and item["reason"] == "outside registered agent roots"
                            for item in plan["preserve"]))
        self.manager.uninstall(plan["confirmation"])
        self.assertEqual((outside / "keep.txt").read_text(), "keep\n")

    def test_registration_rejects_instruction_symlinks_and_parent_symlinks_outside_home(self):
        outside = self.base / "outside"
        outside.mkdir()
        external_file = outside / "AGENTS.md"
        external_file.write_text("user instructions\n")
        codex = self.home / ".codex"
        codex.mkdir()
        instruction_link = codex / "AGENTS.md"
        instruction_link.symlink_to(external_file)
        with self.assertRaisesRegex(ValueError, "Instruction file resolves outside"):
            self.manager.register_block(instruction_link)
        self.assertEqual(external_file.read_text(), "user instructions\n")

        agents_link = self.home / ".agents"
        agents_link.symlink_to(outside, target_is_directory=True)
        source = self.workspace / "wise-writing/skills/writing-skill"
        with self.assertRaisesRegex(ValueError, "Agent directory resolves outside"):
            self.manager.register_link(agents_link / "skills/writing-skill", source, "wise-writing")
        self.assertEqual(list(outside.iterdir()), [external_file])

    def test_missing_or_changed_adopted_backup_blocks_detachment(self):
        for damage in ("missing", "changed"):
            with self.subTest(damage=damage):
                home = (self.base / damage / "home").resolve()
                home.mkdir(parents=True)
                target = home / ".agents/skills/writing-skill"
                target.mkdir(parents=True)
                (target / "SKILL.md").write_text("original\n")
                manager = Manager(workspace=self.workspace, home=home, root=self.source_root)
                manager.install(selected=["codex"], allow_clone=False)
                record = next(r for r in manager.state["registrations"] if r["path"] == str(target))
                backup = Path(record["backup"])
                if damage == "missing":
                    shutil.rmtree(backup)
                else:
                    (backup / "SKILL.md").write_text("tampered backup\n")
                plan = manager.removal_plan(include_adopted=True)
                item = next(item for item in plan["preserve"] if item["path"] == str(target))
                self.assertEqual(item["reason"], "prior registration backup missing or changed")
                self.assertTrue(target.is_symlink())
                target.unlink()

    def test_database_provenance_requires_verified_creation_and_removal_is_quarantined(self):
        db = self.base / "synthetic.duckdb"
        with self.assertRaisesRegex(ValueError, "absent"):
            db.write_text("preexisting")
            self.manager.database_begin(db)
        db.unlink()
        token = self.manager.database_begin(db)
        with self.assertRaisesRegex(ValueError, "verified"):
            self.manager.database_plan(db)
        db.write_bytes(b"synthetic db")
        with self.assertRaisesRegex(ValueError, "verification"):
            self.manager.database_complete(token, verified=False)
        self.manager.database_complete(token, verified=True)
        plan = self.manager.database_plan(db)
        quarantine = self.base / "quarantine"
        with patch.object(Manager, "database_closed", return_value=False):
            with self.assertRaisesRegex(ValueError, "open"):
                self.manager.database_remove(db, plan["confirmation"], quarantine)
        self.assertTrue(db.exists())
        with patch.object(Manager, "database_closed", return_value=True):
            result = self.manager.database_remove(db, plan["confirmation"], quarantine)
        moved = Path(result["recoverable_at"])
        self.assertTrue(moved.exists())
        self.assertFalse(db.exists())
        self.assertEqual(result["associated_files"], "retained; not implicitly selected")

    def test_same_path_database_replacement_fails_identity_check(self):
        db = self.base / "identity.duckdb"
        token = self.manager.database_begin(db)
        db.write_bytes(b"first database")
        self.manager.database_complete(token, verified=True)
        replacement = self.base / "replacement.duckdb"
        replacement.write_bytes(b"new database data")
        os.replace(replacement, db)
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.manager.database_plan(db)

    def test_dangling_database_symlink_is_rejected(self):
        database = self.base / "real.duckdb"
        token = self.manager.database_begin(database)
        database.write_bytes(b"fixture")
        self.manager.database_complete(token, verified=True)
        alias = self.base / "alias.duckdb"
        alias.symlink_to(self.base / "missing.duckdb")
        with self.assertRaisesRegex(ValueError, "Symlink database paths"):
            self.manager.database_plan(alias)

    def test_revoked_consent_remains_false_across_manager_reload(self):
        self.manager.set_consent(True)
        self.manager.set_consent(False)
        fresh = self.new_manager()
        self.assertFalse(fresh.state["consent"]["r_packages"])
        self.assertFalse(fresh.install_plan()["r_packages"])


if __name__ == "__main__":
    unittest.main()
