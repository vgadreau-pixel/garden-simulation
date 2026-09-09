#!/usr/bin/env python3
"""Réduction + planche pour le printemps final."""
from PIL import Image
import os
D = os.path.join(os.path.dirname(__file__), '..', 'preuves')
im = Image.open(os.path.join(D, 'onirique_printemps_final.png')).convert('RGB')
im.resize((640, 360)).save(os.path.join(D, 'pfinal_petit.jpg'), quality=85)
print('pfinal_petit.jpg écrit')
