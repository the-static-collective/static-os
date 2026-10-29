import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BRIDGE=ROOT/'scripts'/'portable-to-cannon.py'
SPEC=importlib.util.spec_from_file_location('portable_bridge_test',BRIDGE)
portable=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(portable)


class StrangePortsTests(unittest.TestCase):
    def test_exact_inert_contract_for_every_device_and_question(self):
        self.assertEqual(len(portable.QUESTIONS),4)
        self.assertEqual(len(portable.DEVICES),6)
        for device in portable.DEVICES:
            for focus in portable.QUESTIONS:
                candidate=portable.make_intent(device,focus)
                self.assertEqual(portable.validate(candidate),candidate)
                self.assertEqual(candidate['scenario'],'FICTIONAL_A_B')
                self.assertFalse(candidate['network_transmitted'])
                self.assertFalse(candidate['independent_witness'])
                self.assertFalse(candidate['signed'])
                self.assertFalse(candidate['physical_observation'])

    def test_changing_any_authority_or_field_refused(self):
        base=portable.make_intent("ESP32_USB_SERIAL","Living House")
        attempts=[
            ('mode','AUTOMATIC_ACTUATION'),('scenario','REAL_NEIGHBOR'),
            ('physical_observation',True),('signed',True),
            ('independent_witness',True),('network_transmitted',True),
            ('status','REAL_DELIVERY'),('source_device','VIRTUAL_AUTHORITY'),
            ('question','DROP TABLE CASCADE'),('focus','AUTHORIZED_OWNER'),
        ]
        for field,value in attempts:
            with self.subTest(field=field):
                changed=dict(base);changed[field]=value
                with self.assertRaises(ValueError):
                    portable.validate(changed)
        changed=dict(base);changed['physical_address']='SECRET'
        with self.assertRaises(ValueError):
            portable.validate(changed)

    def test_terminal_cancellation_and_explicit_file_only(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            script=ROOT/'ports'/'terminal'/'genesis.py'
            base=[sys.executable,str(script),'--device','LEGACY_LINUX_PYTHON3',
                  '--out-dir',str(folder)]
            cancel=subprocess.run(base,input='1\nNO\n',
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(cancel.returncode,0,cancel.stderr)
            self.assertEqual(list(folder.glob('intent-*.json')),[])
            approval=subprocess.run(base,input='1\nEXPORT\n',
                                    capture_output=True,text=True,timeout=10)
            self.assertEqual(approval.returncode,0,approval.stderr)
            one=folder/'intent-001.json'
            self.assertTrue(one.is_file())
            self.assertEqual(portable.load_intent(one)['focus'],'Living House')
            again=subprocess.run(base,input='1\nEXPORT\n',
                                 capture_output=True,text=True,timeout=10)
            self.assertEqual(again.returncode,0,again.stderr)
            self.assertTrue((folder/'intent-002.json').is_file())
            self.assertEqual(portable.load_intent(one)['source_device'],'LEGACY_LINUX_PYTHON3')

    def test_validating_does_not_call_cannon_and_exec_requires_source_roots(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'intent.json'
            p.write_text(json.dumps(portable.make_intent('NINTENDO_DS_DLDI','Repair Lab')))
            val=subprocess.run([sys.executable,str(BRIDGE),'--intent',str(p),'--validate'],
                               capture_output=True,text=True,timeout=10)
            self.assertEqual(val.returncode,0,val.stderr)
            self.assertFalse(json.loads(val.stdout)['executed'])
            run=subprocess.run([sys.executable,str(BRIDGE),'--intent',str(p),'--execute'],
                               capture_output=True,text=True,timeout=10)
            self.assertEqual(run.returncode,2)
            self.assertIn('HOLD:',run.stderr)

    def test_device_builds_and_fallbacks_distinct(self):
        gc=(ROOT/'ports'/'gamecube'/'source'/'main.c').read_text()
        ds=(ROOT/'ports'/'nds'/'source'/'main.c').read_text()
        esp=(ROOT/'ports'/'esp32'/'main'/'main.c').read_text()
        self.assertIn('PAD_ButtonsDown',gc)
        self.assertIn('gamecube_rules',(ROOT/'ports'/'gamecube'/'Makefile').read_text())
        self.assertIn('fatInitDefault',gc)
        self.assertIn('keysDown()',ds)
        self.assertIn('ds_rules',(ROOT/'ports'/'nds'/'Makefile').read_text())
        self.assertIn('fatInitDefault',ds)
        self.assertIn('uart_read_bytes',esp)
        self.assertIn('ESP32_USB_SERIAL',esp)
        for source in (gc,ds,esp):
            self.assertIn('genesis_format_intent',source)
            self.assertNotIn('socket(',source)
            self.assertNotIn('http://',source)
        for path in ('ports/android/genesis-termux.sh',
                     'ports/legacy-linux/genesis.sh',
                     'ports/raspberry-pi/genesis-pi.sh'):
            src=(ROOT/path).read_text()
            self.assertNotIn('apt install',src)
            self.assertNotIn('curl https:',src)
        self.assertIn('GENESIS_NATIVE_ROOTS',(ROOT/'ports/raspberry-pi/genesis-pi.sh').read_text())


if __name__=='__main__':
    unittest.main()
