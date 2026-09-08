#!/usr/bin/env python3
"""Test décisif : le mesh feuille du clone est-il dans le frustum et rendu ?
On descend le joueur au pied du cerisier et on regarde vers le haut (pitch 1.2)."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')


def main():
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

    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(197.7)')
    # Pied du cerisier, regard quasi vertical
    eval_js('''(() => {
      const J = window.__jardin;
      const fps = J.fps;
      fps.position.set(-2.3, 1.7, -0.5);
      fps.yaw = 0;
      fps.pitch = 1.1;
      fps.updateCamera();
    })()''')
    time.sleep(2)
    shot('veg_dessous.png')

    # Vérifie combien de leafMeshes sont dans le frustum de la caméra
    fr = eval_js('''(() => {
  const J = window.__jardin;
  const cam = J.fpsCamera;
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  let dans = 0, total = 0;
  const frustum = new (Object.getPrototypeOf(cam.projectionMatrix).constructor) ? null : null;
  // THREE n'est pas exposé globalement ; via constructor de matrices
  const FrustumCtor = Object.getPrototypeOf(cam).constructor; // pas frustum
  // Fallback : projette le centre du mesh en NDC
  const proj = (v) => {
    const p = v.clone().project(cam);
    return { x: p.x, y: p.y, z: p.z };
  };
  const out = [];
  for (const rec of cer.veg.leafMeshes.slice(0, 3)) {
    rec.mesh.updateWorldMatrix(true, false);
    const centre = rec.mesh.position ? rec.mesh.getWorldPosition(new rec.mesh.position.constructor()) : null;
    if (!centre) continue;
    const ndc = proj(centre);
    out.push({ centre: [centre.x, centre.y, centre.z].map(v=>+v.toFixed(1)), ndc: { x: +ndc.x.toFixed(2), y: +ndc.y.toFixed(2), z: +ndc.z.toFixed(2) } });
  }
  return JSON.stringify(out);
})()''')
    print('projection feuilles:', fr)

if __name__ == '__main__':
    main()
