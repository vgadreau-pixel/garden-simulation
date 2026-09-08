#!/usr/bin/env python3
"""Diagnostic caméra : position/orientation réelles après mes réglages FPS."""
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

# État actuel
print('mode:', eval_js('window.__jardin.modeCamera'))
print('cam orbitale:', eval_js('JSON.stringify(window.__jardin.camera || null) && (function(){const c = window.__jardin.camera; return c ? JSON.stringify({p: c.position.toArray().map(v=>+v.toFixed(2)), look: c.getWorldDirection ? "dir" : "?"}) : "pas expose"})()'))
print('fps pos:', eval_js('JSON.stringify(window.__jardin.fps.position.toArray().map(v=>+v.toFixed(2)))'))
print('instances:', eval_js('window.__jardin.jardin.instances.length'))
# Distribution des positions des instances (où sont les plantes ?)
print('positions:', eval_js('JSON.stringify(window.__jardin.jardin.instances.slice(0,6).map(i=>[+i.group.position.x.toFixed(1), +i.group.position.z.toFixed(1), i.plante.id]))'))
# Limites du terrain
print('terrain:', eval_js('JSON.stringify({minX: window.__jardin.fps.minX, maxX: window.__jardin.fps.maxX, minZ: window.__jardin.fps.minZ, maxZ: window.__jardin.fps.maxZ})'))
