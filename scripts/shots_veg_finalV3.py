#!/usr/bin/env python3
"""Captures finales v3 : Page.bringToFront (evite throttle rAF onglet cache),
50 adultes, ete/automne/hiver + vue dessous + renderer.info."""
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

def scrub(jours, attente=3.0):
    ws.call('Page.bringToFront')
    eval_js(f'window.__jardin.clock.scrubTo({jours})')
    time.sleep(attente)
    return eval_js('window.__jardin.clock.etat.label')

# ---------- 50 adultes ----------
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
ws.call('Page.bringToFront')
print('plante:', eval_js(JS_PLANTER))
time.sleep(14)
print('veg:', eval_js('JSON.stringify({total: window.__jardin.jardin.instances.length, actifs: window.__jardin.jardin.instances.filter(i=>i.vegActif).length})'))

# ---------- ETE ----------
print('label:', scrub(197.5))
cam(-6, 6, 8, 0.6, -0.7); time.sleep(2)
shot('vegV3_ete_dessus.png')
cam(-2.3, 0.9, 1.7, 0, 1.1); time.sleep(2)
shot('vegV3_ete_dessous.png')
print('masse ete:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.slice(0,3).map(i => i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null))'''))

# ---------- AUTOMNE ----------
print('label:', scrub(289.5))
cam(-6, 6, 8, 0.6, -0.7); time.sleep(2)
shot('vegV3_automne_dessus.png')

# ---------- HIVER ----------
print('label:', scrub(15.5))
cam(-6, 6, 8, 0.6, -0.7); time.sleep(2)
shot('vegV3_hiver_dessus.png')
print('masse hiver caducs:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.filter(i=>["cerisier","pommier","bouleau","erable_japonais"].includes(i.plante.id)).slice(0,4).map(i => ({id: i.plante.id, masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null})))'''))
print('masse hiver persistants:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.filter(i=>["sapin","olivier","buis","lavande"].includes(i.plante.id)).slice(0,3).map(i => ({id: i.plante.id, masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null})))'''))

# ---------- Perf ----------
print('label:', scrub(197.5))
print('info @50 adultes:', eval_js('window.__jardinRenderInfo()'))
print('fps (SwiftShader CPU, 2s):', eval_js('''(async () => {
  let n = 0; const t0 = performance.now();
  await new Promise(res => { const loop = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(loop); else res(); }; requestAnimationFrame(loop); });
  return Math.round(n / 2);
})()'''))
