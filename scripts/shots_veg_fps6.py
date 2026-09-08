#!/usr/bin/env python3
"""Avance le joueur vers les arbres (position directe du contrôleur) et capture."""
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

    # Joueur À CÔTÉ du cerisier (-2.3, -2.3) : position (0, 1.7, 2), regard vers (-2.3, 3, -2.3)
    r = eval_js('''(() => {
      const J = window.__jardin;
      const fps = J.fps;
      fps.position.set(1, 1.7, 3);
      // Regard vers le cerisier : yaw = atan2(dx, dz) avec convention -sin/-cos
      const dx = -2.3 - 1, dz = -2.3 - 3;
      fps.yaw = Math.atan2(-dx, -dz);
      fps.pitch = 0.25;
      fps.updateCamera();
      return JSON.stringify({ yaw: +fps.yaw.toFixed(2), pos: fps.position.toArray() });
    })()''')
    print('joueur:', r)
    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(197.7)')
    time.sleep(2)
    shot('veg_fps_proche_ete.png')

    eval_js('window.__jardin.clock.scrubTo(289.0)')
    time.sleep(1.5)
    shot('veg_fps_proche_automne.png')

if __name__ == '__main__':
    main()
