"""Crop rapide des captures FPS pour analyse visuelle."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for name in ['vegetation_ete_fps.png', 'vegetation_automne_fps.png']:
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        print('absent:', name)
        continue
    img = Image.open(p).convert('RGB')
    w, h = img.size
    centre = img.crop((int(w*0.30), int(h*0.20), int(w*0.70), int(h*0.70)))
    out = name.replace('.png', '_crop.png')
    centre.save(os.path.join(BASE, out))
    px = list(centre.getdata())
    n = len(px)
    moy = tuple(round(sum(c[i] for c in px)/n) for i in range(3))
    print(out, img.size, 'moyRGB=', moy)
