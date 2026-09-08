#!/usr/bin/env python3
"""Profil vertical de la capture FPS fusion : trouver l'horizon et le vert."""
import sys
sys.path.insert(0, '/home/vgadreau/.hermes/workspace/jardin-des-saisons/scripts')
from analyse_capture import png_pixels

w, h, px = png_pixels('/home/vgadreau/.hermes/workspace/jardin-des-saisons/preuves/fps_vue_jardin_fusion.png')
print(f'{w}x{h} — vert (G-R) par bande de 5% :')
for i in range(20):
    y0, y1 = i * 0.05, (i + 1) * 0.05
    r = g = b = n = 0
    for y in range(int(h * y0), int(h * y1), 3):
        for x in range(0, w, 8):
            o = (y * w + x) * 3
            r += px[o]; g += px[o + 1]; b += px[o + 2]; n += 1
    r, g, b = r / n, g / n, b / n
    bar = '#' * int(max(0, g - r) / 2)
    print(f'  {int(y0*100):3d}%: R{r:3.0f} G{g:3.0f} B{b:3.0f}  vert+{g-r:4.0f} {bar}')
