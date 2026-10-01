# ROADKIT-001

Status: deployment candidate

ROADKIT-001 turns LIVING-CODEX-ENDPOINT-001 into two operator-usable roads without creating a new authority layer.

## Roads

### 1. Removable-file road

An operator creates a new carrier directory on any ordinary writable filesystem, including a mounted removable drive:

    static-roadkit file-offer HOUSE offer.json /media/USB/CARRIER

The carrier contains a signed reLATTE file-bundle frame, exact content-addressed attachment bytes, a transport-only manifest, and the source House's signed local ADMIT receipt.

The receiving House runs:

    static-roadkit file-import HOUSE /media/USB/CARRIER

Import verifies the crossing signature, every attachment address, the source ADMIT receipt, and the source House identity/key binding. The foreign crossing then lands at `R3_HOLD` with semantic effect `none`.

The operator must separately run:

    static-roadkit accept HOUSE <foreign-crossing-id> <local-effect>

`accept` creates a fresh locally signed human re-crossing and admits only that new crossing.

### 2. LAN HTTP road

Each House may expose two explicit HTTP surfaces:

- a reLATTE relay endpoint for signed crossing frames;
- a read-only content-addressed artifact endpoint.

Start a peer:

    static-roadkit peer HOUSE 45110 45111 127.0.0.1

The command defaults to loopback. Binding a LAN address is an explicit operator choice.

Send one crossing:

    static-roadkit lan-send HOUSE offer.json \
      http://PEER:45110/relatte/v0/crossings \
      http://THIS-HOUSE:45111/roadkit/v0/artifacts/

The receiving relay verifies and records the crossing, then places it at HOLD. It does **not** automatically fetch payload bytes.

The receiving human separately chooses:

    static-roadkit pull HOUSE <foreign-crossing-id>

`pull` retrieves only the exact content-addressed payload refs from the crossing's declared artifact return address, verifies every SHA-256 address, and stores the bytes in the receiver's own TranchNode store.

Even after all bytes are present:

    PULLED != ADMITTED

The crossing remains HOLD until a human invokes `accept`.

## House identity surface

`static-roadkit init` creates a local House identity capsule:

    static.house-identity/v0

It contains:

- House id;
- world id;
- label;
- the House crossing-signing public key;
- creation time;
- explicit `self-asserted-local` authority.

The identity capsule is stored by TranchNode content address and is included in every outgoing RoadKit crossing.

On file import and LAN pull, ROADKIT verifies that:

- the identity artifact address is exact;
- its House id equals the crossing source particular;
- its world id equals the crossing source world;
- its public key equals the public key that actually signed the crossing.

This proves a cryptographic relationship between the self-declared House identity and the crossing signer. It does **not** prove a human identity or external trust relationship.

    SIGNED HOUSE IDENTITY != HUMAN IDENTITY
    PEER ADDRESS != PEER IDENTITY

Inspect the local identity and receiver receipts with:

    static-roadkit status HOUSE

## User-space setup

ROADKIT does not install system packages or run as root.

From a STATIC OS checkout:

    bash scripts/roadkit-setup.sh --install

This fetches the exact reLATTE and TranchNode commits pinned in `manifest/roadkit-001.json` into:

    ~/.local/share/static-roadkit-001/sources/

Then use:

    bash scripts/roadkit.sh --help

The bootstrap refuses to reset or overwrite an existing donor checkout at a different origin or revision.

## Offer spec

Example:

    {
      "schema": "static.roadkit-offer-spec/v0",
      "declared_kind": "static.example/v0",
      "requested_effect": "consider-local-reentry",
      "privacy_policy": "operator-selected-road",
      "audience_policy": "receiver-local-decision",
      "artifacts": [
        {
          "role": "note",
          "path": "/home/me/note.txt",
          "media_type": "text/plain"
        }
      ]
    }

ROADKIT-001 limits each artifact to 16 MiB and one offer to 64 MiB total. Symlinked artifacts are refused.

## Persistence layout

Each House root contains independent local state:

    HOUSE/
      house.json
      crossing-key.json
      relatte-receiver/
      tranchnode/
      inbox/
      outbox/
      receipts/

`crossing-key.json` is created with user-only file permissions. Receiver state is independently journaled by reLATTE.

## Laws

    TRANSPORT != AUTHORITY
    RECEIVED != ADMITTED
    PULLED != ADMITTED
    HOLD != ADMIT
    FOREIGN CROSSING != LOCAL CONSEQUENCE
    HUMAN ACCEPTANCE REQUIRES LOCAL RE-CROSSING
    SOURCE ADMIT != RECEIVER ADMIT
    SHARED HISTORY != SHARED GLOBAL STATE
    PEER ADDRESS != PEER IDENTITY
    CONTENT ADDRESS != SEMANTIC TRUST

## Current security boundary

The LAN road is plain HTTP in ROADKIT-001. Signatures protect crossing integrity/authorship-by-key and content addresses protect payload integrity, but the transport does not provide confidentiality.

Do not use the LAN road for private material on an untrusted network.

ROADKIT-001 also does not perform automatic discovery. A peer address is supplied by the operator.

## Contract proof

`interop/roadkit-contract.ts` creates four fresh houses and proves both roads:

1. File House A locally ADMITs an outgoing crossing.
2. File House B verifies/imports it and keeps the foreign crossing at HOLD.
3. File House B creates a fresh human re-crossing and ADMITs only that local crossing.
4. LAN House A serves exact addressed artifacts and sends a signed crossing over reLATTE HTTP transport.
5. LAN House B receives and HOLDs it with no semantic effect.
6. LAN House B explicitly pulls exact bytes; the crossing remains HOLD.
7. LAN House B explicitly creates and ADMITs a local human re-crossing.
8. Reopening the receiver from disk reconstructs the same receiver state.
9. Source and receiver Houses retain distinct identities and distinct state refs.

## Claims not yet made

ROADKIT-001 is not yet evidence of:

- a physical removable-drive test;
- two installed STATIC OS machines communicating;
- encrypted LAN transport;
- automatic peer discovery;
- authenticated human/network peer identity;
- Bluetooth, LoRa, or QR transport.

The next physical gate is intentionally simple: run the existing file-road proof across a real removable drive between two separately initialized machines, then run the HTTP road between those same machines.
