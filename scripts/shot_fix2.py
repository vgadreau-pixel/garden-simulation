#!/usr/bin/env python3
"""Recharger la page (nouveau bundle recentré), replanter 50 adultes,
   puis refaire les captures FPS des 3 saisons + vue dessous."""
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

# Recharger
ws.call('Page.navigate', url='http://127.0.0.1:4183/?climat=oceanique')
time.sleep(6)

# Planter 50 espèces variées
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
time.sleep(10)  # chargement GLTF

# Maturité -> 1 : vitesse mois ~12 s
eval_js('window.__jardin.clock.setSpeed("mois")')
time.sleep(12)
eval_js('window.__jardin.clock.setSpeed("pause")')
print('maturite:', eval_js('window.__jardin.instances[0].maturite.toFixed(2)'))
print('pos monde feuilles:', eval_js('''(()=>{const i=window.__jardin.jardin.instances.find(x=>x.plante.id==="cerisier");
  const o={}; i.veg.groupe.traverse(m=>{if(m.isMesh&&/Leaves/.test(m.material.name)){o.pos=m.getWorldPosition(new (m.position.constructor)()).toArray().map(v=>+v.toFixed(1)); o.scale=m.scale.x; return true;}}); return JSON.stringify(o);})()'''))

# Été
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2)

# Mode FPS + captures
eval_js('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.4)
def cam(x, y, z, yaw, pitch):
    eval_js(f'''(() => {{
      const fps = window.__jardin.fps;
      fps.position.set({x}, {y}, {z});
      fps.yaw = {yaw}; fps.pitch = {pitch};
      fps.updateCamera();
    }})()''')

cam(-2.3, 1.7, 3.5, 0, 0.45)
time.sleep(1.5)
shot('fix2_ete.png')
cam(-2.3, 1.2, -0.5, 0, 1.15)
time.sleep(1.5)
shot('fix2_dessous.png')

# Automne
eval_js('window.__jardin.clock.scrubTo(289.5)')
time.sleep(2.5)
cam(-2.3, 1.7, 3.5, 0, 0.45)
time.sleep(1)
shot('fix2_automne.png')

# Hiver
eval_js('window.__jardin.clock.scrubTo(15.5)')
time.sleep(2.5)
cam(-2.3, 1.7, 3.5, 0, 0.4)
time.sleep(1)
shot('fix2_hiver.png')

# renderer.info
print('info:', eval_js('window.__jardinRenderInfo()'))

# Retour orbital
eval_js('document.dispatchEvent(new KeyboardEvent("keydown", {code: "KeyV", bubbles: true}))')
time.sleep(0.3)
print('mode final:', eval_js('window.__jardin.modeCamera'))
