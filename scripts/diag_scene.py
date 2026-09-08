#!/usr/bin/env python3
"""Trouve le dôme : traverse complet avec types."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

JS = """(function(){
  try {
    const scene = window.__jardin.scene;
    const types = [];
    scene.traverse(function(o){
      types.push((o.type||'?') + ':' + (o.geometry ? o.geometry.type : '-') + ':' + (o.material ? (o.material.type + (o.material.uniforms?'(uniforms)':'')) : '-'));
    });
    return JSON.stringify(types);
  } catch(e) { return 'ERR ' + e.message; }
})()"""

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9345/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')
    r = ws.call('Runtime.evaluate', expression=JS, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'): print('EXC', str(r['exceptionDetails'])[:300]); return
    types = json.loads(r['result']['value'])
    for t in types: print(t)

if __name__ == '__main__':
    main()
