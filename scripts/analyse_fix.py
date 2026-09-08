#!/usr/bin/env python3
"""Analyse pixel des captures finales."""
import collections
from PIL import Image

NOMS = ['veg_fix_vue_dessus.png', 'veg_fix_vue_dessous.png', 'veg_fix_automne.png', 'veg_fix_hiver.png']
for n in NOMS:
    im = Image.open('preuves/' + n).convert('RGB')
    im2 = im.resize((160, 90))
    cols = collections.Counter(im2.getdata())
    top = cols.most_common(6)
    print(n, im.size)
    print('  top:', ' '.join(f'#{r:02x}{g:02x}{b:02x}x{c}' for (r, g, b), c in top))
    verts = sum(c for (r, g, b), c in cols.items() if g > r + 10 and g > b + 10)
    tot = 160 * 90
    print(f'  pixels dominante verte: {100*verts/tot:.0f}%')
