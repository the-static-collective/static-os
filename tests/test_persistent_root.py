import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config" / "includes.chroot" / "usr" / "local" / "bin" / "static-persist"
LOADER = importlib.machinery.SourceFileLoader("static_persist", str(SCRIPT))
SPEC = importlib.util.spec_from_loader("static_persist", LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class PersistentRootTests(unittest.TestCase):
    def env(self, base: Path):
        root = base / "persistent"
        share = base / "share"
        run = base / "run"
        root.mkdir()
        share.mkdir()
        for name in ("genesis-001.json", "whole-body-001.json", "persistent-root-001.json"):
            (share / name).write_text('{"fixture":true}\n', encoding="utf-8")
        return root, share, run

    def test_two_boots_keep_root_identity_but_not_boot_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            root, share, run=self.env(base)
            with patch.dict(os.environ, {
                "STATIC_OS_PERSIST_TEST":"1",
                "STATIC_OS_PERSIST_ROOT":str(root),
                "STATIC_OS_SHARE_ROOT":str(share),
                "STATIC_OS_RUN_ROOT":str(run),
            }):
                one=MODULE.open_boot(root, share, run)
                specimen=root / "organs" / "tranchnode" / "particular.txt"
                specimen.write_text("survives\n", encoding="utf-8")
                MODULE.close_boot(root, run)
                two=MODULE.open_boot(root, share, run)

                self.assertEqual(one["root_id"], two["root_id"])
                self.assertNotEqual(one["boot_id"], two["boot_id"])
                self.assertEqual(two["previous_boot_id"], one["boot_id"])
                self.assertTrue(two["previous_boot_has_shutdown_receipt"])
                self.assertFalse(two["claims"]["same_process"])
                self.assertEqual(specimen.read_text(encoding="utf-8"), "survives\n")

    def test_unclean_predecessor_remains_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            root, share, run=self.env(base)
            with patch.dict(os.environ, {"STATIC_OS_PERSIST_TEST":"1"}):
                one=MODULE.open_boot(root, share, run)
                two=MODULE.open_boot(root, share, run)
                self.assertEqual(two["previous_boot_id"], one["boot_id"])
                self.assertFalse(two["previous_boot_has_shutdown_receipt"])

    def test_supabardo_has_no_persistent_interior(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.dict(os.environ, {"STATIC_OS_PERSIST_TEST":"1"}):
                MODULE.init_root(root)
            self.assertFalse((root / "organs" / "supabardo").exists())
            self.assertTrue((root / "crossing-exports").is_dir())

    def test_refuses_nonempty_uninitialized_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root / "mystery").write_text("unknown", encoding="utf-8")
            with patch.dict(os.environ, {"STATIC_OS_PERSIST_TEST":"1"}):
                with self.assertRaisesRegex(ValueError, "not empty"):
                    MODULE.init_root(root)

    def test_refuses_unknown_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            value={
                "schema": MODULE.ROOT_SCHEMA,
                "layout_version": 99,
                "root_id": "11111111-1111-4111-8111-111111111111",
                "filesystem_label": "STATIC_STATE",
                "created_at": "fixture",
            }
            (root / "root.json").write_text(json.dumps(value), encoding="utf-8")
            with patch.dict(os.environ, {"STATIC_OS_PERSIST_TEST":"1"}):
                with self.assertRaisesRegex(ValueError, "layout"):
                    MODULE.init_root(root)

    def test_attach_user_refuses_existing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            root=base / "root"
            home=base / "home"
            root.mkdir()
            home.mkdir()
            with patch.dict(os.environ, {"STATIC_OS_PERSIST_TEST":"1"}):
                MODULE.init_root(root)
                state=home / ".local" / "state" / "static-workbench"
                state.mkdir(parents=True)
                with self.assertRaisesRegex(ValueError, "refusing"):
                    MODULE.attach_user(root, home, 1000)


if __name__ == "__main__":
    unittest.main()
