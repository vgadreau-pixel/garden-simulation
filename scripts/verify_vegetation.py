#!/usr/bin/env python3
"""Vérification complète corrigée : végétation GLTF + sol PBR, captures à midi,
attente du rendu après chaque scrub (dernierEtat suit la frame, pas l'appel)."""
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

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'): return ('EXC', str(r['exceptionDetails'])[:400])
        return r['result'].get('value')

    def scrub(jours, attente=1.5):
        """Scrub vers jours (midi si X.5) et attend que le rendu suive."""
        eval_js('window.__jardin.clock.setSpeed && window.__jardin.clock.setSpeed("pause")')
        eval_js(f'window.__jardin.clock.scrubTo({jours})')
        time.sleep(attente)

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        open(os.path.join(PREUVES, nom), 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    # Plan vierge pour un état connu
    ws.call('Page.navigate', url='http://localhost:4183/')
    time.sleep(4)
    eval_js('localStorage.removeItem("jardin-saisons.plan.v1")')
    ws.call('Page.navigate', url='http://localhost:4183/?climat=oceanique')
    time.sleep(6)
    events = ws.drain(1.0)
    errs = [e for e in events if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error']
    excs = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
    print('chargement console_errors:', len(errs), 'exceptions:', len(excs))
    for e in (errs + excs)[:4]: print('  ', json.dumps(e.get('params', {}))[:250])

    # ── 1. Été (midi) : toutes les espèces plantées, modèles actifs ──
    scrub(197.7)
    n_avant = eval_js('window.__jardin.jardin.compter().total')
    planted = eval_js('''(() => {
  const J = window.__jardin;
  const ids = ["cerisier","erable_japonais","sapin","olivier","bouleau","pommier",
               "lavande","rosier","hortensia","buis","romarin","forsythia",
               "tulipe","coquelicot","marguerite","iris","tomate","carotte","courgette"];
  const presents = new Set(J.jardin.instances.map(i => i.plante.id));
  const libres = [];
  for (let ix = 0; ix < 8; ix++) for (let iz = 0; iz < 8; iz++) libres.push([ix, iz]);
  const prises = new Set(J.jardin.instances.map(i => i.parcelle));
  let k = 0;
  for (const id of ids) {
    if (presents.has(id)) continue;
    while (k < libres.length && prises.has(libres[k].join(","))) k++;
    if (k >= libres.length) break;
    const [ix, iz] = libres[k]; k++;
    if (J.jardin.planterParId(id, ix, iz)) prises.add(ix + "," + iz);
  }
  const rng = (n) => Math.floor(Math.random() * n);
  const pool = ["cerisier","erable_japonais","bouleau","pommier","lavande","buis","sapin"];
  while (J.jardin.compter().total < 50 && k < libres.length) {
    const [ix, iz] = libres[k]; k++;
    J.jardin.planterParId(pool[rng(pool.length)], ix, iz);
  }
  return J.jardin.compter().total;
})()''')
    time.sleep(8)  # chargement GLTF async (~17 Mo au 1er chargement)
    veg = eval_js('''JSON.stringify({
  total: window.__jardin.jardin.instances.length,
  vegActifs: window.__jardin.jardin.instances.filter(i => i.vegActif).length,
  especes: [...new Set(window.__jardin.jardin.instances.map(i => i.plante.id))].length,
})''')
    print(f'plantations: {n_avant} -> {planted}; veg: {veg}')
    prims = eval_js('''JSON.stringify(window.__jardin.jardin.instances.filter(i => i.vegActif && i.parties.feuilles.visible).length)''')
    print('primitives_visibles_parmi_veg:', prims)

    # (re)scrub été : les plantations de ce run sont des jeunes pousses,
    # le rendu suit via appliquerEtat chaque frame.
    scrub(197.7)
    ete = eval_js('''(() => {
  const i = window.__jardin.jardin.instances.find(x => x.vegActif && x.plante.id === "cerisier");
  return i ? JSON.stringify({ couleur: "#"+i.dernierEtat.couleur.getHexString(), masse: +i.dernierEtat.masseFoliaire.toFixed(2) }) : "pas de cerisier actif";
})()''')
    print('cerisier_ete:', ete)
    shot('vegetation_ete.png')

    # ── 2. Automne (midi) ──
    scrub(289.0)
    teinte = eval_js('''(() => {
  const i = window.__jardin.jardin.instances.find(x => x.vegActif && x.plante.id === "cerisier");
  if (!i) return "pas de cerisier";
  return JSON.stringify({ c: "#"+i.dernierEtat.couleur.getHexString(), masse: +i.dernierEtat.masseFoliaire.toFixed(2) });
})()''')
    print('cerisier_automne:', teinte)
    shot('vegetation_automne.png')

    # ── 3. Hiver (midi) : caducs nus (masse 0), persistants verts ──
    scrub(15.2)
    hiver = eval_js('''(() => {
  const cer = window.__jardin.jardin.instances.find(x => x.vegActif && x.plante.id === "cerisier");
  const sap = window.__jardin.jardin.instances.find(x => x.vegActif && x.plante.id === "sapin");
  return JSON.stringify({
    cerisier_masse: cer ? +cer.dernierEtat.masseFoliaire.toFixed(2) : null,
    cerisier_feuilles_echelle: cer ? +cer.veg.leafMeshes[0].mesh.scale.x.toFixed(4) : null,
    sapin_masse: sap ? +sap.dernierEtat.masseFoliaire.toFixed(2) : null,
  });
})()''')
    print('hiver:', hiver)
    shot('vegetation_hiver.png')

    # ── 4. Retour été (midi) pour les mesures perf ──
    scrub(197.7)
    nb = eval_js('window.__jardin.jardin.instances.length')
    calls = eval_js('window.__jardinRenderInfo ? JSON.stringify(window.__jardinRenderInfo()) : "absent"')
    fps_raf = eval_js('''new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})''')
    print(f'perf: {nb} instances, render.info={calls}, fps_raf(3s)={fps_raf}')

    # ── 5. Socle intact : climat, time-lapse, audio ──
    eval_js('''(() => { const b=[...document.querySelectorAll("#climat-panel .cbtn")].find(x=>x.dataset.climat==="mediterraneen"); b?.click(); })()''')
    time.sleep(0.4)
    print('climat_change:', eval_js('window.__jardin.clock.climat'))
    pr = json.loads(eval_js('JSON.stringify(document.querySelector("#audio-host .zen-audio-ui button").getBoundingClientRect().toJSON())'))
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=int(pr['x']+pr['width']/2), y=int(pr['y']+pr['height']/2), button='left', clickCount=1)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=int(pr['x']+pr['width']/2), y=int(pr['y']+pr['height']/2), button='left', clickCount=1)
    time.sleep(2.5)
    print('audio_playing:', eval_js('window.__jardin.audio.isPlaying()'))
    vl = json.loads(eval_js('JSON.stringify([...document.querySelectorAll("#timebar .tbtn")].map(b=>({s:b.dataset.speed,r:b.getBoundingClientRect().toJSON()})))'))
    c = next(b for b in vl if b['s'] == 'mois')
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=int(c['r']['x']+c['r']['width']/2), y=int(c['r']['y']+c['r']['height']/2), button='left', clickCount=1)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=int(c['r']['x']+c['r']['width']/2), y=int(c['r']['y']+c['r']['height']/2), button='left', clickCount=1)
    j0 = eval_js('window.__jardin.clock.jours')
    time.sleep(5)
    j1 = eval_js('window.__jardin.clock.jours')
    print(f'timelapse: {(j1-j0):.1f} jours en 5 s (attendu ~150)')
    errs_fin = [e for e in ws.drain(1.0) if e.get('method') == 'Runtime.exceptionThrown']
    print('exceptions_fin:', len(errs_fin))
    print('date:', eval_js('window.__jardin.clock.etat.label'))


if __name__ == '__main__':
    main()
