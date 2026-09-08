#!/usr/bin/env python3
"""Diagnostic WebGL/rendu sous Chrome headless."""
import json, time, sys, base64
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_44f07608/scripts')
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable')
ws.call('Runtime.enable')
ws.call('Page.navigate', url='http://localhost:4173/')
time.sleep(4)
ws.drain(0.5)

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

print('webgl:', eval_js('!!(document.getElementById("app").getContext("webgl2")||document.getElementById("app").getContext("webgl"))'))
print('renderer:', eval_js('(() => { const c=document.getElementById("app"); const g=c.getContext("webgl2")||c.getContext("webgl"); const ext=g.getExtension("WEBGL_debug_renderer_info"); return ext ? g.getParameter(ext.UNMASKED_RENDERER_WEBGL) : "n/a"; })()'))
print('fps hud:', eval_js('document.getElementById("fps").textContent'))
print('nb instances:', eval_js('window.__jardin.instances.length'))
print('visible feuilles:', eval_js('window.__jardin.instances.filter(i=>i.parties.feuilles.visible).length'))
print('scale inst0:', eval_js('window.__jardin.instances[0].group.scale.x'))
print('pos inst0:', eval_js('JSON.stringify(window.__jardin.instances[0].group.position)'))
print('etat inst0:', eval_js('JSON.stringify({stade: window.__jardin.instances[0].dernierEtat.stade, masse: window.__jardin.instances[0].dernierEtat.masseFoliaire, couleur: "#"+window.__jardin.instances[0].dernierEtat.couleur.getHexString()})'))
print('camera zoom/pos:', eval_js('(()=>{const s=window.__jardin.scene; const out=[]; s.traverse(o=>{if(o.isCamera) out.push({z:o.zoom, p:[o.position.x,o.position.y,o.position.z].map(v=>+v.toFixed(1))})}); return JSON.stringify(out)})()'))
