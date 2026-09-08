#!/usr/bin/env python3
"""Copie les 4 captures vers le workspace kanban de la tache (livrable durable)."""
import shutil, os

src = os.path.join(os.path.dirname(__file__), '..', 'preuves')
dst = '/home/vgadreau/.hermes/kanban/workspaces/t_e17a0961/preuves'
os.makedirs(dst, exist_ok=True)
for nom in ['vegV3_ete_dessus.png', 'vegV3_automne_dessus.png', 'vegV3_hiver_dessus.png', 'vegV4_dessous_reel.png']:
    shutil.copy2(os.path.join(src, nom), os.path.join(dst, nom))
    print('copie:', os.path.join(dst, nom))
