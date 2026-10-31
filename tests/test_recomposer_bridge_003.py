"""JSON contract smoke tests for JAR;VIS source-owned bridge."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts" / "recomposer-bridge.py"
spec = importlib.util.spec_from_file_location("recomposer_bridge", path)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class TestRecomposerBridge(unittest.TestCase):
    def test_round_trip_and_strict_consent(self):
        initial = bridge.run({"action": "genesis"})["state"]
        result = bridge.run({"action": "compile", "state": initial, "text": "music and food"})
        self.assertEqual(result["plan"]["status"], "PROPOSAL_ONLY")
        self.assertGreater(len(result["family"]["candidates"]), 1)
        with self.assertRaises(ValueError):
            bridge.run({"action": "feedback", "state": initial,
                        "plan": result["plan"], "selected": "food",
                        "outcome": "helpful"})
        new = bridge.run({"action": "feedback", "state": initial,
                          "plan": result["plan"], "selected": "food",
                          "outcome": "helpful", "consent": True})["state"]
        self.assertEqual(new["revision"], 1)
        self.assertEqual(initial["revision"], 0)
    def test_artifact_receipt_and_mem_projection(self):
        initial = bridge.run({"action": "genesis"})["state"]
        plan = bridge.run({"action": "compile", "state": initial, "text": "food"})["plan"]
        observed = bridge.run({"action": "artifact", "state": initial,
                                "plan": plan, "topic": "food",
                                "output_sha256": "a"*64, "consent": True})["receipt"]
        new = bridge.run({"action": "compile", "state": initial, "text": "food",
                          "artifact_receipts": [observed]})
        self.assertEqual(new["family"]["capsule"]["archive_cut"], initial["head"])
        self.assertTrue(new["family"]["family_id"] != bridge.run({
            "action":"compile","state":initial,"text":"food"})["family"]["family_id"])


if __name__ == "__main__":
    unittest.main()
