import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,rm,access,stat} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {spawnSync} from 'node:child_process';
import {makeSyntheticDonor} from '../return_room/synthetic-donor.mjs';
import {verifyDoor,startDocket,replayDocket,readDocketInputs} from '../return_room/room.mjs';

const relatteRoot=resolve(process.env.RELATTE_SRC||'.deps/reLATTE');
const treasureRoot=resolve(process.env.NATIONAL_TREASURE_SRC||'.deps/national-treasure');
async function withFixture(cb){
 const dir=await mkdtemp(join(tmpdir(),'static-return-room-'));
 try{
  const fixture=await makeSyntheticDonor(dir,relatteRoot,treasureRoot);
  return await cb({...fixture,dir});
 }finally{await rm(dir,{recursive:true,force:true});}
}
const changed=(o,fn)=>{const v=structuredClone(o);fn(v);return v;};
test('real native reLATTE P256 receives and holds, then native NT asks for original source',()=>withFixture(async({input,modules})=>{
 const v=await verifyDoor(input,modules);
 assert.equal(v.receiver_signatures_verified,3);
 assert.equal(v.question_aperture,'source-object');
 assert.equal(v.original_source_ancestry,'NOT_ESTABLISHED');
 assert.equal(v.claimed_human_observer,'NOT_INDEPENDENTLY_AUTHENTICATED');
 assert.equal(v.admission,'none');
 assert.equal(v.next_turn,'NOT_AUTHORIZED');
 assert.equal(v.boot_proof,false);
 assert.match(v.question,/\?$/);
}));
test('create-only operator-selected docket replays cold without re-sending or modifying MEMENTO',()=>withFixture(async({paths,modules,dir})=>{
 const out=join(dir,'return-room-session');
 const at='2026-10-11T14:06:00.000Z';
 await assert.rejects(startDocket({paths,outputDir:out,reviewer:'synthetic-operator',
  at,selected:false,modules}),/EXPLICIT_OPERATOR/);
 const session=await startDocket({paths,outputDir:out,reviewer:'synthetic-operator',
  at,selected:true,modules});
 assert.equal(session.state,'HELD_QUESTION');
 assert.equal(session.writes_to_source_worlds,false);
 assert.equal(session.inspection.automatic_execution,false);
 const checkpoint=JSON.parse(await readFile(join(out,'checkpoint.json'),'utf8'));
 assert.equal(checkpoint.state,'PREPARED');
 assert.equal(checkpoint.automatic_retry,false);
 const again=await replayDocket({paths,outputDir:out,modules});
 assert.equal(again.state,'HELD_QUESTION');
 assert.equal(again.independently_reverified,true);
 assert.equal(again.executed_again,false);
 assert.equal(again.owner_authority,'none');
 assert.equal(again.session_id,session.session_id);
 assert.equal((await stat(join(out,'session.json'))).mode & 0o777,0o600);
 await assert.rejects(startDocket({paths,outputDir:out,reviewer:'synthetic-operator',
   at,selected:true,modules}),{code:'EEXIST'});
 const before=await readFile(join(out,'session.json'),'utf8');
 assert.equal(before,await readFile(join(out,'session.json'),'utf8'));
}));
test('tampered signed receipts, destination claims, payload bytes, witness or canon are rejected',()=>withFixture(async({input,modules})=>{
 for(const mutate of [
  x=>x.review.held.note+=' counterfeit',
  x=>x.review.received.signing.signature='A'.repeat(86),
  x=>x.review.snapshot.admitted.push(x.carrier.crossing.crossing_id),
  x=>x.review.verified_payload_custody.extensions.local_receiver.payload_custody.sha256='f'.repeat(64),
  x=>x.carrier.payload.slots[0].commitment='hmac-sha256:'+'a'.repeat(64),
  x=>x.carrier.payload.authority='owner',
  x=>x.carrier.sender_public_released=true,
  x=>x.contact.occurrence_ref='relatte-receipt-v0:'+'a'.repeat(64),
  x=>x.contact.sensed_at='2026-10-11T13:00:00.000Z',
  x=>x.association.status='accepted',
  x=>x.association.member_refs=['invented','relationship'],
  x=>x.questionSeed.provenance_class='observed',
  x=>x.questionSeed.source_object_recoverable=true,
  x=>x.questionSeed.hold_receipt_id='relatte-receipt-v0:'+'0'.repeat(64),
  x=>x.questionSeed.original_filename='private-note'
 ]){
   await assert.rejects(verifyDoor(changed(input,mutate),modules));
 }
}));
test('PREPARED without a completed session stays HOLD; later replay never executes donor',()=>withFixture(async({paths,modules,dir})=>{
 const out=join(dir,'aborted');
 const session=await startDocket({paths,outputDir:out,reviewer:'operator',selected:true,
   at:'2026-10-11T14:06:00.000Z',modules});
 await rm(join(out,'session.json'));
 const replay=await replayDocket({paths,outputDir:out,modules});
 assert.equal(replay.state,'PREPARED_HOLD');
 assert.equal(replay.no_retry,true);
 assert.equal(replay.executed_again,false);
}));
test('changed original files invalidate existing session even if JSON objects are equivalent',()=>withFixture(async({paths,modules,dir})=>{
 const out=join(dir,'record');
 await startDocket({paths,outputDir:out,reviewer:'operator',selected:true,
   at:'2026-10-11T14:06:00.000Z',modules});
 const orig=await readFile(paths.questionSeed,'utf8');
 await writeFile(paths.questionSeed,' '+orig);
 await assert.rejects(replayDocket({paths,outputDir:out,modules}),/INPUT_BYTES_CHANGED/);
}));
test('read-only CLI works in independent Node process and refuses missing selection',()=>withFixture(async({paths,dir})=>{
 const script=resolve('scripts/return-room.mjs');
 const arg=[
   '--carrier',paths.carrier,'--review',paths.review,'--seed',paths.questionSeed,
   '--contact',paths.contact,'--association',paths.association,
   '--relatte-root',relatteRoot,'--treasure-root',treasureRoot
 ];
 const run=(a)=>spawnSync(process.execPath,['--experimental-strip-types',script,...a],{encoding:'utf8'});
 const inspected=run(['inspect',...arg]);
 assert.equal(inspected.status,0,inspected.stderr);
 const observation=JSON.parse(inspected.stdout);
 assert.equal(observation.operator_selected,false);
 assert.equal(observation.inspection.question_aperture,'source-object');
 const out=join(dir,'cli-docket');
 const without=run(['open',...arg,'--out',out,'--reviewer','operator','--at','2026-10-11T14:06:00.000Z']);
 assert.notEqual(without.status,0);
 await assert.rejects(access(out));
 const opened=run(['open',...arg,'--out',out,'--reviewer','operator',
   '--at','2026-10-11T14:06:00.000Z','--select-local-question']);
 assert.equal(opened.status,0,opened.stderr);
 assert.equal(JSON.parse(opened.stdout).state,'HELD_QUESTION');
 const replay=run(['replay',...arg,'--out',out]);
 assert.equal(replay.status,0,replay.stderr);
 assert.equal(JSON.parse(replay.stdout).executed_again,false);
 const duplicate=run(['open',...arg,'--out',out,'--reviewer','operator',
   '--at','2026-10-11T14:06:00.000Z','--select-local-question']);
 assert.notEqual(duplicate.status,0);
}));
