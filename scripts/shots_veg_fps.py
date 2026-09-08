#!/usr/bin/env python3
"""Captures végétation en vue FPS (immersive) pour prouver les modèles 3D."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')


def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    def scrub(jours, attente=1.5):
        eval_js('window.__jardin.clock.setSpeed && window.__jardin.clock.setSpeed("pause")')
        eval_js(f'window.__jardin.clock.scrubTo({jours})')
        time.sleep(attente)

    # État courant du navigateur : l'app est déjà chargée (50 plantes).
    # Bascule en vue FPS via l'API exposée puis oriente la caméra vers le jardin.
    mode = eval_js('window.__jardin.modeCamera')
    print('mode actuel:', mode)

    # Position FPS : placer le joueur au bord du jardin, regard vers le centre.
    eval_js('''(() => {
      const J = window.__jardin;
      // fps = contrôleur FPS exposé ; on place le joueur au sud, regard nord.
      if (J.fps && J.fps.position) {
        J.fps.position.set(0, 1.7, 18);
        if (J.fps.yaw !== undefined) J.fps.yaw = Math.PI; // regard vers -z ? à ajuster
      }
    })()''')
    # Basculer en mode FPS (sans pointer lock en headless : forcer via l'API)
    r = eval_js('''(() => {
      const J = window.__jardin;
      // Essaie l'activation directe du contrôleur FPS
      if (J.fps && typeof J.fps.activer === 'function') {
        try { J.fps.activer(); } catch (e) { return 'err activer: ' + e.message; }
      }
      return 'ok';
    })()''')
    print('activation fps:', r)
    time.sleep(1)
    print('mode apres:', eval_js('window.__jardin.modeCamera'))

    # Capture été vue FPS
    scrub(197.7)
    shot('vegetation_ete_fps.png')

    # Automne vue FPS
    scrub(289.0)
    shot('vegetation_automne_fps.png')

if __name__ == '__main__':
    main()
