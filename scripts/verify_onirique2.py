#!/usr/bin/env python3
"""Capture finale correcte : navigation fraîche dans le Chrome headless,
forcée en mode FPS AVANT la capture, controls.disabled=false sur orbital.
Les captures 'onirique_*' précédentes sont renommées .invalides."""
import json, time, sys, os, base64, math, urllib.request, shutil
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for f in os.listdir(P):
    if f.startswith('onirique_'):
        shutil.move(os.path.join(P, f), os.path.join(P, f + '.invalide'))
print('anciennes captures invalidées')

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)
ws.call('Page.navigate', url='about:blank')
time.sleep(1)
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=18000')

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

def set_saison(jour, heure):
    ev(f'window.__jardin.clock.jours = {jour} + {heure}/24')

def en_fps(pos, yaw, pitch):
    v_key()
    ev(f'window.__jardin.fps.position.set({pos[0]},1.7,{pos[1]}); window.__jardin.fps.yaw={yaw}; window.__jardin.fps.pitch={pitch}; window.__jardin.fps.updateCamera()')
    time.sleep(1.2)

# Contrôle : mode, position, direction caméra
print('avant:', ev('JSON.stringify({mode:window.__jardin.modeCamera, camPos:window.__jardin.fpsCamera.position.toArray().map(v=>+v.toFixed(1))})'))

PLANS = [
    # (saison, jour, heure, position (x,z), yaw, pitch, nom)
    ('printemps', 75, 10.0, (-14, 17.5), 2.35, 0.06, 'onirique_printemps_fps'),
    ('ete', 166, 10.0, (-14, 17.5), 2.35, 0.06, 'onirique_ete_fps'),
    ('automne', 258, 10.0, (-14, 17.5), 2.35, 0.06, 'onirique_automne_fps'),
    ('hiver', 15, 10.0, (-14, 17.5), 2.35, 0.06, 'onirique_hiver_fps'),
    ('ete', 166, 18.7, (-14, 17.5), 2.9, 0.04, 'onirique_ete_golden_fps'),
    ('ete', 166, 22.5, (-14, 17.5), 2.35, 0.06, 'onirique_ete_nuit_fps'),
]
for saison, jour, heure, pos, yaw, pitch, nom in PLANS:
    set_saison(jour, heure)
    time.sleep(1.8)
    en_fps(pos, yaw, pitch)
    st = ev('JSON.stringify({mode:window.__jardin.modeCamera, cam:[+window.__jardin.fpsCamera.position.x.toFixed(1),+window.__jardin.fpsCamera.position.y.toFixed(1),+window.__jardin.fpsCamera.position.z.toFixed(1)], dir:(()=>{const j=window.__jardin;const d={x:0,y:0,z:0};const m=j.fpsCamera.matrixWorld.elements;d.x=-m[8];d.y=-m[9];d.z=-m[10];return [d.x,d.y,d.z].map(v=>+v.toFixed(2))})()})')
    print(nom, st)
    shot(nom + '.png')
    v_key()
    time.sleep(0.5)

print('particules ete nuit:', ev('JSON.stringify({lucioles:window.__jardin.onirique.infos.particules.lucioles.points.visible})'))
print('FINI')
