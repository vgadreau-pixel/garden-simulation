#!/usr/bin/env python3
"""Vérification de la couche onirique (intégration finale t_47c534e0) :
chargement 0 erreur, herbe instanciée, bassin, particules saisonnières,
rais de lumière, marche FPS, captures 4 saisons."""
import json, time, sys, os, base64, math, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
os.makedirs(PREUVES, exist_ok=True)

PORT = int(os.environ.get('CDP_PORT', '9222'))
tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable')
ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=6000')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:300])
    return r['result'].get('value')

for _ in range(50):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(3)

events = ws.drain(1.0)
excs = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
console_err = [e for e in events if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
log_err = [e for e in events if e.get('method') == 'Log.entryAdded' and e['params'].get('entry', {}).get('level') == 'error']
print('erreurs chargement:', len(excs) + len(console_err) + len(log_err))
for e in (excs + console_err + log_err)[:6]:
    print('  ', json.dumps(e.get('params', {}))[:220])

# État de la couche onirique
print('onirique:', ev('JSON.stringify({brins: window.__jardin?.onirique?.infos?.brins, bassin: window.__jardin?.onirique?.infos?.bassin})'))
print('scene_check:', ev('JSON.stringify((()=>{const s=window.__jardin.scene;let herbe=0,eau=0,points=0,rais=0;s.traverse(o=>{if(o.isInstancedMesh)herbe++;if(o.material&&o.material.uniforms&&o.material.uniforms.uTemps&&o.isMesh&&!o.isInstancedMesh)eau++;if(o.isPoints&&o.material.uniforms)points++;});return {herbe,eau,points,instancesPlantes:s.children.filter(c=>c.type==="Group").length}})())'))

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def v_key():
    key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp'); time.sleep(0.4)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

def set_saison(jour, heure=10.0):
    ev(f'window.__jardin.clock.jours = {jour} + {heure}/24; window.__jardin.clock.paused = false;')

def entre_fps(pos, yaw=2.6, pitch=0.05):
    v_key()
    print(' mode:', ev('window.__jardin.modeCamera'))
    ev(f'window.__jardin.fps.position.set({pos[0]},1.7,{pos[1]}); window.__jardin.fps.yaw={yaw}; window.__jardin.fps.pitch={pitch}; window.__jardin.fps.updateCamera()')
    time.sleep(0.8)

# Vérifier la marche + collision bassin
entre_fps((-16, 16), 2.6, 0.0)
z0 = ev('JSON.stringify({x:+window.__jardin.fps.position.x.toFixed(2),z:+window.__jardin.fps.position.z.toFixed(2)})')
# marche plein ouest (vers le bassin à -20.3,20.3) : yaw tel que forward = -x
ev('window.__jardin.fps.yaw=-1.5708; window.__jardin.fps.updateCamera()')
key('KeyW', 87, 'keyDown'); time.sleep(2.5); key('KeyW', 87, 'keyUp')
p = json.loads(ev('JSON.stringify({x:+window.__jardin.fps.position.x.toFixed(2),z:+window.__jardin.fps.position.z.toFixed(2)})'))
d_bassin = math.hypot(p['x'] + 20.3, p['z'] - 20.3)
print(f"apres marche ouest: {p} — distance au centre bassin: {d_bassin:.2f} m", 'OK (bassin solide)' if d_bassin > 3.0 else 'TRAVERSE!')

# ── Captures 4 saisons (vue FPS depuis l'allée sud) ──
SAISONS = [('printemps', 75, 'onirique_printemps'), ('ete', 166, 'onirique_ete'),
           ('automne', 258, 'onirique_automne'), ('hiver', 15, 'onirique_hiver')]
for saison, jour, nom in SAISONS:
    set_saison(jour, 10.0)
    time.sleep(1.5)
    entre_fps((-14, 17.5), 2.35, 0.06)  # regard vers le jardin + coin bassin
    time.sleep(0.8)
    shot(nom + '_fps.png')
    # vue orbital pour la lisibilité du terrain
    v_key()
    time.sleep(0.6)
    shot(nom + '_dessus.png')

# Golden hour été + rais de lumière + lucioles le soir d'été
set_saison(166, 18.6)
time.sleep(1.5)
entre_fps((-14, 17.5), 2.35, 0.05)
time.sleep(0.8)
shot('onirique_ete_golden_fps.png')
print('rais:', ev('window.__jardin.onirique.infos.raisVisibles'))
set_saison(166, 22.5)
time.sleep(1.5)
shot('onirique_ete_nuit_fps.png')
print('lucioles:', ev('JSON.stringify(window.__jardin.onirique.infos.particules.lucioles.points.visible)'))

# Retour au socle : orbital + plantation fonctionne toujours
if ev('window.__jardin.modeCamera') != 'orbital':
    v_key()
av = ev('window.__jardin.jardin.compter().total')
print('mode final:', ev('window.__jardin.modeCamera'), '| plantes:', av)
fps_hud = ev('document.getElementById("fps")?.textContent')
print('hud fps:', fps_hud)
print('VERIF TERMINEE')
