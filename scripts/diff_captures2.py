#!/usr/bin/env python3
"""Nouvelles captures identiques ? bbox nuit=hud seul, hiver===printemps ?!"""
from PIL import Image, ImageChops
import os
D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
noms = ['onirique_ete_fps', 'onirique_hiver_fps', 'onirique_printemps_fps',
        'onirique_automne_fps', 'onirique_ete_golden_fps', 'onirique_ete_nuit_fps']
imgs = {n: Image.open(os.path.join(D, n + '.png')).convert('RGB') for n in noms}
import hashlib
for n, im in imgs.items():
    print(n, hashlib.md5(im.tobytes()).hexdigest()[:10])
# comparer par paires
for i in range(len(noms)):
    for j in range(i + 1, len(noms)):
        d = ImageChops.difference(imgs[noms[i]], imgs[noms[j]])
        bbox = d.getbbox()
        ext = d.getextrema()
        print(noms[i], 'vs', noms[j], 'bbox:', bbox, 'maxdelta:', max(e[1] for e in ext))
