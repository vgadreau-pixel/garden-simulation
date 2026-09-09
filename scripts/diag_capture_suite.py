#!/usr/bin/env python3
"""Après diag_scene_cachee, la boucle a probablement re-rendu. Test définitif :
stopper la boucle (annuler les rAF) est impossible de l'extérieur — mais on peut
déclencher un renderer.render DIRECT via le contexte three exposé? Non exposé.

PLAN B : utiliser une capture CDP au format jpeg avec fromSurface=true par défaut,
mais avec 'captureBeyondViewport' false, ET surtout tester si Page.captureScreenshot
reflète le canvas : on cache la scène, on screenshot 2 FOIS de suite avec 50ms
d'écart, puis on restaure. Si les 2 screenshots post-cache sont identiques au
screenshot pré-cache => l'écran ne suit pas le canvas."""
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

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png', captureBeyondViewport=False)
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# 1. cacher et NE PAS laisser la boucle restaurer (on stocke la liste globalement)
ev('''window.__cache = []; window.__cacheOn=true;
window.__jardin.scene.traverse(o=>{ if(o!==window.__jardin.scene){ window.__cache.push([o,o.visible]); o.visible=false; }});''')
time.sleep(0.2)
shot('A_cache_t0.png')
time.sleep(0.8)
shot('B_cache_t800.png')
# 2. restaure
ev('window.__cacheOn=false; window.__cache.forEach(([o,v])=>o.visible=v);')
time.sleep(0.2)
shot('C_restaure.png')
print('hashes:')
import hashlib
for n in ('A_cache_t0.png','B_cache_t800.png','C_restaure.png'):
    p = os.path.join(P, n)
    print(' ', n, hashlib.md5(open(p,'rb').read()).hexdigest()[:12])
