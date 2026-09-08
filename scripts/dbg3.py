#!/usr/bin/env python3
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
print('URL:', page['url'])
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable')
ws.call('Page.navigate', url='http://[::1]:4183/')
time.sleep(7)
events = ws.drain(1.5)
errs = [e for e in events if e.get('method') in ('Runtime.consoleAPICalled', 'Runtime.exceptionThrown', 'Log.entryAdded')]
for e in errs[:12]:
    p = e.get('params', {})
    if 'entry' in p:
        print('LOG:', p['entry'].get('level'), p['entry'].get('text')[:200], p['entry'].get('url', ''))
    elif e['method'] == 'Runtime.exceptionThrown':
        print('EXC:', p['exceptionDetails']['exception'].get('description', '')[:400])
    else:
        print(p.get('type'), str(p.get('args'))[:200])
r = ws.call('Runtime.evaluate', expression='JSON.stringify({ready:document.readyState, jardin: typeof window.__jardin, loader: !!document.getElementById("loader"), fps: document.getElementById("fps")?.textContent})', returnByValue=True)
print(r['result'].get('value'))
