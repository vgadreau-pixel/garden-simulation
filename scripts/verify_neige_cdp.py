#!/usr/bin/env python3
"""Complément : neige en continental en hiver + captures comparatives (v2).

Change les climats UNIQUEMENT via clock.setClimat + reclic du bouton,
puis vérifie l'état des particules en relisant le champ `visible` réel.
"""
import json, time, base64, sys
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_d316b27d/scripts')
from verify_cdp import WS
import urllib.request

OUT = '/home/vgadreau/.hermes/kanban/workspaces/t_d316b27d/preuves'
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Page.navigate', url='http://localhost:4173/')
time.sleep(4)
ws.drain(0.5)

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

def shot(name):
    s = ws.call('Page.captureScreenshot', format='png')
    open(f'{OUT}/{name}.png', 'wb').write(base64.b64decode(s['data']))
    print('   capture:', name)

def choisir_climat(cid):
    """Change le climat via l'API (source de vérité) + clic bouton (UI)."""
    eval_js(f'window.__jardin.clock.setClimat("{cid}");')
    eval_js(f'(()=>{{const b=[...document.querySelectorAll(".cbtn")].find(b=>b.dataset.climat==="{cid}"); if(b) b.click();}})()')
    time.sleep(1.5)

def etat_meteo():
    return eval_js('''JSON.stringify({
      pluie: !!document.querySelector('#app') && window.__jardin.meteo.etat().pluieVisible,
      neige: window.__jardin.meteo.etat().neigeVisible,
      brume: window.__jardin.meteo.etat().brumeVisible,
      opNeige: window.__jardin.meteo.etat().opaciteNeige,
    })''')

# Mi-janvier (hiver profond), pause.
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(15.5);')

# Vérifie l'exposition CDP.
print('expose:', eval_js('Object.keys(window.__jardin).join(",")'))

for cid in ['tempre', 'continental', 'mediterraneen', 'aride']:
    choisir_climat(cid)
    e = etat_meteo()
    print(f'hiver {cid}: {e}')
    shot(f'hiver_{cid}')

# Assertions finales : neige en continental, pas de neige méditerranéen/aride.
choisir_climat('continental')
assert eval_js('window.__jardin.meteo.etat().neigeVisible') is True, 'neige attendue en continental/hiver'
choisir_climat('mediterraneen')
assert eval_js('window.__jardin.meteo.etat().neigeVisible') is False, 'pas de neige en méditerranéen'
choisir_climat('aride')
assert eval_js('window.__jardin.meteo.etat().neigeVisible') is False, 'pas de neige en aride'
print('OK: neige en continental (hiver) uniquement, aucune en méditerranéen/aride')
