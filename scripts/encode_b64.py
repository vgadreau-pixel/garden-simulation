#!/usr/bin/env python3
"""Encode les captures V3+V4 en base64 dans des fichiers .b64 pour attach."""
import base64, os

preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
out = os.path.dirname(__file__)
for nom in ['vegV3_ete_dessus.png', 'vegV3_automne_dessus.png', 'vegV3_hiver_dessus.png', 'vegV4_dessous_reel.png']:
    with open(os.path.join(preuves, nom), 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    with open(os.path.join(out, nom + '.b64'), 'w') as f:
        f.write(b64)
    print(nom, len(b64))
