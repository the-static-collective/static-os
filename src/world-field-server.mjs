/* Zero-dependency localhost development runner. Never proxies station media. */
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
const root=join(dirname(fileURLToPath(import.meta.url)),'..','web');
const assets=new Map([
  ['/',['index.html','text/html; charset=utf-8']],
  ['/world-field.js',['world-field.js','text/javascript; charset=utf-8']],
  ['/world-field.css',['world-field.css','text/css; charset=utf-8']],
  ['/sw.js',['sw.js','text/javascript; charset=utf-8']],
  ['/manifest.webmanifest',['manifest.webmanifest','application/manifest+json']],
  ['/icon.svg',['icon.svg','image/svg+xml']],
  ['/model.js',[null,null]]
]);
const headers={'cache-control':'no-store','referrer-policy':'no-referrer',
  'x-content-type-options':'nosniff','x-frame-options':'DENY',
  'content-security-policy':"default-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; worker-src 'self'; media-src 'none'; object-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'"};
export function createFieldServer({host='127.0.0.1',port=0}={}){
  if(host!=='127.0.0.1')throw new TypeError('LOOPBACK_ONLY');
  if(!Number.isInteger(port)||port<0||port>65535)throw new TypeError('PORT_INVALID');
  const server=createServer((req,res)=>{
    const path=new URL(req.url||'/', 'http://127.0.0.1').pathname;
    const respond=(code,body,type='text/plain; charset=utf-8')=>{
      res.writeHead(code,{...headers,'content-type':type,'content-length':Buffer.byteLength(body)});
      res.end(req.method==='HEAD'?undefined:body);
    };
    if(!['GET','HEAD'].includes(req.method))return respond(405,'READ_ONLY');
    let item=assets.get(path);
    if(path==='/src/mandelbrot-field.mjs')item=['../src/mandelbrot-field.mjs','text/javascript; charset=utf-8'];
    if(path==='/src/radio-world-adapter.mjs')item=['../src/radio-world-adapter.mjs','text/javascript; charset=utf-8'];
    if(!item||!item[0])return respond(404,'NO_SUCH_DOOR');
    // Whitelist prevents directory traversal, arbitrary file access and URL relay.
    return respond(200,readFileSync(join(root,item[0])),item[1]);
  });
  let listening=false;
  return {
    async start(){
      if(listening)throw new Error('ALREADY_STARTED');
      await new Promise((resolve,reject)=>{
        server.once('error',reject);
        server.listen(port,host,()=>{server.off('error',reject);resolve()});
      });
      listening=true;
      const a=server.address();
      return {host,port:a.port,url:'http://127.0.0.1:'+a.port+'/'};
    },
    async stop(){
      if(!listening)return;
      await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));
      listening=false;
    }
  };
}
const isCli=process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1];
if(isCli){
  const server=createFieldServer({port:Number(process.env.MWF_PORT||8790)});
  server.start().then(x=>console.log('MANDELBROT WORLD FIELD 001 / '+x.url))
    .catch(e=>{console.error('HOLD:',e.message);process.exitCode=1});
}
