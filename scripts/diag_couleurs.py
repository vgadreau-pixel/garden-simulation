#!/usr/bin/env python3
"""Diag couleurFeuillage : teinte attendue vs reçue à différentes dates."""
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

    for j in [106.5, 197.7, 289.0, 15.2]:
        eval_js(f'window.__jardin.clock.scrubTo({j})')
        time.sleep(0.3)
        res = eval_js('''(() => {
          const J = window.__jardin;
          const inst = J.jardin.instances.find(x => x.plante.id === "cerisier");
          if (!inst) return "pas de cerisier";
          const et = inst.dernierEtat || {};
          const c = et.couleur ? "#"+et.couleur.getHexString() : "n/a";
          const vig = J.vigueur ? null : null;
          return JSON.stringify({ jours: +J.clock.jours.toFixed(1), couleur: c, masse: et.masseFoliaire != null ? +et.masseFoliaire.toFixed(2) : null });
        })()''')
        print(j, '->', res)

if __name__ == '__main__':
    main()
