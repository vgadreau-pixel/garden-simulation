// Jardin des Saisons — point d'entrée.
// Vue orthographique de dessus (plan 2D), pan + zoom, terrain, parcelles,
// moteur temporel (horloge, vitesses, scrubbing), rendu saisonnier,
// climat + météo, plantation interactive (catalogue + clic), musique zen.
import * as THREE from 'three';
import { OrthoTopControls } from './controls.js';
import { FpsControls } from './fpsControls.js';
import { buildTerrain } from './terrain.js';
import { GRID_EXTENT } from './constants.js';
import { SimulationClock } from './simulationClock.js';
import { etatSoleil } from './sun.js';
import { appliquerEtat } from './plantInstances.js';
import { creerControlesTemps } from './timeControls.js';
import { CLIMAT_DEFAUT, climatValide, meteoDuJour, CLIMATS } from './climate.js';
import { creerMeteo } from './weather.js';
import { creerSelecteurClimat } from './climateUI.js';
import { STYLES_CLIMAT } from './climateStyles.js';
import { creerPlantation } from './plantation.js';
import { creerCatalogue } from './catalogueUI.js';
import { STYLES_INTEGRATION } from './uiStyles.js';
import { creerEcranChargement } from './loader.js';
import { createZenAudio } from './zenAudioWrapper.js';
import { majVent } from './vegetation.js';
import { creerOnirique, OBSTACLES_STATIQUES } from './onirique.js';
import {
  chargerEnvironnement, creerComposer, creerCiel, creerBrume, creerEtoiles,
  appliquerCielLumiere,
} from './sky.js';

const loader = creerEcranChargement(); // écran d'accueil zen, fondu à la 1re frame

const canvas = document.getElementById('app');

// --- Renderer ---
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap; // ombres douces
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; // réponse filmique douce
renderer.toneMappingExposure = 0.85;

// --- Scène ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87b56a);

// --- Ciel dynamique + brume + étoiles (couche lumière 3/3) ---
const ciel = creerCiel(scene);
const fog = creerBrume(scene);
const etoiles = creerEtoiles(scene);

// --- Caméra orthographique de dessus ---
const VIEW_HEIGHT = 60; // mètres visibles verticalement à zoom 1
function applyBaseFrustum(camera) {
  const aspect = window.innerWidth / window.innerHeight;
  camera.left = -VIEW_HEIGHT * aspect / 2;
  camera.right = VIEW_HEIGHT * aspect / 2;
  camera.top = VIEW_HEIGHT / 2;
  camera.bottom = -VIEW_HEIGHT / 2;
  camera.near = 0.1;
  camera.far = 500;
}
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 500);
applyBaseFrustum(camera);

// --- Contrôles 2D (pan + zoom, pas de rotation) ---
const controls = new OrthoTopControls(camera, canvas);
controls.update();

// --- Caméra perspective (mode première personne, touche V) ---
// Caméra DÉDIÉE : la caméra orthographique du mode orbital (et les contrôles
// qui en dépendent : pan, zoom, surbrillance, clics de plantation) n'est pas
// touchée. Le mode FPS prend le rendu mais laisse la logique du socle intacte.
const fpsCamera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 800);
const fps = new FpsControls(fpsCamera, canvas, () => jardin.instances);
let modeCamera = 'orbital'; // 'orbital' | 'fps'

// Adapter de vue FPS pour la plantation : la visée passe par la caméra FPS
// (centre de l'écran) au lieu de la caméra ortho de dessus — sinon le point
// de plantation est décalé par rapport à l'endroit regardé.
const vueFps = {
  actif: () => modeCamera === 'fps',
  getCamera: () => fpsCamera,
};

function appliquerAspect() {
  const aspect = window.innerWidth / window.innerHeight;
  applyBaseFrustum(camera);
  camera.updateProjectionMatrix();
  fpsCamera.aspect = aspect;
  fpsCamera.updateProjectionMatrix();
}

const hintMode = document.createElement('div');
hintMode.id = 'hint-mode';
document.body.appendChild(hintMode);

// Viseur central (mode FPS uniquement) : montre où la plantation atterrit.
const viseur = document.createElement('div');
viseur.id = 'viseur';
document.body.appendChild(viseur);
let hintModeTimer = null;
function montrerMode() {
  hintMode.textContent = modeCamera === 'fps'
    ? 'Vue immersive — ZQSD : marche · souris : regard · Maj : course · V : vue du dessus'
    : 'Vue du dessus — V : vue immersive (marche au sol)';
  hintMode.classList.add('visible');
  clearTimeout(hintModeTimer);
  hintModeTimer = setTimeout(() => hintMode.classList.remove('visible'), 3000);
}

function basculerMode() {
  modeCamera = modeCamera === 'fps' ? 'orbital' : 'fps';
  // Herbe instanciée : trop scintillante vue de dessus → réservée à la
  // vue immersive où les brins donnent la profondeur.
  onirique.herbeVisible = modeCamera === 'fps';
  if (modeCamera === 'fps') {
    fps.activer(); // demande le pointer lock
    controls.enabled = false;
    viseur.classList.add('visible');
  } else {
    fps.desactiver();
    controls.enabled = true;
    controls.needsUpdate = true;
    viseur.classList.remove('visible');
  }
  montrerMode();
}
// V bascule ; clic sur le canvas en mode orbital → entrée immersive
// (le pointer lock exige un geste utilisateur). En mode FPS, Échap rend
// la souris (le clic la reprend).
window.addEventListener('keydown', (e) => {
  if (e.code === 'KeyV' && !e.ctrlKey && !e.altKey && !e.metaKey) basculerMode();
});
canvas.addEventListener('click', () => {
  if (modeCamera === 'fps' && document.pointerLockElement !== canvas) {
    canvas.requestPointerLock?.();
  }
});
fps.onLockChange = (locked) => {
  // Échap en mode FPS : on garde le mode mais on affiche la consigne de reprise.
  if (modeCamera === 'fps' && !locked) montrerMode();
};

// --- Post-processing léger + HDRI (couche lumière 3/3) ---
// Composer partagé par les deux caméras : RenderPass suit le mode courant.
const post = creerComposer(renderer, scene, camera);
chargerEnvironnement(scene, renderer); // IBL Poly Haven ; échec silencieux OK

// --- Éclairage ---
// Lumière hémisphérique : ciel/sol, teinte et intensité pilotées par la saison.
const hemi = new THREE.HemisphereLight(0xbfd9ff, 0x6b8f4e, 0.9);
scene.add(hemi);

// Soleil directionnel avec ombres douces — position/couleur pilotées par l'horloge.
const sun = new THREE.DirectionalLight(0xfff2d8, 1.6);
sun.position.set(30, 50, 20);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 300;
const shadowHalf = GRID_EXTENT / 2 + 8;
sun.shadow.camera.left = -shadowHalf;
sun.shadow.camera.right = shadowHalf;
sun.shadow.camera.top = shadowHalf;
sun.shadow.camera.bottom = -shadowHalf;
sun.shadow.bias = -0.0005;
sun.shadow.radius = 4; // adoucit les bords (PCFSoft)
scene.add(sun);
scene.add(sun.target);

// --- Terrain + parcelles ---
buildTerrain(scene);

// --- Couche onirique (herbe instanciée, bassin, particules, rais de lumière) ---
// ?herbe=N réduit le nombre de brins (validations headless / petites configs).
const paramsOnirique = new URLSearchParams(location.search);
const NB_BRINS = Math.max(0, parseInt(paramsOnirique.get('herbe') || '26000', 10) || 0);
const onirique = creerOnirique(scene, { brins: NB_BRINS });
onirique.herbeVisible = false; // vue de dessus par défaut : brins masqués

// --- Moteur temporel ---
// Le climat peut être pré-sélectionné via ?climat=<id> dans l'URL ;
// il peut aussi venir du plan sauvegardé (localStorage), vu plus bas.
const params = new URLSearchParams(location.search);
const climatInitial = params.get('climat');
const CLIMAT_START = climatValide(climatInitial) ? climatInitial : CLIMAT_DEFAUT;
const clock = new SimulationClock(undefined, CLIMAT_START); // départ ~1er avril, 10h

// --- Météo (particules pluie/neige/brume pilotées par le climat) ---
const meteo = creerMeteo(scene);

// --- Feedback plantation : son doux (WebAudio) + libellé du résultat ---
let ctxAudio = null;
function bipPlantation(freq, duree = 0.18) {
  try {
    ctxAudio = ctxAudio || new (window.AudioContext || window.webkitAudioContext)();
    const o = ctxAudio.createOscillator();
    const g = ctxAudio.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(freq, ctxAudio.currentTime);
    o.frequency.exponentialRampToValueAtTime(freq * 1.5, ctxAudio.currentTime + duree);
    g.gain.setValueAtTime(0.12, ctxAudio.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, ctxAudio.currentTime + duree);
    o.connect(g).connect(ctxAudio.destination);
    o.start();
    o.stop(ctxAudio.currentTime + duree);
  } catch { /* audio indisponible : le visuel suffit */ }
}
function surFeedback(res) {
  if (res.action === 'plante') {
    bipPlantation(320, 0.22);
    montrerToast('🌱 Planté !');
  } else if (res.action === 'retire') {
    bipPlantation(200, 0.15);
    montrerToast('Arraché');
  } else if (res.action === 'trop-pres') {
    montrerToast('Trop près d\'une autre plante — décale un peu');
  }
}

// Petit toast discret au-dessus de la timebar (réutilise #hint-plantation).
function montrerToast(texte) {
  const el = document.getElementById('hint-plantation');
  if (!el) return;
  el.textContent = texte;
  el.classList.add('visible');
  clearTimeout(montrerToast._t);
  montrerToast._t = setTimeout(() => el.classList.remove('visible'), 1800);
}

// --- Plantation interactive (catalogue + clic sur parcelles) ---
// Les plantes du plan sauvegardé sont restaurées ici ; l'horloge les fait
// ensuite grandir (maturité modulée par le climat).
const jardin = creerPlantation(scene, canvas, camera, clock, { vueFps, surFeedback });
Object.defineProperty(clock, 'instances', {
  get: () => jardin.instances,
  set: () => {}, // compat ascendante : l'affectation directe est ignorée
});

// Jardin de démonstration si aucun plan sauvegardé : quelques plants pour
// que la première visite ne soit pas vide (plantés en maturité adulte,
// répartis en quinconce naturel — pas de grille).
if (jardin.compter().total === 0) {
  const DEMO = [
    ['cerisier', -6, -7], ['erable_japonais', 5, -9], ['sapin', 10, 4],
    ['pommier', -11, 2], ['lavande', 3, 3], ['rosier', -4, 8],
    ['tulipe', 7, 9], ['coquelicot', -8, 11], ['marguerite', 12, -4],
    ['tomate', 1, 12], ['carotte', -14, -6], ['bouleau', 0, -14],
  ];
  for (const [id, x, z] of DEMO) {
    jardin.planterParId?.(id, x, z, { maturite: 0.9 });
  }
}

// --- Sélecteur de climat (panneau en haut à droite) ---
const styleEl = document.createElement('style');
styleEl.textContent = STYLES_CLIMAT + STYLES_INTEGRATION;
document.head.appendChild(styleEl);
const climatUI = creerSelecteurClimat(document.body, clock, (id) => {
  clock.setClimat(id);
  catalogue.rafraichirAlertes(); // badges « climat inadapté » mis à jour
}, CLIMAT_START);

// --- Catalogue d'espèces (panneau gauche) ---
const catalogue = creerCatalogue(document.body, jardin, climatUI);

// --- Contrôles du temps (boutons vitesse + scrubber) ---
const timeUI = creerControlesTemps(document.body, clock, () => {
  // Pendant un scrub, on gèle l'écoulement pour viser précisément une date.
  if (!clock.paused) clock.setSpeed('pause');
});

// --- Musique méditative (nappe procédurale, démarrage au clic) ---
const audioHost = document.createElement('div');
audioHost.id = 'audio-host';
document.body.appendChild(audioHost);
const audio = createZenAudio(audioHost, { volume: 0.45 });

// Correspondances saison (moteur FR → presets audio EN) et météo.
const SAISON_AUDIO = { printemps: 'spring', ete: 'summer', automne: 'autumn', hiver: 'winter' };
let saisonAudioCourante = null;
let meteoAudioCourante = null;
function majAudio(m) {
  if (!audio.isPlaying()) return; // nappe silencieuse tant que pas lancée
  const saison = SAISON_AUDIO[clock.etat.saison] || 'spring';
  if (saison !== saisonAudioCourante) {
    saisonAudioCourante = saison;
    audio.setSeason(saison);
  }
  // Météo : priorité neige > brume > pluie > chaleur > ciel clair.
  let w = 'clear';
  if (m.neige > 0.15) w = 'snow';
  else if (m.brume > 0.25) w = 'fog';
  else if (m.pluie > 0.2) w = 'rain';
  else if (m.temperature > 28) w = 'heat';
  if (w !== meteoAudioCourante) {
    meteoAudioCourante = w;
    audio.setWeather(w);
  }
}

// Couleurs du ciel désormais gérées par sky.js (palettes saison + cycle jour/nuit).

// --- HUD FPS ---
const fpsEl = document.getElementById('fps');
let frames = 0;
let fpsTimer = performance.now();

// --- Resize ---
window.addEventListener('resize', () => {
  appliquerAspect();
  renderer.setSize(window.innerWidth, window.innerHeight);
  post.composer.setSize(window.innerWidth, window.innerHeight);
  controls.needsUpdate = true;
});

// --- Lumière/ciel : pilotage complet délégué à la couche sky.js (3/3) ---
// À partir de 1 jour/s, le cycle jour/nuit défile plus vite qu'une seconde :
// c'est du clignotement (et du stroboscope à 1 semaine/s). En timelapse on
// fige donc l'éclairage sur une heure dorée fixe (10 h 30) — la scène reste
// lisible et reposante, tandis que saisons et croissance continuent. La
// vraie heure de simulation reste visible dans la barre du temps.
const SEUIL_TIMELAPSE_J_S = 0.5; // ≥ 0,5 jour/s → éclairage figé
const HEURE_SOLEIL_TIMELAPSE = 10.5;
function heureEclairage() {
  return clock.daysPerSecond >= SEUIL_TIMELAPSE_J_S
    ? HEURE_SOLEIL_TIMELAPSE
    : clock.heure;
}
function appliquerLumiere(m) {
  const heureLum = heureEclairage();
  const et = etatSoleil(clock.jours, heureLum);
  sun.position.copy(et.direction);
  sun.target.position.set(0, 0, 0);
  appliquerCielLumiere({
    et,
    meteo: m,
    saison: clock.etat.saison,
    heure: heureLum,
    hemi,
    sun,
    renderer,
    ciel,
    fog,
    etoiles,
    scene,
    nuitAvancee: heureLum < 5 || heureLum > 22,
  });
}

// --- Boucle de rendu ---
// setAnimationLoop passe un timestamp ABSOLU (horloge système), pas un delta :
// on calcule le delta réel nous-mêmes, borné pour éviter les sauts quand
// l'onglet a été throttled/suspendu (le time-lapse doit rester fluide).
let dernierT = performance.now();
let premiereFrame = true;
renderer.setAnimationLoop(() => {
  const t = performance.now();
  // Pas de cap ici : SimulationClock.tick découpe lui-même les deltas longs
  // en sous-pas de 250 ms (max 4). On borne quand même à 2 s pour ignorer
  // les gels extrêmes (onglet suspendu des minutes entières).
  const deltaMs = Math.min(t - dernierT, 2000);
  dernierT = t;
  clock.tick(deltaMs);
  majVent(t / 1000); // horloge du vent (feuillage GLTF)

  // Météo du climat courant (continu, recalculée chaque frame).
  const m = meteoDuJour(clock.climat, clock.jours);
  meteo.appliquer(m, deltaMs / 1000);

  // Rendu saisonnier : états continus recalculés chaque frame, sous climat.
  // Le décor (roche, eau) n'a pas d'état saisonnier : on le saute.
  for (const inst of jardin.instances) if (!inst.decor) appliquerEtat(inst, clock.jours, clock.climat);
  appliquerLumiere(m);
  majAudio(m);

  // Couche onirique : herbe/eau/particules/rais pilotés par l'état courant.
  onirique.update({
    delta: Math.min(deltaMs / 1000, 0.1),
    soleilDir: etatSoleil(clock.jours, heureEclairage()).direction,
    couleurLumiere: sun.color,
    nuit: heureEclairage() < 6.5 || heureEclairage() > 20.5,
    hauteurNorm: etatSoleil(clock.jours, heureEclairage()).hauteurNorm ?? 0.5,
    eclat: m.eclat,
    saison: clock.etat.saison,
    camera: modeCamera === 'fps' ? fpsCamera : camera,
    fog,
  });

  timeUI.maj();
  climatUI.maj();

  // Marche à la première personne (mode fps uniquement, collisions incluses).
  fps.update(deltaMs / 1000);
  // Visée de plantation en vue immersive + animations d'apparition.
  jardin.majFPS?.();
  jardin.majAnims?.();

  if (controls.needsUpdate) controls.update();
  // Post-processing léger (bloom) : rendu via le composer, caméra du mode courant.
  post.renderPass.camera = modeCamera === 'fps' ? fpsCamera : camera;
  post.composer.render();

  // Expose des compteurs rendu pour la vérif perf (renderer.info).
  // autoReset=false autour d'un render à la demande : sinon EffectComposer
  // reset les compteurs à CHAQUE passe interne et on ne mesure que la dernière.
  window.__jardinRenderInfo = () => {
    renderer.info.autoReset = false;
    renderer.info.reset();
    post.composer.render();
    const out = { calls: renderer.info.render.calls, triangles: renderer.info.render.triangles };
    renderer.info.autoReset = true;
    return out;
  };
  // Exposé pour le diagnostic headless (test rendu direct vs composer).
  window.__jardinDebug = {
    renderer, post, scene, camera: () => (modeCamera === 'fps' ? fpsCamera : camera),
    // Redémarre la boucle si le rAF headless l'a abandonnée, avec rendu de secours.
    restart() {
      const boucle = () => {
        const t = performance.now();
        const deltaMs = Math.min(t - dernierT, 2000);
        dernierT = t;
        clock.tick(deltaMs);
        majVent(t / 1000);
        const m = meteoDuJour(clock.climat, clock.jours);
        meteo.appliquer(m, deltaMs / 1000);
        for (const inst of jardin.instances) if (!inst.decor) appliquerEtat(inst, clock.jours, clock.climat);
        appliquerLumiere(m);
        majAudio(m);
        onirique.update({
          delta: Math.min(deltaMs / 1000, 0.1),
          soleilDir: etatSoleil(clock.jours, heureEclairage()).direction,
          couleurLumiere: sun.color,
          nuit: heureEclairage() < 6.5 || heureEclairage() > 20.5,
          hauteurNorm: etatSoleil(clock.jours, heureEclairage()).hauteurNorm ?? 0.5,
          eclat: m.eclat,
          saison: clock.etat.saison,
          camera: modeCamera === 'fps' ? fpsCamera : camera,
          fog,
        });
        timeUI.maj();
        climatUI.maj();
        fps.update(deltaMs / 1000);
        jardin.majFPS?.();
        jardin.majAnims?.();
        if (controls.needsUpdate) controls.update();
        post.renderPass.camera = modeCamera === 'fps' ? fpsCamera : camera;
        post.composer.render();
      };
      renderer.setAnimationLoop(boucle);
    },
    // Une itération complète à la demande (rendu headless : le rAF peut être
    // suspendu par Chrome, on force tick + update + render hors boucle).
    step() {
      const t = performance.now();
      const deltaMs = Math.min(t - dernierT, 2000);
      dernierT = t;
      clock.tick(deltaMs);
      majVent(t / 1000);
      const m = meteoDuJour(clock.climat, clock.jours);
      meteo.appliquer(m, deltaMs / 1000);
      for (const inst of jardin.instances) if (!inst.decor) appliquerEtat(inst, clock.jours, clock.climat);
      appliquerLumiere(m);
      majAudio(m);
      onirique.update({
        delta: Math.min(deltaMs / 1000, 0.1),
        soleilDir: etatSoleil(clock.jours, heureEclairage()).direction,
        couleurLumiere: sun.color,
        nuit: heureEclairage() < 6.5 || heureEclairage() > 20.5,
        hauteurNorm: etatSoleil(clock.jours, heureEclairage()).hauteurNorm ?? 0.5,
        eclat: m.eclat,
        saison: clock.etat.saison,
        camera: modeCamera === 'fps' ? fpsCamera : camera,
        fog,
      });
      timeUI.maj();
      climatUI.maj();
      fps.update(deltaMs / 1000);
      jardin.majFPS?.();
      jardin.majAnims?.();
      if (controls.needsUpdate) controls.update();
      post.renderPass.camera = modeCamera === 'fps' ? fpsCamera : camera;
      post.composer.render();
      return { jours: clock.jours, saison: clock.etat.saison };
    },
  };

  if (premiereFrame) {
    premiereFrame = false;
    loader.retirer(); // la scène est prête : fondu de l'écran de chargement
  }

  frames++;
  const now = performance.now();
  if (now - fpsTimer >= 1000) {
    const fps = Math.round((frames * 1000) / (now - fpsTimer));
    fpsEl.textContent = String(fps);
    fpsEl.className = fps >= 50 ? 'good' : 'warn';
    frames = 0;
    fpsTimer = now;
  }
});

// --- Aide contextuelle à la plantation (hint au-dessus de la timebar) ---
const hint = document.createElement('div');
hint.id = 'hint-plantation';
document.body.appendChild(hint);
let hintTimer = null;
function montrerHint(texte) {
  hint.textContent = texte;
  hint.classList.add('visible');
  clearTimeout(hintTimer);
  hintTimer = setTimeout(() => hint.classList.remove('visible'), 3500);
}
// Premier message d'accueil (fondu après 5 s).
setTimeout(() => {
  montrerHint('Choisissez une espèce à gauche, cliquez sur la pelouse pour planter. Clic droit : arracher. V : marche dans le jardin.');
}, 1200);

// Plantations → compteur du catalogue, tenu à jour en temps réel.
function majCompteurCatalogue() {
  catalogue.majCompteur(jardin.compter().total);
}
const _planter = jardin.planter.bind(jardin);
const _retirer = jardin.retirer.bind(jardin);
jardin.planter = (...a) => { const r = _planter(...a); if (r) majCompteurCatalogue(); return r; };
jardin.retirer = (...a) => { const r = _retirer(...a); if (r) majCompteurCatalogue(); return r; };
majCompteurCatalogue();

// Exposé pour les vérifications automatisées (CDP).
window.__jardin = { clock, instances: jardin.instances, scene, meteo, climatUI, CLIMATS, jardin, catalogue, audio, appliquerEtat, fps, fpsCamera, get modeCamera() { return modeCamera; }, camera, controls, onirique };

