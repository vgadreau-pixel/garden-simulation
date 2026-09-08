#!/usr/bin/env python3
"""Étape état : vérifier masseFoliaire/couleur des instances après scrub hiver,
   et stades de croissance (les plantations récentes sont peut-être des graines)."""
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

# État courant (hiver scrub à 15.5)
print('état global hiver:', eval_js('''JSON.stringify(window.__jardin.instances.slice(0,5).map(i => ({
  id: i.plante.id,
  stade: +(i.stade||0).toFixed(2),
  masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null,
  c: i.dernierEtat ? "#"+i.dernierEtat.couleur.getHexString() : null,
  veg: !!i.vegActif,
  scale: +i.group.scale.x.toFixed(3)
})))'''))
print('date:', eval_js('window.__jardin.clock.etat.label'))
# Age des plantations
print('ages:', eval_js('''JSON.stringify(window.__jardin.instances.slice(0,5).map(i => ({id: i.plante.id, ageJ: i.ageJours !== undefined ? +i.ageJours.toFixed(0) : (i.datePlantation ? "?" : "?")})))'''))
