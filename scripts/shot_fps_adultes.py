#!/usr/bin/env python3
"""Vue FPS au niveau du sol : 3 captures (été, automne, hiver) au cœur du jardin."""
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

# Passer en mode FPS
eval_js('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.4)
print('mode:', eval_js('window.__jardin.modeCamera'))

def cam(x, y, z, yaw, pitch):
    eval_js(f'''(() => {{
      const fps = window.__jardin.fps;
      fps.position.set({x}, {y}, {z});
      fps.yaw = {yaw}; fps.pitch = {pitch};
      fps.updateCamera();
    }})()''')

# Été d'abord
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2)
print('masse cerisier été:', eval_js('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.plante.id==="cerisier");return JSON.stringify({m:i.dernierEtat.masseFoliaire.toFixed(2), leafScaleX: i.veg.leafMeshes[0].mesh.scale.x.toExponential(2)})})()'''))
# Position dans l'allée centrale regardant le cerisier adulte (-2.3, h~5, -2.3)
cam(-2.3, 1.7, 3.5, 0, 0.5)
time.sleep(1.5)
shot('fps_adulte_ete.png')
# Dessous houppier
cam(-2.3, 1.2, -0.5, 0, 1.15)
time.sleep(1.5)
shot('fps_adulte_dessous.png')

# Automne
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2.5)
cam(-2.3, 1.7, 3.5, 0, 0.5)
time.sleep(1)
shot('fps_adulte_automne.png')

# Hiver
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2.5)
cam(-2.3, 1.7, 3.5, 0, 0.4)
time.sleep(1)
shot('fps_adulte_hiver.png')

# Retour orbital
eval_js('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.3)
print('mode final:', eval_js('window.__jardin.modeCamera'))
