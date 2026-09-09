#!/usr/bin/env python3
"""Photos des 4 captures candidates pour comparaison croisée : taille fichier,
 Dimensions, et surtout comparaison printemps ACTUEL vs celui d'hier (04ac39)
 et vs été (validée). Puis décision."""
from PIL import Image
import hashlib, os
D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
CIBLES = ['onirique_ete_fps.png', 'onirique_hiver_fps.png', 'onirique_printemps_fps.png',
          'onirique_automne_fps.png', 'onirique_ete_golden_fps.png', 'onirique_ete_nuit_fps.png']
for f in CIBLES:
    p = os.path.join(D, f)
    im = Image.open(p).convert('RGB')
    h = hashlib.md5(im.tobytes()).hexdigest()[:10]
    print(f, h, os.path.getsize(p) // 1024, 'Ko', im.size)
