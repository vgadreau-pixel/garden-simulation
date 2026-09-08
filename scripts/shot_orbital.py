#!/usr/bin/env python3
"""Captures avec la caméra orbitale orthographique (vue de dessus du projet) :
   - zoom/pan sur le cerisier (-2.3, -2.3) été -> automne -> hiver,
   - la vue de dessus montre le houppier depuis DESSUS (DoubleSide n'y change
     rien) ; le test dessous reste la vue FPS.
   On pilote controls.target/zoom directement (comme un pan/zoom utilisateur)."""
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

def orb(x, z, zoom):
    eval_js(f'''(() => {{
      const J = window.__jardin;
      // controls n'est pas exposé ; passer par le canvas : simuler ? Non —
      // on cherche controls exposé quelque part.
      return "voir script";
    }})()''')

# controls exposé ? sinon exposer via main ? On ne peut pas modifier main pour ça.
# Vérifier ce qui est exposé :
print('clés __jardin:', eval_js('Object.keys(window.__jardin).join(",")'))
