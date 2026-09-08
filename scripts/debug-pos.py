#!/usr/bin/env python3
"""Diagnostic : positions des plantes vs terrain."""
import json, time, sys
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_44f07608/scripts')
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable')
time.sleep(1)
ws.call('Page.navigate', url='http://localhost:4173/')
time.sleep(4)
ws.drain(0.5)

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

print(eval_js('''
(() => {
  const inst = window.__jardin.instances;
  const pos = inst.slice(0,5).map(i => ({id: i.plante.id, p: [+i.group.position.x.toFixed(1), +i.group.position.z.toFixed(1)], s: +i.group.scale.x.toFixed(3), ech: i.echelleBase}));
  // terrain bbox
  let boxes = [];
  window.__jardin.scene.traverse(o => { if (o.isMesh && o.geometry && o.geometry.boundingSphere === null) o.geometry.computeBoundingSphere(); });
  const terrain = window.__jardin.scene.getObjectByName('terrain');
  return JSON.stringify({pos, terrainChildren: terrain ? terrain.children.length : null});
})()
'''))
