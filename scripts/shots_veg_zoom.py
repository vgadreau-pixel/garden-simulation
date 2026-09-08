#!/usr/bin/env python3
"""Coupure nette : distance joueur↔cerisier 3 m, pitch 0 (horizontal), midi été."""
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

    # Le joueur regarde le cerisier de 3 m seulement, à hauteur des feuilles (2,5 m du sol)
    # cerisier (-2.3, 0, -2.3), hauteur feuillage ~2.5-6.9 m
    eval_js('''(() => {
      const J = window.__jardin;
      const fps = J.fps;
      fps.position.set(-2.3, 1.7, 0.7);  // 3 m au sud du cerisier
      fps.yaw = 0;                        // convention : -sin(0)=0, -cos(0)=-1 → regard -z (vers le cerisier)
      fps.pitch = 0.35;                   // vers le haut : houppier à 2.5-6.9 m
      fps.updateCamera();
    })()''')
    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(197.7)')
    time.sleep(2)
    print('cam dir:', eval_js('JSON.stringify(window.__jardin.fpsCamera.getWorldDirection(window.__jardin.fpsCamera.position.constructor ? new window.__jardin.fpsCamera.position.constructor() : null) ? null : null)'))
    d = eval_js('''(() => {
      const cam = window.__jardin.fpsCamera;
      const dir = new (cam.position.constructor)();
      cam.getWorldDirection(dir);
      return JSON.stringify({ pos: cam.position.toArray().map(v=>+v.toFixed(1)), dir: dir.toArray().map(v=>+v.toFixed(2)) });
    })()''')
    print('camera:', d)
    shot('veg_zoom_ete.png')

    eval_js('window.__jardin.clock.scrubTo(289.0)')
    time.sleep(1.5)
    shot('veg_zoom_automne.png')

if __name__ == '__main__':
    main()
