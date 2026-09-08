#!/usr/bin/env python3
# Debug FPS : charge réelle (jardin plein 30+ plantes) + profiling des coûts.
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
    return r['result'].get('value')

def fps(n=3000):
    return ev(f'''new Promise(res=>{{let n=0;const t0=performance.now();
    const f=()=>{{n++;if(performance.now()-t0<{n})requestAnimationFrame(f);
    else res(Math.round(n*1000/(performance.now()-t0)))}};
    requestAnimationFrame(f)}})''')

print('plantactuel:', ev('window.__jardin.jardin.compter().total'))
print('renderer:', ev('window.__jardin.scene.background ? "ok" : "?"'))

# Charge : planter jusqu'à ~40 plantes sur les parcelles libres
print(ev('''(function(){
  const j=window.__jardin.jardin;
  const ids=["cerisier","erable_japonais","sapin","pommier","lavande","rosier","tulipe","coquelicot","marguerite","tomate","carotte","bouleau"];
  let ajoutes=0;
  for(let iz=0;iz<8;iz++)for(let ix=0;ix<8;ix++){
    if(j.compter().total>=40)break;
    // planter directement (API interne exposée ? planter(ix,iz,plante) via planterParId)
    const r=j.planterParId?j.planterParId(ids[(ix+iz*3)%ids.length],ix,iz):null;
    if(r)ajoutes++;
  }
  return 'ajoutes:'+ajoutes+' total:'+j.compter().total;
})()'''))

# FPS en pause
print('fps_pause_40plantes:', ev('window.__jardin.clock.setSpeed("pause")') or '', fps())

# Mesure du coût par étape de la frame
print(ev('''(function(){
  const t={tick:0,meteo:0,etat:0,lumiere:0,render:0};
  const J=window.__jardin;
  const clock=J.clock;
  const N=60;
  // warmup
  for(let i=0;i<10;i++)J.meteo.appliquer(null,0.016);
  let t0=performance.now();
  for(let i=0;i<N;i++){clock.tick(416)}
  t.tick=performance.now()-t0;
  t0=performance.now();
  for(let i=0;i<N;i++){J.meteo.appliquer({pluie:0,neige:0,brume:0,eclat:0.8,temperature:20},0.016)}
  t.meteo=performance.now()-t0;
  t0=performance.now();
  const jours=clock.jours,cl=clock.climat;
  for(let i=0;i<N;i++){for(const inst of J.instances)window.__appliquerEtat(inst,jours,cl)}
  t.etat=performance.now()-t0;
  return JSON.stringify({par_frame_ms:Object.fromEntries(Object.entries(t).map(([k,v])=>[k,+(v/N).toFixed(2)])), plantes:J.instances.length});
})()''') if ev('typeof window.__appliquerEtat') != 'undefined' else 'appliquerEtat non expose')
