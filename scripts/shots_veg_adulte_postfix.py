#!/usr/bin/env python3
"""Captures finales post-fix : 3 ans de time-lapse (arbres adultes) avec le
bundle DoubleSide. Vue dessus jardin, dessous houppier, 2 saisons + info."""
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

# 3 ans plus tard, ete midi : arbres adultes
eval_js('window.__jardin.clock.scrubTo(1292.5)')
time.sleep(3)
print('label:', eval_js('window.__jardin.clock.etat.label'))
print('stades:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.slice(0,4).map(i => ({id: i.plante.id, stade: +(i.stade||0).toFixed(2), scale: +i.group.scale.x.toFixed(2), veg: i.vegActif})))'''))

# Vue dessus
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(2)
shot('veg_fix50_adulte_ete_dessus.png')

# Vue dessous houppier du cerisier
cam(-2.3, 0.9, 1.7, 0, 1.1)
time.sleep(2)
shot('veg_fix50_adulte_ete_dessous.png')

# Automne midi (adulte)
eval_js('window.__jardin.clock.scrubTo(1384.5)')
time.sleep(3)
print('label:', eval_js('window.__jardin.clock.etat.label'))
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(2)
shot('veg_fix50_adulte_automne_dessus.png')

# Hiver : arbre nu attendu
eval_js('window.__jardin.clock.scrubTo(1110.5)')
time.sleep(3)
print('label:', eval_js('window.__jardin.clock.etat.label'))
cam(-6, 6, 8, 0.6, -0.7)
time.sleep(2)
shot('veg_fix50_adulte_hiver_dessus.png')
print('etat hiver:', eval_js('''JSON.stringify(window.__jardin.jardin.instances.slice(0,5).map(i => ({id: i.plante.id, masse: i.dernierEtat ? +i.dernierEtat.masseFoliaire.toFixed(2) : null})))'''))

# retour ete pour renderer.info + fps
eval_js('window.__jardin.clock.scrubTo(1292.5)')
time.sleep(3)
print('info @50 adultes:', eval_js('window.__jardinRenderInfo()'))
print('fps (SwiftShader CPU, 2s):', eval_js('''(async () => {
  let n = 0; const t0 = performance.now();
  await new Promise(res => { const loop = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(loop); else res(); }; requestAnimationFrame(loop); });
  return Math.round(n / 2);
})()'''))
