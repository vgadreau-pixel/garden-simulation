#!/usr/bin/env python3
"""Test : dans le même onglet, capturer été (déjà validée) puis printemps,
avec EXACTEMENT le même protocole que verify_onirique4 (pause+scrub+15 s).
Si été re-passe vert et printemps échoue encore, le problème est la SAISON
(printemps = jour 75 : heures de soleil/états différents ?)."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=4000')
time.sleep(2)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

for _ in range(60):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(5)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# 1) refaire ÉTÉ (contrôle positif)
ev('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(166 + 10/24)')
time.sleep(15)
print('controle ete:', ev('window.__jardin.clock.jours'))
shot('onirique_ete_ctrl.png')
# état saison + herbe
print('etat:', ev('JSON.stringify({saison:window.__jardin.clock.etat.saison, jours:window.__jardin.clock.jours})'))

# 2) printemps
ev('window.__jardin.clock.scrubTo(75 + 10/24)')
time.sleep(15)
print('printemps:', ev('window.__jardin.clock.jours'), ev('window.__jardin.clock.etat.saison'))
shot('onirique_printemps_ctrl.png')
print('FINI')
