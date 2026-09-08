#!/usr/bin/env python3
"""Vision GLM (glm-5v-turbo) direct : décrire les captures du jardin."""
import base64, json, os, sys, urllib.request

# Charger .env Hermes
env = {}
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

KEY = env['GLM_API_KEY']
BASE = env.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')
if '/coding/' in BASE:
    BASE = BASE.replace('/coding/', '/')  # vision : endpoint général
BASE = BASE.rstrip('/')

MODEL = 'glm-5v-turbo'

def analyze(path, question):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        'model': MODEL,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64}'}},
                {'type': 'text', 'text': question},
            ],
        }],
        'max_tokens': 2000,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        out = json.load(r)
    return out['choices'][0]['message']['content']

if __name__ == '__main__':
    preuves = os.path.join(os.path.dirname(__file__), '..', 'preuves')
    questions = {
        'veg_fix_vue_dessous.png': "Vue 3D d'un jardin depuis le sol, regard vers le haut dans le houppier d'un arbre. Décris ce que tu vois : y a-t-il des feuilles visibles depuis DESSOUS, des branches, du ciel ? Le feuillage est-il présent ou voit-on surtout du vide ?",
        'veg_fix_vue_dessus.png': "Vue 3D d'un jardin. Décris : voit-on des arbres avec feuillage coloré, un sol texturé, des chemins ? Les arbres ressemblent-ils à des vrais arbres (pas des cubes) ?",
        'veg_fix_automne.png': "Capture 3D d'un jardin en automne. Les feuillages ont-ils des couleurs orangées/rouges ? Les arbres sont-ils texturés et réalistes ?",
        'veg_fix_hiver.png': "Capture 3D d'un jardin en hiver. Les arbres caducs sont-ils nus (sans feuilles) ? Y a-t-il de la neige ou un ciel d'hiver ?",
    }
    for nom, q in questions.items():
        p = os.path.join(preuves, nom)
        if not os.path.exists(p):
            print(f'{nom}: ABSENT'); continue
        try:
            print(f'--- {nom} ---')
            print(analyze(p, q))
        except Exception as e:
            print(f'{nom}: ERREUR {e}')
