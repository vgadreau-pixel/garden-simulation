"""Crop des vues FPS pour analyse."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for name in ['veg_fps_vue1.png', 'veg_fps_vue2.png']:
    p = os.path.join(BASE, name)
    img = Image.open(p).convert('RGB')
    w, h = img.size
    centre = img.crop((int(w*0.30), int(h*0.20), int(w*0.70), int(h*0.70)))
    out = name.replace('.png', '_crop.png')
    centre.save(os.path.join(BASE, out))
    px = list(centre.getdata())
    n = len(px)
    moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
    verts = sum(1 for r, g, b in px if g > r+15 and g > b+15)
    print(out, 'moyRGB=', moy, f'verts={100*verts//n}%')
