// Terrain : sol PBR (textures albedo+normal+roughness Poly Haven, CC0),
// allées, grille 8x8 de parcelles de jardin délimitées par des bordures bois,
// terre travaillée au centre.
// Les 256 parcelles sont fusionnées en 2 meshes (bordures + terre) pour
// limiter les draw calls et garantir un framerate élevé.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { PLOT_COUNT, PLOT_SIZE, PITCH, PLOT_PATH, GRID_EXTENT, GROUND_MARGIN, COLORS } from './constants.js';

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

function makeSoilTexture(size = 256) {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#6b4a2f';
  ctx.fillRect(0, 0, size, size);
  // Sillons de terre travaillée
  for (let i = 0; i < size; i += 8) {
    ctx.strokeStyle = `rgba(${60 + rnd(20)}, ${38 + rnd(14)}, ${22 + rnd(10)}, 0.5)`;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, i);
    ctx.lineTo(size, i);
    ctx.stroke();
  }
  // Cailloux / miettes
  for (let i = 0; i < 250; i++) {
    ctx.fillStyle = `rgba(${120 + rnd(40)}, ${95 + rnd(30)}, ${70 + rnd(25)}, ${0.25 + Math.random() * 0.3})`;
    ctx.beginPath();
    ctx.arc(Math.random() * size, Math.random() * size, 0.6 + Math.random() * 1.8, 0, Math.PI * 2);
    ctx.fill();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1.5, 1.5);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function rnd(n) {
  return Math.floor(Math.random() * n);
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

  // --- Chemins (allées) : croix centrale + pourtour de la grille ---
  const pathMat = matPBR('chemin', { repeat: 8, normalScale: 0.4 });
  const pathY = 0.02;

  // Pourtour : légère bande claire autour de la grille
  const apron = new THREE.Mesh(
    new THREE.PlaneGeometry(GRID_EXTENT + PLOT_PATH * 2, GRID_EXTENT + PLOT_PATH * 2),
    new THREE.MeshStandardMaterial({ color: 0xb9c489, roughness: 1 })
  );
  apron.rotation.x = -Math.PI / 2;
  apron.position.y = 0.01;
  apron.receiveShadow = true;
  group.add(apron);

  const addPath = (w, d, x, z) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, 0.04, d), pathMat);
    m.position.set(x, pathY, z);
    m.receiveShadow = true;
    group.add(m);
  };
  // Croix centrale (allées traversantes)
  addPath(PLOT_PATH + 0.4, GRID_EXTENT + PLOT_PATH, 0, 0);
  addPath(GRID_EXTENT + PLOT_PATH, PLOT_PATH + 0.4, 0, 0);

  // --- Grille de parcelles 8x8 ---
  const soilTex = makeSoilTexture();
  const soilMat = matPBR('terre', { repeat: 1.5, normalScale: 0.55 });
  const borderMat = new THREE.MeshStandardMaterial({ color: COLORS.border, roughness: 0.9 });

  const offset = (PLOT_COUNT - 1) / 2;
  const borderGeos = [];
  const soilGeos = [];
  for (let ix = 0; ix < PLOT_COUNT; ix++) {
    for (let iz = 0; iz < PLOT_COUNT; iz++) {
      const px = (ix - offset) * PITCH;
      const pz = (iz - offset) * PITCH;

      // Bordure bois : 4 côtés fins formant un cadre
      const t = 0.18; // épaisseur bordure
      const h = 0.22; // hauteur bordure
      const s = PLOT_SIZE / 2;
      const sides = [
        [PLOT_SIZE + t * 2, t, 0, -s - t / 2],
        [PLOT_SIZE + t * 2, t, 0, s + t / 2],
        [t, PLOT_SIZE, -s - t / 2, 0],
        [t, PLOT_SIZE, s + t / 2, 0],
      ];
      for (const [w, d, lx, lz] of sides) {
        const g = new THREE.BoxGeometry(w, h, d);
        g.translate(px + lx, h / 2, pz + lz);
        borderGeos.push(g);
      }

      // Terre cultivée
      const soil = new THREE.PlaneGeometry(PLOT_SIZE - 0.1, PLOT_SIZE - 0.1);
      soil.rotateX(-Math.PI / 2);
      soil.translate(px, 0.05, pz);
      soilGeos.push(soil);
    }
  }

  const borders = new THREE.Mesh(mergeGeometries(borderGeos), borderMat);
  borders.castShadow = true;
  borders.receiveShadow = true;
  group.add(borders);

  const soilField = new THREE.Mesh(mergeGeometries(soilGeos), soilMat);
  soilField.receiveShadow = true;
  group.add(soilField);

  scene.add(group);
  return group;
}
