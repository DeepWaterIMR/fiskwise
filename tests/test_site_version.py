"""The HTML/CSS build shares one immutable release stamp with the README."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SiteVersionTest(unittest.TestCase):
    def test_build_stamps_all_pages_without_modifying_version_or_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ['site', 'assets', 'scripts']:
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns('__pycache__'))
            for file in ['VERSION', 'packages.json', 'LICENSE', *[p.name for p in ROOT.glob('*.md')]]:
                shutil.copy2(ROOT / file, root / file)
            before = {str(p.relative_to(root)): p.read_bytes() for p in [root / 'VERSION', root / 'README.md', *sorted((root / 'site').rglob('*'))] if p.is_file()}
            result = subprocess.run(['python3', str(root / 'scripts/build_site.py')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            version, date = [line.partition(':')[2].strip() for line in (root / 'VERSION').read_text().splitlines()]
            self.assertIn(f'**Version {version}** ({date})', (root / 'README.md').read_text())
            for page in (root / 'dist').glob('*.html'):
                self.assertIn(f'v{version}', page.read_text())
                self.assertIn(date, page.read_text())
                self.assertNotIn('<!-- FISKWISE_VERSION -->', page.read_text())
            for relative, content in before.items():
                self.assertEqual((root / relative).read_bytes(), content)
