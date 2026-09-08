#!/usr/bin/env python3
"""Capture après chargement HDRI forcé : été midi + hiver midi."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(os.path.dirname(__file__), '..', 'preuves', nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    eval_js('window.__jardin.clock.setSpeed("pause")')
    eval_js('window.__jardin.clock.scrubTo(181.54)')
    time.sleep(1.2)
    shot('lumiere_hdri_ete_midi.png')
    eval_js('window.__jardin.clock.scrubTo(354.54)')
    time.sleep(1.2)
    shot('lumiere_hdri_hiver_midi.png')
    print('env:', eval_js('!!window.__jardin.scene.environment'))

if __name__ == '__main__':
    main()
