#!/usr/bin/env python3
"""Vérification CDP du parcours complet (t_4eea8dbc) :
choisir un climat, planter 10+ végétaux au clic, accélérer sur une année
avec musique active, déplacer la caméra — 0 erreur console, FPS stable."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
os.makedirs(PREUVES, exist_ok=True)

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable')
    ws.call('Runtime.enable')
    ws.call('Page.navigate', url='http://localhost:4183/')
    time.sleep(5)
    events = ws.drain(1.0)
    console_errors = [e for e in events
        if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
    exceptions = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
    print('etape0_chargement console_errors:', len(console_errors), 'exceptions:', len(exceptions))
    for e in (console_errors + exceptions)[:5]:
        print('  ', json.dumps(e.get('params', {}))[:300])

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        p = os.path.join(PREUVES, nom)
        open(p, 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    # 1. Loader parti ?
    print('loader_parti:', eval_js('!document.getElementById("loader") || document.getElementById("loader").classList.contains("parti")'))

    # 2. État initial (jardin de démo planté ?)
    st = eval_js('JSON.stringify({plantes: window.__jardin.jardin.compter().total, climat: window.__jardin.clock.climat})')
    print('etat_initial:', st)

    # 3. Choisir un climat (clic réel sur bouton méditerranéen)
    boutons = eval_js('JSON.stringify([...document.querySelectorAll("#climat-panel .cbtn")].map(b=>({c:b.dataset.climat, r:b.getBoundingClientRect().toJSON()})))')
    bl = json.loads(boutons)
    cible = next(b for b in bl if b['c'] == 'mediterraneen')
    cx, cy = cible['r']['x'] + cible['r']['width']/2, cible['r']['y'] + cible['r']['height']/2
    for typ, xy in [('mousePressed',(cx,cy)), ('mouseReleased',(cx,cy))]:
        ws.call('Input.dispatchMouseEvent', type=typ, x=xy[0], y=xy[1], button='left', clickCount=1)
    time.sleep(0.5)
    print('climat_apres_clic:', eval_js('window.__jardin.clock.climat'))

    # 4. Musique : vrai clic sur le bouton play (geste utilisateur)
    play = eval_js('JSON.stringify(document.querySelector("#audio-host .zen-audio-ui button").getBoundingClientRect().toJSON())')
    pr = json.loads(play)
    px, py = pr['x'] + pr['width']/2, pr['y'] + pr['height']/2
    for typ, xy in [('mousePressed',(px,py)), ('mouseReleased',(px,py))]:
        ws.call('Input.dispatchMouseEvent', type=typ, x=xy[0], y=xy[1], button='left', clickCount=1)
    time.sleep(3.2)  # fondu 2,5 s
    print('audio_playing:', eval_js('window.__jardin.audio.isPlaying()'),
          'ctx:', eval_js('window.__jardin.audio._debug().state'))

    # 5. Planter 10 végétaux de plus : sélectionne une espèce dans le catalogue
    #    puis clic sur des parcelles vides.
    # 5a. Sélectionner la tulipe (clic réel)
    sel = eval_js('JSON.stringify((()=>{const b=[...document.querySelectorAll(".cat-item")].find(x=>x.dataset.id==="iris");const r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})())')
    s = json.loads(sel)
    for typ, xy in [('mousePressed',(s['x'],s['y'])), ('mouseReleased',(s['x'],s['y']))]:
        ws.call('Input.dispatchMouseEvent', type=typ, x=xy[0], y=xy[1], button='left', clickCount=1)
    time.sleep(0.3)
    print('espece_selectionnee:', eval_js('window.__jardin.jardin.especeSelectionnee'))

    # 5b. Clics sur 10 parcelles vides (positions monde → écran).
    # Canvas plein écran, caméra ortho centrée (target 0,0, zoom 1),
    # VIEW_HEIGHT=60 m verticaux. On calcule la conversion côté JS.
    clics = eval_js('''(async () => {
      const { centreParcelle } = await import('/src/plantation.js').catch(()=>({}));
      return 'dynamic-import-indisponible';
    })()''')
    # Conversion côté Python : viewport 1280x800 par défaut headless.
    vp = eval_js('JSON.stringify({w: innerWidth, h: innerHeight, dpr: devicePixelRatio})')
    vp = json.loads(vp)
    VIEW = 60.0
    echelle = vp['h'] / VIEW  # px par mètre (zoom 1)
    def px_de_monde(x, z):
        # caméra au centre (0,0) ; nord (-z) en haut ; x vers la droite.
        sx = vp['w'] / 2 + x * echelle
        sy = vp['h'] / 2 + z * echelle
        return sx, sy
    parcelles = [(0,1),(1,1),(2,2),(3,3),(4,3),(5,4),(6,4),(7,5),(6,6),(5,7),(1,6),(2,7)]
    avant = eval_js('window.__jardin.jardin.compter().total')
    ok = 0
    for (ix, iz) in parcelles:
        # centre de parcelle : offset=(8-1)/2, PITCH=4.6
        wx = (ix - 3.5) * 4.6
        wz = (iz - 3.5) * 4.6
        sx, sy = px_de_monde(wx, wz)
        for typ, xy in [('mousePressed',(sx,sy)), ('mouseReleased',(sx,sy))]:
            ws.call('Input.dispatchMouseEvent', type=typ, x=sx, y=sy, button='left', clickCount=1)
        time.sleep(0.12)
        apres = eval_js('window.__jardin.jardin.compter().total')
        if apres > avant + ok:
            ok += 1
    print(f'plante_au_clic: {ok}/{len(parcelles)} nouveaux plants, total:', eval_js('window.__jardin.jardin.compter().total'))

    # 5c. Retirer une plante (clic droit sur une occupée)
    wx, wz = (3 - 3.5) * 4.6, (3 - 3.5) * 4.6
    sx, sy = px_de_monde(wx, wz)
    avant = eval_js('window.__jardin.jardin.compter().total')
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=sx, y=sy, button='right', clickCount=1)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=sx, y=sy, button='right', clickCount=1)
    time.sleep(0.3)
    apres = eval_js('window.__jardin.jardin.compter().total')
    print('retrait_clic_droit:', avant, '->', apres, 'OK' if apres == avant - 1 else 'ECHEC')

    # 6. Sauvegarde localStorage
    print('sauvegarde:', eval_js('JSON.parse(localStorage.getItem("jardin-saisons.plan.v1")||"null")?.plan?.length'))

    # 7. Accélérer le temps sur une année complète (1 mois/s → ~12,2 s)
    vit = eval_js('JSON.stringify([...document.querySelectorAll("#timebar .tbtn")].map(b=>({s:b.dataset.speed,r:b.getBoundingClientRect().toJSON()})))')
    vl = json.loads(vit)
    cible = next(b for b in vl if b['s'] == 'mois')
    cx, cy = cible['r']['x'] + cible['r']['width']/2, cible['r']['y'] + cible['r']['height']/2
    for typ, xy in [('mousePressed',(cx,cy)), ('mouseReleased',(cx,cy))]:
        ws.call('Input.dispatchMouseEvent', type=typ, x=xy[0], y=xy[1], button='left', clickCount=1)
    j0 = eval_js('window.__jardin.clock.jours')
    # Échantillonner FPS + erreurs pendant 12,5 s (~1 an simulé)
    fps_mesures = []
    erreurs_pendant = []
    t0 = time.time()
    ws.drain(0.1)
    while time.time() - t0 < 12.5:
        time.sleep(1.0)
        fps_mesures.append(eval_js('document.getElementById("fps").textContent'))
        evts = ws.drain(0.05)
        for e in evts:
            if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error':
                erreurs_pendant.append(json.dumps(e['params'])[:200])
            if e.get('method') == 'Runtime.exceptionThrown':
                erreurs_pendant.append(json.dumps(e['params'])[:200])
    j1 = eval_js('window.__jardin.clock.jours')
    delta = (j1 - j0) % 365
    print(f'annee_acceleree: {delta:.1f} jours en 12,5 s (attendu ~375 max, vitesse 30 j/s)')
    print('fps_echantillons:', fps_mesures)
    print('erreurs_pendant_timelapse:', len(erreurs_pendant), erreurs_pendant[:3])
    print('audio_toujours_actif:', eval_js('window.__jardin.audio.isPlaying()'))
    shot('parcours_ete.png')

    # 8. Caméra : pan + zoom via vrais événements souris
    ws.call('Input.dispatchMouseEvent', type='mouseWheel', x=640, y=400, deltaX=0, deltaY=-500)
    time.sleep(0.4)
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=640, y=400, button='left', clickCount=1)
    for i in range(1, 9):
        ws.call('Input.dispatchMouseEvent', type='mouseMoved', x=640 - 18*i, y=400 + 10*i, button='left', buttons=1)
        time.sleep(0.02)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=500, y=480, button='left', clickCount=1)
    time.sleep(0.5)
    shot('parcours_camera.png')
    print('zoom_camera:', eval_js('window.__jardin.scene ? "ok" : "?"'))

    # 9. Bilan final des erreurs console
    evts = ws.drain(1.0)
    errs = [e for e in evts if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
    excs = [e for e in evts if e.get('method') == 'Runtime.exceptionThrown']
    print('etape_finale console_errors:', len(errs), 'exceptions:', len(excs))
    print('date_finale:', eval_js('window.__jardin.clock.etat.label'))

if __name__ == '__main__':
    main()
