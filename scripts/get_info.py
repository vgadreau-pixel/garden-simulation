#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')
print('renderInfo:', eval_js('window.__jardinRenderInfo()'))
