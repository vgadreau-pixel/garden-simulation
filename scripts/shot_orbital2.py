#!/usr/bin/env python3
"""Captures via la caméra orbitale trouvée dans la scène (OrthographicCamera) :
   - on la repose au-dessus du cerisier (-2.3,-2.3) avec zoom serré,
   - été -> automne -> hiver + une vue FPS dessous pour le DoubleSide."""
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
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# Trouver la caméra orthographique dans la scène (pas exposée directement)
print('cams:', eval_js('''(() => {
  const J = window.__jardin;
  let found = [];
  J.scene.traverse(o => { if (o.isCamera) found.push(o.type); });
  return JSON.stringify(found);
})()'''))

# La caméra de rendu est créée hors scène dans main.js ? Tester via composer render pass:
# Solution simple : exposer les données via l'objet renderer ? Non.
# Le plus fiable : la fonction __jardinRenderInfo utilise renderer fermé...
# Essayer THREE via le bundle : impossible hors module.
# => Passer par les événements UI : wheel/pointer sur le canvas pour zoomer (comportement orbital).
# La caméra orbite est TOUJOURS en vue de dessus (lookAt vertical), donc un zoom suffit.
def wheel(dy):
    eval_js(f'''(() => {{
      const cv = document.querySelector('canvas');
      const ev = new WheelEvent('wheel', {{deltaY: {dy}, clientX: 400, clientY: 300, bubbles: true, cancelable: true}});
      cv.dispatchEvent(ev);
    }})()''')

# Été d'abord
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(1.5)
# zoom serré sur le centre (le cerisier est proche du centre) : beaucoup de wheel négatif
for _ in range(12):
    wheel(-240)
    time.sleep(0.08)
time.sleep(1)
shot('veg_fix_orb_ete.png')

# Automne
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2)
shot('veg_fix_orb_automne.png')

# Hiver
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2)
shot('veg_fix_orb_hiver.png')

print('zoom:', eval_js('''(() => "voir image")()'''))
