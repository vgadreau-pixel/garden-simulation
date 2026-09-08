#!/usr/bin/env python3
"""Re-prépare des captures claires pour la validation visuelle :
- scrub à midi en été (lumière maximale) et en hiver,
- zoome un peu pour voir les modèles de près.
Capture 2 PNG nets et une vue FPS proche d'un arbre.
"""
import json
import time
import os
import sys
import base64
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')


def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    # état : 50 instances déjà plantées, pause
    eval_js('window.__jardin.clock.setSpeed("pause")')
    # Été 12h30 : scrub jour 197.5 (0.5 = midi)
    eval_js('window.__jardin.clock.scrubTo(197.55)')
    time.sleep(1.5)
    print('date:', eval_js('window.__jardin.clock.etat.label'))
    shot('vegetation_ete_midi.png')

    # Hiver midi
    eval_js('window.__jardin.clock.scrubTo(15.55)')
    time.sleep(1.5)
    print('date:', eval_js('window.__jardin.clock.etat.label'))
    shot('vegetation_hiver_midi.png')

    # retour été pour la propreté du plan
    eval_js('window.__jardin.clock.scrubTo(197.55)')


if __name__ == '__main__':
    main()
