#!/usr/bin/env python3
"""Est-ce que la RENDU change vraiment entre captures ? Diff pixel brut
entre onirique_printemps et onirique_ete (fichiers PNG complets)."""
from PIL import Image, ImageChops
from statistics import mean
import os

D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
a = Image.open(os.path.join(D, 'onirique_printemps_fps.png')).convert('RGB')
b = Image.open(os.path.join(D, 'onirique_ete_fps.png')).convert('RGB')
c = Image.open(os.path.join(D, 'onirique_hiver_fps.png')).convert('RGB')
n = Image.open(os.path.join(D, 'onirique_ete_nuit_fps.png')).convert('RGB')

def diff(x, y, label):
    d = ImageChops.difference(x, y)
    h = d.histogram()
    # moyenne par canal
    tot = sum(sum(h[i * 256:(i + 1) * 256]) for i in range(3)) / 3
    m = sum((i % 256) * n_ for i, n_ in enumerate(h[:256]))
    print(label, 'px differents (delta>8):', sum(1 for v in h[256 * 2 + 8:256 * 3] for _ in [0]) and '...')
    # simple : bbox
    print(label, 'bbox:', d.getbbox(), 'extrema:', d.getextrema())

diff(a, b, 'printemps vs ete:')
diff(a, c, 'printemps vs hiver:')
diff(b, n, 'ete jour vs nuit:')
