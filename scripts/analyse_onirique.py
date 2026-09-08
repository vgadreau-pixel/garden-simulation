#!/usr/bin/env python3
"""Analyse pixel des captures oniriques : bandes ciel/horizon/sol + variance."""
from PIL import Image
from statistics import pstdev
import os, sys

D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
FICHIERS = ['onirique_printemps_fps.png', 'onirique_ete_fps.png',
            'onirique_automne_fps.png', 'onirique_hiver_fps.png',
            'onirique_ete_golden_fps.png', 'onirique_ete_nuit_fps.png',
            'onirique_printemps_dessus.png']

for f in FICHIERS:
    im = Image.open(os.path.join(D, f)).convert('RGB')
    w, h = im.size
    px = im.load()

    def band(y0, y1):
        rs = gs = bs = n = 0
        for y in range(y0, y1, 4):
            for x in range(0, w, 8):
                r, g, b = px[x, y]
                rs += r; gs += g; bs += b; n += 1
        return (rs // n, gs // n, bs // n)

    haut = band(0, h // 3)
    milieu = band(h // 3, 2 * h // 3)
    bas = band(2 * h // 3, h)
    vals = [sum(px[x, y]) / 3 for y in range(0, h, 6) for x in range(0, w, 12)]
    print(f"{f}: {w}x{h} haut={haut} milieu={milieu} bas={bas} std={pstdev(vals):.1f}")
