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

MANIFEST = json.loads((ROOT / "manifest" / "whole-body-001.json").read_text(encoding="utf-8"))


def fixture(base: Path):
    image = base / "image"
    persistent = base / "persistent"
    share = image / "usr" / "share" / "static-os"
    relatte = image / "opt" / "static-os" / "organs" / "relatte"
    share.mkdir(parents=True)
    persistent.mkdir()
    (persistent / "crossing-exports").mkdir()
    (persistent / "organs").mkdir()

    (share / "whole-body-001.json").write_text(
        json.dumps(MANIFEST), encoding="utf-8"
    )
    proof = next(row for row in MANIFEST["organs"] if row["id"] == "supabardo")["proof"]
    evidence = {
        "schema": "supabardo.sb001-evidence-manifest/v0",
        "body": {},
        "evidence_set_id": proof["evidence_set_id"],
    }
    (relatte / "fixtures").mkdir(parents=True)
    (relatte / "scripts").mkdir(parents=True)
    (relatte / "docs").mkdir(parents=True)
    (relatte / "fixtures" / "sb001-evidence-manifest.json").write_text(
        json.dumps(evidence), encoding="utf-8"
    )
    (relatte / "scripts" / "sb001-verify.ts").write_text("fixture\n", encoding="utf-8")
    (relatte / "docs" / "SUPABARDO-SB-001.md").write_text("fixture\n", encoding="utf-8")
    return image, persistent


class BardoBridgeTests(unittest.TestCase):
    def test_reports_proven_destroyed_membrane_without_querying_live_service(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            result = MODULE.inspect(image, persistent)
            self.assertEqual(
                result["sb001"]["status"],
                "proven-external-destructible-specimen",
            )
            self.assertTrue(result["sb001"]["evidence_set_matches"])
            self.assertTrue(result["sb001"]["runtime_destroyed_after_export"])
            self.assertFalse(result["sb001"]["reconstruction_requires_live_membrane"])
            self.assertFalse(result["live_membrane"]["queried"])
            self.assertEqual(result["live_membrane"]["unresolved_crossings"], "not-observed")
            self.assertTrue(result["durability"]["boundary_ok"])

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

    def test_refuses_substituted_evidence_set(self):
        with tempfile.TemporaryDirectory() as directory:
            image, persistent = fixture(Path(directory))
            path = image / "opt/static-os/organs/relatte/fixtures/sb001-evidence-manifest.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["evidence_set_id"] = "sb001-evidence-v0:" + "0" * 64
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                MODULE.inspect(image, persistent)


if __name__ == "__main__":
    unittest.main()
