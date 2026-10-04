import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


external_fixture = load_module(
    "static_os_external_witness_fixture_for_field",
    "tests/test_external_witness_gate.py",
)
external = load_module(
    "static_os_external_witness_for_field_test",
    "scripts/world_external_witness.py",
)
field = load_module(
    "static_os_world_witness_field_test",
    "scripts/world_witness_field.py",
)


def composed_candidate():
    return external_fixture.composed_candidate()


def make_source(index):
    return {
        "schema": "static.external-witness-source/v0",
        "source_id": f"outside-observer-{index:03d}",
        "channel": "direct_observation",
        "claim_text": f"Independent external witness claim {index}.",
        "claim_limit": "Contract fixture; source claim is not authenticated by this runtime.",
    }


def source_digest(source):
    return external.canonical_digest(source)


def make_selection(source, seed):
    digest = source_digest(source)
    chars = "123456789abcdef"
    return {
        "schema": "static.selection-path-audit/v0",
        "audit_id": f"selection-{seed}",
        "candidate_source_sha256": digest,
        "criteria": {
            "question_origin": {
                "status": "preexisting_or_external",
                "evidence_sha256": chars[(seed + 0) % len(chars)] * 64,
            },
            "assignment_origin": {
                "status": "independently_assigned",
                "evidence_sha256": chars[(seed + 1) % len(chars)] * 64,
            },
            "hypothesis_exposure": {
                "status": "unexposed_to_composed_history",
                "evidence_sha256": chars[(seed + 2) % len(chars)] * 64,
            },
            "sampling_frame": {
                "status": "predeclared_or_external",
                "evidence_sha256": chars[(seed + 3) % len(chars)] * 64,
            },
        },
        "claim_limit": "Selection evidence is structurally declared only.",
    }


def make_measurement(source, seed):
    digest = source_digest(source)
    chars = "abcdef123456789"
    return {
        "schema": "static.measurement-path-audit/v0",
        "audit_id": f"measurement-{seed}",
        "candidate_source_sha256": digest,
        "criteria": {
            "channel_origin": {
                "status": "preexisting_or_external",
                "evidence_sha256": chars[(seed + 0) % len(chars)] * 64,
            },
            "capture_control": {
                "status": "not_controlled_by_orientation",
                "evidence_sha256": chars[(seed + 1) % len(chars)] * 64,
            },
            "result_selection": {
                "status": "result_blind_capture",
                "evidence_sha256": chars[(seed + 2) % len(chars)] * 64,
            },
            "operator_relation": {
                "status": "independent_or_automatic",
                "evidence_sha256": chars[(seed + 3) % len(chars)] * 64,
            },
        },
        "claim_limit": "Measurement evidence is structurally declared only.",
    }


def make_receipt(index, relation):
    candidate = composed_candidate()
    source = make_source(index)
    comparison = {
        "schema": "static.external-witness-comparison/v0",
        "composed_source_sha256": candidate["source_sha256"],
        "external_source_sha256": source_digest(source),
        "claim_relation": relation,
        "relation_basis": f"Fixture relation for witness {index}.",
    }
    return external.classify(
        candidate,
        source,
        make_selection(source, index * 4),
        make_measurement(source, index * 4),
        comparison,
    )


def pair_audit(source_a, source_b, seed, status_override=None):
    a, b = sorted((source_a, source_b))
    chars = "9876543210abcdef"
    criteria = {
        "shared_source_ancestry": {
            "status": "no_shared_ancestor_evidence",
            "evidence_sha256": chars[(seed + 0) % len(chars)] * 64,
        },
        "operator_overlap": {
            "status": "distinct_or_automatic",
            "evidence_sha256": chars[(seed + 1) % len(chars)] * 64,
        },
        "capture_coordination": {
            "status": "not_coordinated",
            "evidence_sha256": chars[(seed + 2) % len(chars)] * 64,
        },
        "selection_coordination": {
            "status": "independently_selected",
            "evidence_sha256": chars[(seed + 3) % len(chars)] * 64,
        },
    }
    if status_override is not None:
        criterion, value = status_override
        criteria[criterion]["status"] = value
    return {
        "schema": "static.external-witness-pair-audit/v0",
        "audit_id": f"pair-{seed}",
        "source_a_sha256": a,
        "source_b_sha256": b,
        "criteria": criteria,
        "claim_limit": "Pairwise witness independence evidence is structurally declared only.",
    }


def make_three(relations=("corroborates", "corroborates", "contradicts")):
    candidate = composed_candidate()
    receipts = [
        make_receipt(1, relations[0]),
        make_receipt(2, relations[1]),
        make_receipt(3, relations[2]),
    ]
    sources = [receipt["external_source_sha256"] for receipt in receipts]
    pairs = [
        pair_audit(sources[0], sources[1], 1),
        pair_audit(sources[0], sources[2], 5),
        pair_audit(sources[1], sources[2], 9),
    ]
    witness_field = field.build_field(candidate["source_sha256"], receipts, pairs)
    receipt = field.classify(witness_field, receipts, pairs)
    return candidate, receipts, pairs, witness_field, receipt


class ExternalWitnessFieldTests(unittest.TestCase):
    def test_three_independent_witnesses_can_disagree_without_verdict(self):
        _, _, _, _, receipt = make_three()

        self.assertEqual(receipt["plurality_status"], "independent_plurality_candidate")
        self.assertEqual(receipt["field_state"], "disagreement_preserved")
        self.assertEqual(receipt["relation_counts"]["corroborates"], 2)
        self.assertEqual(receipt["relation_counts"]["contradicts"], 1)
        self.assertFalse(receipt["majority_rule_used"])
        self.assertEqual(receipt["verdict_status"], "withheld")

    def test_unanimous_relation_is_convergence_not_truth(self):
        _, _, _, _, receipt = make_three(
            ("corroborates", "corroborates", "corroborates")
        )

        self.assertEqual(receipt["field_state"], "convergence_without_verdict")
        self.assertEqual(receipt["relation_counts"]["corroborates"], 3)
        self.assertEqual(receipt["verdict_status"], "withheld")
        limits = " ".join(receipt["does_not_establish"]).lower()
        self.assertIn("most common relation is true", limits)
        self.assertIn("majority of witnesses determines a verdict", limits)

    def test_pairwise_shared_lineage_blocks_independent_plurality(self):
        candidate, receipts, pairs, _, _ = make_three()
        bad_pairs = copy.deepcopy(pairs)
        bad_pairs[0]["criteria"]["operator_overlap"]["status"] = "shared_operator"

        witness_field = field.build_field(
            candidate["source_sha256"], receipts, bad_pairs
        )
        receipt = field.classify(witness_field, receipts, bad_pairs)

        self.assertEqual(receipt["plurality_status"], "shared_external_lineage")
        self.assertEqual(receipt["field_state"], "plurality_not_established")
        self.assertEqual(receipt["pair_audit_summary"]["failed"], 1)
        self.assertFalse(receipt["majority_rule_used"])

    def test_unknown_pairwise_independence_blocks_plurality(self):
        candidate, receipts, pairs, _, _ = make_three()
        unknown_pairs = copy.deepcopy(pairs)
        unknown_pairs[1]["criteria"]["shared_source_ancestry"]["status"] = "unknown"

        witness_field = field.build_field(
            candidate["source_sha256"], receipts, unknown_pairs
        )
        receipt = field.classify(witness_field, receipts, unknown_pairs)

        self.assertEqual(
            receipt["plurality_status"],
            "inter_witness_independence_unknown",
        )
        self.assertEqual(receipt["field_state"], "plurality_not_established")
        self.assertEqual(receipt["pair_audit_summary"]["unknown"], 1)

    def test_every_pair_must_be_audited(self):
        candidate, receipts, pairs, _, _ = make_three()
        with self.assertRaisesRegex(ValueError, "cover every external witness pair"):
            field.build_field(
                candidate["source_sha256"],
                receipts,
                pairs[:-1],
            )

    def test_individually_unqualified_source_cannot_enter_field(self):
        candidate, receipts, pairs, _, _ = make_three()
        bad_receipts = copy.deepcopy(receipts)
        bad_receipts[0]["counts_as_independent_witness"] = False
        bad_receipts[0]["selection_independence"] = "unknown"
        bad_receipts[0]["lineage_class"] = "external_independence_unknown"
        bad_receipts[0]["independent_witness_status"] = "independence_not_established"
        bad_receipts[0]["relation_role"] = "relation_without_independent_witness_status"

        with self.assertRaisesRegex(ValueError, "only admit qualified"):
            field.build_field(candidate["source_sha256"], bad_receipts, pairs)

    def test_relation_count_majority_cannot_be_relabelled_as_verdict(self):
        _, _, _, _, receipt = make_three()
        bad = copy.deepcopy(receipt)
        bad["majority_rule_used"] = True

        with self.assertRaisesRegex(ValueError, "cannot use majority rule"):
            field.validate_receipt(bad)

        bad = copy.deepcopy(receipt)
        bad["verdict_status"] = "corroborated"
        with self.assertRaisesRegex(ValueError, "verdict must remain withheld"):
            field.validate_receipt(bad)

    def test_mixed_relevance_is_preserved(self):
        _, _, _, _, receipt = make_three(
            ("corroborates", "unrelated", "unrelated")
        )
        self.assertEqual(receipt["field_state"], "mixed_relevance")
        self.assertEqual(receipt["verdict_status"], "withheld")

    def test_pair_audit_cannot_self_certify(self):
        _, receipts, pairs, _, _ = make_three()
        bad = copy.deepcopy(pairs[0])
        bad["criteria"]["capture_coordination"]["evidence_sha256"] = (
            bad["source_a_sha256"]
        )
        with self.assertRaisesRegex(ValueError, "cannot self-certify"):
            field.validate_pair_audit(bad)

    def test_field_is_order_invariant(self):
        candidate, receipts, pairs, witness_field, _ = make_three()
        reversed_field = field.build_field(
            candidate["source_sha256"],
            list(reversed(receipts)),
            list(reversed(pairs)),
        )
        self.assertEqual(
            field.canonical_digest(witness_field),
            field.canonical_digest(reversed_field),
        )

    def test_duplicate_witness_source_is_refused(self):
        candidate, receipts, pairs, _, _ = make_three()
        duplicate = [receipts[0], receipts[0]]
        source = receipts[0]["external_source_sha256"]
        fake_pair = pair_audit(source, "f" * 64, 12)
        with self.assertRaisesRegex(ValueError, "duplicate external witness source"):
            field.build_field(
                candidate["source_sha256"],
                duplicate,
                [fake_pair],
            )

    def test_inspection_allows_disagreement_and_claims_no_truth(self):
        _, _, _, _, receipt = make_three()
        inspection = field.inspect(receipt)

        self.assertTrue(inspection["disagreement_allowed"])
        self.assertFalse(inspection["majority_rule_used"])
        self.assertEqual(inspection["verdict_status"], "withheld")
        self.assertFalse(inspection["truth_claimed"])
        self.assertTrue(inspection["typed_composed_origin_preserved"])

    def test_relation_counts_must_match_witness_count(self):
        _, _, _, _, receipt = make_three()
        bad = copy.deepcopy(receipt)
        bad["relation_counts"]["corroborates"] += 1
        with self.assertRaisesRegex(ValueError, "do not match witness count"):
            field.validate_receipt(bad)


if __name__ == "__main__":
    unittest.main()
