"""Build the static Fiskwise hub. Python standard library only; no network access."""
from pathlib import Path
from datetime import date
import html
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"

def read_version():
    fields = {}
    for line in VERSION_FILE.read_text().splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or key.strip() in fields:
            raise ValueError(f"Invalid VERSION entry: {line!r}")
        fields[key.strip()] = value.strip()
    if set(fields) != {"version", "date"}:
        raise ValueError("VERSION must define exactly 'version' and 'date'.")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", fields["version"]):
        raise ValueError(f"Invalid Fiskwise version: {fields['version']!r}")
    date.fromisoformat(fields["date"])
    return fields["version"], fields["date"]

def inject_version(website, version, release_date):
    pages = sorted(website.rglob("*.html"))
    if not pages:
        raise ValueError("No HTML pages found to stamp with the Fiskwise version.")
    for page in pages:
        source = page.read_text()
        if source.count("<!-- FISKWISE_VERSION -->") != 1 or source.count("<!-- FISKWISE_DATE -->") != 2:
            raise ValueError(f"{page.relative_to(website)} must contain one version and two date tokens.")
        rendered = source.replace("<!-- FISKWISE_VERSION -->", html.escape(version))
        rendered = rendered.replace("<!-- FISKWISE_DATE -->", html.escape(release_date))
        page.write_text(rendered)

    if any("<!-- FISKWISE_VERSION -->" in page.read_text() or "<!-- FISKWISE_DATE -->" in page.read_text() for page in pages):
        raise ValueError("A website page still has an unstamped Fiskwise version token.")

def link(url, label, cls=""):
    return f'<a class="{cls}" href="{html.escape(url, quote=True)}">{label}</a>'

def main():
    version_source = VERSION_FILE.read_bytes()
    version, release_date = read_version()
    packages = json.loads((ROOT / "packages.json").read_text())
    dest = ROOT / "dist"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "site", dest)
    shutil.copytree(ROOT / "assets", dest / "assets")
    cards, planned, tools = [], [], []
    for p in packages:
        name = html.escape(p["name"])
        status = '<span class="planned">Planned</span>' if p["status"] == "planned" else ''
        links = []
        if p["site"]:
            links.append(link(p["site"], 'Explore documentation <span aria-hidden="true">↗</span>', 'primary-link'))
        if p.get("overview") and p.get("overview") != p.get("site"):
            links.insert(0, link(p['name'] + '.html', 'How to use this pack', 'primary-link'))
        if p["repo"]:
            links.append(link(p["repo"], 'GitHub <span aria-hidden="true">↗</span>'))
        if p["kind"] == "knowledge":
            pack_type = "Planned pack" if p["status"] == "planned" else "Core pack" if p.get("core") else {"data": "Data add-on", "presentations": "Presentation add-on", "methods": "Method add-on"}.get(p.get("role"), "Optional pack")
            (planned if p["status"] == "planned" else cards).append(f'''<article class="pack" id="{name}" style="--pack-accent:{p['accent']}">
              <div class="pack-top"><img src="assets/icons/{p['icon']}.svg" alt="" width="44" height="44"><span class="pack-type">{pack_type}</span>{status}</div>
              <h3>{name}</h3><p class="pack-label">{html.escape(p['label'])}</p>
              <p>{html.escape(p['detail'])}</p><div class="pack-links">{' '.join(links)}</div></article>''')
        else:
            tools.append(f'''<article class="r-package"><img src="assets/icons/{p['icon']}.svg" alt="" width="38" height="38">
              <div><h3>{name} {status}</h3><p>{html.escape(p['purpose'])}</p><div class="pack-links">{' '.join(links)}</div></div></article>''')
    page = (ROOT / "site/index.html").read_text()
    page = page.replace("<!-- KNOWLEDGE_PACKS -->", "\n".join(cards)).replace("<!-- R_PACKAGES -->", "\n".join(tools)).replace("<!-- PLANNED_PACKS -->", "\n".join(planned))
    (dest / "index.html").write_text(page)
    # Small pack landing pages share the hub design and canonical inventory.
    shell = (ROOT / 'site/getting-started.html').read_text()
    header, tail = shell.split('<main id="main">', 1)
    footer = tail.split('</main>', 1)[1].split('  <script>', 1)[0] + '</body>\n</html>\n'
    for pack in packages:
        if not pack.get('overview'):
            continue
        name = html.escape(pack['name'])
        page_header = header.replace('Getting started — Fiskwise', name + ' — Fiskwise')
        page_header = page_header.replace('https://deepwaterimr.github.io/fiskwise/getting-started.html', pack['overview'])
        page_header = page_header.replace(' aria-current="page"', '')
        page_header = page_header.replace('Install, update, and remove Fiskwise with clear previews, optional dependencies, and researcher control.', html.escape(pack['purpose'], quote=True))
        supporting = ''.join('<li>' + link(item['url'], html.escape(item['name'])) + ' — ' + html.escape(item['purpose']) + '</li>' for item in pack.get('supporting_tools', []))
        documentation = link(pack['repo'], 'Read the pack instructions on GitHub')
        if pack.get('site') and pack['site'] != pack['overview']:
            documentation += ' · ' + link(pack['site'], 'Open specialist documentation')
        body = f'''<main id="main"><section class="guide-hero container"><p class="eyebrow">FISKWISE / {html.escape(pack['role'].upper())}</p><h1>{name}</h1><p>{html.escape(pack['purpose'])}</p><p>{html.escape(pack['detail'])}</p><p>{documentation}</p></section>
        <section class="guide-section guide-tint"><div class="container"><div class="guide-heading"><h2>Start with your question</h2><p class="example-prompt">{html.escape(pack['example'])}</p></div><p>The agent reads the relevant instructions, inspects your inputs and proposes an approach. Review scientific choices, outputs and limitations; the researcher directs and remains responsible for the work.</p></div></section>
        <section class="guide-section container"><div class="guide-heading"><h2>Use it independently or with Fiskwise</h2></div><p>For the full ecosystem, follow the <a href="getting-started.html">installation and update guide</a>. To use this pack alone, tell your agent:</p><div class="prompt-card"><pre>install {html.escape(pack['repo'])}</pre></div><p>Then describe your task. The pack retains its own setup and update instructions. R packages and system tools are installed only with the applicable permission.</p>{('<h3>Supporting tools</h3><ul>' + supporting + '</ul>') if supporting else ''}<p><a href="./#knowledge-packs">Explore related packs →</a></p></section></main>'''
        (dest / (pack['name'] + '.html')).write_text(page_header + body + footer)

    shutil.copy2(ROOT / "packages.json", dest / "packages.json")
    for name in ["MIGRATION.md", "BRAND.md", "CONTRIBUTING.md", "LICENSE"]:
        shutil.copy2(ROOT / name, dest / name)
    if (ROOT / "docs").exists():
        shutil.copytree(ROOT / "docs", dest / "docs")
    inject_version(dest, version, release_date)
    (dest / ".nojekyll").touch()
    if VERSION_FILE.read_bytes() != version_source:
        raise RuntimeError("VERSION changed while building the site; restore it and rerun the build.")
    print(f"Built {len(packages)} package entries in dist/ at Fiskwise v{version} ({release_date}).")

if __name__ == "__main__":
    main()
