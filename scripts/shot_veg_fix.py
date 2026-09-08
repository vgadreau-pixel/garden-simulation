#!/usr/bin/env python3
"""Validation finale des fixs DoubleSide + frustumCulled :
   - recharger la page (nouveau bundle),
   - vue de DESSOUS du houppier (feuilles visibles grâce au DoubleSide),
   - renderer.info (draw calls / triangles) + fps mesuré sur 2 s."""
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

# Recharger pour servir le nouveau bundle
ws.call('Page.navigate', url='http://127.0.0.1:4183/?climat=oceanique')
time.sleep(6)
print('titre:', eval_js('document.title'))
print('instances:', eval_js('window.__jardin && Object.keys(window.__jardin).length'))

# Été, midi
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(2)
print('label:', eval_js('window.__jardin.clock.etat.label'))

# Caméra SOUS le houppier du cerisier, regard vers le haut
eval_js('''(() => {
  const J = window.__jardin;
  const fps = J.fps;
  fps.position.set(-2.3, 0.9, 1.7);
  fps.yaw = 0;
  fps.pitch = 1.1;
  fps.updateCamera();
})()''')
time.sleep(1.5)
shot('veg_final_dessous.png')

# Vérifier que les feuilles sont rendues : compter meshes feuilles visibles
print('vegActifs:', eval_js('window.__jardin.jardin.instances.filter(i=>i.vegActif).length'))
print('instances total:', eval_js('window.__jardin.jardin.instances.length'))
print('primitives visibles:', eval_js('window.__jardin.jardin.instances.filter(i=>!i.vegActif && i.group.visible!==false).length'))

# renderer.info + fps sur 2 s
print('info:', eval_js('''(() => {
  const J = window.__jardin;
  const r = J.renderer || (J.composer && J.composer.renderer) || (window.__jardinRenderInfo && window.__jardinRenderInfo());
  return JSON.stringify(typeof r === 'string' ? r : (r ? {calls: r.info.render.calls, tris: r.info.render.triangles} : 'n/a'));
})()'''))
fps_val = eval_js('''(async () => {
  let n = 0; const t0 = performance.now();
  await new Promise(res => { const loop = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(loop); else res(); }; requestAnimationFrame(loop); });
  return Math.round(n / 2);
})()''')
print('fps (2 s, SwiftShader CPU):', fps_val)
