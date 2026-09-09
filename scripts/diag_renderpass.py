#!/usr/bin/env python3
"""Test contrasté : au LIEU de laisser la boucle rendre l'ortho par-dessus,
on compare le screenshot normal VS un screenshot pris pendant que la boucle
rend fpsCamera FORCÉ. On triche : on remplace la camera ortho par la fpsCamera
dans l'objet __jardin (camera = fpsCamera) pour voir si le rendu change.

But: déterminer si le problème vient du chemin de rendu (composer) ou de la
boucle (qqch réassigne renderPass.camera ou rend l'ortho après)."""
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

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# Vérifier qui est renderPass.camera pendant que la page tourne
print('renderCam:', ev('''(()=>{const j=window.__jardin; return JSON.stringify({
  mode: j.modeCamera,
  fpsCam: j.fpsCamera.type,
  orbCam: j.camera.type,
})})()'''))
