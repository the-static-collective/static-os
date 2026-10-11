import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
 createField,validateField,turn,setDial,enter,rise,address,restoreAddress,exactCell,
 compareCells,previewViewport,worldState,MAX_PATH,RENDER_DEPTH_LIMIT
} from '../src/mandelbrot-field.mjs';
import {mandelbrotEscape} from '../src/mandelbrot-math.mjs';
import {radioWorldDoors,chooseRadioDoor} from '../src/radio-world-adapter.mjs';
import {createFieldServer} from '../src/world-field-server.mjs';

const clone=x=>structuredClone(x);
const src=name=>readFileSync(new URL('../web/'+name,import.meta.url),'utf8');

test('start is two 6-of-11 dial positions at exact root',()=>{
  const s=createField();
  assert.deepEqual({t:s.tuning,g:s.granularity,depth:s.path.length},{t:6,g:6,depth:0});
  assert.equal(address(s),'MWF1/t06g06');
  assert.equal(worldState(s).radioTransmission,false);
});
test('11 tuning positions and 11 granularity positions are independent',()=>{
  const s=createField();
  for(let t=1;t<=11;t++)for(let g=1;g<=11;g++){
    const a=setDial(setDial(s,'tuning',t),'granularity',g);
    assert.equal(a.tuning,t);assert.equal(a.granularity,g);
    assert.equal(restoreAddress(address(a)).tuning,t);
    assert.equal(restoreAddress(address(a)).granularity,g);
  }
});
test('dial turns clamp without carry or granting new authority',()=>{
  const s=turn(turn(createField(),'tuning',11),'granularity',-11);
  assert.equal(s.tuning,11);assert.equal(s.granularity,1);
  assert.equal(worldState(s).crossingGranted,false);
  assert.equal(worldState(s).remoteCompute,false);
});
test('invalid axes and fractional out-of-range positions fail closed',()=>{
  for(const x of ['play','publish','transmit','__proto__',null]){
    assert.throws(()=>turn(createField(),x,1));
    assert.throws(()=>setDial(createField(),x,6));
  }
  for(const x of [0,12,1.5,'6',NaN,null]){
    assert.throws(()=>setDial(createField(),'tuning',x));
  }
});
test('non-integer and huge deltas denied',()=>{
  for(const x of [0.5,Infinity,NaN,'2',12,-12])
    assert.throws(()=>turn(createField(),'granularity',x));
});
test('enter commits current 11-pair and creates fresh nested dial center',()=>{
  let s=setDial(setDial(createField(),'tuning',8),'granularity',3);
  s=enter(s);
  assert.equal(address(s),'MWF1/t08g03/t06g06');
  assert.deepEqual(s.path,[{t:8,g:3}]);
  assert.equal(s.tuning,6);assert.equal(s.granularity,6);
});
test('rise returns exactly the parent dials without changing it',()=>{
  const parent=setDial(setDial(createField(),'tuning',11),'granularity',1);
  const child=turn(enter(parent),'tuning',2);
  assert.deepEqual(rise(child),parent);
  assert.deepEqual(parent.path,[]);
});
test('rising root is deterministic no-op',()=>{
  const root=createField();
  assert.deepEqual(rise(root),root);
  assert.notEqual(rise(root),root);
});
test('deep address round trip exactly restores every nested cup',()=>{
  let s=createField();
  for(let k=0;k<80;k++){
    s=setDial(setDial(s,'tuning',(k%11)+1),'granularity',((k*7)%11)+1);
    s=enter(s);
  }
  s=setDial(s,'tuning',9);
  const literal=address(s);
  assert.deepEqual(restoreAddress(literal),s);
  assert.equal(address(restoreAddress(literal)),literal);
  assert.equal(worldState(s).depth,80);
  assert.equal(worldState(s).mediaPlayback,false);
});
test('exact 11-way cell denominator and numerator are integer strings',()=>{
  const s=createField();
  assert.deepEqual(exactCell(s,'tuning').denominator,'11');
  assert.deepEqual(exactCell(s,'tuning').lowerNumerator,'5');
  const q=enter(setDial(s,'tuning',11));
  assert.equal(exactCell(q,'tuning').denominator,'121');
  assert.equal(exactCell(q,'tuning').lowerNumerator,(10n*11n+5n).toString());
});
test('different paths distinguish cells after JS floating-point collapse',()=>{
  let a=createField();
  for(let i=0;i<75;i++)a=enter(a);
  const b=setDial(a,'tuning',7);
  const x=exactCell(a,'tuning'),y=exactCell(b,'tuning');
  assert.notEqual(x.lowerNumerator,y.lowerNumerator);
  assert.equal(compareCells(x,y),-1);
  assert.equal(compareCells(y,x),1);
  assert.equal(compareCells(x,x),0);
  assert.ok(x.denominator.length>50);
});
test('exact granularity cell and tune cell are typed distinctly',()=>{
  const s=enter(setDial(setDial(createField(),'tuning',2),'granularity',10));
  const t=exactCell(s,'tuning'),g=exactCell(s,'granularity');
  assert.equal(t.axis,'tuning');assert.equal(g.axis,'granularity');
  assert.notEqual(t.lowerNumerator,g.lowerNumerator);
  assert.equal(t.exact,true);assert.equal(g.exact,true);
});
test('empty exact cell parent interval is exactly [0,1)',()=>{
  const a=exactCell(createField(),'tuning',false);
  assert.deepEqual([a.lowerNumerator,a.upperNumerator,a.denominator],['0','1','1']);
});
test('malformed schemas and extra authority fields never restore',()=>{
  for(const mutate of [
    s=>s.schema='evil',
    s=>s.transmit=true,
    s=>s.path=[{t:6,g:6,grant:true}],
    s=>s.path=[{t:12,g:1}],
    s=>s.path='000',
    s=>s.tuning=0,
    s=>s.granularity='6'
  ]){const x=clone(createField());mutate(x);assert.throws(()=>validateField(x));}
});
test('reject unknown and malicious bookmark addresses',()=>{
  for(const x of [
    'MWF0/t06g06','MWF1/t00g06','MWF1/t06g12','MWF1/t6g06','MWF1/t06g06/',
    'MWF1/t06g06/grant','MWF1/t06g06?stream=1','javascript:alert(1)', ''
  ])assert.throws(()=>restoreAddress(x));
});
test('valid bookmarks cannot contain executable or cross-boundary instructions',()=>{
  const a=address(enter(setDial(createField(),'granularity',11)));
  assert.ok(/^MWF1\/(?:t\d{2}g\d{2}\/)*t\d{2}g\d{2}$/.test(a));
  assert.ok(!a.includes('https:'));
  assert.ok(!a.includes('grant'));
});
test('depth stays bounded at 96 while normal path is still exact',()=>{
  let s=createField();
  for(let i=0;i<MAX_PATH;i++)s=enter(s);
  assert.equal(s.path.length,MAX_PATH);
  assert.throws(()=>enter(s),/ADDRESS_DEPTH_EXCEEDED/);
  assert.deepEqual(restoreAddress(address(s)),s);
});
test('oversized paths and addresses are refused before allocating',()=>{
  const s=createField();
  s.path=Array.from({length:MAX_PATH+1},()=>({t:6,g:6}));
  assert.throws(()=>validateField(s));
  assert.throws(()=>restoreAddress('MWF1/'+'t06g06/'.repeat(1000)));
});
test('preview is actual finite float c-plane and does not claim exact coordinates',()=>{
  const view=previewViewport(createField());
  assert.ok(view.renderable);assert.equal(view.approximate,true);
  assert.equal(view.coordinateProof,'EXACT_CELL_IN_NAVIGATION_SNAPSHOT_NOT_FLOAT_VIEWPORT');
  assert.ok(view.re<0&&view.re>-2);
  assert.ok(view.span>0);
});
test('vertical tune steers imaginary position, granularity controls scale',()=>{
  const base=createField();
  const upper=previewViewport(setDial(base,'tuning',11));
  const lower=previewViewport(setDial(base,'tuning',1));
  assert.ok(upper.im>lower.im);
  const fine=previewViewport(setDial(base,'granularity',11));
  const coarse=previewViewport(setDial(base,'granularity',1));
  assert.ok(fine.span<coarse.span);
  assert.equal(fine.re,coarse.re);
});
test('zooming in each committed nested world reduces scale',()=>{
  const root=previewViewport(createField()).span;
  const child=previewViewport(enter(createField())).span;
  assert.ok(child<root);
  const grandchild=previewViewport(enter(enter(createField()))).span;
  assert.ok(grandchild<child);
});
test('deep preview refuses numerically unreliable rendering, preserves identity',()=>{
  let s=createField();
  for(let k=0;k<RENDER_DEPTH_LIMIT+1;k++)s=enter(s);
  const view=previewViewport(s);
  assert.equal(view.renderable,false);
  assert.equal(view.reason,'FLOAT_PRECISION_RENDER_LIMIT');
  assert.deepEqual(restoreAddress(address(s)),s);
});
test('correct Mandelbrot orbit does not escape at c=0 for finite budget',()=>{
  const c=mandelbrotEscape(0,0,160);
  assert.equal(c.escaped,false);
  assert.equal(c.iterations,160);
});
test('Mandelbrot orbit at c=-1 cycles with no detected escape',()=>{
  const c=mandelbrotEscape(-1,0,160);
  assert.equal(c.escaped,false);
});
test('quadratic Mandelbrot iteration escapes for exterior parameters',()=>{
  for(const [x,y] of [[2,0],[1,1],[3,0]]){
    const c=mandelbrotEscape(x,y,160);
    assert.equal(c.escaped,true);
    assert.ok(c.iterations<160);
  }
});
test('nonfinite complex coordinates and nonsensical iteration budgets refused',()=>{
  for(const args of [[Infinity,0,100],[0,NaN,100],[0,0,0],[0,0,10000],[0,0,'64']])
    assert.throws(()=>mandelbrotEscape(...args),/MANDELBROT_ARGUMENTS_INVALID/);
});
test('Radio World adapter has only the two explicit independently governed official doorways',()=>{
  const d=radioWorldDoors(createField());
  assert.equal(d.entries.length,2);
  assert.deepEqual(d.entries.map(x=>x.id),['kinship-radio','rock-impact']);
  assert.deepEqual(d.entries.map(x=>x.source),[
    'https://kinshipradio.org/main/','https://rockimpactmakersglobal.org/'
  ]);
  assert.ok(d.entries.every(x=>x.externalAuthority==='OWNER_HELD'));
  assert.ok(d.entries.every(x=>x.streamRights==='NOT_ESTABLISHED'));
});
test('Radio World adapter cannot infer content relationship from Mandelbrot path',()=>{
  let s=createField();
  for(let i=0;i<24;i++)s=enter(setDial(s,'tuning',i%11+1));
  const d=radioWorldDoors(s);
  assert.equal(d.placement,'EXPLICIT_CATALOG_NOT_MANDELBROT_INFERENCE');
  assert.equal(d.playing,false);
  assert.equal(d.performedCrossing,false);
  assert.equal(d.entries.length,2);
});
test('explicit external user action cannot represent playback or crossings',()=>{
  const r=chooseRadioDoor(createField(),'kinship-radio');
  assert.equal(r.intent,'USER_CLICK_OPENS_OFFICIAL_SOURCE');
  assert.equal(r.played,false);
  assert.equal(r.autoplay,false);
  assert.equal(r.crossingsPerformed,0);
  assert.equal(r.computeStarted,false);
  assert.throws(()=>chooseRadioDoor(createField(),'unauthorized-source'));
});
test('UI includes actual canvas, swipe, sliders, keyboard, bookmark and both source doors',()=>{
  const html=src('index.html'),app=src('world-field.js');
  for(const item of [
    'id="fractal"','id="guides"','id="tuning"','id="granularity"',
    'id="bookmark"','id="enter"','id="rise"','id="root"',
    'id="door-list"','id="exact-intervals"'
  ])assert.ok(html.includes(item),item);
  assert.ok(html.includes('Copy world address'));
  for(const item of [
    "pointermove","pointerdown","wheel","popstate","hashchange",
    "keydown","requestAnimationFrame","mandelbrotEscape","radioWorldDoors",
    "clipboard","history.replaceState","history.pushState"
  ])assert.ok(app.toLowerCase().includes(item.toLowerCase()),item);
});
test('app never calls audio, geolocation, streaming or remote compute APIs',()=>{
  const app=src('world-field.js');
  assert.ok(!app.includes('getUserMedia('));
  assert.ok(!app.includes('new Audio('));
  assert.ok(!app.includes('RTCPeerConnection('));
  assert.ok(!app.includes('WebSocket('));
  assert.ok(!app.includes('geolocation'));
  assert.ok(!src('index.html').includes('<audio'));
  assert.ok(!src('index.html').includes('<iframe'));
});
test('service worker keeps offline first-party shell only',()=>{
  const sw=src('sw.js');
  assert.ok(sw.includes('url.origin!==self.location.origin'));
  assert.ok(sw.includes("e.request.method!=='GET'"));
  assert.ok(!sw.includes('kinshipradio.org'));
  assert.ok(!sw.includes('rockimpactmakersglobal.org'));
  assert.ok(!sw.includes('.mp3'));
  assert.ok(!sw.includes('.m3u8'));
});
test('offline app manifest has no external script or hidden permissions',()=>{
  const manifest=JSON.parse(src('manifest.webmanifest'));
  assert.equal(manifest.display,'standalone');
  assert.equal(manifest.scope,'/');
  assert.equal(Object.hasOwn(manifest,'permissions'),false);
});
test('development server fails closed against public binding',()=>{
  assert.throws(()=>createFieldServer({host:'0.0.0.0'}),/LOOPBACK_ONLY/);
  assert.throws(()=>createFieldServer({port:99999}),/PORT_INVALID/);
});
test('real localhost serves the fractal app and pure model with restrictive CSP',async()=>{
  const server=createFieldServer();
  const up=await server.start();
  try{
    const index=await fetch(up.url);
    assert.equal(index.status,200);
    assert.match(index.headers.get('content-security-policy'),/media-src 'none'/);
    assert.match(index.headers.get('content-security-policy'),/script-src 'self'/);
    assert.equal(index.headers.get('x-frame-options'),'DENY');
    for(const file of [
      'world-field.css','world-field.js','src/mandelbrot-field.mjs',
      'src/mandelbrot-math.mjs','src/radio-world-adapter.mjs',
      'sw.js','manifest.webmanifest','icon.svg'
    ])assert.equal((await fetch(up.url+file)).status,200,file);
  }finally{await server.stop();}
});
test('HTTP refuses POST, stream relay, OBS action, local file and URL proxy routes',async()=>{
  const server=createFieldServer();const up=await server.start();
  try{
    for(const path of ['api/live','relay','proxy','stream.mp3',
      'etc/passwd','server-key','src/world-field-server.mjs','src/../README.md']){
      const result=await fetch(up.url+path,{redirect:'manual'});
      assert.equal(result.status,404,path);
    }
    for(const method of ['POST','PUT','DELETE']){
      assert.equal((await fetch(up.url,{method})).status,405,method);
    }
    assert.equal((await fetch(up.url,{method:'HEAD'})).status,200);
  }finally{await server.stop();}
});
