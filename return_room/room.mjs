// STATIC OS RETURN ROOM 001
// An operator-controlled, read-only encounter cockpit: signed foreign receipt
// + redacted question + strictly local, resumable dossier. Never becomes owner.
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile,lstat} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const hash=data=>'sha256:'+createHash('sha256').update(data).digest('hex');
const stable=v=>v&&typeof v==='object'
  ?Array.isArray(v)?v.map(stable):Object.fromEntries(Object.keys(v).sort().map(k=>[k,stable(v[k])]))
  :v;
const canonical=v=>JSON.stringify(stable(v));
const eq=(a,b)=>canonical(a)===canonical(b);
const requireFields=(v,fields,label)=>{
  if(!v||typeof v!=='object'||Array.isArray(v)||
     Object.keys(v).length!==fields.length||fields.some(k=>!Object.hasOwn(v,k)))
    throw Error(label+'_UNEXPECTED_FIELDS');
};
const utc=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(v)&&Number.isFinite(Date.parse(v));
const proposalKinds=new Set(['resonance','contrast','callback','same-symbol-different-road','decoder-shift','absence','madd-clown']);
const sourceKinds=new Set(['declared_hint','structural','fallback']);
const payloadFields=['schema','relation_kind','typing_basis','slots','itinerary_commitment','outcome','evidence_class','authority','admission','laws'];
const expectedLaws=[
  'ARRANGEMENT != SEQUENCE','ADJACENCY != ANCESTRY',
  'PROPOSAL != ADMISSION','HINT != EVIDENCE',
  'SIGNATURE != SOURCE AUTHORITY','HOLD != CANON',
  'PUBLIC COMMITMENT != PRIVATE SOURCE DISCLOSURE'
];
export function inspectRedactedPayload(p){
  requireFields(p,payloadFields,'PAYLOAD');
  if(p.schema!=='memento.clown-proposal/v0'||!proposalKinds.has(p.relation_kind)||
    !sourceKinds.has(p.typing_basis)||p.outcome!=='PROPOSED_ONLY'||
    p.evidence_class!=='proposal'||p.authority!=='none'||p.admission!=='none'||
    !eq(p.laws,expectedLaws))throw Error('PAYLOAD_PROMOTION_OR_UNKNOWN_PROFILE');
  if(p.typing_basis==='fallback'&&p.relation_kind!=='madd-clown'||
    p.typing_basis==='structural'&&p.relation_kind==='madd-clown')
    throw Error('PAYLOAD_FALSE_EVIDENCE');
  if(!Array.isArray(p.slots)||p.slots.length!==2)throw Error('PAYLOAD_SLOTS');
  for(const [i,slot] of p.slots.entries()){
    requireFields(slot,['position','commitment'],'SLOT');
    if(slot.position!==i||!/^hmac-sha256:[0-9a-f]{64}$/.test(slot.commitment))throw Error('SLOT_COMMITMENT');
  }
  if(!/^hmac-sha256:[0-9a-f]{64}$/.test(p.itinerary_commitment))throw Error('ITINERARY_COMMITMENT');
}
const receipt=(r,kind,crossingId)=>{
  if(!r||r.schema!=='relatte.receipt/v0'||r.kind!==kind||r.crossing_id!==crossingId||
     r.semantic_effect!=='none'||!utc(r.created_at)||typeof r.receipt_id!=='string')
    throw Error('RECEIPT_SCOPE_OR_SEMANTIC_EFFECT');
};
export async function verifyDoor(input,{protocol,organ,questionBox}){
  const {carrier,review,questionSeed,contact,association}=input||{};
  if(!protocol?.verifyReceipt||!organ?.verifyOpaqueOrganCrossing||!questionBox?.fromMementoHeldSeed)
    throw Error('PINNED_NATIVE_VERIFIERS_REQUIRED');
  requireFields(carrier,['schema','payload','crossing','authenticity','admission','sender_public_released'],'CARRIER');
  if(carrier.schema!=='memento.clown-relatte-carrier/v0'||
    carrier.authenticity!=='EXPERIMENTAL_EPHEMERAL_SIGNER_NOT_MEMENTO_OWNER'||
    carrier.admission!=='none'||carrier.sender_public_released!==false)
    throw Error('FOREIGN_CARRIER_AUTHORITY_DENIED');
  const x=carrier.crossing,p=carrier.payload;
  inspectRedactedPayload(p);
  if(!(await organ.verifyOpaqueOrganCrossing(x)))throw Error('INVALID_FOREIGN_CROSSING_SIGNATURE');
  if(x.schema!=='relatte.crossing-envelope/v0'||x.declared_kind!=='OPAQUE_ORGAN_ARTIFACT'||
    x.source_world!=='world:memento-crazy-slots-experimental-adapter'||
    x.requested_effect!==null||x.extensions?.organ_adapter?.family_ref!=='memento:crazy-slots-proposed-adjacency/v0'||
    x.payload_refs?.length!==1||x.payload_refs[0].role!=='redacted-proposal'||
    x.payload_refs[0].media_type!=='application/vnd.static-collective.clown-proposal+json')
    throw Error('CROSSING_PROFILE_NOT_SUPPORTED');
  const bytes=Buffer.from(canonical(p),'utf8'),address=hash(bytes);
  if(bytes.length>8192||x.payload_refs[0].address!==address)throw Error('PROPOSAL_BYTES_NOT_BOUND');

  requireFields(review,['schema','crossing_id','receiver_signer_scope','received','held','verified_payload_custody','snapshot','admission','locally_held','remotely_delivered'],'REVIEW');
  if(review.schema!=='memento.clown-relatte-review/v0'||
    review.crossing_id!==x.crossing_id||review.admission!=='none'||
    review.receiver_signer_scope!=='EXPERIMENTAL_LOCAL_KEY_NOT_REAL_WORLD_IDENTITY'||
    review.locally_held!==true||review.remotely_delivered!==false)
    throw Error('REVIEW_NOT_LOCAL_HOLD');
  const {received:r,held:h,verified_payload_custody:c,snapshot:s}=review;
  for(const [value,kind] of [[r,'RECEIVED'],[h,'R3_HOLD'],[c,'PAYLOAD_BYTES_VERIFIED']]){
    receipt(value,kind,x.crossing_id);
    if(!(await protocol.verifyReceipt(value)))throw Error('INVALID_NATIVE_RELATTE_RECEIPT');
    if(value.world_id!==h.world_id||value.receiver_particular!==h.receiver_particular||
      value.contract_ref!==h.contract_ref||
      !eq(value.signing?.public_key,h.signing?.public_key))throw Error('INDEPENDENT_RECEIVER_MISMATCH');
  }
  if(h.extensions?.local_receiver?.disposition!=='HOLD'||
     h.extensions?.local_receiver?.receive_receipt_id!==r.receipt_id||
     h.extensions?.local_receiver?.protected_payload_effect!==false||
     !eq(h.residual_refs,[address])||
     c.extensions?.local_receiver?.payload_custody?.sha256!==address.slice(7)||
     c.extensions?.local_receiver?.payload_custody?.byte_length!==bytes.length||
     c.extensions?.local_receiver?.payload_custody?.retained!==true||
     c.extensions?.local_receiver?.payload_custody?.disposition!=='HOLD'||
     c.extensions?.local_receiver?.payload_custody?.receive_receipt_id!==r.receipt_id||
     c.extensions?.local_receiver?.payload_custody?.disposition_receipt_id!==h.receipt_id||
     !eq(c.residual_refs,[address]))
     throw Error('HOLD_OR_CUSTODY_LINK_CHANGED');
  if(s?.schema!=='relatte.local-receiver-snapshot/v0'||s.world_id!==h.world_id||
    s.receiver_particular!==h.receiver_particular||!Array.isArray(s.held)||
    !s.held.includes(x.crossing_id)||!Array.isArray(s.admitted)||s.admitted.length!==0||
    !Array.isArray(s.received)||!s.received.includes(x.crossing_id))
    throw Error('SNAPSHOT_NOT_HELD');

  // UNDERSTORY records are owner-local *claimed* observations: check binding but
  // do not pretend Static-OS authenticates the human witness or MEMENTO canon.
  if(!contact||contact.schema!=='memento.understory-record/v0'||contact.family!=='contact'||
    !utc(contact.sensed_at)||!utc(contact.recorded_at)||typeof contact.id!=='string'||
    !contact.id.startsWith('contact-madd-hold-')||
    contact.occurrence_ref!==h.receipt_id||
    !eq(contact.evidence_refs,[x.crossing_id,r.receipt_id,h.receipt_id,c.receipt_id])||
    typeof contact.observer!=='string'||!contact.observer.trim())
    throw Error('CONTACT_NOT_BOUND_TO_NATIVE_RECEIPT');
  if(Date.parse(contact.sensed_at)<Math.max(...[r,h,c].map(z=>Date.parse(z.created_at)))||
     contact.recorded_at!==contact.sensed_at)throw Error('CONTACT_BEFORE_RECEIPTS');
  if(!association||association.schema!=='memento.understory-record/v0'||
    association.family!=='association'||association.status!=='unresolved'||
    association.observer!==contact.observer||
    !eq(association.member_refs,p.slots.map(z=>z.commitment))||
    !eq(association.evidence_refs,[contact.id,h.receipt_id,c.receipt_id])||
    association.relation_hint!=='unresolved-later-adjacency/'+p.relation_kind+'/'+p.typing_basis||
    !utc(association.recorded_at)||Date.parse(association.recorded_at)<Date.parse(contact.sensed_at))
    throw Error('ASSOCIATION_PROMOTION_OR_MISMATCH');
  if(questionSeed?.crossing_id!==x.crossing_id||
     questionSeed?.hold_receipt_id!==h.receipt_id||
     questionSeed?.relation_kind!==p.relation_kind||
     questionSeed?.typing_basis!==p.typing_basis)throw Error('QUESTION_SEED_REBOUND');
  const handoff=questionBox.fromMementoHeldSeed(questionSeed);
  if(handoff.authority!=='none'||handoff.admission!=='none'||
    handoff.question_receipt?.aperture?.id!=='source-object'||
    handoff.question_receipt?.evidence?.source_locator!==''||
    handoff.question_receipt?.evidence?.provenance_class!=='speculation'||
    handoff.question_receipt?.evidence?.support_confidence!=='unsupported')
    throw Error('QUESTION_BECAME_PREMATURE_ANSWER');

  return {
    schema:'static-os.return-room-inspection/v0',
    crossing_id:x.crossing_id,public_payload_sha256:address,
    receive_receipt_id:r.receipt_id,hold_receipt_id:h.receipt_id,
    custody_receipt_id:c.receipt_id,understory_contact_ref:contact.id,
    understory_association_ref:association.id,
    question_aperture:handoff.question_receipt.aperture.id,
    question:handoff.question_receipt.question,
    question_receipt_digest:hash(canonical(handoff.question_receipt)),
    verifier:'NATIVE_RELATTE_AND_NATIONAL_TREASURE',
    receiver_signatures_verified:3,
    claimed_human_observer:'NOT_INDEPENDENTLY_AUTHENTICATED',
    original_source_ancestry:'NOT_ESTABLISHED',
    admission:'none',automatic_execution:false, next_turn:'NOT_AUTHORIZED',
    memento_canon_changed:false,remote_delivery:false,boot_proof:false
  };
}
export async function donorModules(relatteRoot,treasureRoot){
  if(!relatteRoot||!treasureRoot)throw Error('EXPLICIT_PINNED_DONORS_REQUIRED');
  const r=resolve(relatteRoot),t=resolve(treasureRoot);
  const protocol=await import(pathToFileURL(join(r,'src/protocol.ts')).href);
  const organ=await import(pathToFileURL(join(r,'src/organ.ts')).href);
  const questionBox=await import(pathToFileURL(join(t,'tools/question-box/from-memento.mjs')).href);
  return {protocol,organ,questionBox};
}
export async function readDocketInputs(paths){
  const names=['carrier','review','questionSeed','contact','association'];
  if(names.some(k=>!paths?.[k]))throw Error('EXPLICIT_FIVE_INPUTS_REQUIRED');
  const input={},fingerprints={};
  for(const k of names){
    const p=resolve(paths[k]),stat=await lstat(p);
    if(!stat.isFile()||stat.isSymbolicLink()||stat.size>65536)throw Error('UNSAFE_INPUT_'+k);
    const bytes=await readFile(p);
    if(bytes.length>65536)throw Error('INPUT_LIMIT_'+k);
    input[k]=JSON.parse(bytes.toString('utf8'));
    fingerprints[k]=hash(bytes);
  }
  return {input,fingerprints};
}
const readJSON=async p=>JSON.parse(await readFile(p,'utf8'));
const put=async(p,value)=>writeFile(p,JSON.stringify(value,null,2)+'\n',{flag:'wx',mode:0o600});
export async function startDocket({paths,outputDir,reviewer,selected,at,modules}){
  if(selected!==true)throw Error('EXPLICIT_OPERATOR_SELECTION_REQUIRED');
  if(typeof reviewer!=='string'||reviewer.length<2||reviewer.length>128||!reviewer.trim())throw Error('REVIEWER_REQUIRED');
  if(!utc(at))throw Error('INVALID_LOCAL_TIME');
  const dest=resolve(outputDir);
  const {input,fingerprints}=await readDocketInputs(paths);
  // Reserve a local, create-only checkpoint BEFORE any donor verification.
  // A crash after PREPARED leaves HOLD. Never silently retry or re-execute.
  await mkdir(dest,{mode:0o700,recursive:false});
  const checkpoint={schema:'static-os.return-room-checkpoint/v0',state:'PREPARED',
    input_fingerprints:fingerprints,at,operator_selected:true,automatic_retry:false,
    reviewer_claim:'local-operator-provided-not-authenticated'};
  await put(join(dest,'checkpoint.json'),checkpoint);
  const observed=await verifyDoor(input,modules);
  if(Date.parse(at)<Date.parse(input.contact.sensed_at))throw Error('SESSION_BEFORE_ENCOUNTER');
  const body={schema:'static-os.return-room-session/v0',
    state:'HELD_QUESTION',input_fingerprints:fingerprints,
    inspection:observed, at,operator_selected:true,
    scope:'LOCAL_QUESTION_WORKBENCH_ONLY',writes_to_source_worlds:false,
    unresolved_questions:[observed.question]};
  const session={...body,session_id:hash(canonical(body))};
  await put(join(dest,'session.json'),session);
  return session;
}
export async function replayDocket({paths,outputDir,modules}){
  const folder=resolve(outputDir);
  const checkpoint=await readJSON(join(folder,'checkpoint.json'));
  if(checkpoint.schema!=='static-os.return-room-checkpoint/v0'||checkpoint.state!=='PREPARED'||
     checkpoint.operator_selected!==true||checkpoint.automatic_retry!==false)
     throw Error('INVALID_CHECKPOINT');
  // PREPARED remains a durable uncertainty, not implicit authority to retry.
  const statePath=join(folder,'session.json');
  let saved;
  try{saved=await readJSON(statePath);}catch(e){
    if(e.code==='ENOENT')return {state:'PREPARED_HOLD',no_retry:true,executed_again:false};
    throw e;
  }
  const {input,fingerprints}=await readDocketInputs(paths);
  if(!eq(checkpoint.input_fingerprints,fingerprints)||
    !eq(saved.input_fingerprints,fingerprints))throw Error('INPUT_BYTES_CHANGED');
  const inspection=await verifyDoor(input,modules);
  const {session_id,...body}=saved;
  if(session_id!==hash(canonical(body))||saved.schema!=='static-os.return-room-session/v0'||
     saved.state!=='HELD_QUESTION'||saved.at!==checkpoint.at||
     !eq(inspection,saved.inspection)||!eq(saved.unresolved_questions,[inspection.question])||
     saved.scope!=='LOCAL_QUESTION_WORKBENCH_ONLY'||saved.writes_to_source_worlds!==false)
    throw Error('SESSION_REPLAY_NOT_RECONSTRUCTIBLE');
  return {schema:'static-os.return-room-replay/v0',state:'HELD_QUESTION',
    session_id,crossing_id:inspection.crossing_id,question:inspection.question,
    independently_reverified:true,read_only:true,executed_again:false,
    next_turn:'NOT_AUTHORIZED',owner_authority:'none'};
}
