# REGENERATIVE DESIGN CAPACITY 010 — digital CAD evidence, not physical inventory

**Draft executable Static OS source-owned adapter** stacked on STATIC-CAD-006 #57 (and its parent chain, including CAD-005 #56). This does not change the boot image, physical machine permissions, GHoT runtime, reLATTE wire format, or GOATnote authority.

## What is real

The parent code already:
- executes actual CadQuery/OpenCASCADE BRep construction from a solved sketch;
- produces real STEP and STL bytes and independently reimports STEP;
- records a six-event inspectable design-decision ledger;
- calls native reLATTE R14 to issue signed crossing, RECEIVE and R3_HOLD receipts;
- can also produce a selected CAD-006 revision and a GOATnote-native **proposed import**, without browser-side note mutation.

010 adds **zero new fabrication operations**. Its cold verifier uses Static OS's real `verify_files` and `verify_native` code on existing files. With a CAD-006 package it additionally runs the source-owned `verify_branch` (including real GOATnote), not a copied proof adapter. All these checks happen before a digital-design proposal is exported.

```text
Static OS real solved sketch / OCCT solid / STEP-STL
  → native reLATTE signed crossing, RECEIVE, R3_HOLD
  → Static OS own byte and signature cold verification
  → immutable DigitalDesignCandidate (inert, no manufacturing rights)
  → optional separately reviewed Jubilee asset OFFER
  → native Treasury separate signed ACCEPT
  → native Treasury separate signed RECEIVE
  → Living Capacity Index DIGITAL DESIGN lane
  → possible design + work-hour → human shop-planning proposal
  → STOP
```

### Operators

Select a previously generated and signed package (see CAD-005 and CAD-006 docs). It must have the original source and receipts, not a detached screenshot, STEP file alone or copied textual claim.

```sh
python3 scripts/static-design-capacity.py export \
  --family STATIC_CAD_005 \
  --package /path/to/verified-solid \
  --out /private/new/cad010-candidate.json

python3 scripts/static-design-capacity.py verify \
  --family STATIC_CAD_005 \
  --package /path/to/verified-solid \
  --out /private/new/cad010-candidate.json
```

For a selected CAD-006 revision use `--family STATIC_CAD_006` and point `--package` to the **entire** branch folder containing its signed `solid/`, `tree.json`, `manifest.json` and GOATnote handoff.

The JSON candidate contains exact source sketch / decision history / solid manifest / optional feature branch identities, four byte hashes (sketch, trace, STEP, STL) and signed reLATTE crossing / RECEIVE / HOLD IDs. It exposes **no receiver private keys**. Its `candidate_id` is content-addressed, **not itself a signature**.

`native_signatures_cold_verified: true` is an assertion from this source-owned exporter *when executed*. A copied JSON object cannot prove that this verifier ran, because anyone can edit the field and recompute its hash. A downstream receiver should call this trusted verifier on actual original bytes and verify signatures itself before accepting anything. CI does so in an ordered native two-repository run. A public export with only a SHA digest is not a substitute for source verification.

### Typed boundaries

- `digital_design`, `unit:design`, `quantity:1`: cataloged source artifact, **not** one manufactured part or universal production right.
- `fabricated_physical_units:0`, `engineering_safety_certified:false`, `legal_rights_verified:false`.
- reLATTE disposition stays `HOLD`; neither a signed receipt nor a successful STEP readback grants manufacturing.
- Digital copies can be reused, but without confirmed licensing/custody they are not transferable property, currency, liquid collateral, or guaranteed market capacity.
- Distinct revisions may remain historically attributable. Repeated identical STEP bytes must not silently increase scarce physical inventory or imply more verified design rights.
- No automatic repeated questions, CAD turns, fabrication, procurement, AI inference or human-admission decisions.

### Native test

`.github/workflows/regenerative-design-capacity-010.yml` checks out actual pinned GHoT and reLATTE owners, runs real OCCT/STEP/reimport, signs the original crossing through reLATTE, cold exports a candidate, tests tampered STEP/signature/economy fields, and checks the pinned draft Jubilee recipient's proposal/receipt seam against that very output.

The source owner retains every underlying artifact and its original authority. The recipient may present new proposals but must make its own locally authorized disposition.

**Law:** `VERIFIED DIGITAL DESIGN != PHYSICAL MACHINE`; `CAD REPLAY != NEW PRODUCTION`; `SIGNATURE != RIGHTS`; `RECEIVED != ADMITTED`; `DESIGN REUSE != PHYSICAL MULTIPLICATION`; `INDEX != CREDIT`.
