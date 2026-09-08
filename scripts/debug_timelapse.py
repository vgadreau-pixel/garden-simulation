#!/usr/bin/env python3
# Time-lapse ciblé : mesure les jours parcourus SANS poller CDP pendant la course.
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

# Accélérer le temps PUIS attendre 12 s sans toucher au protocole
print('speed:', ev('window.__jardin.clock.setSpeed("mois")'))
j0 = ev('window.__jardin.clock.jours')
t0 = time.time()
time.sleep(12.0)
j1 = ev('window.__jardin.clock.jours')
dt = time.time() - t0
parcourus = (j1 - j0) % 365
print(f'jours parcourus en {dt:.1f}s: {parcourus:.1f} (attendu ~{30*dt:.0f})')
print('audio:', ev('window.__jardin.audio.isPlaying()'))
# repasse en pause pour la suite
print(ev('window.__jardin.clock.setSpeed("pause")'))
