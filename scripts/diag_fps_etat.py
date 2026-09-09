#!/usr/bin/env python3
"""Diagnostic final : état précis de la boucle de rendu.
- fpsCamera.matrixWorldInverse à jour ? projection OK ?
- Test : rendre UNE frame via la boucle elle-même (forcer rAF), screenshotter tout de suite.
- Comparer fpsCamera vs camera: quel objet la RenderPass utilise au moment du rendu ?
"""
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
        return ('EXC', str(r['exceptionDetails'])[:500])
    return r['result'].get('value')

# État FPS complet
print('fps_etat:', ev('''JSON.stringify({
 pos: window.__jardin.fps.position ? [...window.__jardin.fps.position].map(v=>+v.toFixed(2)) : null,
 yaw: window.__jardin.fps.yaw, pitch: window.__jardin.fps.pitch,
 actif: window.__jardin.fps.actif !== undefined ? window.__jardin.fps.actif : '?',
 keys: window.__jardin.fps.touche ? Object.fromEntries([...window.__jardin.fps.touche].map(k=>[k,1])) : undefined,
 camPos: [...window.__jardin.fpsCamera.position].map(v=>+v.toFixed(2)),
 camQuat: [...window.__jardin.fpsCamera.quaternion].map(v=>+v.toFixed(3)),
 camMatrixAutoUpdate: window.__jardin.fpsCamera.matrixAutoUpdate,
 camMatrixWorldNeedsUpdate: window.__jardin.fpsCamera.matrixWorldNeedsUpdate,
})'''))
