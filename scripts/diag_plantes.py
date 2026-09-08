#!/usr/bin/env python3
"""Diagnostic : pourquoi les 23 plantes ne se voient pas après reload ?"""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', str(r['exceptionDetails'])[:500])
        return r['result'].get('value')

    print(eval_js('''(() => {
      const j = window.__jardin.jardin;
      const insts = j.instances.slice(0, 8).map(i => ({
        p: i.parcelle, esp: i.especeId || i.espece, mat: +i.maturite.toFixed(3),
        scale: i.mesh ? +i.mesh.scale.x.toFixed(3) : null,
        visible: i.mesh ? i.mesh.visible : null,
        pos: i.mesh ? i.mesh.position.toArray().map(v=>+v.toFixed(1)) : null
      }));
      return JSON.stringify({n: j.instances.length, echantillon: insts,
        sceneEnfants: window.__jardin.scene.children.length});
    })()'''))
    print('etatPlante exemple:', eval_js('''(() => {
      const c = window.__jardin.clock;
      return JSON.stringify({jours: +c.jours.toFixed(2), instancesClock: c.instances.length});
    })()'''))

if __name__ == '__main__':
    main()
