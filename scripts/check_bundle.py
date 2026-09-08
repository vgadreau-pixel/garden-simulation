#!/usr/bin/env python3
"""Vérifie que le bundle contient les nouvelles couleurs de palette."""
data = open('/home/vgadreau/.hermes/workspace/jardin-des-saisons/dist/assets/index-Ds1rzzQx.js').read()
for hexa in ('a8cdea', 'c2e0f0', 'e8d9b0', 'e4ecf2'):
    dec = str(int(hexa, 16))
    print(hexa, '=', dec, 'présent:', dec in data)
