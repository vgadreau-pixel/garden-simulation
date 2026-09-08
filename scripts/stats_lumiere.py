#!/usr/bin/env python3
"""Stats pixel des captures : moyenne globale, bande ciel (haut), bande sol (bas)."""
import glob, sys, os
try:
    from PIL import Image
except ImportError:
    print('PIL absent'); sys.exit(1)

def avg(ps):
    return tuple(sum(p[i] for p in ps)//len(ps) for i in range(3))

for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'preuves', 'lumiere_*.png'))):
    im = Image.open(f).convert('RGB')
    w, h = im.size
    im = im.resize((64, 36))
    px = list(im.getdata())
    glob_avg = avg(px)
    sky = avg(px[:64*6])
    ground = avg(px[-64*6:])
    print(os.path.basename(f), 'global', glob_avg, 'ciel', sky, 'sol', ground)
