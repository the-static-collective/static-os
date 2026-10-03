import argparse
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_os_nav", ROOT / "scripts" / "nav.py"
)
nav = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nav)
PACKET = json.loads(
    (ROOT / "bridge" / "nav.packet.json").read_text(encoding="utf-8")
)


class NavBridgeTests(unittest.TestCase):
    def test_packet_contract(self):
        self.assertEqual(
            nav.validate_packet(copy.deepcopy(PACKET))["id"],
            "nav-001",
        )

    def test_refuse_invariant_drift(self):
        bad = copy.deepcopy(PACKET)
        bad["core_distinction"] = "MOVE FAST"
        with self.assertRaisesRegex(ValueError, "invariant"):
            nav.validate_packet(bad)

    def test_refuse_automatic_external_effects(self):
        bad = copy.deepcopy(PACKET)
        bad["runtime"]["automatic_external_effects"] = True
        with self.assertRaisesRegex(ValueError, "automatic external"):
            nav.validate_packet(bad)

    def test_orient_then_contact(self):
        args = argparse.Namespace(
            heading="Test the smallest viable route.",
            preserve=["reversibility"],
            aperture=["one independent observation"],
            move="Run one bounded trial.",
            stop="Stop if the preserve condition fails.",
            claim_limit="One trial is not a final answer.",
        )
        oriented = nav.make_orientation(args)
        self.assertEqual(oriented["status"], "oriented")
        contacted = nav.record_encounter(
            oriented,
            "The trial produced a result the plan did not predict.",
            "The next route needs less scope.",
            "Reduce the move and repeat with a fresh observation.",
        )
        self.assertEqual(contacted["status"], "contacted")
        self.assertIn("less scope", contacted["delta"])

    def test_refuse_fake_contact(self):
        args = argparse.Namespace(
            heading="H",
            preserve=["P"],
            aperture=["A"],
            move="M",
            stop="S",
            claim_limit="L",
        )
        oriented = nav.make_orientation(args)
        bad = dict(oriented)
        bad["status"] = "contacted"
        with self.assertRaisesRegex(ValueError, "contacted receipt missing"):
            nav.validate_receipt(bad)

    def test_game_does_not_award_generation_points(self):
        args = argparse.Namespace(
            heading="H",
            preserve=["P"],
            aperture=["A"],
            move="M",
            stop="S",
            claim_limit="L",
        )
        oriented = nav.make_orientation(args)
        event = nav.game_event(oriented)
        self.assertEqual(event["progress_class"], "awaiting-world-contact")
        self.assertIsNone(event["scalar_score"])

        contacted = nav.record_encounter(oriented, "O", "D", "N")
        event2 = nav.game_event(contacted)
        self.assertEqual(event2["progress_class"], "world-contacted")
        self.assertIsNone(event2["scalar_score"])

    def test_card_uses_packet(self):
        card = nav.render_card(PACKET)
        self.assertIn("THE LOOP MUST BE SURPRISED.", card)
        self.assertIn("7. Reorient.", card)


if __name__ == "__main__":
    unittest.main()
