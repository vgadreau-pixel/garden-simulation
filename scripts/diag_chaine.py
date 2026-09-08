#!/usr/bin/env python3
"""Debug position monde du groupe veg (les positions d'instance sont bonnes :
   cerisier en -2.3,-2.3 mais ses meshes en 14.5). Où est le décalage ?
   Hypothèse : group.add(cl) ajoute le clone à l'instance, mais inst.group
   est peut-être lui-même enfant d'un group parent décalé, ou le clone a un
   transform propre hérité du template (racine.position modifiée ensuite ?)."""
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
print(ev('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.plante.id==="cerisier");
  const g = i.group; const veg = i.veg.groupe;
  // remonter la hiérarchie du veg groupe
  let chain=[]; let o=veg;
  while(o){ chain.push({type:o.type, name:o.name, pos:o.position.toArray().map(v=>+v.toFixed(2)), scale:o.scale.toArray().map(v=>+v.toFixed(2)), quat:o.quaternion.toArray().map(v=>+v.toFixed(2))}); o=o.parent; }
  return JSON.stringify(chain);
})()'''))
