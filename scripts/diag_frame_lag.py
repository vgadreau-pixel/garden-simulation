#!/usr/bin/env python3
"""Diag 3 : dernierEtat prend-il la valeur de la frame en cours après scrub ?"""
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

    # Passage direct par etatPlante (pas via dernierEtat) : existe-t-il dans __jardin ?
    expos = eval_js('JSON.stringify(Object.keys(window.__jardin))')
    print('expositions __jardin:', expos)

    # Scrub 289 puis lecture IMMÉDIATE vs après 1 s
    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(289)')
    t0 = eval_js('''(() => {
      const inst = window.__jardin.jardin.instances.find(x => x.plante.id === "cerisier");
      const c = inst.dernierEtat.couleur ? "#"+inst.dernierEtat.couleur.getHexString() : "n/a";
      return JSON.stringify({ quand: "immediat", jours: +window.__jardin.clock.jours.toFixed(1), couleur: c });
    })()''')
    print('lecture immédiate après scrub:', t0)
    time.sleep(1.5)
    t1 = eval_js('''(() => {
      const inst = window.__jardin.jardin.instances.find(x => x.plante.id === "cerisier");
      const c = "#"+inst.dernierEtat.couleur.getHexString();
      const mat = "#"+inst.veg.leafMats[0].color.getHexString();
      return JSON.stringify({ quand: "apres 1.5s", jours: +window.__jardin.clock.jours.toFixed(1), dernierEtat: c, mat: mat, feuilleVisible: inst.veg.leafMeshes[0].mesh.scale.x.toFixed(3) });
    })()''')
    print('après 1.5 s:', t1)

if __name__ == '__main__':
    main()
