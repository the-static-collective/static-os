/* Typed Static Live Radio World adapter: specific official link doors only.
 * Not live audio, no source scraping, no implication of broadcaster endorsement.
 */
import {address,validateField} from './mandelbrot-field.mjs';
const WORLDS=Object.freeze([
  Object.freeze({
    id:'kinship-radio',
    owner:'Kinship Radio',
    territory:'Minnesota, USA',
    source:'https://kinshipradio.org/main/',
    externalAuthority:'OWNER_HELD',
    streamRights:'NOT_ESTABLISHED',
    mediaMode:'OFFICIAL_LINK_ONLY'
  }),
  Object.freeze({
    id:'rock-impact',
    owner:'Rock Impact Makers',
    territory:'Nigeria',
    source:'https://rockimpactmakersglobal.org/',
    externalAuthority:'OWNER_HELD',
    streamRights:'NOT_ESTABLISHED',
    mediaMode:'OFFICIAL_LINK_ONLY'
  })
]);
export function radioWorldDoors(field){
  validateField(field);
  return {schema:'static-os.radio-world-doors/v0',
    atAddress:address(field),
    placement:'EXPLICIT_CATALOG_NOT_MANDELBROT_INFERENCE',
    contentRights:'NOT_ESTABLISHED',
    entries:WORLDS.map(x=>({...x})),
    playing:false,autoTune:false,stationAudiencesMerged:false,
    performedCrossing:false,sourceOwnerControl:'INDEPENDENT'};
}
export function chooseRadioDoor(field,id){
  validateField(field);
  const world=WORLDS.find(x=>x.id===id);
  if(!world)throw new TypeError('RADIO_WORLD_NOT_FOUND');
  return {schema:'static-os.radio-world-link-handoff/v0',
    atAddress:address(field),selected:id,href:world.source,
    intent:'USER_CLICK_OPENS_OFFICIAL_SOURCE',
    autoplay:false,played:false,licensed:false,
    localMediaCaptured:false,computeStarted:false,
    crossingsPerformed:0};
}
