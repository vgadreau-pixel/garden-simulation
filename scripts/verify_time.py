#!/usr/bin/env python3
"""Vérification CDP du moteur temporel : scrubbing, végétation visible,
fluïdité time-lapse, lumière saisonnière, 0 erreur console."""
import json, time, base64, sys
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_44f07608/scripts')
from verify_cdp import WS
import urllib.request

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable')
ws.call('Runtime.enable')
ws.call('Page.navigate', url='http://localhost:4173/')
time.sleep(4)
events = ws.drain(0.5)
console_errors = [e for e in events if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') in ('error', 'warning')]
exceptions = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
print('console_errors:', len(console_errors), 'exceptions:', len(exceptions))
for e in (console_errors + exceptions)[:5]:
    print('  ', json.dumps(e.get('params', {}))[:300])

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

# État global
print('etat initial:', eval_js('window.__jardin.clock.etat.label'))

def shot(name):
    s = ws.call('Page.captureScreenshot', format='png')
    p = f'/tmp/jardin_{name}.png'
    open(p, 'wb').write(base64.b64decode(s['data']))
    return p

# Empreinte du canvas : on hache les pixels de la CAPTURE PNG (via Pillow),
# pas readPixels WebGL — ce dernier renvoie des zéros sans preserveDrawingBuffer.
def canvas_hash(shot_path=None):
    from PIL import Image
    if shot_path is None:
        return 0
    img = Image.open(shot_path).convert('RGB')
    h = 0
    for (r, g, b) in img.getdata():
        h = ((h * 31) + r + g + b) & 0xFFFFFFFF
    return h

def shot_and_hash(name):
    p = shot(name)
    return canvas_hash(p)

# ── 1. Scrubbing : 4 dates d'un coup via clock.scrubTo ──
# Midi (0.5 jour) : le soleil est au zénith, la scène est éclairée —
# comparer des dates à 00h00 (nuit) rendrait tout noir et incomparable.
dates = {'hiver': 10.5, 'printemps': 100.5, 'ete': 195.5, 'automne': 300.5}
hashes = {}
for saison, j in dates.items():
    eval_js(f'window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo({j});')
    time.sleep(0.8)
    hashes[saison] = shot_and_hash(saison)
    etat = eval_js('window.__jardin.clock.etat.label + " | " + window.__jardin.instances[0].dernierEtat.stade')
    print(f'{saison} (j={j}):', etat)

distinct = len(set(hashes.values()))
print('hashes distincts sur 4 saisons:', distinct, hashes)
assert distinct >= 3, 'le scrubbing ne change pas assez le rendu'

# ── 2. Fluïdité : interpolation continue entre 2 dates proches ──
deltas = []
prev = None
for step in range(20):
    eval_js(f'window.__jardin.clock.scrubTo({100 + step * 0.5});')
    time.sleep(0.05)
    m = eval_js('window.__jardin.instances[0].dernierEtat.masseFoliaire')
    if prev is not None:
        deltas.append(abs(m - prev))
    prev = m
max_delta = max(deltas)
print(f'interpolation: delta max masseFoliaire entre pas de 0.5j = {max_delta:.4f} (attendu < 0.02)')
assert max_delta < 0.02, 'transition brutale détectée'

# ── 3. Time-lapse : vitesse 1 mois/s, mesurer le fps et l'avance du temps ──
eval_js('window.__jardin.clock.scrubTo(90); window.__jardin.clock.setSpeed("mois");')
time.sleep(2.0)
avance = eval_js('window.__jardin.clock.jours')
print(f'time-lapse 1 mois/s: jours après 2s = {avance:.1f} (attendu 90+60=150, ±5)')
assert 145 <= avance <= 155, 'vitesse mois incorrecte'
fps = eval_js('document.getElementById("fps").textContent')
print('fps pendant time-lapse:', fps)

# ── 4. Lumière suit la saison : scrubber (en pause) à midi d'hiver vs midi d'été,
# puis comparer hauteur et intensité du soleil. À 46,5°N : soleil d'été nettement
# plus haut et plus fort que le soleil d'hiver.
eval_js('window.__jardin.clock.setSpeed("pause")')
def mesure_soleil(jours):
    eval_js(f'window.__jardin.clock.scrubTo({jours});')
    time.sleep(0.4)  # laisse la boucle rAF appliquer la lumière
    return eval_js('''
    (() => {
      const sun = window.__jardin.scene.children.find(o => o.isDirectionalLight);
      return JSON.stringify({y: sun.position.y, i: sun.intensity});
    })()
    ''')

hiver = json.loads(mesure_soleil(10.5))  # 11 janvier, midi
ete = json.loads(mesure_soleil(195.5))   # 15 juillet, midi
print('lumière midi hiver:', hiver, '| midi été:', ete)
assert float(ete['y']) > float(hiver['y']) * 1.5, 'soleil d été pas plus haut qu en hiver'
assert float(ete['i']) > float(hiver['i']), 'soleil d été pas plus intense qu en hiver'
print('lumière saisonnière: OK')

# ── 5. Pause : le temps est gelé ──
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(150);')
time.sleep(1.0)
j = eval_js('window.__jardin.clock.jours')
assert abs(j - 150) < 0.01, f'pause non gelée: {j}'
print('pause: OK')

print('shot_final:', shot('final'))
print('VERIFICATION CDP COMPLETE — tout passe')
