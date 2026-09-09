#!/usr/bin/env python3
"""Test vitesse rendu + mesure: combien de temps prend un composer.render() ?
Si SwiftShader met 3-5 s par frame, la capture CDP (qui rate le moment du
swap) reste identique. On rend 3 fois et on chronomètre."""
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

# Chronométrer un render hors boucle (interrompt l'affichage 1 instant)
print('chrono_render:', ev('''(async()=>{
  const j = window.__jardin;
  j.fps.position.set(-14,1.7,17.5); j.fps.yaw=2.35; j.fps.pitch=0.06; j.fps.updateCamera();
  const t0 = performance.now();
  // accéder au composer via __jardinRenderInfo (il rend une fois)
  const info = window.__jardinRenderInfo();
  const dt = performance.now() - t0;
  return JSON.stringify({ms:+dt.toFixed(0), calls:info.calls, tris:info.triangles});
})()'''))
