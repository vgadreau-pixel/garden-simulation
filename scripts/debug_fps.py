#!/usr/bin/env python3
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'].get('exception', {}))[:250])
    return r['result'].get('value')

def key(code, vk, typ):
    ws.call('Input.dispatchKeyEvent', type=typ, code=code, key='k',
            windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

print('lock:', ev('document.pointerLockElement ? document.pointerLockElement.id : null'))
print('mode:', ev('window.__jardin.modeCamera'))
# passer en FPS si besoin
if ev('window.__jardin.modeCamera') != 'fps':
    key('KeyV', 86, 'keyDown'); time.sleep(0.05); key('KeyV', 86, 'keyUp'); time.sleep(0.3)
print('mode2:', ev('window.__jardin.modeCamera'), 'lock2:', ev('!!document.pointerLockElement'))

# mousemove CDP remplit-il movementX ?
print('yaw0:', ev('window.__jardin.fps.yaw'))
ws.call('Input.dispatchMouseEvent', type='mouseMoved', x=640, y=400, movementX=200, movementY=0)
time.sleep(0.2)
print('yaw1:', ev('window.__jardin.fps.yaw'))

# collision : test deterministe — teleport a cote de l'arbre, 1 update manuel
print('inst:', ev('JSON.stringify(window.__jardin.jardin.instances.slice(0,3).map(i=>({t:i.plante.type,x:i.group.position.x,z:i.group.position.z})))'))
print('setpos:', ev('window.__jardin.fps.position.set(-2.3,1.7,-1.6); window.__jardin.fps.yaw=0; "ok"'))
# simule 10 pas de 0.1 s vers -z avec update()
print('walk:', ev('''(()=>{const f=window.__jardin.fps; const out=[]; for(let i=0;i<12;i++){f.position.z-=0.32; f.update(0.0001); out.push(+f.position.z.toFixed(2));} return JSON.stringify(out)})()'''))
print('getInstances:', ev('window.__jardin.jardin.instances.length'))
