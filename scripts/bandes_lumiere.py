#!/usr/bin/env python3
"""Bandes horizontales RGB (haut/centre/bas) d'une capture."""
import sys, os
from PIL import Image

f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'preuves', 'lumiere_ete_midi.png')
im = Image.open(f).convert('RGB')
w, h = im.size
for y, label in [(int(h*0.08), 'haut-ciel'), (int(h*0.5), 'centre-sol'), (int(h*0.9), 'bas-sol')]:
    px = [im.getpixel((x, y)) for x in range(0, w, 50)]
    n = len(px)
    print(label, tuple(sum(p[i] for p in px)//n for i in range(3)))
print('taille', w, h)
