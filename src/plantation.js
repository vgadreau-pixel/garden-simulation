// Plantation interactive : catalogue d'espèces (panneau gauche), clic sur la
// pelouse pour planter / retirer un végétal — n'importe où, librement,
// comme dans un vrai jardin paysager. Sauvegarde du plan en localStorage.
//
// Règles :
//  - une espèce est sélectionnée dans le catalogue → un clic sur la pelouse
//    la plante (maturité initiale « jeune pousse », rotation aléatoire
//    légère pour casser l'uniformité) ;
//  - un clic (même outil) sur une plante existante la retire ;
//  - clic droit (contextmenu) retire aussi la plante — geste naturel ;
//  - le plan (liste de {espece, x, z}) est persisté et restauré au démarrage.
//  - une distance minimale entre plantes évite les superpositions absurdes
//    (on plante « raisonnablement », pas dans le tronc du voisin).
import * as THREE from 'three';
import { PLANTES, planteParId } from './data/plants.js';
import { GRID_EXTENT, GROUND_MARGIN } from './constants.js';
import { creerInstancePlante } from './plantInstances.js';
import { habillerInstance } from './vegetation.js';
import { OBSTACLES_STATIQUES } from './onirique.js';

const CLE_SAUVEGARDE = 'jardin-saisons.plan.v2';

/** Rayon d'encombrement approximatif d'une plante (m) selon son type. */
function rayonEncombrement(plante) {
  if (!plante) return 0.6;
  if (plante.type === 'arbre') return 1.6;
  if (plante.type === 'arbuste') return 1.1;
  return 0.5; // fleurs / légumes
}

export function creerPlantation(scene, canvas, camera, clock, { onChangement, vueFps, surFeedback } = {}) {
  const group = new THREE.Group();
  group.name = 'plantations';
  scene.add(group);

  // Plantes posées : Set d'instances.
  const plantees = new Set();
  // Sélection courante du catalogue.
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

  /**
   * Point monde visé.
   *  - Vue de dessus : rayon sous le curseur (clientX, clientY) via la caméra ortho.
   *  - Vue immersive (FPS) : pointer lock fige le curseur — on vise par le
   *    CENTRE DE L'ÉCRAN via la caméra FPS (fournie par vueFps.getCamera()).
   *    C'est la caméra du mode courant qui définit le rayon, jamais l'autre :
   *    utiliser l'ortho en FPS décalait la visée (bug « pointeur décalé »).
   */
  function pointSousCurseur(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    let nx, ny, cam;
    if (vueFps && vueFps.actif()) {
      cam = vueFps.getCamera();
      nx = 0; ny = 0; // centre de l'écran = direction du regard
    } else {
      cam = camera;
      nx = ((clientX - rect.left) / rect.width) * 2 - 1;
      ny = -(((clientY - rect.top) / rect.height) * 2 - 1);
    }
    raycaster.setFromCamera(new THREE.Vector2(nx, ny), cam);
    const pt = new THREE.Vector3();
    if (raycaster.ray.intersectPlane(planSol, pt)) return pt;
    // Regard horizontal ou vers le ciel (rasant) : le rayon ne coupe pas le
    // plan du sol — on vise un point « à ses pieds » à ~6 m devant la caméra
    // pour que planter reste possible sans viser le sol explicitement.
    const origine = raycaster.ray.origin;
    const dir = raycaster.ray.direction;
    if (dir.y >= -0.02) {
      const horiz = Math.hypot(dir.x, dir.z);
      if (horiz > 1e-4) {
        pt.set(origine.x + (dir.x / horiz) * 6, 0, origine.z + (dir.z / horiz) * 6);
        return pt;
      }
    }
    return null;
  }

  // ── Surbrillance de la zone de plantation visée ──
  // Un doux disque de lumière qui suit le curseur (naturel, pas une case).
  const surbrillance = new THREE.Mesh(
    new THREE.CircleGeometry(1, 28),
    new THREE.MeshBasicMaterial({ color: 0xfff3c4, transparent: true, opacity: 0.0, depthWrite: false })
  );
  surbrillance.rotation.x = -Math.PI / 2;
  surbrillance.position.y = 0.07;
  surbrillance.visible = false;
  group.add(surbrillance);

  /** Point libre ? (dans la pelouse, hors bassin, loin des voisins) */
  function pointValide(pt, plante, ignore = null) {
    const limite = GRID_EXTENT / 2 + GROUND_MARGIN - 0.8;
    if (Math.abs(pt.x) > limite || Math.abs(pt.z) > limite) return false;
    // Bassin : on ne plante ni dans l'eau ni dans les pierres.
    for (const o of OBSTACLES_STATIQUES) {
      const d = Math.hypot(pt.x - o.x, pt.z - o.z);
      if (d < o.r + rayonEncombrement(plante) * 0.6) return false;
    }
    // Voisins : respecter l'encombrement mutuel (sinon plantes empilées).
    for (const inst of plantees) {
      if (inst === ignore) continue;
      const p = inst.group.position;
      const d = Math.hypot(pt.x - p.x, pt.z - p.z);
      if (d < (rayonEncombrement(plante) + rayonEncombrement(inst.plante)) * 0.55) return false;
    }
    return true;
  }

  /** Plante existante sous le curseur (disque d'encombrement), ou null. */
  function planteSous(pt) {
    let meilleure = null, dMin = Infinity;
    for (const inst of plantees) {
      const p = inst.group.position;
      const r = rayonEncombrement(inst.plante);
      const d = Math.hypot(pt.x - p.x, pt.z - p.z);
      if (d < r && d < dMin) { meilleure = inst; dMin = d; }
    }
    return meilleure;
  }

  function majSurbrillance(e) {
    // En FPS : pas d'événement souris exploitable (pointer lock) — appelé
    // chaque frame par majFPS() avec les coordonnées du centre.
    const pt = e
      ? pointSousCurseur(e.clientX, e.clientY)
      : pointSousCurseur(0, 0);
    if (!pt) { surbrillance.visible = false; return; }
    const plante = planteParId(especeSelectionnee);
    const cible = planteSous(pt);
    const r = cible ? rayonEncombrement(cible.plante) : rayonEncombrement(plante) * 0.9;
    surbrillance.scale.setScalar(r);
    surbrillance.position.set(pt.x, 0.07, pt.z);
    // Rouge doux si occupé/invalide, crème si plantable.
    surbrillance.material.color.set(cible || !pointValide(pt, plante) ? 0xd98880 : 0xfff3c4);
    surbrillance.material.opacity = 0.3;
    surbrillance.visible = true;
  }

  // ── Planter / retirer ──
  // Animation d'apparition : la plante « pousse » du sol en 0,6 s (élastique
  // doux) + anneau d'onde au sol qui s'étend et s'estompe. Feedback clair :
  // impossible de rater le fait que la plantation a réussi.
  const anims = []; // { inst, t0, onde, mats0 }
  const ondeGeo = new THREE.RingGeometry(0.55, 0.75, 32);
  function animerApparition(inst) {
    const onde = new THREE.Mesh(
      ondeGeo,
      new THREE.MeshBasicMaterial({
        color: 0xd8f5a8, transparent: true, opacity: 0.75,
        side: THREE.DoubleSide, depthWrite: false,
      })
    );
    onde.rotation.x = -Math.PI / 2;
    onde.position.set(inst.group.position.x, 0.08, inst.group.position.z);
    group.add(onde);
    anims.push({ inst, t0: performance.now(), onde });
  }

  function majAnims() {
    const now = performance.now();
    for (let i = anims.length - 1; i >= 0; i--) {
      const a = anims[i];
      const t = Math.min(1, (now - a.t0) / 600);
      // Ease out-back doux : léger dépassement puis stabilisation.
      const e = 1 + 2.2 * Math.pow(t - 1, 3) + 1.2 * Math.pow(t - 1, 2);
      // Facteur lu par appliquerEtat (plantInstances.js) qui l'applique à
      // l'échelle après croissance — pas de conflit d'écriture d'échelle.
      a.inst.apparition = Math.max(0.05, 0.15 + 0.85 * e);
      // Onde : s'étend de x1 à x4, fondu.
      const ot = Math.min(1, (now - a.t0) / 900);
      a.onde.scale.setScalar(1 + ot * 3);
      a.onde.material.opacity = 0.75 * (1 - ot);
      if (t >= 1) {
        a.inst.apparition = undefined; // fin de l'anim : croissance normale
        group.remove(a.onde);
        a.onde.material.dispose();
        anims.splice(i, 1);
      }
    }
  }

  function planter(x, z, plante, { sauvegarder = true, maturite = 0.12, silencieux = false } = {}) {
    const pt = new THREE.Vector3(x, 0, z);
    if (!pointValide(pt, plante)) return null;
    const inst = creerInstancePlante(
      plante,
      pt,
      maturite,
      (Math.random() - 0.5) * 0.5
    );
    group.add(inst.group);
    plantees.add(inst);
    habillerInstance(inst); // modèle GLTF texturé (asynchrone, repli primitives)
    if (!silencieux) animerApparition(inst);
    if (sauvegarder) signaler();
    return inst;
  }

  function retirerInstance(inst, { sauvegarder = true } = {}) {
    if (!plantees.has(inst)) return false;
    group.remove(inst.group);
    plantees.delete(inst);
    if (sauvegarder) signaler();
    return true;
  }

  function basculer(pt) {
    const existante = planteSous(pt);
    if (existante) {
      retirerInstance(existante);
      return { ok: true, action: 'retire' };
    }
    const plante = planteParId(especeSelectionnee);
    if (!plante) return { ok: false, action: 'aucune' };
    const inst = planter(pt.x, pt.z, plante);
    return inst
      ? { ok: true, action: 'plante', inst }
      : { ok: false, action: 'trop-pres' };
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
    if (!pt) return;
    const res = basculer(pt);
    if (surFeedback) surFeedback(res);
    if (res.ok) majSurbrillance(e);
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
    const inst = planteSous(pt);
    if (inst) retirerInstance(inst);
  }
  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointerup', onPointerUp);
  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerleave', () => { surbrillance.visible = false; });
  canvas.addEventListener('contextmenu', onContextMenu);

  // ── Vue immersive : visée au centre de l'écran ──
  // majFPS() est appelé chaque frame par main.js : le disque suit le regard
  // et les animations d'apparition progressent.
  function majFPS() {
    majAnims();
    if (!vueFps || !vueFps.actif()) return;
    majSurbrillance(null);
  }

  // ── Sauvegarde / restauration (localStorage) ──
  function sauvegarder() {
    try {
      const plan = [...plantees].map((inst) => ({
        espece: inst.plante.id,
        x: Number(inst.group.position.x.toFixed(2)),
        z: Number(inst.group.position.z.toFixed(2)),
        maturite: Number(inst.maturite.toFixed(3)),
      }));
      localStorage.setItem(CLE_SAUVEGARDE, JSON.stringify({ plan, climat: clock.climat }));
    } catch { /* quota / mode privé : on ignore, le jeu reste jouable */ }
  }
  listenersChangement.push(sauvegarder);

  function restaurer() {
    try {
      // v2 : positions libres ; v1 (ancienne grille) : converti en positions libres.
      const brut = localStorage.getItem(CLE_SAUVEGARDE) || localStorage.getItem('jardin-saisons.plan.v1');
      if (!brut) return;
      const { plan } = JSON.parse(brut);
      if (!Array.isArray(plan)) return;
      // Espacement relâché à la restauration (les vieux plans/grilles étaient serrés) :
      for (const ent of plan) {
        const plante = planteParId(ent.espece);
        if (!plante) continue;
        let x, z;
        if (typeof ent.x === 'number' && typeof ent.z === 'number') {
          x = ent.x; z = ent.z;
        } else if (typeof ent.parcelle === 'string') {
          // Migration v1 : centre de l'ancienne parcelle "ix,iz".
          const [ix, iz] = ent.parcelle.split(',').map(Number);
          if (!Number.isInteger(ix) || !Number.isInteger(iz)) continue;
          const PITCH = 4.6, offset = 3.5;
          x = (ix - offset) * PITCH; z = (iz - offset) * PITCH;
        } else continue;
        planter(x, z, plante, { sauvegarder: false, maturite: ent.maturite || 0.12 });
      }
    } catch { /* plan corrompu : on repart d'un jardin vide */ }
  }
  restaurer();

  function compter() {
    return { total: plantees.size };
  }

  return {
    group,
    planter,
    /** Mise à jour visée FPS + animations (appelé chaque frame). */
    majFPS,
    /** Animations d'apparition (appelé chaque frame en vue de dessus aussi). */
    majAnims,
    /** Plante une espèce par identifiant de catalogue (usage : démo/main.js). */
    planterParId(id, x, z, opts) {
      const plante = planteParId(id);
      return plante ? planter(x, z, plante, opts) : null;
    },
    retirer: (x, z, opts) => {
      const inst = planteSous(new THREE.Vector3(x, 0, z));
      return inst ? retirerInstance(inst, opts) : false;
    },
    /** Espèce sélectionnée dans le catalogue (id). */
    get especeSelectionnee() { return especeSelectionnee; },
    set especeSelectionnee(id) { especeSelectionnee = id; },
    compter,
    /** Liste des instances plantées (pour le rendu saisonnier). */
    get instances() { return [...plantees]; },
    /** Vide le jardin (bouton « tout arracher »). */
    toutRetirer() {
      for (const inst of [...plantees]) retirerInstance(inst, { sauvegarder: false });
      signaler();
    },
  };
}
