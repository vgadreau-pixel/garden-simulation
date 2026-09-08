#!/usr/bin/env python3
"""Diagnostic : pourquoi les plantes ne sont pas visibles ? État des instances."""
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')

    def ev(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    print('instances:', ev('JSON.stringify(window.__jardin.jardin.instances.map(i=>({p:i.parcelle, pos:[+i.group.position.x.toFixed(1),+i.group.position.z.toFixed(1)], scale:+i.group.scale.x.toFixed(2), visible:i.group.visible, inScene:!!i.group.parent})))')[:1500])
    print('clock_instances_nb:', ev('window.__jardin.clock.instances.length'))
    print('climat:', ev('window.__jardin.clock.climat'))
    print('climatUI:', ev('window.__jardin.climatUI.climat'))
    # Les plantes de démo ont-elles été plantées avant la restauration ?
    print('camera:', ev('JSON.stringify({x:0,z:0})'))
    # état plante d'une instance
    print('etat0:', ev('(()=>{const i=window.__jardin.jardin.instances[0];const e=i.dernierEtat;return JSON.stringify({stade:e?.stade, masse:+(e?.masseFolaire||e?.masseFoliaire||0).toFixed(2), feuillesVis:i.parties.feuilles.visible})})()'))

if __name__ == '__main__':
    main()
