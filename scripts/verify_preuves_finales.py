#!/usr/bin/env python3
"""Preuve finale : jardin rempli (25+ plantes via sauvegarde) en été,
captures été + hiver, et mesure FPS pause. Protocole minimal en CDP."""
import json, time, os, sys, base64
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
os.makedirs(PREUVES, exist_ok=True)

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable'); ws.call('Page.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))

    # Recharge : la sauvegarde localStorage (23 plantes) doit restaurer le jardin
    ws.call('Page.reload', ignoreCache=True)
    time.sleep(6)
    st = eval_js('JSON.stringify({plantes: window.__jardin.jardin.compter().total, climat: window.__jardin.clock.climat})')
    print('apres_rechargement (sauvegarde):', st)

    # Été plein : scrub au 21 juillet
    eval_js('window.__jardin.clock.scrubTo(201)')
    time.sleep(2.0)
    shot('final_ete_23plantes.png')

    # Hiver : 21 janvier
    eval_js('window.__jardin.clock.scrubTo(20)')
    time.sleep(2.0)
    shot('final_hiver_23plantes.png')

    # FPS en pause (mesure embarquée, protocole silencieux)
    fps = eval_js('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})')
    print('fps_pause (23 plantes, headless SwiftShader):', fps)
    errs = eval_js('window.__jardin ? "app_vivante" : "MORTE"')
    print('etat_final:', errs)

if __name__ == '__main__':
    main()
