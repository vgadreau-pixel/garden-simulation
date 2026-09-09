#!/usr/bin/env python3
"""Vision : printemps jour 105."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

q = "Vue subjective jardin 3D printemps. 1) Feuillage vert ? 2) Vue 3D immersive ou grille 2D ? 3) Sol et chemins visibles ? 3 lignes max."
try:
    print(analyze('preuves/onirique_printemps_j105.png', q)[:400])
except Exception as e:
    print('ERREUR:', e)
