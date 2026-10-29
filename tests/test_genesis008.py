"""Independent boundaries: universal cartridge is not a warrant, service or receipt."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cartridges import genesis008 as c
from cartridges import audio

spec=importlib.util.spec_from_file_location("genesis008_command",ROOT/"scripts"/"genesis008.py")
cli=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class Genesis008CartridgeTests(unittest.TestCase):
    def test_all_twenty_five_verb_focus_types_and_all_device_entrances(self):
        self.assertEqual(len(c.KINDS),5)
        self.assertEqual(len(c.FOCI),4)
        for source in c.SOURCES:
            for focus in c.FOCI:
                a=c.mint("ASK",focus,source)
                self.assertEqual(c.decode(c.encode(a)),a)
                self.assertEqual(c.validate(a),a)
                self.assertEqual(a["disposition"],"QUESTION_ONLY")
                self.assertFalse(a["human_permission"])
                self.assertFalse(a["physical_observation"])
                self.assertFalse(a["independent_witness"])
                self.assertFalse(a["delivered"])
                for kind in c.KINDS[1:]:
                    child=c.mint(kind,focus,source,[a["digest"]])
                    self.assertEqual(c.validate(child),child)
                    self.assertEqual(c.decode(c.encode(child)),child)
                    self.assertNotEqual(child["digest"],a["digest"])
                    self.assertEqual(child["parents"],[a["digest"]])

    def test_no_cartridge_can_forge_real_deed_authority_or_human_witness(self):
        x=c.mint("WITNESS","Community Food","FESTIVAL_SYNTHETIC_DEMO",
                 [c.mint("ASK","Community Food","FESTIVAL_SYNTHETIC_DEMO")["digest"]])
        for field, fake in [
            ("human_permission",True),("physical_observation",True),
            ("independent_witness",True),("signed",True),("delivered",True),
            ("authority","OWNER_APPROVED"),("disposition","REAL_HELP_DELIVERED"),
            ("statement","A human was helped"),("source","UNKNOWN_PERSON"),
        ]:
            attempt={**x,field:fake}
            with self.subTest(field=field),self.assertRaises(ValueError):
                c.validate(attempt)
        extra={**x,"phone_number":"555-1111"}
        with self.assertRaises(ValueError):
            c.validate(extra)

    def test_lineage_requires_known_prior_local_link_and_correct_focus(self):
        ask=c.mint("ASK","Festival Table","FESTIVAL_SYNTHETIC_DEMO")
        other=c.mint("ASK","Repair Lab","FESTIVAL_SYNTHETIC_DEMO")
        offer=c.mint("OFFER","Festival Table","FESTIVAL_SYNTHETIC_DEMO",[ask["digest"]])
        proposal=c.mint("PROPOSE","Festival Table","FESTIVAL_SYNTHETIC_DEMO",
                        [ask["digest"],offer["digest"]])
        witness=c.mint("WITNESS","Festival Table","FESTIVAL_SYNTHETIC_DEMO",
                       [proposal["digest"]])
        repeat=c.mint("REPLICATE","Festival Table","FESTIVAL_SYNTHETIC_DEMO",
                      [proposal["digest"],witness["digest"]])
        result=c.validate_chain([ask,offer,proposal,witness,repeat])
        self.assertEqual(result["count"],5)
        self.assertFalse(result["has_real_field_witness"])
        for chain in ([offer,ask], [ask,ask],
                      [ask,other,offer,c.mint("PROPOSE","Repair Lab",
                                             "FESTIVAL_SYNTHETIC_DEMO",[offer["digest"]])]):
            with self.assertRaises(ValueError):
                c.validate_chain(list(chain))

    def test_broken_portable_bits_rejected(self):
        a=c.mint("ASK","Living House","NINTENDO_GAMECUBE_SD")
        encoded=c.encode(a)
        for broken in ("GC1:not@valid", "XX1:"+encoded[4:], encoded+"A",
                       "GC1:"+("a"*9000),"GC1:AA", "GC1:"):
            with self.subTest(broken=broken[:26]),self.assertRaises(ValueError):
                c.decode(broken)
        changed={**a,"digest":"sha256:"+"a"*64}
        with self.assertRaises(ValueError):
            c.encode(changed)

    def test_audio_wav_digital_roundtrip_without_claiming_acoustic_channel(self):
        for focus in ("Living House","Festival Table"):
            a=c.mint("ASK",focus,"NINTENDO_GAMECUBE_SD")
            wav=audio.to_wav(a)
            self.assertTrue(wav.startswith(b"RIFF"))
            self.assertLess(len(wav),3_000_000)
            self.assertEqual(audio.from_wav(wav),a)
            with self.assertRaises(ValueError):
                audio.from_wav(wav[:len(wav)//2])
            with self.assertRaises(ValueError):
                audio.from_wav(b"not a WAV file")

    def test_legacy_wii_and_portable_apps_convert_without_execution(self):
        original=cli._import_module("original_portable_test",ROOT/"scripts"/"portable-to-cannon.py")
        wii=cli._import_module("original_wii_test",ROOT/"scripts"/"wii-to-cannon.py")
        with tempfile.TemporaryDirectory() as tmp:
            for source,focus in (
                ("NINTENDO_GAMECUBE_SD","Community Food"),
                ("NINTENDO_DS_DLDI","Repair Lab"),
                ("ESP32_USB_SERIAL","Living House"),
                ("ANDROID_TERMUX_LOCAL","Festival Table"),
            ):
                name=Path(tmp)/(source+".json")
                name.write_text(json.dumps(original.make_intent(source,focus)))
                promoted=cli.legacy_to_cartridge(name)
                self.assertEqual(promoted["source"],source)
                self.assertEqual(original.validate(cli.legacy_from_cartridge(promoted))
                                 ["question"],original.QUESTIONS[focus])
            wiidata={
                "schema":wii.SCHEMA,"mission":"living-house",
                "focus":"Living House","question":wii.QUESTION["Living House"],
                "scenario":"FICTIONAL_A_B","mode":"OFFLINE_HOLD_ONLY",
                "source_device":"WII_HOMEBREW_LOCAL_OPERATOR",
                "operator_action":"PLUS_EXPORT_PRESSED",
                "status":"PROPOSAL_ONLY_NOT_EXECUTED",
                "transmitted":False,"physical_observation":False,
                "signed":False,"independent_witness":False,
            }
            original_file=Path(tmp)/"wii.json"
            original_file.write_text(json.dumps(wiidata))
            converted=cli.legacy_to_cartridge(original_file)
            self.assertEqual(converted["source"],"NINTENDO_WII_SD")
            self.assertEqual(wii.validate(cli.legacy_from_cartridge(converted)),wiidata)
            self.assertEqual(cli.bridge_to_cannon(c.encode(converted),
                             type("Opts",(),{"execute":False})())["executed"],False)

    def test_synthetic_cartridge_cannot_be_run_through_real_device_bridge(self):
        a=c.mint("ASK","Festival Table","FESTIVAL_SYNTHETIC_DEMO")
        with self.assertRaises(ValueError):
            cli.legacy_from_cartridge(a)
        with self.assertRaises(ValueError):
            cli.legacy_from_cartridge(c.mint("WITNESS","Festival Table",
                 "NINTENDO_DS_DLDI",[a["digest"]]))
        with self.assertRaises(ValueError):
            cli.bridge_to_cannon(c.encode(c.mint("ASK","Festival Table",
              "NINTENDO_DS_DLDI")),type("Opts",(),{"execute":True})())

    def test_actual_printable_synthetic_festival_and_manual_museum_created(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"next-festival"
            result=cli.demo(output,"Festival Table",False)
            self.assertEqual(result["status"],"CREATED_SYNTHETIC_GENESIS008_FESTIVAL")
            self.assertFalse(result["chain"]["has_real_field_witness"])
            self.assertEqual(result["chain"]["count"],5)
            self.assertTrue((output/"festival.html").exists())
            self.assertTrue((output/"museum.html").exists())
            self.assertTrue((output/"ask.wav").exists())
            self.assertEqual(c.decode((output/"ask.gc1").read_text().strip()),
                             audio.from_wav((output/"ask.wav").read_bytes()))
            staged=json.loads((output/"station-plan.json").read_text())
            self.assertEqual(len(staged["stations"]),5)
            self.assertEqual(staged["site_permission"],"MISSING")
            self.assertFalse(staged["actual_hardware_operated"])
            repeat=json.loads((output/"replication-blueprint-candidate.json").read_text())
            self.assertEqual(repeat["stage"],"DRAFT_NOT_AUTHORIZED")
            self.assertEqual(repeat["real_participants"],0)
            registry=cli.load_registry()
            self.assertGreaterEqual(len(registry["machines"]),10)
            self.assertTrue(all(x["physical"]=="UNTESTED" for x in registry["machines"]))
            with self.assertRaises(ValueError):
                cli.demo(output,"Festival Table",False)

    def test_command_line_inert_festival_inspection_and_text_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"festival"
            exe=[sys.executable,str(ROOT/"scripts"/"genesis008.py")]
            a=subprocess.run(exe+["demo","--out-dir",str(output)],
                             capture_output=True,text=True,timeout=35)
            self.assertEqual(a.returncode,0,a.stderr)
            check=subprocess.run(exe+["inspect","--text",str(output/"ask.gc1")],
                                 capture_output=True,text=True,timeout=15)
            self.assertEqual(check.returncode,0,check.stderr)
            self.assertEqual(json.loads(check.stdout)["cartridge"]["kind"],"ASK")
            inspect_wav=subprocess.run(exe+["inspect","--wav",str(output/"ask.wav")],
                                     capture_output=True,text=True,timeout=15)
            self.assertEqual(inspect_wav.returncode,0,inspect_wav.stderr)
            self.assertEqual(json.loads(inspect_wav.stdout)["cartridge"]["kind"],"ASK")


if __name__=="__main__":
    unittest.main()
