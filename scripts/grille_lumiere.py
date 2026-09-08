#!/usr/bin/env python3
"""Grille 8x8 de luminance (niveau de gris 0-255) pour détecter zone figée."""
import sys, os
from PIL import Image

f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'preuves', 'lumiere_ete_midi.png')
im = Image.open(f).convert('L').resize((16, 9))
px = list(im.getdata())
print(os.path.basename(f))
for row in range(9):
    print(' '.join(f'{px[row*16+c]:3d}' for c in range(16)))
