#!/usr/bin/env python3
"""Ecrit chaque .b64 sur UNE ligne pour lecture integrale via read_file."""
import os
scripts = os.path.dirname(__file__)
for nom in ['vegV3_ete_dessus.png.b64', 'vegV3_automne_dessus.png.b64', 'vegV3_hiver_dessus.png.b64', 'vegV4_dessous_reel.png.b64']:
    p = os.path.join(scripts, nom)
    with open(p) as f:
        data = f.read().replace('\n', '')
    with open(p, 'w') as f:
        f.write(data)
print('ok - une ligne par fichier')
