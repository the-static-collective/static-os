/* MANDELBROT-WORLD-FIELD-001
 * Genuine c -> z^2 + c Mandelbrot plane renderer is in web/world-field.js.
 * This module owns only the exact, typed 11-dial navigation grammar.
 * 11-position tuning = vertical position; 11-position granularity = zoom sensitivity.
 * Neither dial is permission to cross worlds, start a stream or issue a compute job.
 */
export const SCHEMA='static-os.mandelbrot-world-field/v0.1';
export const RADIX=11;
export const MAX_PATH=96;
export const RENDER_DEPTH_LIMIT=12;
export const START={tuning:6,granularity:6,path:[]};
const exact=(value,names)=>value&&typeof value==='object'&&!Array.isArray(value)
  && Object.keys(value).sort().join('|')===names.slice().sort().join('|');
const assert=(yes,why)=>{if(!yes)throw new TypeError(why)};
const dial=v=>Number.isSafeInteger(v)&&v>=1&&v<=11;
const segment=v=>exact(v,['t','g'])&&dial(v.t)&&dial(v.g);
const clone=s=>({schema:SCHEMA,tuning:s.tuning,granularity:s.granularity,path:s.path.map(x=>({...x}))});

export function createField(){
  return {schema:SCHEMA,...structuredClone(START)};
}
export function validateField(value){
  assert(exact(value,['schema','tuning','granularity','path']),'FIELD_SHAPE');
  assert(value.schema===SCHEMA,'FIELD_SCHEMA');
  assert(dial(value.tuning)&&dial(value.granularity),'DIAL_OUT_OF_RANGE');
  assert(Array.isArray(value.path)&&value.path.length<=MAX_PATH,'ADDRESS_DEPTH_EXCEEDED');
  assert(value.path.every(segment),'INVALID_NESTED_DIAL');
  return value;
}
export function turn(value,axis,delta){
  validateField(value);
  assert(axis==='tuning'||axis==='granularity','INVALID_DIAL_AXIS');
  assert(Number.isSafeInteger(delta)&&Math.abs(delta)<=11,'INVALID_STEP');
  const next=clone(value);
  next[axis]=Math.max(1,Math.min(11,next[axis]+delta));
  return next;
}
export function setDial(value,axis,position){
  validateField(value);
  assert(axis==='tuning'||axis==='granularity','INVALID_DIAL_AXIS');
  assert(dial(position),'DIAL_OUT_OF_RANGE');
  const next=clone(value);next[axis]=position;return next;
}
export function enter(value){
  validateField(value);
  assert(value.path.length<MAX_PATH,'ADDRESS_DEPTH_EXCEEDED');
  const next=clone(value);
  next.path.push({t:value.tuning,g:value.granularity});
  next.tuning=6;next.granularity=6;
  return next;
}
export function rise(value){
  validateField(value);
  if(!value.path.length)return clone(value);
  const next=clone(value);
  const previous=next.path.pop();
  next.tuning=previous.t;next.granularity=previous.g;
  return next;
}
export function address(value){
  validateField(value);
  // Exact base-11 dial address: both past nesting and current live dial settings.
  return 'MWF1/'+[...value.path,{t:value.tuning,g:value.granularity}]
    .map(({t,g})=>'t'+String(t).padStart(2,'0')+'g'+String(g).padStart(2,'0')).join('/');
}
export function restoreAddress(raw){
  assert(typeof raw==='string'&&raw.length<=8+MAX_PATH*7+8,'INVALID_ADDRESS_LENGTH');
  const pieces=raw.split('/');
  assert(pieces[0]==='MWF1'&&pieces.length>=2&&pieces.length<=MAX_PATH+2,'ADDRESS_VERSION_OR_DEPTH');
  const all=pieces.slice(1).map(part=>{
    assert(/^t(0[1-9]|1[01])g(0[1-9]|1[01])$/.test(part),'ADDRESS_DIGIT_INVALID');
    return {t:Number(part.slice(1,3)),g:Number(part.slice(4,6))};
  });
  const live=all.pop();
  return validateField({schema:SCHEMA,tuning:live.t,granularity:live.g,path:all});
}
export function exactCell(value,axis='tuning',includeDial=true){
  validateField(value);
  assert(axis==='tuning'||axis==='granularity','INVALID_DIAL_AXIS');
  assert(typeof includeDial==='boolean','INVALID_CELL_SCOPE');
  const key=axis==='tuning'?'t':'g';
  const digits=value.path.map(x=>x[key]-1);
  if(includeDial)digits.push(value[axis]-1);
  let n=0n,denominator=1n;
  for(const x of digits){n=n*11n+BigInt(x);denominator*=11n;}
  return {schema:'static-os.exact-eleven-cell/v0',axis,
    radix:11,positions:digits.map(v=>v+1),
    lowerNumerator:n.toString(),upperNumerator:(n+1n).toString(),
    denominator:denominator.toString(),
    // This is a rational interval; do not cast it to a float for provenance.
    exact:true};
}
export function compareCells(a,b){
  // For proving distinct near-identical deep addresses, never convert to floats.
  const x=BigInt(a.lowerNumerator),dx=BigInt(a.denominator);
  const y=BigInt(b.lowerNumerator),dy=BigInt(b.denominator);
  return x*dy<y*dx?-1:x*dy>y*dx?1:0;
}
export function worldState(value){
  validateField(value);
  return {schema:'static-os.mandelbrot-world-snapshot/v0.1',
    address:address(value),depth:value.path.length,
    tuning:value.tuning,granularity:value.granularity,
    tuningCell:exactCell(value,'tuning'),
    granularityCell:exactCell(value,'granularity'),
    navigation:'READ_ONLY',
    worldSourceAuthority:'NONE',
    mediaPlayback:false,streamSelected:false,
    crossingGranted:false,remoteCompute:false,
    radioTransmission:false};
}
export function previewViewport(value){
  validateField(value);
  // Pure deterministic float viewport. Exact positioning source is exactCell,
  // not this finite-precision approximation. Deep preview refuses to render.
  let re=-0.743643887037151,im=0.13182590420533,span=3.4;
  for(const item of value.path){
    im+=(item.t-6)*span/11;
    span=(span/11)*Math.pow(2,(6-item.g)/5);
  }
  im+=(value.tuning-6)*span/11;
  span*=Math.pow(2,(6-value.granularity)/5);
  const able=value.path.length<=RENDER_DEPTH_LIMIT &&
    Number.isFinite(re)&&Number.isFinite(im)&&Number.isFinite(span) &&
    span>1e-13;
  return {schema:'static-os.mandelbrot-preview/v0',re,im,span,
    approximate:true,renderable:able,
    reason:able?null:'FLOAT_PRECISION_RENDER_LIMIT',
    depth:value.path.length,
    coordinateProof:'EXACT_CELL_IN_NAVIGATION_SNAPSHOT_NOT_FLOAT_VIEWPORT'};
}
