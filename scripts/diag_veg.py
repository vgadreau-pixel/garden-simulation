#!/usr/bin/env python3
"""Diagnostic ponctuel : que se passe-t-il après plantations via planterParId ?"""
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

    ws.call('Page.navigate', url='http://localhost:4183/')
    time.sleep(3)
    eval_js('localStorage.removeItem("jardin-saisons.plan.v1")')
    ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
    time.sleep(5)

    print('demo:', eval_js('window.__jardin.jardin.compter().total'))
    # pause pour figer la croissance
    eval_js('window.__jardin.clock.setSpeed("pause")')
    r = eval_js('''(() => {
  const J = window.__jardin;
  const res = [];
  for (const id of ["forsythia","hortensia","buis","romarin","olivier","iris","tomate"]) {
    const inst = J.jardin.planterParId(id, 7 - res.length, 7);
    res.push(inst ? id : "ECHEC:" + id);
  }
  return JSON.stringify(res);
})()''')
    print('plantation:', r)
    for delay in (0.5, 2, 5):
        time.sleep(delay - (0.5 if delay == 0.5 else 0))
        print(f't={delay}s total=', eval_js('window.__jardin.jardin.compter().total'),
              'veg=', eval_js('window.__jardin.instances.filter(i=>i.vegActif).length'))
    print('ids:', eval_js('JSON.stringify(window.__jardin.instances.map(i=>i.plante.id))'))
    print('sauvegarde:', eval_js('localStorage.getItem("jardin-saisons.plan.v1")?.length'))


if __name__ == '__main__':
    main()
