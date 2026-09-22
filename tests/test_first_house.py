"""First House desktop flavor: contract checks only; no installation or game effects."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "packaging/desktop/first-house.json"
spec = importlib.util.spec_from_file_location("first_house_validation", ROOT / "scripts/validate-first-house.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class FirstHouseDesktopTests(unittest.TestCase):
    def data(self):
        return json.loads(DECLARATION.read_text(encoding="utf-8"))

    def test_release_claims_and_exact_source(self):
        data = self.data()
        sha = validator.validate(data)
        self.assertEqual(sha, "38d8840c053d3675818ac3b8b74ab56731434bd7")
        self.assertEqual(data["workbench"]["start_route"], "/arg")
        self.assertEqual(data["claims"]["cross_project_game"], "not-integrated")

    def test_reject_unpinned_source_unearned_gates_and_auto_seed(self):
        for mutate in (
            lambda d: d["workbench"].update(source_commit="main"),
            lambda d: d["workbench"].update(start_route="/"),
            lambda d: d["workbench"].update(required_assets=["arg.html"]),
            lambda d: d["claims"].update(physical_install="verified"),
            lambda d: d["user_data"].update(auto_seed=True),
        ):
            with self.subTest(mutate=mutate):
                data = self.data()
                mutate(data)
                with self.assertRaises(ValueError):
                    validator.validate(data)

    def test_shell_syntax_and_explicit_mode(self):
        script = ROOT / "scripts/build-desktop-deb.sh"
        subprocess.run(["bash", "-n", str(script)], check=True)
        source = script.read_text(encoding="utf-8")
        self.assertIn('if [[ "$MODE" = "--first-house" ]]', source)
        self.assertIn('python3 "$ROOT/scripts/validate-manifest.py"', source)
        self.assertIn('python3 "$ROOT/scripts/validate-first-house.py"', source)
        self.assertIn('git -C "$BUILD/source" checkout --detach "$SHA"', source)
        self.assertIn('SELF_TEST=(--self-test --first-house)', source)
        self.assertIn('first-house.json" "$PKG/opt/static-workbench/first-house.json"', source)

    def test_desktop_entry_and_bundled_route_self_test(self):
        entry = (ROOT / "packaging/desktop/static-first-house.desktop").read_text(encoding="utf-8")
        launcher = (ROOT / "packaging/desktop/launch.py").read_text(encoding="utf-8")
        self.assertIn(" --first-house", entry)
        self.assertIn("start_route = '/arg' if '--first-house' in sys.argv else '/'", launcher)
        self.assertIn("{'/arg', '/arg/world'} <= paths", launcher)
        self.assertIn("'arg-world.js'", launcher)

    def test_original_iso_elf_pins_are_untouched_by_desktop_only_source(self):
        data = self.data()
        genesis = json.loads((ROOT / "manifest/genesis-001.json").read_text(encoding="utf-8"))
        triad = json.loads((ROOT / "interop/triad-001.json").read_text(encoding="utf-8"))
        flight = json.loads((ROOT / "interop/flight-003.json").read_text(encoding="utf-8"))
        old = genesis["house"]["commit"]
        self.assertEqual(old, genesis["elf"]["source_commit"])
        self.assertEqual(old, triad["sources"][2]["commit"])
        self.assertEqual(old, flight["candidate"]["house_source_commit"])
        self.assertNotEqual(old, data["workbench"]["source_commit"])


if __name__ == "__main__":
    unittest.main()
