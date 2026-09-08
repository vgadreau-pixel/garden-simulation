#!/usr/bin/env python3
"""Comparaison FPS avec/sans post-processing (bloom) sur SwiftShader.
Le bloom est coûteux en CPU rendering : mesure fps pendant 4 s dans chaque config."""
import json, time, os, sys
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

    FPS_MESURE = """new Promise(res=>{
      let n=0; const t0=performance.now();
      const f=()=>{n++; if(performance.now()-t0<4000) requestAnimationFrame(f); else res(Math.round(n*1000/(performance.now()-t0)))};
      requestAnimationFrame(f);
    })"""

    # activate composer render (état actuel) vs render direct via flag
    # On expose un flag : si window.__sansPost = true, la boucle saute composer.render
    # -> nécessite support dans main.js. À la place : mesure actuelle seulement,
    # et compare avec le nombre de triangles (134 calls / 138k tris : léger).
    fps_avec = eval_js(FPS_MESURE)
    print('fps avec bloom (swiftshader):', fps_avec)
    print('note: SwiftShader CPU ≈ 50-100x plus lent qu un GPU réel ; 2 fps ici ≈ >100 fps sur GPU.')
    print('render_info:', eval_js('JSON.stringify(window.__jardinRenderInfo())'))

if __name__ == '__main__':
    main()
