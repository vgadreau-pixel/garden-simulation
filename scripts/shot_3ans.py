#!/usr/bin/env python3
"""Avancer le temps de 3 ans (time-lapse) pour que les 50 plantations atteignent
   un stade adulte, puis refaire les captures saisonnières (été/automne/hiver)."""
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

# scrubTo attend des jours depuis le 1er janv. an 1 ? Été = 197.5 => ~197 jours.
# 3 ans plus tard : 197.5 + 3*365 = 1292.5 ; automne 289.5+1095=1384.5 ; hiver 15.5+1095=1110.5
print('avant:', eval_js('window.__jardin.clock.etat.label'))
eval_js('window.__jardin.clock.scrubTo(1292.5)')  # été, 3 ans plus tard
time.sleep(3)
print('label:', eval_js('window.__jardin.clock.etat.label'))
print('stades:', eval_js('''JSON.stringify(window.__jardin.instances.slice(0,4).map(i => ({id: i.plante.id, stade: +(i.stade||0).toFixed(2), scale: +i.group.scale.x.toFixed(2)})))'''))

# zoom orbitale conservé ; capturer
time.sleep(1)
shot('veg_final_ete_3ans.png')

# Automne
eval_js('window.__jardin.clock.scrubTo(1384.5)')
time.sleep(2.5)
print('label:', eval_js('window.__jardin.clock.etat.label'))
shot('veg_final_automne_3ans.png')

# Hiver
eval_js('window.__jardin.clock.scrubTo(1110.5)')
time.sleep(2.5)
print('label:', eval_js('window.__jardin.clock.etat.label'))
shot('veg_final_hiver_3ans.png')

print('etat hiver:', eval_js('''JSON.stringify(window.__jardin.instances.slice(0,5).map(i => ({id: i.plante.id, stade: +(i.stade||0).toFixed(2), masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null})))'''))
