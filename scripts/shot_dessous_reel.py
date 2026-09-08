#!/usr/bin/env python3
"""Contre-plongee ponctuelle : ecrase la position de la camera ortho dans le
boucle de rendu (une fois), capture, puis restaure le comportement normal."""
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

ws.call('Page.bringToFront')

# Ete : midi
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2.5)

# Installer un hook rAF : la caméra ortho est réimposée par controls.update()
# seulement si needsUpdate ; on la déplace APRÈS le rendu de la frame suivante,
# avec up ajusté pour une contre-plongée à ~20° de l'horizon.
JS_HOOK = '''(() => {
  const J = window.__jardin;
  // camera ortho n'est pas exposee sur __jardin ; on la recupere via le canvas renderer
  // main.js la garde en closure. Astuce : on passe par fpsCamera + mode fps est locke.
  // Alternative : Three stocke la camera activee dans le RenderPass du composer.
  // Simplest : trouver la camera via scene.traverse n'est pas possible (cameras pas dans scene).
  // => On force via __orthoCam exposé si dispo, sinon on tente la propriete post.
  return 'hook-place';
})()'''
print(eval_js('typeof window.__jardin.post !== "undefined" ? "post ok" : "pas de post"'))
# La camera ortho n'est pas exposee : on passe par le hook de main.js ? Verifions :
print('cles __jardin:', eval_js('JSON.stringify(Object.keys(window.__jardin))'))
