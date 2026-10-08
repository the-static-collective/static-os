"""APPARATUS-COMPILER-002: questions which NEED new instruments.

Dedicated CI must supply GHOT_SRC at a pinned commit. The test executes the
actual GHoT signed Instrument Rack; it never constructs a fake receipt.
"""
from __future__ import annotations
import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from question_first.apparatus_donor import DIRECT, GEARED, run as donor
from question_first.apparatus_compiler import (
    APPROVAL, CATALOG_WITNESS, NEEDS, STATE, Hold, _sealed,
    _state, _state_file, _write_new, compile_apparatus,
    execute_selected, replay_state, validate_seed, verify_plan,
)
from question_first.session import discover_ghot

ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads((ROOT / "fixtures/apparatus-002/source-grounded-question.json").read_text())
MANIFEST_001 = ROOT / "integrations/question-first-001/adapter-manifest.json"
MANIFEST_002 = ROOT / "integrations/apparatus-002/adapter-manifest.json"


class ApparatusCompiler002Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="static-apparatus-")
        self.root = Path(self.temp.name)
        self.ghot = Path(os.environ["GHOT_SRC"]) if os.environ.get("GHOT_SRC") else None
        self.saved = {k: os.environ.get(k)
                      for k in ("GHOT_HOME", "GHOT_ADAPTER_MANIFESTS")}
        os.environ["GHOT_HOME"] = str(self.root / "ghot")
        os.environ["GHOT_ADAPTER_MANIFESTS"] = str(MANIFEST_002)

    def tearDown(self):
        for key, prior in self.saved.items():
            if prior is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prior
        self.temp.cleanup()

    def require_ghot(self):
        if self.ghot is None:
            self.skipTest("Requires pinned GHOT_SRC checkout; dedicated CI must provide")
        self.assertTrue((self.ghot / "ghot/instrument_rack.py").is_file())

    def plan(self, seed=SEED):
        self.require_ghot()
        return compile_apparatus(seed, discover_ghot(self.ghot))

    def selected(self, plan, candidate="gear-then-screw", approved=True):
        choice = next(x for x in plan["assembly_candidates"]
                      if x["candidate_id"] == candidate)
        return {
            "schema": APPROVAL, "plan_id": plan["plan_id"],
            "candidate_id": candidate, "executor_card_id": choice["executor_card_id"],
            "approved": approved, "owner_id": "human-reviewer",
        }

    def test_donor_direct_and_composite_are_distinct_and_pure(self):
        req = {
            "schema": "static-os.apparatus-input/v0", "mode": "geared",
            "driver_teeth": 12, "driven_teeth": 36,
            "input_turns": 6, "lead_um_per_turn": 1500,
            "source_ref": "apparatus-source-v0:" + "a" * 64,
        }
        geared = donor(req, GEARED)
        direct = donor({**req, "mode": "direct"}, DIRECT)
        self.assertEqual(geared["output_axial_um"], {"numerator": -3000, "denominator": 1})
        self.assertEqual(direct["output_axial_um"], {"numerator": 9000, "denominator": 1})
        self.assertEqual(geared["instrument_steps"],
                         ["IDEAL_GEAR_RATIO", "IDEAL_LEADSCREW_TRANSLATION"])
        self.assertEqual(direct["instrument_steps"], ["IDEAL_LEADSCREW_TRANSLATION"])
        self.assertFalse(geared["physical_execution"])
        self.assertFalse(direct["historical_reconstruction"])

    def test_donor_hostile_input_refusal(self):
        base = {
            "schema": "static-os.apparatus-input/v0", "mode": "geared",
            "driver_teeth": 12, "driven_teeth": 36, "input_turns": 6,
            "lead_um_per_turn": 1500, "source_ref": "apparatus-source-v0:" + "a" * 64,
        }
        for bad in (
            {**base, "mode": "direct"},
            {**base, "driver_teeth": True},
            {**base, "lead_um_per_turn": -4},
            {**base, "input_turns": 999},
            {**base, "transmit": True},
            {**base, "source_ref": "proof:leo"},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                donor(bad, GEARED)

    def test_source_catalog_is_grounded_but_technical_model_not_attributed(self):
        self.assertEqual(validate_seed(SEED), SEED)
        self.assertEqual(CATALOG_WITNESS["folio"], "Codex Atlanticus f. 1069 recto")
        self.assertFalse(CATALOG_WITNESS["source_image_bytes_verified"])
        self.assertFalse(CATALOG_WITNESS["exact_gear_leadscrew_assembly_depicted"])
        for altered in (
            {**SEED, "source_witness": {**CATALOG_WITNESS, "source_image_bytes_verified": True}},
            {**SEED, "source_witness": {**CATALOG_WITNESS, "folio": "made-up folio"}},
            {**SEED, "source_witness": {**CATALOG_WITNESS, "exact_gear_leadscrew_assembly_depicted": True}},
            {**SEED, "source_witness": {**CATALOG_WITNESS, "source_image_sha256": "a" * 64}},
            {**SEED, "construction_permission": True},
            {**SEED, "driver_teeth": False},
        ):
            with self.subTest(altered=altered), self.assertRaises(Hold):
                validate_seed(altered)

    def test_original_001_instrument_field_cannot_answer_axial_question(self):
        self.require_ghot()
        os.environ["GHOT_ADAPTER_MANIFESTS"] = str(MANIFEST_001)
        old_rack = discover_ghot(self.ghot)
        missing = compile_apparatus(SEED, old_rack)
        self.assertEqual(missing["status"], "NEEDS_NEW_INSTRUMENT")
        self.assertEqual(set(missing["missing_capabilities"]), {DIRECT, GEARED})
        self.assertEqual(missing["assembly_candidates"], [])
        self.assertEqual(missing["physical_effects"], False)
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())
        with self.assertRaisesRegex(Hold, "UNMET_APPARATUS_CAPABILITY_GAP"):
            execute_selected(missing, {
                "schema": APPROVAL, "approved": True, "plan_id": missing["plan_id"],
                "candidate_id": "gear-then-screw", "executor_card_id": "not-a-card",
                "owner_id": "human-reviewer",
            }, ghot_root=self.ghot, state_dir=self.root / "none")

    def test_new_capabilities_produce_two_typed_graphs_without_running(self):
        plan = self.plan()
        self.assertEqual(plan["status"], "PROPOSAL_ONLY")
        self.assertEqual(plan["missing_capabilities"], [])
        self.assertEqual(len(plan["assembly_candidates"]), 2)
        first, second = plan["assembly_candidates"]
        self.assertEqual([n["id"] for n in first["nodes"]], ["screw"])
        self.assertEqual([n["id"] for n in second["nodes"]], ["gear", "screw"])
        self.assertEqual(second["nodes"][0]["output"], second["nodes"][1]["input"])
        self.assertEqual(second["submodule_dispatches"], 0)
        self.assertTrue(second["simulation_only"])
        self.assertEqual(verify_plan(plan), plan)
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())

    def test_modified_graph_or_stale_cards_are_refused(self):
        self.require_ghot()
        rack = discover_ghot(self.ghot)
        plan = compile_apparatus(SEED, rack)
        changed = copy.deepcopy(plan)
        changed["assembly_candidates"][1]["nodes"][0]["output"] = "INVENTED_ENERGY"
        with self.assertRaises(Hold):
            verify_plan(changed)
        changed = copy.deepcopy(plan)
        changed["assembly_candidates"][1]["nodes"][0]["output"] = "INVENTED_ENERGY"
        changed = _sealed({k: v for k, v in changed.items() if k != "plan_id"},
                          "plan_id", "static-os-apparatus-plan-v0:")
        with self.assertRaises(Hold):
            verify_plan(changed)
        unsafe = copy.deepcopy(rack)
        for card in unsafe["cards"]:
            if card.get("capability") == GEARED:
                card["limits"]["physical_effects"] = True
        with self.assertRaises(Hold):
            compile_apparatus(SEED, unsafe)
        no_gear = copy.deepcopy(rack)
        no_gear["cards"] = [c for c in no_gear["cards"]
                            if c.get("capability") != "mechanism.gear.forward.simulate"]
        self.assertEqual(compile_apparatus(SEED, no_gear)["status"], "NEEDS_NEW_INSTRUMENT")

    def test_explicit_selection_refuses_forged_or_stale_approvals(self):
        self.require_ghot()
        plan = self.plan()
        selected = self.selected(plan)
        for bad in (
            {**selected, "approved": 1},
            {**selected, "approved": False},
            {**selected, "candidate_id": "not-offered"},
            {**selected, "executor_card_id": "stale"},
            {**selected, "plan_id": "other"},
            {**selected, "owner_id": "inject;drop"},
            {**selected, "next_turn": "execute-now"},
        ):
            with self.subTest(bad=bad), self.assertRaises(Hold):
                execute_selected(plan, bad, ghot_root=self.ghot,
                                 state_dir=self.root / "refused")
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())

    def test_native_signed_dispatch_independent_math_and_cold_replay(self):
        self.require_ghot()
        plan = self.plan()
        chosen = self.selected(plan)
        state_dir = self.root / "executed"
        first = execute_selected(plan, chosen, ghot_root=self.ghot, state_dir=state_dir)
        state = first["state"]
        self.assertFalse(first["replayed"])
        self.assertEqual(state["observation"]["axial_um"],
                         {"numerator": -3000, "denominator": 1})
        self.assertEqual(state["observation"]["disposition"], "IDEAL_CLAIM_CONTRADICTED")
        self.assertEqual(state["next_question"]["status"], "PROPOSAL_ONLY")
        self.assertEqual(state["next_question"]["proposed_candidate"], "direct-screw")
        self.assertFalse(state["real_hardware"])
        self.assertFalse(state["next_turn_executed"])
        self.assertEqual(state["native_result"]["packet"]["status"], "PORTABLE_NOT_ADMITTED")
        before = sorted((self.root / "ghot" / "instrument-rack" / "dispatches").iterdir())
        self.assertEqual(len(before), 1)
        cold = replay_state(_state_file(state_dir, plan), ghot_root=self.ghot)
        self.assertEqual(cold, state)
        same = execute_selected(plan, chosen, ghot_root=self.ghot, state_dir=state_dir)
        self.assertTrue(same["replayed"])
        self.assertEqual(same["state"], state)
        self.assertEqual(sorted((self.root / "ghot" / "instrument-rack" / "dispatches").iterdir()), before)

    def test_competing_apparatuses_produce_different_outcomes(self):
        self.require_ghot()
        plan = self.plan()
        direct = execute_selected(plan, self.selected(plan, "direct-screw"),
                                  ghot_root=self.ghot, state_dir=self.root / "direct")
        geared = execute_selected(plan, self.selected(plan, "gear-then-screw"),
                                  ghot_root=self.ghot, state_dir=self.root / "geared")
        self.assertEqual(direct["state"]["observation"]["disposition"], "IDEAL_CLAIM_MATCH")
        self.assertEqual(geared["state"]["observation"]["disposition"], "IDEAL_CLAIM_CONTRADICTED")
        self.assertNotEqual(direct["state"]["observation"]["native_packet_id"],
                            geared["state"]["observation"]["native_packet_id"])
        self.assertEqual(direct["state"]["next_question"]["action"], "NONE")

    def test_ambiguous_prepared_cannot_retry_even_with_owner_approval(self):
        self.require_ghot()
        plan = self.plan()
        selected = self.selected(plan)
        chosen = plan["assembly_candidates"][1]
        state_dir = self.root / "interrupted"
        _write_new(_state_file(state_dir, plan), _state({
            "schema": STATE, "stage": "PREPARED",
            "plan": plan, "selection": selected, "chosen": chosen,
            "auto_retry": False,
        }))
        with self.assertRaisesRegex(Hold, "NO_AUTORETRY"):
            execute_selected(plan, selected, ghot_root=self.ghot, state_dir=state_dir)
        with self.assertRaises(Hold):
            replay_state(_state_file(state_dir, plan), ghot_root=self.ghot)
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())

    def test_tampered_signed_packet_refuses_even_with_rehashed_local_state(self):
        self.require_ghot()
        plan = self.plan()
        state_dir = self.root / "tamper"
        result = execute_selected(plan, self.selected(plan), ghot_root=self.ghot,
                                  state_dir=state_dir)
        corrupted = copy.deepcopy(result["state"])
        corrupted["native_result"]["packet"]["donor_result"]["result"]["output_axial_um"]["numerator"] = 888
        path = _state_file(state_dir, plan)
        path.write_text(json.dumps(_state({k: v for k, v in corrupted.items()
                                           if k != "state_id"})))
        with self.assertRaises(Hold):
            replay_state(path, ghot_root=self.ghot)

    def test_operator_cli_compile_and_explicit_execute(self):
        self.require_ghot()
        script = ROOT / "scripts/apparatus-compiler.py"
        seed_file = ROOT / "fixtures/apparatus-002/source-grounded-question.json"
        plan_file = self.root / "plan.json"
        selection_file = self.root / "selection.json"
        result_file = self.root / "result.json"
        state_dir = self.root / "cli-state"
        cmd = [sys.executable, str(script)]
        def call(*opts):
            return subprocess.run(cmd + list(opts), capture_output=True, text=True)
        common = ["--ghot-root", str(self.ghot)]
        planned = call("compile", *common, "--seed", str(seed_file), "--out", str(plan_file))
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertEqual(stat.S_IMODE(plan_file.stat().st_mode), 0o600)
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())
        plan = json.loads(plan_file.read_text())["plan"]
        selection_file.write_text(json.dumps(self.selected(plan)))
        do = ["execute", *common, "--plan", str(plan_file),
              "--selection", str(selection_file), "--state-dir", str(state_dir),
              "--out", str(result_file)]
        executed = call(*do)
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(json.loads(result_file.read_text())["state"]["stage"], "COMPLETED")
        denied = call(*do)
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("OUTPUT_OCCUPIED", denied.stderr)
        self.assertEqual(len(list((self.root / "ghot" / "instrument-rack" / "dispatches").iterdir())), 1)
        replayed = call("replay", *common, "--state", str(_state_file(state_dir, plan)),
                        "--out", str(self.root / "replay.json"))
        self.assertEqual(replayed.returncode, 0, replayed.stderr)
        self.assertTrue(json.loads((self.root / "replay.json").read_text())["read_only_replay"])


if __name__ == "__main__":
    unittest.main()
