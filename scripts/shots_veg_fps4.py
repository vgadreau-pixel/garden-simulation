#!/usr/bin/env python3
"""Vue FPS de jour : scrub à midi AVANT de capturer, position caméra au centre du jardin."""
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

    # Été midi + caméra FPS au sol regardant les arbres
    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(197.7)')  # 15 juillet midi
    r = eval_js('''(() => {
      const cam = window.__jardin.fpsCamera;
      // Les arbres sont entre -12 et +12 ; joueur à z=14, regard vers z=-6 (cerisier/érable)
      cam.position.set(0, 1.7, 14);
      cam.lookAt(0, 3, -3);
      return 'ok';
    })()''')
    time.sleep(2.0)  # laisser le rendu suivre (2 frames min)
    heure = eval_js('window.__jardin.clock.etat.label')
    print('date:', heure)
    mode = eval_js('window.__jardin.modeCamera')
    print('mode:', mode)
    shot('veg_fps_jour.png')

    # Automne
    eval_js('window.__jardin.clock.scrubTo(289.0)')
    time.sleep(1.5)
    shot('veg_fps_automne.png')
    print('ok')

if __name__ == '__main__':
    main()
