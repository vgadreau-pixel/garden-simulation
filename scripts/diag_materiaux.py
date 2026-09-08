#!/usr/bin/env python3
"""Diag matériaux du modèle GLTF : opacité, visible, nom, échelle des meshes feuilles."""
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

    res = eval_js('''(() => {
  const J = window.__jardin;
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  if (!cer) return 'pas de cerisier actif';
  const veg = cer.veg;
  const out = { nLeafMats: veg.leafMats.length, nLeafMeshes: veg.leafMeshes.length, meshes: [] };
  for (const rec of veg.leafMeshes.slice(0, 4)) {
    const m = rec.mesh;
    out.meshes.push({
      nom: m.material?.name || '?',
      visible: m.visible,
      opacite: m.material?.opacity,
      transparent: m.material?.transparent,
      echelle: +m.scale.x.toFixed(3),
      echelleBase: rec.base ? +rec.base.x.toFixed(3) : null,
      mondeEchelle: (() => { m.updateWorldMatrix(true, false); return +m.matrixWorld.elements[0].toFixed(4); })(),
    });
  }
  // groupe veg échelle + instance échelle
  out.vegGroupeEchelle = +veg.groupe.scale.x.toFixed(3);
  out.instanceEchelle = +cer.group.scale.x.toFixed(3);
  out.dernierEtatMasse = cer.dernierEtat ? +cer.dernierEtat.masseFoliaire.toFixed(2) : null;
  return JSON.stringify(out);
})()''')
    print('materiaux cerisier:', res)

    # Taille monde du modèle : via Box3 de three exposé par la scène
    box = eval_js('''(() => {
  const J = window.__jardin;
  const cer = J.jardin.instances.find(x => x.plante.id === 'cerisier' && x.vegActif);
  let minY = 1e9, maxY = -1e9;
  cer.group.traverse(o => {
    if (o.isMesh && o.visible) {
      o.updateWorldMatrix(true, false);
      o.geometry.computeBoundingBox();
      const gb = o.geometry.boundingBox;
      const corners = [
        [gb.min.x, gb.min.y, gb.min.z], [gb.max.x, gb.max.y, gb.max.z],
        [gb.min.x, gb.max.y, gb.min.z], [gb.max.x, gb.min.y, gb.max.z],
      ];
      for (const c of corners) {
        const v = new (o.position.constructor)(c[0], c[1], c[2]);
        v.applyMatrix4(o.matrixWorld);
        minY = Math.min(minY, v.y); maxY = Math.max(maxY, v.y);
      }
    }
  });
  return JSON.stringify({ hauteurMonde: +(maxY - minY).toFixed(2), maxY: +maxY.toFixed(2) });
})()''')
    print('taille monde cerisier:', box)

if __name__ == '__main__':
    main()
