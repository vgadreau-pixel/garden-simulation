#!/usr/bin/env python3
# Profiling fin avec appliquerEtat exposé + nouveau chargement de page.
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.navigate', url='http://localhost:4183/')
time.sleep(5); ws.drain(0.5)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

# Remplir le jardin à ~40 plantes
print(ev('''(function(){
  const j=window.__jardin.jardin;
  const ids=["cerisier","erable_japonais","sapin","pommier","lavande","rosier","tulipe","coquelicot","marguerite","tomate","carotte","bouleau"];
  for(let iz=0;iz<8;iz++)for(let ix=0;ix<8;ix++){
    if(j.compter().total>=40)break;
    j.planterParId(ids[(ix+iz*3)%ids.length],ix,iz);
  }
  return 'total:'+j.compter().total;
})()'''))
print('fps:', ev('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})'))

print(ev('''(function(){
  const J=window.__jardin, N=100, t={};
  const clock=J.clock; clock.setSpeed("pause");
  let t0=performance.now();
  for(let i=0;i<N;i++)clock.tick(416);
  t.tick=+((performance.now()-t0)/N).toFixed(3);
  t0=performance.now();
  for(let i=0;i<N;i++)J.meteo.appliquer({pluie:0,neige:0,brume:0,eclat:0.8,temperature:20},0.016);
  t.meteo=+((performance.now()-t0)/N).toFixed(3);
  t0=performance.now();
  const jours=clock.jours,cl=clock.climat;
  for(let i=0;i<N;i++){for(const inst of J.instances)J.appliquerEtat(inst,jours,cl)}
  t.etat=+((performance.now()-t0)/N).toFixed(3);
  return JSON.stringify({par_frame_ms:t, plantes:J.instances.length});
})()'''))
