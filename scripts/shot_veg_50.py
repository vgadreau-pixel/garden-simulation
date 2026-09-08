#!/usr/bin/env python3
"""50 instances + renderer.info + capture dessous du houppier (validation DoubleSide)."""
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

# Compléter jusqu'à 50 instances
print('planté ->', eval_js('''(() => {
  const J = window.__jardin;
  const libres = [];
  for (let ix = 0; ix < 8; ix++) for (let iz = 0; iz < 8; iz++) libres.push([ix, iz]);
  const prises = new Set(J.jardin.instances.map(i => i.parcelle));
  let k = 0;
  const rng = (n) => Math.floor(Math.random() * n);
  const pool = ["cerisier","erable_japonais","bouleau","pommier","lavande","buis","sapin"];
  while (J.jardin.compter().total < 50 && k < libres.length) {
    const [ix, iz] = libres[k]; k++;
    if (prises.has(ix + "," + iz)) continue;
    prises.add(ix + "," + iz);
    J.jardin.planterParId(pool[rng(pool.length)], ix, iz);
  }
  return J.jardin.compter().total;
})()'''))
time.sleep(10)  # chargement GLTF async
print('veg:', eval_js('JSON.stringify({total: window.__jardin.jardin.instances.length, actifs: window.__jardin.jardin.instances.filter(i=>i.vegActif).length})'))
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2)
print('label:', eval_js('window.__jardin.clock.etat.label'))

# Vue dessus (orbitale par défaut, caméra FPS haute vue plongeante)
eval_js('''(() => {
  const fps = window.__jardin.fps;
  fps.position.set(-6, 6, 8);
  fps.yaw = 0.6; fps.pitch = -0.7;
  fps.updateCamera();
})()''')
time.sleep(1.5)
shot('veg_fix_50_vue1.png')

# Vue de dessous du houppier
eval_js('''(() => {
  const fps = window.__jardin.fps;
  fps.position.set(-2.3, 0.9, 1.7);
  fps.yaw = 0; fps.pitch = 1.1;
  fps.updateCamera();
})()''')
time.sleep(1.5)
shot('veg_fix_50_dessous.png')

# renderer.info @ 50 instances
print('info @50:', eval_js('window.__jardinRenderInfo()'))
fps_val = eval_js('''(async () => {
  let n = 0; const t0 = performance.now();
  await new Promise(res => { const loop = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(loop); else res(); }; requestAnimationFrame(loop); });
  return Math.round(n / 2);
})()''')
print('fps (SwiftShader CPU):', fps_val)
