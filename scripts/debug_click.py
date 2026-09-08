#!/usr/bin/env python3
# Debug plantation au clic : les events souris arrivent-ils sur le canvas ?
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

def clic(x, y, bouton='left'):
    for t in ('mousePressed', 'mouseReleased'):
        ws.call('Input.dispatchMouseEvent', type=t, x=x, y=y, button=bouton, clickCount=1)

print('total:', ev('window.__jardin.jardin.compter().total'))
# Installe des compteurs d'événements sur le canvas
print(ev('''(function(){
  let down=0, up=0, move=0;
  const c=document.getElementById('app');
  c.addEventListener('pointerdown',()=>down++,true);
  c.addEventListener('pointerup',()=>up++,true);
  c.addEventListener('pointermove',()=>move++,true);
  window.__evt=()=>({down,up,move});
  return 'ok';
})()'''))

# Parcelle libre (6,1) → monde (11.04, -11.5) ; échelle test
vp = json.loads(ev('JSON.stringify({w:innerWidth,h:innerHeight})'))
ech = vp['h']/60.0
def w2px(x,z): return vp['w']/2+x*ech, vp['h']/2+z*ech
sx, sy = w2px((6-3.5)*4.6, (1-3.5)*4.6)
print('cible px:', sx, sy, 'element dessus:', ev(f'(()=>{{const e=document.elementFromPoint({sx},{sy});return e?e.id||e.tagName:"?"}})()'))
clic(sx, sy); time.sleep(0.3)
print('events:', ev('JSON.stringify(window.__evt())'))
print('total apres:', ev('window.__jardin.jardin.compter().total'))
# Test direct : forcer la sélection iris puis planter via API
print('espece courante:', ev('window.__jardin.jardin.especeSelectionnee'))
