#!/usr/bin/env python3
"""Force le basculement FPS via dispatchKeyEvent 'V' + place la caméra,
puis capture l'été/automne en vue subjective."""
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

    def scrub(jours, attente=1.2):
        eval_js('window.__jardin.clock.setSpeed && window.__jardin.clock.setSpeed("pause")')
        eval_js(f'window.__jardin.clock.scrubTo({jours})')
        time.sleep(attente)

    # Positionner le joueur d'abord (le focus FPS l'utilise)
    pos = eval_js('''(() => {
      const J = window.__jardin;
      // Le contrôleur FPS utilise fpsCamera ; réglons sa position directement.
      const cam = J.fpsCamera;
      if (!cam) return 'pas de fpsCamera';
      cam.position.set(2, 1.7, 16);
      cam.lookAt(0, 2.5, 0);
      return JSON.stringify({ pos: cam.position.toArray().map(v=>+v.toFixed(2)) });
    })()''')
    print('fpsCamera:', pos)

    # Envoyer la touche V (bascule orbital→FPS)
    ws.call('Input.dispatchKeyEvent', type='keyDown', code='KeyV', key='v', windowsVirtualKeyCode=86, nativeVirtualKeyCode=86)
    ws.call('Input.dispatchKeyEvent', type='keyUp', code='KeyV', key='v', windowsVirtualKeyCode=86, nativeVirtualKeyCode=86)
    time.sleep(1.0)
    print('mode:', eval_js('window.__jardin.modeCamera'))
    print('camera:', eval_js('JSON.stringify(window.__jardin.fpsCamera ? window.__jardin.fpsCamera.position.toArray().map(v=>+v.toFixed(1)) : null)'))

    scrub(197.7)
    shot('vegetation_ete_fps.png')
    scrub(289.0)
    shot('vegetation_automne_fps.png')

if __name__ == '__main__':
    main()
