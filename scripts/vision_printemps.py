#!/usr/bin/env python3
"""Vision : printemps v10."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

q = "Vue subjective jardin 3D printemps (a hauteur d homme). 1) Feuillage vert visible ? 2) Vue 3D immersive ou grille 2D ? 3) Sol, chemins, vegetaux ? Reponds en 3 lignes."
try:
    print(analyze('preuves/onirique_printemps_v10.png', q)[:500])
except Exception as e:
    print('ERREUR:', e)
