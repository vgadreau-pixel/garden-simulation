#!/usr/bin/env python3
"""Diagnostic direct dans la page : octets HDRI vus par le navigateur + erreur complète."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

JS1 = """(async()=>{
  const r = await fetch('/hdri/kloppenheim_02_1k.hdr?cb='+Date.now());
  const b = new Uint8Array(await r.arrayBuffer());
  const head = Array.from(b.subarray(0,16)).map(x=>x.toString(16).padStart(2,'0')).join(' ');
  return 'status='+r.status+' len='+b.byteLength+' head='+head;
})()"""

JS2 = """(async()=>{
  const THREE = await import('three');
  const {RGBELoader} = await import('three/addons/loaders/RGBELoader.js');
  return new Promise(res=>{
    new RGBELoader().load('/hdri/kloppenheim_02_1k.hdr?cb='+Date.now(),
      t=>{window.__jardin.scene.environment=t; t.mapping=THREE.EquirectangularReflectionMapping; res('OK type='+t.type+' '+t.image.width+'x'+t.image.height)},
      undefined,
      e=>res('ERR: '+(e&&e.message||e)));
  });
})()"""

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:500])
        return r['result'].get('value')

    print('fetch_frais:', eval_js(JS1))
    print('rgbeloader_retry:', eval_js(JS2))
    time.sleep(1)
    print('env_apres:', eval_js('!!window.__jardin.scene.environment'))

if __name__ == '__main__':
    main()
