#!/usr/bin/env python3
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
def ev(e):
    r = ws.call('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True)
    return ('EXC', str(r.get('exceptionDetails'))[:200]) if r.get('exceptionDetails') else r['result'].get('value')
print('label courant:', ev('window.__jardin.clock.etat.label'))
print('cerisier:', ev('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.plante.id==="cerisier");return JSON.stringify({m:i.dernierEtat.masseFoliaire.toFixed(2), s:i.group.scale.x.toFixed(2), veg: !!i.vegActif, leafMeshes: i.veg?i.veg.leafMeshes.length:0, leafScaleX: i.veg&&i.veg.leafMeshes[0]? i.veg.leafMeshes[0].mesh.scale.x.toExponential(2):null})})()'''))
