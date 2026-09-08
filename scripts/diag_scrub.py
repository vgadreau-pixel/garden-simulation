#!/usr/bin/env python3
"""Diagnostic : état de l'horloge avant/après scrub dans la vraie app."""
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
    etat = eval_js('''JSON.stringify({
      jours: +window.__jardin.clock.jours.toFixed(2),
      speedId: window.__jardin.clock.speedId,
      paused: window.__jardin.clock.paused,
      hasSetSpeed: typeof window.__jardin.clock.setSpeed,
    })''')
    print('etat initial:', etat)
    eval_js('window.__jardin.clock.setSpeed && window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(288.5)')
    time.sleep(0.5)
    apres = eval_js('''JSON.stringify({
      jours: +window.__jardin.clock.jours.toFixed(2),
      label: window.__jardin.clock.etat.label,
      saison: window.__jardin.clock.etat.saison,
    })''')
    print('apres scrub 288.5:', apres)
    # Teinte cerisier via etatPlante direct
    teinte = eval_js('''(() => {
      const J = window.__jardin;
      const inst = J.jardin.instances.find(x => x.plante.id === "cerisier");
      if (!inst) return "pas de cerisier";
      const et = J.etatPlante ? J.etatPlante(inst.plante, J.clock.jours, J.clock.climat) : inst.dernierEtat;
      return JSON.stringify({ couleur: "#"+et.couleur.getHexString(), masse: +et.masseFoliaire.toFixed(2), vegActif: !!inst.vegActif });
    })()''')
    print('cerisier:', teinte)

if __name__ == '__main__':
    main()
