"""Toaster-inspired witness projection and recomposer integration."""
import copy
import json
import unittest
from question_first.recomposer import genesis, compile_turn, observe_feedback
from question_first.recomposer_witness import (
    project_receipt_memory, compile_memory_capsule, compile_candidate_family,
    witness_artifact
)

class TestToasterWitnessRecomposer(unittest.TestCase):
    def setUp(self):
        self.state = genesis()
        self.plan = compile_turn(self.state, "music and food")

    def test_projection_is_derived_not_mutating(self):
        frozen = copy.deepcopy(self.state)
        a = project_receipt_memory(self.state)
        b = project_receipt_memory(self.state)
        self.assertEqual(a, b)
        self.assertEqual(self.state, frozen)
        self.assertEqual(a["total_verdicts"], 0)
        self.assertEqual(a["revision"], 0)

    def test_candidate_family_is_repeatable_and_bounded(self):
        a = compile_candidate_family(self.state, self.plan)
        b = compile_candidate_family(self.state, self.plan)
        self.assertEqual(a, b)
        self.assertLessEqual(len(a["candidates"]), 6)
        self.assertGreater(len(a["candidates"]), 1)
        self.assertTrue(all(x["requires_separate_choice"] for x in a["candidates"]))
        self.assertTrue(all(x["status"] == "PROPOSAL_ONLY" for x in a["candidates"]))
        self.assertEqual(a["accepted_candidate"], None)

    def test_no_unrelated_routes_or_prompt_copied(self):
        original = "music and food"
        family = compile_candidate_family(self.state, compile_turn(self.state, original))
        for candidate in family["candidates"]:
            self.assertTrue(set(candidate["routes"]).issubset(self.plan["topics"]))
        # Only controlled labels and hashes travel, not the original prompt.
        self.assertNotIn(original, json.dumps(family))
        self.assertEqual(family["toaster_execution_authority"], False)

    def test_witness_memory_changes_after_explicit_feedback(self):
        before = compile_candidate_family(self.state, self.plan)
        updated = observe_feedback(self.state, self.plan, "music", "helpful", consent=True)
        latest = compile_turn(updated, "music and food")
        after = compile_candidate_family(updated, latest)
        self.assertNotEqual(before["family_id"], after["family_id"])
        self.assertEqual(after["capsule"]["archive_cut"], updated["head"])
        self.assertIn("relationship-favor", after["influence_trace"]["pressure_kinds"])
        self.assertEqual(project_receipt_memory(updated)["helpful"]["music"], 1)
        self.assertEqual(self.state["revision"], 0)

    def test_repeated_use_causes_saturation_without_fake_success(self):
        s=self.state
        for i in range(3):
            p=compile_turn(s,"music and food")
            s=observe_feedback(s,p,"food","not_helpful",consent=True)
        family=compile_candidate_family(s,compile_turn(s,"music and food"))
        kinds=family["influence_trace"]["pressure_kinds"]
        self.assertIn("saturation-avoid", kinds)
        self.assertIn("counterexampled", kinds)
        self.assertNotIn("relationship-favor", kinds)
        self.assertEqual(project_receipt_memory(s)["not_helpful"]["food"], 3)

    def test_influence_trace_links_attributable_feedback_evidence(self):
        revised = observe_feedback(self.state,self.plan,"food","helpful",consent=True)
        family = compile_candidate_family(revised,compile_turn(revised,"music and food"))
        self.assertIn(revised["events"][0]["hash"],
                      family["influence_trace"]["evidence_refs"])
        self.assertTrue(family["influence_trace"]["trace_id"].startswith("witness-trace:"))

    def test_stale_plan_and_tamper_refused(self):
        revised = observe_feedback(self.state,self.plan,"music","helpful",consent=True)
        with self.assertRaisesRegex(ValueError,"STALE"):
            compile_candidate_family(revised,self.plan)
        changed=copy.deepcopy(self.plan)
        changed["doors"]=["https://attacker.invalid/"]
        with self.assertRaisesRegex(ValueError,"MISMATCH"):
            compile_candidate_family(self.state,changed)

    def test_single_relevant_topic_does_not_invent_six_variants(self):
        p=compile_turn(self.state,"music")
        family=compile_candidate_family(self.state,p)
        self.assertEqual(len(family["candidates"]),1)
        self.assertEqual(family["candidates"][0]["routes"],["music"])

    def test_unknown_topic_not_granted_artificial_authority(self):
        p=compile_turn(self.state,"???? mysterious whatever")
        f=compile_candidate_family(self.state,p)
        self.assertTrue(p["uncertain"])
        self.assertEqual(f["status"],"PROPOSAL_ONLY")
        self.assertTrue(all(c["external_effect"] is False for c in f["candidates"]))

    def test_every_created_artifact_can_change_coverage_without_verdict(self):
        # No thumbs-up or rating: source-controlled output is an observation,
        # not a quality judgment, external benefit or publication.
        receipt=witness_artifact(self.plan,"food","a"*64,consent=True)
        projection=project_receipt_memory(self.state,[receipt])
        self.assertEqual(projection["observed_artifacts"]["food"],1)
        self.assertEqual(projection["helpful"]["food"],0)
        capsule=compile_memory_capsule(self.state,self.plan,[receipt])
        exploration=[p["target"] for p in capsule["pressures"]
                     if p["kind"]=="coverage-explore"]
        self.assertEqual(exploration,["music"])
        self.assertIn(receipt["observation_id"],projection["sources"]["food"])
        family=compile_candidate_family(self.state,self.plan,[receipt])
        self.assertEqual(family["capsule"]["capsule_id"],capsule["capsule_id"])
        self.assertEqual(self.state["revision"],0)

    def test_artifact_memory_opt_in_and_tampering(self):
        with self.assertRaisesRegex(ValueError,"NOT_AUTHORIZED"):
            witness_artifact(self.plan,"food","b"*64)
        with self.assertRaisesRegex(ValueError,"INVALID_ARTIFACT_DIGEST"):
            witness_artifact(self.plan,"food","not-a-digest",consent=True)
        r=witness_artifact(self.plan,"music","b"*64,consent=True)
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            project_receipt_memory(self.state,[r,r])
        x=copy.deepcopy(r);x["topic"]="food"
        with self.assertRaisesRegex(ValueError,"MISMATCH"):
            project_receipt_memory(self.state,[x])

    def test_artifact_receipt_order_does_not_change_projection(self):
        a=witness_artifact(self.plan,"food","a"*64,consent=True)
        b=witness_artifact(self.plan,"music","b"*64,consent=True)
        self.assertEqual(project_receipt_memory(self.state,[a,b]),
                         project_receipt_memory(self.state,[b,a]))

    def test_negative_feedback_affects_future_compilation(self):
        state=self.state
        for _ in range(2):
            plan=compile_turn(state,"food and music")
            state=observe_feedback(state,plan,"food","not_helpful",consent=True)
        plan2=compile_turn(state,"food and music")
        self.assertEqual(plan2["topics"][0],"music")
        capsule=compile_memory_capsule(state,plan2)
        self.assertTrue(any(p["kind"]=="counterexampled" and p["target"]=="food"
                            for p in capsule["pressures"]))

if __name__ == "__main__":
    unittest.main()
