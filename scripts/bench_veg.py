#!/usr/bin/env python3
"""Bench complet : identifie le goulot sur SwiftShader.
Étapes : tout ON / sans bloom (post désactivé) / sans ciel+étoiles / sans ombres.
"""
import json
import subprocess
import time
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))

PORT = 9353
PROFIL = '/tmp/chrome-veg-bench2'


def wait_debug(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            return json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('Chrome pas prêt')


def main():
    cmd = [
        'google-chrome', '--headless=new',
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={PROFIL}',
        '--no-first-run', '--no-sandbox',
        '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
        '--window-size=1280,720',
        'about:blank',
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tabs = wait_debug(PORT)
        page = [t for t in tabs if t['type'] == 'page'][0]
        from verify_cdp import WS
        ws = WS(page['webSocketDebuggerUrl'])
        ws.call('Page.enable'); ws.call('Runtime.enable')
        ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
        time.sleep(10)

        def eval_js(expr):
            r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
            if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:200])
            return r['result'].get('value')

        def fps3():
            return eval_js('''new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})''')

        eval_js('''(() => {
  const J = window.__jardin;
  J.clock.setSpeed("pause"); J.clock.scrubTo(197);
  const libres = [];
  for (let ix = 0; ix < 8; ix++) for (let iz = 0; iz < 8; iz++) libres.push([ix, iz]);
  const prises = new Set(J.jardin.instances.map(i => i.parcelle));
  const pool = ["cerisier","erable_japonais","bouleau","pommier","lavande","buis","sapin"];
  let k = 0;
  while (J.jardin.compter().total < 50 && k < libres.length) {
    const [ix, iz] = libres[k]; k++;
    if (!prises.has(ix + "," + iz)) {
      J.jardin.planterParId(pool[Math.floor(Math.random() * pool.length)], ix, iz);
      prises.add(ix + "," + iz);
    }
  }
  return J.jardin.compter().total;
})()''')
        time.sleep(6)
        print('setup:', eval_js('window.__jardin.jardin.compter().total'), 'instances')
        print('1. tout ON        :', fps3(), 'fps')

        # Ombres OFF (impact majeur sur CPU)
        eval_js('''(() => { const s = window.__jardin.scene.getObjectByProperty; })()''')
        # sun shadow : via lumière → on passe par renderer.shadowMap
        eval_js('''(() => {
  const r = window.__jardinRenderInfo; // juste pour vérifier l'accès
  return "ok";
})()''')
        # sans post (composer → renderer direct n'est pas exposé ; on coupe bloom via tonemap)
        # Test : cache les étoiles + ciel (sky.js) = couche 3/3
        r = eval_js('''(() => {
  const scene = window.__jardin.scene;
  let n = 0;
  scene.traverse(o => { if (o.userData && (o.userData.ciel || o.userData.etoiles)) { o.visible = false; n++; } });
  return n;
})()''')
        print('sky/etoiles cachés:', r, '→', fps3(), 'fps')

        # météo particules OFF
        r = eval_js('''(() => {
  const m = window.__jardin.meteo;
  if (m && m.points) { m.points.visible = false; return "ok"; }
  return JSON.stringify(Object.keys(m || {}));
})()''')
        print('meteo off:', r, '→', fps3(), 'fps')
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()


if __name__ == '__main__':
    main()
