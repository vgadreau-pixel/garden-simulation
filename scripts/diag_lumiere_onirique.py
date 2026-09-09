#!/usr/bin/env python3
"""Debug lumiere : plusieurs frames, heures différentes, couleurs uniques.
Le scene_check montrait herbe+eau+particules ; ici on vérifie que la LUMIERE
change (palettes par heure) et on capture avec preserveDrawingBuffer forcé."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

for _ in range(40):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(2)

for heure, nom in [(10.0, 'dbg_10h'), (13.0, 'dbg_13h'), (22.0, 'dbg_22h')]:
    ev(f'window.__jardin.clock.jours = 166 + {heure}/24')
    time.sleep(2.0)
    etat = ev('JSON.stringify({s: window.__jardin.clock.etat.saison, h: +window.__jardin.clock.heure.toFixed(1), sun: {x:+window.__jardin.scene.children.find(o=>o.isDirectionalLight).position.x.toFixed(1), y:+window.__jardin.scene.children.find(o=>o.isDirectionalLight).position.y.toFixed(1), i:+window.__jardin.scene.children.find(o=>o.isDirectionalLight).intensity.toFixed(2)}, hemi:+window.__jardin.scene.children.find(o=>o.isHemisphereLight).intensity.toFixed(2), expo:+ (window.__jardin.scene.renderer ? 0 : 0)})')
    print(nom, etat)
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom + '.png'), 'wb').write(base64.b64decode(s['data']))
