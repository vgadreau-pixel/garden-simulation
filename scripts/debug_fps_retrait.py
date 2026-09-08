#!/usr/bin/env python3
"""Diagnostic ciblé : FPS réel + renderer.info + retrait clic droit."""
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

    # État courant (page déjà chargée par le test précédent)
    print('etat:', eval_js('JSON.stringify({plantes: window.__jardin.jardin.compter().total, fps: document.getElementById("fps").textContent, vitesse: window.__jardin.clock.speedId})'))

    # draw calls / geometries / textures
    print('renderer_info:', eval_js('JSON.stringify(window.__jardin.scene ? "n/a direct" : "?")'))
    # Pas d'accès direct au renderer : on mesure le frame time brut côté rAF.
    ft = eval_js('''new Promise(res => {
      const n = 60; let last = performance.now(); let i = 0; let max = 0; let sum = 0;
      const f = () => { const t = performance.now(); const d = t - last; last = t; sum += d; max = Math.max(max, d); if (++i < n) requestAnimationFrame(f); else res(JSON.stringify({moyen: +(sum/n).toFixed(1), max: +max.toFixed(1)})); };
      requestAnimationFrame(f);
    })''')
    print('frame_time_ms_60frames:', ft)

    # Pause pour mesurer le FPS « à vide » (rendu seul, pas de croissance)
    # puis test du retrait clic droit : re-scinder un point occupé.
    # D'abord : où sont les plantes ?
    parcelles = eval_js('JSON.stringify(window.__jardin.jardin.instances.map(i => i.parcelle))')
    print('parcelles_occupees:', parcelles)
    pl = json.loads(parcelles)
    if pl:
        ix, iz = map(int, pl[0].split(','))
        vp = json.loads(eval_js('JSON.stringify({w: innerWidth, h: innerHeight})'))
        echelle = vp['h'] / 60.0
        wx = (ix - 3.5) * 4.6; wz = (iz - 3.5) * 4.6
        sx = vp['w']/2 + wx*echelle; sy = vp['h']/2 + wz*echelle
        avant = eval_js('window.__jardin.jardin.compter().total')
        ws.call('Input.dispatchMouseEvent', type='mousePressed', x=sx, y=sy, button='right', clickCount=1)
        ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=sx, y=sy, button='right', clickCount=1)
        time.sleep(0.4)
        apres = eval_js('window.__jardin.jardin.compter().total')
        print(f'retrait_clic_droit sur {pl[0]}: {avant} -> {apres}', 'OK' if apres == avant-1 else 'ECHEC')
        # restaure
        if apres == avant - 1:
            r = eval_js(f'window.__jardin.jardin.planterParId && (window.__jardin.jardin.especeSelectionnee, "x")')

if __name__ == '__main__':
    main()
