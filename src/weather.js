// Particules météo (pluie, neige, brume) pilotées par le système climatique.
// Un seul système par type, activé/désactivé par intensité 0..1 continue :
// le nombre de particules VISIBLES varie, la géométrie est allouée une fois.

import * as THREE from 'three';
import { GRID_EXTENT } from './constants.js';

const ZONE = GRID_EXTENT * 1.1; // emprise au sol de la zone météo
const HAUTEUR = 40; // hauteur de spawn

function creerPluie(scene) {
  const N = 1400;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    pos[i * 3] = (Math.random() - 0.5) * ZONE;
    pos[i * 3 + 1] = Math.random() * HAUTEUR;
    pos[i * 3 + 2] = (Math.random() - 0.5) * ZONE;
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({
    color: 0x9db8d9, size: 0.28, transparent: true, opacity: 0,
    depthWrite: false, sizeAttenuation: true,
  });
  const points = new THREE.Points(geo, mat);
  points.visible = false;
  points.frustumCulled = false;
  scene.add(points);
  return { points, mat, pos, geo, N, vitesse: 26, derivee: 4 };
}

function creerNeige(scene) {
  const N = 900;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    pos[i * 3] = (Math.random() - 0.5) * ZONE;
    pos[i * 3 + 1] = Math.random() * HAUTEUR;
    pos[i * 3 + 2] = (Math.random() - 0.5) * ZONE;
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({
    color: 0xffffff, size: 0.42, transparent: true, opacity: 0,
    depthWrite: false, sizeAttenuation: true,
  });
  const points = new THREE.Points(geo, mat);
  points.visible = false;
  points.frustumCulled = false;
  scene.add(points);
  return { points, mat, pos, geo, N, vitesse: 3.2, derivee: 1.6, phase: new Float32Array(N).map(() => Math.random() * Math.PI * 2) };
}

function creerBrume(scene) {
  // Volutes de brume : gros points doux (sprite radial) dérivant lentement.
  // Une texture canvas radiale évite les carrés discrets de PointsMaterial.
  const N = 36;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(230,238,244,0.55)');
  g.addColorStop(0.6, 'rgba(230,238,244,0.22)');
  g.addColorStop(1, 'rgba(230,238,244,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);

  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  const phases = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    pos[i * 3] = (Math.random() - 0.5) * ZONE * 0.95;
    pos[i * 3 + 1] = 2.5 + Math.random() * 4;
    pos[i * 3 + 2] = (Math.random() - 0.5) * ZONE * 0.95;
    phases[i] = Math.random() * Math.PI * 2;
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({
    map: tex, transparent: true, opacity: 0, depthWrite: false,
    sizeAttenuation: false, size: 90, color: 0xffffff,
  });
  const points = new THREE.Points(geo, mat);
  points.visible = false;
  points.frustumCulled = false;
  scene.add(points);
  return { points, mat, pos, geo, N, phases };
}

/**
 * Système météo. Usage :
 *   const meteo = creerMeteo(scene);
 *   meteo.appliquer({ pluie, neige, brume }, deltaSec); // chaque frame
 */
export function creerMeteo(scene) {
  const pluie = creerPluie(scene);
  const neige = creerNeige(scene);
  const brume = creerBrume(scene);
  const cible = { pluie: 0, neige: 0, brume: 0 };

  function majPluie(dt, intensite) {
    const p = pluie;
    if (intensite <= 0.01) { p.points.visible = false; return; }
    p.points.visible = true;
    p.mat.opacity = Math.min(0.75, intensite * 0.9);
    const n = Math.max(50, Math.floor(p.N * intensite));
    const v = p.vitesse * dt;
    const d = p.derivee * dt;
    for (let i = 0; i < n; i++) {
      let y = p.pos[i * 3 + 1] - v;
      if (y < 0) { y = HAUTEUR; p.pos[i * 3] = (Math.random() - 0.5) * ZONE; p.pos[i * 3 + 2] = (Math.random() - 0.5) * ZONE; }
      p.pos[i * 3 + 1] = y;
      p.pos[i * 3] += d; // vent léger
    }
    p.geo.attributes.position.needsUpdate = true;
  }

  function majNeige(dt, intensite) {
    const s = neige;
    if (intensite <= 0.01) { s.points.visible = false; return; }
    s.points.visible = true;
    s.mat.opacity = Math.min(0.9, intensite);
    const n = Math.max(40, Math.floor(s.N * intensite));
    const t = performance.now() / 1000;
    for (let i = 0; i < n; i++) {
      let y = s.pos[i * 3 + 1] - s.vitesse * dt;
      if (y < 0) { y = HAUTEUR; s.pos[i * 3] = (Math.random() - 0.5) * ZONE; s.pos[i * 3 + 2] = (Math.random() - 0.5) * ZONE; }
      s.pos[i * 3 + 1] = y;
      // Dérive sinusoïdale : flocons qui zigzaguent.
      s.pos[i * 3] += Math.sin(t * 1.2 + s.phase[i]) * 0.8 * dt * 3;
      s.pos[i * 3 + 2] += Math.cos(t * 0.9 + s.phase[i]) * 0.6 * dt * 3;
    }
    s.geo.attributes.position.needsUpdate = true;
  }

  function majBrume(dt, intensite) {
    const b = brume;
    if (intensite <= 0.03) { b.points.visible = false; return; }
    b.points.visible = true;
    b.mat.opacity = Math.min(0.5, intensite * 0.65);
    const t = performance.now() / 1000;
    for (let i = 0; i < b.N; i++) {
      // Dérive lente en boucle fermée (pas de saut).
      b.pos[i * 3] += Math.sin(t * 0.06 + b.phases[i]) * 0.35 * dt;
      b.pos[i * 3 + 2] += Math.cos(t * 0.05 + b.phases[i] * 1.7) * 0.35 * dt;
      // Maintient dans la zone (rebond doux).
      const lim = ZONE / 2;
      if (b.pos[i * 3] > lim) b.pos[i * 3] = -lim;
      if (b.pos[i * 3] < -lim) b.pos[i * 3] = lim;
      if (b.pos[i * 3 + 2] > lim) b.pos[i * 3 + 2] = -lim;
      if (b.pos[i * 3 + 2] < -lim) b.pos[i * 3 + 2] = lim;
    }
    b.geo.attributes.position.needsUpdate = true;
  }

  return {
    cible,
    /** Applique les intensités météo courantes (0..1) et anime les particules. */
    appliquer(m, deltaSec) {
      const dt = Math.min(deltaSec, 0.25);
      majPluie(dt, m.pluie || 0);
      majNeige(dt, m.neige || 0);
      majBrume(dt, m.brume || 0);
    },
    /** Intensités courantes exposées pour tests. */
    etat() {
      return {
        pluieVisible: pluie.points.visible,
        neigeVisible: neige.points.visible,
        brumeVisible: brume.points.visible,
        opacitePluie: pluie.mat.opacity,
        opaciteNeige: neige.mat.opacity,
      };
    },
  };
}
