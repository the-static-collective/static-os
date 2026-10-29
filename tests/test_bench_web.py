"""SUITCASE 001 inert link: refusal tests and loopback-only HTTP proof."""
import importlib.util
import json
import pathlib
import threading
import unittest
from urllib import error, request

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'bench-web.py'
spec = importlib.util.spec_from_file_location('suitcase_bench_web', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class BenchTests(unittest.TestCase):
    def test_address_refusals(self):
        for addr in ('0.0.0.0', '8.8.8.8', '::', 'localhost', '169.254.10.1', '224.0.0.1'):
            with self.assertRaises(ValueError):
                mod.permitted_bind(addr, True)
        with self.assertRaises(ValueError):
            mod.permitted_bind('192.168.1.23', False)
        self.assertEqual(mod.permitted_bind('192.168.1.23', True), '192.168.1.23')
        self.assertEqual(mod.permitted_bind('127.0.0.1', False), '127.0.0.1')

    def test_card_cannot_claim_federation(self):
        self.assertFalse(mod.CARD['organization_founded'])
        self.assertFalse(mod.CARD['federation_active'])
        self.assertFalse(mod.CARD['private_information_present'])

    def test_local_http_read_only(self):
        server = mod.ThreadingHTTPServer(('127.0.0.1', 0), mod.Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with request.urlopen(base + '/health', timeout=2) as resp:
                self.assertEqual(resp.read(), b'BENCH_ONLY\n')
            with request.urlopen(base + '/', timeout=2) as resp:
                self.assertIn(b'The suitcase can speak locally.', resp.read())
            with request.urlopen(base + '/bench-card.json', timeout=2) as resp:
                self.assertFalse(json.load(resp)['federation_active'])
            with self.assertRaises(error.HTTPError) as err:
                request.urlopen(request.Request(base, data=b'private-data'), timeout=2)
            self.assertEqual(err.exception.code, 405)
            with self.assertRaises(error.HTTPError) as err:
                request.urlopen(base + '/secrets', timeout=2)
            self.assertEqual(err.exception.code, 404)
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()


if __name__ == '__main__':
    unittest.main()
