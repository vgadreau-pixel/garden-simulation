// Terrain : sol en herbe PBR (textures Poly Haven CC0 + repli procédural),
// pelouse continue SANS grille de parcelles, chemins de dalles naturelles
// (pas japonais) reliant l'entrée sud au bassin et au cœur du jardin.
// Le style cherche un jardin paysager, pas un potager en carrés.
import * as THREE from 'three';
import { GRID_EXTENT, GROUND_MARGIN } from './constants.js';

const DEFAUTS_PBR = { normalScale: 0.6, repeat: 10 };

/** Charge une texture locale avec wrapping/répétition ; null si introuvable. */
function texCharge(chemin, { repeat = 1, srgb = false } = {}) {
  const t = new THREE.TextureLoader().load(chemin, undefined, undefined, () => {});
  t.wrapS = THREE.RepeatWrapping;
  t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

/** Matériau PBR complet (albedo + normal + roughness) à partir de 3 fichiers. */
function matPBR(role, { repeat, normalScale } = DEFAUTS_PBR) {
  const albedo = texCharge(`/textures/${role}_albedo.jpg`, { repeat, srgb: true });
  const normal = texCharge(`/textures/${role}_normal.jpg`, { repeat });
  const rough = texCharge(`/textures/${role}_roughness.jpg`, { repeat });
  return new THREE.MeshStandardMaterial({
    map: albedo,
    normalMap: normal,
    roughnessMap: rough,
    roughness: 1.0,
    normalScale: new THREE.Vector2(normalScale, normalScale),
  });
}

function makeGrassTexture(size = 512) {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  // Fond dégradé doux
  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, '#79a850');
  grad.addColorStop(0.5, '#6f9f49');
  grad.addColorStop(1, '#82b058');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);

  // Brins d'herbe aléatoires
  const blades = size * 14;
  for (let i = 0; i < blades; i++) {
    const x = Math.random() * size;
    const y = Math.random() * size;
    const light = Math.random() > 0.5;
    ctx.strokeStyle = light
      ? `rgba(${140 + rnd(30)}, ${185 + rnd(25)}, ${90 + rnd(20)}, 0.55)`
      : `rgba(${70 + rnd(25)}, ${115 + rnd(25)}, ${50 + rnd(18)}, 0.5)`;
    ctx.lineWidth = 1 + Math.random();
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + (Math.random() * 2 - 1) * 2, y - 2 - Math.random() * 4);
    ctx.stroke();
  }

  // Taches de variété pour casser la répétition
  for (let i = 0; i < 90; i++) {
    const x = Math.random() * size;
    const y = Math.random() * size;
    const r = 4 + Math.random() * 14;
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    const hue = 95 + rnd(20);
    g.addColorStop(0, `hsla(${hue}, 45%, ${42 + rnd(12)}%, 0.25)`);
    g.addColorStop(1, 'hsla(100, 45%, 45%, 0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(10, 10);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

function rnd(n) {
  return Math.floor(Math.random() * n);
}

/** RNG déterministe (mêmes dalles entre les builds). */
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Pas japonais : dalles rondes posées sur la pelouse le long d'une courbe
 * souple (Catmull-Rom). L'herbe passe entre les dalles — naturel, aucun
 * conflit avec le champ d'herbe instancié.
 */
function poserPasJaponais(group, matDalles, points, { nDalles = 14, rMin = 0.42, rMax = 0.62 } = {}) {
  const courbe = new THREE.CatmullRomCurve3(points.map(([x, z]) => new THREE.Vector3(x, 0, z)));
  const rng = mulberry32(20260909);
  const geoProto = new THREE.CircleGeometry(1, 14);
  for (let i = 0; i < nDalles; i++) {
    const t = i / (nDalles - 1);
    const p = courbe.getPoint(t);
    // Jitter latéral léger : la ligne n'est pas une autoroute.
    const n = courbe.getTangent(t);
    const lat = new THREE.Vector3(-n.z, 0, n.x).multiplyScalar((rng() - 0.5) * 0.5);
    const dalle = new THREE.Mesh(geoProto, matDalles);
    dalle.rotation.x = -Math.PI / 2;
    dalle.rotation.z = rng() * Math.PI * 2;
    dalle.scale.setScalar(rMin + rng() * (rMax - rMin));
    dalle.position.set(p.x + lat.x, 0.03 + rng() * 0.01, p.z + lat.z);
    dalle.receiveShadow = true;
    group.add(dalle);
  }
}

export function buildTerrain(scene) {
  const group = new THREE.Group();
  group.name = 'terrain';

  // --- Sol en herbe : PBR Poly Haven (repli texture procédurale si 404) ---
  const groundSize = GRID_EXTENT + GROUND_MARGIN * 2;
  const grassTex = makeGrassTexture();
  const matHerbe = matPBR('pelouse', { repeat: 12, normalScale: 0.5 });
  matHerbe.map.image = grassTex.image; // placeholder en attendant le chargement
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(groundSize, groundSize),
    matHerbe
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  group.add(ground);

  // --- Pas japonais : entrée sud → cœur du jardin, et vers le bassin ---
  // (le bassin est posé à (-20.3, 20.3) par la couche onirique).
  const matDalles = matPBR('chemin', { repeat: 1.2, normalScale: 0.4 });
  poserPasJaponais(group, matDalles, [
    [0, GRID_EXTENT / 2 + GROUND_MARGIN - 1.5], // entrée sud
    [3, 12], [-2, 6], [2, 0], [-3, -6], [0, -12], [4, -16], // vers le nord
  ]);
  poserPasJaponais(group, matDalles, [
    [-2, 4], [-8, 8], [-14, 13], [-18.5, 17.5], // embranchement vers le bassin
  ], { nDalles: 10 });

  scene.add(group);
  return group;
}
