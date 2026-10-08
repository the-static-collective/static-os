from dataclasses import replace
from fractions import Fraction
import json
import unittest

from experiment import fixture, radio, run, TARGET, NOW
from infinite_radio import (
    Address, AttentionSelection, AuthorityGate, ControlMap, CURVES, Denied, Dial,
    FrequencySelection, Signal, TransmissionRequest, digest, replay,
)


class AddressTests(unittest.TestCase):
    def test_every_three_level_address_is_distinct_and_partitions_the_domain(self):
        cells = [Address((a, b, c)).interval for a in range(11)
                 for b in range(11) for c in range(11)]
        self.assertEqual(len(set(cells)), 11 ** 3)
        self.assertEqual(cells[0][0], 0)
        self.assertEqual(cells[-1][1], 1)
        self.assertTrue(all(left[1] == right[0] for left, right in zip(cells, cells[1:])))

    def test_arbitrary_precision_handoff_beyond_float_resolution(self):
        address = Address((10, 0, 7, 3) * 25)
        restored = Address.from_dict(json.loads(json.dumps(address.to_dict())))
        self.assertEqual(address, restored)
        self.assertEqual(restored.interval[1] - restored.interval[0], Fraction(1, 11 ** 100))
        self.assertNotEqual(address.center, address.shift(1).center)
        self.assertEqual(float(address.center), float(address.shift(1).center))

    def test_zoom_is_contained_and_center_child_keeps_center(self):
        parent = Address((7, 10))
        self.assertEqual(parent.center, parent.zoom().center)
        self.assertEqual(parent.interval[1] - parent.interval[0],
                         11 * (parent.zoom().interval[1] - parent.zoom().interval[0]))
        for digit in range(11):
            child = parent.zoom(digit)
            self.assertGreaterEqual(child.interval[0], parent.interval[0])
            self.assertLessEqual(child.interval[1], parent.interval[1])

    def test_carry_and_end_stops(self):
        self.assertEqual(Address((1, 10)).shift(1), Address((2, 0)))
        self.assertEqual(Address((0, 0)).shift(-1), Address((0, 0)))
        self.assertEqual(Address((10, 10)).shift(1), Address((10, 10)))

    def test_invalid_addresses_are_rejected(self):
        for digits in ((), (11,), (-1,), (True,), (1.0,), [5]):
            with self.subTest(digits=digits), self.assertRaises(ValueError):
                Address(digits)
        with self.assertRaises(ValueError):
            Address.from_dict({"radix": True, "digits": [5]})


class MotionTests(unittest.TestCase):
    def test_curves_have_specific_meanings(self):
        original = Dial(Address((5, 5)))
        self.assertEqual(original.turn(1).address.index - original.address.index, 1)
        logarithmic = replace(original, curve="logarithmic").turn(1)
        self.assertEqual(logarithmic.address.index - original.address.index, 2)
        self.assertEqual(logarithmic.remainder, Fraction(787536, 1000000))
        thresholded = replace(original, curve="thresholded")
        self.assertEqual(thresholded.turn(1).address, original.address)
        self.assertEqual(thresholded.turn(2).address.index - original.address.index, 2)
        contextual = replace(original, curve="context-sensitive", context_load=Fraction(3))
        self.assertEqual(contextual.turn(4).address.index - original.address.index, 1)

    def test_fractional_movement_accumulates_in_both_directions(self):
        original = Dial(Address((5, 5)), sensitivity=Dial(Address((5,))))  # Gain 1/6.
        for direction in (1, -1):
            dial = original
            for _ in range(5):
                dial = dial.turn(direction)
            self.assertEqual(dial.address, original.address)
            self.assertEqual(dial.remainder, Fraction(direction * 5, 6))
            dial = dial.turn(direction)
            self.assertEqual(dial.address.index, original.address.index + direction)
            self.assertEqual(dial.remainder, 0)

    def test_recursive_sensitivity_and_context_round_trip_future_behavior(self):
        dial = Dial(Address((7, 3, 5)), "context-sensitive", Fraction(7, 3),
                    remainder=Fraction(2, 5),
                    sensitivity=Dial(Address((8, 2)), sensitivity=Dial(Address((4, 7)))))
        restored = Dial.from_dict(json.loads(json.dumps(dial.to_dict())))
        self.assertEqual(restored, dial)
        for ticks in (1, 10, -3, -10, 4):
            dial, restored = dial.turn(ticks), restored.turn(ticks)
            self.assertEqual(restored, dial)

    def test_end_stop_clears_pending_motion(self):
        dial = Dial(Address((0,)), remainder=Fraction(-3, 4))
        self.assertEqual(dial.turn(-1).remainder, 0)
        self.assertEqual(dial.turn(-1).turn(1).address, Address((1,)))

    def test_invalid_motion_and_curve_parameters(self):
        for ticks in (11, -11, True, 1.5):
            with self.subTest(ticks=ticks), self.assertRaises(ValueError):
                Dial().turn(ticks)
        for kwargs in ({"curve": "unknown"}, {"threshold": 0}, {"context_load": Fraction(-1)},
                       {"remainder": Fraction(1)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Dial(**kwargs)


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.gate, self.console = fixture()
        self.source = next(iter(self.console.signals.values()))

    def attention(self):
        self.console.switch_map(ControlMap("attention", 1, "attention", signal_id=self.source.id,
                                           sample_region=(0, len(self.source.samples))))

    def test_maps_preserve_physical_state_and_keep_quantity_types_distinct(self):
        original = self.console.dial
        frequency = self.console.control_map.interpret(original.address)
        self.attention()
        attention = self.console.control_map.interpret(original.address)
        self.console.switch_map(ControlMap("tx", 1, "transmit"))
        transmission = self.console.control_map.interpret(original.address)
        self.assertIs(self.console.dial, original)
        self.assertIs(type(frequency), FrequencySelection)
        self.assertIs(type(attention), AttentionSelection)
        self.assertIs(type(transmission), TransmissionRequest)

    def test_old_requests_do_not_cross_map_switch_even_when_switched_back(self):
        request = self.console.prepare()
        old_map = self.console.control_map
        self.attention()
        self.console.switch_map(old_map)
        with self.assertRaisesRegex(Denied, "stale control binding"):
            self.console.execute(request, now=NOW)

    def test_movement_or_response_change_invalidates_prepared_binding(self):
        for change in (lambda: self.console.turn(1), lambda: self.console.zoom(),
                       lambda: self.console.set_response("thresholded"),
                       lambda: self.console.set_sensitivity(Dial())):
            request = self.console.prepare()
            change()
            with self.assertRaisesRegex(Denied, "stale control binding"):
                self.console.execute(request, now=NOW)

    def test_withdrawal_retains_history_and_regrant_does_not_revive_request(self):
        request = self.console.prepare()
        snapshot, history = self.console.snapshot(), self.console.history
        self.gate.withdraw("receive")
        self.assertEqual(self.console.snapshot(), snapshot)
        self.assertEqual(self.console.history, history)
        with self.assertRaises(Denied):
            self.console.execute(request, now=NOW)
        with self.assertRaises(Denied):
            self.console.execute(self.console.prepare(), now=NOW)
        self.gate.grant_affordance("receive")
        with self.assertRaisesRegex(Denied, "stale authority epoch"):
            self.console.execute(request, now=NOW)
        self.console.execute(self.console.prepare(), now=NOW)

    def test_forged_or_cross_console_request_rejected(self):
        request = self.console.prepare()
        forged = replace(request, operation="transmit", selection=TransmissionRequest(
            Fraction(99_000_000), Fraction(100), "FM"))
        with self.assertRaisesRegex(Denied, "not prepared"):
            self.console.execute(forged, now=NOW)
        _, other = fixture()
        with self.assertRaisesRegex(Denied, "not prepared"):
            other.execute(request, now=NOW)

    def test_success_consumes_request(self):
        request = self.console.prepare()
        self.console.execute(request, now=NOW)
        with self.assertRaisesRegex(Denied, "consumed"):
            self.console.execute(request, now=NOW)

    def test_gate_rejects_type_confusion(self):
        self.gate.grant_affordance("transmit")
        with self.assertRaisesRegex(Denied, "type disagree"):
            self.gate.check("transmit", self.gate.epoch("transmit"),
                            self.console.control_map.interpret(self.console.dial.address), now=NOW)

    def test_many_dial_gestures_do_not_change_any_authority(self):
        self.gate.withdraw("receive")
        self.gate.withdraw("attend")
        expected = self.gate.state()
        self.console.set_sensitivity(Dial(Address((8,)), sensitivity=Dial(Address((4,)))))
        self.console.turn_sensitivity(2)
        self.console.turn_sensitivity(-1, depth=2)
        for _ in range(3):
            self.console.turn_response(3)
            self.assertEqual(self.gate.state(), expected)
        self.console.zoom()
        for curve in CURVES:
            self.console.set_response(curve, context_load=Fraction(2, 3))
            for ticks in range(-10, 11):
                self.console.turn(ticks)
                self.assertEqual(self.gate.state(), expected)
        with self.assertRaises(Denied):
            self.console.execute(self.console.prepare(), now=NOW)

    def test_attention_bounds_are_validated(self):
        for source_id, region in (("absent", (0, 3)), (self.source.id, (0, 21))):
            with self.assertRaises(ValueError):
                self.console.switch_map(ControlMap("attention", 1, "attention",
                    signal_id=source_id, sample_region=region))
        for region in ((-1, 3), (2, 2), (False, 3)):
            with self.assertRaises(ValueError):
                ControlMap("attention", 1, "attention", signal_id=self.source.id, sample_region=region)

    def test_source_replacement_and_out_of_band_dial_changes_invalidate_requests(self):
        request = self.console.prepare()
        self.console.signals[self.source.id] = replace(self.source, samples=(1,) * 20)
        with self.assertRaisesRegex(Denied, "stale source binding"):
            self.console.execute(request, now=NOW)
        request = self.console.prepare()
        self.console.dial = self.console.dial.turn(1)
        with self.assertRaisesRegex(Denied, "stale dial binding"):
            self.console.execute(request, now=NOW)

    def test_response_and_sensitivity_are_themselves_operable_dials(self):
        primary = self.console.dial.address
        for curve in CURVES[1:]:
            self.console.turn_response(3)
            self.assertEqual(self.console.dial.curve, curve)
            self.assertEqual(self.console.dial.address, primary)
        self.console.set_sensitivity(Dial(Address((5,)), sensitivity=Dial(Address((4,)))))
        before = self.console.dial.sensitivity.sensitivity.address
        self.console.turn_sensitivity(2, depth=2)
        self.assertNotEqual(self.console.dial.sensitivity.sensitivity.address, before)
        self.assertEqual(self.console.dial.address, primary)
        with self.assertRaises(ValueError):
            self.console.turn_sensitivity(1, depth=3)


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.gate, self.console = fixture()
        self.source = next(iter(self.console.signals.values()))
        self.console.switch_map(ControlMap("attention", 1, "attention", signal_id=self.source.id,
                                           sample_region=(0, len(self.source.samples))))

    def test_proposal_is_advisory_and_acceptance_does_not_move_physical_controls(self):
        snapshot, authority = self.console.snapshot(), self.gate.state()
        proposal = self.console.autodisco()
        self.assertEqual(proposal.region, (13, 16))
        self.assertEqual(self.console.snapshot(), snapshot)
        self.assertEqual(self.gate.state(), authority)
        self.console.accept(proposal, now=NOW)
        self.assertEqual(self.console.control_map.sample_region, (13, 16))
        self.assertEqual(self.console.dial.to_dict(), snapshot["dial"])
        self.assertEqual(self.gate.state(), authority)

    def test_withdrawal_blocks_acceptance_without_destroying_proposal_or_settings(self):
        proposal = self.console.autodisco()
        snapshot = self.console.snapshot()
        self.gate.withdraw("attend")
        with self.assertRaises(Denied):
            self.console.accept(proposal, now=NOW)
        self.assertEqual(self.console.snapshot(), snapshot)

    def test_forged_stale_and_changed_source_proposals_rejected(self):
        proposal = self.console.autodisco()
        with self.assertRaisesRegex(Denied, "not created"):
            self.console.accept(replace(proposal, region=(0, 30)), now=NOW)
        self.console.turn(1)
        with self.assertRaisesRegex(Denied, "stale proposal"):
            self.console.accept(proposal, now=NOW)
        proposal = self.console.autodisco()
        self.console.signals[self.source.id] = replace(self.source, samples=(1,) * 20)
        with self.assertRaisesRegex(Denied, "stale proposal"):
            self.console.accept(proposal, now=NOW)

    def test_proposals_remain_inside_the_current_region(self):
        self.console.switch_map(replace(self.console.control_map, sample_region=(0, 8)))
        self.assertEqual(self.console.autodisco().region, (2, 5))
        for width in (0, -1, 8, 9, True):
            with self.subTest(width=width), self.assertRaises(ValueError):
                self.console.autodisco(width)


class TransmitTests(unittest.TestCase):
    def setUp(self):
        self.gate, self.console = fixture()
        self.console.switch_map(ControlMap("tx", 1, "transmit"))
        self.gate.grant_affordance("transmit")

    def execute(self, now=NOW):
        return self.console.execute(self.console.prepare(), now=now)

    def test_independent_permission_combinations(self):
        for permission in (None, 200):
            for authorization in (None, radio()):
                with self.subTest(permission=permission, authorization=authorization):
                    self.gate.set_transmit_permission(permission)
                    self.gate.set_radio_authorization(authorization)
                    if permission and authorization:
                        self.assertFalse(self.execute()["rf_emitted"])
                    else:
                        with self.assertRaises(Denied):
                            self.execute()

    def test_radio_authorization_covers_all_applicable_dimensions(self):
        self.gate.set_transmit_permission(200)
        for overrides in (
            {"operator": "another-operator"}, {"device": "another-device"},
            {"jurisdiction": "another-jurisdiction"}, {"modes": ("AM",)},
            {"max_power_w": Fraction(1, 2)}, {"low_hz": Fraction(107_000_000)},
            {"high_hz": Fraction(89_000_000)},
        ):
            with self.subTest(overrides=overrides):
                self.gate.set_radio_authorization(radio(**overrides))
                with self.assertRaisesRegex(Denied, "does not cover"):
                    self.execute()

    def test_expiry_checked_at_execution_including_exact_deadline(self):
        self.gate.set_transmit_permission(120)
        self.gate.set_radio_authorization(radio(expires_at=130))
        self.assertFalse(self.execute(now=119)["rf_emitted"])
        with self.assertRaisesRegex(Denied, "permission absent or expired"):
            self.execute(now=120)
        self.gate.set_transmit_permission(200)
        with self.assertRaisesRegex(Denied, "authorization absent or expired"):
            self.execute(now=130)

    def test_permission_or_radio_replacement_invalidates_prepared_request(self):
        self.gate.set_transmit_permission(200)
        self.gate.set_radio_authorization(radio())
        for change in (lambda: self.gate.set_transmit_permission(None),
                       lambda: self.gate.set_radio_authorization(None)):
            self.gate.set_transmit_permission(200)
            self.gate.set_radio_authorization(radio())
            request = self.console.prepare()
            change()
            with self.assertRaisesRegex(Denied, "stale authority epoch"):
                self.console.execute(request, now=NOW)


class ReplayTests(unittest.TestCase):
    def test_replay_retains_provenance_and_does_not_import_authority_or_requests(self):
        gate, console = fixture()
        console.set_sensitivity(Dial(Address((2, 8)), sensitivity=Dial(Address((7, 1)))))
        console.set_response("context-sensitive", context_load=Fraction(5, 2))
        console.turn(2)
        request = console.prepare()
        archive = json.loads(json.dumps(console.export()))
        restored_gate = AuthorityGate()
        restored = replay(archive, restored_gate)
        self.assertEqual(restored.snapshot(), console.snapshot())
        self.assertEqual(restored.history[:len(console.history)], console.history)
        self.assertEqual(restored_gate.state()["affordances"], [])
        with self.assertRaises(Denied):
            restored.execute(restored.prepare(), now=NOW)
        restored_gate.grant_affordance("receive")
        with self.assertRaisesRegex(Denied, "not prepared"):
            restored.execute(request, now=NOW)
        restored.execute(restored.prepare(), now=NOW)

    def test_mutation_reordering_and_truncation_break_hash_chain(self):
        _, console = fixture()
        console.turn(1)
        console.zoom()
        for mutate in (
            lambda h: h[0]["snapshot"]["dial"]["address"]["digits"].append(10),
            lambda h: h.reverse(),
            lambda h: h.pop(0),
        ):
            archive = console.export()
            mutate(archive["history"])
            with self.assertRaisesRegex(ValueError, "integrity"):
                replay(archive, AuthorityGate())

    def test_external_history_copy_cannot_modify_historic_record(self):
        _, console = fixture()
        expected = digest(console.export())
        copy = console.history
        copy[0]["snapshot"]["dial"]["curve"] = "thresholded"
        self.assertEqual(digest(console.export()), expected)

    def test_full_experiment(self):
        result = run()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["checks"]), 25)
        self.assertTrue(all(check["passed"] for check in result["checks"]))


if __name__ == "__main__":
    unittest.main()
