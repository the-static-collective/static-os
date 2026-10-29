#!/usr/bin/env python3
"""Read-only STATIC OS Suitcase planning CLI; no installation actions."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from suitcase.plan import compose, probe, verify, validate_inventory  # noqa: E402
from suitcase.house import compose_house, verify_house, empty_survey, validate_survey  # noqa: E402


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
    h = commands.add_parser('house-compose', help='generate a HOLD-only Living House construction recipe')
    h.add_argument('--inventory', help='observations; default: current host')
    h.add_argument('--site', help='public-safe site and parts survey JSON; default: unknown everything')
    h.add_argument('--profile', choices=['commons','church','resilience','protected','foundry'], default='foundry')
    h.add_argument('--media', choices=['seed','grow','forest'], default='grow')
    h.add_argument('--privacy', choices=['private','invitation-only','public-candidate'], default='private')
    hv = commands.add_parser('house-verify', help='cold verify a house plan, without executing it')
    hv.add_argument('plan')
    commands.add_parser('house-template', help='emit a blank public-safe single-house survey')
    v = commands.add_parser('verify', help='recompute and check a plan, without executing it')
    v.add_argument('plan')
    args = parser.parse_args(argv)
    try:
        if args.cmd == 'probe':
            result = probe()
        elif args.cmd == 'house-template':
            result = empty_survey()
        elif args.cmd == 'house-compose':
            observed = validate_inventory(read_json(args.inventory)) if args.inventory else probe()
            survey = validate_survey(read_json(args.site)) if args.site else empty_survey()
            result = compose_house(observed, survey, args.profile, args.media, args.privacy)
        elif args.cmd == 'house-verify':
            verify_house(read_json(args.plan))
            print('VALID HOUSE PROPOSAL; NO BUILD, INSTALLATION OR AUTHORITY')
            return 0
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
