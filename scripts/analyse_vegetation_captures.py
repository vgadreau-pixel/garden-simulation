#!/usr/bin/env python3
"""Analyse couleur des captures vegetation_*.png (zone centrale de la scène)."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for name in ['vegetation_ete.png', 'vegetation_automne.png', 'vegetation_hiver.png']:
    img = Image.open(os.path.join(BASE, name)).convert('RGB')
    w, h = img.size
    centre = img.crop((int(w*0.28), int(h*0.30), int(w*0.72), int(h*0.90)))
    px = list(centre.getdata())
    n = len(px)
    moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
    verts = sum(1 for r, g, b in px if g > r+15 and g > b+15)
    oranges = sum(1 for r, g, b in px if r > g+15 and g > b+10)
    clairs = sum(1 for r, g, b in px if r+g+b > 350)
    print(f"{name}: {w}x{h} moyRGB={moy} verts={100*verts//n}% oranges={100*oranges//n}% clairs={100*clairs//n}%")
