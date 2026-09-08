#!/usr/bin/env python3
"""Vision GLM sur les captures arbres adultes (zoom orbital conservé)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from vision_glm import analyze

preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
questions = {
    'veg_adulte_ete.png': "Capture 3D vue de dessus d'un jardin en été (15 juillet, 12:00). Question unique : les arbres ont-ils des houppiers de feuillage vert fournis et texturés (vrais modèles d'arbres, pas des cubes/sphères unies) ? Réponds en 3 phrases max.",
    'veg_adulte_automne.png': "Capture 3D vue de dessus d'un jardin en automne (17 octobre, 12:00). Question unique : certains feuillages ont-ils des teintes orangées/rouges/brunes d'automne, différentes du vert d'été ? Réponds en 3 phrases max.",
    'veg_adulte_hiver.png': "Capture 3D vue de dessus d'un jardin en hiver (16 janvier, 12:00). Question unique : les arbres caducs paraissent-ils nus (houppiers disparus/réduits) alors que des conifères ou arbustes persistants restent verts ? Réponds en 3 phrases max.",
}
for nom, q in questions.items():
    p = os.path.join(preuves, nom)
    print(f'=== {nom} ===')
    try:
        print(analyze(p, q))
    except Exception as e:
        print('ERREUR', e)
    print()
