#!/usr/bin/env python3
"""Analyse pixel fine d'une capture : rangées d'échantillons en croix pour
visualiser la structure (panneaux UI vs scène vs dôme en bord d'écran)."""
import sys, os
from PIL import Image

f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'preuves', 'lumiere_ete_midi.png')
im = Image.open(f).convert('RGB')
w, h = im.size
print(f'{f}  {w}x{h}')
# rangée horizontale au centre (y=50%) et au 8% (au-dessus des panneaux)
for yf in (0.06, 0.5):
    y = int(h * yf)
    row = []
    for xf in [i/24 for i in range(24)]:
        x = int(w * xf)
        r, g, b = im.getpixel((x, y))
        row.append(f'{r:3d},{g:3d},{b:3d}')
    print(f'y={yf:.0%}: ' + ' | '.join(row))
