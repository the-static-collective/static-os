// Synthetic native reLATTE x National Treasure witness for STATIC OS RETURN ROOM.
// No checkout of private MEMENTO; this only creates public-safe portable shapes.
import {createHash} from 'node:crypto';
import {mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {donorModules} from '../return_room/room.mjs';

const h=s=>'sha256:'+createHash('sha256').update(s).digest('hex');
const stable=v=>v&&typeof v==='object'
 ?Array.isArray(v)?v.map(stable):Object.fromEntries(Object.keys(v).sort().map(k=>[k,stable(v[k])]))
 :v;
const canonical=v=>JSON.stringify(stable(v));
const laws=[
 'ARRANGEMENT != SEQUENCE','ADJACENCY != ANCESTRY',
 'PROPOSAL != ADMISSION','HINT != EVIDENCE',
 'SIGNATURE != SOURCE AUTHORITY','HOLD != CANON',
 'PUBLIC COMMITMENT != PRIVATE SOURCE DISCLOSURE'
];
const nonClaims=[
 'HOLD receipt witnesses a local receiving disposition, not historical ancestry.',
 'MEMENTO original source objects remain private and have not been independently inspected here.',
 'A shuffled adjacency is a question candidate, not an admitted relation.'
];
export async function makeSyntheticDonor(root,relatteRoot,treasureRoot){
 const modules=await donorModules(relatteRoot,treasureRoot);
 const payload={
  schema:'memento.clown-proposal/v0',relation_kind:'madd-clown',typing_basis:'fallback',
  slots:[
   {position:0,commitment:'hmac-sha256:'+'3'.repeat(64)},
   {position:1,commitment:'hmac-sha256:'+'4'.repeat(64)}
  ],
  itinerary_commitment:'hmac-sha256:'+'5'.repeat(64),
  outcome:'PROPOSED_ONLY',evidence_class:'proposal',authority:'none',admission:'none',laws
 };
 const bytes=Buffer.from(canonical(payload));
 const address=h(bytes);
 const spec={
  schema:'relatte.opaque-organ-spec/v0',
  family_ref:'memento:crazy-slots-proposed-adjacency/v0',
  donor_contract_ref:'memento:crazy-slots/v0',
  artifact_kind:'proposed-adjacency-no-source-authority',
  source_world:'world:memento-crazy-slots-experimental-adapter',
  source_particular:'particular:madd-clown:'+address.slice(7),
  source_history_head:null,
  payload_refs:[{address,role:'redacted-proposal',media_type:'application/vnd.static-collective.clown-proposal+json'}],
  donor_claims:{source_authority:'not_authenticated',projection:'hmac-redacted',
   proposed_relation_type:'madd-clown',type_source:'fallback',admission:'none',semantic_effect:'none'},
  requested_effect:null,return_address:null,created_at:'2026-10-11T14:00:00.000Z'
 };
 const key=await modules.protocol.generateP256KeyPair();
 const crossing=await modules.organ.sealOpaqueOrganCrossing(spec,key);
 const carrier={
  schema:'memento.clown-relatte-carrier/v0',payload,crossing,
  authenticity:'EXPERIMENTAL_EPHEMERAL_SIGNER_NOT_MEMENTO_OWNER',
  admission:'none',sender_public_released:false
 };
 const {LocalReceiver}=await import(pathToFileURL(join(relatteRoot,'src/receiver.ts')).href);
 const receiver=await LocalReceiver.create(join(root,'native-receiver'),{
  world_id:'world:static-os-synthetic-donor',
  receiver_particular:'particular:static-os-synthetic-donor',
  contract_ref:'static-os:synthetic-question-review/v0'
 });
 const received=await receiver.receive(crossing,'2026-10-11T14:00:00.000Z');
 const held=await receiver.dispose(crossing.crossing_id,'HOLD','2026-10-11T14:01:00.000Z');
 const verified_payload_custody=await receiver.verifyPayloadBytes(
  crossing.crossing_id,bytes,'2026-10-11T14:02:00.000Z');
 const review={
  schema:'memento.clown-relatte-review/v0',crossing_id:crossing.crossing_id,
  receiver_signer_scope:'EXPERIMENTAL_LOCAL_KEY_NOT_REAL_WORLD_IDENTITY',
  received,held,verified_payload_custody,snapshot:receiver.snapshot(),
  admission:'none',locally_held:true,remotely_delivered:false
 };
 const contact={
  schema:'memento.understory-record/v0',family:'contact',id:'contact-madd-hold-synthetic001',
  observer:'synthetic-reader',recorded_at:'2026-10-11T14:05:00.000Z',
  sensed_at:'2026-10-11T14:05:00.000Z',
  occurrence_ref:held.receipt_id,
  evidence_refs:[crossing.crossing_id,received.receipt_id,held.receipt_id,verified_payload_custody.receipt_id]
 };
 const association={
  schema:'memento.understory-record/v0',family:'association',id:'association-madd-hold-synthetic001',
  observer:'synthetic-reader',recorded_at:'2026-10-11T14:05:00.000Z',
  evidence_refs:[contact.id,held.receipt_id,verified_payload_custody.receipt_id],
  member_refs:payload.slots.map(z=>z.commitment),
  relation_hint:'unresolved-later-adjacency/madd-clown/fallback',status:'unresolved'
 };
 const questionSeed={
  schema:'memento.held-question-seed/v0',crossing_id:crossing.crossing_id,hold_receipt_id:held.receipt_id,
  relation_kind:'madd-clown',typing_basis:'fallback',source_object_recoverable:false,
  historical_relation_established:false,private_source_included:false,
  observed_event:'LOCAL_HOLD_ENCOUNTER',provenance_class:'speculation',support_confidence:'unsupported',
  non_claims:nonClaims
 };
 const pathset={};
 for(const [k,obj] of Object.entries({carrier,review,questionSeed,contact,association})){
  const file=join(root,k+'.json');
  await writeFile(file,JSON.stringify(obj,null,2)+'\n',{flag:'wx',mode:0o600});
  pathset[k]=file;
 }
 return {input:{carrier,review,questionSeed,contact,association},paths:pathset,modules,
  signed_ids:[received.receipt_id,held.receipt_id,verified_payload_custody.receipt_id]};
}
