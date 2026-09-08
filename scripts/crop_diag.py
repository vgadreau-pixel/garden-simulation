"""Analyse rapide diag_fps_haut.png."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
img = Image.open(os.path.join(BASE, 'diag_fps_haut.png')).convert('RGB')
w, h = img.size
centre = img.crop((int(w*0.25), int(h*0.15), int(w*0.75), int(h*0.75)))
centre.save(os.path.join(BASE, 'diag_fps_haut_crop.png'))
px = list(centre.getdata())
n = len(px)
moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
verts = sum(1 for r, g, b in px if g > r+15 and g > b+15)
print('diag_fps_haut_crop moyRGB=', moy, f'verts={100*verts//n}%')
