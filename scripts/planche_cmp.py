#!/usr/bin/env python3
"""Couper une planche 2x2 : printemps vs été pour comparer visuellement
(même cadrage). Sauver en petit jpg pour analyse humaine + stats couleurs."""
from PIL import Image
import os
D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
a = Image.open(os.path.join(D, 'onirique_printemps_j105.png')).convert('RGB').resize((640, 360))
b = Image.open(os.path.join(D, 'onirique_ete_fps.png')).convert('RGB').resize((640, 360))
planche = Image.new('RGB', (1280, 360))
planche.paste(a, (0, 0))
planche.paste(b, (640, 0))
planche.save(os.path.join(D, 'cmp_printemps_ete.jpg'), quality=88)
print('cmp_printemps_ete.jpg écrit (gauche=printemps j105, droite=été)')
