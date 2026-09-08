#!/usr/bin/env python3
"""Diagnostic : échantillonnage couleur ligne par ligne + crop d'une plante."""
from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'preuves')

for name in ['vegetation_ete.png', 'vegetation_automne.png', 'vegetation_hiver.png']:
    img = Image.open(os.path.join(BASE, name)).convert('RGB')
    w, h = img.size
    print(f"\n=== {name} ({w}x{h}) ===")
    # Moyenne par bande horizontale de 10% de hauteur (zone scène 28-72% largeur)
    for i in range(10):
        bande = img.crop((int(w*0.28), int(h*i*0.1), int(w*0.72), int(h*(i+1)*0.1)))
        px = list(bande.getdata())
        n = len(px)
        moy = tuple(round(sum(c[j] for c in px)/n) for j in range(3))
        print(f"  bande {i}: moyRGB={moy}")
    # Crop d'une plante (zone dense) pour inspection manuelle
    crop = img.crop((int(w*0.35), int(h*0.25), int(w*0.55), int(h*0.60)))
    crop.save(os.path.join(BASE, name.replace('.png', '_crop.png')))
    print(f"  crop sauvegardé: {name.replace('.png', '_crop.png')}")
