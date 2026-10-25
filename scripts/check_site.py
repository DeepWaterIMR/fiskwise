"""Validate built Fiskwise pages, catalogue coverage, links, assets, and version metadata."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import read_version


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.articles = [], set(), []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            assert attributes["id"] not in self.ids, f"Duplicate anchor: {attributes['id']}"
            self.ids.add(attributes["id"])
        for attribute in ("href", "src"):
            if attribute in attributes:
                self.links.append(attributes[attribute])
        if tag == "article":
            self.articles.append(attributes)


def main():
    dist = ROOT / "dist"
    packages = json.loads((ROOT / "packages.json").read_text())
    version, release_date = read_version()
    pages = {path.resolve(): Page() for path in sorted(dist.rglob("*.html"))}
    assert dist / "index.html" in [Path(path) for path in pages], "Missing home page"
    assert (dist / "getting-started.html").resolve() in pages, "Missing getting-started guide"

    sources = {}
    for path, parser in pages.items():
        source = path.read_text()
        sources[path] = source
        parser.feed(source)
        assert "<!-- FISKWISE_VERSION -->" not in source, f"Unstamped version on {path.name}"
        assert "<!-- FISKWISE_DATE -->" not in source, f"Unstamped date on {path.name}"
        assert f"Fiskwise v{version}" in source, f"Missing version footer on {path.name}"
        assert f'<time datetime="{release_date}">{release_date}</time>' in source, f"Missing release date on {path.name}"

    home = (dist / "index.html").resolve()
    home_source = sources[home]
    knowledge_count = sum(package["kind"] == "knowledge" for package in packages)
    r_package_count = sum(package["kind"] == "r" for package in packages)
    planned_count = sum(package["status"] == "planned" for package in packages)
    assert len(pages[home].articles) == knowledge_count + r_package_count
    assert home_source.count('<span class="planned">Planned</span>') == planned_count
    assert "<!-- KNOWLEDGE_PACKS -->" not in home_source
    assert "<!-- R_PACKAGES -->" not in home_source
    assert "<!-- PLANNED_PACKS -->" not in home_source

    for package in packages:
        assert package["name"] in home_source
        assert package["status"] in ("available", "planned")
        for key in ("repo", "site"):
            if package.get(key):
                assert package[key] in home_source, f"Missing {package['name']} {key} link"

    for page_path, parser in pages.items():
        for url in parser.links:
            split = urlsplit(url)
            if split.scheme or split.netloc:
                assert split.scheme == "https", f"Non-HTTPS link: {url}"
                continue

            target = (page_path.parent / unquote(split.path)).resolve() if split.path else page_path
            if target.is_dir():
                target = (target / "index.html").resolve()
            if split.path:
                assert not split.path.startswith("/"), f"Nonportable Pages path: {url}"
                assert target.exists(), f"Missing local target from {page_path.name}: {url}"
            if split.fragment:
                assert target in pages, f"Fragment target is not an HTML page: {url}"
                assert unquote(split.fragment) in pages[target].ids, f"Missing anchor: {url}"

    for svg in (dist / "assets").rglob("*.svg"):
        ET.parse(svg)

    print(
        f"PASS: {len(pages)} pages; {knowledge_count} knowledge packs, {r_package_count} R tools, "
        f"{planned_count} planned entries; local links, anchors, SVGs, and v{version} ({release_date}) footers"
    )


if __name__ == "__main__":
    main()
