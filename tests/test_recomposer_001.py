"""RECOMPOSER-001: deterministic recomposition and refusal contract."""
import copy
import unittest
from question_first.recomposer import genesis, compile_turn, observe_feedback, verify_state

class TestRecomposer(unittest.TestCase):
    def test_same_input_and_state_same_graph(self):
        s = genesis()
        self.assertEqual(compile_turn(s, "Food and music"), compile_turn(s, "Food and music"))
    def test_assembly_changes_with_question(self):
        s=genesis()
        a=compile_turn(s,"I want to sing a song")
        b=compile_turn(s,"My vegetable garden is growing")
        self.assertNotEqual(a["operators"],b["operators"])
        self.assertIn("https://abundent.org/jubilee/",a["doors"])
        self.assertIn("https://garden.abundent.org/",b["doors"])
    def test_compound_recipe_proposed_not_automatically_promoted(self):
        s=genesis()
        p=compile_turn(s,"What if food and music happen at a table?")
        self.assertIsNotNone(p["candidate_recipe"])
        self.assertEqual(s["recipes"],[])
        self.assertEqual(p["status"],"PROPOSAL_ONLY")
    def test_explicit_promotion_reuses_macro_with_smaller_graph(self):
        s=genesis();p=compile_turn(s,"music and food")
        n=observe_feedback(s,p,p["topics"][0],"helpful",consent=True,promote_recipe=True)
        later=compile_turn(n,"music and food")
        self.assertEqual(later["reused_recipe"],p["candidate_recipe"])
        self.assertLess(later["operator_count"],p["operator_count"])
        self.assertTrue(any(x["id"].startswith("join:") for x in later["operators"]))
        self.assertEqual(s["revision"],0)
        verify_state(n)
    def test_feedback_can_change_future_ranking(self):
        s=genesis();p=compile_turn(s,"music and food")
        self.assertEqual(p["topics"][0],"food")
        n=observe_feedback(s,p,"music","helpful",consent=True)
        self.assertEqual(compile_turn(n,"music and food")["topics"][0],"music")
    def test_nonconsensual_feedback_and_unselected_route_refused(self):
        s=genesis();p=compile_turn(s,"music and food")
        with self.assertRaises(ValueError):
            observe_feedback(s,p,p["topics"][0],"helpful")
        with self.assertRaises(ValueError):
            observe_feedback(s,p,"paper","helpful",consent=True)
    def test_stale_plan_refused(self):
        s=genesis();p=compile_turn(s,"music and food")
        n=observe_feedback(s,p,"music","helpful",consent=True)
        with self.assertRaisesRegex(ValueError,"STALE"):
            observe_feedback(n,p,"music","helpful",consent=True)
    def test_replay_detects_mutated_event_and_weights(self):
        s=genesis();p=compile_turn(s,"music and food")
        n=observe_feedback(s,p,"music","helpful",consent=True)
        x=copy.deepcopy(n);x["weights"]["music"]=5
        with self.assertRaises(ValueError): verify_state(x)
        x=copy.deepcopy(n);x["events"][0]["selected"]="food"
        with self.assertRaises(ValueError): verify_state(x)
    def test_unknown_question_remains_uncertain(self):
        p=compile_turn(genesis(),"zyxwvplunk foobar")
        self.assertTrue(p["uncertain"])
        self.assertEqual(p["status"],"PROPOSAL_ONLY")
    def test_input_budget(self):
        for q in ("","a"*321):
            with self.assertRaises(ValueError): compile_turn(genesis(),q)
    def test_negative_feedback_does_not_activate_recipe(self):
        s=genesis();p=compile_turn(s,"music")
        n=observe_feedback(s,p,"music","not_helpful",consent=True)
        self.assertEqual(n["weights"]["music"],-2)
        self.assertEqual(n["recipes"],[])

if __name__ == "__main__":
    unittest.main()
