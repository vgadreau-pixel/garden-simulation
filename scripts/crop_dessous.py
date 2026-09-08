"""Analyse veg_dessous.png : houppier vu du dessous."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
img = Image.open(os.path.join(BASE, 'veg_dessous.png')).convert('RGB')
w, h = img.size
centre = img.crop((int(w*0.15), int(h*0.05), int(w*0.85), int(h*0.85)))
centre.save(os.path.join(BASE, 'veg_dessous_crop.png'))
px = list(centre.getdata())
n = len(px)
moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
verts = sum(1 for r, g, b in px if g > r+12 and g > b+12)
print('veg_dessous_crop moyRGB=', moy, f'verts={100*verts//n}%')
