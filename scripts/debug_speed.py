#!/usr/bin/env python3
# Pourquoi le time-lapse n'avance-t-il pas après les clics ? On reproduit la
# séquence exacte et on regarde speedId/jours avant et après.
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

def clic(x, y, bouton='left'):
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button=bouton, clickCount=1)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button=bouton, clickCount=1)

print('etat:', ev('JSON.stringify({speed: window.__jardin.clock.speedId, jours: window.__jardin.clock.jours})'))
# Le bouton mois existe-t-il ? où ?
vl = json.loads(ev('JSON.stringify([...document.querySelectorAll("#timebar .tbtn")].map(b=>({s:b.dataset.speed, txt:b.textContent, r:b.getBoundingClientRect().toJSON(), actif:b.classList.contains("active")})))'))
for b in vl: print('btn:', b['s'], b['txt'], 'actif:', b['actif'], 'pos:', round(b['r']['x']), round(b['r']['y']))
c = next(b for b in vl if b['s'] == 'mois')
clic(c['r']['x']+c['r']['width']/2, c['r']['y']+c['r']['height']/2)
time.sleep(0.3)
print('apres clic mois:', ev('JSON.stringify({speed: window.__jardin.clock.speedId, dps: window.__jardin.clock.daysPerSecond})'))
