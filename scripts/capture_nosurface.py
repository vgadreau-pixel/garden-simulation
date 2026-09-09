#!/usr/bin/env python3
"""Capture via Page.captureScreenshot fromSurface=false (bypass surface gelée)."""
import json, time, sys, os, base64, urllib.request, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

vis = ev('JSON.stringify({vis: document.visibilityState, hidden: document.hidden})')
print('visibilité:', vis)

for jour, nom in [(105, 'fs_printemps'), (258, 'fs_automne'), (166, 'fs_ete'), (15, 'fs_hiver')]:
    ev(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({jour} + 10/24)')
    time.sleep(8)
    saison = ev('window.__jardin.clock.etat.saison')
    s = ws.call('Page.captureScreenshot', format='png', fromSurface=False)
    data = base64.b64decode(s['data'])
    f = os.path.join(P, nom + '.png')
    open(f, 'wb').write(data)
    print(nom, '| saison:', saison, '|', len(data), 'octets | md5:', hashlib.md5(data).hexdigest()[:10])

import numpy as np
from PIL import Image
def arr(f): return np.asarray(Image.open(os.path.join(P, f)).convert('RGB'), dtype=np.int16)
def diff(a, b):
    x, y = arr(a), arr(b)
    if x.shape != y.shape: return f'shapes differ {x.shape} vs {y.shape}'
    return (round(float(np.abs(x-y).mean()), 2), round(float((np.abs(x-y).max(axis=2) > 20).mean())*100, 1))
print('\n-- diffs fromSurface=false --')
print('printemps vs automne:', diff('fs_printemps.png', 'fs_automne.png'))
print('ete vs hiver        :', diff('fs_ete.png', 'fs_hiver.png'))
print('printemps vs ete    :', diff('fs_printemps.png', 'fs_ete.png'))
