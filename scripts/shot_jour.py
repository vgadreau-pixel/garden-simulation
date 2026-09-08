#!/usr/bin/env python3
"""Captures de jour : scrub sur 21 juillet 14h et 21 janvier 13h."""
import json, time, os, sys, base64
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))

    # 21 juillet 14h = jour 201 + 14/24
    eval_js('window.__jardin.clock.scrubTo(201 + 14/24)')
    time.sleep(2.5)
    shot('final_ete_jour.png')
    # 21 janvier 13h = jour 20 + 13/24
    eval_js('window.__jardin.clock.scrubTo(20 + 13/24)')
    time.sleep(2.5)
    shot('final_hiver_jour.png')

if __name__ == '__main__':
    main()
