#!/usr/bin/env python3
"""Le render loop tourne-t-il ? Compter les frames rendues sur 3 secondes
via un hook sur requestAnimationFrame + vérifier clock.tick.
Hypothèse principale : la page est en ARRIERE-PLAN (onglet caché) → rAF
suspendu → render() ne tourne jamais → screenshot = dernier état figé."""
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
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

for _ in range(40):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)

print('visibility:', ev('document.visibilityState'))
print('hasFocus:', ev('document.hasFocus()'))
ev('window.__frames=0; const oldRAF=window.requestAnimationFrame; window.requestAnimationFrame=(cb)=>oldRAF((t)=>{window.__frames++;cb(t)})')
time.sleep(3)
print('frames en 3s:', ev('window.__frames'))
print('hud fps:', ev('document.getElementById("fps")?.textContent'))
# Timestamp de la dernière frame WebGL? Comparons plutôt via renderer.info (autoReset true en boucle)
print('info frame:', ev('JSON.stringify({calls:(()=>{const i=window.__jardinRenderInfo();return i.calls})()})' if False else 'n/a'))
