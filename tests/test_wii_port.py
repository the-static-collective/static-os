import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BRIDGE=ROOT/'scripts'/'wii-to-cannon.py'
SOURCE=ROOT/'ports'/'wii'/'source'/'main.c'
MAKE=ROOT/'ports'/'wii'/'Makefile'
meta=ROOT/'ports'/'wii'/'meta.xml'
spec=importlib.util.spec_from_file_location('wii_bridge', BRIDGE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class WiiPortTests(unittest.TestCase):
    def fixture(self, focus='Living House'):
        return {
            'schema':mod.SCHEMA,
            'mission':'living-house',
            'focus':focus,
            'question':mod.QUESTION[focus],
            'scenario':'FICTIONAL_A_B',
            'mode':'OFFLINE_HOLD_ONLY',
            'source_device':'WII_HOMEBREW_LOCAL_OPERATOR',
            'operator_action':'PLUS_EXPORT_PRESSED',
            'status':'PROPOSAL_ONLY_NOT_EXECUTED',
            'transmitted':False,
            'physical_observation':False,
            'signed':False,
            'independent_witness':False
        }

    def test_all_four_wii_questions_match_importer_exactly(self):
        s=SOURCE.read_text()
        self.assertEqual(len(mod.QUESTION),4)
        for name,question in mod.QUESTION.items():
            self.assertIn(name,s)
            self.assertIn(question,s)
            self.assertEqual(mod.validate(self.fixture(name))['question'],question)

    def test_refuses_made_up_real_world_authority_and_unsafe_data(self):
        for key,value in [
            ('mode','EXECUTE'),('scenario','REAL_PEOPLE'),('signed',True),
            ('physical_observation',True),('transmitted',True),
            ('independent_witness',True),('status','COMPLETED'),
            ('operator_action','SILENT_ACTION'),('question','delete everybody'),
            ('focus','HOME_INSTALL'),('mission','authority')
        ]:
            x=self.fixture();x[key]=value
            with self.assertRaises(ValueError):
                mod.validate(x)
        x=self.fixture();x['private_address']='not permitted'
        with self.assertRaises(ValueError):
            mod.validate(x)

    def test_file_is_inert_until_explicit_import_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'intent-001.json'
            p.write_text(json.dumps(self.fixture()))
            result=subprocess.run([sys.executable,str(BRIDGE),
                  '--intent',str(p),'--validate'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(json.loads(result.stdout)['executed'])
            invalid=subprocess.run([sys.executable,str(BRIDGE),
                '--intent',str(p),'--execute'],capture_output=True,text=True)
            self.assertEqual(invalid.returncode,2)
            self.assertIn('HOLD:',invalid.stderr)

    def test_no_wii_network_or_nand_and_file_is_create_only(self):
        s=SOURCE.read_text()
        self.assertIn('fatInitDefault()',s)
        self.assertIn('O_CREAT | O_EXCL',s)
        self.assertIn('WPAD_BUTTON_PLUS',s)
        self.assertIn('WPAD_BUTTON_A',s)
        self.assertIn('WPAD_BUTTON_HOME',s)
        self.assertIn('approved = 0;',s)
        for risk in ('net_init(', 'socket(', 'http://', 'ISFS_', 'NAND_', 'WPAD_Connect(', 'IOS_ReloadIOS('):
            self.assertNotIn(risk,s)

    def test_sdk_and_hbc_layout(self):
        self.assertIn('$(DEVKITPPC)/wii_rules',MAKE.read_text())
        self.assertIn('-lfat',MAKE.read_text())
        self.assertIn('<app version="1">',meta.read_text())
        self.assertIn('No network',meta.read_text())


if __name__=='__main__':
    unittest.main()
