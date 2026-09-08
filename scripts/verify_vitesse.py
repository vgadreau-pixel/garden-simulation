#!/usr/bin/env python3
"""Vérif vitesse : mesure sur 2 s avec remise à zéro du point de départ."""
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

    eval_js('window.__jardin.clock.scrubTo(100)')
    eval_js('window.__jardin.clock.setSpeed("semaine")')
    time.sleep(0.3)
    j0 = eval_js('window.__jardin.clock.jours')
    time.sleep(2.0)
    j1 = eval_js('window.__jardin.clock.jours')
    delta = (j1 - j0) % 365
    print(f'vitesse semaine: {delta:.1f} jours / 2s (attendu ~14)', 'OK' if 11 < delta < 17 else 'KO')
    eval_js('window.__jardin.clock.setSpeed("pause")')

if __name__ == '__main__':
    main()
