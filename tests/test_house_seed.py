"""HOUSE-SEED-001: the portable OS composes a house, never silently builds one."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from suitcase.plan import INVENTORY_SCHEMA  # noqa: E402
from suitcase.house import (compose_house, verify_house, empty_survey,  # noqa: E402
                            validate_survey, MODULES, NO_EFFECTS)


class HouseSeedTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {'schema': INVENTORY_SCHEMA, 'architecture': 'amd64',
                          'ram_mib': 4096, 'workspace_free_mib': 16000,
                          'links_observed': ['wifi'], 'power_observation': 'unknown'}
        self.site = empty_survey()

    def test_blank_house_outputs_a_real_staged_recipe_with_no_claimed_build(self):
        h = compose_house(self.inventory, self.site)
        self.assertTrue(verify_house(h))
        self.assertEqual(h['status'], 'HOLD_FOR_SITE_POWER_SAFETY_AND_HUMAN_REVIEW')
        self.assertEqual(h['mission'], 'BUILD_ONE_HOUSE_AS_A_MODEL_OF_A_COOPERATIVE_CITY')
        self.assertEqual(len(h['modules']), len(MODULES))
        self.assertEqual(len(h['stages']), 5)
        self.assertEqual(h['hardware_effects'], NO_EFFECTS)
        self.assertFalse(any(h['hardware_effects'].values()))
        self.assertEqual(h['network']['discovery'], 'DISABLED')
        self.assertEqual(h['outputs']['real_home'], 'NOT_BUILT')
        self.assertEqual(h['outputs']['os_image'], 'NOT_BUILT')
        self.assertEqual(h['parent_suitcase_plan']['status'], 'HOLD_FOR_BUILD_AND_HUMAN_REVIEW')
        self.assertEqual(h['parent_suitcase_plan']['identity']['keys'], 'NOT_GENERATED')
        self.assertEqual({m['state'] for m in h['modules']}, {'HOLD_FOR_SITE_SURVEY'})

    def test_derived_candidate_is_not_an_install_or_verified_work(self):
        s = empty_survey()
        s['site_permission'] = 'OPERATOR_SELF_ATTESTED'
        s['spaces'] = dict.fromkeys(s['spaces'], 'PRESENT_UNVERIFIED')
        s['parts'] = dict.fromkeys(s['parts'], 'PRESENT_UNVERIFIED')
        h = compose_house(self.inventory, s, 'commons', 'forest', 'invitation-only')
        self.assertTrue(verify_house(h))
        self.assertTrue(all(m['state'] == 'BENCH_CANDIDATE_UNVERIFIED' for m in h['modules']))
        self.assertTrue(all(m['authority'] == 'HUMAN_REVIEW_REQUIRED' for m in h['modules']))
        self.assertTrue(all(m['automatic_actuation'] is False for m in h['modules']))
        self.assertEqual(h['network']['consent'], 'NOT_ESTABLISHED_BY_SITE_SURVEY')
        self.assertEqual(h['outputs']['real_home'], 'NOT_BUILT')
        self.assertIn('NO_RELATIONAL_MEMORY_PROOF', h['claims_not_earned'])

    def test_partial_site_generates_precise_gaps_and_module_choices(self):
        s = empty_survey()
        s['spaces']['roof_or_window'] = 'PRESENT_UNVERIFIED'
        s['parts']['solar_module'] = 'PRESENT_UNVERIFIED'
        h = compose_house(self.inventory, s)
        solar = next(x for x in h['modules'] if x['id'] == 'solar_budget')
        self.assertEqual(solar['holds'], ['solar_controller'])
        self.assertIn('measured', solar['test_receipt_to_collect'])
        self.assertEqual(h['modules'][0]['state'], 'HOLD_FOR_SITE_SURVEY')

    def test_tamper_and_authority_escalation_refused_even_with_rehashed_plan(self):
        h = compose_house(self.inventory, self.site)
        changes = [
            lambda x: x['hardware_effects'].update(building_modification=True),
            lambda x: x['network'].update(discovery='PUBLIC'),
            lambda x: x['outputs'].update(real_home='BUILT'),
            lambda x: x['modules'][0].update(automatic_actuation=True),
            lambda x: x['modules'][0]['holds'].clear(),
            lambda x: x['parent_suitcase_plan']['identity'].update(keys='GENERATED'),
            lambda x: x.update(status='AUTHORIZED'),
        ]
        for change in changes:
            corrupted = copy.deepcopy(h)
            change(corrupted)
            with self.assertRaises(ValueError):
                verify_house(corrupted)

    def test_invalid_survey_refused(self):
        examples = [
            lambda x: x.update(residential_address='private'),
            lambda x: x.update(information_scope='PERSONAL_RECORDS'),
            lambda x: x['spaces'].update(utility='CONSTRUCTED'),
            lambda x: x['parts'].update(computer=True),
            lambda x: x.update(site_permission='GRANTED_BY_AI'),
            lambda x: x['parts'].pop('peer_device'),
        ]
        for change in examples:
            s = empty_survey()
            change(s)
            with self.assertRaises(ValueError):
                validate_survey(s)

    def test_deterministic_and_cold_verification(self):
        s = empty_survey()
        a = compose_house(self.inventory, s)
        self.assertEqual(a, compose_house(copy.deepcopy(self.inventory), copy.deepcopy(s)))
        self.assertEqual(len(a['plan_sha256']), 64)
        self.assertTrue(verify_house(json.loads(json.dumps(a))))

    def test_cli_compose_verify_and_refuse_tampered_document(self):
        cmd = [sys.executable, str(ROOT / 'scripts' / 'suitcase.py')]
        template = subprocess.run(cmd+['house-template'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(template.stdout), empty_survey())
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp)/'survey.json'
            f.write_text(template.stdout)
            inv = Path(tmp)/'inventory.json'
            inv.write_text(json.dumps(self.inventory))
            run = subprocess.run(cmd+['house-compose','--inventory',str(inv),
                                      '--site',str(f),'--profile','foundry'],
                                 capture_output=True,text=True,check=True)
            p = Path(tmp)/'house.json'
            p.write_text(run.stdout)
            self.assertEqual(subprocess.run(cmd+['house-verify',str(p)],
                                            capture_output=True).returncode, 0)
            bad = json.loads(run.stdout)
            bad['hardware_effects']['network_send'] = True
            p.write_text(json.dumps(bad))
            self.assertEqual(subprocess.run(cmd+['house-verify',str(p)],
                                            capture_output=True).returncode, 2)


if __name__ == '__main__':
    unittest.main()
