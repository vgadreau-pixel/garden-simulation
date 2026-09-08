#!/usr/bin/env python3
"""Diagnostic ciblé : eclat météo, renderer WebGL, état HDRI, uniforms ciel."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    print('gl:', eval_js('''(()=>{const c=document.createElement('canvas');const g=c.getContext('webgl');const e=g.getExtension('WEBGL_debug_renderer_info');return e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER)})()'''))
    print('meteo_ete:', eval_js('''(()=>{const {meteoDuJour}=window.__jardinMeteo||{};return 'noop'})()'''))
    # eclat via l'app : exposer ? On recalcule via import dynamique.
    print('meteo:', eval_js('''(async()=>{const m=await import('/src/climate.js');const j=meteoDuJourSafe();function meteoDuJourSafe(){return null}return JSON.stringify(m.meteoDuJour('tempre',181))})()''') if False else eval_js('''(async()=>{const m=await import('/src/climate.js');return JSON.stringify({ete181:m.meteoDuJour('tempre',181), hiver354:m.meteoDuJour('tempre',354)})})()'''))
    print('env:', eval_js('!!window.__jardin.scene.environment'))
    # re-tentative de chargement HDRI avec log d'erreur
    print('hdri_retry:', eval_js('''(async()=>{const {RGBELoader}=await import('/node_modules/three/examples/jsm/loaders/RGBELoader.js');return new Promise(res=>{new RGBELoader().load('/hdri/kloppenheim_02_1k.hdr',t=>{window.__jardin.scene.environment=t;t.mapping=301;res('OK '+t.image.width+'x'+t.image.height)},undefined,e=>res('ERR '+String(e)))})})()'''))
    time.sleep(2)
    print('env_apres:', eval_js('!!window.__jardin.scene.environment'))

if __name__ == '__main__':
    main()
