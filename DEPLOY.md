# Déploiement — Jardin des Saisons

Application : SPA statique **Vite + three.js** (build dans `dist/`, aucune API, aucun secret requis).
Hébergeur choisi : **GitHub Pages** (gratuit, HTTPS, déclenché à chaque push sur `main`).

URL de production : https://vgadreau-pixel.github.io/garden-simulation/

## Configuration déjà en place

1. **Workflow GitHub Actions** : `.github/workflows/deploy.yml`
   - build (`npm ci` + `vite build --base=./`) puis déploiement de `dist/` vers Pages.
   - `--base=./` : chemins relatifs, indispensables pour une *project page* servie sous `/garden-simulation/`.
2. **Secrets / variables** : **aucun requis.** L'app est 100 % côté client (pas de clé d'API).
   Le workflow utilise seulement le `GITHUB_TOKEN` implicite (permissions `pages: write` + `id-token: write` déjà déclarées).
3. **Source Pages** : doit être réglée sur **GitHub Actions** (voir ci-dessous si ce n'est pas déjà fait).

## Première activation (une seule fois)

```bash
# Source = GitHub Actions (sinon le déploiement échoue avec "Pages not configured")
gh api -X POST repos/vgadreau-pixel/garden-simulation/pages \
  -f build_type=workflow -f source='{"branch":"main","path":"/"}'

# Vérifier
gh api repos/vgadreau-pixel/garden-simulation/pages --jq '.build_type, .html_url'
```

## Déployer

Automatique : tout push sur `main` déclenche build + déploiement.

Manuel (redéploiement sans push) :

```bash
gh workflow run deploy.yml --repo vgadreau-pixel/garden-simulation
```

Suivre l'exécution :

```bash
gh run list --workflow=deploy.yml --repo vgadreau-pixel/garden-simulation --limit 3
gh run watch   # sur la dernière exécution
```

## Vérifier le site en ligne

```bash
curl -sI https://vgadreau-pixel.github.io/garden-simulation/ | head -3
```

## Dépannage

| Symptôme | Cause probable | Fix |
|---|---|---|
| "Get Pages site failed / not configured" | Pages pas encore activé en mode Actions | Commande d'activation ci-dessus |
| Écran blanc après déploiement | Assets servis avec des chemins absolus `/assets/...` | Vérifier que le build utilise bien `--base=./` |
| 404 sur les textures/modèles GLB | Fichiers hors de `public/` | Les mettre dans `public/` pour qu'ils soient copiés dans `dist/` |
| Cache obsolète | CDN Pages | Forcer rechargement (Ctrl+Shift+R) ou relancer le workflow |

## Note : si l'app évolue vers un backend

Si une API ou des variables secrètes deviennent nécessaires, migrer vers un hébergeur avec runtime (Render, Fly.io) : ajouter les secrets via `gh secret set`, sans jamais les committer.
