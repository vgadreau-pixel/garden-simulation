"""Zoom analyse veg_zoom."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for name in ['veg_zoom_ete.png', 'veg_zoom_automne.png']:
    img = Image.open(os.path.join(BASE, name)).convert('RGB')
    w, h = img.size
    centre = img.crop((int(w*0.15), int(h*0.05), int(w*0.85), int(h*0.85)))
    out = name.replace('.png', '_crop.png')
    centre.save(os.path.join(BASE, out))
    px = list(centre.getdata())
    n = len(px)
    moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
    verts = sum(1 for r, g, b in px if g > r+12 and g > b+12)
    oranges = sum(1 for r, g, b in px if r > g+12 and g > b+8)
    print(out, 'moyRGB=', moy, f'verts={100*verts//n}% oranges={100*oranges//n}%')
