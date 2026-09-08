#!/usr/bin/env python3
"""Perf sur ANGLE/SwiftShader-Vulkan : essaie plusieurs backends ANGLE.
Objectif : obtenir un contexte WebGL plus rapide que le SwiftShader GL 1.0."""
import json
import subprocess
import time
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))


def wait_debug(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            return json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('Chrome pas prêt')


BACKENDS = [
    ('vulkan', ['--use-angle=vulkan', '--enable-unsafe-swiftshader']),
    ('swiftshader-vk', ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']),
]

PORT = 9351
for nom, flags in BACKENDS:
    profil = f'/tmp/chrome-veg-{nom}'
    cmd = [
        'google-chrome', '--headless=new',
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={profil}',
        '--no-first-run', '--no-sandbox',
        '--window-size=1400,800',
    ] + flags + ['about:blank']
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tabs = wait_debug(PORT)
        page = [t for t in tabs if t['type'] == 'page'][0]
        from verify_cdp import WS
        ws = WS(page['webSocketDebuggerUrl'])
        ws.call('Page.enable'); ws.call('Runtime.enable')
        ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
        time.sleep(10)

        def eval_js(expr):
            r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
            if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:200])
            return r['result'].get('value')

        renderer = eval_js('''(() => {
  const c = document.createElement("canvas");
  const g = c.getContext("webgl2") || c.getContext("webgl");
  if (!g) return "PAS DE WEBGL";
  const ext = g.getExtension("WEBGL_debug_renderer_info");
  return ext ? g.getParameter(ext.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER);
})()''')
        plantes = eval_js('window.__jardin ? window.__jardin.jardin.compter().total : "pas de page"')
        if isinstance(plantes, int):
            fps = eval_js('''new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<5000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})''')
            info = eval_js('JSON.stringify(window.__jardinRenderInfo())')
            hud = eval_js('document.getElementById("fps").textContent')
            print(f'[{nom}] renderer={renderer}')
            print(f'[{nom}] plantes={plantes} FPS_5s={fps} hud={hud} info={info}')
        else:
            print(f'[{nom}] renderer={renderer} — page KO: {plantes}')
    except Exception as e:
        print(f'[{nom}] ERREUR {e}')
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()
