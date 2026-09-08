#!/usr/bin/env python3
"""Diag profondeur : distance joueur-arbres, brouillard, visibility feuilles."""
import json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    diag = eval_js('''(() => {
  const J = window.__jardin;
  const out = {};
  // Brouillard ?
  out.fog = J.scene.fog ? { type: J.scene.fog.constructor.name, density: J.scene.fog.density, near: J.scene.fog.near, far: J.scene.fog.far } : null;
  // Groupe plantes visible ?
  const g = J.jardin.group;
  out.groupeVisible = g.visible;
  out.enfants = g.children.length;
  // 1er cerisier : visible ? positions mondiales ?
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  if (cer) {
    const p = new (cer.group.position.constructor)();
    cer.group.getWorldPosition(p);
    out.cerisier = { monde: p.toArray().map(v=>+v.toFixed(1)), vegVisible: cer.veg.groupe.visible,
      feuillesEchelle: +cer.veg.leafMeshes[0].mesh.scale.x.toFixed(3),
      distJoueur: Math.hypot(p.x - J.fps.position.x, p.z - J.fps.position.z).toFixed(1) };
  }
  // Taille monde du modèle GLTF
  if (cer) {
    const box = new (window.__jardin.scene.children[0].position.constructor) ? null : null;
  }
  return JSON.stringify(out);
})()''')
    print('diag:', diag)

    # Bounding box du cerisier
    box = eval_js('''(() => {
  const J = window.__jardin;
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  if (!cer) return 'n/a';
  const b = new (cer.group.children[0].geometry ? require : Object) ? null : null;
  // Utilise Box3 via THREE exposé ? Non — calcule via vertices monde
  let minY = 1e9, maxY = -1e9, minX = 1e9, maxX = -1e9;
  cer.group.traverse(o => {
    if (o.isMesh) {
      o.updateWorldMatrix(true, false);
      const gb = o.geometry.boundingBox;
      if (gb) {
        const v = gb.min.clone ? gb.min : null;
        // min/max monde approx via boundingBox transformée
        const m = o.matrixWorld;
        for (const corner of [[gb.min.x, gb.min.y, gb.min.z],[gb.max.x, gb.max.y, gb.max.z]]) {
          const p = new (o.position.constructor)(corner[0], corner[1], corner[2]).applyMatrix4(m);
          minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
          minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
        }
      }
    }
  });
  return JSON.stringify({ minY: +minY.toFixed(2), maxY: +maxY.toFixed(2), minX: +minX.toFixed(2), maxX: +maxX.toFixed(2) });
})()''')
    print('bbox cerisier:', box)

if __name__ == '__main__':
    main()
