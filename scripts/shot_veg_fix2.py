#!/usr/bin/env python3
"""Captures finales via la caméra FPS (basculée depuis l'orbital) :
   - vue dessus du jardin à 50 instances (été midi),
   - vue de DESSOUS du houppier (validation DoubleSide),
   - automne, hiver (arbre nu), remise en orbital."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

def cam(x, y, z, yaw, pitch):
    eval_js(f'''(() => {{
      const fps = window.__jardin.fps;
      fps.position.set({x}, {y}, {z});
      fps.yaw = {yaw}; fps.pitch = {pitch};
      fps.updateCamera();
    }})()''')

# Été midi
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(1)

# Basculer en mode FPS (comme un clic utilisateur)
eval_js('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.5)
print('mode:', eval_js('window.__jardin.modeCamera'))

# Vue 1 : dessus du jardin
cam(0, 6, 14, 'Math.PI', -0.6)
time.sleep(1.5)
shot('veg_fix_vue_dessus.png')

# Vue 2 : de dessous, dans le houppier du cerisier (-2.3, 1.7)
cam(-2.3, 0.9, 1.7, 0, 1.1)
time.sleep(1.5)
shot('veg_fix_vue_dessous.png')

# Automne (midi)
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2)
cam(-4, 1.7, 6, 0.2, 0.35)
time.sleep(1)
shot('veg_fix_automne.png')

# Hiver (midi) : caducs nus
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2)
shot('veg_fix_hiver.png')

# Retour orbital (état propre pour la suite)
eval_js('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.3)
print('mode final:', eval_js('window.__jardin.modeCamera'))
print('info:', eval_js('window.__jardinRenderInfo()'))
