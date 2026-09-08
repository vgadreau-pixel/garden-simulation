#!/usr/bin/env python3
"""Compléter automne + hiver après le crash CDP (la page est déjà en bon état)."""
import json, time, sys, os, base64
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(e):
    r = ws.call('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True)
    return ('EXC', str(r.get('exceptionDetails'))[:200]) if r.get('exceptionDetails') else r['result'].get('value')

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

def cam(x, y, z, yaw, pitch):
    ev(f'''(() => {{
      const fps = window.__jardin.fps;
      fps.position.set({x}, {y}, {z});
      fps.yaw = {yaw}; fps.pitch = {pitch};
      fps.updateCamera();
    }})()''')

print('mode:', ev('window.__jardin.modeCamera'))
print('instances:', ev('window.__jardin.jardin.instances.length'))

# Remettre en FPS (le crash a peut-être interrompu avant la bascule inverse)
ev('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.4)

# Automne
ev('window.__jardin.clock.scrubTo(289.5)')
time.sleep(3)
cam(-2.3, 1.7, 3.5, 0, 0.45)
time.sleep(1.5)
shot('fix2_automne.png')

# Hiver
ev('window.__jardin.clock.scrubTo(15.5)')
time.sleep(3)
cam(-2.3, 1.7, 3.5, 0, 0.4)
time.sleep(1.5)
shot('fix2_hiver.png')

print('info:', ev('window.__jardinRenderInfo()'))
ev('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
print('mode final:', ev('window.__jardin.modeCamera'))
