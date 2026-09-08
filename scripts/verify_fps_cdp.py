#!/usr/bin/env python3
"""Vérification CDP du mode FPS (t_93eba93e) :
bascule V, marche ZQSD, collisions plantes + bornes, retour orbital,
socle intact (saisons/climat/audio/plantation), FPS — + screenshot de preuve."""
import json, time, os, base64, sys
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS
import urllib.request

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')
os.makedirs(PREUVES, exist_ok=True)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9334

def main():
    tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable')
    ws.call('Runtime.enable')
    errors = []
    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            errors.append(str(r['exceptionDetails'])[:300])
            return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    def key(code, typ='keyDown', ms=60):
        ws.call('Input.dispatchKeyEvent', type=typ, key=code,
                code=code, windowsVirtualKeyCode=0, nativeVirtualKeyCode=0)
        time.sleep(ms / 1000)

    def v_key():
        # V = KeyV
        ws.call('Input.dispatchKeyEvent', type='keyDown', code='KeyV', key='v',
                windowsVirtualKeyCode=86, nativeVirtualKeyCode=86)
        time.sleep(0.05)
        ws.call('Input.dispatchKeyEvent', type='keyUp', code='KeyV', key='v',
                windowsVirtualKeyCode=86, nativeVirtualKeyCode=86)
        time.sleep(0.3)

    def hold(code, seconds, vk):
        ws.call('Input.dispatchKeyEvent', type='keyDown', code=code, key='k',
                windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
        time.sleep(seconds)
        ws.call('Input.dispatchKeyEvent', type='keyUp', code=code, key='k',
                windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

    def shot(nom):
        s = ws.call('Page.captureScreenshot', format='png')
        p = os.path.join(PREUVES, nom)
        open(p, 'wb').write(base64.b64decode(s['data']))
        print('capture:', nom)

    def pos():
        return eval_js('JSON.stringify({x:+window.__jardin.fps.position.x.toFixed(2), z:+window.__jardin.fps.position.z.toFixed(2), y:window.__jardin.fpsCamera.position.y, mode:window.__jardin.modeCamera})')

    time.sleep(4)
    ws.drain(0.5)
    print('== 0. chargement ==')
    print('etat_initial:', eval_js('JSON.stringify({mode:window.__jardin.modeCamera, plantes:window.__jardin.jardin.compter().total, climat:window.__jardin.clock.climat, fps:document.getElementById("fps").textContent})'))

    # 1. bascule vers FPS
    print('== 1. bascule V -> FPS ==')
    v_key()
    print('apres_V:', pos())
    eval_js('window.__jardin.fps.yaw = 0; window.__jardin.fps.pitch = 0; window.__jardin.fps.updateCamera()')  # regarde -z fixe pour des mesures reproductibles

    # 2. marche avant (Z/W = KeyW) : la position.z doit diminuer
    p0 = json.loads(pos())
    hold('KeyW', 1.0, 87)
    p1 = json.loads(pos())
    print(f'marche_avant: z {p0["z"]} -> {p1["z"]} (attendu: z diminue)', 'OK' if p1['z'] < p0['z'] - 2 else 'ECHEC')

    # 3. marche arrière + laterale : S (KeyS) puis Q (KeyA) puis D (KeyD)
    hold('KeyS', 1.0, 83)
    p2 = json.loads(pos())
    print(f'marche_arriere: z {p1["z"]} -> {p2["z"]}', 'OK' if abs(p2['z'] - p0['z']) < 1 else '?')
    hold('KeyD', 0.8, 68)
    p3 = json.loads(pos())
    print(f'strafe_droite: x {p2["x"]} -> {p3["x"]} (attendu: x augmente)', 'OK' if p3['x'] > p2['x'] + 1.5 else 'ECHEC')

    # 4. regard souris : mouvement -> yaw/pitch changent
    y0 = eval_js('window.__jardin.fps.yaw')
    ws.call('Input.dispatchMouseEvent', type='mouseMoved', x=640, y=400, movementX=200, movementY=0)
    y1 = eval_js('window.__jardin.fps.yaw')
    print(f'regard_souris: yaw {y0:.3f} -> {y1:.3f}', 'OK' if abs(y1 - y0) > 0.2 else 'ECHEC(mousemove hors lock?)')

    # 5. collisions : viser une plante, marcher dedans, verifier la distance mini
    plante = eval_js('JSON.stringify((()=>{const i=window.__jardin.jardin.instances;const f=i.find(x=>x.plante.type==="arbre")||i[0];return {x:f.group.position.x,z:f.group.position.z}})())')
    pl = json.loads(plante)
    print('cible_arbre:', pl)
    # teleporter a 3 m au sud de l'arbre, yaw=0 (face -z), avancer 2 s
    eval_js(f'window.__jardin.fps.position.set({pl["x"]}, 1.70, {pl["z"]}+3); window.__jardin.fps.yaw=0; window.__jardin.fps.updateCamera()')
    hold('KeyW', 2.0, 87)
    pf = json.loads(pos())
    import math
    d = math.hypot(pf['x'] - pl['x'], pf['z'] - pl['z'])
    print(f'collision_arbre: distance au tronc = {d:.2f} m (attendu ~0.90 = 0.55+0.35)', 'OK' if 0.7 < d < 1.2 else 'ECHEC')

    # 6. bornes : courir vers le nord longtemps -> z borne a ~-21.4
    eval_js('window.__jardin.fps.position.set(0, 1.70, 10); window.__jardin.fps.updateCamera()')
    hold('KeyW', 12.0, 87)
    pb = json.loads(pos())
    print(f'borne_nord: z = {pb["z"]:.2f} (attendu ~-21.4)', 'OK' if -23 < pb['z'] < -19 else 'ECHEC')

    # hauteur des yeux
    print(f'hauteur_yeux: y = {pb["y"]} (attendu 1.70)', 'OK' if abs(pb['y'] - 1.7) < 0.01 else 'ECHEC')

    # 7. screenshot FPS vue jardin (retour au centre, regard vers le jardin)
    eval_js('window.__jardin.fps.position.set(0, 1.70, 14); window.__jardin.fps.yaw=0.5; window.__jardin.fps.pitch=0.05; window.__jardin.fps.updateCamera()')
    time.sleep(0.6)
    shot('fps_vue_jardin.png')

    # 8. retour orbital (V) : le rendu reutilise la cam ortho, pan/zoom OK
    v_key()
    print('apres_V_retour:', pos())
    # planter via l'API pendant le mode orbital (le socle doit marcher)
    avant = eval_js('window.__jardin.jardin.compter().total')
    eval_js('(()=>{const r=window.__jardin.jardin.planterParId("tulipe",7,7); return r?("plante:"+r.plante.id):"null"})()')
    apres = eval_js('window.__jardin.jardin.compter().total')
    print(f'plantation_orbital: {avant} -> {apres}', 'OK' if apres == avant + 1 else 'ECHEC')
    shot('retour_orbital.png')

    # 9. re-FPS puis socle : avancer le temps, verifier horloge + FPS HUD
    v_key()
    eval_js('window.__jardin.clock.setSpeed("jour")')
    time.sleep(2)
    jr = eval_js('Math.round(window.__jardin.clock.jours)')
    hud = eval_js('document.getElementById("fps").textContent')
    print(f'acceleration_temps_en_fps: jours ~= {jr} (doit avoir avance)', 'OK' if jr >= 90 else 'ECHEC')
    print('fps_hud:', hud, 'OK' if int(hud) >= 50 else 'LOW')
    # audio encore la
    print('audio_present:', eval_js('typeof window.__jardin.audio.isPlaying === "function"'))

    print('== erreurs JS ==', len(errors))
    for e in errors[:5]:
        print('  ', e)

if __name__ == '__main__':
    main()
