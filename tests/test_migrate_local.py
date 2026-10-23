"""Exercise filesystem behavior using a synthetic home and workspace."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('migration', ROOT / 'scripts/migrate_local.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class LocalMigrationTest(unittest.TestCase):
    def test_preserves_settings_retires_only_owned_and_repeats_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace, home, backup = root / 'packs', root / 'home', root / 'backup'
            for pack in ['BAIT', 'wise-writing', 'index-wise', 'spict-wise', 'wise-presentations']:
                p = workspace / pack
                p.mkdir(parents=True)
                (p / 'AGENTS.md').write_text('pack')
                skills = p / ('.agents/skills' if pack == 'wise-presentations' else 'skills')
                skill = skills / (pack + '-skill')
                skill.mkdir(parents=True)
                (skill / 'SKILL.md').write_text('canonical')
            (workspace / 'BAIT/knowledge').mkdir()
            (home / '.bait').mkdir(parents=True)
            (home / '.bait/config.json').write_text(json.dumps({'bait_path':'old', 'bes_db_path':'keep.db', 'privacy_onboarded_at':'keep', 'skills_synced_to':['~/.claude/skills','~/.codex/skills']}))
            (home / '.academic-writing').mkdir()
            (home / '.academic-writing/config.json').write_text('{"custom":"preserve"}')
            oldskill = home / '.codex/skills/BAIT-skill'
            oldskill.mkdir(parents=True)
            (oldskill / 'SKILL.md').write_text('customized legacy copy')
            unrelated = home / '.codex/skills/unrelated'
            unrelated.mkdir()
            (unrelated / 'SKILL.md').write_text('untouched')
            (home / '.claude').mkdir()
            (home / '.claude/CLAUDE.md').write_text('Original user instructions\n')
            (home / '.codex/config.toml').write_text(f'[projects."{workspace / "academic-writing"}"]\ntrust_level = "trusted"\n')
            dry = mod.Migration(workspace, home, backup, False)
            self.assertTrue(dry.run())
            self.assertTrue(oldskill.exists())
            self.assertFalse(backup.exists())
            mod.Migration(workspace, home, backup, True).run()
            bait = json.loads((home / '.bait/config.json').read_text())
            self.assertEqual(bait['bes_db_path'], 'keep.db')
            self.assertEqual(bait['privacy_onboarded_at'], 'keep')
            self.assertEqual(bait['skills_synced_to'], ['~/.claude/skills', '~/.agents/skills'])
            self.assertEqual(bait['bait_path'], str(workspace / 'BAIT'))
            self.assertEqual(json.loads((home / '.wise-writing/config.json').read_text())['custom'], 'preserve')
            self.assertTrue((home / '.agents/skills/BAIT-skill').is_symlink())
            self.assertFalse(oldskill.exists())
            self.assertEqual((backup / '.codex/skills/BAIT-skill/SKILL.md').read_text(), 'customized legacy copy')
            self.assertEqual((unrelated / 'SKILL.md').read_text(), 'untouched')
            self.assertTrue((home / '.claude/knowledge').is_dir())
            self.assertTrue((home / '.agents/knowledge').is_dir())
            self.assertIn('Original user instructions', (home / '.claude/CLAUDE.md').read_text())
            self.assertEqual(mod.Migration(workspace, home, root / 'backup2', True).run(), [])

if __name__ == '__main__':
    unittest.main()
