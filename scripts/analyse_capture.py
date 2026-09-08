#!/usr/bin/env python3
"""Analyse pixel de la capture FPS : ciel en haut, sol/herbe en bas,
horizon au tiers moyen — signature d'une vue première personne à 1,70 m."""
import struct, zlib, sys

def png_pixels(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat = b''
    w = h = 0
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', chunk[:10])
            assert bd == 8 and ct == 2, (bd, ct)
        elif typ == b'IDAT':
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    px = bytearray(w * h * 3)
    prev = bytearray(w * 3)
    i = 0
    for y in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i+w*3]); i += w*3
        if f == 1:
            for x in range(3, len(line)):
                line[x] = (line[x] + line[x-3]) & 0xFF
        elif f == 2:
            for x in range(len(line)):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif f == 3:
            for x in range(len(line)):
                a = line[x-3] if x >= 3 else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(len(line)):
                a = line[x-3] if x >= 3 else 0
                b = prev[x-3] if x >= 3 else 0
                c = prev[x] if x >= 3 else prev[x]
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        px[y*w*3:(y+1)*w*3] = line
        prev = line
    return w, h, px

def zone(px, w, h, y0, y1):
    """Moyenne RGB d'une bande horizontale."""
    r = g = b = n = 0
    for y in range(int(h*y0), int(h*y1), 4):
        for x in range(0, w, 16):
            o = (y*w + x) * 3
            r += px[o]; g += px[o+1]; b += px[o+2]; n += 1
    return r/n, g/n, b/n

for path in sys.argv[1:]:
    w, h, px = png_pixels(path)
    haut = zone(px, w, h, 0.02, 0.20)
    milieu = zone(px, w, h, 0.45, 0.60)
    bas = zone(px, w, h, 0.80, 0.98)
    print(path.split('/')[-1], f'{w}x{h}')
    print('  haut  RGB %.0f/%.0f/%.0f (ciel attendu: bleu/gris dominant)' % haut)
    print('  milieu RGB %.0f/%.0f/%.0f' % milieu)
    print('  bas   RGB %.0f/%.0f/%.0f (herbe attendu: vert dominant)' % bas)
    ciel = haut[2] > haut[1] - 10  # bleu pas inférieur au vert
    herbe = bas[1] > bas[0] and bas[1] > bas[2]
    horizon = milieu != haut and milieu != bas
    print('  verdict: ciel=%s herbe_bas=%s horizon_marque=%s' % (ciel, herbe, horizon))
