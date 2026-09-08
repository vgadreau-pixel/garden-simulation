#!/usr/bin/env python3
"""Test frustum culling : boundingSphere des géométries Quaternius est-elle
correcte ? (modèles en cm → scale ×400 : si boundingSphere absente, three la
calcule une fois puis le culling la garde en unités locales écrasées)"""
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
  const out = [];
  for (const rec of cer.veg.leafMeshes.slice(0, 3)) {
    const m = rec.mesh;
    const g = m.geometry;
    out.push({
      hasBS: !!g.boundingSphere,
      bsR: g.boundingSphere ? +g.boundingSphere.radius.toFixed(1) : null,
      bsCentre: g.boundingSphere ? [g.boundingSphere.center.x, g.boundingSphere.center.y, g.boundingSphere.center.z].map(v=>+v.toFixed(1)) : null,
      frustumCulled: m.frustumCulled,
      bboxMin: g.boundingBox ? [g.boundingBox.min.x, g.boundingBox.min.y, g.boundingBox.min.z].map(v=>+v.toFixed(0)) : null,
      bboxMax: g.boundingBox ? [g.boundingBox.max.x, g.boundingBox.max.y, g.boundingBox.max.z].map(v=>+v.toFixed(0)) : null,
    });
  }
  return JSON.stringify(out);
})()''')
    print('geometries feuilles:', res)

    # Tronc : même check
    tronc = eval_js('''(() => {
  const J = window.__jardin;
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  const g = cer.veg.groupe;
  const meshes = [];
  g.traverse(o => { if (o.isMesh && !/leaf/i.test(o.material?.name || '')) meshes.push(o); });
  const m = meshes[0];
  if (!m) return 'pas de tronc';
  return JSON.stringify({ nom: m.material?.name, bsR: m.geometry.boundingSphere ? +m.geometry.boundingSphere.radius.toFixed(1) : null,
    frustumCulled: m.frustumCulled, bboxMax: m.geometry.boundingBox ? m.geometry.boundingBox.max.y.toFixed(1) : null });
})()''')
    print('tronc:', tronc)

if __name__ == '__main__':
    main()
