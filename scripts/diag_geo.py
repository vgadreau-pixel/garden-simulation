#!/usr/bin/env python3
"""Test rendu tronc : InstancedMesh ? Ou geometry vide (Billboard/LOD) ?"""
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    res = eval_js('''(() => {
  const J = window.__jardin;
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  const g = cer.veg.groupe;
  const infos = [];
  g.traverse(o => {
    if (!o.isMesh) return;
    const geo = o.geometry;
    infos.push({
      nom: o.material?.name || '?',
      type: geo.constructor.name,
      isInstanced: geo.isInstancedBufferGeometry === true || o.isInstancedMesh === true,
      nVertices: geo.attributes?.position ? geo.attributes.position.count : -1,
      position: [o.position.x, o.position.y, o.position.z].map(v=>+v.toFixed(1)),
      echelle: [o.scale.x, o.scale.y, o.scale.z].map(v=>+v.toFixed(2)),
      visible: o.visible,
    });
  });
  return JSON.stringify(infos.slice(0, 8));
})()''')
    print(json.dumps(json.loads(res), indent=1)[:2000])

if __name__ == '__main__':
    main()
