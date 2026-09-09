#!/usr/bin/env python3
"""Découpe dbg_13h en 4 quadrants réduits et assemble une planche contact
(les requêtes vision timeout sur image pleine ; on tente une version réduite)."""
from PIL import Image
import os
D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
im = Image.open(os.path.join(D, 'dbg_13h.png')).convert('RGB')
im2 = im.resize((640, 360))
im2.save(os.path.join(D, 'dbg_13h_petit.jpg'), quality=88)
print('dbg_13h_petit.jpg écrit')

# Crop centre en 320x240 (zone avec plantes)
im.crop((400, 200, 912, 584)).resize((512, 384)).save(os.path.join(D, 'dbg_13h_centre.jpg'), quality=88)
print('dbg_13h_centre.jpg écrit')

# Golden hour crop
g = Image.open(os.path.join(D, 'onirique_ete_golden_fps.png')).convert('RGB')
g.resize((640, 360)).save(os.path.join(D, 'dbg_golden_petit.jpg'), quality=88)
print('dbg_golden_petit.jpg écrit')
