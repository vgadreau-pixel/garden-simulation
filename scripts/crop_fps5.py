"""Analyse captures proches."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for name in ['veg_fps_proche_ete.png', 'veg_fps_proche_automne.png']:
    img = Image.open(os.path.join(BASE, name)).convert('RGB')
    w, h = img.size
    centre = img.crop((int(w*0.20), int(h*0.10), int(w*0.80), int(h*0.80)))
    out = name.replace('.png', '_crop.png')
    centre.save(os.path.join(BASE, out))
    px = list(centre.getdata())
    n = len(px)
    moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
    verts = sum(1 for r, g, b in px if g > r+15 and g > b+15)
    oranges = sum(1 for r, g, b in px if r > g+15 and g > b+10)
    print(out, 'moyRGB=', moy, f'verts={100*verts//n}% oranges={100*oranges//n}%')
