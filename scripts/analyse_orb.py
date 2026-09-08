#!/usr/bin/env python3
"""Analyse pixel des captures orbitales zoomées."""
import collections
from PIL import Image

for n in ['veg_fix_orb_ete.png', 'veg_fix_orb_automne.png', 'veg_fix_orb_hiver.png']:
    im = Image.open('preuves/' + n).convert('RGB')
    im2 = im.resize((160, 90))
    cols = collections.Counter(im2.getdata())
    top = cols.most_common(8)
    print(n, im.size)
    print('  top:', ' '.join(f'#{r:02x}{g:02x}{b:02x}x{c}' for (r, g, b), c in top))
    verts = sum(c for (r, g, b), c in cols.items() if g > r + 10 and g > b + 10)
    oranges = sum(c for (r, g, b), c in cols.items() if r > g + 15 and g > b + 15)
    tot = 160 * 90
    print(f'  vert: {100*verts/tot:.0f}%  orangé/brun: {100*oranges/tot:.0f}%')
