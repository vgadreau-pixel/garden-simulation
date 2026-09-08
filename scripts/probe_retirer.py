#!/usr/bin/env python3
"""Probe B : navigate au_reload en cours de test — qui reset le jardin ?
Surveille compter() toutes les 250 ms pendant 10 s sans re-naviguer."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request


def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    # page déjà ouverte par le probe précédent (19 plantes, pause)
    print('total:', eval_js('window.__jardin.jardin.compter().total'),
          'url:', eval_js('location.href'))
    # planter 7 de plus + surveiller finement
    eval_js('''(() => {
  const J = window.__jardin;
  window.__retirs = [];
  const orig = J.jardin.retirer.bind(J.jardin);
  J.jardin.retirer = (...a) => {
    window.__retirs.push(performance.now().toFixed(0));
    return orig(...a);
  };
  for (const [i, id] of ["forsythia","hortensia","buis","romarin","olivier","iris","tomate"].entries()) {
    J.jardin.planterParId(id, 6, 7 - i);
  }
  return J.jardin.compter().total;
})()''')
    t0 = time.time()
    serie = []
    while time.time() - t0 < 10:
        tot = eval_js('window.__jardin.jardin.compter().total')
        if serie and tot != serie[-1]:
            print(f'CHANGEMENT à t={time.time()-t0:.2f}s : {serie[-1]} -> {tot}')
        serie.append(tot)
        time.sleep(0.25)
    print('série:', serie)
    print('retirs:', eval_js('JSON.stringify(window.__retirs)'))


if __name__ == '__main__':
    main()
