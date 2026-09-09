// Éclairage physique + ciel dynamique + post-processing léger (tâche 3/3).
// Une seule couche : on configure renderer/scene/lumières/composer en fonction
// de l'état existant (moteur temporel + météo). Aucune modification des
// contrôles caméra ni des modèles végétaux.
import * as THREE from 'three';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { GRID_EXTENT } from './constants.js';

// --- Tone mapping photoréaliste ---
// ACESFilmic + exposition modulée par le climat : l'aride écrase un peu,
// le couvert assombrit, la nuit laisse une exposition douce aux étoiles.
const EXPO_BASE = 0.72;
const EXPO_ARIDE = 1.0;
const EXPO_NUIT = 0.9;

// --- Post-processing : chaîne minimale (Render → Bloom léger → Output) ---
// Pas de SSAO sur un sol quasi plat vu de dessus : coût GPU pour un gain
// invisible. L'occlusion ambiante vient de la luminosité hémisphérique douce.
export function creerComposer(renderer, scene, camera) {
  const composer = new EffectComposer(renderer);
  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);
  const bloom = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.18,  // strength — très léger, halos oniriques seulement
    0.55,  // radius
    0.88,  // threshold — seuls les pixels très lumineux fleurissent
  );
  composer.addPass(bloom);
  composer.addPass(new OutputPass()); // tone mapping + sRGB en fin de chaîne
  // SwiftShader / GPU logiciel : UnrealBloomPass ET OutputPass rendent le
  // canvas entièrement noir (bug driver, err GL 0, rAF vif). On contourne en
  // désactivant TOUTES les passes post-render : le renderPass finalise direct
  // sur le canvas avec ACESFilmic + sRGB déjà configurés sur le renderer.
  const gl = renderer.getContext();
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  const rendu = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '';
  if (/swiftshader|llvmpipe|softpipe|software/i.test(String(rendu))) {
    for (const p of composer.passes) if (p !== renderPass) p.enabled = false;
    console.warn('[sky] GPU logiciel détecté (' + rendu + ') : post-processing désactivé (canvas noir sinon).');
  }
  return { composer, bloom, renderPass };
}

// --- Ciel : grand dôme à sommet de gradient (inversé), toujours visible ---
// Les couleurs du dégradé sont réécrites chaque frame par le cycle jour/nuit
// et la saison — shader minimal, aucun coût de passes supplémentaires.
const VERT_CIEL = /* glsl */ `
  varying vec3 vWorldPos;
  void main() {
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vWorldPos = wp.xyz;
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;
const FRAG_CIEL = /* glsl */ `
  varying vec3 vWorldPos;
  uniform vec3 cHaut;      // zénith
  uniform vec3 cMilieu;    // milieu du dôme
  uniform vec3 cHorizon;   // rasante (teinté soleil)
  uniform vec3 cSoleilGlow; // couleur du halo autour du soleil
  uniform vec3 dirSoleil;   // direction du soleil (normalisée)
  uniform float uGlow;      // intensité du halo (crépuscule → 1)
  void main() {
    vec3 dir = normalize(vWorldPos);
    // Le dégradé directionnel (haut = dir.y) n'est visible qu'en vue
    // perspective (mode FPS). En ortho plongeante tous les fragments ont
    // dir.y ≈ -1 : on mixe alors selon la coordonnée écran gl_FragCoord
    // via un dégradé supplémentaire doux nord/sud (z monde).
    float h = clamp(dir.y, 0.0, 1.0);
    float zBand = clamp(vWorldPos.z / 380.0, -1.0, 1.0); // -1 sud → +1 nord
    vec3 col = mix(cHorizon, cMilieu, smoothstep(0.0, 0.28, h));
    col = mix(col, cHaut, smoothstep(0.22, 0.85, h));
    // Vue ortho : léger dégradé nord (cMilieu) → sud (cHorizon chaud)
    col = mix(col, cMilieu, smoothstep(0.0, 1.0, -zBand) * (1.0 - h) * 0.55);
    // Halo chaud autour du soleil à l'horizon (aube/crépuscule onirique)
    float soleil = max(dot(dir, normalize(dirSoleil)), 0.0);
    col += cSoleilGlow * pow(soleil, 8.0) * uGlow;
    gl_FragColor = vec4(col, 1.0);
  }
`;

export function creerCiel(scene) {
  const uniforms = {
    cHaut: { value: new THREE.Color(0x2e5a8f) },
    cMilieu: { value: new THREE.Color(0x88b3d8) },
    cHorizon: { value: new THREE.Color(0xd6e3ec) },
    cSoleilGlow: { value: new THREE.Color(0xffc98a) },
    dirSoleil: { value: new THREE.Vector3(0.3, 0.6, 0.2) },
    uGlow: { value: 0.35 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: VERT_CIEL,
    fragmentShader: FRAG_CIEL,
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(380, 32, 18), mat);
  dome.frustumCulled = false;
  dome.renderOrder = -10; // dessiné d'abord, sous tout le reste
  scene.add(dome);
  return { dome, uniforms };
}

// --- Brume scénique (printemps/automne matin) : THREE.FogExp2 piloté ---
// La caméra est ortho à y=100, far=500 : la densité reste très faible, elle
// ne fait qu'unifier lointain et ciel d'un voile laiteux, sans manger la scène.
const FOG_COLOR_NUIT = new THREE.Color(0x1b2438);
const FOG_COLOR_JOUR = new THREE.Color(0xdfe8ee);
const FOG_COLOR_HIVER = new THREE.Color(0xe4ebf2);
const FOG_COLOR_AUTOMNE = new THREE.Color(0xe8dfc8);

export function creerBrume(scene) {
  scene.fog = new THREE.FogExp2(0xdfe8ee, 0.0);
  return scene.fog;
}

// --- Étoiles la nuit : Points discrets sur la moitié haute du dôme ---
export function creerEtoiles(scene) {
  const N = 320;
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    // répartition uniforme sur l'hémisphère supérieur du dôme
    const u = Math.random();
    const theta = u * Math.PI * 2;
    const phi = Math.acos(Math.random() * 0.94 + 0.03); // évite l'horizon ras
    const r = 350;
    pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    pos[i * 3 + 1] = r * Math.cos(phi) + 2;
    pos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({
    color: 0xdfe8ff, size: 1.35, sizeAttenuation: false,
    transparent: true, opacity: 0, depthWrite: false,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.renderOrder = -9; // au-dessus du dôme, sous la scène
  scene.add(points);
  return { points, mat };
}

// --- Environnement HDRI (Poly Haven CC0) pour les reflets/ambiance PBR ---
const HDRI_URL = '/hdri/kloppenheim_02_1k.hdr';
export function chargerEnvironnement(scene, renderer) {
  return new Promise((resolve) => {
    new RGBELoader().load(
      HDRI_URL,
      (tex) => {
        tex.mapping = THREE.EquirectangularReflectionMapping;
        scene.environment = tex; // éclairage d'ambiance PBR (IBL)
        resolve(true);
      },
      undefined,
      () => resolve(false), // HDRI absent → le ciel dégradé reste suffisant
    );
  });
}

// --- Presets de palettes par saison (jour dégagé) ---
// Onirique et reposant : saturations douces, jamais cliniques.
const PALETTES = {
  printemps: {
    jour: { haut: 0x4f83c4, milieu: 0x9cc4e4, horizon: 0xc2e0f0, glow: 0xffd9a8 },
    nuit: { haut: 0x121d33, milieu: 0x1e2c48, horizon: 0x33415e, glow: 0x8fa8d8 },
  },
  ete: {
    jour: { haut: 0x3f74c2, milieu: 0x8db8e0, horizon: 0xa8cdea, glow: 0xffe3b0 },
    nuit: { haut: 0x0e1a30, milieu: 0x1a2a46, horizon: 0x2e3e5c, glow: 0x92aede },
  },
  automne: {
    jour: { haut: 0x6d88b0, milieu: 0xc2b494, horizon: 0xe8d9b0, glow: 0xffc078 },
    nuit: { haut: 0x141a2c, milieu: 0x27293e, horizon: 0x4a4054, glow: 0xd8a878 },
  },
  hiver: {
    jour: { haut: 0x8fa6bd, milieu: 0xc4d4e0, horizon: 0xe4ecf2, glow: 0xffe8d0 },
    nuit: { haut: 0x101626, milieu: 0x1c2438, horizon: 0x36415a, glow: 0xa8bce0 },
  },
};

const _cHaut = new THREE.Color();
const _cMilieu = new THREE.Color();
const _cHorizon = new THREE.Color();
const _cGlow = new THREE.Color();
const _fogJour = new THREE.Color();
const _dir = new THREE.Vector3();

/**
 * Applique l'état lumière/ciel complet pour cette frame.
 * @param {object} opts
 *   et        : sortie de etatSoleil(jours, heure)
 *   meteo     : {eclat, brume, neige, pluie}
 *   saison    : 'printemps'|'ete'|'automne'|'hiver'
 *   heure     : 0..24
 *   hemi      : HemisphereLight pilotée
 *   sun       : DirectionalLight pilotée
 *   renderer  : pour l'exposition
 */
export function appliquerCielLumiere(opts) {
  const { et, meteo, saison, heure, hemi, sun, renderer, nuitAvancee } = opts;
  const pal = PALETTES[saison] || PALETTES.printemps;
  const p = et.nuit ? pal.nuit : pal.jour;

  // Interpolation douce jour↔nuit autour du crépuscule (hauteurNorm 0..0.25)
  const mixNuit = et.nuit
    ? 1
    : 1 - Math.min(1, (et.hauteurNorm ?? 0) / 0.22); // aube/crépuscule →Palette nuit
  _cHaut.setHex(pal.jour.haut).lerp(_cHaut2.setHex(pal.nuit.haut), mixNuit);
  _cMilieu.setHex(pal.jour.milieu).lerp(_cMilieu2.setHex(pal.nuit.milieu), mixNuit);
  _cHorizon.setHex(pal.jour.horizon).lerp(_cHorizon2.setHex(pal.nuit.horizon), mixNuit);
  _cGlow.setHex(pal.jour.glow).lerp(_cGlow2.setHex(pal.nuit.glow), mixNuit);

  // Couvert nuageux/brume : désature partiellement vers un gris chaud
  // (garde de la couleur : onirique, pas clinique).
  const couvert = 1 - (meteo.eclat || 0) * 0.75;
  if (couvert > 0.01) {
    const gris = new THREE.Color(0.62, 0.66, 0.70).multiplyScalar(et.nuit ? 0.22 : 1.0);
    _cHaut.lerp(gris, couvert * 0.35);
    _cMilieu.lerp(gris, couvert * 0.45);
    _cHorizon.lerp(gris, couvert * 0.55);
  }

  // Hiver : désaturation froide supplémentaire (lumières basses, neige)
  if (saison === 'hiver') {
    const hsl = {};
    _cMilieu.getHSL(hsl);
    _cMilieu.setHSL(hsl.h, hsl.s * 0.7, Math.min(0.92, hsl.l * 1.12 + 0.04));
  }

  // Écriture des uniforms du dôme
  const u = opts.ciel.uniforms;
  u.cHaut.value.copy(_cHaut);
  u.cMilieu.value.copy(_cMilieu);
  u.cHorizon.value.copy(_cHorizon);
  u.cSoleilGlow.value.copy(_cGlow);
  _dir.copy(et.direction).normalize();
  if (et.nuit) {
    // la nuit, le halo suit une lune fictive à l'opposé du soleil couchant
    _dir.set(-et.direction.x, Math.max(0.25, -et.direction.y), -et.direction.z).normalize();
    u.uGlow.value = 0.25;
  } else {
    u.uGlow.value = 0.35 + (1 - Math.min(1, et.hauteurNorm / 0.35)) * 0.85; // fort à l'aube/crépuscule
  }
  u.dirSoleil.value.copy(_dir);

  // --- Lumières ---
  // Hémisphérique : du zénith du ciel vers le sol, teintée selon la saison.
  hemi.color.copy(_cMilieu).lerp(_cHaut, 0.4);
  hemi.groundColor.setHex(saison === 'hiver' ? 0x8a94a2 : saison === 'automne' ? 0x8a7a52 : 0x6b8f5e);
  const baseHemi = et.nuit ? 0.30 : 0.62 + (et.hauteurNorm ?? 0) * 0.55;
  hemi.intensity = baseHemi * Math.max(0.60, 1 - (meteo.brume || 0) * 0.2) * (0.75 + (meteo.eclat || 0) * 0.25);

  // Soleil : couleur/intensité d'étatSoleil, atténué par le couvert/brume.
  sun.color.copy(et.couleur);
  if (!et.nuit) {
    const att = (0.55 + (meteo.eclat || 0) * 0.45) * (1 - (meteo.brume || 0) * 0.35);
    sun.intensity = et.intensite * att;
  } else {
    sun.intensity = et.intensite; // quasi nul la nuit
  }

  // --- Exposition (tone mapping ACESFilmic déjà configuré) ---
  const cibleExpo = et.nuit
    ? EXPO_NUIT
    : EXPO_BASE + (meteo.eclat || 0) * (EXPO_ARIDE - EXPO_BASE);
  renderer.toneMappingExposure += (cibleExpo - renderer.toneMappingExposure) * 0.08; // lissage

  // --- Brume : densité pilotée (brume météo + matin printemps/automne) ---
  // NB : FogExp2 s'applique sur la distance CAMÉRA. En vue ortho de dessus la
  // caméra est à 100 m : les densités restent de l'ordre du millième pour ne
  // faire qu'un voile laiteux (et non engloutir la scène).
  const matin = Math.max(0, 1 - Math.abs(heure - 7.5) / 3.2); // cloche autour de 7h30
  const matineeSaison = (saison === 'printemps' || saison === 'automne') ? 1 : (saison === 'hiver' ? 0.5 : 0.12);
  const brumeMeteo = (meteo.brume || 0) * 0.010;
  const densite = Math.min(0.012, brumeMeteo + matin * matineeSaison * 0.004);
  const fog = opts.fog;
  fog.density += (densite - fog.density) * 0.06;
  _fogJour.copy(FOG_COLOR_JOUR);
  if (saison === 'hiver') _fogJour.lerp(FOG_COLOR_HIVER, 0.7);
  else if (saison === 'automne') _fogJour.lerp(FOG_COLOR_AUTOMNE, 0.5);
  _fogJour.lerp(FOG_COLOR_NUIT, mixNuit * 0.85);
  fog.color.copy(_fogJour).lerp(new THREE.Color().copy(_cHorizon), 0.35);

  // --- Étoiles : opacité fondu avec la hauteur du soleil ---
  opts.etoiles.mat.opacity = Math.max(0, Math.min(1, (0.12 - (et.hauteurNorm ?? 0)) * 8));

  // scene.background n'est plus utilisé (le dôme le remplace), mais on tient
  // à jour une couleur de secours cohérente pour l'init avant 1re frame.
  if (opts.scene.background && opts.scene.background.isColor) {
    opts.scene.background.copy(_cMilieu);
  }

  return { mixNuit };
}

// Couleurs temporaires pour l'interpolation jour/nuit (module-level)
const _cHaut2 = new THREE.Color();
const _cMilieu2 = new THREE.Color();
const _cHorizon2 = new THREE.Color();
const _cGlow2 = new THREE.Color();
