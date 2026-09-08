#!/usr/bin/env python3
"""Une seule capture : AUTOMNE en réutilisant l'onglet ÉTÉ (hash f677...)
comme point de départ. Protocole EXACT de la capture golden qui a marché :
1. navigation fraîche ?herbe=4000
2. scrub 258+10/24 + pause
3. V (clavier), position caméra
4. attente 15 s
5. capture
Puis vision GLM. Si encore 'grille 2D', on rapprochera du fait que
l'onglet oscille : comparer les METRIQUES de hauteur du soleil (été 10h vs
automne 10h : plus bas → lumière plus rasante, ombres longues)."""
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

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

# scrub automne AVANT le mode FPS
ev('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(258 + 10/24)')
time.sleep(3)
key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp')
ev('window.__jardin.fps.position.set(-14,1.7,17.5); window.__jardin.fps.yaw=2.35; window.__jardin.fps.pitch=0.06; window.__jardin.fps.updateCamera()')
time.sleep(20)
print('état:', ev('JSON.stringify({mode:window.__jardin.modeCamera, jours:+window.__jardin.clock.jours.toFixed(1), saison:window.__jardin.clock.etat.saison})'))
shot('onirique_automne_v10.png')
