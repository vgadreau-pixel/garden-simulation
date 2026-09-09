#!/usr/bin/env python3
"""Test décisif : que rend la scene vue par fpsCamera ?
Calcule les bounding boxes projetées: si fpsCamera voit la grille du terrain
depuis 1.7m, le rendu DOM devrait montrer l'horizon. On vérifie aussi si
updateCamera() modifie réellement la matrice (matrixWorldNeedsUpdate=true
signifie qu'un updateMatrixWorld n'a PAS encore été fait après notre set)."""
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

# Forcer la caméra, puis rendre explicitement le composer avec fpsCamera et
# capturer via toDataURL IMMÉDIATEMENT dans le même tick (avant swap).
expr = '''(async()=>{
  const j = window.__jardin;
  j.fps.position.set(-14, 1.7, 17.5);
  j.fps.yaw = 2.35; j.fps.pitch = 0.06;
  j.fps.updateCamera();
  j.fpsCamera.updateMatrixWorld(true);
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  return JSON.stringify({
    matrixWorldNeedsUpdate: j.fpsCamera.matrixWorldNeedsUpdate,
    matrixWorld: j.fpsCamera.matrixWorld.elements.slice(12,15).map(v=>+v.toFixed(2)),
  });
})()'''
print('matrice:', ev(expr))
