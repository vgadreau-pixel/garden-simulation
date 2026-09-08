#!/usr/bin/env python3
"""Captures post-fix DoubleSide (bundle 23:18) : reload, 50 instances,
vue dessus + dessous houppier, ete + automne. Stdlib only."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
print('URL onglet:', page['url'])
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

def cam(x, y, z, yaw, pitch):
    eval_js(f'''(() => {{
      const fps = window.__jardin.fps;
      fps.position.set({x}, {y}, {z});
      fps.yaw = {yaw}; fps.pitch = {pitch};
      fps.updateCamera();
    }})()''')

# Reload pour servir le bundle avec le fix DoubleSide
ws.call('Page.reload')
time.sleep(7)
print('app:', eval_js('!!window.__jardin'))
if eval_js('!!window.__jardin') is not True:
    print('ERREUR: app non chargee'); sys.exit(1)

# Planter jusqu'a 50 instances
print('plante ->', eval_js('''(() => {
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
time.sleep(12)  # chargement GLTF async
print('veg:', eval_js('JSON.stringify({total: window.__jardin.jardin.instances.length, actifs: window.__jardin.jardin.instances.filter(i=>i.vegActif).length, prim: window.__jardin.jardin.instances.filter(i=>!i.vegActif).length})'))

# Ete midi + maturite pleine (scrub direct)
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2)
print('label:', eval_js('window.__jardin.clock.etat.label'))

# Vue 1 : dessus du jardin
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(1.5)
shot('veg_final50_ete_dessus.png')

# Vue 2 : de dessous, dans le houppier du cerisier (validation DoubleSide)
cam(-2.3, 0.9, 1.7, 0, 1.1)
time.sleep(1.5)
shot('veg_final50_ete_dessous.png')

# Automne midi
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2)
print('label:', eval_js('window.__jardin.clock.etat.label'))
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(1.5)
shot('veg_final50_automne_dessus.png')
cam(-2.3, 0.9, 1.7, 0, 1.1)
time.sleep(1.5)
shot('veg_final50_automne_dessous.png')

# renderer.info @ 50 instances
print('info @50:', eval_js('window.__jardinRenderInfo()'))
print('fps (SwiftShader CPU, 2s):', eval_js('''(async () => {
  let n = 0; const t0 = performance.now();
  await new Promise(res => { const loop = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(loop); else res(); }; requestAnimationFrame(loop); });
  return Math.round(n / 2);
})()'''))

# Etat socle : climat + audio + console
print('climat:', eval_js('window.__jardin.climatActuel || "?"'))
