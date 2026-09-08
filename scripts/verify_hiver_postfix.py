#!/usr/bin/env python3
"""Verif programmatique hiver : echelle des meshes feuilles ~0 pour caducs."""
import json, time, os, base64, sys
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

# Hiver
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2.5)
print('label:', eval_js('window.__jardin.clock.etat.label'))
print('hiver:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.filter(i => ["cerisier","bouleau","pommier","erable_japonais"].includes(i.plante.id)).slice(0,6).map(i => ({
  id: i.plante.id,
  masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(3) : null,
  leafScales: (i.veg ? i.veg.leafMeshes : []).map(l => +l.mesh.scale.x.toFixed(4)),
  visible: i.veg ? i.veg.groupe.visible : null
})))'''))
print('persistants:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.filter(i => ["sapin","olivier","buis","romarin","lavande"].includes(i.plante.id)).slice(0,4).map(i => ({
  id: i.plante.id,
  masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(3) : null,
  leafScales: (i.veg ? i.veg.leafMeshes : []).map(l => +l.mesh.scale.x.toFixed(4))
})))'''))

# Retour ete pour laisser l'app dans un etat coherent
eval_js('window.__jardin.clock.scrubTo(197.5)')
