#!/usr/bin/env python3
"""Vision : contrôle été (doit être OK) + printemps même protocole."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

for f, q in [
    ('onirique_ete_ctrl.png', "Vue subjective jardin 3D été. 1) Arbres feuillage vert + ciel + relief ? Réponds en 2 lignes."),
    ('onirique_printemps_ctrl.png', "Vue subjective jardin 3D printemps. 1) Feuillage vert clair visible ? 2) Particules/pollen ? 3) Vue 3D immersive ou grille 2D ? Réponds en 3 lignes."),
]:
    print('===', f)
    try:
        print(analyze('preuves/' + f, q)[:400])
    except Exception as e:
        print('ERREUR:', e)
    print()
