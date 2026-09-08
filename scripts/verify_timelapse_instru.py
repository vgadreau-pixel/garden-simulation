#!/usr/bin/env python3
"""Time-lapse ambiguïté levée : on instrumente clock._avancer pour compter
le TOTAL de millisecondes passées à l'horloge (wraps d'année inclus),
avec seulement 3 évaluations CDP (avant / après / lecture) — pas de polling.
Prérequis : verify_finale.py déjà passé (audio actif, jardin planté)."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    def clic(x, y):
        ws.call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)

    # Instrumentation : on compte les ms réellement passés à l'horloge.
    eval_js('''(() => {
      const c = window.__jardin.clock;
      window.__avMs = 0; window.__frames = 0;
      const orig = c._avancer.bind(c);
      c._avancer = (ms) => { window.__avMs += ms; window.__frames++; orig(ms); };
      window.__origAvancer = orig;
      return 'instrumente';
    })()''')

    # Clic sur la vitesse 'mois' (vrai clic souris)
    vl = json.loads(eval_js('JSON.stringify([...document.querySelectorAll("#timebar .tbtn")].map(b=>({s:b.dataset.speed,r:b.getBoundingClientRect().toJSON()})))'))
    c = next(b for b in vl if b['s'] == 'mois')
    clic(c['r']['x']+c['r']['width']/2, c['r']['y']+c['r']['height']/2)

    t0 = time.time()
    time.sleep(12.6)
    duree = time.time() - t0

    res = json.loads(eval_js('''(() => {
      const c = window.__jardin.clock;
      c._avancer = window.__origAvancer;  // restauration
      return JSON.stringify({ avMs: window.__avMs, frames: window.__frames,
                              jours: c.jours, label: c.etat.label });
    })()'''))
    av_s = res['avMs'] / 1000.0
    jours_total = av_s * 30.0
    print(f"duree_reelle: {duree:.1f}s  frames: {res['frames']}  fps: {res['frames']/duree:.1f}")
    print(f"temps_accumule_horloge: {av_s:.2f}s -> {jours_total:.1f} jours (wraps inclus)")
    print(f"attendu: {duree*30:.0f} jours ; couverture annee: {jours_total/365*100:.0f}%")
    print("annee_complete:", "OUI" if jours_total >= 365 else "NON")
    print("date_fin:", res['label'])

if __name__ == '__main__':
    main()
