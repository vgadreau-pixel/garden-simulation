#!/usr/bin/env python3
"""Vérification fonctionnelle : le socle (plantation, timebar, climat, audio UI) fonctionne.
À exécuter sur le Chrome dédié 9345 APRÈS verify_lumiere."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9345/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    # 1. plantation au clic (via l'API du jardin, comme le socle le permet)
    avant = eval_js('window.__jardin.jardin.compter().total')
    ok = eval_js('window.__jardin.jardin.planterParId ? (window.__jardin.jardin.planterParId("tulipe", 7, 7) !== false) : "pas dAPI"')
    apres = eval_js('window.__jardin.jardin.compter().total')
    print(f'plantation: {avant} -> {apres}', 'OK' if (isinstance(ok, bool) and apres > avant) else ok)

    # 2. scrub + vitesse
    eval_js('window.__jardin.clock.setSpeed("semaine")')
    time.sleep(1.2)
    j0 = eval_js('window.__jardin.clock.jours')
    time.sleep(1.0)
    j1 = eval_js('window.__jardin.clock.jours')
    print(f'vitesse semaine: {j1-j0:.2f} jours/s (attendu ~7)', 'OK' if abs((j1-j0) - 7) < 2 else 'KO')
    eval_js('window.__jardin.clock.setSpeed("pause")')

    # 3. bascule climat
    cl0 = eval_js('window.__jardin.clock.climat')
    eval_js('window.__jardin.clock.setClimat("mediterraneen")')
    cl1 = eval_js('window.__jardin.clock.climat')
    print('climat:', cl0, '->', cl1, 'OK' if cl1 == 'mediterraneen' else 'KO')

    # 4. mode FPS existe
    print('modeCamera:', eval_js('window.__jardin.modeCamera'), '| fpsCamera:', eval_js('!!window.__jardin.fpsCamera'))

    # 5. scrub nuit → étoiles visibles
    eval_js('window.__jardin.clock.scrubTo(182.2)')
    time.sleep(1.0)
    print('etoiles_opacity_nuit:', eval_js('(window.__jardin.scene.children.find(o=>o.type==="Points"&&o.material.color&&o.material.color.getHexString()==="dfe8ff")||{material:{opacity:-1}}).material.opacity'))
    eval_js('window.__jardin.clock.scrubTo(181.5)')
    time.sleep(1.0)
    print('etoiles_opacity_jour:', eval_js('(window.__jardin.scene.children.find(o=>o.type==="Points"&&o.material.color&&o.material.color.getHexString()==="dfe8ff")||{material:{opacity:-1}}).material.opacity'))

if __name__ == '__main__':
    main()
