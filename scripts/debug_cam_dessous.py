#!/usr/bin/env python3
"""Debug cam : position fps avant/apres cam(), et pourquoi la cam ne bouge pas."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

ws.call('Page.bringToFront')
print('modeCamera:', eval_js('window.__jardin.modeCamera'))
print('fps.pos avant:', eval_js('JSON.stringify(window.__jardin.fps.position)'))
eval_js('''(() => {
  const fps = window.__jardin.fps;
  fps.position.set(-2.3, 0.9, 1.7);
  fps.yaw = 0; fps.pitch = 1.1;
  fps.updateCamera();
})()''')
time.sleep(1.5)
print('fps.pos apres:', eval_js('JSON.stringify(window.__jardin.fps.position)'))
print('camera.pos:', eval_js('JSON.stringify(window.__jardin.scene ? window.__jardin.scene.getObjectByName ? "n/a" : "n/a" : "n/a")'))
# La position de la vraie camera three :
print('cam three:', eval_js('''(() => {
  const c = window.__jardin.fpsCamera;
  return c ? JSON.stringify({p: c.position.toArray().map(v=>+v.toFixed(2))}) : 'pas de fpsCamera';
})()'''))
print('mode apres:', eval_js('window.__jardin.modeCamera'))
