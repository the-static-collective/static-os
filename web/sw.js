/* First-party offline shell only; no audio, feeds, recordings or requests across origin. */
const CACHE='static-os-mandelbrot-world-field-001-v1';
const SHELL=['/','/world-field.js','/world-field.css','/icon.svg','/manifest.webmanifest',
  '/src/mandelbrot-field.mjs','/src/mandelbrot-math.mjs','/src/radio-world-adapter.mjs'];
self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(
    keys.filter(k=>k.startsWith('static-os-mandelbrot-world-field-')&&k!==CACHE)
    .map(k=>caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin||!SHELL.includes(url.pathname)||url.search)return;
  e.respondWith(fetch(e.request).then(r=>{
    if(r.ok){const snapshot=r.clone();caches.open(CACHE).then(c=>c.put(e.request,snapshot));}
    return r;
  }).catch(()=>caches.match(e.request)));
});
