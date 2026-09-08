#!/usr/bin/env python3
"""Verif ponctuelle : la contre-plongee V4 montre-t-elle des feuilles par en dessous ?"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

q = ("Vue 3D d'un jardin. Cette capture est-elle prise depuis DESSOUS le feuillage "
     "d'un arbre, regardant vers le ciel ? Voit-on des feuilles par leur face "
     "inferieure (avec des trous de ciel entre elles), des branches ? Ou est-ce "
     "une vue de dessus ? Reponds en 4 phrases max.")
print(analyze(os.path.join(os.path.dirname(__file__), '..', 'preuves', 'vegV4_dessous_reel.png'), q))
