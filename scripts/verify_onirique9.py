#!/usr/bin/env python3
"""Recapture printemps avec V->FPS dans le MÊME onglet que verify_onirique8
(on y est encore en orbital). Protocole : V, position caméra, attente 15 s,
puis shot. Ensuite la même chose pour automne."""
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

# on est en jour 75 (printemps), mode orbital → basculer en FPS
key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp')
ev('window.__jardin.fps.position.set(-14,1.7,17.5); window.__jardin.fps.yaw=2.35; window.__jardin.fps.pitch=0.06; window.__jardin.fps.updateCamera()')
time.sleep(18)
print('mode:', ev('window.__jardin.modeCamera'), '| jours:', ev('window.__jardin.clock.jours'))
shot('onirique_printemps_fps.png')

# automne
ev('window.__jardin.clock.scrubTo(258 + 10/24)')
time.sleep(18)
print('jours automne:', ev('window.__jardin.clock.jours'), ev('window.__jardin.clock.etat.saison'))
shot('onirique_automne_fps.png')
print('FINI')
