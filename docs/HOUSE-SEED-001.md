# HOUSE-SEED-001 — the Suitcase is designed to grow a house around itself

**MIT-facing research framing:** *One house is the smallest working model of a cooperative city.*

**Implementation status:** executable **read-only construction-recipe generator**, extending SUITCASE-GENESIS-001 on its existing draft branch. **No house, OS installer, bootable image, instrumentation, field test, institutional approval, or operating city is claimed.** An inspectable plan and independently repeatable tests exist; builders must perform and measure the physical work.

## The inversion

Ordinary systems install software into an already designed building. This proposal begins with an independently controlled portable computing node—the Living Suitcase—and uses a validated *site/parts survey* to propose how a building could become its larger body. The software generates a **construction plan**, not a magical building or permission to alter property.

```text
HUMAN PURPOSE + ACTUAL PARTS + SITE OBSERVATIONS
           |                            (never inferred from AI)
           v
  STATIC OS SUITCASE (mission / independent private core)
           |
           v
  HOUSE-SEED deterministic generator + HOLD-only cold verification
           |
           +-- utility: local brain and approved low-voltage power
           +-- roof/window: measured solar and energy budget
           +-- entrance: pressure sensing, optional honest harvesting research
           +-- hall/walls: removable light transceiver experiment
           +-- garden/kitchen: measured conditions and public-safe resource offer
           +-- living room: voice OR text -> draft -> human decision
           +-- independent peer: signed exchange and local right of refusal
           +-- tranchNOSE bay: geometry-sensitive optical A/B/A experiment
           |
           v
  5 work stages + site-specific missing-part holds + test receipts
           |
           v
  HUMAN CHOICE / EXTERNAL SAFE CONSTRUCTION / MEASUREMENT
           |
           v
  OPTIONAL SECOND INDEPENDENT SUITCASE, NEVER A SUBORDINATE
```

Nothing in the generator grants legal incorporation, private-data consent, building permits, grid connection, external authority, or claims of deployed physical performance.

## Run locally, no new dependencies or network calls

From a source checkout of the **Suitcase Genesis branch**:

```sh
python3 scripts/suitcase.py house-template > site.json
python3 scripts/suitcase.py probe > host-inventory.json
python3 scripts/suitcase.py house-compose --inventory host-inventory.json --site site.json --profile foundry --media grow --privacy private > living-house.json
python3 scripts/suitcase.py house-verify living-house.json
python3 scripts/suitcase.py house-render living-house.json > living-house-work-cards.html
python3 -m unittest discover -s tests -p 'test_house_seed.py' -v
```

The output `living-house-work-cards.html` is a **standalone, script-free printable document** for a phone or laptop; its plan hash can be compared to the verified JSON. No server, user account, network link or cloud provider is required to open it. It is a plan, not a live dashboard or device controller.\n\nInitially all spaces and parts are `UNOBSERVED`. Editing **only** documented public-safe observation states to `PRESENT_UNVERIFIED` creates specific bench candidates and missing-part HOLDs. `ABSENT` stays unavailable. `site_permission=OPERATOR_SELF_ATTESTED` means only an unverified self-report, **not** legal or technical authorization to build. A real address, coordinates, identities, child/survivor records, or private case details are not accepted by the schema and must not be placed in the file.

The host probe sees the *current Python computer*, not the house, a future target disk, a solar panel, or the second device. The schema fixes which independent physical observations may affect the generated plan. Cold `house-verify` regenerates the entire plan, compares it exactly and refuses fabricated "BUILT", service, governance, discovery or safety claims. The SHA-256 digest is only an unkeyed integrity check, **not** a signature or approval.

## Five real construction stages (not executed automatically)

1. **Suitcase → utility room.** Inspect safe intact commercial power, computer, network isolation and local offline operation. Reversible bench, not permanent wiring.
2. **House surfaces → instruments.** Measure PV voltage/current/Wh; count pressure sensor events; send/check bits via short-range LED and photodiode. Do not promise walkway or concert venue electrical generation. A footfall or sound event is an external energy input; there is no positive-energy feedback loop.
3. **Speech → human-reviewed proposal.** Text input is a necessary accessible fallback. Microphone is off unless deliberately enabled in a later, separately reviewed implementation. Drafting a task cannot operate a switch, door, stove, charger, lock, fire alarm, or emergency system.
4. **Second independently controlled node.** Existing webZ Suitcase illustrates signed experimental SEED/GENESIS/OFFER/REFUSE via manual file transfer. That envelope is **not currently reLATTE wire-compatible**. Two keys on one person's devices do not prove two organizations or independent human governance.
5. **Reproduction rather than subordination.** A genuinely independent steward may make a distinct node under its own rules. Origin ancestry never entails authority, membership, data access, or public discovery.

For a physical experiment, first run on detached benchtop components. Do not modify mains, in-wall wiring, roof, road, sidewalk, structure or public rights-of-way; get qualified review and owner permission where relevant. No bare battery cells or improvised lithium charging. No radio transmission, surveillance, or publicly visible identities by default. A pressure panel may be useful as a *sensor* even if energy output is negligible. A claimed power result needs separately measured input and output with losses.

## Scientific core and practical product

The **product** is a reproducible, offline-capable kit that helps ordinary community spaces plan and document local energy awareness, resource coordination and opt-in federation, with independent ownership at every site.

The **research tracks** remain distinct:
- **Cooperative computing:** Can locally governed nodes exchange public-safe signed offers and refuse independent of central servers?
- **Energy-aware built surfaces:** How much genuinely usable energy/signal can removable solar, pressure and optical components provide in realistic conditions?
- **Relational physical computation:** When geometry changes but control is held constant, does a tranchNOSE fixture show a repeatable additional effect? A/B/A alone does *not* prove memory distributed in a field.

The experimental fixture's failure must never disable the base Suitcase. TranchNOSE and TranchNode are distinct experiments with distinct claims; neither governs this plan. GHoT owns proposed hardware work, JAR;VIS can eventually suggest human-approved work, and reLATTE can eventually carry signed independent crossings only after an explicit interoperability test. There is no runtime integration with those projects in HOUSE-SEED-001; `source_owners` is a traceable reference map.

## MIT presentation: one house, a city implied by composition

**Opening:** *What if the infrastructure to build a cooperative city could fit in a suitcase—and the first city were a single house?*

The suitcase is both the first node and the human-reviewable architect of its expanded physical environment. The outcome proposed for an initial research demo is modest: a public-safe offline bench, measured low-voltage solar input, one successful short-range optical message, a pressure sensor, and one independently reviewed signed refusal. None of those specific combined outcomes have been observed yet. The resulting five-stage recipe is portable, not centralized, and can be repeated by a second independent user.

**Impact hypothesis:** Community spaces can coordinate local resources, document their own infrastructure and retain their right to refuse without buying into a centrally controlled smart-building platform.

**Evaluation gates:** real power measurements with baselines and power losses; optical bit-error rate versus distance; offline service survival; time/cost to replicate; false-positive sensor rate; independent human review and right-of-refusal evidence. The house-scale plan does not establish city-scale economics, permitting, accessibility, survivability or governance.

**What the proposal seeks:** collaborators and resources for hardware safety, empirical evaluation, human-centered pilots and replication—not endorsement of speculative physics. Check actual MIT program eligibility and timing before submission.

## Independent source lanes

- STATIC OS and builder: https://github.com/the-static-collective/static-os
- Living Suitcase browser demo: https://github.com/the-static-collective/webZ/tree/main/bridge/suitcase
- Physical research: https://github.com/the-static-collective/tranchNOSE
- Hardware experimentation: https://github.com/the-static-collective/GHoT
- Planned signed crossings: https://github.com/the-static-collective/reLATTE
- Human intent ideas: https://github.com/the-static-collective/JAR-VIS

**Boundary:** `PLAN != INSTALL`; `SURVEY != PERMISSION`; `SPEECH != AUTHORITY`; `LIGHT_SIGNAL != RELATIONAL_MEMORY`; `HARVESTED_ENERGY != FREE_ENERGY`; `ANCESTRY != GOVERNANCE`; `ONE_HOUSE_PLAN != CITY_PROOF`.
