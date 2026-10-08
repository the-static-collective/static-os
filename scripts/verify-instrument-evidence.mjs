// Verify exported public evidence using reLATTE itself, in a fresh process without receiver keys.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [donor, packetPath] = process.argv.slice(2);
const { verifyOpaqueOrganCrossing, verifyReceipt } = await import(pathToFileURL(join(donor,'src/index.ts')).href);
const packet = JSON.parse(await readFile(packetPath,'utf8'));
const bytes = Buffer.from(packet.bytes,'base64');
const address = 'sha256:' + createHash('sha256').update(bytes).digest('hex');
assert.equal(await verifyOpaqueOrganCrossing(packet.proposal_crossing), true);
assert.equal(await verifyOpaqueOrganCrossing(packet.admission.crossing), true);
for (const receipt of [packet.receive_receipt,packet.hold_receipt,packet.admission.receipt]) {
  assert.equal(await verifyReceipt(receipt), true);
}
assert.equal(packet.proposal_crossing.payload_refs[0].address,address);
assert.equal(packet.admission.crossing.payload_refs[0].address,address);
assert.equal(packet.receive_receipt.crossing_id,packet.proposal_crossing.crossing_id);
assert.equal(packet.hold_receipt.crossing_id,packet.proposal_crossing.crossing_id);
assert.equal(packet.hold_receipt.kind,'R3_HOLD');
assert.equal(packet.hold_receipt.semantic_effect,'none');
assert.equal(packet.admission.receipt.crossing_id,packet.admission.crossing.crossing_id);
assert.equal(packet.admission.receipt.kind,'R3_ADMIT');
assert.equal(packet.admission.receipt.semantic_effect,'one-readonly-instrument-record-authorized');
assert.deepEqual(packet.hold_receipt.signing.public_key,packet.admission.receipt.signing.public_key);
assert.equal(packet.admission.crossing.extensions.organ_adapter.donor_claims.held_proposal_crossing_id,
             packet.proposal_crossing.crossing_id);
assert.equal(packet.request.operation,'record');
assert.deepEqual(packet.request.required_capabilities,['observe','record']);
assert.equal(packet.request.transmission,'DISABLED');
assert.equal(packet.admission.crossing.requested_effect.request_id,packet.request.id);
process.stdout.write(JSON.stringify({schema:'static-os.instrument-public-verification/v0',
  native_relatte_signature_verification:true, fresh_process:true, receiver_private_keys_used:false,
  historical_evidence_only:true, grants_imported:false, rf_emitted:false}) + '\n');
