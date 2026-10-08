"""Run the reproducible experiment and write its evidence. No dependencies or RF I/O."""
from dataclasses import replace
from fractions import Fraction
import argparse
import json
from pathlib import Path

from infinite_radio import (
    Address, AttentionSelection, AuthorityGate, Console, ControlMap, CURVES,
    Denied, Dial, FrequencySelection, RadioAuthorization, Signal,
    TransmissionRequest, digest, replay,
)

TARGET = Address((7, 3, 10, 2, 8, 4))
NOW = 100


def fixture() -> tuple[AuthorityGate, Console]:
    frequency_map = ControlMap("frequency", 1, "frequency")
    signal = Signal(
        "static-collective/beacon-001", frequency_map.interpret(TARGET).frequency_hz,
        (0, 1, 1, 0, 2, 1, 0, 1, 0, 2, 1, 0, 3, 8, 13, 9, 2, 0, 1, 0),
        ("synthetic-generator:v1", "seed:ELEVEN-HEAP-001", "receiver:simulated-receiver"),
    )
    gate = AuthorityGate()
    gate.grant_affordance("receive")
    gate.grant_affordance("attend")
    return gate, Console(gate, (signal,))


def radio(**overrides) -> RadioAuthorization:
    authorization = RadioAuthorization(
        "experimenter", "simulated-receiver", "simulation", Fraction(88_000_000),
        Fraction(108_000_000), Fraction(2), ("FM",), 200,
    )
    return replace(authorization, **overrides)


def run() -> dict:
    gate, console = fixture()
    checks = []

    def check(name: str, passed: bool, evidence: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": evidence})
        if not passed:
            raise AssertionError(name)

    def denied(name: str, action) -> str:
        try:
            action()
        except Denied as error:
            check(name, True, str(error))
            return str(error)
        raise AssertionError(f"operation unexpectedly authorized: {name}")

    console.turn(TARGET.digits[0] - 5)
    for child in TARGET.digits[1:]:
        console.zoom(child)
    reception = console.execute(console.prepare(), now=NOW)
    historic = console.snapshot()
    historic_digest = digest(historic)
    source = reception["signal"]
    check("tune one exact nested address", console.dial.address == TARGET
          and source is not None and source["id"] == "static-collective/beacon-001",
          {"address": TARGET.to_dict(), "frequency_hz": reception["frequency_hz"],
           "distinguishable_cells": 11 ** len(TARGET.digits)})
    source_archive = console.export()
    reconstructed = replay(json.loads(json.dumps(source_archive)), AuthorityGate())
    check("reconstruct exact address and source history", reconstructed.snapshot() == historic,
          {"historic_snapshot_sha256": historic_digest, "source_history": source["source_history"]})
    denied("reconstruction imports no authority",
           lambda: reconstructed.execute(reconstructed.prepare(), now=NOW))

    physical = console.dial.to_dict()
    frequency = console.control_map.interpret(console.dial.address)
    console.switch_map(ControlMap("attention", 1, "attention", signal_id=source["id"],
                                  sample_region=(0, len(source["samples"]))))
    attention = console.control_map.interpret(console.dial.address)
    check("same physical dials, different typed quantities", console.dial.to_dict() == physical
          and type(frequency) is FrequencySelection and type(attention) is AttentionSelection,
          {"frequency_type": type(frequency).__name__, "frequency_unit": "Hz",
           "attention_type": type(attention).__name__, "attention_unit": "source sample index",
           "physical_controls_unchanged": True})

    before = console.snapshot()
    authority_before = gate.state()
    proposal = console.autodisco()
    check("Autodisco proposes without moving controls or granting authority",
          console.snapshot() == before and gate.state() == authority_before,
          {"proposed_sample_region": list(proposal.region), "rationale": proposal.rationale})
    console.accept(proposal, now=NOW)
    check("explicit acceptance narrows the listening region",
          console.control_map.sample_region == proposal.region and console.dial.to_dict() == physical,
          {"sample_region": list(proposal.region), "map_version": console.control_map.version})
    listening = console.execute(console.prepare(), now=NOW)

    stale = console.prepare()
    before_withdrawal = console.snapshot()
    immutable_prefix = console.history
    gate.withdraw("attend")
    check("withdraw affordance without changing dials or settings",
          console.snapshot() == before_withdrawal and console.history == immutable_prefix,
          {"historic_settings_retained": True, "current_affordances": gate.state()["affordances"]})
    denied("previously prepared operation denied after withdrawal",
           lambda: console.execute(stale, now=NOW))
    denied("fresh preparation cannot restore withdrawn affordance",
           lambda: console.execute(console.prepare(), now=NOW))
    gate.grant_affordance("attend")
    denied("old request stays stale after a separate regrant",
           lambda: console.execute(stale, now=NOW))
    gate.withdraw("attend")

    authority_before = gate.state()
    console.set_sensitivity(Dial(Address((8, 2)), sensitivity=Dial(Address((4, 7)))))
    console.turn_sensitivity(1)
    console.turn_sensitivity(2, depth=2)
    console.turn_response(3)
    curve_evidence = []
    for curve in CURVES:
        console.set_response(curve, context_load=Fraction(3, 2))
        start = console.dial.to_dict()
        for _ in range(5):
            console.turn(10)
        curve_evidence.append({"curve": curve, "before": start, "after": console.dial.to_dict()})
    check("recursive sensitivity and every response curve leave authority unchanged",
          gate.state() == authority_before,
          {"nested_sensitivity_depth": 2, "curves": list(CURVES)})
    denied("dial motion still cannot restore attention",
           lambda: console.execute(console.prepare(), now=NOW))
    microscopic = Dial(Address((5,)))
    coarse_delta = microscopic.turn(1).address.center - microscopic.address.center
    for _ in range(5):
        microscopic = microscopic.zoom()
    fine_delta = microscopic.turn(1).address.center - microscopic.address.center
    check("zoom makes one physical tick progressively finer", coarse_delta / fine_delta == 11 ** 5,
          {"coarse_fraction": str(coarse_delta), "fine_fraction": str(fine_delta),
           "refinement_factor": 11 ** 5})

    console.switch_map(ControlMap("transmit", 1, "transmit"))
    authority_before = gate.state()
    request = console.prepare()
    check("transmit dial prepares only a typed request", type(request.selection) is TransmissionRequest
          and gate.state() == authority_before, {"rf_emitted": False, "request_type": "TransmissionRequest"})
    denied("transmit request cannot grant its affordance", lambda: console.execute(request, now=NOW))
    gate.grant_affordance("transmit")
    denied("transmit affordance alone is insufficient",
           lambda: console.execute(console.prepare(), now=NOW))
    gate.set_radio_authorization(radio())
    denied("radio authorization alone is insufficient",
           lambda: console.execute(console.prepare(), now=NOW))
    gate.set_radio_authorization(None)
    gate.set_transmit_permission(200)
    denied("permission alone is insufficient", lambda: console.execute(console.prepare(), now=NOW))
    gate.set_radio_authorization(radio(device="different-device"))
    denied("both grants must cover this device", lambda: console.execute(console.prepare(), now=NOW))
    gate.set_radio_authorization(radio())
    denied("expired grants denied at execution time", lambda: console.execute(console.prepare(), now=200))
    authorized_request = console.prepare()
    transmission = console.execute(authorized_request, now=NOW)
    check("both valid grants allow only the simulated transmission", transmission["rf_emitted"] is False,
          transmission)
    denied("successful requests cannot be replayed",
           lambda: console.execute(authorized_request, now=NOW))
    prepared_before_revoke = console.prepare()
    gate.set_transmit_permission(None)
    denied("separate transmission permission is revocable",
           lambda: console.execute(prepared_before_revoke, now=NOW))

    archive = console.export()
    restored = replay(archive, AuthorityGate())
    check("full instrument microscope survives handoff", restored.snapshot() == console.snapshot()
          and restored.dial.sensitivity.sensitivity is not None,
          {"exact_snapshot_sha256": digest(console.snapshot()), "authority_imported": False})
    check("initial reception remains intact after every later operation", digest(historic) == historic_digest
          and archive["history"][:len(immutable_prefix)] == immutable_prefix,
          {"initial_snapshot_sha256": historic_digest, "source_archive_head": source_archive["history"][-1]["hash"]})
    return {"experiment": "ELEVEN-HEAP-001", "title": "The Infinite Radio Console",
            "status": "PASS", "simulation_only": True, "checks": checks,
            "initial_reception": reception, "listening": listening,
            "response_examples": curve_evidence, "archive": archive}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    result = run()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "experiment.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "history.json").write_text(json.dumps(result["archive"], indent=2) + "\n")
    rows = ["# ELEVEN-HEAP-001 — The Infinite Radio Console", "",
            f"PASS: {len(result['checks'])} experiment checks. Simulation only; no RF emitted.", "",
            "| Check | Result |", "| --- | --- |"]
    rows.extend(f"| {check['name']} | PASS |" for check in result["checks"])
    rows.extend(["", "Exact initial address: `11:[7,3,10,2,8,4]`.",
                 f"Exact frequency: `{result['initial_reception']['frequency_hz']} Hz`.",
                 "Autodisco proposed source samples `[13,16)`; acceptance changed only the typed map.",
                 "Full source lineage, map definitions, response context, nested sensitivity, and",
                 "fractional motion remainders are retained in `history.json`.", ""])
    (args.output / "RESULTS.md").write_text("\n".join(rows))
    print(f"ELEVEN-HEAP-001: PASS ({len(result['checks'])} checks)")
    print(f"Evidence: {args.output / 'RESULTS.md'}")
    print("RF emitted: false")


if __name__ == "__main__":
    main()
