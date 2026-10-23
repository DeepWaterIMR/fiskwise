"""Build the static Fiskwise hub. Python standard library only; no network access."""
from pathlib import Path
import html
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]

def link(url, label, cls=""):
    return f'<a class="{cls}" href="{html.escape(url, quote=True)}">{label}</a>'

def main():
    packages = json.loads((ROOT / "packages.json").read_text())
    dest = ROOT / "dist"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "site", dest)
    shutil.copytree(ROOT / "assets", dest / "assets")
    cards, tools = [], []
    for p in packages:
        name = html.escape(p["name"])
        status = '<span class="planned">Planned</span>' if p["status"] == "planned" else ''
        links = []
        if p["site"]:
            links.append(link(p["site"], 'Explore documentation <span aria-hidden="true">↗</span>', 'primary-link'))
        if p["repo"]:
            links.append(link(p["repo"], 'GitHub <span aria-hidden="true">↗</span>'))
        if p["kind"] == "knowledge":
            cards.append(f'''<article class="pack" id="{name}" style="--pack-accent:{p['accent']}">
              <div class="pack-top"><img src="assets/icons/{p['icon']}.svg" alt="" width="44" height="44"><span class="pack-type">Knowledge pack</span>{status}</div>
              <h3>{name}</h3><p class="pack-label">{html.escape(p['label'])}</p>
              <p>{html.escape(p['detail'])}</p><div class="pack-links">{' '.join(links)}</div></article>''')
        else:
            tools.append(f'''<article class="r-package"><img src="assets/icons/{p['icon']}.svg" alt="" width="38" height="38">
              <div><h3>{name} {status}</h3><p>{html.escape(p['purpose'])}</p><div class="pack-links">{' '.join(links)}</div></div></article>''')
    page = (ROOT / "site/index.html").read_text()
    page = page.replace("<!-- KNOWLEDGE_PACKS -->", "\n".join(cards)).replace("<!-- R_PACKAGES -->", "\n".join(tools))
    (dest / "index.html").write_text(page)
    shutil.copy2(ROOT / "packages.json", dest / "packages.json")
    for name in ["MIGRATION.md", "BRAND.md", "CONTRIBUTING.md", "LICENSE"]:
        shutil.copy2(ROOT / name, dest / name)
    (dest / ".nojekyll").touch()
    print(f"Built {len(packages)} package entries in dist/")

if __name__ == "__main__":
    main()
