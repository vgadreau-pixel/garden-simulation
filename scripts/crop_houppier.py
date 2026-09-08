"""Zoom sur le haut des captures (houppiers) + compte couleurs précis."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for name in ['veg_fps_proche_ete.png', 'veg_fps_proche_automne.png']:
    img = Image.open(os.path.join(BASE, name)).convert('RGB')
    w, h = img.size
    # Bande au-dessus de l'horizon : là où les houppiers devraient être
    bande = img.crop((int(w*0.20), int(h*0.30), int(w*0.80), int(h*0.62)))
    out = name.replace('.png', '_houppier.png')
    bande.save(os.path.join(BASE, out))
    px = list(bande.getdata())
    n = len(px)
    moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
    verts = sum(1 for r, g, b in px if g > r+12 and g > b+12)
    oranges = sum(1 for r, g, b in px if r > g+12 and g > b+8)
    verts_fonce = sum(1 for r, g, b in px if 30 < g < 120 and g > r and g > b)
    print(out, 'moyRGB=', moy, f'verts={100*verts//n}% oranges={100*oranges//n}% verts_fonce={100*verts_fonce//n}%')
