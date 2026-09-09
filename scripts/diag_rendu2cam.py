#!/usr/bin/env python3
"""Test rendu des 2 caméras sur canvas : orbital vs FPS — quelle caméra produit quoi ?"""
import json, time, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

# 1) Avec le composer (chemin de rendu normal, caméra selon mode)
print('mode:', ev('window.__jardin.modeCamera'))
print('fpsCam_pos:', ev('window.__jardin.fpsCamera.position.toArray().map(v=>+v.toFixed(2))'))
print('fpsCam_update:', ev('typeof window.__jardin.fps.updateCamera'))
# Forcer update caméra FPS puis rendre via composer avec fpsCamera, lire pixel central
expr = '''(async()=>{
  const j = window.__jardin;
  j.fps.updateCamera ? j.fps.updateCamera() : null;
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const c = document.getElementById('app');
  const gl = c.getContext('webgl2')||c.getContext('webgl');
  const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
  const px = new Uint8Array(4);
  gl.readPixels(w>>1, h>>1, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  const pxHaut = new Uint8Array(4);
  gl.readPixels(w>>1, Math.floor(h*0.8), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pxHaut);
  return JSON.stringify({centre:[...px], haut:[...pxHaut], fpsCamY:j.fpsCamera.position.y});
})()'''
print('pixels:', ev(expr))
