import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import {
  acceptHeld,
  fileImport,
  fileOffer,
  houseStatus,
  initHouse,
  lanSend,
  pullHeldArtifacts,
  startPeer,
} from "./roadkit-001.ts";

async function writeJson(path: string, value: unknown) {
  await writeFile(path, JSON.stringify(value, null, 2) + "\n", "utf8");
}

async function main() {
  const [relatteRootArg, tranchRootArg, outputRootArg] = process.argv.slice(2);
  if (!relatteRootArg || !tranchRootArg || !outputRootArg) {
    throw new Error(
      "usage: roadkit-contract.ts <relatte-root> <tranchnode-root> <output-root>",
    );
  }

  const relatteRoot = resolve(relatteRootArg);
  const tranchRoot = resolve(tranchRootArg);
  const outputRoot = resolve(outputRootArg);
  await mkdir(outputRoot, { recursive: true });

  const specimen = join(outputRoot, "specimen.txt");
  await writeFile(
    specimen,
    [
      "ROADKIT-001",
      "A house may carry another house's history without carrying its authority.",
      "RECEIVED != ADMITTED",
      "PULLED != ADMITTED",
    ].join("\n") + "\n",
    "utf8",
  );

  const specPath = join(outputRoot, "offer.json");
  await writeJson(specPath, {
    schema: "static.roadkit-offer-spec/v0",
    declared_kind: "static.roadkit-specimen/v0",
    requested_effect: "index-roadkit-specimen",
    privacy_policy: "public-test-specimen",
    audience_policy: "receiver-local-decision",
    artifacts: [
      {
        role: "specimen",
        path: specimen,
        media_type: "text/plain",
      },
    ],
  });

  // ROAD 1 — REMOVABLE FILE CARRIER
  const fileA = join(outputRoot, "file-house-a");
  const fileB = join(outputRoot, "file-house-b");
  const carrier = join(outputRoot, "carrier");

  const initFileA = await initHouse(relatteRoot, tranchRoot, fileA, {
    house_id: "static-house:file-a",
    world_id: "static-world:file-a",
    label: "File House A",
  });
  const initFileB = await initHouse(relatteRoot, tranchRoot, fileB, {
    house_id: "static-house:file-b",
    world_id: "static-world:file-b",
    label: "File House B",
  });
  assert.notEqual(initFileA.identity_ref, initFileB.identity_ref);

  const fileSent = await fileOffer(
    relatteRoot,
    tranchRoot,
    fileA,
    specPath,
    carrier,
  );
  assert.equal(fileSent.status, "file-carrier-created");

  const fileReceived = await fileImport(
    relatteRoot,
    tranchRoot,
    fileB,
    carrier,
  );
  assert.equal(fileReceived.status, "foreign-crossing-held");
  assert.equal(fileReceived.receiver_disposition, "HOLD");
  assert.equal(fileReceived.semantic_effect, "none");
  assert.equal(fileReceived.crossing_id, fileSent.crossing_id);

  const fileBeforeAccept = await houseStatus(relatteRoot, tranchRoot, fileB);
  assert.ok(fileBeforeAccept.receiver.held.includes(fileSent.crossing_id));
  assert.equal(fileBeforeAccept.receiver.admitted.includes(fileSent.crossing_id), false);

  const fileAccepted = await acceptHeld(
    relatteRoot,
    tranchRoot,
    fileB,
    fileSent.crossing_id,
    "index-roadkit-specimen",
  );
  assert.equal(fileAccepted.foreign_disposition, "R3_HOLD");
  assert.notEqual(fileAccepted.local_crossing_id, fileSent.crossing_id);

  const fileAStatus = await houseStatus(relatteRoot, tranchRoot, fileA);
  const fileBStatus = await houseStatus(relatteRoot, tranchRoot, fileB);
  assert.ok(fileAStatus.receiver.admitted.includes(fileSent.crossing_id));
  assert.ok(fileBStatus.receiver.held.includes(fileSent.crossing_id));
  assert.ok(fileBStatus.receiver.admitted.includes(fileAccepted.local_crossing_id));
  assert.equal(fileBStatus.receiver.admitted.includes(fileSent.crossing_id), false);
  assert.notEqual(fileAStatus.receiver.state_ref, fileBStatus.receiver.state_ref);

  // ROAD 2 — LIVE HTTP CROSSING + EXPLICIT MATERIAL PULL
  const lanA = join(outputRoot, "lan-house-a");
  const lanB = join(outputRoot, "lan-house-b");

  const initLanA = await initHouse(relatteRoot, tranchRoot, lanA, {
    house_id: "static-house:lan-a",
    world_id: "static-world:lan-a",
    label: "LAN House A",
  });
  const initLanB = await initHouse(relatteRoot, tranchRoot, lanB, {
    house_id: "static-house:lan-b",
    world_id: "static-world:lan-b",
    label: "LAN House B",
  });
  assert.notEqual(initLanA.identity_ref, initLanB.identity_ref);

  const peerA = await startPeer(relatteRoot, tranchRoot, lanA, {
    host: "127.0.0.1",
    relay_port: 0,
    artifact_port: 0,
  });
  const peerB = await startPeer(relatteRoot, tranchRoot, lanB, {
    host: "127.0.0.1",
    relay_port: 0,
    artifact_port: 0,
  });

  let lanSent: any;
  try {
    lanSent = await lanSend(
      relatteRoot,
      tranchRoot,
      lanA,
      specPath,
      peerB.relay_url,
      peerA.artifact_base_url,
    );
    assert.equal(lanSent.status, "lan-crossing-delivered");
    assert.equal(lanSent.semantic_effect_at_receiver, "none");
    assert.equal(lanSent.ack.semantic_effect, "none");

    const lanHeld = await houseStatus(relatteRoot, tranchRoot, lanB);
    assert.ok(lanHeld.receiver.held.includes(lanSent.crossing_id));
    assert.equal(lanHeld.receiver.admitted.includes(lanSent.crossing_id), false);

    const pulled = await pullHeldArtifacts(
      relatteRoot,
      tranchRoot,
      lanB,
      lanSent.crossing_id,
    );
    assert.equal(pulled.status, "held-artifacts-pulled");
    assert.equal(pulled.semantic_effect, "none");
    assert.equal(pulled.law, "PULLED != ADMITTED");
    assert.ok(pulled.imported.length >= 2);

    const afterPull = await houseStatus(relatteRoot, tranchRoot, lanB);
    assert.ok(afterPull.receiver.held.includes(lanSent.crossing_id));
    assert.equal(afterPull.receiver.admitted.includes(lanSent.crossing_id), false);

    const lanAccepted = await acceptHeld(
      relatteRoot,
      tranchRoot,
      lanB,
      lanSent.crossing_id,
      "index-roadkit-specimen",
    );
    assert.equal(lanAccepted.foreign_disposition, "R3_HOLD");

    const lanAStatus = await houseStatus(relatteRoot, tranchRoot, lanA);
    const lanBStatus = await houseStatus(relatteRoot, tranchRoot, lanB);
    assert.ok(lanAStatus.receiver.admitted.includes(lanSent.crossing_id));
    assert.ok(lanBStatus.receiver.held.includes(lanSent.crossing_id));
    assert.ok(lanBStatus.receiver.admitted.includes(lanAccepted.local_crossing_id));
    assert.equal(lanBStatus.receiver.admitted.includes(lanSent.crossing_id), false);
    assert.notEqual(lanAStatus.receiver.state_ref, lanBStatus.receiver.state_ref);

    // Reopen from disk through houseStatus and require identical durable state.
    const reopened = await houseStatus(relatteRoot, tranchRoot, lanB);
    assert.deepEqual(reopened.receiver, lanBStatus.receiver);

    const proof = {
      schema: "static.roadkit-proof/v0",
      id: "ROADKIT-001",
      proof: "PASS",
      removable_file: {
        crossing_id: fileSent.crossing_id,
        source_disposition: "ADMIT",
        receiver_foreign_disposition: "HOLD",
        receiver_local_crossing_id: fileAccepted.local_crossing_id,
        receiver_local_disposition: "ADMIT",
        source_identity_ref: initFileA.identity_ref,
        receiver_identity_ref: initFileB.identity_ref,
        source_state_ref: fileAStatus.receiver.state_ref,
        receiver_state_ref: fileBStatus.receiver.state_ref,
      },
      lan_http: {
        crossing_id: lanSent.crossing_id,
        source_disposition: "ADMIT",
        receiver_foreign_disposition: "HOLD",
        explicit_pull_before_accept: true,
        pulled_is_semantic_effect: false,
        receiver_local_disposition: "ADMIT",
        source_identity_ref: initLanA.identity_ref,
        receiver_identity_ref: initLanB.identity_ref,
        source_state_ref: lanAStatus.receiver.state_ref,
        receiver_state_ref: lanBStatus.receiver.state_ref,
      },
      invariants: {
        received_not_admitted: true,
        pulled_not_admitted: true,
        foreign_crossing_never_receiver_admitted: true,
        destination_human_recrossing_required: true,
        house_identities_distinct: true,
        shared_history_without_shared_global_state: true,
        durable_receiver_reopen: true,
      },
      claims_not_made: [
        "physical removable-drive hardware proof",
        "two-installed-machine proof",
        "encrypted LAN transport",
        "automatic peer discovery",
        "authenticated network peer identity",
      ],
    };
    await writeJson(join(outputRoot, "roadkit-001-proof.json"), proof);
    console.log(JSON.stringify(proof, null, 2));
  } finally {
    await Promise.all([peerA.close(), peerB.close()]);
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exitCode = 1;
});
