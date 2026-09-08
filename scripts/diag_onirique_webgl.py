#!/usr/bin/env python3
"""Diag 3 : sur le Chrome headless 9335, y a-t-il WebGL ? __jardin ? Plusieurs pages ?"""
import json, time, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
print('pages:', [(t['type'], t['url'][:60]) for t in tabs])
pages = [t for t in tabs if t['type'] == 'page']
# Ouvrir notre propre onglet propre
ws = WS(pages[0]['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Page.navigate', url='about:blank')
time.sleep(1)
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=6000')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return 'EXC: ' + r['exceptionDetails']['exception']['description'][:200]
    return r['result'].get('value')

for _ in range(40):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(2)
print('jardin:', ev('typeof window.__jardin === "object"'))
print('webgl:', ev('(()=>{const c=document.createElement("canvas");const g=c.getContext("webgl2")||c.getContext("webgl");return g?g.getParameter(g.RENDERER):"AUCUN"})()'))
print('renderInfo:', ev('JSON.stringify(window.__jardinRenderInfo ? window.__jardinRenderInfo() : "absent")'))
print('scene enfants:', ev('JSON.stringify(window.__jardin.scene.children.map(o=>o.type+":"+ (o.name||"") ).slice(0,20))'))
