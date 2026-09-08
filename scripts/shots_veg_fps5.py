#!/usr/bin/env python3
"""Vue FPS correcte : piloter le contrôleur (position + yaw/pitch), pas la caméra.
Le contrôleur écrase la caméra à chaque frame via updateCamera()."""
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

    # Piloter le CONTRÔLEUR : position (0, z=14) + yaw=PI (regard -z vers le jardin)
    r = eval_js('''(() => {
      const J = window.__jardin;
      const fps = J.fps;
      if (!fps || !fps.position) return 'pas de controleur';
      fps.position.set(0, 1.7, 14);
      fps.yaw = Math.PI;   // regard vers -z : le jardin
      fps.pitch = 0.1;     // légèrement vers le haut pour voir les houppiers
      fps.updateCamera();
      return JSON.stringify({ pos: fps.position.toArray(), yaw: fps.yaw });
    })()''')
    print('controleur:', r)

    # Été midi
    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(197.7)')
    time.sleep(2.0)
    shot('veg_fps_jour.png')

    # Automne midi
    eval_js('window.__jardin.clock.scrubTo(289.0)')
    time.sleep(1.5)
    shot('veg_fps_automne.png')

    # Hiver midi (arbres nus + neige)
    eval_js('window.__jardin.clock.scrubTo(15.2)')
    time.sleep(1.5)
    shot('veg_fps_hiver.png')

if __name__ == '__main__':
    main()
