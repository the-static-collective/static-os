// Native calls into the exact reLATTE owner implementation. No copied signature/receiver code.
import { pathToFileURL } from 'node:url';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash, randomUUID } from 'node:crypto';

const [donor, root, action] = process.argv.slice(2);
const {
  LocalReceiver, generateP256KeyPair, sealOpaqueOrganCrossing,
  verifyOpaqueOrganCrossing, verifyReceipt,
} = await import(pathToFileURL(join(donor, 'src/index.ts')).href);
let input = '';
for await (const chunk of process.stdin) input += chunk;
if (Buffer.byteLength(input) > 65536) throw new Error('BRIDGE_INPUT_TOO_LARGE');
const args = JSON.parse(input);
const sha = value => createHash('sha256').update(value).digest('hex');
const packetPath = id => {
  if (!/^[a-f0-9-]{36}$/.test(id)) throw new Error('INVALID_OPERATION_ID');
  return join(root, 'packets', id + '.json');
};
const timestamp = () => new Date().toISOString();
const read = async path => JSON.parse(await readFile(path, 'utf8'));
const receiverPath = join(root, 'receiver');
let receiver;
if (action === 'init') {
  receiver = await LocalReceiver.create(receiverPath, {
    world_id: 'world:static-os-instrument:' + randomUUID(),
    receiver_particular: 'particular:instrument-owner:' + randomUUID(),
    contract_ref: 'static-os:instrument-host/v0',
  });
  await mkdir(join(root, 'packets'), { recursive: true });
} else {
  receiver = await LocalReceiver.open(receiverPath);
}

const spec = (request, bytes, owner = false, heldId = null, expiresAt = null) => ({
  schema: 'relatte.opaque-organ-spec/v0',
  family_ref: 'static-os.instrument-host/v0',
  donor_contract_ref: 'static-os:INSTRUMENT-HOST-001',
  artifact_kind: owner ? 'OWNER_LOCAL_INSTRUMENT_DECISION' : 'INSTRUMENT_OPERATION_PROPOSAL',
  source_world: owner ? receiver.config.world_id : 'world:static-os-instrument-proposer',
  source_particular: owner ? receiver.config.receiver_particular : 'particular:instrument-request:' + request.id,
  source_history_head: request.source.sha256,
  payload_refs: [{ address: 'sha256:' + sha(bytes), role: 'instrument-operation', media_type: 'application/json' }],
  donor_claims: {
    proposal_only: !owner, authority_effect: 'none', rf_transmission: 'DISABLED',
    held_proposal_crossing_id: heldId,
  },
  requested_effect: owner
    ? { kind: 'RECORD_ONE_READONLY_SELECTION', request_id: request.id, expires_at: expiresAt }
    : { kind: 'PRESENT_FOR_LOCAL_REVIEW', automatic_execution: false, automatic_admission: false },
  return_address: null,
  created_at: timestamp(),
});
const checkRequest = request => {
  if (request.schema !== 'static-os.instrument-operation/v0' || request.operation !== 'record'
      || request.proposal_only !== true || request.transmission !== 'DISABLED'
      || JSON.stringify(request.required_capabilities) !== JSON.stringify(['observe','record'])) {
    throw new Error('ONLY_BOUNDED_READONLY_RECORD_MAY_BE_ADMITTED');
  }
};
const checkedPacket = async id => {
  const packet = await read(packetPath(id));
  checkRequest(packet.request);
  const bytes = Buffer.from(packet.bytes, 'base64');
  if (bytes.length > 65536 || JSON.stringify(JSON.parse(bytes)) !== JSON.stringify(packet.request)) {
    throw new Error('REQUEST_BYTES_CHANGED');
  }
  if (!(await verifyOpaqueOrganCrossing(packet.proposal_crossing))
      || packet.proposal_crossing.payload_refs[0].address !== 'sha256:' + sha(bytes)
      || !(await verifyReceipt(packet.hold_receipt))) throw new Error('INVALID_PROPOSAL_PACKET');
  const held = receiver.getDispositionReceipt(packet.proposal_crossing.crossing_id);
  if (!held || held.kind !== 'R3_HOLD' || held.receipt_id !== packet.hold_receipt.receipt_id) {
    throw new Error('PROPOSAL_NOT_HELD_BY_CURRENT_OWNER');
  }
  return packet;
};

let result;
if (action === 'init' || action === 'snapshot') {
  result = receiver.snapshot();
} else if (action === 'propose') {
  checkRequest(args.request);
  const bytes = Buffer.from(args.bytes, 'base64');
  if (bytes.length > 65536 || JSON.stringify(JSON.parse(bytes)) !== JSON.stringify(args.request)) {
    throw new Error('REQUEST_BYTES_CHANGED');
  }
  const crossing = await sealOpaqueOrganCrossing(spec(args.request, bytes), await generateP256KeyPair());
  if (!(await verifyOpaqueOrganCrossing(crossing))) throw new Error('INVALID_CROSSING');
  const received = await receiver.receive(crossing, timestamp());
  const hold = await receiver.dispose(crossing.crossing_id, 'HOLD', timestamp());
  const packet = { request: args.request, bytes: args.bytes, proposal_crossing: crossing,
                   receive_receipt: received, hold_receipt: hold };
  await writeFile(packetPath(args.request.id), JSON.stringify(packet), { mode: 0o600, flag: 'wx' });
  result = { boundary: 'native-relatte', crossing, receive_receipt: received, hold_receipt: hold,
             admitted: false, signature_verified: await verifyReceipt(hold) };
} else if (action === 'owner-admit') {
  // Only reached through the explicit owner command; never from dials or proposal processing.
  const packet = await checkedPacket(args.id);
  if (packet.admission) throw new Error('OPERATION_ALREADY_DECIDED');
  if (!Number.isSafeInteger(args.expires_at) || args.expires_at <= Date.now()
      || args.expires_at > Date.now() + 3600000) throw new Error('INVALID_ADMISSION_EXPIRY');
  const bytes = Buffer.from(packet.bytes, 'base64');
  const crossing = await sealOpaqueOrganCrossing(
    spec(packet.request, bytes, true, packet.proposal_crossing.crossing_id, args.expires_at),
    await generateP256KeyPair(),
  );
  await receiver.receive(crossing, timestamp());
  const receipt = await receiver.dispose(crossing.crossing_id, 'ADMIT', timestamp(), {
    admit_effect: 'one-readonly-instrument-record-authorized',
    descendant_refs: [crossing.payload_refs[0].address],
    note: 'explicit owner-local decision; original proposal remains HOLD; transmission stays DISABLED',
  });
  packet.admission = { crossing, receipt };
  await writeFile(packetPath(args.id), JSON.stringify(packet), { mode: 0o600 });
  result = { boundary: 'native-relatte', ...packet.admission, signature_verified: await verifyReceipt(receipt) };
} else if (action === 'verify-admission') {
  const packet = await checkedPacket(args.id);
  const admission = packet.admission;
  if (!admission || !(await verifyOpaqueOrganCrossing(admission.crossing))
      || !(await verifyReceipt(admission.receipt))) throw new Error('CURRENT_OWNER_ADMISSION_REQUIRED');
  const current = receiver.getDispositionReceipt(admission.crossing.crossing_id);
  if (!current || current.kind !== 'R3_ADMIT' || current.receipt_id !== admission.receipt.receipt_id
      || !receiver.snapshot().admitted.includes(admission.crossing.crossing_id)
      || admission.crossing.source_world !== receiver.config.world_id
      || admission.crossing.requested_effect.request_id !== args.id
      || admission.crossing.requested_effect.kind !== 'RECORD_ONE_READONLY_SELECTION'
      || admission.crossing.payload_refs[0].address !== packet.proposal_crossing.payload_refs[0].address
      || admission.crossing.extensions.organ_adapter.donor_claims.held_proposal_crossing_id
         !== packet.proposal_crossing.crossing_id
      || admission.receipt.world_id !== receiver.config.world_id
      || admission.receipt.semantic_effect !== 'one-readonly-instrument-record-authorized') {
    throw new Error('CURRENT_OWNER_ADMISSION_REQUIRED');
  }
  if (Date.now() >= admission.crossing.requested_effect.expires_at) throw new Error('ADMISSION_EXPIRED');
  if (sha(Buffer.from(packet.bytes, 'base64')) !== args.request_sha256) throw new Error('REQUEST_BINDING_CHANGED');
  result = { boundary: 'native-relatte', admitted: true, receipt: current, crossing: admission.crossing,
             signature_verified: true };
} else {
  throw new Error('UNSUPPORTED_OWNER_ACTION');
}
process.stdout.write(JSON.stringify(result) + '\n');
