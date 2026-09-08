#!/usr/bin/env python3
"""Diagnostic page blanche sur le Chrome GPU : que dit la console ?"""
import json
import subprocess
import time
import os
import sys
import urllib.request

PORT = 9350
PROFILE = '/tmp/chrome-veg-gpu2'


def wait_debug(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            return json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('Chrome pas prêt')


def main():
    cmd = [
        'google-chrome', '--headless=new',
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={PROFILE}',
        '--no-first-run', '--no-sandbox',
        '--use-gl=angle', '--use-angle=gl', '--enable-gpu',
        '--window-size=1400,800',
        'about:blank',
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tabs = wait_debug(PORT)
        page = [t for t in tabs if t['type'] == 'page'][0]
        sys.path.insert(0, os.path.dirname(__file__))
        from verify_cdp import WS
        ws = WS(page['webSocketDebuggerUrl'])
        ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable')
        ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
        time.sleep(12)
        evts = ws.drain(2.0)
        for e in evts:
            m = e.get('method', '')
            if m == 'Runtime.consoleAPICalled':
                txt = ' '.join(str(a.get('value', a.get('description', '')))[:150] for a in e['params'].get('args', []))
                print(f"[console.{e['params'].get('type')}] {txt[:250]}")
            elif m == 'Runtime.exceptionThrown':
                det = e['params']['exceptionDetails']
                print(f"[exception] {json.dumps(det)[:300]}")
            elif m == 'Log.entryAdded':
                en = e['params']['entry']
                print(f"[log.{en.get('level')}] {en.get('text', '')[:250]}")
        r = ws.call('Runtime.evaluate', expression='JSON.stringify({title: document.title, jardin: !!window.__jardin, body: document.body?.innerHTML.length})', returnByValue=True)
        print('etat:', json.dumps(r.get('result', {}).get('value')))
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()


if __name__ == '__main__':
    main()
