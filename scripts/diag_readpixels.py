#!/usr/bin/env python3
"""Rendu off-screen via la fpsCamera : lit les pixels du framebuffer après un
render explicite dans le canvas préservé. Déterministe, indépendant du HUD."""
import json, time, sys, os, base64, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from verify_cdp import WS

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json'))
page = [t for t in tabs if t['type'] == 'page'][0]
ws = WS(page['webSocketDebuggerUrl'])
ws.call('Page.enable'); ws.call('Runtime.enable')

def ev(expr):
    r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    if r.get('exceptionDetails'):
        return ('EXC', str(r['exceptionDetails'])[:500])
    return r['result'].get('value')

# Expose les modules three via __jardin ? On passe par le rendu du composer :
# 1) placer fpsCamera, 2) rendre hors-boucle via __jardinRenderInfo-like mais en lisant
# les pixels juste après composer.render() dans le même tick JS.
expr = '''(async()=>{
  const j = window.__jardin;
  // stopper la boucle pour rendre tranquillement ? Non: on rend simplement après un rAF.
  j.fps.position.set(-14, 1.7, 17.5);
  j.fps.yaw = 2.35; j.fps.pitch = 0.06;
  if (j.fps.updateCamera) j.fps.updateCamera();
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const c = document.getElementById('app');
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  // preserveDrawingBuffer inconnu: on lit IMMÉDIATEMENT, mais le rAF de la boucle
  // peut avoir déjà swapé. Test: lecture brute maintenant.
  const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
  const buf = new Uint8Array(4*w*h);
  gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,buf);
  // stats par zone (attention: origin bas-gauche en GL)
  function zone(x0,y0,x1,y1){
    let r=0,g=0,b=0,n=0;
    for(let y=y0;y<y1;y+=Math.max(1,(y1-y0)>>6))
      for(let x=x0;x<x1;x+=Math.max(1,(x1-x0)>>6)){
        const i=(y*w+x)*4; r+=buf[i];g+=buf[i+1];b+=buf[i+2];n++;
      }
    return [Math.round(r/n),Math.round(g/n),Math.round(b/n)];
  }
  // y GL: 0=bas. "ciel visuel" = haut = y proche de h
  return JSON.stringify({
    haut_gl:[...zone(0,Math.floor(h*0.85),w,h)],
    milieu_gl:[...zone(0,Math.floor(h*0.4),w,Math.floor(h*0.6))],
    bas_gl:[...zone(0,0,w,Math.floor(h*0.15))],
    taille:[w,h],
    preserve: gl.getContextAttributes()
  });
})()'''
print(ev(expr))
