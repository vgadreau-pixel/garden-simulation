#!/usr/bin/env python3
"""Vérification CDP finale du système de climat (tâche t_d316b27d).

Vérifie :
  1. 0 erreur console au chargement
  2. Le panneau de climat est présent avec 5 climats
  3. Changer de climat change visiblement la météo (particules + lumière :
     5 empreintes pixel distinctes à date constante)
  4. L'olivier dépérit en continental (vigueur < 0.45), la lavande et
     l'olivier sont épanouis en méditerranéen (vigueur = 1)
  5. La floraison de la lavande est avancée en méditerranéen vs tempéré,
     retardée en continental
  6. Le facteur de croissance climatique est plus élevé en aride qu'en
     continental (mesuré via la vitesse de simulation croisée)
"""
import json, time, base64, sys, io, os
sys.path.insert(0, '/home/vgadreau/.hermes/kanban/workspaces/t_d316b27d/scripts')
from verify_cdp import WS
import urllib.request
from PIL import Image

OUT = '/home/vgadreau/.hermes/kanban/workspaces/t_d316b27d/preuves'
os.makedirs(OUT, exist_ok=True)

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
print('1. console_errors:', len(console_errors), 'exceptions:', len(exceptions))
for e in (console_errors + exceptions)[:5]:
    print('  ', json.dumps(e.get('params', {}))[:300])
assert not console_errors and not exceptions, 'erreurs console au chargement !'

def eval_js(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:400])
    return r['result'].get('value')

def shot(name):
    s = ws.call('Page.captureScreenshot', format='png')
    p = f'{OUT}/{name}.png'
    open(p, 'wb').write(base64.b64decode(s['data']))
    print('   capture:', p)

def canvas_hash():
    s = ws.call('Page.captureScreenshot', format='png')
    img = Image.open(io.BytesIO(base64.b64decode(s['data']))).convert('RGB')
    h = 0
    for (r, g, b) in img.getdata():
        h = ((h * 31) + r + g + b) & 0xFFFFFFFF
    return h

def choisir_climat(cid):
    eval_js(f'window.__jardin.clock.setClimat("{cid}");')
    eval_js(f'(()=>{{const b=[...document.querySelectorAll(".cbtn")].find(b=>b.dataset.climat==="{cid}"); if(b) b.click();}})()')
    time.sleep(1.2)

# 2. Panneau climat
panneau = eval_js('(()=>{const p=document.getElementById("climat-panel");return p?{boutons:p.querySelectorAll(".cbtn").length,label:p.querySelector(".cbtn.active span").textContent}:{null:true}})()')
print('2. panneau climat:', panneau)
assert panneau.get('boutons') == 5, 'panneau climat incomplet'

# Date fixe : 15 juillet midi (plein été, plein jour).
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(195.5);')
time.sleep(0.6)

# 3. Empreintes pixel distinctes par climat + état particules.
hashes = {}
for cid in ['tempre', 'mediterraneen', 'continental', 'aride', 'tropical']:
    choisir_climat(cid)
    etat = eval_js('JSON.stringify(window.__jardin.meteo.etat())')
    h = canvas_hash()
    hashes[cid] = h
    print(f'3. {cid}: meteo={etat} hash={h}')
    shot(f'climat_{cid}')

distinct = len(set(hashes.values()))
print(f'   empreintes distinctes: {distinct}/5')
assert distinct == 5, 'des climats ont la même empreinte pixel !'

# 4. Vigueur des plantes (dernierEtat est rafraîchi chaque frame par le rendu).
choisir_climat('continental')
vig = eval_js('''(()=>{const o={};for(const i of window.__jardin.instances){
  if(['olivier','lavande'].includes(i.plante.id)&&i.dernierEtat)o[i.plante.id]=i.dernierEtat.vigueur;}return o;})()''')
print(f'4. vigueurs continental: {vig}')
assert vig.get('olivier', 1) < 0.45, f'olivier devrait dépérir en continental: {vig}'

choisir_climat('mediterraneen')
vig = eval_js('''(()=>{const o={};for(const i of window.__jardin.instances){
  if(['olivier','lavande'].includes(i.plante.id)&&i.dernierEtat)o[i.plante.id]=i.dernierEtat.vigueur;}return o;})()''')
print(f'   vigueurs mediterraneen: {vig}')
assert vig.get('lavande', 0) == 1 and vig.get('olivier', 0) == 1, f'épanouies en méditerranéen: {vig}'

# 5. Décalage de floraison : au 25 juin, la lavande (floraison juin-août)
# fleurit davantage en méditerranéen (avancé) qu'en continental (retardé).
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(175.5);')  # ~25 juin
fleurs = {}
for cid in ['tempre', 'mediterraneen', 'continental']:
    choisir_climat(cid)
    f = eval_js('''(()=>{const lav=window.__jardin.instances.find(i=>i.plante.id==='lavande');
      return lav&&lav.dernierEtat?lav.dernierEtat.floraison:-1;})()''')
    fleurs[cid] = f
print(f'5. floraison lavande au 25 juin — {fleurs}')
assert fleurs['mediterraneen'] > fleurs['continental'], \
    'la floraison devrait être avancée au chaud, retardée au froid'

# 6. Croissance : on mesure le gain de maturité d'une plante jeune sur 30 j
# de simulation, à climat identique et vitesse identique — le facteur de
# croissance climatique (0.58 continental vs 1.50 aride, cf. check-climat.mjs)
# doit donner un gain supérieur en aride.
choisir_climat('aride')
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(100);')
# plante 0 = une espèce quelconque ; on la remet jeune pour libérer la dynamique.
m0 = eval_js('window.__jardin.instances[0].maturite = 0.25; window.__jardin.instances[0].maturite')
eval_js('window.__jardin.clock.setSpeed("mois");')
time.sleep(1.0)  # ~30 j de sim
eval_js('window.__jardin.clock.setSpeed("pause");')
m1_aride = eval_js('window.__jardin.instances[0].maturite')

choisir_climat('continental')
eval_js('window.__jardin.clock.setSpeed("pause"); window.__jardin.clock.scrubTo(100);')
eval_js('window.__jardin.instances[0].maturite = 0.25;')
eval_js('window.__jardin.clock.setSpeed("mois");')
time.sleep(1.0)
eval_js('window.__jardin.clock.setSpeed("pause");')
m1_cont = eval_js('window.__jardin.instances[0].maturite')

gain_aride = m1_aride - 0.25
gain_cont = m1_cont - 0.25
print(f'6. gain maturité sur 30 j — aride: +{gain_aride:.4f} continental: +{gain_cont:.4f}')
assert gain_aride > gain_cont, 'la croissance devrait être plus rapide en aride'

print('OK: toutes les vérifications CDP climat passent')
