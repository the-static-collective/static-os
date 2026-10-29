# SUITCASE GENESIS 001 — mission first, machine second

**Status:** bounded, executable **read-only composer** stacked on GENESIS-001 live-image candidate. Not a booted distribution, installed OS, firmware scanner, real federation, production privacy solution, or source-verified package bundle.

## Why this exists

The operator should specify a purpose—commons, church, resilience, protected room, or organization foundry—before STATIC OS determines what the target machine *could* become. Hardware observations and mission preferences yield a bounded, addressable **HOLD-only composition candidate**. A candidate never creates an organization or authorizes a network publication.

## Try it without root or internet

~~~sh
python3 scripts/suitcase.py probe
python3 scripts/suitcase.py compose --profile church --media forest --privacy invitation-only > plan.json
python3 scripts/suitcase.py verify plan.json
python3 -m unittest discover -s tests -p 'test_suitcase.py' -v
~~~

`probe` reads the current machine's architecture, memory, network-interface types and available space **in the current working directory**. These are observations, not capability, connection, power-safety or target-disk guarantees. It does not inspect arbitrary removable drives or radios. An existing inventory can be supplied using `--inventory inventory.json`.

Media intentions:

* **seed** — eventual network-assisted install bootstrap;
* **grow** — eventual verified offline boot/installer and minimal application payload;
* **forest** — eventual full offline reference and recovery bundle.

In 001 **none is built**. All plans retain missing asset / package closure gates. On non-amd64 hardware, no supported image is falsely assumed. The preexisting `genesis-001-live-iso` recipe is itself an unverified Debian bookworm **live ISO with installer disabled**; SUITCASE 001 does **not** enable disk installation.

## Authority and privacy

Every mode defaults to private. The public-candidate request never activates discovery. Protected room categorically refuses public-candidate. The composer never generates organization keys, selects a sovereign identity, publishes ancestral relationships, starts services, transmits radio, opens a socket, installs software, or modifies disks. It only prints an inspectable JSON candidate. There are no real partner enrollments or grants.

`plan_sha256` is an unkeyed checksum over a deterministic canonicalized proposal. It is **not a signature**, human agreement, legal charter, source closure, image verification, network identity, or installation receipt. `verify` regenerates the full expected proposal and refuses tampering and unrecognized authority fields.

## Next actual engineering gates

1. Run this tool on an expendable known device; independently inspect hardware and power; record a test receipt.
2. Supply a reviewed base-image matrix and cryptographically verified offline package closure for the intended architecture; pin app bytes and licenses.
3. Add an explicit preview of what will be installed, including target-disk selection, backups, rollback and clear human authorization; use disposable VM before physical disk.
4. Prove BIOS/UEFI boots, local-only services, offline operation, cross-boot persistence, and safe disconnect/reconnect. Each gate needs independent observations.
5. Prove independent reLATTE crossing with two keys/two hosts, receiver-local HOLD/REFUSE, and no private data leakage.
6. Only then test TABLELIGHT / Foundry handoffs with consenting humans; a printed charter is not an organization, and a public label is not authority.

**Laws:** `MISSION != EXECUTION`; `PROBE != HARDWARE CERTIFICATION`; `PLAN != INSTALL`; `PROFILE != SERVICE DEPLOYMENT`; `PUBLIC-CANDIDATE != PUBLICATION`; `ANCESTRY != AUTHORITY`; `OFFLINE INTENT != OFFLINE PROOF`.
