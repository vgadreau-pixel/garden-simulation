#!/usr/bin/env python3
"""Capture finale v3 : tout-en-un.
La boucle tourne (x1 temps réel). Saison via scrubTo() qui est la voie publique.
On change la vitesse par setSpeed. Vérifier à CHAQUE étape que jours bouge.
Screenshots après contrôle caméra complet."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)
ws.call('Page.navigate', url='about:blank')
time.sleep(1)
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=18000')
time.sleep(2)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

for _ in range(50):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(3)

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def v_key():
    key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp'); time.sleep(0.5)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# setSpeed pause pour figer le temps ; scrubTo pour changer la date
print('setSpeed pause:', ev('window.__jardin.clock.setSpeed("pause")'))
j = ev('window.__jardin.clock.jours')
print('jours actuels:', j)

def set_date(jour, heure):
    # scrubTo accepte 0..365 (jour de l'année). jour + heure/24
    ev(f'window.__jardin.clock.scrubTo({jour} + {heure}/24)')
    return ev('window.__jardin.clock.jours')

print('scrub ete 10h ->', set_date(166, 10.0))
v_key()
print('mode:', ev('window.__jardin.modeCamera'))
ev('window.__jardin.fps.position.set(-14,1.7,17.5); window.__jardin.fps.yaw=2.35; window.__jardin.fps.pitch=0.06; window.__jardin.fps.updateCamera()')
time.sleep(1.5)
print('cam:', ev('JSON.stringify([+window.__jardin.fpsCamera.position.x.toFixed(1), +window.__jardin.fpsCamera.position.y.toFixed(1), +window.__jardin.fpsCamera.position.z.toFixed(1)])'))
shot('onirique_ete_fps.png')

# Changer la date EN MODE FPS, sans bouger la caméra
print('scrub hiver ->', set_date(15, 10.0))
time.sleep(1.5)
shot('onirique_hiver_fps.png')
print('scrub printemps ->', set_date(75, 10.0))
time.sleep(1.5)
shot('onirique_printemps_fps.png')
print('scrub automne ->', set_date(258, 10.0))
time.sleep(1.5)
shot('onirique_automne_fps.png')
# Golden hour (été 18h45)
print('scrub golden ->', set_date(166, 18.75))
ev('window.__jardin.fps.yaw=2.9; window.__jardin.fps.updateCamera()')
time.sleep(1.5)
shot('onirique_ete_golden_fps.png')
# Nuit d'été (22h30) — lucioles
print('scrub nuit ->', set_date(166, 22.5))
ev('window.__jardin.fps.yaw=2.35; window.__jardin.fps.updateCamera()')
time.sleep(2.0)
print('lucioles:', ev('window.__jardin.onirique.infos.particules.lucioles.points.visible'))
print('opacite lucioles:', ev('window.__jardin.onirique.infos.particules.lucioles.mat.uniforms.uOpacite.value'))
shot('onirique_ete_nuit_fps.png')
print('FINI')
