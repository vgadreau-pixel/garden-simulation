#!/usr/bin/env python3
"""Capture 4 saisons via Chrome headless ÉPHÉMÈRE piloté en CDP (port libre).
Contourne totalement la fenêtre Xvfb occluse du Chrome 9335."""
import json, time, os, base64, socket, subprocess, sys, urllib.request, hashlib

sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

OUT = os.path.join(os.path.dirname(__file__), '..', 'preuves')
PORT = 9341

# 1. Lancer un Chrome headless éphémère
proc = subprocess.Popen([
    'google-chrome', '--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
    f'--remote-debugging-port={PORT}', '--user-data-dir=/tmp/jardin-chrome-profil',
    '--window-size=1280,720', '--hide-scrollbars', 'about:blank',
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json', timeout=1); break
        except Exception:
            time.sleep(0.5)
    tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')
    ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)

    def ev(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', r['exceptionDetails']['exception']['description'][:250])
        return r['result'].get('value')

    def key(code, vk):
        ws.call('Input.dispatchKeyEvent', type='keyDown', code=code, key=code[-1].lower(),
                windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
        time.sleep(0.05)
        ws.call('Input.dispatchKeyEvent', type='keyUp', code=code, key=code[-1].lower(),
                windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        data = base64.b64decode(s['data'])
        open(os.path.join(OUT, nom), 'wb').write(data)
        return hashlib.md5(data).hexdigest()[:10]

    ws.call('Page.navigate', url='http://[::1]:4183/?herbe=4000')
    for _ in range(60):
        if ev('typeof window.__jardin === "object"') is True: break
        time.sleep(1.5)
    time.sleep(6)
    key('KeyV', 86); time.sleep(1.5)
    print('mode:', ev('window.__jardin.modeCamera'))

    noms = []
    for jour, nom in [(105, 'final_printemps_fps'), (258, 'final_automne_fps'),
                      (166, 'final_ete_fps'), (15, 'final_hiver_fps')]:
        ev(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({jour} + 10/24)')
        time.sleep(10)
        print(nom, '| saison:', ev('window.__jardin.clock.etat.saison'),
              '| jours:', round(ev('window.__jardin.clock.jours'), 1))
        shot(nom + '.png'); noms.append(nom + '.png')

    # Vérif pixel immédiate
    import numpy as np
    from PIL import Image
    def arr(f): return np.asarray(Image.open(os.path.join(OUT, f)).convert('RGB'), dtype=np.int16)
    def diff(a, b):
        x, y = arr(a), arr(b)
        return (round(float(np.abs(x-y).mean()), 2), round(float((np.abs(x-y).max(axis=2) > 20).mean())*100, 1))
    print('\n-- diffs --')
    print('printemps vs automne:', diff('final_printemps_fps.png', 'final_automne_fps.png'))
    print('ete vs hiver        :', diff('final_ete_fps.png', 'final_hiver_fps.png'))
    print('printemps vs hiver  :', diff('final_printemps_fps.png', 'final_hiver_fps.png'))
finally:
    proc.terminate()
    try: proc.wait(5)
    except Exception: proc.kill()
