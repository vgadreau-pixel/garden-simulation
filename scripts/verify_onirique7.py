#!/usr/bin/env python3
"""Capture printemps/automne v7 : navigateur FRAIS, on passe en FPS dès le
départ, on scrub APRÈS être en FPS, attente large. Une seule saison par
navigation pour éviter tout état résiduel."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

def run_saison(jour, nom):
    ws.call('Page.navigate', url=f'http://[::1]:4183/?herbe=4000&saison={jour}')
    time.sleep(3)
    for _ in range(50):
        if ev('typeof window.__jardin === "object"') is True: break
        time.sleep(1.5)
    ev(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({jour} + 10/24)')
    key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp')
    ev('window.__jardin.fps.position.set(-14,1.7,17.5); window.__jardin.fps.yaw=2.35; window.__jardin.fps.pitch=0.06; window.__jardin.fps.updateCamera()')
    time.sleep(25)  # très large : ≥ 5 frames lentes
    print(nom, 'mode:', ev('window.__jardin.modeCamera'), 'jours:', ev('window.__jardin.clock.jours'))
    shot(nom + '.png')

run_saison(75, 'onirique_printemps_fps')
run_saison(258, 'onirique_automne_fps')
print('FINI')
