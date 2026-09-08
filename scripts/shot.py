#!/usr/bin/env python3
"""Screenshot de printemps (date par défaut)."""
import time, sys, base64
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_44f07608/scripts')
from verify_cdp import WS
import json, urllib.request
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.navigate', url='http://localhost:4173/')
time.sleep(4)
ws.drain(0.5)
s = ws.call('Page.captureScreenshot', format='png')
open('/tmp/jardin_printemps2.png', 'wb').write(base64.b64decode(s['data']))
print('ok')
