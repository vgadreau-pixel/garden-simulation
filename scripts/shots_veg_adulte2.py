#!/usr/bin/env python3
"""Captures ADULTES post-fix : replantage a maturite 0.55-1.0 (jardin etabli),
vue dessus + dessous houppier, ete/automne/hiver + renderer.info."""
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

def cam(x, y, z, yaw, pitch):
    eval_js(f'''(() => {{
      const fps = window.__jardin.fps;
      fps.position.set({x}, {y}, {z});
      fps.yaw = {yaw}; fps.pitch = {pitch};
      fps.updateCamera();
    }})()''')

# Charger planteParId depuis le bundle (module non expose sur window sinon)
eval_js("import('/assets/index-CEfvqw5P.js').then(m => { window.__planteParId = m.planteParId; })")
time.sleep(1)

JS_PLANTER = '''(() => {
  const J = window.__jardin;
  J.jardin.toutRetirer();
  const libres = [];
  for (let ix = 0; ix < 8; ix++) for (let iz = 0; iz < 8; iz++) libres.push([ix, iz]);
  const rng = (n) => Math.floor(Math.random() * n);
  const pool = ["cerisier","erable_japonais","bouleau","pommier","lavande","buis","sapin","olivier","romarin","hortensia"];
  let k = 0;
  if (!window.__planteParId) return 'PAS_DE_PLANTEPARID';
  for (const [ix, iz] of libres) {
    if (k >= 50) break;
    const plante = window.__planteParId(pool[rng(pool.length)]);
    if (!plante) continue;
    J.jardin.planter(ix, iz, plante, { maturite: 0.55 + Math.random() * 0.45 });
    k++;
  }
  return J.jardin.compter().total;
})()'''

print('plante:', eval_js(JS_PLANTER))
time.sleep(14)  # chargement GLTF async
print('veg:', eval_js('JSON.stringify({total: window.__jardin.jardin.instances.length, actifs: window.__jardin.jardin.instances.filter(i=>i.vegActif).length, prim: window.__jardin.jardin.instances.filter(i=>!i.vegActif).length})'))
print('scales:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.slice(0,5).map(i => ({id: i.plante.id, mat: +i.maturite.toFixed(2), scale: +i.group.scale.x.toFixed(2)})))'''))

# ETE midi
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2.5)
print('label:', eval_js('window.__jardin.clock.etat.label'))
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(2)
shot('vegV2_ete_dessus.png')
cam(-2.3, 0.9, 1.7, 0, 1.1)
time.sleep(2)
shot('vegV2_ete_dessous.png')

# AUTOMNE midi
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2.5)
print('label:', eval_js('window.__jardin.clock.etat.label'))
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(2)
shot('vegV2_automne_dessus.png')

# HIVER midi
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2.5)
print('label:', eval_js('window.__jardin.clock.etat.label'))
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(2)
shot('vegV2_hiver_dessus.png')
print('masse hiver:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.slice(0,5).map(i => ({id: i.plante.id, masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null})))'''))

# Retour ete : renderer.info + fps
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2.5)
print('info @50 adultes:', eval_js('window.__jardinRenderInfo()'))
print('fps (SwiftShader CPU, 2s):', eval_js('''(async () => {
  let n = 0; const t0 = performance.now();
  await new Promise(res => { const loop = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(loop); else res(); }; requestAnimationFrame(loop); });
  return Math.round(n / 2);
})()'''))
