#!/usr/bin/env python3
"""Printemps : deux tentatives, deux captures grises/2D alors qu'été/automne/
hiver passent avec le même protocole. Hypothèse restante : le localStorage du
navigateur contient un plan sauvegardé, et au jour 75 les plantes existantes
sont en repousse (masse foliaire faible) — non : l'été montre les mêmes plantes
en feuillage. AUTRE hypothèse : au jour 75 (mi-mars→avril), l'heure solaire
10h a une azimut différent... Peu importe : essayer jour 105 (15 avril,
plein printemps) et jour 90 (1er avril, état initial). Capturer les deux,
garder la meilleure."""
import json, time, sys, os, base64, urllib.request
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

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

# On est encore en jour 75 (v10). Scrub vers 105 (mi-avril, printemps établi)
ev('window.__jardin.clock.scrubTo(105 + 10/24)')
time.sleep(20)
print('jours:', ev('window.__jardin.clock.jours'), ev('window.__jardin.clock.etat.saison'))
shot('onirique_printemps_j105.png')
