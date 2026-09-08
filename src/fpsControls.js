// Contrôles première personne (FPS) : ZQSD/WASD + souris (Pointer Lock).
// Une seule couche : caméra perspective dédiée, marche au sol (yeux ~1,70 m),
// collisions cylindres approximatifs contre les plantes (pas de physics engine),
// bornes du terrain. Le mode orbital existant (OrthoTopControls) est préservé
// et la bascule se fait par la touche V (gérée dans main.js).
import * as THREE from 'three';
import { GRID_EXTENT, GROUND_MARGIN } from './constants.js';

const HAUTEUR_YEUX = 1.70; // m
const VITESSE_MARCHE = 3.2; // m/s
const VITESHE_COURSE = 6.0; // m/s (Shift)
const RAYON_JOUEUR = 0.35; // m — cylindre de collision du joueur
const SENSIBILITE = 0.0022; // rad / pixel de mouvement souris
const ACCEL = 14; // raideur d'accélération / freinage (lerp exponentiel)

/** Rayon du cylindre de collision d'une plante selon son type. */
function rayonCollision(plante) {
  if (!plante) return 0.2;
  if (plante.type === 'arbre') return 0.55;
  if (plante.type === 'arbuste') return 0.45;
  return 0.18; // fleurs / légumes : on frôle, on ne traverse pas
}

export class FpsControls {
  /**
   * @param camera THREE.PerspectiveCamera dédiée (créée par main.js)
   * @param domElement canvas de rendu
   * @param getInstances () => instances[] du jardin (collisions dynamiques)
   */
  constructor(camera, domElement, getInstances) {
    this.camera = camera;
    this.domElement = domElement;
    this.getInstances = getInstances || (() => []);

    this.enabled = false; // actif seulement en mode FPS
    this.position = new THREE.Vector3(0, HAUTEUR_YEUX, 14); // départ : au sud de la grille, dans l'allée
    this.velocity = new THREE.Vector3();
    this.yaw = Math.PI; // regarde vers -z (vers le jardin) — cf. convention orbital « nord = -z »
    this.pitch = 0;

    // Bornes : rester sur la pelouse (grille + marge d'herbe, moins un peu).
    const LIMITE = GRID_EXTENT / 2 + GROUND_MARGIN - 1; // ≈ 21.4 m
    this.minX = -LIMITE; this.maxX = LIMITE;
    this.minZ = -LIMITE; this.maxZ = LIMITE;

    this._keys = new Set(); // codes physiques (KeyW…) — agnostique AZERTY/QWERTY
    this._locked = false;

    this._onKeyDown = (e) => {
      if (!this.enabled) return;
      // Ignorer les touches modifiées (Ctrl+… du navigateur).
      if (e.ctrlKey || e.altKey || e.metaKey) return;
      this._keys.add(e.code);
      if (e.code.startsWith('Arrow') || ['Space'].includes(e.code)) e.preventDefault();
    };
    this._onKeyUp = (e) => this._keys.delete(e.code);
    this._onMouseMove = (e) => {
      if (!this.enabled || !this._locked) return;
      this.yaw -= e.movementX * SENSIBILITE;
      this.pitch -= e.movementY * SENSIBILITE;
      const L = Math.PI / 2 - 0.06;
      this.pitch = Math.max(-L, Math.min(L, this.pitch));
    };
    this._onLockChange = () => {
      this._locked = document.pointerLockElement === this.domElement;
      this.onLockChange?.(this._locked);
      // Échap ou perte du focus : les touches resteraient « collées » sinon.
      if (!this._locked) this._keys.clear();
    };

    window.addEventListener('keydown', this._onKeyDown);
    window.addEventListener('keyup', this._onKeyUp);
    document.addEventListener('mousemove', this._onMouseMove);
    document.addEventListener('pointerlockchange', this._onLockChange);
  }

  /** Entrée en mode FPS : demande le pointer lock (doit venir d'un geste utilisateur). */
  activer() {
    this.enabled = true;
    this.domElement.requestPointerLock?.();
    this.updateCamera();
  }

  desactiver() {
    this.enabled = false;
    this._keys.clear();
    this.velocity.set(0, 0, 0);
    if (document.pointerLockElement === this.domElement) document.exitPointerLock?.();
  }

  /** Direction avant (yaw seul, la marche reste horizontale). */
  _forward(out) {
    return out.set(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
  }
  _right(out) {
    return out.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw));
  }

  /** Direction demandée par les touches (ZQSD/WASD/flèches), normalisée. */
  directionDemandee(out) {
    const k = this._keys;
    let f = 0, s = 0;
    if (k.has('KeyW') || k.has('ArrowUp')) f += 1; // Z (AZERTY) / W (QWERTY)
    if (k.has('KeyS') || k.has('ArrowDown')) f -= 1;
    if (k.has('KeyA') || k.has('ArrowLeft')) s -= 1; // Q (AZERTY) / A (QWERTY)
    if (k.has('KeyD') || k.has('ArrowRight')) s += 1;
    if (!f && !s) return out.set(0, 0, 0);
    this._forward(out).multiplyScalar(f);
    const r = this._right(new THREE.Vector3()).multiplyScalar(s);
    out.add(r).normalize();
    return out;
  }

  /** Pas de physique : intégration directe + résolution de pénétration.
   * Le pas est sous-découpé (≤ 33 ms) : au pire 0,2 m parcourus par sous-pas,
   * inférieur au plus petit rayon de collision (0,53 m) → aucun tunneling,
   * même sur une machine lente qui rend à quelques fps. */
  update(dt) {
    if (!this.enabled) return;
    const dtMax = 1 / 30;
    let n = Math.min(120, Math.ceil(dt / dtMax));
    if (n < 1) n = 1;
    const pas = dt / n;
    for (let i = 0; i < n; i++) this._sousPas(pas);
  }

  _sousPas(dt) {
    const dir = this.directionDemandee(new THREE.Vector3());
    const vitesse = (this._keys.has('ShiftLeft') || this._keys.has('ShiftRight'))
      ? VITESHE_COURSE : VITESSE_MARCHE;
    const cible = dir.multiplyScalar(vitesse);
    // Accélération / freinage doux (indépendant du framerate).
    const a = 1 - Math.exp(-ACCEL * dt);
    this.velocity.x += (cible.x - this.velocity.x) * a;
    this.velocity.z += (cible.z - this.velocity.z) * a;

    this.position.x += this.velocity.x * dt;
    this.position.z += this.velocity.z * dt;

    // ── Collisions ──
    // 1. Bornes du terrain (mur invisible au bord de la pelouse).
    this.position.x = Math.max(this.minX, Math.min(this.maxX, this.position.x));
    this.position.z = Math.max(this.minZ, Math.min(this.maxZ, this.position.z));
    // 2. Cylindres des plantes : rejet hors du disque (troncs / touffes).
    for (const inst of this.getInstances()) {
      const p = inst.group?.position;
      if (!p) continue;
      const r = rayonCollision(inst.plante) + RAYON_JOUEUR;
      const dx = this.position.x - p.x;
      const dz = this.position.z - p.z;
      const d2 = dx * dx + dz * dz;
      if (d2 < r * r && d2 > 1e-8) {
        const d = Math.sqrt(d2);
        this.position.x = p.x + (dx / d) * r;
        this.position.z = p.z + (dz / d) * r;
      }
    }
    // 3. Bassin : obstacle statique (on ne marche pas sur l'eau).
    for (const o of OBSTACLES_STATIQUES) {
      const r = o.r + RAYON_JOUEUR;
      const dx = this.position.x - o.x;
      const dz = this.position.z - o.z;
      const d2 = dx * dx + dz * dz;
      if (d2 < r * r && d2 > 1e-8) {
        const d = Math.sqrt(d2);
        this.position.x = o.x + (dx / d) * r;
        this.position.z = o.z + (dz / d) * r;
      }
    }

    this.updateCamera();
  }

  /** Applique position + orientation à la caméra perspective. */
  updateCamera() {
    const c = this.camera;
    c.position.set(this.position.x, HAUTEUR_YEUX, this.position.z);
    const cp = Math.cos(this.pitch);
    c.lookAt(
      c.position.x - Math.sin(this.yaw) * cp,
      c.position.y + Math.sin(this.pitch),
      c.position.z - Math.cos(this.yaw) * cp,
    );
  }

  dispose() {
    window.removeEventListener('keydown', this._onKeyDown);
    window.removeEventListener('keyup', this._onKeyUp);
    document.removeEventListener('mousemove', this._onMouseMove);
    document.removeEventListener('pointerlockchange', this._onLockChange);
  }
}
