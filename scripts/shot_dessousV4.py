#!/usr/bin/env python3
"""Contre-plongee REELLE : reload (nouveau bundle avec camera+controls exposes),
50 adultes, hook la boucle de rendu pour poser la camera ortho basse (y=1.2,
regard vers le haut dans le houppier), capture dessous, restaure."""
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

# Reload pour servir le nouveau bundle
ws.call('Page.reload')
time.sleep(8)
print('app:', eval_js('!!window.__jardin && !!window.__jardin.camera'))
print('ortho:', eval_js('window.__jardin.camera ? window.__jardin.camera.type : "?"'))

# 50 adultes
JS_PLANTER = '''(() => {
  const J = window.__jardin;
  J.jardin.toutRetirer();
  const libres = [];
  for (let ix = 0; ix < 8; ix++) for (let iz = 0; iz < 8; iz++) libres.push([ix, iz]);
  const rng = (n) => Math.floor(Math.random() * n);
  const pool = ["cerisier","erable_japonais","bouleau","pommier","lavande","buis","sapin","olivier","romarin","hortensia"];
  let k = 0;
  for (const [ix, iz] of libres) {
    if (k >= 50) break;
    J.jardin.planterParId(pool[rng(pool.length)], ix, iz);
    k++;
  }
  for (const inst of J.jardin.instances) inst.maturite = 0.55 + Math.random() * 0.45;
  return J.jardin.compter().total;
})()'''
print('plante:', eval_js(JS_PLANTER))
time.sleep(14)
print('veg:', eval_js('window.__jardin.jardin.instances.filter(i=>i.vegActif).length'))

# Ete midi
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2.5)

# Hook : apres le prochain rendu, poser la camera ortho en contre-plongee
# sous le houppier du cerisier (-2.3, 0.5, 1.7) regarde vers le haut.
JS_HOOK = '''(() => {
  const J = window.__jardin;
  const cam = J.camera;
  const ctl = J.controls;
  // neutraliser controls.update (evite qu'il repositionne la cam)
  const origUpdate = ctl.update.bind(ctl);
  ctl.update = () => { ctl.needsUpdate = false; };
  cam.near = 0.05; cam.far = 300;
  cam.position.set(-2.3, 0.5, 1.7);
  cam.up.set(0, 1, 0);
  cam.lookAt(-2.3, 6, 1.7); // regarde verticalement vers le haut (houppier)
  cam.updateProjectionMatrix();
  cam.updateMatrixWorld();
  return 'cam-posee';
})()'''
print('hook:', eval_js(JS_HOOK))
time.sleep(1.5)
shot('vegV4_dessous_reel.png')

# Restore : reload de la page (plus simple et sur)
ws.call('Page.reload')
time.sleep(8)
print('restore:', eval_js('!!window.__jardin'))
