#!/usr/bin/env python3
"""Diag caméra FPS : la caméra rend-elle la scène ? (test à différentes hauteurs + angles)"""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')


def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    print('etat horloge:', eval_js('JSON.stringify({jours:+window.__jardin.clock.jours.toFixed(1), pause:window.__jardin.clock.paused})'))
    print('mode:', eval_js('window.__jardin.modeCamera'))

    # Diagnostic : quels objets dans la scène ?
    scene = eval_js('''(() => {
      const J = window.__jardin;
      const compter = (o, acc) => {
        acc.objets++;
        if (o.isMesh) acc.meshes++;
        if (o.visible === false) acc.invisibles++;
        o.children.forEach(c => compter(c, acc));
        return acc;
      };
      return JSON.stringify(compter(J.scene, {objets:0, meshes:0, invisibles:0}));
    })()''')
    print('scene:', scene)

    # Position réelle de fpsCamera vs fps controls
    cams = eval_js('''(() => {
      const J = window.__jardin;
      const c = J.fpsCamera;
      return JSON.stringify({ pos: c.position.toArray().map(v=>+v.toFixed(1)),
        lookAt: c.getWorldDirection(new (c.position.constructor)()).toArray().map(v=>+v.toFixed(2)),
        aspect: c.aspect, fov: c.fov, near: c.near, far: c.far });
    })()''')
    print('fpsCamera:', cams)

    # Le rendu utilise bien fpsCamera en mode fps ? Regarder post.renderPass.camera
    rendu = eval_js('JSON.stringify({renderPassCam: window.__jardin.post ? "expose" : "non expose"})')
    print(rendu)
    # Caméra élevée, regard piquant : voit-on le sol ?
    eval_js('''(() => {
      const cam = window.__jardin.fpsCamera;
      cam.position.set(0, 12, 18);
      cam.lookAt(0, 0, 0);
    })()''')
    time.sleep(1.5)
    shot('diag_fps_haut.png')

if __name__ == '__main__':
    main()
