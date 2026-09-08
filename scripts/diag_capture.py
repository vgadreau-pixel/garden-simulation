#!/usr/bin/env python3
"""Capture de contrôle : renderer.domElement.toDataURL (frame réelle du canvas)
vs Page.captureScreenshot, pour expliquer les captures grises."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:200])
    return r['result'].get('value')

for _ in range(40):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(2)

# 1) toDataURL du canvas WebGL (preserveDrawingBuffer=false → capture au moment du draw)
r = ws.call('Runtime.evaluate', returnByValue=False, expression='document.getElementById("app").toDataURL("image/png")')
dataurl = r['result'].get('value', '')
if dataurl.startswith('data:image'):
    b64 = dataurl.split(',', 1)[1]
    open(os.path.join(PREUVES, 'ctrl_todataurl.png'), 'wb').write(base64.b64decode(b64))
    print('ctrl_todataurl.png écrit,', len(b64) // 1024, 'Ko')
else:
    print('toDataURL vide/erreur:', str(dataurl)[:120])

# 2) Page.captureScreenshot classique
s = ws.call('Page.captureScreenshot', format='png')
open(os.path.join(PREUVES, 'ctrl_cdpshot.png'), 'wb').write(base64.b64decode(s['data']))
print('ctrl_cdpshot.png écrit,', len(s['data']) // 1024, 'Ko')

# 3) mode orbital actif ? on met la caméra FPS pour la vue subjective
r2 = ws.call('Runtime.evaluate', expression='''
  (()=>{const j=window.__jardin;
   const kdown=(code,vk)=>j.fps.enabled; 
   j.modeCamera; // lecture
   return null;})()
''')
print('ok')
