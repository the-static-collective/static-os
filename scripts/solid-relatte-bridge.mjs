#!/usr/bin/env node
/**
 * Native reLATTE 005 crossing/verification bridge. REAL reLATTE imports,
 * never local Python imitation of P-256 signatures or canonical envelopes.
 * Called from Static OS after kernel evidence exists. One selected
 * bounded crossing; destination owner retains independent HOLD authority.
 */
import { readFile } from 'node:fs/promises';
import {
  runOpaqueOrganRoundTrip,
  verifyOpaqueOrganCrossing,
  verifyReceipt,
} from '../external/reLATTE/src/index.ts';

async function verifyEvidence(value) {
  if (value?.schema !== 'static-os.cad-relatte-evidence/v0') {
    throw new Error('NOT_REAL_RELATTE_EVIDENCE');
  }
  const result = value.result;
  if (result?.schema !== 'relatte.opaque-roundtrip-result/v0'
      || !(await verifyOpaqueOrganCrossing(result.crossing))
      || !(await verifyReceipt(result.receive_receipt))
      || !(await verifyReceipt(result.disposition_receipt))) {
    throw new Error('NATIVE_RELATTE_VERIFICATION_FAILED');
  }
  if (result.receive_receipt.crossing_id !== result.crossing.crossing_id
      || result.disposition_receipt.crossing_id !== result.crossing.crossing_id
      || result.receive_receipt.kind !== 'RECEIVED'
      || result.disposition_receipt.kind !== 'R3_HOLD'
      || result.receive_receipt.semantic_effect !== 'none'
      || result.disposition_receipt.semantic_effect !== 'none'
      || result.crossing.extensions?.organ_adapter?.artifact_kind
          !== 'STATIC_CAD_005_DECISION_TRACE'
      || result.crossing.requested_effect?.automatic_execution !== false
      || result.crossing.requested_effect?.kind !== 'PRESENT_FOR_LOCAL_REVIEW'
      || result.receiver_snapshot?.held?.includes(result.crossing.crossing_id) !== true) {
    throw new Error('RELATTE_OWNER_BOUNDARY_MISMATCH');
  }
  const payloadRefs = result.crossing.payload_refs;
  const expected = value.expected_refs;
  // reLATTE's source adapter normalizes field insertion order; compare
  // strict semantic values, not JSON.stringify object insertion order.
  const matches = Array.isArray(payloadRefs) && Array.isArray(expected)
    && payloadRefs.length === 4 && expected.length === 4
    && expected.every((ref, i) => {
      const native = payloadRefs[i];
      return native && ref
        && Object.keys(native).length === 3
        && Object.keys(ref).length === 3
        && native.address === ref.address
        && native.role === ref.role
        && native.media_type === ref.media_type;
    });
  if (!matches || result.crossing.source_history_head !== value.trace_id) {
    throw new Error('RELATTE_PAYLOAD_BINDING_MISMATCH');
  }
  return {
    schema: 'static-os.cad-relatte-native-verification/v0',
    status: 'SIGNED_CROSSING_AND_RECEIVE_HOLD_VERIFIED',
    crossing_id: result.crossing.crossing_id,
    receive_receipt_id: result.receive_receipt.receipt_id,
    disposition_receipt_id: result.disposition_receipt.receipt_id,
    source_trace_id: value.trace_id,
    disposition: 'HOLD',
    fabrication_grant: false,
    interpretation_authority: 'none',
  };
}

async function main() {
  const mode = process.argv[2];
  if (mode !== 'cross' && mode !== 'verify') throw new Error('UNKNOWN_BRIDGE_MODE');
  const data = JSON.parse(await readFile(process.argv[3], 'utf8'));
  if (mode === 'verify') {
    process.stdout.write(JSON.stringify(await verifyEvidence(data))+'\n');
    return;
  }
  if (data.schema !== 'static-os.cad-relatte-request/v0'
      || data.request?.schema !== 'relatte.opaque-roundtrip-request/v0'
      || data.request.disposition !== 'HOLD'
      || data.request.spec?.artifact_kind !== 'STATIC_CAD_005_DECISION_TRACE'
      || data.request.spec?.requested_effect?.automatic_execution !== false) {
    throw new Error('UNSAFE_RELATTE_CROSSING_REQUEST');
  }
  const result = await runOpaqueOrganRoundTrip(data.request);
  const output = {
    schema: 'static-os.cad-relatte-evidence/v0',
    trace_id: data.trace_id,
    expected_refs: data.request.spec.payload_refs,
    result,
  };
  await verifyEvidence(output);
  process.stdout.write(JSON.stringify(output)+'\n');
}
main().catch((error)=>{
  process.stderr.write('RELATTE_HOLD: '+String(error).slice(0,240)+'\n');
  process.exitCode=2;
});
