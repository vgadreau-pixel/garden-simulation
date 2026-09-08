#!/usr/bin/env python3
"""Midi réel (12h pile) + caméra 3 m du cerisier : dernier test du feuillage.
Le scrub .5 donne 12:00 pile — vérifié label '16 octobre · 12:00'. L'été à 197.7
donne 19:00. Donc les captures 'été' étaient en SOIRÉE : soleil couchant,
feuillage dans l'ombre du tone mapping nocturne."""
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

    # Date exacte pour midi : 197.7 = 17 juillet 16:48 ? Vérifions : scrub et label
    for j in [197.0, 197.5, 198.0]:
        eval_js(f'window.__jardin.clock.scrubTo({j})')
        time.sleep(0.2)
        print(j, '->', eval_js('window.__jardin.clock.etat.label'))

    # joueur à 4 m du cerisier, regard franc sur le houppier
    eval_js('''(() => {
      const J = window.__jardin;
      const fps = J.fps;
      fps.position.set(-2.3, 1.7, 1.7);
      fps.yaw = 0;
      fps.pitch = 0.45;
      fps.updateCamera();
    })()''')
    eval_js('window.__jardin.clock.scrubTo(197.5)')
    time.sleep(2.5)
    print('label:', eval_js('window.__jardin.clock.etat.label'))
    shot('veg_final_ete.png')
    eval_js('window.__jardin.clock.scrubTo(289.5)')
    time.sleep(2)
    print('label:', eval_js('window.__jardin.clock.etat.label'))
    shot('veg_final_automne.png')

if __name__ == '__main__':
    main()
