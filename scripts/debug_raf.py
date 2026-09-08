#!/usr/bin/env python3
# Mesure du temps de rendu GPU/CPU par frame via performance du renderer :
# on chronomètre renderer.info render calls + triangles pour évaluer la charge.
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

# Pas d'accès direct au renderer… mais on peut estimer via les infos exposées
# par le HUD fps et le nombre d'objets. Le renderer n'est pas dans __jardin —
# on peut quand même mesurer le temps CPU de la boucle via un hook rAF.
print(ev('''(function(){
  // chronomètre le temps passé entre rAF successifs côté JS (hors GPU)
  const deltas = [];
  let last = performance.now();
  return new Promise(res=>{
    let n=0;
    const f=()=>{
      const now=performance.now();
      deltas.push(now-last); last=now;
      if(++n<30) requestAnimationFrame(f);
      else {
        deltas.sort((a,b)=>a-b);
        res(JSON.stringify({
          mediane_ms: deltas[15].toFixed(1),
          p90_ms: deltas[27].toFixed(1),
          fps_effectif: Math.round(1000/(deltas.reduce((a,b)=>a+b,0)/30))
        }));
      }
    };
    requestAnimationFrame(f);
  });
})()'''))
