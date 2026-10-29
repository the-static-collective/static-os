#!/usr/bin/env python3
"""Read-only STATIC OS Suitcase planning CLI; no installation actions."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from suitcase.plan import compose, probe, verify, validate_inventory  # noqa: E402


def read_json(path):
    data = Path(path).read_bytes()
    if len(data) > 32768:
        raise ValueError('JSON input exceeds 32 KiB')
    return json.loads(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description='STATIC OS Suitcase candidate (read-only)')
    commands = parser.add_subparsers(dest='cmd', required=True)
    commands.add_parser('probe', help='inspect current host without modifying it')
    p = commands.add_parser('compose', help='print a deterministic HOLD-only plan')
    p.add_argument('--inventory', help='previously recorded JSON inventory; default: probe this host')
    p.add_argument('--profile', required=True,
                   choices=['commons', 'church', 'resilience', 'protected', 'foundry'])
    p.add_argument('--media', default='seed', choices=['seed', 'grow', 'forest'])
    p.add_argument('--privacy', default='private',
                   choices=['private', 'invitation-only', 'public-candidate'])
    v = commands.add_parser('verify', help='recompute and check a plan, without executing it')
    v.add_argument('plan')
    args = parser.parse_args(argv)
    try:
        if args.cmd == 'probe':
            result = probe()
        elif args.cmd == 'compose':
            observed = validate_inventory(read_json(args.inventory)) if args.inventory else probe()
            result = compose(observed, args.profile, args.media, args.privacy)
        else:
            verify(read_json(args.plan))
            print('VALID HOLD-ONLY PLAN; NO INSTALLATION OR AUTHORITY')
            return 0
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f'REFUSE: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
