#!/usr/bin/env python3
"""Frustum caméra orbitale (pas dans la scène : cherchons dans __jardin)."""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

JS = """(function(){
  try {
    const J = window.__jardin;
    let out = [];
    // la caméra ortho n'est pas ajoutée à la scène : cherchons via fpsCamera ou exposition
    // on teste les propriétés connues
    const keys = Object.keys(J);
    out.push('keys=' + keys.join(','));
    // renderer exposition via canvas : impossible direct. Estimons via luminosité.
    return JSON.stringify(out);
  } catch(e) { return 'ERR ' + e.message; }
})()"""

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9345/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Runtime.enable')
    r = ws.call('Runtime.evaluate', expression=JS, returnByValue=True, awaitPromise=True)
    print(r['result'].get('value'))

if __name__ == '__main__':
    main()
