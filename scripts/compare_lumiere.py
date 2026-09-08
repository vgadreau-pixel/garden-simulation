#!/usr/bin/env python3
"""Analyse zone centrale du jardin (exclut panneaux UI) : ciel implicite (pas de
ciel en vue ortho de dessus), sol, parcelles. Compare aussi 2 captures."""
import sys, os
from PIL import Image

PREUVES = os.path.join(os.path.dirname(__file__), '..', 'preuves')

def zone(nom, x0f, y0f, x1f, y1f):
    im = Image.open(os.path.join(PREUVES, nom)).convert('RGB')
    w, h = im.size
    x0, y0, x1, y1 = int(w*x0f), int(h*y0f), int(w*x1f), int(h*y1f)
    px = [im.getpixel((x, y)) for x in range(x0, x1, 8) for y in range(y0, y1, 8)]
    n = len(px)
    return tuple(sum(p[i] for p in px)//n for i in range(3)), n

# En vue ortho de dessus, tout l'écran est "sol". Zones : centre (parcelles),
# coins (herbe autour), sans les panneaux latéraux (x 0.25-0.75).
for nom in ['ete_matin', 'ete_midi', 'ete_crepuscule', 'ete_nuit',
            'hiver_matin', 'hiver_midi', 'hiver_crepuscule', 'hiver_nuit']:
    centre, _ = zone(f'lumiere_{nom}.png', 0.40, 0.35, 0.60, 0.60)
    herbe, _ = zone(f'lumiere_{nom}.png', 0.26, 0.80, 0.55, 0.92)
    print(f'{nom:18s} parcelles {centre}  herbe {herbe}')
