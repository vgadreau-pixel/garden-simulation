#!/usr/bin/env python3
"""Mesure du cout FPS + plantation API + strafe Q (AZERTY) — apres reload propre."""
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Page.navigate', url='http://[::1]:4183/')
time.sleep(6)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', r['exceptionDetails']['exception']['description'][:200])
    return r['result'].get('value')

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def v_key():
    key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp'); time.sleep(0.3)

def raf_fps():
    return ev('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++; if(performance.now()-t0<2000) requestAnimationFrame(f); else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})')

print('charge:', ev('JSON.stringify({mode:window.__jardin.modeCamera, plantes:window.__jardin.jardin.compter().total})'))
ev('window.__jardin.clock.setSpeed("pause")')
print('fps_orbital:', raf_fps())
v_key()
print('mode:', ev('window.__jardin.modeCamera'))
key('KeyW', 87, 'keyDown')
print('fps_fps_marche:', raf_fps())
key('KeyW', 87, 'keyUp')
print('fps_fps_immobile:', raf_fps())

# plantation sur parcelle reellement libre
libre = ev('(()=>{const o=new Set(window.__jardin.jardin.instances.map(i=>i.parcelle)); for(let a=0;a<8;a++)for(let b=0;b<8;b++){if(!o.has(a+","+b))return a+","+b} return null})()')
print('parcelle_libre:', libre)
a, b = (int(v) for v in libre.split(','))
avant = ev('window.__jardin.jardin.compter().total')
ev(f'(()=>{{const r=window.__jardin.jardin.planterParId("tulipe",{a},{b}); return r?("ok:"+r.plante.id):"null"}})()')
apres = ev('window.__jardin.jardin.compter().total')
print(f'plantation_api: {avant} -> {apres}', 'OK' if apres == avant + 1 else 'ECHEC')

# strafe gauche = Q azerty = KeyA physique
ev('window.__jardin.fps.yaw = 0; window.__jardin.fps.updateCamera()')
x0 = ev('window.__jardin.fps.position.x')
key('KeyA', 65, 'keyDown'); time.sleep(1.0); key('KeyA', 65, 'keyUp')
x1 = ev('window.__jardin.fps.position.x')
print(f'strafe_gauche_Q: x {x0:.2f} -> {x1:.2f}', 'OK' if isinstance(x1, float) and x1 < x0 - 1.5 else 'ECHEC')

# course : Shift + W doit aller ~2x plus vite
ev('window.__jardin.fps.position.set(0,1.7,14); window.__jardin.fps.updateCamera()')
z0 = ev('window.__jardin.fps.position.z')
key('ShiftLeft', 16, 'keyDown'); key('KeyW', 87, 'keyDown'); time.sleep(1.0)
key('KeyW', 87, 'keyUp'); key('ShiftLeft', 16, 'keyUp')
z1 = ev('window.__jardin.fps.position.z')
print(f'course_shift: {(z0-z1):.2f} m/s (marche=3.2, course=6.0)', 'OK' if (z0 - z1) > 4 else 'ECHEC')
