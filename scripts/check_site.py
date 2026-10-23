"""Validate built package coverage, local links/assets, anchors, SVGs, and planned status."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.articles = [], set(), []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            assert a['id'] not in self.ids, f"Duplicate anchor: {a['id']}"
            self.ids.add(a['id'])
        for attr in ("href", "src"):
            if attr in a:
                self.links.append(a[attr])
        if tag == "article":
            self.articles.append(a)

def main():
    dist = ROOT / "dist"
    parser = Page()
    source = (dist / "index.html").read_text()
    parser.feed(source)
    packages = json.loads((ROOT / "packages.json").read_text())
    assert len(parser.articles) == len(packages) == 9
    assert '<span class="planned">Planned</span>' in source
    assert source.count('<span class="planned">Planned</span>') == 2
    assert "<!-- KNOWLEDGE_PACKS -->" not in source
    for p in packages:
        assert p['name'] in source
        assert p['status'] in ['available', 'planned']
        for key in ['repo', 'site']:
            if p[key]:
                assert p[key] in source, f"Missing {p['name']} {key} link"
    for url in parser.links:
        split = urlsplit(url)
        if split.scheme or split.netloc:
            assert split.scheme == 'https', f"Non-HTTPS link: {url}"
            continue
        if split.path:
            assert not split.path.startswith('/'), f"Nonportable Pages path: {url}"
            assert (dist / unquote(split.path)).exists(), f"Missing local target: {url}"
        if split.fragment:
            assert split.fragment in parser.ids, f"Missing anchor: {url}"
    for svg in (dist / "assets").rglob("*.svg"):
        ET.parse(svg)
    print(f"PASS: {len(packages)} components; all local links, anchors and SVGs; two planned labels")

if __name__ == "__main__":
    main()
