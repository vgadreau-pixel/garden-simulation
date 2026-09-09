#!/usr/bin/env python3
"""Captures printemps + automne en vue FPS, avec vérification pixel immédiate.
Protocole : navigation fraîche ?herbe=4000, V→FPS, scrub → attente → 2 shots
espacés (identiques = frame gelée → on force un rendu)."""
import json, time, sys, os, base64, urllib.request, hashlib
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
time.sleep(6)

def key(code, vk):
    ws.call('Input.dispatchKeyEvent', type='keyDown', code=code, key=code[-1].lower(),
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
    time.sleep(0.05)
    ws.call('Input.dispatchKeyEvent', type='keyUp', code=code, key=code[-1].lower(),
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    return hashlib.md5(open(os.path.join(P, nom), 'rb').read()).hexdigest()[:10]

def frame_hash():
    return ev('(()=>{const c=document.querySelector("canvas"); return c ? c.toDataURL("image/png").length : 0})()')

# Activer le mode FPS
key('KeyV', 86)
time.sleep(1.5)
print('mode:', ev('window.__jardin.modeCamera'))

resultats = {}
for jour, heure, nom in [(105, 10.0, 'onirique_printemps_fps'), (258, 10.0, 'onirique_automne_fps')]:
    ev(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({jour} + {heure}/24)')
    time.sleep(10)
    print(nom, '| jours =', round(ev('window.__jardin.clock.jours'), 2),
          '| saison =', ev('window.__jardin.clock.etat.saison'),
          '| mode =', ev('window.__jardin.modeCamera'))
    h1 = shot(nom + '.png')
    time.sleep(1)
    h2 = shot(nom + '_ctrl.png')
    print(f'  md5 {h1} / ctrl {h2} → distincts: {h1 != h2} | frame canvas len: {frame_hash()}')
    resultats[nom] = (h1, h2)

# Sanity : les 4 png doivent être 2 à 2 différents (printemps vs automne)
import numpy as np
from PIL import Image
def arr(f): return np.asarray(Image.open(os.path.join(P, f)).convert('RGB'), dtype=np.int16)
a, b = arr('onirique_printemps_fps.png'), arr('onirique_automne_fps.png')
d = float(np.abs(a - b).mean())
frac = float((np.abs(a - b).max(axis=2) > 20).mean()) * 100
print(f'PRINT vs AUTOMNE: diff moyenne {d:.2f} | % pixels distincts {frac:.1f}%')
print('VERDICT:', 'OK saisons distinctes' if d > 2 and frac > 1 else 'ÉCHEC : encore identiques')
