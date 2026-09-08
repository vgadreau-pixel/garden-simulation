#!/usr/bin/env python3
"""Diagnostic perf : compare FPS vitesse pause vs 1 mois/s, et check météo."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def fps_pendant(duree_s, label):
        ws.call('Runtime.evaluate', expression='document.getElementById("fps").textContent="..."')
        n = 0; t0 = performance_now = time.time()
        # mesure via rAF côté page
        r = eval_js('''new Promise(res => {
          let n = 0; const t0 = performance.now();
          const f = () => { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(f); else res(n * 1000 / (performance.now() - t0)); };
          requestAnimationFrame(f);
        })''')
        print(f'{label}: rAF {r} fps')
        return r

    print('climat:', eval_js('window.__jardin.clock.climat'), 'jours:', eval_js('window.__jardin.clock.jours.toFixed(1)'))
    m = eval_js('JSON.stringify(meteoLocale())' if False else 'null')

    # Vitesse pause (via l'API clock, pas l'UI)
    eval_js('window.__jardin.clock.setSpeed("pause")')
    time.sleep(0.5)
    fps_pendant(3, 'fps_pause')

    # Vitesse 1 mois/s
    eval_js('window.__jardin.clock.setSpeed("mois")')
    time.sleep(0.5)
    fps_pendant(3, 'fps_mois_s')

    # Nombre de plantes et FPS associé
    print('plantes:', eval_js('window.__jardin.jardin.compter().total'))

    # Particules météo visibles ?
    print('meteo:', eval_js('JSON.stringify({pluie: !!document.querySelector("#climat-infos")?.textContent})'))
    # Compter les Points three.js dans la scène
    print('objets_scene:', eval_js('JSON.stringify({children: window.__jardin.scene.children.length})'))

if __name__ == '__main__':
    main()
