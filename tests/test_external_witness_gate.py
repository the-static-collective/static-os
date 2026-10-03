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


composed_fixture = load_module(
    "static_os_composed_world_fixture_for_external",
    "tests/test_composed_witness_to_world.py",
)
external = load_module(
    "static_os_world_external_witness_test",
    "scripts/world_external_witness.py",
)


def composed_candidate():
    *_, candidate, _ = composed_fixture.make_source()
    return candidate


def external_source():
    return {
        "schema": "static.external-witness-source/v0",
        "source_id": "outside-observer-001",
        "channel": "direct_observation",
        "claim_text": (
            "An outside observer recorded the target condition without receiving "
            "the composed-history prompt or experiment instruction."
        ),
        "claim_limit": (
            "This contract fixture represents an external source package; it does "
            "not externally authenticate the observation."
        ),
    }


def source_digest():
    return external.canonical_digest(external_source())


def selection_audit():
    digest = source_digest()
    return {
        "schema": "static.selection-path-audit/v0",
        "audit_id": "selection-audit-001",
        "candidate_source_sha256": digest,
        "criteria": {
            "question_origin": {
                "status": "preexisting_or_external",
                "evidence_sha256": "1" * 64,
            },
            "assignment_origin": {
                "status": "independently_assigned",
                "evidence_sha256": "2" * 64,
            },
            "hypothesis_exposure": {
                "status": "unexposed_to_composed_history",
                "evidence_sha256": "3" * 64,
            },
            "sampling_frame": {
                "status": "predeclared_or_external",
                "evidence_sha256": "4" * 64,
            },
        },
        "claim_limit": "Selection-path evidence is declared, not externally authenticated here.",
    }


def measurement_audit():
    digest = source_digest()
    return {
        "schema": "static.measurement-path-audit/v0",
        "audit_id": "external-measurement-audit-001",
        "candidate_source_sha256": digest,
        "criteria": {
            "channel_origin": {
                "status": "preexisting_or_external",
                "evidence_sha256": "5" * 64,
            },
            "capture_control": {
                "status": "not_controlled_by_orientation",
                "evidence_sha256": "6" * 64,
            },
            "result_selection": {
                "status": "result_blind_capture",
                "evidence_sha256": "7" * 64,
            },
            "operator_relation": {
                "status": "independent_or_automatic",
                "evidence_sha256": "8" * 64,
            },
        },
        "claim_limit": "Measurement-path evidence is declared, not externally authenticated here.",
    }


def comparison(relation="corroborates"):
    candidate = composed_candidate()
    return {
        "schema": "static.external-witness-comparison/v0",
        "composed_source_sha256": candidate["source_sha256"],
        "external_source_sha256": source_digest(),
        "claim_relation": relation,
        "relation_basis": "The source claims were compared without using agreement as an independence criterion.",
    }


class ExternalWitnessGateTests(unittest.TestCase):
    def test_all_independence_axes_pass_yields_external_witness_candidate(self):
        candidate = composed_candidate()
        receipt = external.classify(
            candidate,
            external_source(),
            selection_audit(),
            measurement_audit(),
            comparison(),
        )
        self.assertEqual(receipt["selection_independence"], "independent_candidate")
        self.assertEqual(receipt["measurement_independence"], "independent_candidate")
        self.assertEqual(receipt["lineage_class"], "independent_external_candidate")
        self.assertEqual(receipt["independent_witness_status"], "independent_witness_candidate")
        self.assertTrue(receipt["counts_as_independent_witness"])

    def test_corroboration_does_not_create_independence(self):
        candidate = composed_candidate()
        bad_selection = selection_audit()
        bad_selection["criteria"]["hypothesis_exposure"]["status"] = "unknown"
        receipt = external.classify(
            candidate,
            external_source(),
            bad_selection,
            measurement_audit(),
            comparison("corroborates"),
        )
        self.assertFalse(receipt["counts_as_independent_witness"])
        self.assertEqual(receipt["independent_witness_status"], "independence_not_established")
        self.assertEqual(receipt["relation_role"], "relation_without_independent_witness_status")

    def test_contradiction_can_be_equally_independent(self):
        candidate = composed_candidate()
        receipt = external.classify(
            candidate,
            external_source(),
            selection_audit(),
            measurement_audit(),
            comparison("contradicts"),
        )
        self.assertTrue(receipt["counts_as_independent_witness"])
        self.assertEqual(receipt["relation_role"], "independent_contradiction_candidate")

    def test_relation_does_not_change_provenance_classification(self):
        candidate = composed_candidate()
        roles = {}
        for relation in ("corroborates", "contradicts", "corrects", "unrelated"):
            receipt = external.classify(
                candidate,
                external_source(),
                selection_audit(),
                measurement_audit(),
                comparison(relation),
            )
            self.assertEqual(receipt["lineage_class"], "independent_external_candidate")
            self.assertTrue(receipt["counts_as_independent_witness"])
            roles[relation] = receipt["relation_role"]
        self.assertEqual(
            roles,
            {
                "corroborates": "independent_corroboration_candidate",
                "contradicts": "independent_contradiction_candidate",
                "corrects": "independent_correction_candidate",
                "unrelated": "independent_unrelated_source",
            },
        )

    def test_one_failed_measurement_criterion_blocks_external_witness(self):
        candidate = composed_candidate()
        bad_measurement = measurement_audit()
        bad_measurement["criteria"]["capture_control"]["status"] = "controlled_by_orientation"
        receipt = external.classify(
            candidate,
            external_source(),
            selection_audit(),
            bad_measurement,
            comparison(),
        )
        self.assertEqual(receipt["measurement_independence"], "not_independent")
        self.assertEqual(receipt["lineage_class"], "external_not_independent")
        self.assertFalse(receipt["counts_as_independent_witness"])

    def test_one_unknown_selection_criterion_blocks_external_witness(self):
        candidate = composed_candidate()
        bad_selection = selection_audit()
        bad_selection["criteria"]["question_origin"]["status"] = "unknown"
        receipt = external.classify(
            candidate,
            external_source(),
            bad_selection,
            measurement_audit(),
            comparison(),
        )
        self.assertEqual(receipt["selection_independence"], "unknown")
        self.assertEqual(receipt["lineage_class"], "external_independence_unknown")
        self.assertFalse(receipt["counts_as_independent_witness"])

    def test_external_source_must_be_distinct_from_composed_source(self):
        candidate = composed_candidate()
        source = external_source()
        # Monkeypatch source content until its digest is impossible to equal the composed hash
        # is unnecessary; instead ensure the real fixture is distinct.
        self.assertNotEqual(external.canonical_digest(source), candidate["source_sha256"])

    def test_selection_audit_cannot_self_certify(self):
        candidate = composed_candidate()
        bad = selection_audit()
        bad["criteria"]["question_origin"]["evidence_sha256"] = source_digest()
        with self.assertRaisesRegex(ValueError, "cannot self-certify"):
            external.classify(
                candidate,
                external_source(),
                bad,
                measurement_audit(),
                comparison(),
            )

    def test_composed_ancestry_cannot_impersonate_external_audit_evidence(self):
        candidate = composed_candidate()
        bad = selection_audit()
        bad["criteria"]["question_origin"]["evidence_sha256"] = (
            candidate["orientation_ancestry"]["source_generation_sha256"]
        )
        with self.assertRaisesRegex(ValueError, "impersonate composed ancestry"):
            external.classify(
                candidate,
                external_source(),
                bad,
                measurement_audit(),
                comparison(),
            )

    def test_audits_must_address_external_source(self):
        candidate = composed_candidate()
        bad = selection_audit()
        bad["candidate_source_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "selection audit source does not match"):
            external.classify(
                candidate,
                external_source(),
                bad,
                measurement_audit(),
                comparison(),
            )

    def test_comparison_must_address_both_sources(self):
        candidate = composed_candidate()
        bad = comparison()
        bad["composed_source_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "comparison composed source mismatch"):
            external.classify(
                candidate,
                external_source(),
                selection_audit(),
                measurement_audit(),
                bad,
            )

    def test_independent_witness_does_not_claim_truth(self):
        candidate = composed_candidate()
        receipt = external.classify(
            candidate,
            external_source(),
            selection_audit(),
            measurement_audit(),
            comparison("corroborates"),
        )
        limits = " ".join(receipt["does_not_establish"]).lower()
        self.assertIn("external source is correct", limits)
        self.assertIn("corroboration proves truth", limits)
        self.assertIn("independent provenance determines which claim should win", limits)

    def test_inspection_keeps_independence_separate_from_agreement(self):
        candidate = composed_candidate()
        receipt = external.classify(
            candidate,
            external_source(),
            selection_audit(),
            measurement_audit(),
            comparison("contradicts"),
        )
        inspection = external.inspect(receipt)
        self.assertTrue(inspection["counts_as_independent_witness"])
        self.assertEqual(inspection["claim_relation"], "contradicts")
        self.assertFalse(inspection["independence_collapsed_into_agreement"])
        self.assertFalse(inspection["truth_claimed"])
        self.assertTrue(inspection["typed_composed_origin_preserved"])

    def test_receipt_rejects_relation_role_laundering(self):
        candidate = composed_candidate()
        receipt = external.classify(
            candidate,
            external_source(),
            selection_audit(),
            measurement_audit(),
            comparison("contradicts"),
        )
        bad = copy.deepcopy(receipt)
        bad["relation_role"] = "independent_corroboration_candidate"
        with self.assertRaisesRegex(ValueError, "relation role contradicts"):
            external.validate_receipt(bad)


if __name__ == "__main__":
    unittest.main()
