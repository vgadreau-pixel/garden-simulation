#!/usr/bin/env python3
# FPS en accéléré : l'horloge avance via requestAnimationFrame, donc les jours
# parcourus dépendent du nb de frames. Mesure fps pendant la course au mois/s.
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

ev('window.__jardin.clock.setSpeed("mois")')
# mesure fps sur 12 s via compteur interne (pas de raf polling bloquant :
# rAF et l'horloge partagent la même boucle, donc le compteur est fidèle)
r = ev('''new Promise(res=>{
  let n=0; const t0=performance.now();
  const f=()=>{n++; if(performance.now()-t0<12000) requestAnimationFrame(f);
    else res(JSON.stringify({frames:n, fps:Math.round(n*12), jours:window.__jardin.clock.jours}))};
  requestAnimationFrame(f)})''')
print('fps pendant mois/s:', r)
# framecount théorique : 12 s à 30 j/s. Frames mesurées * delta * 30
d = json.loads(r) if isinstance(r, str) else {}
print('jours attendus pour', d.get('frames'), 'frames à 30 j/s avec delta 0.25s:',
      d.get('frames', 0) * 0.25 * 30)
