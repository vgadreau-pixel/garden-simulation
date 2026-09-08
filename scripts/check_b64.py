#!/usr/bin/env python3
"""Decode les .b64 en 4 captures selectionnees (ATTENTION: jamais utile en prod,
sert uniquement a la verification d'integrite base64 avant attach kanban)."""
import base64, os

scripts = os.path.dirname(__file__)
pairs = [
    ('vegV3_ete_dessus.png.b64', 692256),
    ('vegV3_automne_dessus.png.b64', 719160),
    ('vegV3_hiver_dessus.png.b64', 703252),
    ('vegV4_dessous_reel.png.b64', 255800),
]
ok = True
for nom, expected in pairs:
    p = os.path.join(scripts, nom)
    with open(p) as f:
        b64 = f.read().strip()
    if len(b64) != expected:
        print(f'{nom}: TAILLE {len(b64)} != {expected}'); ok = False; continue
    try:
        data = base64.b64decode(b64, validate=True)
        sig_ok = data[:8] == b'\x89PNG\r\n\x1a\n'
        print(f'{nom}: {len(data)} octets, signature PNG={"OK" if sig_ok else "KO"}')
        if not sig_ok: ok = False
    except Exception as e:
        print(f'{nom}: base64 INVALIDE {e}'); ok = False
print('TOUT_OK' if ok else 'ERREURS')
