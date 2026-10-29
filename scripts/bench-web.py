#!/usr/bin/env python3
"""SUITCASE BENCH 001: opt-in, read-only local network handshake.

Inert demo endpoint: no persistence, case data, authentication or federation.
Loopback by default. LAN requires a specific RFC1918 IP and explicit consent.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from urllib.parse import urlsplit

CARD = {
    'schema': 'static-os.bench-link/v0',
    'claim': 'UNVERIFIED_PHYSICAL_LINK_TEST',
    'system': 'STATIC OS SUITCASE BENCH',
    'service': 'READ_ONLY_DEMONSTRATION',
    'allowed_action': 'view_this_page_only',
    'organization_founded': False,
    'federation_active': False,
    'private_information_present': False,
}
PAGE = '''<!doctype html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>STATIC OS | First Signal</title><style>
body{background:#15241e;color:#eef6ef;font:18px/1.5 system-ui,sans-serif;max-width:680px;margin:8vh auto;padding:0 22px}
h1{font-size:clamp(28px,5vw,48px)}.badge{display:inline-block;background:#314b3d;padding:6px 12px;border-radius:6px}
small{opacity:.75}</style></head><body><p class="badge">LOCAL BENCH / NO FEDERATION</p>
<h1>The suitcase can speak locally.</h1>
<p>If this page is visible on a second device with the internet disconnected, you have demonstrated one local HTTP connection.</p>
<p>Nothing here sends a request for help, identifies people, discovers organizations, or grants authority.</p>
<p><small>Next steps: independently verified signed crossings, privacy controls, and real local owner consent.</small></p>
</body></html>'''.encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    server_version = 'SuitcaseBench/0'
    sys_version = ''

    def log_message(self, format, *args):
        # No intentional application request/visitor logs.
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            data, mime, code = PAGE, 'text/html; charset=utf-8', 200
        elif path == '/health':
            data, mime, code = b'BENCH_ONLY\n', 'text/plain; charset=utf-8', 200
        elif path == '/bench-card.json':
            data = (json.dumps(CARD, sort_keys=True) + '\n').encode('utf-8')
            mime, code = 'application/json; charset=utf-8', 200
        else:
            data, mime, code = b'NOT_FOUND\n', 'text/plain; charset=utf-8', 404
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        self.send_error(405, 'Read-only bench')


def permitted_bind(host, lan):
    try:
        addr = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError('supply a numeric IPv4 address') from exc
    if addr.version != 4 or addr.is_multicast or addr.is_unspecified:
        raise ValueError('IPv4 unicast required; wildcard and IPv6 refused')
    if addr.is_loopback:
        return str(addr)
    if not lan or not addr.is_private or addr.is_link_local:
        raise ValueError('LAN requires explicit approval and specific RFC1918 IPv4')
    if not any(addr in ipaddress.ip_network(cidr) for cidr in
               ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
        raise ValueError('not RFC1918')
    return str(addr)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only Suitcase local-link demonstration')
    parser.add_argument('--bind', default='127.0.0.1', help='specific local IPv4')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--permit-lan-test', action='store_true',
                        help='The public demonstration page will be visible to this local network')
    args = parser.parse_args(argv)
    try:
        address = permitted_bind(args.bind, args.permit_lan_test)
        if not 1024 <= args.port <= 65535:
            raise ValueError('nonprivileged port must be 1024..65535')
        srv = ThreadingHTTPServer((address, args.port), Handler)
    except (ValueError, OSError) as exc:
        parser.error(f'REFUSE: {exc}')
    print(f'BENCH_ONLY: http://{address}:{args.port}/ (Ctrl+C to stop)', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == '__main__':
    main()
