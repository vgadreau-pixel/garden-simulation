#!/usr/bin/env python3
"""Uniforms du dôme : première SphereGeometry=ShaderMaterial trouvée."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

JS = """(function(){
  try {
    const scene = window.__jardin.scene;
    let dome=null;
    scene.traverse(function(o){
      if(!dome && o.geometry && o.geometry.type==='SphereGeometry' && o.material && o.material.type==='ShaderMaterial') dome=o;
    });
    if(!dome) return 'pas de dome shader';
    const u = dome.material.uniforms;
    function hex(c){ return '#'+c.getHexString(); }
    return JSON.stringify({
      cHaut: hex(u.cHaut.value), cMilieu: hex(u.cMilieu.value),
      cHorizon: hex(u.cHorizon.value), glow: hex(u.cSoleilGlow.value),
      uGlow: +u.uGlow.value.toFixed(2),
      date: window.__jardin.clock.etat.label,
      fogD: window.__jardin.scene.fog ? +window.__jardin.scene.fog.density.toFixed(5) : null,
      hemiI: (function(){let h=0;scene.traverse(function(o){if(o.isHemisphereLight)h=o.intensity;});return +h.toFixed(2);})(),
      sunI: (function(){let s=0;scene.traverse(function(o){if(o.isDirectionalLight)s=o.intensity;});return +s.toFixed(2);})()
    });
  } catch(e) { return 'ERR ' + e.message; }
})()"""

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9345/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    for nom, j in [('ete_matin', 181.40), ('ete_midi', 181.54), ('ete_crepuscule', 181.93), ('hiver_midi', 354.54)]:
        eval_js(f'window.__jardin.clock.scrubTo({j})')
        time.sleep(0.5)
        print(nom, eval_js(JS))

if __name__ == '__main__':
    main()
