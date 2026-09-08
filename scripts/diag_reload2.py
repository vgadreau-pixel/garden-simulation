#!/usr/bin/env python3
"""Reload + vérif recentrage (diagnostic)."""
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable')
def ev(e):
    r = ws.call('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True)
    return ('EXC', str(r.get('exceptionDetails'))[:400]) if r.get('exceptionDetails') else r['result'].get('value')
ws.call('Page.navigate', url='http://127.0.0.1:4183/?climat=oceanique')
time.sleep(6)
print('veg:', ev('''(()=>{ if(!window.__jardin) return "chargement";
  const i = window.__jardin.jardin.instances[0];
  return JSON.stringify({id: i.plante.id, veg: !!i.vegActif});})()'''))
time.sleep(4)
print('chaine:', ev('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.vegActif && x.plante.type==="arbre");
  if(!i) return "aucun arbre veg";
  let chain=[]; let o=i.veg.groupe;
  while(o && o.type!=="Scene"){ chain.push({name:o.name||o.type, pos:o.position.toArray().map(v=>+v.toFixed(2))}); o=o.parent; }
  return JSON.stringify(chain);
})()'''))
print('monde feuilles:', ev('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.vegActif && x.plante.type==="arbre");
  let o={}; i.veg.groupe.traverse(m=>{if(m.isMesh&&/Leaves|leaf/i.test(m.material.name)){o.pos=m.getWorldPosition(new (m.position.constructor)()).toArray().map(v=>+v.toFixed(1)); return true;}}); return JSON.stringify(o);})()'''))
