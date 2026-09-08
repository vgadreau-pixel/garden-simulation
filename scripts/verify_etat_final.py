#!/usr/bin/env python3
"""Etat final : page saine, socle OK, puis rendu des chemins de captures."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

ws.call('Page.bringToFront')
time.sleep(2)
print('app:', eval_js('!!window.__jardin'))
print('label:', eval_js('window.__jardin.clock ? window.__jardin.clock.etat.label : "?"'))
print('erreurs:', eval_js('window.__errs ? window.__errs.length : "hook absent (page rechargee)"'))
