#!/usr/bin/env python3
"""Capture comparée : rendu avec et sans UI (masquage DOM des panneaux),
puis analyse pixel pour déterminer si la vue 3D est derrière l'interface."""
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
        return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# Cacher toute l'UI DOM (panneaux, HUD, barre temps) : ne garder que le canvas
n = ev('''(()=>{let k=0; document.body.querySelectorAll('*').forEach(el=>{
  if(el.id!=='app' && el.tagName!=='CANVAS' && !el.contains(document.getElementById('app'))){
    const st=getComputedStyle(el);
    if(st.position==='fixed'||st.position==='absolute'){ el.dataset.cachedDisplay=el.style.display; el.style.display='none'; k++; }
  }}); return k})()''')
print('elements masques:', n)
time.sleep(2)
shot('diag_sans_ui.png')
# restaurer
ev('''(()=>{document.body.querySelectorAll('[data-cached-display]').forEach(el=>{el.style.display=el.dataset.cachedDisplay; delete el.dataset.cachedDisplay})})()''')
print('restaure')
