# GLEAN-001 — the remainder is a door

**Status:** independent, offline, testable surplus-offer organ in Static OS.
GLEAN is not an alias of FORAGE: the source is **intentionally offered by an
identified steward** for specified use, rather than encountered as apparently
discarded material. Neither instrument establishes legal ownership itself.

## Lawful source distinctions

Agricultural gleaning means collecting owner-donated agricultural crops for
free distribution in New Mexico's Food Donors Liability Act, NM Statutes
41-10-2(B): https://law.justia.com/codes/new-mexico/chapter-41/article-10/section-41-10-2/
The statute includes qualified donor liability rules, NOT an automatic right
of entry or removal, and preserves governmental food safety authority
(41-10-3):
https://law.justia.com/codes/new-mexico/chapter-41/article-10/section-41-10-3/
The USDA distinguishes field gleaning after primary harvest (or uneconomical
harvest) and donated surplus crops:
https://www.usda.gov/sites/default/files/documents/usda_gleaning_toolkit.pdf

Other workshop surplus is an **analogy**, not statutory crop gleaning. An
owner-offered spare-part gift must not claim food-donor protections or authorize
salvage from somebody else's property.

## Executable flow

1. Create a `static-os.glean-offer/v0` with an owner donation ASSERTION;
   original steward, bounded source, quantity, use, recipient, window, hazard
   declaration and evidence pointer.
2. GLEAN records a `HOLD_AND_VERIFY` plan until a distinct human review.
   `owner_donation_asserted` is not external verification.
3. Review `SCOPED_ACCESS_ASSERTED` names entry **and** removal, exact
   recipient and intended use, maximum collection, and time window.
   The output is still a `HUMAN_REVIEWED_PROPOSAL_ONLY`, not a legal
   permission certificate. Land access, licenses, food safety and owner
   identity remain externally governed.
4. Future real-world collection may be documented via operator-reported
   pickup events, with source evidence references, unique IDs, actual stated
   dates, recipient, amount and an explicit `plan_id`. Replaying independent
   reports must conserve the capped remainder and reject repeated IDs.
5. Each deterministic receipt chains to the prior one. The reported remaining
   amount is arithmetic on **operator statements**, not proof of remaining
   physical stock. Physical accepted inventory and transport are always zero.
6. A future signed reLATTE crossing and independent owner-local receiver
   admission, safe food handling and quality review are necessary for real
   physical acceptance, and are **not implemented** here.

### Sample, purely synthetic

```bash
python3 -m unittest discover -s tests -p 'test_glean_001.py' -v

python3 scripts/static-glean.py assess \
  --offer fixtures/glean-001/orchard-offer.json \
  --out dist/glean-001/orchard-held.json

python3 scripts/static-glean.py assess \
  --offer fixtures/glean-001/orchard-offer.json \
  --review fixtures/glean-001/orchard-review.json \
  --out dist/glean-001/orchard-proposal.json

python3 scripts/static-glean.py verify \
  --offer fixtures/glean-001/orchard-offer.json \
  --review fixtures/glean-001/orchard-review.json \
  --out dist/glean-001/orchard-proposal.json
```

To construct a `journal`, a human independently records operator-reported
events with original `plan_id`, unique `pickup_ref`, amount and recipient.
The native tests show the exact JSON contract; no source fixture describes a
real pickup. Reusing an event ID, exceeding the same reviewed cap, changing
scope or cold replaying against altered inputs must fail.

**Limits:** `amount` is an integer and unit is explicit; the code checks
software quantities and apparent claims, not actual volume, time, ownership,
food safety, real harvesting, or whether a recipient independently accepted.

### Architecture

- **GrO:** future bounded *quest encounter* at a named place, without
  automatically distributing collection rights or public world traces.
- **WEBZ:** future opt-in public invitation exposing at most generic purpose
  and offered class; never publish private owner/recipient addresses or
  perishable pickup windows automatically.
- **FORAGE:** remains a distinct observational scavenging/prospect tool.
- **reLATTE:** possible signed human physical handoff and sovereign
  recipient disposition. This implementation does not produce valid signed
  envelopes/receipts.
- **Jubilee/Robot Garden:** may eventually propose worthwhile reuse after
  a real material passes custody, hazard review and owner-local admission;
  not before.

**Laws:** REMAINDER != ABANDONED; OFFER != TITLE; OWNER ASSERTION !=
AUTHENTICATED GRANT; ACCESS != REMOVAL; FOOD-GLEANING LAW != WORKSHOP GIFT;
REPORT != ACTUAL PICKUP; CLAIMED REMAINDER != PHYSICAL INVENTORY;
HASH != SIGNATURE; DISTRIBUTION PLAN != FOOD SAFETY CLEARANCE.
