"""Sync canonical assets into sibling documentation sites; never touches scientific themes."""
from pathlib import Path
import argparse
import shutil

ROOT = Path(__file__).resolve().parents[1]

def sync(workspace):
    bait = workspace / "BAIT/docs/assets"
    slides = workspace / "wise-presentations/website/public/fiskwise"
    if not bait.parent.exists() or not slides.parents[1].exists():
        raise SystemExit("Expected sibling BAIT and wise-presentations checkouts; pass --workspace.")
    bait.mkdir(parents=True, exist_ok=True)
    for source, target in [("fiskwise-tokens.css", "fiskwise-tokens.css"),
                           ("wordmark.svg", "fiskwise-wordmark.svg"),
                           ("favicon.svg", "fiskwise-favicon.svg")]:
        shutil.copy2(ROOT / "assets" / source, bait / target)
    shutil.copytree(ROOT / "assets", slides, dirs_exist_ok=True)
    print("Synced brand assets to BAIT/docs/assets and wise-presentations/website/public/fiskwise")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=ROOT.parent)
    sync(parser.parse_args().workspace)
