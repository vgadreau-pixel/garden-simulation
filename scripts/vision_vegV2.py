#!/usr/bin/env python3
"""Validation GLM vision des captures vegV2 (post-fix DoubleSide)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
questions = {
    'vegV2_ete_dessus.png': "Vue 3D d'un jardin avec 50 plantes adultes en ete. Decris : voit-on des arbres avec troncs et houppiers, des buissons, du feuillage texture ? Ou des plateaux vides ? Y a-t-il des artefacts (formes noires, feuilles manquantes, objets flottants) ?",
    'vegV2_ete_dessous.png': "Vue 3D depuis DESSOUS le houppier d'un arbre, regard vers le ciel. Voit-on des FEUILLES depuis dessous (faces cachees) ou surtout du vide ? Decris brievement.",
    'vegV2_automne_dessus.png': "Vue 3D du jardin en automne. Les feuillages ont-ils des teintes orangees/rouges/jaunes ? Les arbres sont-ils bien rendus ?",
    'vegV2_hiver_dessus.png': "Vue 3D du jardin en hiver. Les arbres caducs sont-ils NUS (sans feuilles) ? Y a-t-il neige ou ciel d'hiver ?",
}
for nom, q in questions.items():
    p = os.path.join(preuves, nom)
    if not os.path.exists(p):
        print(f'{nom}: ABSENT'); continue
    try:
        print(f'--- {nom} ---')
        print(analyze(p, q)[:900])
    except Exception as e:
        print(f'{nom}: ERREUR {e}')
