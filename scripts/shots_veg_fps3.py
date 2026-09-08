#!/usr/bin/env python3
"""Vue FPS : cherche une position avec les arbres bien visibles, capture 3 angles."""
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

    # Où sont les plantes ?
    info = eval_js('''(() => {
      const J = window.__jardin;
      const inst = J.jardin.instances.filter(x => x.vegActif).slice(0, 5);
      return JSON.stringify(inst.map(i => ({ id: i.plante.id, p: i.group.position.toArray().map(v=>+v.toFixed(1)) })));
    })()''')
    print('plantes (5 premières):', info)
    bornes = eval_js('''(() => {
      const box = new (window.__jardin.scene.children[0].constructor)(); // fallback
      return "skip";
    })()''')
    # Position joueur : au sud (z+), regard vers le nord (z-) où sont les plantes
    r = eval_js('''(() => {
      const J = window.__jardin;
      const cam = J.fpsCamera;
      // Centre du jardin : moyenne des positions
      let cx = 0, cz = 0, n = 0;
      for (const i of J.jardin.instances) { cx += i.group.position.x; cz += i.group.position.z; n++; }
      cx /= n; cz /= n;
      cam.position.set(cx, 1.7, cz + 14);
      cam.lookAt(cx, 3, cz);
      return JSON.stringify({ joueur: [cx, 1.7, cz + 14].map(v=>+v.toFixed(1)), cible: [cx, 3, cz].map(v=>+v.toFixed(1)) });
    })()''')
    print('placement:', r)
    time.sleep(0.5)
    shot('veg_fps_vue1.png')

    # Rotation : yaw 180° (regarde derrière)
    r2 = eval_js('''(() => {
      const cam = window.__jardin.fpsCamera;
      cam.position.set(0, 1.7, 20);
      cam.lookAt(0, 2.0, 0);
      return 'ok';
    })()''')
    time.sleep(0.5)
    shot('veg_fps_vue2.png')

if __name__ == '__main__':
    main()
