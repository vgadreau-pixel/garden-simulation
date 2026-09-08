#!/usr/bin/env python3
"""Après reload : état du jardin, position des instances, debug du décalage."""
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
print('nb instances:', ev('window.__jardin ? window.__jardin.jardin.instances.length : "pas chargé"'))
print('positions (5):', ev('''JSON.stringify(window.__jardin.jardin.instances.slice(0,5).map(i=>({id:i.plante.id, parcelle:i.parcelle, pos:i.group.position.toArray().map(v=>+v.toFixed(1))})))'''))
print('cerisier veg:', ev('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.plante.id==="cerisier");
  if(!i||!i.veg) return "pas de veg";
  let o={}; i.veg.groupe.traverse(m=>{if(m.isMesh){o[m.material.name]={localPos:m.position.toArray().map(v=>+v.toFixed(1)), worldPos:m.getWorldPosition(new (m.position.constructor)()).toArray().map(v=>+v.toFixed(1))};}});
  return JSON.stringify(o);})()'''))
