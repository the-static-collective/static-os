import assert from "node:assert/strict";
import { createServer } from "node:http";
import {
  chmod,
  lstat,
  mkdir,
  readFile,
  realpath,
  stat,
  writeFile,
} from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const MAX_ARTIFACT_BYTES = 16 * 1024 * 1024;
const MAX_TOTAL_BYTES = 64 * 1024 * 1024;
const HOUSE_SCHEMA = "static.roadkit-house/v0";
const IDENTITY_SCHEMA = "static.house-identity/v0";
const SPEC_SCHEMA = "static.roadkit-offer-spec/v0";

function now() {
  return new Date().toISOString();
}

function jsonBytes(value: unknown) {
  return Buffer.from(JSON.stringify(value, null, 2) + "\n", "utf8");
}

function plain(value: unknown): value is Record<string, any> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function nonEmpty(value: unknown, code: string) {
  if (typeof value !== "string" || value.trim() === "") throw new Error(code);
  return value;
}

function safeId(value: string) {
  return value.replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 180);
}

function digestOf(address: string) {
  const match = /^sha256:([a-f0-9]{64})$/.exec(address);
  if (!match) throw new Error("INVALID_SHA256_ADDRESS");
  return match[1];
}

function requireHttpBase(value: string) {
  const url = new URL(value);
  if (
    url.protocol !== "http:" ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    !url.port ||
    !url.pathname.endsWith("/roadkit/v0/artifacts/")
  ) {
    throw new Error("INVALID_ARTIFACT_BASE_URL");
  }
  return url.toString();
}

async function exists(path: string) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

async function readJson(path: string) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function writeJson(path: string, value: unknown, mode?: number) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, JSON.stringify(value, null, 2) + "\n", {
    encoding: "utf8",
    ...(mode ? { mode } : {}),
  });
}

async function importPrivateKey(jwk: JsonWebKey) {
  return crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"],
  );
}

async function importPublicKey(jwk: JsonWebKey) {
  return crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["verify"],
  );
}

async function loadDonors(relatteRoot: string, tranchRoot: string) {
  const relatte = await import(pathToFileURL(join(resolve(relatteRoot), "src/index.ts")).href);
  const tranch = await import(pathToFileURL(join(resolve(tranchRoot), "src/artifact-store.ts")).href);
  return { relatte, tranch };
}

function housePaths(rootArg: string) {
  const root = resolve(rootArg);
  return {
    root,
    house: join(root, "house.json"),
    key: join(root, "crossing-key.json"),
    receiver: join(root, "relatte-receiver"),
    artifacts: join(root, "tranchnode"),
    inbox: join(root, "inbox"),
    outbox: join(root, "outbox"),
    receipts: join(root, "receipts"),
  };
}

async function loadHouse(rootArg: string, donors: any) {
  const paths = housePaths(rootArg);
  const house = await readJson(paths.house);
  if (house.schema !== HOUSE_SCHEMA) throw new Error("INVALID_ROADKIT_HOUSE");
  const receiver = await donors.relatte.LocalReceiver.open(paths.receiver);
  const store = new donors.tranch.FilesystemArtifactStore(paths.artifacts);
  return { paths, house, receiver, store };
}

async function loadSigningKeys(path: string) {
  const stored = await readJson(path);
  if (
    stored.schema !== "static.roadkit-crossing-key/v0" ||
    !plain(stored.private_jwk) ||
    !plain(stored.public_jwk)
  ) {
    throw new Error("INVALID_ROADKIT_KEY");
  }
  return {
    privateKey: await importPrivateKey(stored.private_jwk as JsonWebKey),
    publicKey: await importPublicKey(stored.public_jwk as JsonWebKey),
    publicKeyJwk: stored.public_jwk as JsonWebKey,
  };
}

async function putJson(store: any, value: unknown) {
  return store.put(jsonBytes(value));
}

async function verifySourceIdentityBinding(store: any, crossing: any) {
  const refs = crossing.payload_refs.filter((entry: any) => entry?.role === "source-house-identity");
  if (refs.length !== 1) throw new Error("SOURCE_IDENTITY_REF_REQUIRED");
  const identity = JSON.parse((await store.get(refs[0].address)).toString("utf8"));
  if (
    identity.schema !== IDENTITY_SCHEMA ||
    identity.house_id !== crossing.source_particular ||
    identity.world_id !== crossing.source_world ||
    identity.authority !== "self-asserted-local"
  ) {
    throw new Error("SOURCE_IDENTITY_CROSSING_MISMATCH");
  }
  const expected = crossing.signing?.public_key;
  const actual = identity.signing_public_key;
  if (
    !plain(expected) ||
    !plain(actual) ||
    expected.kty !== actual.kty ||
    expected.crv !== actual.crv ||
    expected.x !== actual.x ||
    expected.y !== actual.y
  ) {
    throw new Error("SOURCE_IDENTITY_KEY_MISMATCH");
  }
  return {
    identity_ref: refs[0].address,
    house_id: identity.house_id,
    world_id: identity.world_id,
    authority: identity.authority,
    law: "SIGNED HOUSE IDENTITY != HUMAN IDENTITY",
  };
}

async function readArtifactFile(pathArg: string) {
  const absolute = resolve(pathArg);
  const info = await lstat(absolute);
  if (info.isSymbolicLink() || !info.isFile()) throw new Error("ARTIFACT_MUST_BE_REGULAR_FILE");
  if (info.size <= 0 || info.size > MAX_ARTIFACT_BYTES) throw new Error("ARTIFACT_SIZE_OUT_OF_BOUNDS");
  const canonical = await realpath(absolute);
  const bytes = await readFile(canonical);
  return { absolute: canonical, bytes };
}

export async function initHouse(
  relatteRoot: string,
  tranchRoot: string,
  rootArg: string,
  spec: { house_id: string; world_id: string; label?: string },
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const paths = housePaths(rootArg);
  if (await exists(paths.root)) throw new Error("HOUSE_ROOT_EXISTS");

  const houseId = nonEmpty(spec.house_id, "HOUSE_ID_REQUIRED");
  const worldId = nonEmpty(spec.world_id, "WORLD_ID_REQUIRED");
  await mkdir(paths.artifacts, { recursive: true });
  await mkdir(paths.inbox, { recursive: true });
  await mkdir(paths.outbox, { recursive: true });
  await mkdir(paths.receipts, { recursive: true });

  const keys = await donors.relatte.generateP256KeyPair();
  const privateJwk = await crypto.subtle.exportKey("jwk", keys.privateKey);
  const publicJwk = await crypto.subtle.exportKey("jwk", keys.publicKey);
  await writeJson(
    paths.key,
    {
      schema: "static.roadkit-crossing-key/v0",
      private_jwk: privateJwk,
      public_jwk: publicJwk,
    },
    0o600,
  );
  await chmod(paths.key, 0o600);

  const receiver = await donors.relatte.LocalReceiver.create(paths.receiver, {
    world_id: worldId,
    receiver_particular: houseId,
    contract_ref: "static:roadkit-001",
  });
  const store = new donors.tranch.FilesystemArtifactStore(paths.artifacts);

  const identity = {
    schema: IDENTITY_SCHEMA,
    house_id: houseId,
    world_id: worldId,
    label: typeof spec.label === "string" && spec.label.trim() ? spec.label.trim() : houseId,
    signing_public_key: publicJwk,
    created_at: now(),
    authority: "self-asserted-local",
    laws: [
      "PUBLIC KEY != HUMAN IDENTITY",
      "HOUSE IDENTITY != GLOBAL IDENTITY",
      "ADDRESS != AUTHORITY",
      "REPLICATION != IDENTITY",
    ],
  };
  const identityPut = await putJson(store, identity);

  const house = {
    schema: HOUSE_SCHEMA,
    house_id: houseId,
    world_id: worldId,
    label: identity.label,
    identity_ref: identityPut.address,
    created_at: identity.created_at,
    roads: {
      file_bundle: true,
      lan_http: true,
    },
    authority: "local",
  };
  await writeJson(paths.house, house);

  return {
    ok: true,
    status: "house-initialized",
    house,
    identity,
    identity_ref: identityPut.address,
    receiver: receiver.snapshot(),
  };
}

export async function houseStatus(
  relatteRoot: string,
  tranchRoot: string,
  rootArg: string,
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(rootArg, donors);
  const identityBytes = await loaded.store.get(loaded.house.identity_ref);
  const identity = JSON.parse(identityBytes.toString("utf8"));
  const inboxEntries = await listJsonDirectory(loaded.paths.inbox);
  const outboxEntries = await listJsonDirectory(loaded.paths.outbox);
  return {
    schema: "static.roadkit-house-status/v0",
    house: loaded.house,
    identity,
    receiver: loaded.receiver.snapshot(),
    inbox_count: inboxEntries.length,
    outbox_count: outboxEntries.length,
    authority: "local-observation",
    laws: [
      "STATUS != AUTHORITY",
      "PUBLIC KEY != HUMAN IDENTITY",
      "RECEIPT != ADMISSION",
    ],
  };
}

async function listJsonDirectory(path: string) {
  const fs = await import("node:fs/promises");
  try {
    const names = await fs.readdir(path);
    return names.filter((name) => name.endsWith(".json")).sort();
  } catch {
    return [];
  }
}

async function prepareOutgoing(
  donors: any,
  loaded: any,
  specPath: string,
  returnAddress: string | null,
) {
  const spec = await readJson(resolve(specPath));
  if (spec.schema !== SPEC_SCHEMA) throw new Error("INVALID_ROADKIT_OFFER_SPEC");
  if (!Array.isArray(spec.artifacts) || spec.artifacts.length < 1 || spec.artifacts.length > 16) {
    throw new Error("INVALID_ROADKIT_ARTIFACT_SET");
  }

  const payloadRefs: any[] = [];
  let total = 0;
  for (const item of spec.artifacts) {
    if (!plain(item)) throw new Error("INVALID_ROADKIT_ARTIFACT");
    const role = nonEmpty(item.role, "ARTIFACT_ROLE_REQUIRED");
    const mediaType = nonEmpty(item.media_type, "ARTIFACT_MEDIA_TYPE_REQUIRED");
    const { bytes, absolute } = await readArtifactFile(nonEmpty(item.path, "ARTIFACT_PATH_REQUIRED"));
    total += bytes.byteLength;
    if (total > MAX_TOTAL_BYTES) throw new Error("ARTIFACT_TOTAL_TOO_LARGE");
    const put = await loaded.store.put(bytes);
    payloadRefs.push({
      address: put.address,
      role,
      media_type: mediaType,
      byte_length: bytes.byteLength,
      source_name: absolute.split("/").pop(),
    });
  }

  payloadRefs.push({
    address: loaded.house.identity_ref,
    role: "source-house-identity",
    media_type: "application/json",
  });

  const keys = await loadSigningKeys(loaded.paths.key);
  const snapshot = loaded.receiver.snapshot();
  const crossing = await donors.relatte.sealCrossingEnvelope(
    {
      schema: "relatte.crossing-envelope/v0",
      protocol_version: "0",
      source_particular: loaded.house.house_id,
      source_world: loaded.house.world_id,
      source_history_head: snapshot.history_head,
      parents: Array.isArray(spec.parents) ? spec.parents : [],
      declared_kind: nonEmpty(spec.declared_kind, "DECLARED_KIND_REQUIRED"),
      payload_refs: payloadRefs,
      requested_effect:
        typeof spec.requested_effect === "string" && spec.requested_effect.trim()
          ? spec.requested_effect
          : "consider-local-reentry",
      capability_ref: null,
      privacy_policy:
        typeof spec.privacy_policy === "string" && spec.privacy_policy.trim()
          ? spec.privacy_policy
          : "operator-selected-road",
      audience_policy:
        typeof spec.audience_policy === "string" && spec.audience_policy.trim()
          ? spec.audience_policy
          : "receiver-local-decision",
      return_address: returnAddress,
      created_at: now(),
      extensions: {
        roadkit: {
          schema: "static.roadkit-crossing/v0",
          source_identity_ref: loaded.house.identity_ref,
          source_house_id: loaded.house.house_id,
          source_world_id: loaded.house.world_id,
          law: "SOURCE ADMIT != RECEIVER ADMIT",
        },
      },
    },
    keys,
  );
  assert.equal(await donors.relatte.verifyCrossingEnvelope(crossing), true);

  const receive = await loaded.receiver.receive(crossing, now());
  const admit = await loaded.receiver.dispose(crossing.crossing_id, "ADMIT", now(), {
    note: "Source house locally admits its outgoing RoadKit crossing.",
    admit_effect: "outgoing-crossing-committed",
    descendant_refs: payloadRefs.map((entry) => entry.address),
  });
  assert.equal(await donors.relatte.verifyReceipt(admit), true);

  const outboxPath = join(loaded.paths.outbox, safeId(crossing.crossing_id) + ".json");
  const receiptPath = join(loaded.paths.receipts, safeId(admit.receipt_id) + ".json");
  await writeJson(outboxPath, crossing);
  await writeJson(receiptPath, admit);

  return { crossing, source_receive_receipt: receive, source_admit_receipt: admit };
}

export async function fileOffer(
  relatteRoot: string,
  tranchRoot: string,
  houseRoot: string,
  specPath: string,
  carrierRootArg: string,
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(houseRoot, donors);
  const carrierRoot = resolve(carrierRootArg);
  if (await exists(carrierRoot)) throw new Error("CARRIER_ROOT_EXISTS");

  const prepared = await prepareOutgoing(donors, loaded, specPath, null);
  const frame = await donors.relatte.makeTransportFrame(
    prepared.crossing,
    "file-bundle",
    now(),
    "ROADKIT-001 removable-file carrier",
  );

  await mkdir(join(carrierRoot, "objects"), { recursive: true });
  await donors.relatte.writeFileBundle(join(carrierRoot, "crossing.frame.json"), frame);
  await writeJson(join(carrierRoot, "source-admit-receipt.json"), prepared.source_admit_receipt);

  const attachments = [];
  for (const ref of prepared.crossing.payload_refs) {
    const digest = digestOf(ref.address);
    const bytes = await loaded.store.get(ref.address);
    const relativePath = join("objects", digest + ".bin");
    await writeFile(join(carrierRoot, relativePath), bytes);
    attachments.push({
      address: ref.address,
      role: ref.role,
      media_type: ref.media_type,
      path: relativePath,
      byte_length: bytes.byteLength,
    });
  }

  const bundle = {
    schema: "static.roadkit-file-carrier/v0",
    transport_id: frame.transport_id,
    crossing_id: prepared.crossing.crossing_id,
    source_house_id: loaded.house.house_id,
    source_world_id: loaded.house.world_id,
    source_identity_ref: loaded.house.identity_ref,
    source_admit_receipt_id: prepared.source_admit_receipt.receipt_id,
    attachments,
    authority: "transport-only",
    laws: [
      "TRANSPORT != AUTHORITY",
      "ATTACHMENT PRESENCE != ADMISSION",
      "SOURCE ADMIT != RECEIVER ADMIT",
    ],
  };
  await writeJson(join(carrierRoot, "bundle.json"), bundle);

  return {
    ok: true,
    status: "file-carrier-created",
    carrier_root: carrierRoot,
    crossing_id: prepared.crossing.crossing_id,
    transport_id: frame.transport_id,
    source_admit_receipt_id: prepared.source_admit_receipt.receipt_id,
    attachment_count: attachments.length,
  };
}

async function saveInbox(paths: any, crossing: any) {
  const path = join(paths.inbox, safeId(crossing.crossing_id) + ".json");
  await writeJson(path, crossing);
  return path;
}

async function verifyAndImportAttachments(
  donors: any,
  store: any,
  crossing: any,
  carrierRoot: string,
  bundle: any,
) {
  if (bundle.schema !== "static.roadkit-file-carrier/v0") throw new Error("INVALID_CARRIER_MANIFEST");
  if (bundle.crossing_id !== crossing.crossing_id) throw new Error("CARRIER_CROSSING_MISMATCH");
  if (!Array.isArray(bundle.attachments)) throw new Error("INVALID_CARRIER_ATTACHMENTS");

  const expected = [...crossing.payload_refs].map((ref: any) => ref.address).sort();
  const declared = bundle.attachments.map((entry: any) => entry.address).sort();
  assert.deepEqual(declared, expected);

  for (const attachment of bundle.attachments) {
    const digest = digestOf(attachment.address);
    const expectedPath = join("objects", digest + ".bin");
    if (attachment.path !== expectedPath) throw new Error("INVALID_CARRIER_OBJECT_PATH");
    const bytes = await readFile(join(carrierRoot, expectedPath));
    if (donors.tranch.artifactAddress(bytes) !== attachment.address) {
      throw new Error("CARRIER_OBJECT_HASH_MISMATCH");
    }
    if (Number.isInteger(attachment.byte_length) && attachment.byte_length !== bytes.byteLength) {
      throw new Error("CARRIER_OBJECT_LENGTH_MISMATCH");
    }
    const imported = await store.put(bytes);
    assert.equal(imported.address, attachment.address);
  }
}

export async function fileImport(
  relatteRoot: string,
  tranchRoot: string,
  houseRoot: string,
  carrierRootArg: string,
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(houseRoot, donors);
  const carrierRoot = resolve(carrierRootArg);

  const { frame, crossing } = await donors.relatte.readFileBundle(
    join(carrierRoot, "crossing.frame.json"),
  );
  const bundle = await readJson(join(carrierRoot, "bundle.json"));
  await verifyAndImportAttachments(donors, loaded.store, crossing, carrierRoot, bundle);

  const sourceIdentity = await verifySourceIdentityBinding(loaded.store, crossing);

  const sourceAdmit = await readJson(join(carrierRoot, "source-admit-receipt.json"));
  if (!(await donors.relatte.verifyReceipt(sourceAdmit))) throw new Error("INVALID_SOURCE_ADMIT_RECEIPT");
  if (
    sourceAdmit.crossing_id !== crossing.crossing_id ||
    sourceAdmit.kind !== "R3_ADMIT"
  ) {
    throw new Error("SOURCE_ADMIT_RECEIPT_MISMATCH");
  }

  const receive = await loaded.receiver.receive(crossing, now());
  let hold = loaded.receiver.getDispositionReceipt(crossing.crossing_id);
  if (!hold) {
    hold = await loaded.receiver.dispose(crossing.crossing_id, "HOLD", now(), {
      note: "Foreign RoadKit crossing remains held pending an explicit local human re-crossing.",
    });
  }
  if (hold.kind !== "R3_HOLD") throw new Error("FOREIGN_CROSSING_NOT_HELD");
  await saveInbox(loaded.paths, crossing);
  await writeJson(
    join(loaded.paths.receipts, safeId(sourceAdmit.receipt_id) + ".source.json"),
    sourceAdmit,
  );

  return {
    ok: true,
    status: "foreign-crossing-held",
    crossing_id: crossing.crossing_id,
    transport_id: frame.transport_id,
    receive_receipt_id: receive.receipt_id,
    hold_receipt_id: hold.receipt_id,
    source_admit_receipt_id: sourceAdmit.receipt_id,
    source_identity: sourceIdentity,
    receiver_disposition: "HOLD",
    semantic_effect: "none",
  };
}

async function loadInboxCrossing(paths: any, crossingId: string) {
  const path = join(paths.inbox, safeId(crossingId) + ".json");
  const crossing = await readJson(path);
  if (crossing.crossing_id !== crossingId) throw new Error("INBOX_CROSSING_MISMATCH");
  return crossing;
}

export async function acceptHeld(
  relatteRoot: string,
  tranchRoot: string,
  houseRoot: string,
  crossingId: string,
  effect: string,
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(houseRoot, donors);
  const foreign = await loadInboxCrossing(loaded.paths, crossingId);
  const hold = loaded.receiver.getDispositionReceipt(crossingId);
  if (!hold || hold.kind !== "R3_HOLD") throw new Error("FOREIGN_CROSSING_MUST_BE_HELD");

  const humanIntent = {
    schema: "static.house-human-admission/v0",
    house_id: loaded.house.house_id,
    world_id: loaded.house.world_id,
    foreign_crossing_id: crossingId,
    foreign_hold_receipt_id: hold.receipt_id,
    decision: "ACCEPT",
    requested_local_effect: nonEmpty(effect, "LOCAL_EFFECT_REQUIRED"),
    created_at: now(),
    authority: "human-local-decision",
    laws: [
      "FOREIGN CROSSING != LOCAL CONSEQUENCE",
      "HOLD != ADMIT",
      "ACCEPTANCE REQUIRES LOCAL RE-CROSSING",
    ],
  };
  const intentPut = await putJson(loaded.store, humanIntent);

  const keys = await loadSigningKeys(loaded.paths.key);
  const localCrossing = await donors.relatte.sealCrossingEnvelope(
    {
      schema: "relatte.crossing-envelope/v0",
      protocol_version: "0",
      source_particular: loaded.house.house_id + "/human-steward",
      source_world: loaded.house.world_id,
      source_history_head: loaded.receiver.snapshot().history_head,
      parents: [crossingId],
      declared_kind: "static.local-admission-request/v0",
      payload_refs: [
        {
          address: intentPut.address,
          role: "human-admission-intent",
          media_type: "application/json",
        },
        ...foreign.payload_refs,
      ],
      requested_effect: effect,
      capability_ref: "static:human-local-admission/v0",
      privacy_policy: "local-house-only",
      audience_policy: loaded.house.house_id,
      return_address: null,
      created_at: now(),
      extensions: {
        roadkit: {
          foreign_crossing_id: crossingId,
          foreign_hold_receipt_id: hold.receipt_id,
          explicit_human_recrossing: true,
        },
      },
    },
    keys,
  );
  assert.equal(await donors.relatte.verifyCrossingEnvelope(localCrossing), true);

  const receive = await loaded.receiver.receive(localCrossing, now());
  const consequence = {
    schema: "static.local-roadkit-consequence/v0",
    house_id: loaded.house.house_id,
    world_id: loaded.house.world_id,
    foreign_crossing_id: crossingId,
    foreign_hold_receipt_id: hold.receipt_id,
    human_local_crossing_id: localCrossing.crossing_id,
    source_payload_refs: foreign.payload_refs.map((entry: any) => entry.address).sort(),
    effect,
    created_at: now(),
    authority: "local-only",
    laws: [
      "LOCAL CONSEQUENCE != SOURCE MUTATION",
      "SOURCE ADMIT != RECEIVER ADMIT",
      "SHARED HISTORY != SHARED GLOBAL STATE",
    ],
  };
  const consequencePut = await putJson(loaded.store, consequence);

  const admit = await loaded.receiver.dispose(localCrossing.crossing_id, "ADMIT", now(), {
    note: "Destination human re-crossing creates one receiver-local consequence.",
    admit_effect: effect,
    descendant_refs: [consequencePut.address],
  });
  assert.equal(await donors.relatte.verifyReceipt(admit), true);
  await writeJson(
    join(loaded.paths.outbox, safeId(localCrossing.crossing_id) + ".json"),
    localCrossing,
  );
  await writeJson(
    join(loaded.paths.receipts, safeId(admit.receipt_id) + ".json"),
    admit,
  );

  return {
    ok: true,
    status: "local-human-recrossing-admitted",
    foreign_crossing_id: crossingId,
    foreign_disposition: hold.kind,
    local_crossing_id: localCrossing.crossing_id,
    local_receive_receipt_id: receive.receipt_id,
    local_admit_receipt_id: admit.receipt_id,
    local_consequence_ref: consequencePut.address,
    semantic_effect: effect,
  };
}

function listen(server: any, port: number, host: string) {
  return new Promise<void>((resolvePromise, reject) => {
    const onError = (error: Error) => reject(error);
    server.once("error", onError);
    server.listen(port, host, () => {
      server.off("error", onError);
      resolvePromise();
    });
  });
}

function closeServer(server: any) {
  return new Promise<void>((resolvePromise, reject) => {
    server.close((error: Error | undefined) => (error ? reject(error) : resolvePromise()));
  });
}

export async function startPeer(
  relatteRoot: string,
  tranchRoot: string,
  houseRoot: string,
  options: { host?: string; relay_port: number; artifact_port: number },
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(houseRoot, donors);
  const host = options.host ?? "127.0.0.1";
  const relayPort = Number(options.relay_port);
  const artifactPort = Number(options.artifact_port);
  const validPort = (value: number) =>
    Number.isInteger(value) && (value === 0 || (value >= 1024 && value <= 65535));
  if (!validPort(relayPort)) throw new Error("INVALID_RELAY_PORT");
  if (!validPort(artifactPort)) throw new Error("INVALID_ARTIFACT_PORT");
  if (relayPort !== 0 && artifactPort !== 0 && relayPort === artifactPort) {
    throw new Error("PORTS_MUST_DIFFER");
  }

  const relay = donors.relatte.createHttpRelayServer(async (crossing: any) => {
    await loaded.receiver.receive(crossing, now());
    let disposition = loaded.receiver.getDispositionReceipt(crossing.crossing_id);
    if (!disposition) {
      disposition = await loaded.receiver.dispose(crossing.crossing_id, "HOLD", now(), {
        note: "LAN foreign crossing held; network delivery is not local admission.",
      });
    }
    if (disposition.kind !== "R3_HOLD") throw new Error("FOREIGN_CROSSING_NOT_HELD");
    await saveInbox(loaded.paths, crossing);
  });

  const artifactServer = createServer(async (request, response) => {
    try {
      if (request.method !== "GET") {
        response.statusCode = 405;
        response.end("method_not_allowed\n");
        return;
      }
      const match = /^\/roadkit\/v0\/artifacts\/([a-f0-9]{64})$/.exec(request.url ?? "");
      if (!match) {
        response.statusCode = 404;
        response.end("not_found\n");
        return;
      }
      const address = "sha256:" + match[1];
      const bytes = await loaded.store.get(address);
      response.statusCode = 200;
      response.setHeader("content-type", "application/octet-stream");
      response.setHeader("content-length", String(bytes.byteLength));
      response.setHeader("x-roadkit-address", address);
      response.setHeader("cache-control", "no-store");
      response.end(bytes);
    } catch {
      response.statusCode = 404;
      response.end("not_found\n");
    }
  });

  await listen(relay, relayPort, host);
  try {
    await listen(artifactServer, artifactPort, host);
  } catch (error) {
    await closeServer(relay);
    throw error;
  }

  const relayAddress = relay.address();
  const artifactAddress = artifactServer.address();
  if (!relayAddress || typeof relayAddress === "string") throw new Error("RELAY_ADDRESS_UNAVAILABLE");
  if (!artifactAddress || typeof artifactAddress === "string") throw new Error("ARTIFACT_ADDRESS_UNAVAILABLE");

  return {
    schema: "static.roadkit-peer/v0",
    house_id: loaded.house.house_id,
    world_id: loaded.house.world_id,
    host,
    relay_url: `http://${host}:${relayAddress.port}/relatte/v0/crossings`,
    artifact_base_url: `http://${host}:${artifactAddress.port}/roadkit/v0/artifacts/`,
    authority: "transport-only",
    laws: [
      "PEER ADDRESS != PEER IDENTITY",
      "DELIVERED != ADMITTED",
      "PULLED != ADMITTED",
    ],
    close: async () => {
      await Promise.all([closeServer(relay), closeServer(artifactServer)]);
    },
  };
}

export async function lanSend(
  relatteRoot: string,
  tranchRoot: string,
  houseRoot: string,
  specPath: string,
  targetRelayUrl: string,
  sourceArtifactBaseUrl: string,
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(houseRoot, donors);
  const artifactBase = requireHttpBase(sourceArtifactBaseUrl);
  const target = new URL(targetRelayUrl);
  if (
    target.protocol !== "http:" ||
    target.username ||
    target.password ||
    target.search ||
    target.hash ||
    target.pathname !== "/relatte/v0/crossings"
  ) {
    throw new Error("INVALID_TARGET_RELAY_URL");
  }

  const prepared = await prepareOutgoing(donors, loaded, specPath, artifactBase);
  const frame = await donors.relatte.makeTransportFrame(
    prepared.crossing,
    "http-relay",
    now(),
    "ROADKIT-001 operator-addressed LAN road",
  );
  const ack = await donors.relatte.postHttpTransport(target.toString(), frame);

  return {
    ok: true,
    status: "lan-crossing-delivered",
    crossing_id: prepared.crossing.crossing_id,
    transport_id: frame.transport_id,
    target_relay_url: target.toString(),
    source_artifact_base_url: artifactBase,
    ack,
    source_admit_receipt_id: prepared.source_admit_receipt.receipt_id,
    semantic_effect_at_receiver: "none",
  };
}

export async function pullHeldArtifacts(
  relatteRoot: string,
  tranchRoot: string,
  houseRoot: string,
  crossingId: string,
) {
  const donors = await loadDonors(relatteRoot, tranchRoot);
  const loaded = await loadHouse(houseRoot, donors);
  const crossing = await loadInboxCrossing(loaded.paths, crossingId);
  const hold = loaded.receiver.getDispositionReceipt(crossingId);
  if (!hold || hold.kind !== "R3_HOLD") throw new Error("FOREIGN_CROSSING_MUST_BE_HELD");
  const base = requireHttpBase(nonEmpty(crossing.return_address, "CROSSING_HAS_NO_ARTIFACT_RETURN_ADDRESS"));

  let total = 0;
  const imported = [];
  for (const ref of crossing.payload_refs) {
    const digest = digestOf(ref.address);
    const response = await fetch(new URL(digest, base));
    if (!response.ok) throw new Error("ARTIFACT_PULL_FAILED");
    const bytes = Buffer.from(await response.arrayBuffer());
    total += bytes.byteLength;
    if (bytes.byteLength <= 0 || bytes.byteLength > MAX_ARTIFACT_BYTES || total > MAX_TOTAL_BYTES) {
      throw new Error("PULLED_ARTIFACT_SIZE_OUT_OF_BOUNDS");
    }
    if (donors.tranch.artifactAddress(bytes) !== ref.address) throw new Error("PULLED_ARTIFACT_HASH_MISMATCH");
    const put = await loaded.store.put(bytes);
    imported.push({ address: put.address, byte_length: put.byteLength, role: ref.role });
  }

  const sourceIdentity = await verifySourceIdentityBinding(loaded.store, crossing);

  return {
    ok: true,
    status: "held-artifacts-pulled",
    crossing_id: crossingId,
    source_identity: sourceIdentity,
    hold_receipt_id: hold.receipt_id,
    imported,
    semantic_effect: "none",
    law: "PULLED != ADMITTED",
  };
}

function usage() {
  return [
    "STATIC ROADKIT-001",
    "",
    "Environment:",
    "  ROADKIT_RELATTE_ROOT=/path/to/pinned/reLATTE",
    "  ROADKIT_TRANCHNODE_ROOT=/path/to/pinned/tranchnode",
    "",
    "Commands:",
    "  init <house-root> <house-id> <world-id> [label]",
    "  status <house-root>",
    "  file-offer <house-root> <offer-spec.json> <new-carrier-dir>",
    "  file-import <house-root> <carrier-dir>",
    "  accept <house-root> <foreign-crossing-id> <local-effect>",
    "  peer <house-root> <relay-port> <artifact-port> [bind-host]",
    "  lan-send <house-root> <offer-spec.json> <target-relay-url> <source-artifact-base-url>",
    "  pull <house-root> <foreign-crossing-id>",
  ].join("\n");
}

async function main() {
  const relatteRoot = process.env.ROADKIT_RELATTE_ROOT;
  const tranchRoot = process.env.ROADKIT_TRANCHNODE_ROOT;
  if (!relatteRoot || !tranchRoot) {
    throw new Error("ROADKIT donor roots are required. Run scripts/roadkit-setup.sh --install first.");
  }

  const [command, ...args] = process.argv.slice(2);
  let result: any;
  if (!command || command === "--help" || command === "help") {
    console.log(usage());
    return;
  }

  if (command === "init") {
    const [root, houseId, worldId, label] = args;
    result = await initHouse(relatteRoot, tranchRoot, root, {
      house_id: houseId,
      world_id: worldId,
      label,
    });
  } else if (command === "status") {
    result = await houseStatus(relatteRoot, tranchRoot, args[0]);
  } else if (command === "file-offer") {
    result = await fileOffer(relatteRoot, tranchRoot, args[0], args[1], args[2]);
  } else if (command === "file-import") {
    result = await fileImport(relatteRoot, tranchRoot, args[0], args[1]);
  } else if (command === "accept") {
    result = await acceptHeld(relatteRoot, tranchRoot, args[0], args[1], args[2]);
  } else if (command === "lan-send") {
    result = await lanSend(relatteRoot, tranchRoot, args[0], args[1], args[2], args[3]);
  } else if (command === "pull") {
    result = await pullHeldArtifacts(relatteRoot, tranchRoot, args[0], args[1]);
  } else if (command === "peer") {
    const relayPort = Number(args[1]);
    const artifactPort = Number(args[2]);
    const peer = await startPeer(relatteRoot, tranchRoot, args[0], {
      relay_port: relayPort,
      artifact_port: artifactPort,
      host: args[3] ?? "127.0.0.1",
    });
    console.log(JSON.stringify({
      ...peer,
      close: undefined,
    }, null, 2));
    const stop = async () => {
      await peer.close();
      process.exit(0);
    };
    process.once("SIGINT", stop);
    process.once("SIGTERM", stop);
    await new Promise(() => {});
    return;
  } else {
    throw new Error("UNKNOWN_ROADKIT_COMMAND\n" + usage());
  }

  console.log(JSON.stringify(result, null, 2));
}

const invoked = (process.argv[1] ?? "").endsWith("roadkit-001.ts");
if (invoked) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack ?? error.message : String(error));
    process.exitCode = 1;
  });
}
