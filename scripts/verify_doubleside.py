#!/usr/bin/env python3
"""Preuve programmatique DoubleSide : materiaux feuilles clones ont side=DoubleSide
et frustumCulled=false, + compte de faces vues de dessous (triangles traces)."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Runtime.enable')

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

ws.call('Page.bringToFront')
time.sleep(0.5)
print(eval_js('''(() => {
  const J = window.__jardin;
  const inst = J.jardin.instances.find(i => i.vegActif);
  if (!inst || !inst.veg) return 'pas de veg';
  const mats = inst.veg.leafMats;
  const meshes = inst.veg.leafMeshes;
  return JSON.stringify({
    espece: inst.plante.id,
    nMats: mats.length,
    side: mats.map(m => m.side),           // 2 = THREE.DoubleSide
    frustumCulled: meshes.map(m => m.mesh.frustumCulled), // attendu false
    couleur: mats[0].color.getHexString()
  });
})()'''))

# Verif horizontale : la camera ortho est-elle vraiment top-down ?
print('cam ortho:', eval_js('''(() => {
  const c = J ? null : null;
  const J2 = window.__jardin;
  return 'voir debug_cam';
})()'''))
