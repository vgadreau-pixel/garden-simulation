#!/usr/bin/env python3
"""Re-verification finale sur l'etat FUSIONNE (FPS 2/3 + sky 3/3) :
chargement propre, bascule V, marche, collision, retour orbital, capture."""
import json, time, sys, os, base64, math
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable')
ws.call('Page.navigate', url='http://[::1]:4183/')
# Attendre que le module principal soit pret (l'HDRI 1,7 Mo peut etre long en SwiftShader)
def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', r['exceptionDetails']['exception']['description'][:200])
    return r['result'].get('value')

for _ in range(40):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(2)
events = ws.drain(1.0)
errs = [e for e in events if e.get('method') in ('Runtime.exceptionThrown',
        'Log.entryAdded') and e.get('params', {}).get('entry', {}).get('level') == 'error']
excs = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
console_err = [e for e in events if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
print('erreurs chargement:', len(errs) + len(excs) + len(console_err))
for e in (excs + console_err)[:5]:
    print('  ', json.dumps(e.get('params', {}))[:250])

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def v_key():
    key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp'); time.sleep(0.3)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

print('charge:', ev('JSON.stringify({mode:window.__jardin?.modeCamera, plantes:window.__jardin?.jardin?.compter().total, hudfps:document.getElementById("fps")?.textContent})'))

v_key()
print('fps_mode:', ev('window.__jardin.modeCamera'))
ev('window.__jardin.fps.yaw=0; window.__jardin.fps.pitch=0; window.__jardin.fps.updateCamera()')
z0 = ev('window.__jardin.fps.position.z')
key('KeyW', 87, 'keyDown'); time.sleep(1.0); key('KeyW', 87, 'keyUp')
z1 = ev('window.__jardin.fps.position.z')
print(f'marche: z {z0:.2f} -> {z1:.2f}', 'OK' if z1 < z0 - 2 else 'ECHEC')

# collision sur le 1er arbre
pl = json.loads(ev('JSON.stringify((()=>{const i=window.__jardin.jardin.instances;const f=i.find(x=>x.plante.type==="arbre")||i[0];return {x:f.group.position.x,z:f.group.position.z}})())'))
ev(f'window.__jardin.fps.position.set({pl["x"]},1.7,{pl["z"]}+3); window.__jardin.fps.yaw=0; window.__jardin.fps.updateCamera()')
key('KeyW', 87, 'keyDown'); time.sleep(2.0); key('KeyW', 87, 'keyUp')
pf = json.loads(ev('JSON.stringify({x:+window.__jardin.fps.position.x.toFixed(2),z:+window.__jardin.fps.position.z.toFixed(2)})'))
d = math.hypot(pf['x'] - pl['x'], pf['z'] - pl['z'])
print(f'collision_arbre: {d:.2f} m', 'OK' if 0.7 < d < 1.2 else 'ECHEC')

# screenshot FPS sur l'etat fusionne
ev('window.__jardin.fps.position.set(0,1.7,14); window.__jardin.fps.yaw=0.4; window.__jardin.fps.pitch=0.04; window.__jardin.fps.updateCamera()')
time.sleep(0.6)
shot('fps_vue_jardin_fusion.png')

# retour orbital + socle
v_key()
print('retour_orbital:', ev('window.__jardin.modeCamera'))
av = ev('window.__jardin.jardin.compter().total')
libre = ev('(()=>{const o=new Set(window.__jardin.jardin.instances.map(i=>i.parcelle)); for(let a=0;a<8;a++)for(let b=0;b<8;b++){if(!o.has(a+","+b))return a+","+b} return null})()')
a, b = int(libre.split(',')[0]), int(libre.split(',')[1])
ev(f'(()=>{{const r=window.__jardin.jardin.planterParId("tulipe",{a},{b}); return r?"ok":"null"}})()')
ap = ev('window.__jardin.jardin.compter().total')
print(f'plantation_orbital: {av} -> {ap}', 'OK' if ap == av + 1 else 'ECHEC')
shot('retour_orbital_fusion.png')

ev('window.__jardin.clock.setSpeed("jour")')
time.sleep(1.5)
print('horloge_avance:', ev('Math.round(window.__jardin.clock.jours)'))
print('audio_present:', ev('typeof window.__jardin.audio.isPlaying === "function"'))
