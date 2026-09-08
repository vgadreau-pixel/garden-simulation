#!/usr/bin/env python3
"""Diagnostic rendu : les meshes feuilles existent-ils dans la scène avec une
   bounding sphere correcte ? Sont-ils dans le frustum de la caméra FPS ?"""
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
def ev(e):
    r = ws.call('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True)
    return ('EXC', str(r.get('exceptionDetails'))[:400]) if r.get('exceptionDetails') else r['result'].get('value')

print('label:', ev('window.__jardin.clock.etat.label'))
print('cerisier groupe:', ev('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.plante.id==="cerisier");
  const g = i.veg.groupe;
  let infos = [];
  g.traverse(o=>{ if(o.isMesh) infos.push({mat: o.material.name, vis: o.visible, fc: o.frustumCulled, side: o.material.side, scale: +o.scale.x.toPrecision(3), pos: o.getWorldPosition(new (o.position.constructor)()).toArray().map(v=>+v.toFixed(1)) }); });
  return JSON.stringify({groupeVisible: g.visible, echelleGroupe: +g.scale.x.toPrecision(3), echelleParent: +i.group.scale.x.toPrecision(3), posGroupe: g.getWorldPosition(new (g.position.constructor)()).toArray().map(v=>+v.toFixed(1)), meshes: infos.slice(0,4)});
})()'''))
