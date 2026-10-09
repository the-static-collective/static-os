import {
  createField,validateField,turn,setDial,enter,rise,address,restoreAddress,
  worldState,previewViewport,RENDER_DEPTH_LIMIT
} from '/src/mandelbrot-field.mjs';
import {radioWorldDoors,chooseRadioDoor} from '/src/radio-world-adapter.mjs';

const $=id=>document.getElementById(id);
let state=createField();
let renderSerial=0;
let pointer=null;
let wheelX=0,wheelY=0;
const canvas=$('fractal'),ctx=canvas.getContext('2d',{alpha:false});
const guides=$('guides'),g=guides.getContext('2d');
const originAddress=address(state);
const W=canvas.width,H=canvas.height;
const colors=Array.from({length:512},(_,i)=>{
  const u=i/512;
  const r=Math.round(26+196*Math.pow(.5+.5*Math.sin(6.283*(u+.66)),2));
  const gg=Math.round(40+172*Math.pow(.5+.5*Math.sin(6.283*(u+.12)),2));
  const b=Math.round(57+178*Math.pow(.5+.5*Math.sin(6.283*(u+.37)),2));
  return [r,gg,b];
});

function notice(message){$('notice').textContent=message;}
function urlField(){
  const hash=location.hash;
  if(!hash.startsWith('#field='))return null;
  try{return restoreAddress(decodeURIComponent(hash.slice('#field='.length)));}
  catch{return null;}
}
function remember(push=false){
  const hash='#field='+encodeURIComponent(address(state));
  if(push)history.pushState({field:address(state)},'',hash);
  else history.replaceState({field:address(state)},'',hash);
}
function apply(next,{push=false,announce=null}={}){
  state=validateField(next);
  remember(push);
  paintUI();
  drawFractal();
  if(announce)notice(announce);
}
function pointColor(iter,zr,zi,limit){
  if(iter>=limit)return [4,11,20];
  const magnitude=Math.sqrt(zr*zr+zi*zi);
  const smooth=iter+1-Math.log2(Math.max(1,Math.log2(Math.max(1.001,magnitude))));
  const n=Math.max(0,Math.round(smooth*7));
  return colors[n%colors.length];
}
function paintGuides(){
  g.clearRect(0,0,W,H);
  g.lineWidth=.45;g.strokeStyle='rgba(182,241,215,.16)';
  for(let x=1;x<11;x++){
    g.beginPath();g.moveTo(x*W/11,0);g.lineTo(x*W/11,H);g.stroke();
  }
  for(let y=1;y<11;y++){
    g.beginPath();g.moveTo(0,y*H/11);g.lineTo(W,y*H/11);g.stroke();
  }
  g.lineWidth=1.3;g.strokeStyle='rgba(179,250,215,.67)';
  const cx=W/2,cy=H/2;
  g.beginPath();g.moveTo(cx-11,cy);g.lineTo(cx+11,cy);g.moveTo(cx,cy-11);g.lineTo(cx,cy+11);g.stroke();
}
function drawFractal(){
  const viewport=previewViewport(state),serial=++renderSerial;
  $('preview-hold').hidden=viewport.renderable;
  $('render-status').className='pill'+(viewport.renderable?' good':'');
  $('render-status').textContent=viewport.renderable?'MATHEMATICAL PREVIEW':'PRECISION HOLD';
  $('precision-label').textContent=viewport.renderable?
    'Float viewport · exact dial address':'Address exact · render bounded at depth '+RENDER_DEPTH_LIMIT;
  const zoom=3.4/viewport.span;
  $('zoom-readout').textContent=Number.isFinite(zoom)?zoom.toExponential(2)+'×':'BEYOND FLOAT';
  if(!viewport.renderable){
    ctx.fillStyle='#06111c';ctx.fillRect(0,0,W,H);
    paintGuides();return;
  }
  const image=ctx.createImageData(W,H),data=image.data;
  const iterations=Math.min(260,88+viewport.depth*12+state.granularity*3);
  const factor=viewport.span/W;
  let row=0;
  const batch=()=>{
    if(serial!==renderSerial)return;
    const end=Math.min(H,row+8);
    for(let y=row;y<end;y++){
      const im=viewport.im+(y-H/2)*factor;
      for(let x=0;x<W;x++){
        const re=viewport.re+(x-W/2)*factor;
        let zr=0,zi=0,zr2=0,zi2=0,n=0;
        while(n<iterations&&zr2+zi2<=256){
          zi=2*zr*zi+im;
          zr=zr2-zi2+re;
          zr2=zr*zr;zi2=zi*zi;n++;
        }
        const c=pointColor(n,zr,zi,iterations),idx=(y*W+x)*4;
        data[idx]=c[0];data[idx+1]=c[1];data[idx+2]=c[2];data[idx+3]=255;
      }
    }
    row=end;
    ctx.putImageData(image,0,0);
    if(row<H)requestAnimationFrame(batch);
    else if(serial===renderSerial)paintGuides();
  };
  requestAnimationFrame(batch);
}
function paintUI(){
  $('tuning').value=state.tuning;
  $('granularity').value=state.granularity;
  $('tune-number').innerHTML=String(state.tuning).padStart(2,'0')+' <small>/11</small>';
  $('grain-number').innerHTML=String(state.granularity).padStart(2,'0')+' <small>/11</small>';
  $('world-address').textContent=address(state);
  $('depth-number').textContent=String(state.path.length);
  $('rise').disabled=!state.path.length;
  $('enter').disabled=state.path.length>=96;
  const crumb=$('breadcrumbs');crumb.replaceChildren();
  const root=document.createElement('button');root.type='button';
  root.className='crumb'+(state.path.length===0?' current':'');
  root.textContent='ROOT';root.addEventListener('click',()=>apply(createField(),{push:true,announce:'Returned to root; no external consequence.'}));
  crumb.append(root);
  let prefix=createField();
  for(const [index,pair] of state.path.entries()){
    prefix={...prefix,path:[...prefix.path,pair]};
    const snapshot={...prefix,tuning:6,granularity:6};
    const button=document.createElement('button');button.type='button';
    button.className='crumb'+(index===state.path.length-1?' current':'');
    button.textContent=String(index+1).padStart(2,'0')+' · '+String(pair.t).padStart(2,'0')+
      '/'+String(pair.g).padStart(2,'0');
    button.addEventListener('click',()=>apply(snapshot,{push:true,announce:'Returned to preserved ancestor address.'}));
    crumb.append(button);
  }
  const witness=worldState(state);
  $('exact-intervals').textContent=JSON.stringify({
    exact:true,radix:11,
    tuning:witness.tuningCell,
    granularity:witness.granularityCell,
    no_authority:witness.worldSourceAuthority,
    no_crossing:witness.crossingGranted,
    media_playing:witness.mediaPlayback
  },null,2);
}
function range(axis,value){apply(setDial(state,axis,Number(value)));}
$('tuning').addEventListener('input',e=>range('tuning',e.target.value));
$('granularity').addEventListener('input',e=>range('granularity',e.target.value));
for(const [id,axis,delta] of [
  ['tune-down','tuning',-1],['tune-up','tuning',1],
  ['grain-down','granularity',-1],['grain-up','granularity',1]
]){
  $(id).addEventListener('click',()=>apply(turn(state,axis,delta)));
}
$('enter').addEventListener('click',()=>{
  if(state.path.length>=96)return;
  apply(enter(state),{push:true,announce:'Entered nested world. Tuning only; no stream or compute initiated.'});
});
$('rise').addEventListener('click',()=>{
  apply(rise(state),{push:true,announce:'Rose one level; prior dials restored.'});
});
$('root').addEventListener('click',()=>{
  apply(createField(),{push:true,announce:'Returned to root.'});
});
$('bookmark').addEventListener('click',async()=>{
  const exact=address(state),link=location.href;
  try{
    if(!navigator.clipboard?.writeText)throw new Error('clipboard unavailable');
    await navigator.clipboard.writeText(link);
    notice('Exact nested address copied to clipboard: '+exact+'. No stream was contacted.');
  }catch{
    notice('Copy manually: '+link+' . This address reconstructs the dial settings exactly.');
    $('world-address').focus();
  }
});
function handleKeys(e){
  if(e.altKey||e.metaKey||e.ctrlKey)return;
  if(e.target instanceof HTMLInputElement && ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;
  let next=null;
  if(e.key==='ArrowUp')next=turn(state,'tuning',1);
  if(e.key==='ArrowDown')next=turn(state,'tuning',-1);
  if(e.key==='ArrowLeft')next=turn(state,'granularity',-1);
  if(e.key==='ArrowRight')next=turn(state,'granularity',1);
  if(e.key==='Enter'&&e.target===$('field')&&state.path.length<96)next=enter(state);
  if(e.key==='Backspace'&&e.target===$('field'))next=rise(state);
  if(next){e.preventDefault();apply(next,{push:['Enter','Backspace'].includes(e.key)});}
}
window.addEventListener('keydown',handleKeys);
const field=$('field');
field.addEventListener('pointerdown',e=>{
  if(e.button!==0)return;
  pointer={id:e.pointerId,x:e.clientX,y:e.clientY,t:state.tuning,g:state.granularity};
  field.setPointerCapture(e.pointerId);
});
field.addEventListener('pointermove',e=>{
  if(!pointer||pointer.id!==e.pointerId)return;
  const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
  const nextT=Math.max(1,Math.min(11,pointer.t-Math.round(dy/28)));
  const nextG=Math.max(1,Math.min(11,pointer.g+Math.round(dx/28)));
  if(nextT!==state.tuning||nextG!==state.granularity){
    apply({...state,tuning:nextT,granularity:nextG});
  }
});
function releasePointer(){pointer=null;}
field.addEventListener('pointerup',releasePointer);
field.addEventListener('pointercancel',releasePointer);
field.addEventListener('wheel',e=>{
  e.preventDefault();
  if(e.shiftKey){wheelX+=e.deltaY;}else{wheelX+=e.deltaX;wheelY+=e.deltaY;}
  let dt=0,dg=0;
  while(Math.abs(wheelY)>=28){dt+=wheelY<0?1:-1;wheelY+=wheelY<0?28:-28;}
  while(Math.abs(wheelX)>=28){dg+=wheelX>0?1:-1;wheelX+=wheelX>0?-28:28;}
  if(dt||dg)apply({...state,tuning:Math.max(1,Math.min(11,state.tuning+dt)),
    granularity:Math.max(1,Math.min(11,state.granularity+dg))});
},{passive:false});
function mountRadioDoors(){
  const container=$('door-list');container.replaceChildren();
  const worlds=radioWorldDoors(state);
  for(const item of worlds.entries){
    const card=document.createElement('article');card.className='door';
    const place=document.createElement('div');place.className='where';place.textContent=item.territory;
    const name=document.createElement('strong');name.textContent=item.owner;
    const label=document.createElement('div');label.className='owner';
    label.textContent='Independent source · no in-app audio license';
    const link=document.createElement('a');link.href=chooseRadioDoor(state,item.id).href;
    link.target='_blank';link.rel='noopener noreferrer';link.referrerPolicy='no-referrer';
    link.textContent='Open official site ↗';
    link.addEventListener('click',()=>{
      // User-initiated external navigation is not proof of play.
      notice('Opened '+item.owner+' official doorway on user request. Playback, rights and reach remain unverified.');
    });
    card.append(place,name,label,link);container.append(card);
  }
}
function onHistory(){
  const restored=urlField();
  if(restored){state=restored;paintUI();drawFractal();notice('Restored exact nested address from URL. No effects replayed.');}
  else{state=createField();paintUI();drawFractal();notice('Invalid address refused; root restored without external action.');}
}
window.addEventListener('popstate',onHistory);
window.addEventListener('hashchange',onHistory);
const initial=urlField();
if(initial)state=initial;
else if(location.hash.startsWith('#field='))notice('Invalid world address refused; root selected.');
remember(false);
paintUI();mountRadioDoors();drawFractal();
if('serviceWorker' in navigator && location.hostname==='127.0.0.1'){
  navigator.serviceWorker.register('/sw.js').catch(()=>{});
}
