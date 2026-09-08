#!/usr/bin/env python3
"""Diag : que charge le navigateur sur 4183 ? Erreurs console ?"""
import json, time, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
for t in tabs:
    if t['type'] == 'page':
        print('PAGE:', t['url'])
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable')
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=6000')
time.sleep(12)
for expr in [
    'location.href',
    'document.title',
    'document.querySelector("script[type=module]")?.src || "no-module-script"',
    'typeof window.__jardin',
    'document.getElementById("chargement") ? "ecran-chargement-present" : document.body.innerHTML.slice(0,200)',
]:
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        print('EXC:', r['exceptionDetails']['exception']['description'][:200])
    else:
        print(repr(r['result'].get('value'))[:300])
events = ws.drain(1.0)
for e in events:
    if e.get('method') in ('Runtime.exceptionThrown', 'Log.entryAdded', 'Runtime.consoleAPICalled'):
        print(json.dumps(e.get('params', {}))[:400])
