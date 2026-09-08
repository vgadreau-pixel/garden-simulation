#!/usr/bin/env python3
"""Perf 50 instances : renderer.info + fps rAF (complément verify_vegetation)."""
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
    time.sleep(6)
    eval_js('localStorage.removeItem("jardin-saisons.plan.v1")')
    ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
    time.sleep(6)

    PLANT = '''(() => {
  const J = window.__jardin;
  const ids = ["cerisier","erable_japonais","sapin","olivier","bouleau","pommier",
               "lavande","rosier","hortensia","buis","romarin","forsythia",
               "tulipe","coquelicot","marguerite","iris","tomate","carotte","courgette"];
  const presents = new Set(J.jardin.instances.map(i => i.plante.id));
  const libres = [];
  for (let ix = 0; ix < 8; ix++) for (let iz = 0; iz < 8; iz++) libres.push([ix, iz]);
  const prises = new Set(J.jardin.instances.map(i => i.parcelle));
  let k = 0;
  for (const id of ids) {
    if (presents.has(id)) continue;
    while (k < libres.length && prises.has(libres[k].join(","))) k++;
    if (k >= libres.length) break;
    const [ix, iz] = libres[k]; k++;
    if (J.jardin.planterParId(id, ix, iz)) prises.add(ix + "," + iz);
  }
  const rng = (n) => Math.floor(Math.random() * n);
  const pool = ["cerisier","erable_japonais","bouleau","pommier","lavande","buis","sapin"];
  while (J.jardin.compter().total < 50 && k < libres.length) {
    const [ix, iz] = libres[k]; k++;
    J.jardin.planterParId(pool[rng(pool.length)], ix, iz);
  }
  return J.jardin.compter().total;
})()'''
    n = eval_js(PLANT)
    time.sleep(8)
    eval_js('window.__jardin.clock.setSpeed && window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(197.5)')
    time.sleep(1)
    veg = eval_js('JSON.stringify({total: window.__jardin.jardin.instances.length, actifs: window.__jardin.jardin.instances.filter(i=>i.vegActif).length})')
    info = eval_js('JSON.stringify(window.__jardinRenderInfo())')
    fps = eval_js('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})')
    print('instances_50:', n, veg)
    print('render_info_50:', info)
    print('fps_raf_50:', fps)

if __name__ == '__main__':
    main()
