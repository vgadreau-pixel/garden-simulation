#!/usr/bin/env python3
"""Diagnostic : le canvas readPixels renvoie-t-il toujours la même chose ?
Teste aussi la comparaison via screenshots PNG."""
import json, time, sys, base64, hashlib
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_44f07608/scripts')
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable')
ws.call('Page.navigate', url='http://localhost:4173/')
time.sleep(4)
ws.drain(0.3)

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

def canvas_hash():
    return eval_js('(()=>{const c=document.getElementById("app");const g=c.getContext("webgl2")||c.getContext("webgl");const p=new Uint8Array(4*g.drawingBufferWidth*g.drawingBufferHeight);g.readPixels(0,0,g.drawingBufferWidth,g.drawingBufferHeight,g.RGBA,g.UNSIGNED_BYTE,p);let h=0;for(let i=0;i<p.length;i+=37)h=((h*31)+p[i])>>>0;return h})()')

def png_hash():
    s = ws.call('Page.captureScreenshot', format='png')
    return hashlib.md5(s['data'].encode()).hexdigest()[:10]

# test : deux captures à 1s d'intervalle sans rien changer (fps change → hash devrait bouger ?)
print('a: canvas', canvas_hash(), 'png', png_hash())
time.sleep(1.0)
print('b: canvas', canvas_hash(), 'png', png_hash())

# scrub hiver
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(10);')
time.sleep(0.8)
print('hiver: canvas', canvas_hash(), 'png', png_hash())

# scrub été
eval_js('window.__jardin.clock.scrubTo(195);')
time.sleep(0.8)
print('ete: canvas', canvas_hash(), 'png', png_hash())
