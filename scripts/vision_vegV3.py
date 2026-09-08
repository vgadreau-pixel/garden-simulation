#!/usr/bin/env python3
"""Validation GLM vision des captures V3 (post-fix, bringToFront)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
questions = {
    'vegV3_ete_dessus.png': "Vue 3D jardin ete, 50 plantes adultes. Voit-on des arbres avec houppiers verts feuillus, buissons ? Les arbres ressemblent-ils a de vrais arbres (pas des cubes) ? Artefacts ?",
    'vegV3_ete_dessous.png': "Vue 3D DESSOUS le houppier d'un arbre, regard vers le ciel. Voit-on des feuilles par en dessous (pas que du vide) ?",
    'vegV3_automne_dessus.png': "Vue 3D jardin automne. Feuillages orange/rouge/jaune visibles ?",
    'vegV3_hiver_dessus.png': "Vue 3D jardin hiver. Les arbres caducs sont-ils nus (branches sans feuilles) ? Certains persistants gardent-ils du vert ? Neige/ciel hivernal ?",
}
for nom, q in questions.items():
    p = os.path.join(preuves, nom)
    if not os.path.exists(p):
        print(f'{nom}: ABSENT'); continue
    try:
        print(f'--- {nom} ---')
        print(analyze(p, q)[:600])
    except Exception as e:
        print(f'{nom}: ERREUR {e}')
