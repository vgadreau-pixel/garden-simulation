#!/usr/bin/env python3
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def evfull(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    print(r.get('exceptionDetails') or r['result'].get('value'))

evfull('window.__jardin.modeCamera')
evfull('JSON.stringify(window.__jardin.jardin.instances.map(i=>i.parcelle))')
