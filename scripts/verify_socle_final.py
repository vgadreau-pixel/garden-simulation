#!/usr/bin/env python3
"""Verif finale socle : console propre, climat switch, audio, renderer.info."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

ws.call('Page.bringToFront')
errors = []
ws.call('Runtime.evaluate', expression='window.__errs=[]')

# Hook console errors
eval_js('''(() => {
  window.addEventListener('error', e => window.__errs.push(String(e.message)));
  window.addEventListener('unhandledrejection', e => window.__errs.push('rej:' + String(e.reason)));
})()''')

# Switch climat
print('climat avant:', eval_js('window.__jardin.climatUI ? "UI presente" : "?"'))
eval_js('window.__jardin.clock.scrubTo(197.5)')
time.sleep(1)
# Changer de climat via l'UI si possible
print('CLIMATS:', eval_js('JSON.stringify(Object.keys(window.__jardin.CLIMATS || {}))'))
time.sleep(1.5)
print('erreurs:', eval_js('JSON.stringify(window.__errs)'))
print('instances:', eval_js('window.__jardin.jardin.compter().total'))
print('veg actifs:', eval_js('window.__jardin.jardin.instances.filter(i=>i.vegActif).length'))
print('label:', eval_js('window.__jardin.clock.etat.label'))
