#!/usr/bin/env python3
"""Diag 2 : erreurs de module sur la page chargée avec le nouveau bundle."""
import json, time, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable')
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=6000')
time.sleep(15)
events = ws.drain(1.0)
errs = [e for e in events if e.get('method') in ('Runtime.exceptionThrown', 'Log.entryAdded', 'Runtime.consoleAPICalled')]
print('evenements:', len(errs))
for e in errs[:15]:
    print(json.dumps(e.get('params', {}))[:500])
r = ws.call('Runtime.evaluate', expression='typeof window.__jardin', returnByValue=True)
print('jardin:', r['result'].get('value'))
