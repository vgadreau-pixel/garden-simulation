#!/usr/bin/env python3
"""Faire pousser les 50 plantes jusqu'à maturité via setSpeed('mois') puis
   capturer les 3 saisons avec arbres adultes."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# Vitesse 1 mois/s : ~88 jours pour +0.88 maturité -> ~9 s réelles (à 30 j/s mesuré).
eval_js('window.__jardin.clock.setSpeed("mois")')
time.sleep(12)
eval_js('window.__jardin.clock.setSpeed("pause")')
print('maturites:', eval_js('''JSON.stringify(window.__jardin.instances.slice(0,5).map(i => ({id: i.plante.id, mat: +i.maturite.toFixed(2), stade: +(i.stade||0).toFixed(2), scale: +i.group.scale.x.toFixed(2)})))'''))
print('label:', eval_js('window.__jardin.clock.etat.label'))

# Été
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2)
print('stades été:', eval_js('''JSON.stringify(window.__jardin.instances.slice(0,3).map(i => ({id: i.plante.id, scale: +i.group.scale.x.toFixed(2), masse: i.dernierEtat?+i.dernierEtat.masseFoliaire.toFixed(2):null})))'''))
shot('veg_adulte_ete.png')

# Automne
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2)
shot('veg_adulte_automne.png')

# Hiver
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2)
shot('veg_adulte_hiver.png')
