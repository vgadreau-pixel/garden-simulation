#!/usr/bin/env python3
"""Vérification complète du parcours (t_4eea8dbc) sur Chrome SwiftShader : Port 9344.
Climat → plantation 10+ au clic → 1 an à 1 mois/s avec musique → caméra.
"""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
os.makedirs(PREUVES, exist_ok=True)

def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9344/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')
    ws.call('Page.navigate', url='http://localhost:4183/')
    time.sleep(5)
    events = ws.drain(1.0)
    errs = [e for e in events if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
    excs = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
    print('chargement console_errors:', len(errs), 'exceptions:', len(excs))
    for e in (errs + excs)[:3]: print('  ', json.dumps(e.get('params', {}))[:250])

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    def clic(x, y, bouton='left'):
        ws.call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button=bouton, clickCount=1)
        ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button=bouton, clickCount=1)

    print('webgl:', eval_js('document.createElement("canvas").getContext("webgl").getParameter(document.createElement("canvas").getContext("webgl").VERSION)'))
    print('loader_parti:', eval_js('!document.getElementById("loader") || document.getElementById("loader").classList.contains("parti")'))

    # Nouvelle visite : nettoyer le plan sauvegardé pour partir du jardin de démo (12)
    # NB: démo est déjà restauré depuis localStorage du run précédent ? Non : autre profil chrome.
    st = eval_js('JSON.stringify({plantes: window.__jardin.jardin.compter().total, climat: window.__jardin.clock.climat, viewport: innerWidth+"x"+innerHeight})')
    print('etat_initial:', st)

    # ── 1. Choisir un climat : méditerranéen ──
    bl = json.loads(eval_js('JSON.stringify([...document.querySelectorAll("#climat-panel .cbtn")].map(b=>({c:b.dataset.climat, r:b.getBoundingClientRect().toJSON()})))'))
    c = next(b for b in bl if b['c'] == 'mediterraneen')
    clic(c['r']['x']+c['r']['width']/2, c['r']['y']+c['r']['height']/2)
    time.sleep(0.4)
    print('climat_selectionne:', eval_js('window.__jardin.clock.climat'))

    # ── 2. Musique : vrai clic play ──
    pr = json.loads(eval_js('JSON.stringify(document.querySelector("#audio-host .zen-audio-ui button").getBoundingClientRect().toJSON())'))
    clic(pr['x']+pr['width']/2, pr['y']+pr['height']/2)
    time.sleep(3.2)
    print('audio_playing:', eval_js('window.__jardin.audio.isPlaying()'))

    # ── 3. Planter 12 végétaux au clic (iris sélectionné puis clics parcelles) ──
    s = json.loads(eval_js('JSON.stringify((()=>{const b=[...document.querySelectorAll(".cat-item")].find(x=>x.dataset.id==="iris");const r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})())'))
    clic(s['x'], s['y']); time.sleep(0.2)
    print('espece:', eval_js('window.__jardin.jardin.especeSelectionnee'))

    vp = json.loads(eval_js('JSON.stringify({w: innerWidth, h: innerHeight})'))
    ech = vp['h'] / 60.0
    def monde_vers_px(x, z): return vp['w']/2 + x*ech, vp['h']/2 + z*ech
    parcelles = [(0,1),(1,1),(2,2),(4,3),(5,4),(6,4),(7,5),(6,6),(5,7),(1,6),(2,7),(0,6)]
    avant = eval_js('window.__jardin.jardin.compter().total')
    ok = 0
    for ix, iz in parcelles:
        sx, sy = monde_vers_px((ix-3.5)*4.6, (iz-3.5)*4.6)
        clic(sx, sy)
        time.sleep(0.15)
        if eval_js('window.__jardin.jardin.compter().total') > avant + ok: ok += 1
    total = eval_js('window.__jardin.jardin.compter().total')
    print(f'plante_au_clic: {ok}/{len(parcelles)} nouveaux, total jardin: {total}')

    # Retrait d'une plante : clic droit sur une occupée
    p0 = json.loads(eval_js('JSON.stringify(window.__jardin.jardin.instances[0].parcelle)'))
    ix, iz = map(int, p0.split(','))
    sx, sy = monde_vers_px((ix-3.5)*4.6, (iz-3.5)*4.6)
    avant = eval_js('window.__jardin.jardin.compter().total')
    clic(sx, sy, bouton='right'); time.sleep(0.3)
    apres = eval_js('window.__jardin.jardin.compter().total')
    print('retrait_clic_droit:', avant, '->', apres, 'OK' if apres == avant-1 else 'ECHEC')

    print('sauvegarde_localStorage:', eval_js('JSON.parse(localStorage.getItem("jardin-saisons.plan.v1")||"null")?.plan?.length'))
    total_final = eval_js('window.__jardin.jardin.compter().total')

    # ── 4. FPS en conditions normales (pause) ──
    eval_js('window.__jardin.clock.setSpeed("pause")'); time.sleep(0.6)
    fps_pause = eval_js('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})')
    print('fps_pause ({} plantes):'.format(total_final), fps_pause)

    # ── 5. Accélérer sur une année complète avec musique active ──
    vl = json.loads(eval_js('JSON.stringify([...document.querySelectorAll("#timebar .tbtn")].map(b=>({s:b.dataset.speed,r:b.getBoundingClientRect().toJSON()})))'))
    c = next(b for b in vl if b['s'] == 'mois')
    clic(c['r']['x']+c['r']['width']/2, c['r']['y']+c['r']['height']/2)
    j0 = eval_js('window.__jardin.clock.jours')
    fps_lus = []; errs_timelapse = []
    t0 = time.time(); ws.drain(0.1)
    while time.time() - t0 < 12.6:
        time.sleep(1.0)
        fps_lus.append(eval_js('document.getElementById("fps").textContent'))
        for e in ws.drain(0.05):
            if e.get('method') in ('Runtime.consoleAPICalled',) and e['params'].get('type') == 'error':
                errs_timelapse.append(json.dumps(e['params'])[:150])
            if e.get('method') == 'Runtime.exceptionThrown':
                errs_timelapse.append(json.dumps(e['params'])[:150])
    j1 = eval_js('window.__jardin.clock.jours')
    print(f'annee_acceleree: {(j1-j0)%365:.1f} jours parcourus (attendu ≈ 360-375)')
    print('fps_time-lapse:', fps_lus)
    print('erreurs_timelapse:', len(errs_timelapse), errs_timelapse[:2])
    print('audio_actif_fin:', eval_js('window.__jardin.audio.isPlaying()'))
    shot('parcours_ete.png')

    # ── 6. Caméra : zoom molette + pan drag ──
    ws.call('Input.dispatchMouseEvent', type='mouseWheel', x=700, y=450, deltaX=0, deltaY=-500)
    time.sleep(0.4)
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=700, y=450, button='left', clickCount=1)
    for i in range(1, 9):
        ws.call('Input.dispatchMouseEvent', type='mouseMoved', x=700-18*i, y=450+10*i, button='left', buttons=1)
        time.sleep(0.02)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=556, y=530, button='left', clickCount=1)
    time.sleep(0.5)
    shot('parcours_camera.png')

    # ── 7. Bilan erreurs ──
    evts = ws.drain(1.0)
    errs2 = [e for e in evts if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
    excs2 = [e for e in evts if e.get('method') == 'Runtime.exceptionThrown']
    print('final console_errors:', len(errs2), 'exceptions:', len(excs2))
    print('date:', eval_js('window.__jardin.clock.etat.label'))

if __name__ == '__main__':
    main()
