// Plantation interactive : catalogue d'espèces (panneau gauche), clic sur une
// parcelle pour planter / retirer un végétal, sauvegarde du plan de jardin en
// localStorage.
//
// Règles :
//  - une espèce est sélectionnée dans le catalogue → un clic sur une parcelle
//    libre la plante (maturité initiale « jeune pousse », rotation aléatoire
//    légère pour casser l'uniformité) ;
//  - un clic (même outil) sur une parcelle occupée retire la plante ;
//  - clic droit (contextmenu) retire aussi la plante — geste naturel ;
//  - le plan (liste de {espece, parcelle}) est persisté et restauré au
//    démarrage, indépendamment du climat choisi.
import * as THREE from 'three';
import { PLANTES, planteParId } from './data/plants.js';
import { PLOT_COUNT, PLOT_SIZE, PITCH } from './constants.js';
import { creerInstancePlante } from './plantInstances.js';
import { habillerInstance } from './vegetation.js';

const CLE_SAUVEGARDE = 'jardin-saisons.plan.v1';

/** Centre monde (x, z) d'une parcelle (ix, iz ∈ 0..PLOT_COUNT-1). */
export function centreParcelle(ix, iz) {
  const offset = (PLOT_COUNT - 1) / 2;
  return { x: (ix - offset) * PITCH, z: (iz - offset) * PITCH };
}

/** Index de parcelle sous un point monde, ou null si hors grille. */
export function parcelleSous(x, z) {
  const offset = (PLOT_COUNT - 1) / 2;
  const fx = x / PITCH + offset;
  const fz = z / PITCH + offset;
  const ix = Math.floor(fx + 0.5);
  const iz = Math.floor(fz + 0.5);
  if (ix < 0 || ix >= PLOT_COUNT || iz < 0 || iz >= PLOT_COUNT) return null;
  // Rejeter les clics dans les allées : distance au centre > demi-parcelle.
  const c = centreParcelle(ix, iz);
  if (Math.abs(x - c.x) > PLOT_SIZE / 2 || Math.abs(z - c.z) > PLOT_SIZE / 2) return null;
  return { ix, iz };
}

export function creerPlantation(scene, canvas, camera, clock, { onChangement } = {}) {
  const group = new THREE.Group();
  group.name = 'plantations';
  scene.add(group);

  // Occupations : clé "ix,iz" → instance.
  const occupees = new Map();
  // Sélection courante du catalogue (null = outil « retirer »).
  let especeSelectionnee = PLANTES[0].id;
  const listenersChangement = [];
  function signaler() {
    if (onChangement) onChangement(compter());
    for (const l of listenersChangement) l();
  }
  /** Abonnement interne (le compteur du catalogue s'en sert). */
  function surChangement(fn) { listenersChangement.push(fn); }

  const raycaster = new THREE.Raycaster();
  const planSol = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

  /** Point monde sous le curseur (intersection avec le plan du sol). */
  function pointSousCurseur(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const nx = ((clientX - rect.left) / rect.width) * 2 - 1;
    const ny = -(((clientY - rect.top) / rect.height) * 2 - 1);
    raycaster.setFromCamera(new THREE.Vector2(nx, ny), camera);
    const pt = new THREE.Vector3();
    return raycaster.ray.intersectPlane(planSol, pt) ? pt : null;
  }

  // ── Surbrillance de la parcelle visée ──
  const surbrillance = new THREE.Mesh(
    new THREE.PlaneGeometry(PLOT_SIZE - 0.05, PLOT_SIZE - 0.05),
    new THREE.MeshBasicMaterial({ color: 0xfff3c4, transparent: true, opacity: 0.0, depthWrite: false })
  );
  surbrillance.rotation.x = -Math.PI / 2;
  surbrillance.position.y = 0.07;
  surbrillance.visible = false;
  group.add(surbrillance);

  function majSurbrillance(e) {
    const pt = pointSousCurseur(e.clientX, e.clientY);
    const p = pt ? parcelleSous(pt.x, pt.z) : null;
    if (!p) {
      surbrillance.visible = false;
      return;
    }
    const c = centreParcelle(p.ix, p.iz);
    surbrillance.position.set(c.x, 0.07, c.z);
    const occupee = occupees.has(`${p.ix},${p.iz}`);
    surbrillance.material.color.set(occupee ? 0xd98880 : 0xfff3c4);
    surbrillance.material.opacity = 0.35;
    surbrillance.visible = true;
  }

  // ── Planter / retirer ──
  function planter(ix, iz, plante, { sauvegarder = true, maturite = 0.12 } = {}) {
    const cle = `${ix},${iz}`;
    if (occupees.has(cle)) return null;
    const c = centreParcelle(ix, iz);
    const inst = creerInstancePlante(
      plante,
      new THREE.Vector3(c.x, 0, c.z),
      maturite,
      (Math.random() - 0.5) * 0.5
    );
    inst.parcelle = cle;
    group.add(inst.group);
    occupees.set(cle, inst);
    habillerInstance(inst); // modèle GLTF texturé (asynchrone, repli primitives)
    if (sauvegarder) signaler();
    return inst;
  }

  function retirer(ix, iz, { sauvegarder = true } = {}) {
    const cle = `${ix},${iz}`;
    const inst = occupees.get(cle);
    if (!inst) return false;
    group.remove(inst.group);
    occupees.delete(cle);
    if (sauvegarder) signaler();
    return true;
  }

  function basculer(pt) {
    const p = parcelleSous(pt.x, pt.z);
    if (!p) return false;
    const cle = `${p.ix},${p.iz}`;
    if (occupees.has(cle)) {
      retirer(p.ix, p.iz);
      return true;
    }
    const plante = planteParId(especeSelectionnee);
    if (plante) planter(p.ix, p.iz, plante);
    return true;
  }

  // ── Événements souris ──
  // On distingue clic (poser/retirer) et drag (pan caméra) : un déplacement
  // de plus de 6 px entre pointerdown et pointerup annule l'action.
  let downXY = null;
  function onPointerDown(e) {
    if (e.button !== 0) return;
    downXY = { x: e.clientX, y: e.clientY };
  }
  function onPointerUp(e) {
    if (e.button !== 0 || !downXY) return;
    const dx = e.clientX - downXY.x;
    const dy = e.clientY - downXY.y;
    downXY = null;
    if (dx * dx + dy * dy > 36) return; // c'était un drag de caméra
    if (e.target !== canvas) return;
    const pt = pointSousCurseur(e.clientX, e.clientY);
    if (pt && basculer(pt)) majSurbrillance(e);
  }
  function onPointerMove(e) {
    if (downXY) return; // drag en cours : pas de surbrillance parasite
    majSurbrillance(e);
  }
  function onContextMenu(e) {
    if (e.target !== canvas) return;
    e.preventDefault();
    const pt = pointSousCurseur(e.clientX, e.clientY);
    if (!pt) return;
    const p = parcelleSous(pt.x, pt.z);
    if (p) retirer(p.ix, p.iz);
  }
  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointerup', onPointerUp);
  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerleave', () => { surbrillance.visible = false; });
  canvas.addEventListener('contextmenu', onContextMenu);

  // ── Sauvegarde / restauration (localStorage) ──
  function sauvegarder() {
    try {
      const plan = [...occupees.entries()].map(([cle, inst]) => ({
        parcelle: cle,
        espece: inst.plante.id,
        maturite: Number(inst.maturite.toFixed(3)),
      }));
      localStorage.setItem(CLE_SAUVEGARDE, JSON.stringify({ plan, climat: clock.climat }));
    } catch { /* quota / mode privé : on ignore, le jeu reste jouable */ }
  }
  listenersChangement.push(sauvegarder);

  function restaurer() {
    try {
      const brut = localStorage.getItem(CLE_SAUVEGARDE);
      if (!brut) return;
      const { plan } = JSON.parse(brut);
      if (!Array.isArray(plan)) return;
      for (const ent of plan) {
        const plante = planteParId(ent.espece);
        if (!plante || typeof ent.parcelle !== 'string') continue;
        const [ix, iz] = ent.parcelle.split(',').map(Number);
        if (!Number.isInteger(ix) || !Number.isInteger(iz)) continue;
        if (ix < 0 || ix >= PLOT_COUNT || iz < 0 || iz >= PLOT_COUNT) continue;
        planter(ix, iz, plante, { sauvegarder: false, maturite: ent.maturite || 0.12 });
      }
    } catch { /* plan corrompu : on repart d'un jardin vide */ }
  }
  restaurer();

  function compter() {
    return { total: occupees.size };
  }

  return {
    group,
    planter,
    /** Plante une espèce par identifiant de catalogue (usage : démo/main.js). */
    planterParId(id, ix, iz) {
      const plante = planteParId(id);
      return plante ? planter(ix, iz, plante) : null;
    },
    retirer,
    /** Espèce sélectionnée dans le catalogue (id). */
    get especeSelectionnee() { return especeSelectionnee; },
    set especeSelectionnee(id) { especeSelectionnee = id; },
    compter,
    /** Liste des instances plantées (pour le rendu saisonnier). */
    get instances() { return [...occupees.values()]; },
    /** Vide le jardin (bouton « tout arracher »). */
    toutRetirer() {
      for (const cle of [...occupees.keys()]) {
        const [ix, iz] = cle.split(',').map(Number);
        retirer(ix, iz, { sauvegarder: false });
      }
      signaler();
    },
  };
}
