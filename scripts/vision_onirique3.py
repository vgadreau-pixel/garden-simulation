#!/usr/bin/env python3
"""Vision GLM : printemps + automne après re-capture avec attente 20 s."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

for f, q in [
    ('onirique_printemps_fps.png', "Vue subjective jardin 3D printemps. 1) Feuillage vert clair ? 2) Particules/pollen dans l air ? 3) Sol et allées visibles ? Réponds brièvement."),
    ('onirique_automne_fps.png', "Vue subjective jardin 3D automne. 1) Teintes orangées/jaunes ? 2) Pétales/feuilles flottantes ? 3) Ambiance automnale ? Réponds brièvement."),
]:
    print('===', f)
    try:
        print(analyze('preuves/' + f, q)[:450])
    except Exception as e:
        print('ERREUR:', e)
    print()
