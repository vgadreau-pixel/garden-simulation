#!/usr/bin/env python3
"""Moyennes RGB des captures de contrôle."""
from PIL import Image
import os
D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
for f in ['ctrl_todataurl.png', 'ctrl_cdpshot.png']:
    im = Image.open(os.path.join(D, f)).convert('RGB')
    w, h = im.size
    px = im.load()
    rs = gs = bs = n = 0
    for y in range(0, h, 4):
        for x in range(0, w, 8):
            r, g, b = px[x, y]
            rs += r; gs += g; bs += b; n += 1
    print(f, (rs // n, gs // n, bs // n))
