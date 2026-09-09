#!/usr/bin/env python3
"""Instrumentation directe de la boucle : injecter un compteur dans la closure
de setAnimationLoop n'est pas possible après coup. Solution : modifier
temporairement main.js pour exposer window.__frames++ dans la boucle, rebuild,
recharger. C'est lourd — d'abord, vérifier une hypothèse plus simple :
setAnimationLoop utilise un rAF sur le contexte XHR ? Non : three utilise
XRSession ou rAF standard. Le hook ci-dessus montre 0 rAF en 3s → le rAF est
bien mort OU la page est throttled en headless (rAF ne tourne pas sans
compositing actif). Headless=new+SwiftShader : rAF devrait tourner.
Test décisif : un rAF de test posé AVANT la navigation (via Page.addScriptToEvaluateOnNewDocument)."""
import json, time, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Page.addScriptToEvaluateOnNewDocument', source='''
window.__rafCount = 0;
const oldRaf = window.requestAnimationFrame.bind(window);
window.requestAnimationFrame = (cb) => oldRaf((t) => { window.__rafCount++; cb(t); });
window.__t0 = performance.now();
''')
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=6000')
time.sleep(15)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

c1 = ev('window.__rafCount')
time.sleep(3)
c2 = ev('window.__rafCount')
print(f'rafCount: {c1} -> {c2} (delta {c2 - c1} en 3 s)')
print('jardin chargé:', ev('typeof window.__jardin === "object"'))
print('hud:', ev('document.getElementById("fps")?.textContent'))
