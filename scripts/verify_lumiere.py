#!/usr/bin/env python3
"""Vérification couche lumière sur Chrome DÉDIÉ port 9345 (pas d'interférence sœurs).
Capture 2 saisons x 2 moments + FPS + renderer.info + état HDRI."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
PORT = 9345

def main():
    tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')
    ws.drain(0.3)
    ws.call('Page.navigate', url='http://localhost:4183/?climat=tempre')
    time.sleep(8)
    events = ws.drain(1.0)
    errs = [e for e in events if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
    excs = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
    print('chargement console_errors:', len(errs), 'exceptions:', len(excs))
    for e in (errs + excs)[:3]: print('  ', json.dumps(e.get('params', {}))[:300])

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    def set_date(jours, nom):
        eval_js(f'window.__jardin.clock.scrubTo({jours})')
        time.sleep(2.0)  # exposition/brume lissées (lerp 0.06/frame)
        print(nom, eval_js('window.__jardin.clock.etat.label'), 'env:', eval_js('!!window.__jardin.scene.environment'))
        shot(f'lumiere_{nom}.png')

    eval_js('window.__jardin.clock.setSpeed("pause")')
    set_date(181.40, 'ete_matin')
    set_date(181.54, 'ete_midi')
    set_date(181.93, 'ete_crepuscule')
    set_date(182.13, 'ete_nuit')
    set_date(354.40, 'hiver_matin')
    set_date(354.54, 'hiver_midi')
    set_date(354.93, 'hiver_crepuscule')
    set_date(355.10, 'hiver_nuit')

    # FPS + renderer.info (fenêtre de 5 s, SwiftShader est lent mais comparatif)
    fps = eval_js('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<5000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})')
    print('fps_pause (swiftshader, 5s):', fps)
    print('render_info:', eval_js('JSON.stringify(window.__jardinRenderInfo ? window.__jardinRenderInfo() : null)'))
    print('dome_visible:', eval_js('(window.__jardin.scene.children.find(o=>o.geometry&&o.geometry.type==="SphereGeometry")||{visible:"?"}).visible'))

if __name__ == '__main__':
    main()
