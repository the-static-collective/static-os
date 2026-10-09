# FORAGE-001 — the field has a pantry

**Status:** executable local-first field ledger. Discovery, review and human-reported
handoff are distinct; there is no automatic legal right to take anything.
This is a *procedure for checking* lawfulness, not a device that can certify it.

This is a separate Static OS experiment (branch from main), not a descendant
of the Robot Garden camera draft chain. A later bridge can carry eligible
candidates to Robot Garden for independent quality/safety inspection and
owner-local admission.

## The actual user experience

1. **Notice:** make a lead, without entering fenced land, opening bins or
   collecting anything. Example categories are recovered electronics,
   mechanical parts, building material, food/plant material, minerals, and
   digital assets with unresolved licenses.
2. **Identify the steward:** private owner, municipal reuse operator,
   BLM/USFS local land manager, state park/state trust authority, or UNKNOWN.
   Ownership of waste is never assumed from curbside placement or a dumpster.
3. **Check authority:** who grants entry, who permits **removal**, exactly which
   item, quantity, purpose, location and window; review local rules, posted
   restrictions and relevant license conditions. Enter a pointer to the
   genuine external evidence; the app does not authenticate that person or
   permission itself.
4. **Handle hazards separately:** no collecting protected items, unidentified
   edible plants/fungi, cultural artifacts, active mining claims, locked or
   posted containers, damaged lithium packs, unknown chemicals or biohazards.
   Caution flags on powered gear, loose lithium cells and sharp materials
   remain gated. Do not attempt a high-voltage repair on discovered electronics.
5. **Handoff:** only for a valid, human-reviewed, nonblocked proposal; enter
   an *operator-reported* physical pickup with witness/evidence pointers.
   The app records the statement without certifying title, condition or
   independent witness identity. No inventory value or robot permission appears.
6. **Inspection/owner admission:** future Robot Garden and Jubilee crossings.
   Different machines/people may reject the proposed item. A physical part's
   presence alone does not make it safe to use or economically valuable.

## Land distinctions relevant to New Mexico

These are **external research leads**, not executable collection grants.

- BLM permits some reasonable personal, non-commercial recreation collection.
  However restrictions can depend on district, area, species, amount and
  protection/mining status. New Mexico's BLM notes some renewable personal-use
  quantities and permit requirements. Call the **actual field office** when
  in doubt. https://www.blm.gov/Learn/Can-I-Keep-This
  and https://www.blm.gov/programs/natural-resources/forests-and-woodlands/forest-product-permits
- New Mexico BLM fuelwood for household heating requires a cutting permit
  with designated species/areas and field-office restrictions. Ordinary
  deadwood is not universally free to haul away.
  https://www.blm.gov/programs/natural-resources/forests-and-woodlands/forest-product-permits/new-mexico-wood-cutting-permits
- New Mexico **state trust land** is not BLM land. It generally prohibits
  removal of native plants and valuable minerals under recreational access,
  aside from specified exceptions such as noncommercial piñon nuts.
  https://www.srca.nm.gov/parts/title19/19.002.0019.html
- New Mexico **state parks** have their own rules; Rockhound State Park
  permits souvenir rocks only in designated areas, not resale, and restricts
  tools. https://www.srca.nm.gov/parts/title19/19.005.0002.html
- EPA warns that damaged lithium batteries can burn and require appropriate
  special handling and recycling instead of ordinary trash or casual salvage:
  https://www.epa.gov/recycle/used-household-batteries

**Commercial/community distinction:** personal-use public-land collection
permissions may not cover workshop redistribution, barter, commercial work,
community tool production or gifts. Ask about those **particular uses** rather
than relying on recreational collection conditions.

## What the software actually checks

- Only bounded, exactly shaped lead/review/pickup documents are accepted.
- A lead does not create ownership or permission.
- Unverified curbside finds and unknown-source goods cannot transition to
  human-reviewed pickup proposals on a made-up owner assertion.
- Public land requires a land-manager source, and designated special land
  rules remain held until a specific written-permission **assertion**.
- A human review binds item, site, maximum quantity, unit, proposed use,
  validity interval, and entry+removal assertion. These claims are still
  externally unverified, not signatures or legal conclusions.
- Any hard-stop hazard blocks pickup even when the reviewer asserts permission.
- Operator pickup attestations must fall inside the recorded time/scope;
  human reports have no effect on accepted physical inventory.
- Deterministic hashes bind original records; checks catch altered files.
  **Hashes do not make human permission claims authentic.**

### Run the included synthetic examples

Requires Python 3.11+, standard library only, no network, no installed sensors.

```bash
python3 -m unittest discover -s tests -p 'test_forage_001.py' -v

# An offered stepper is not collectible just because somebody noticed it.
python3 scripts/static-forage.py assess \
  --lead fixtures/forage-001/owner-offered-stepper.json \
  --out dist/forage-001/held-stepper.json

# A separate explicitly reviewed scope changes only the PROPOSAL.
python3 scripts/static-forage.py assess \
  --lead fixtures/forage-001/owner-offered-stepper.json \
  --review fixtures/forage-001/owner-stepper-human-review.json \
  --out dist/forage-001/reviewed-stepper.json

python3 scripts/static-forage.py verify \
  --lead fixtures/forage-001/owner-offered-stepper.json \
  --review fixtures/forage-001/owner-stepper-human-review.json \
  --out dist/forage-001/reviewed-stepper.json
```

The pickup fixture intentionally includes
`"assessment_id": "REPLACE_DURING_TEST"`. Copy the **exact** reviewed
assessment ID into a working copy of that pickup form before calling
`handoff`. The test suite demonstrates this. Every output is first-write-only
and cold-verifiable against the original lead, review and pickup report.
No fixture represents a real grant, real pickup, or real person's signature.

```
LEAD DISCOVERED
  |
  v
HOLD for title/land/permission/safety
  |
  | specific externally supported human review
  v
HUMAN-REVIEWED PICKUP PROPOSAL (not a license)
  |
  | human operator actually chooses action under applicable rules
  v
OPERATOR-REPORTED PHYSICAL HANDOFF (not independently verified)
  |
  v
FUTURE reLATTE owner-local source+part inspection and signed acceptance
  |
  v
FUTURE physical inventory / Robot Garden use only when separately admitted
```

## Architecture doors

- **Static OS:** local prospect and offline review interface.
- **GHoT:** propose repairs and useful functions from *accepted* inventory, not
  from public-land guesses or trash seen at a distance.
- **Robot Garden:** photograph, measure and test lawfully acquired components.
- **CANNON:** preserve alternate observed histories without inventing canon.
- **reLATTE:** proposed physical-handoff crossings; receiving/accepting still
  needs real owner-local authorities and receipts.
- **Jubilee:** future capacity accounting once independently admitted;
  no extraction or invented monetary value from seeing something.

**Rules:** SEEN != OFFERED; OFFERED != GRANTED; ENTER != REMOVE;
CURBSIDE != ABANDONED; LAND_OPEN != HARVEST_OPEN; FOUND != SAFE;
OPERATOR_NOTE != VERIFIED_PERMISSION; HASH != SIGNATURE;
PICKUP_REPORTED != INVENTORY_ACCEPTED.
