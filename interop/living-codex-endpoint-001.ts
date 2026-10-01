import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [relatteRootArg, roomRootArg, tranchRootArg, outputRootArg] = process.argv.slice(2);
if (!relatteRootArg || !roomRootArg || !tranchRootArg || !outputRootArg) {
  throw new Error(
    "usage: living-codex-endpoint-001.ts <relatte-root> <roroomom-root> <tranchnode-root> <output-root>",
  );
}

const relatteRoot = resolve(relatteRootArg);
const roomRoot = resolve(roomRootArg);
const tranchRoot = resolve(tranchRootArg);
const outputRoot = resolve(outputRootArg);

const relatte = await import(pathToFileURL(join(relatteRoot, "src/index.ts")).href);
const roomApi = await import(
  pathToFileURL(join(roomRoot, "experiments/relatte-com5-room-001/room.mjs")).href
);
const tranch = await import(pathToFileURL(join(tranchRoot, "src/artifact-store.ts")).href);

const {
  LocalReceiver,
  generateP256KeyPair,
  sealCrossingEnvelope,
  verifyCrossingEnvelope,
  makeTransportFrame,
  writeFileBundle,
  readFileBundle,
  verifyReceipt,
} = relatte;

const {
  openNavigator,
  enterDoor,
  acceptMediaResolution,
  acceptLocalTextBytes,
  compileRoomScore,
  actRoomScore,
  createPerformanceMemory,
  createHumanOffer,
  createGuestPortPacket,
  createGuestPortResponse,
  importGuestPortResponse,
  resolveHumanAiCrossing,
} = roomApi;

const { FilesystemArtifactStore, artifactAddress } = tranch;

const jsonBytes = (value: unknown) =>
  Buffer.from(JSON.stringify(value, null, 2) + "\n", "utf8");

const digestOf = (address: string) => {
  const match = /^sha256:([a-f0-9]{64})$/.exec(address);
  if (!match) throw new Error("INVALID_SHA256_ADDRESS");
  return match[1];
};

async function putJson(store: InstanceType<typeof FilesystemArtifactStore>, value: unknown) {
  return store.put(jsonBytes(value));
}

async function expectMissing(
  store: InstanceType<typeof FilesystemArtifactStore>,
  address: string,
) {
  let missing = false;
  try {
    await store.get(address);
  } catch (error: any) {
    missing = error?.code === "ARTIFACT_NOT_FOUND";
  }
  assert.equal(missing, true);
}

await mkdir(outputRoot, { recursive: true });
const houseARoot = join(outputRoot, "house-a");
const houseBRoot = join(outputRoot, "house-b");
const houseAArtifactsRoot = join(houseARoot, "tranchnode");
const houseBArtifactsRoot = join(houseBRoot, "tranchnode");
await mkdir(houseAArtifactsRoot, { recursive: true });
await mkdir(houseBArtifactsRoot, { recursive: true });

const houseAStore = new FilesystemArtifactStore(houseAArtifactsRoot);
const houseBStore = new FilesystemArtifactStore(houseBArtifactsRoot);

const audioBytes = Buffer.from("living-codex-endpoint-001 audio specimen\n", "utf8");
const videoBytes = Buffer.from("living-codex-endpoint-001 video specimen\n", "utf8");
const lyricBytes = Buffer.from(
  [
    "The house remembers.",
    "The road crosses.",
    "House A offers.",
    "House B decides.",
  ].join("\n"),
  "utf8",
);

const audioPut = await houseAStore.put(audioBytes);
const videoPut = await houseAStore.put(videoBytes);
const lyricPut = await houseAStore.put(lyricBytes);

const fixturePath = join(
  roomRoot,
  "experiments/relatte-com5-room-001/fixture-enterable-song.json",
);
const packet = JSON.parse(await readFile(fixturePath, "utf8"));
packet.subject = "relatte-crossing-v0:living-codex-source-particular";
for (const door of packet.doors) {
  for (const observation of door.observations ?? []) {
    if (observation.subject) observation.subject = packet.subject;
  }
}
for (const media of packet.media_refs) {
  media.source_crossing_id = packet.subject;
  if (media.role === "song") {
    media.address = audioPut.address;
    media.media_type = "audio/mpeg";
  }
  if (media.role === "lyrics") {
    media.address = lyricPut.address;
    media.media_type = "text/plain";
  }
  if (media.role === "video") {
    media.address = videoPut.address;
    media.media_type = "video/mp4";
  }
}
const compose = packet.doors.find((door: any) => door.role === "COMPOSE");
assert.ok(compose);
for (const instrument of compose.instruments) {
  if (instrument.kind === "audio-player") {
    instrument.ref = audioPut.address;
    instrument.media_type = "audio/mpeg";
  }
  if (instrument.kind === "text-sheet") {
    instrument.ref = lyricPut.address;
    instrument.media_type = "text/plain";
  }
  if (instrument.kind === "video-player") {
    instrument.ref = videoPut.address;
    instrument.media_type = "video/mp4";
  }
}

const navigator = openNavigator(packet);
assert.equal(navigator.ok, true);
let encounter = enterDoor(
  navigator,
  "COMPOSE",
  true,
  "room-encounter:living-codex-endpoint-001",
);
assert.equal(encounter.ok, true);

const audioDigest = digestOf(audioPut.address);
encounter = acceptMediaResolution(encounter, "lego:2:audio-player", {
  organ: "autodiscography-vault.audio-resolver-v0",
  status: "resolved-verified",
  address: audioPut.address,
  sha256: audioDigest,
  mediaType: "audio/mpeg",
  byteLength: audioBytes.byteLength,
  playbackUrl: `http://127.0.0.1:45101/v0/media/${audioDigest}`,
  authority: "none",
});
assert.equal(encounter.ok, true);

const videoDigest = digestOf(videoPut.address);
encounter = acceptMediaResolution(encounter, "lego:4:video-player", {
  organ: "haunted-blender.accepted-video-resolver-v0",
  status: "resolved-filmmaker-accepted-private-take",
  address: videoPut.address,
  sha256: videoDigest,
  mediaType: "video/mp4",
  byteLength: videoBytes.byteLength,
  playbackUrl: `http://127.0.0.1:45102/v0/media/${videoDigest}`,
  distributionAuthorized: false,
  authority: "none",
});
assert.equal(encounter.ok, true);

encounter = await acceptLocalTextBytes(encounter, "lego:3:text-sheet", lyricBytes);
assert.equal(encounter.ok, true);

encounter = compileRoomScore(encounter, {
  schema: "roroomom.room-score/v0",
  title: "Living Codex Endpoint 001",
  clock: "lego:2:audio-player",
  mediaTracks: [
    { instrument: "lego:2:audio-player", offsetMs: 0 },
    { instrument: "lego:4:video-player", offsetMs: 250 },
  ],
  lyricTrack: {
    instrument: "lego:3:text-sheet",
    cues: [
      { atMs: 0, fromLine: 1, toLine: 2 },
      { atMs: 8000, fromLine: 3, toLine: 4 },
    ],
  },
});
assert.equal(encounter.ok, true);
encounter = actRoomScore(encounter, "CONDUCT");
assert.equal(encounter.ok, true);

const playMemory = await createPerformanceMemory(encounter, {
  verdict: "weird",
  reopenRequested: true,
});
assert.equal(playMemory.schema, "roroomom.performance-memory/v0");

const humanOffer = await createHumanOffer(encounter, {
  intent:
    "Try one bounded nearby timing mutation, preserve every source, and let the accepted encounter become portable memory.",
  offeredInstruments: [
    "lego:2:audio-player",
    "lego:4:video-player",
    "lego:3:text-sheet",
  ],
  allowedActions: [
    "INSPECT_ROOM_SCORE",
    "READ_PLAY_MEMORY",
    "PROPOSE_MEDIA_OFFSET_MS",
  ],
  memoryPolicy: { enabled: true, allowedVerdicts: ["weird"] },
  maxOffsetDeltaMs: 500,
});
assert.equal(humanOffer.schema, "roroomom.human-offer/v0");

const guestPort = await createGuestPortPacket(encounter, [playMemory], humanOffer);
assert.equal(guestPort.schema, "roroomom.guest-port/v0");

const guestResponse = await createGuestPortResponse(guestPort, {
  schema: "roroomom.guest-response-draft/v0",
  participant: {
    type: "ai-participant",
    id: "ai:living-codex-guest",
    label: "Living Codex Guest",
    provider: "portable-draft",
    model: "guest-specimen-v0",
  },
  understanding:
    "I may use only the offered material and invited WEIRD memory and may propose one bounded local timing change.",
  uncertainties: ["The human remains the only authority for consequence."],
  proposal: {
    op: "SET_MEDIA_OFFSET_MS",
    instrument: "lego:4:video-player",
    value: 500,
    rationale: "Try the offered video 250 ms later without changing any source.",
  },
});
assert.equal(guestResponse.schema, "roroomom.guest-port-response/v0");

const importedGuest = await importGuestPortResponse(
  encounter,
  [playMemory],
  humanOffer,
  guestPort,
  guestResponse,
);
assert.equal(importedGuest.ok, true);
assert.ok(importedGuest.proposal);

const acceptedRoom = await resolveHumanAiCrossing(
  encounter,
  importedGuest.proposal,
  "ACCEPT",
);
assert.equal(acceptedRoom.ok, true);
assert.equal(acceptedRoom.crossingReceipt.decision, "ACCEPT");
assert.equal(acceptedRoom.crossingReceipt.changed, true);
assert.equal(acceptedRoom.room.sourceMutated, false);
assert.equal(acceptedRoom.room.sharedWorldChanged, false);

const memoryPut = await putJson(houseAStore, playMemory);
const roomDecisionPut = await putJson(houseAStore, acceptedRoom.crossingReceipt);

const houseAGenesis = {
  schema: "static.seed-house/v0",
  house_id: "static-house:a",
  world_id: "static-world:a",
  role: "source-house",
  artifact_store: "tranchnode.filesystem-artifact-store",
  authority: "local",
};
const houseAGenesisPut = await putJson(houseAStore, houseAGenesis);

const houseAReceiver = await LocalReceiver.create(join(houseARoot, "relatte-receiver"), {
  world_id: "static-world:a",
  receiver_particular: "static-house:a",
  contract_ref: "static:living-codex-endpoint-001",
});
const houseBReceiver = await LocalReceiver.create(join(houseBRoot, "relatte-receiver"), {
  world_id: "static-world:b",
  receiver_particular: "static-house:b",
  contract_ref: "static:living-codex-endpoint-001",
});

const houseAKeys = await generateP256KeyPair();
const outgoingCrossing = await sealCrossingEnvelope(
  {
    schema: "relatte.crossing-envelope/v0",
    protocol_version: "0",
    source_particular: "static-house:a",
    source_world: "static-world:a",
    source_history_head: acceptedRoom.crossingReceipt.receiptId,
    parents: [acceptedRoom.crossingReceipt.receiptId],
    declared_kind: "static.living-codex-room-memory/v0",
    payload_refs: [
      {
        address: memoryPut.address,
        role: "play-memory",
        media_type: "application/json",
      },
      {
        address: roomDecisionPut.address,
        role: "human-ai-decision",
        media_type: "application/json",
      },
      {
        address: houseAGenesisPut.address,
        role: "source-house-genesis",
        media_type: "application/json",
      },
    ],
    requested_effect: "consider-local-reentry",
    capability_ref: null,
    privacy_policy: "explicit-file-bundle",
    audience_policy: "named-receiver-local-decision",
    return_address: null,
    created_at: "2026-10-01T22:00:00.000Z",
    extensions: {
      living_codex_endpoint: {
        schema: "static.living-codex-crossing/v0",
        human_governed_room_receipt: acceptedRoom.crossingReceipt.receiptId,
        laws: [
          "ROOM CONSEQUENCE != REMOTE AUTHORITY",
          "PAYLOAD ADDRESS != ADMISSION",
        ],
      },
    },
  },
  houseAKeys,
);
assert.equal(await verifyCrossingEnvelope(outgoingCrossing), true);

const houseAReceive = await houseAReceiver.receive(
  outgoingCrossing,
  "2026-10-01T22:00:01.000Z",
);
assert.equal(houseAReceive.kind, "RECEIVED");
const houseAAdmit = await houseAReceiver.dispose(
  outgoingCrossing.crossing_id,
  "ADMIT",
  "2026-10-01T22:00:02.000Z",
  {
    note: "House A locally admits the room-governed memory crossing before export.",
    admit_effect: "local-room-memory-committed",
    descendant_refs: [roomDecisionPut.address],
  },
);
assert.equal(houseAAdmit.kind, "R3_ADMIT");
assert.equal(await verifyReceipt(houseAAdmit), true);

const frame = await makeTransportFrame(
  outgoingCrossing,
  "file-bundle",
  "2026-10-01T22:00:03.000Z",
  "LIVING-CODEX-ENDPOINT-001 removable-file specimen",
);
const carrierRoot = join(outputRoot, "carrier");
await mkdir(join(carrierRoot, "objects"), { recursive: true });
await writeFileBundle(join(carrierRoot, "crossing.frame.json"), frame);

const attachmentManifest = {
  schema: "static.file-crossing-bundle/v0",
  transport_id: frame.transport_id,
  crossing_id: outgoingCrossing.crossing_id,
  attachments: [] as Array<{
    address: string;
    role: string;
    path: string;
    byteLength: number;
  }>,
  authority: "transport-only",
  laws: [
    "TRANSPORT != AUTHORITY",
    "ATTACHMENT PRESENCE != ADMISSION",
    "CONTENT ADDRESS != LOCAL CONSEQUENCE",
  ],
};

for (const ref of outgoingCrossing.payload_refs) {
  const bytes = await houseAStore.get(ref.address);
  const filename = `${digestOf(ref.address)}.bin`;
  const relativePath = join("objects", filename);
  await writeFile(join(carrierRoot, relativePath), bytes);
  attachmentManifest.attachments.push({
    address: ref.address,
    role: ref.role,
    path: relativePath,
    byteLength: bytes.byteLength,
  });
}
await writeFile(
  join(carrierRoot, "bundle.json"),
  JSON.stringify(attachmentManifest, null, 2) + "\n",
  "utf8",
);

const { crossing: receivedCrossing, frame: receivedFrame } = await readFileBundle(
  join(carrierRoot, "crossing.frame.json"),
);
assert.equal(receivedFrame.transport_id, frame.transport_id);
assert.equal(receivedCrossing.crossing_id, outgoingCrossing.crossing_id);

const receivedManifest = JSON.parse(await readFile(join(carrierRoot, "bundle.json"), "utf8"));
assert.equal(receivedManifest.crossing_id, receivedCrossing.crossing_id);
assert.equal(receivedManifest.authority, "transport-only");

for (const attachment of receivedManifest.attachments) {
  const bytes = await readFile(join(carrierRoot, attachment.path));
  assert.equal(artifactAddress(bytes), attachment.address);
  assert.equal(bytes.byteLength, attachment.byteLength);
  const imported = await houseBStore.put(bytes);
  assert.equal(imported.address, attachment.address);
}

assert.deepEqual(
  receivedCrossing.payload_refs.map((entry: any) => entry.address).sort(),
  receivedManifest.attachments.map((entry: any) => entry.address).sort(),
);

const houseBReceive = await houseBReceiver.receive(
  receivedCrossing,
  "2026-10-01T22:00:04.000Z",
);
assert.equal(houseBReceive.kind, "RECEIVED");
assert.equal(houseBReceive.semantic_effect, "none");

const houseBHold = await houseBReceiver.dispose(
  receivedCrossing.crossing_id,
  "HOLD",
  "2026-10-01T22:00:05.000Z",
  {
    note: "Foreign crossing remains held; verification does not import House A authority.",
  },
);
assert.equal(houseBHold.kind, "R3_HOLD");
assert.equal(houseBHold.semantic_effect, "none");
assert.equal(await verifyReceipt(houseBHold), true);

const humanAdmissionIntent = {
  schema: "static.house-human-admission/v0",
  house_id: "static-house:b",
  foreign_crossing_id: receivedCrossing.crossing_id,
  foreign_hold_receipt_id: houseBHold.receipt_id,
  decision: "ACCEPT",
  requested_local_effect: "index-memory-for-local-reentry",
  authority: "human-local-decision",
  laws: [
    "FOREIGN CROSSING != LOCAL CONSEQUENCE",
    "HOLD != ADMIT",
    "ACCEPTANCE REQUIRES LOCAL RE-CROSSING",
  ],
};
const humanAdmissionPut = await putJson(houseBStore, humanAdmissionIntent);

const houseBHumanKeys = await generateP256KeyPair();
const localAdmissionCrossing = await sealCrossingEnvelope(
  {
    schema: "relatte.crossing-envelope/v0",
    protocol_version: "0",
    source_particular: "static-house:b/human-steward",
    source_world: "static-world:b",
    source_history_head: houseBHold.receipt_id,
    parents: [receivedCrossing.crossing_id],
    declared_kind: "static.local-admission-request/v0",
    payload_refs: [
      {
        address: humanAdmissionPut.address,
        role: "human-admission-intent",
        media_type: "application/json",
      },
      ...receivedCrossing.payload_refs,
    ],
    requested_effect: "index-memory-for-local-reentry",
    capability_ref: "static:human-local-admission/v0",
    privacy_policy: "local-house-only",
    audience_policy: "static-house:b",
    return_address: null,
    created_at: "2026-10-01T22:00:06.000Z",
    extensions: {
      living_codex_endpoint: {
        foreign_crossing_id: receivedCrossing.crossing_id,
        foreign_hold_receipt_id: houseBHold.receipt_id,
        explicit_human_recrossing: true,
      },
    },
  },
  houseBHumanKeys,
);
assert.equal(await verifyCrossingEnvelope(localAdmissionCrossing), true);
assert.notDeepEqual(
  outgoingCrossing.signing.public_key,
  localAdmissionCrossing.signing.public_key,
);

const houseBLocalReceive = await houseBReceiver.receive(
  localAdmissionCrossing,
  "2026-10-01T22:00:07.000Z",
);
assert.equal(houseBLocalReceive.kind, "RECEIVED");

const localConsequence = {
  schema: "static.local-memory-consequence/v0",
  world_id: "static-world:b",
  receiver_particular: "static-house:b",
  foreign_crossing_id: receivedCrossing.crossing_id,
  foreign_hold_receipt_id: houseBHold.receipt_id,
  human_admission_crossing_id: localAdmissionCrossing.crossing_id,
  source_payload_refs: receivedCrossing.payload_refs.map((entry: any) => entry.address).sort(),
  effect: "memory-indexed-for-local-reentry",
  authority: "local-only",
  laws: [
    "LOCAL CONSEQUENCE != SOURCE MUTATION",
    "SHARED HISTORY != SHARED GLOBAL STATE",
  ],
};
const localConsequencePut = await putJson(houseBStore, localConsequence);

const houseBAdmit = await houseBReceiver.dispose(
  localAdmissionCrossing.crossing_id,
  "ADMIT",
  "2026-10-01T22:00:08.000Z",
  {
    note: "House B human re-crossing creates one local consequence.",
    admit_effect: "memory-indexed-for-local-reentry",
    descendant_refs: [localConsequencePut.address],
  },
);
assert.equal(houseBAdmit.kind, "R3_ADMIT");
assert.equal(houseBAdmit.semantic_effect, "memory-indexed-for-local-reentry");
assert.equal(await verifyReceipt(houseBAdmit), true);

const houseASnapshot = houseAReceiver.snapshot();
const houseBSnapshot = houseBReceiver.snapshot();
assert.equal(houseASnapshot.world_id, "static-world:a");
assert.equal(houseBSnapshot.world_id, "static-world:b");
assert.notEqual(houseASnapshot.state_ref, houseBSnapshot.state_ref);
assert.ok(houseASnapshot.admitted.includes(outgoingCrossing.crossing_id));
assert.ok(houseBSnapshot.held.includes(outgoingCrossing.crossing_id));
assert.ok(houseBSnapshot.admitted.includes(localAdmissionCrossing.crossing_id));
assert.equal(houseBSnapshot.admitted.includes(outgoingCrossing.crossing_id), false);

const reopenedB = await LocalReceiver.open(join(houseBRoot, "relatte-receiver"));
assert.deepEqual(reopenedB.snapshot(), houseBSnapshot);
assert.equal(reopenedB.journalLength(), houseBReceiver.journalLength());

const importedMemoryBytes = await houseBStore.get(memoryPut.address);
assert.deepEqual(importedMemoryBytes, await houseAStore.get(memoryPut.address));
const persistedConsequence = JSON.parse(
  (await houseBStore.get(localConsequencePut.address)).toString("utf8"),
);
assert.equal(persistedConsequence.foreign_crossing_id, outgoingCrossing.crossing_id);

await expectMissing(houseAStore, humanAdmissionPut.address);
await expectMissing(houseAStore, localConsequencePut.address);

const summary = {
  schema: "static.living-codex-endpoint-proof/v0",
  id: "LIVING-CODEX-ENDPOINT-001",
  proof: "PASS",
  houses: {
    a: {
      world_id: houseASnapshot.world_id,
      state_ref: houseASnapshot.state_ref,
      exported_crossing_id: outgoingCrossing.crossing_id,
      disposition: "ADMIT",
      durable_memory_ref: memoryPut.address,
      durable_decision_ref: roomDecisionPut.address,
    },
    b: {
      world_id: houseBSnapshot.world_id,
      state_ref: houseBSnapshot.state_ref,
      foreign_crossing_disposition: "HOLD",
      human_local_crossing_id: localAdmissionCrossing.crossing_id,
      human_local_disposition: "ADMIT",
      local_consequence_ref: localConsequencePut.address,
      durable_reopen_verified: true,
    },
  },
  transport: {
    kind: "file-bundle",
    transport_id: frame.transport_id,
    attachment_count: receivedManifest.attachments.length,
    all_attachments_content_address_verified: true,
  },
  invariants: {
    same_foreign_crossing_different_local_consequence: true,
    node_signing_identity_distinct: true,
    shared_history_without_shared_global_state: true,
    foreign_crossing_not_admitted_by_house_b: true,
    human_local_recrossing_required_for_house_b_consequence: true,
    house_b_local_artifacts_absent_from_house_a: true,
  },
  laws: [
    "TRANSPORT != AUTHORITY",
    "RECEIVED != ADMITTED",
    "HOLD != ADMIT",
    "FOREIGN CROSSING != LOCAL CONSEQUENCE",
    "HUMAN ACCEPTANCE REQUIRES LOCAL RE-CROSSING",
    "SHARED HISTORY != SHARED GLOBAL STATE",
  ],
};

const proofPath = join(outputRoot, "living-codex-endpoint-001-proof.json");
await mkdir(dirname(proofPath), { recursive: true });
await writeFile(proofPath, JSON.stringify(summary, null, 2) + "\n", "utf8");
console.log(JSON.stringify(summary, null, 2));
