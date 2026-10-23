#!/usr/bin/env python3
"""Preview first. Applying skills never installs R/system software or downloads data."""
import argparse
import json
import sys
from lifecycle import Manager


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', help='Isolated home for testing or an explicitly selected user')
    parser.add_argument('--workspace', help='Parent directory for component checkouts')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['install', 'update', 'uninstall']:
        p = sub.add_parser(command)
        p.add_argument('--apply', action='store_true')
        if command == 'install':
            p.add_argument('--include', action='append', default=[])
            p.add_argument('--agent', action='append', choices=['claude', 'codex'])
            p.add_argument('--adopt-existing', action='store_true')
            p.add_argument('--no-clone', action='store_true')
            p.add_argument('--copy', action='store_true', help='Use copies where symlinks are unavailable')
        if command == 'uninstall':
            p.add_argument('--confirm', help='Exact digest from the user-approved current preview')
            p.add_argument('--include-adopted', action='store_true', help='Detach adopted entries, restoring their previous registrations')
    sub.add_parser('status')
    p = sub.add_parser('consent')
    p.add_argument('choice', choices=['allow', 'revoke'])
    p = sub.add_parser('database-begin')
    p.add_argument('path')
    p = sub.add_parser('database-complete')
    p.add_argument('token')
    p.add_argument('--bait-verified', action='store_true')
    for command in ['database-preview', 'database-remove']:
        p = sub.add_parser(command)
        p.add_argument('path')
        if command == 'database-remove':
            p.add_argument('--confirm', required=True)
            p.add_argument('--quarantine', help='Explicit user-approved same-filesystem recovery directory')
    args = parser.parse_args(argv)
    manager = Manager(workspace=args.workspace, home=args.home)
    if args.command == 'install':
        result = manager.install(args.include, args.agent, args.adopt_existing, not args.no_clone, args.copy) if args.apply else manager.install_plan(args.include, args.agent, args.adopt_existing)
    elif args.command == 'update':
        result = manager.update(args.apply)
    elif args.command == 'uninstall':
        result = manager.uninstall(args.confirm, args.include_adopted) if args.apply else manager.removal_plan(args.include_adopted)
    elif args.command == 'status':
        result = manager.state
    elif args.command == 'consent':
        manager.set_consent(args.choice == 'allow')
        result = manager.state['consent']
    elif args.command == 'database-begin':
        result = {'token': manager.database_begin(args.path)}
    elif args.command == 'database-complete':
        manager.database_complete(args.token, args.bait_verified)
        result = {'verified': True}
    elif args.command == 'database-preview':
        result = manager.database_plan(args.path)
    else:
        result = manager.database_remove(args.path, args.confirm, args.quarantine)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(str(error))
