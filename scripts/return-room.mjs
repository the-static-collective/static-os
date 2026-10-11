#!/usr/bin/env node
// STATIC OS RETURN ROOM: one read-only foreign encounter; all input paths explicit.
// No background process, network, boot hooks, or writes to source repositories.
import {resolve} from 'node:path';
import {readDocketInputs,verifyDoor,donorModules,startDocket,replayDocket} from '../return_room/room.mjs';
const flags=['carrier','review','seed','contact','association','relatte-root','treasure-root','out','reviewer','at'];
const parse=a=>{
 const command=a.shift();
 if(!['inspect','open','replay'].includes(command))throw Error('EXPECTED_INSPECT_OPEN_OR_REPLAY');
 const o={};
 for(let i=0;i<a.length;i++){
   if(a[i]==='--select-local-question'){o.selected=true;continue;}
   if(!a[i].startsWith('--')||!flags.includes(a[i].slice(2))||!a[i+1]||a[i+1].startsWith('--')||
      Object.hasOwn(o,a[i].slice(2)))throw Error('INVALID_ARGUMENT: '+a[i]);
   o[a[i].slice(2)]=a[++i];
 }
 for(const k of ['carrier','review','seed','contact','association','relatte-root','treasure-root'])
   if(!o[k])throw Error('MISSING_'+k);
 if(command!=='inspect'&&!o.out)throw Error('MISSING_OUT');
 if(command==='open'&&(!o.selected||!o.reviewer||!o.at))throw Error('EXPLICIT_LOCAL_SELECTION_REQUIRED');
 if(command!=='open'&&(o.selected||o.reviewer||o.at))throw Error('OPERATOR_ACTION_UNEXPECTED');
 return {command,o};
};
try{
 const {command,o}=parse(process.argv.slice(2));
 const paths={carrier:o.carrier,review:o.review,questionSeed:o.seed,contact:o.contact,association:o.association};
 const modules=await donorModules(o['relatte-root'],o['treasure-root']);
 if(command==='inspect'){
  const {input}=await readDocketInputs(paths);
  const v=await verifyDoor(input,modules);
  process.stdout.write(JSON.stringify({inspection:v,proposed_only:true,operator_selected:false},null,2)+'\n');
 }else if(command==='open'){
  const session=await startDocket({paths,outputDir:o.out,reviewer:o.reviewer,
    at:o.at,selected:o.selected,modules});
  process.stdout.write(JSON.stringify({path:resolve(o.out),session_id:session.session_id,
    state:session.state,question:session.inspection.question,
    automatic_next_turn:false,public_release:false},null,2)+'\n');
 }else{
  const replay=await replayDocket({paths,outputDir:o.out,modules});
  process.stdout.write(JSON.stringify(replay,null,2)+'\n');
 }
}catch(e){
 console.error('HOLD: '+e.message);
 process.exitCode=2;
}
