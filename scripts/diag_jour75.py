#!/usr/bin/env python3
"""Debug jour 75 : pourquoi le rendu ressemble à une grille 2D alors que le
protocole est identique à l'été ? Vérifier état complet : soleil, saison,
couleur du dôme, position caméra, et surtout — comparer les pixels."""
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

print('etat:', ev('JSON.stringify({saison:window.__jardin.clock.etat.saison, jours:+window.__jardin.clock.jours.toFixed(2), mode:window.__jardin.modeCamera, camPos:[+window.__jardin.fpsCamera.position.x.toFixed(1),+window.__jardin.fpsCamera.position.y.toFixed(1),+window.__jardin.fpsCamera.position.z.toFixed(1)]})'))
print('sun:', ev('(()=>{const s=window.__jardin.scene.children.find(o=>o.isDirectionalLight);return JSON.stringify({pos:[+s.position.x.toFixed(0),+s.position.y.toFixed(0),+s.position.z.toFixed(0)],i:+s.intensity.toFixed(2)})})()'))
print('fog:', ev('(()=>{const f=window.__jardin.scene.fog;return JSON.stringify({d:+f.density.toFixed(4), c:"#"+f.color.getHexString()})})()'))
print('hemi:', ev('(()=>{const h=window.__jardin.scene.children.find(o=>o.isHemisphereLight);return +h.intensity.toFixed(2)})()'))
