#!/usr/bin/env python3
"""Le rAF tourne (1 frame/3 s — lent mais vivant). MAIS hud fps = 0 et
l'horloge n'avance pas → la BOUCLE de setAnimationLoop est peut-être
différente du rAF (three r170 : XRSession ? Non, WebGLRenderer.setAnimationLoop
utilise rAF si pas de XR). La frame prend ~3 s (SwiftShader avec 26k brins
+ EffectComposer = lourds). À 1 frame/3 s : fps affiché 0 (calcul <1), et
clock.tick(3000) → jours avance de 3000ms*x1=0.035 ms... NON: x1 = 1/86400
j/s → 3 s réelles = 0.035 ms de temps simu ≈ rien. C'EST NORMAL pour x1 !
MAIS alors mes scrubTo() + captures : la boucle tourne à 1 frame/3 s et mes
captures intermédiaires étaient prises avant le rendu de la frame suivante !
C'est tout : entre scrubTo et shot il faut attendre 2-3 FRAMES = 6-10 s.
Et le premier onirique_ete_fps.png (différent) = première frame rendue APRÈS
1,5 s de scrub mais avec l'état ANCIEN (frame de 3 s plus tôt)."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

P = os.path.join(os.path.dirname(__file__), '..', 'preuves')
tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')
ws.call('Emulation.setDeviceMetricsOverride', width=1280, height=720, deviceScaleFactor=1, mobile=False)
ws.call('Page.navigate', url='http://[::1]:4183/?herbe=4000')  # léger pour SwiftShader
time.sleep(2)

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', r['exceptionDetails']['exception']['description'][:250])
    return r['result'].get('value')

for _ in range(60):
    if ev('typeof window.__jardin === "object"') is True: break
    time.sleep(1.5)
time.sleep(5)  # laisser passer 1-2 frames

def attendre_frames(n=2, max_s=40):
    """Attend que N frames passent (via compteur rAF déjà hooké au 1er script ? non).
    On attend simplement assez longtemps."""
    time.sleep(max_s)

def shot(nom):
    s = ws.call('Page.captureScreenshot', format='png')
    open(os.path.join(P, nom), 'wb').write(base64.b64decode(s['data']))
    print('capture:', nom)

def scrub(jour, heure):
    ev(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({jour} + {heure}/24)')
    attendre_frames()  # ~10 s = 3 frames lentes
    return ev('window.__jardin.clock.jours')

PLANS = [
    ('ete', 166, 10.0, 'onirique_ete_fps'),
    ('hiver', 15, 10.0, 'onirique_hiver_fps'),
    ('ete', 166, 18.75, 'onirique_ete_golden_fps'),
    ('ete', 166, 22.5, 'onirique_ete_nuit_fps'),
]
for saison, jour, heure, nom in PLANS:
    print(nom, 'jours =', scrub(jour, heure))
    shot(nom + '.png')
print('FINI')
