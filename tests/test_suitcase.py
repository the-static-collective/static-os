"""Hostile boundary tests for deterministic, non-installing Suitcase candidate."""
import copy
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from suitcase.plan import compose, verify, INVENTORY_SCHEMA  # noqa: E402


class SuitcaseTests(unittest.TestCase):
    def setUp(self):
        self.inv = dict(schema=INVENTORY_SCHEMA, architecture='amd64', ram_mib=4096,
                        workspace_free_mib=16000, links_observed=['ethernet'],
                        power_observation='unknown')

    def test_all_five_profiles_hold_and_never_execute(self):
        for name in ('commons', 'church', 'resilience', 'protected', 'foundry'):
            plan = compose(self.inv, name)
            self.assertTrue(verify(plan))
            self.assertEqual(plan['status'], 'HOLD_FOR_BUILD_AND_HUMAN_REVIEW')
            self.assertFalse(any(plan['hardware_effects'].values()))
            self.assertEqual(plan['federation']['discovery'], 'DISABLED')
            self.assertEqual(plan['identity']['keys'], 'NOT_GENERATED')

    def test_deterministic_hash(self):
        a = compose(self.inv, 'church', 'forest', 'invitation-only')
        self.assertEqual(a, compose(copy.deepcopy(self.inv), 'church', 'forest', 'invitation-only'))
        self.assertEqual(len(a['plan_sha256']), 64)

    def test_tampered_capability_and_authority_refused(self):
        plan = compose(self.inv, 'commons')
        for mutate in (lambda p: p['capabilities'].append({'name': 'root-shell'}),
                       lambda p: p['federation'].update(discovery='PUBLIC'),
                       lambda p: p['hardware_effects'].update(disk_write=True),
                       lambda p: p.update(status='INSTALLED'),
                       lambda p: p.update(plan_sha256='a'*64)):
            bad = copy.deepcopy(plan)
            mutate(bad)
            with self.assertRaises(ValueError):
                verify(bad)

    def test_unknown_fields_and_arch_refused_or_held(self):
        bad = dict(self.inv, root_shell=True)
        with self.assertRaises(ValueError):
            compose(bad, 'church')
        bad = dict(self.inv, architecture='arm64')
        self.assertIn('NO_VERIFIED_BASE_IMAGE_FOR_ARCH', compose(bad, 'church')['holds'])
        bad = dict(self.inv, architecture='unknown-arch')
        with self.assertRaises(ValueError):
            compose(bad, 'church')

    def test_insufficient_resources_and_media_closure(self):
        bad = dict(self.inv, ram_mib=128, workspace_free_mib=32)
        holds = compose(bad, 'resilience', 'forest')['holds']
        self.assertIn('INSUFFICIENT_OBSERVED_RAM_FOR_CANDIDATE', holds)
        self.assertIn('INSUFFICIENT_BUILD_WORKSPACE_FREE_SPACE', holds)
        self.assertIn('OFFLINE_PACKAGE_CLOSURE_NOT_VERIFIED', holds)

    def test_refuse_public_protected(self):
        with self.assertRaises(ValueError):
            compose(self.inv, 'protected', 'grow', 'public-candidate')
        public = compose(self.inv, 'commons', privacy='public-candidate')
        self.assertEqual(public['federation']['discovery'], 'DISABLED')

    def test_incorrect_inventory_types_refused(self):
        for field, value in [('ram_mib', True), ('links_observed', ['wifi', 'wifi']),
                             ('power_observation', 'transmitting'),
                             ('workspace_free_mib', -1)]:
            bad = dict(self.inv, **{field: value})
            with self.assertRaises(ValueError):
                compose(bad, 'commons')

    def test_cli_probe_and_compose_offline(self):
        cmd = [sys.executable, str(ROOT/'scripts'/'suitcase.py')]
        p = subprocess.run(cmd+['probe'], capture_output=True, text=True, check=True)
        self.assertIn('static-os.hardware-observation/v0', p.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            inv = pathlib.Path(tmp)/'inv.json'
            import json
            inv.write_text(json.dumps(self.inv))
            p = subprocess.run(cmd+['compose', '--profile', 'foundry', '--inventory', str(inv)],
                               capture_output=True, text=True, check=True)
            plan = pathlib.Path(tmp)/'plan.json'
            plan.write_text(p.stdout)
            self.assertEqual(subprocess.run(cmd+['verify', str(plan)], capture_output=True).returncode, 0)
            payload = json.loads(p.stdout)
            payload['identity']['keys'] = 'GENERATED'
            plan.write_text(json.dumps(payload))
            self.assertEqual(subprocess.run(cmd+['verify', str(plan)], capture_output=True).returncode, 2)


if __name__ == '__main__':
    unittest.main()
