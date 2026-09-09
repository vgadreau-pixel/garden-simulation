#!/usr/bin/env python3
"""Le screenshot CDP capture-t-il le canvas WebGL du tout sous SwiftShader ?
Méthode décisive: remplir le canvas avec une couleur FLAT via un rendu d'une
scène vide (ou clearing), screenshotter, et vérifier si le screenshot reflète
le changement. Si le screenshot ne change JAMAIS => captureScreenshot est
décorrélé du canvas (problème d'outil, pas d'app)."""
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
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# Rendu avec fpsCamera SUPPRIMÉE de la scène? Non — test plus simple :
# rendre une frame où on cache TOUT sauf le fond (scene.background), via
# scene.visible=false? Three n'a pas scene.visible global pour le rendu...
# Alternative: masquer tous les enfants de la scène sauf le ciel.
expr = '''(async()=>{
  const j = window.__jardin;
  // Cacher tout (grille, plantes, herbe, eau) => rendu = fond + ciel seulement
  const cache = [];
  j.scene.traverse(o=>{ if(o!==j.scene){ cache.push([o, o.visible]); o.visible=false; } });
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  return cache.length;
})()'''
n = ev(expr)
print('objets masques:', n)
time.sleep(1)
shot('diag_scene_cachee.png')
