import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config" / "includes.chroot" / "usr" / "local" / "bin" / "static-bardo"
LOADER = importlib.machinery.SourceFileLoader("static_bardo", str(SCRIPT))
SPEC = importlib.util.spec_from_loader("static_bardo", LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

WHOLE = json.loads((ROOT / "manifest" / "whole-body-001.json").read_text(encoding="utf-8"))
GENERALITY = json.loads((ROOT / "manifest" / "bardo-generality-002.json").read_text(encoding="utf-8"))


def fixture(base: Path):
    image = base / "image"
    persistent = base / "persistent"
    share = image / "usr" / "share" / "static-os"
    sb1 = image / "opt" / "static-os" / "organs" / "relatte"
    sb2 = image / "opt" / "static-os" / "bardo-proofs" / "sb002-relatte"
    share.mkdir(parents=True)
    persistent.mkdir()
    (persistent / "crossing-exports").mkdir()
    (persistent / "organs").mkdir()

    (share / "whole-body-001.json").write_text(json.dumps(WHOLE), encoding="utf-8")
    (share / "bardo-generality-002.json").write_text(
        json.dumps(GENERALITY), encoding="utf-8"
    )

    for specimen, root in (("sb001", sb1), ("sb002", sb2)):
        proof = GENERALITY["specimens"][specimen]
        (root / "fixtures").mkdir(parents=True)
        (root / "scripts").mkdir(parents=True)
        (root / "docs").mkdir(parents=True)
        (root / "fixtures" / f"{specimen}-evidence-manifest.json").write_text(
            json.dumps({"evidence_set_id": proof["evidence_set_id"]}),
            encoding="utf-8",
        )
        (root / "scripts" / f"{specimen}-verify.ts").write_text(
            "fixture\n", encoding="utf-8"
        )
        label = specimen.upper().replace("SB00", "SB-00")
        (root / "docs" / f"SUPABARDO-{label}.md").write_text(
            "fixture\n", encoding="utf-8"
        )

    witness = share / "bardo-proofs" / "sb002-relatte.commit"
    witness.parent.mkdir(parents=True)
    witness.write_text(
        GENERALITY["specimens"]["sb002"]["proof_commit"] + "\n", encoding="utf-8"
    )
    return image, persistent


class BardoBridgeTests(unittest.TestCase):
    def test_reports_two_proven_destroyed_membranes_without_live_query(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            result = MODULE.inspect(image, persistent)
            self.assertTrue(result["specimens"]["sb001"]["evidence_set_matches"])
            self.assertTrue(result["specimens"]["sb002"]["evidence_set_matches"])
            self.assertEqual(
                result["specimens"]["sb001"]["destination_disposition"], "ADMIT"
            )
            self.assertEqual(
                result["specimens"]["sb002"]["destination_disposition"], "HOLD"
            )
            self.assertFalse(result["specimens"]["sb002"]["render_authority"])
            self.assertTrue(result["specimens"]["sb002"]["commit_witness_matches"])
            self.assertFalse(result["live_membrane"]["queried"])
            self.assertEqual(
                result["live_membrane"]["unresolved_crossings"], "not-observed"
            )
            self.assertEqual(
                result["generality"]["extraction_gate"],
                "eligible-for-reconsideration-not-promoted",
            )

    def test_counts_only_escaped_durable_files(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            exports = persistent / "crossing-exports"
            (exports / "a.json").write_text("{}\n", encoding="utf-8")
            (exports / "nested").mkdir()
            (exports / "nested" / "b.json").write_text("{}\n", encoding="utf-8")
            result = MODULE.inspect(image, persistent)
            self.assertEqual(result["durability"]["durable_export_files"], 2)

    def test_refuses_persistent_bardo_interior(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            (persistent / "organs" / "supabardo").mkdir()
            with self.assertRaisesRegex(ValueError, "persistent SupaBardo"):
                MODULE.inspect(image, persistent)

    def test_refuses_substituted_sb002_evidence_set(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            path = (
                image
                / "opt/static-os/bardo-proofs/sb002-relatte/fixtures"
                / "sb002-evidence-manifest.json"
            )
            path.write_text(
                json.dumps({"evidence_set_id": "sb002-evidence-v0:" + "0" * 64}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "SB-002 evidence"):
                MODULE.inspect(image, persistent)

    def test_refuses_wrong_sb002_commit_witness(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            witness = (
                image
                / "usr/share/static-os/bardo-proofs/sb002-relatte.commit"
            )
            witness.write_text("0" * 40 + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "commit witness"):
                MODULE.inspect(image, persistent)


if __name__ == "__main__":
    unittest.main()
