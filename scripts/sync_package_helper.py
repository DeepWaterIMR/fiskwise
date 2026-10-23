#!/usr/bin/env python3
"""Check the standalone presentation copy against wise-writing; --apply synchronizes it."""
from pathlib import Path
import argparse
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source = args.workspace / 'wise-writing/project-template/R/package_setup.R'
    target = args.workspace / 'wise-presentations/R/package_setup.R'
    if not source.is_file() or not target.is_file():
        parser.error('Both pack checkouts are required; no files were changed.')
    if source.read_bytes() != target.read_bytes():
        if not args.apply:
            parser.exit(1, 'Presentation helper differs. Review then run --apply.\n')
        shutil.copy2(source, target)
    print('Presentation helper matches wise-writing. Index/SPiCT copy it during scaffolding.')


if __name__ == '__main__':
    main()
