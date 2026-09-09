#!/usr/bin/env python3
"""Captures via Page.startScreencast (pipeline de présentation réel)."""
import json, time, sys, os, base64, urllib.request, hashlib, socket
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

def screencast_frame(attente_s=10):
    ws.call('Page.startScreencast', format='jpeg', quality=92, everyNthFrame=1)
    ws.sock.settimeout(attente_s)
    try:
        while True:
            m = ws._recv_frame()
            if m.get('method') == 'Page.screencastFrame':
                ws.call('Page.screencastFrameAck', sessionId=m['params']['sessionId'])
                return base64.b64decode(m['params']['data'])
    finally:
        ws.sock.settimeout(30)
        ws.call('Page.stopScreencast')

for jour, nom in [(105, 'sc_printemps'), (258, 'sc_automne'), (166, 'sc_ete'), (15, 'sc_hiver')]:
    ev(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({jour} + 10/24)')
    time.sleep(8)
    saison = ev('window.__jardin.clock.etat.saison')
    data = screencast_frame()
    f = os.path.join(P, nom + '.jpg')
    open(f, 'wb').write(data)
    print(nom, '| saison:', saison, '|', len(data), 'octets | md5:', hashlib.md5(data).hexdigest()[:10])

import numpy as np
from PIL import Image
def arr(f): return np.asarray(Image.open(os.path.join(P, f)).convert('RGB'), dtype=np.int16)
def diff(a, b):
    x, y = arr(a), arr(b)
    if x.shape != y.shape: return 'shapes differ'
    return (round(float(np.abs(x-y).mean()), 2), round(float((np.abs(x-y).max(axis=2) > 20).mean())*100, 1))
print('\n-- diffs screencast --')
print('printemps vs automne:', diff('sc_printemps.jpg', 'sc_automne.jpg'))
print('ete vs hiver        :', diff('sc_ete.jpg', 'sc_hiver.jpg'))
print('printemps vs ete    :', diff('sc_printemps.jpg', 'sc_ete.jpg'))
