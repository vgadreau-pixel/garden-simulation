// Végétation réaliste — modèles GLTF texturés (Quaternius, CC0) + vent.
//
// Remplace le rendu en primitives par des modèles 3D texturés :
//  - 1-2 modèles par catégorie du catalogue (arbre, arbuste, fleur/légume),
//    réutilisés avec variations d'échelle / rotation / teinte : la FORME vient
//    du modèle, la COULEUR saisonnière vient du moteur (seasons.js) appliquée
//    en teinte multiplicative sur les matériaux de feuillage ;
//  - feuillage animé par un léger vertex shader (onBeforeCompile) : oscillation
//    sinusoïdale proportionnelle à la hauteur du modèle, phase par instance ;
//  - normalisation automatique de la taille : chaque modèle est mis à l'échelle
//    pour que sa hauteur monde = min(tailleMatureM, 7) m (proportions jardin).
// Les primitives d'origine restent en repli visuel si un modèle échoue à charger.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const URLS_MODELES = {
  arbre_normal: '/models/arbre_normal.glb',
  arbre_maple: '/models/arbre_maple.glb',
  arbre_birch: '/models/arbre_birch.glb',
  arbre_pine: '/models/arbre_pine.glb',
  arbuste_bush: '/models/arbuste_bush.glb',
  fleur_clump: '/models/fleur_clump.glb',
  fleur_plant: '/models/fleur_plant.glb',
};

// Espèce du catalogue → modèle. Repli par type si absent.
const ESPECE_VERS_MODELE = {
  cerisier: 'arbre_normal',
  pommier: 'arbre_normal',
  erable_japonais: 'arbre_maple',
  bouleau: 'arbre_birch',
  sapin: 'arbre_pine',
  olivier: 'arbre_normal',
  lavande: 'arbuste_bush',
  romarin: 'arbuste_bush',
  buis: 'arbuste_bush',
  rosier: 'arbuste_bush',
  hortensia: 'arbuste_bush',
  forsythia: 'arbuste_bush',
  tulipe: 'fleur_clump',
  coquelicot: 'fleur_clump',
  marguerite: 'fleur_clump',
  iris: 'fleur_plant',
  tomate: 'fleur_plant',
  carotte: 'fleur_plant',
  courgette: 'fleur_plant',
};
const TYPE_VERS_MODELE = {
  arbre: 'arbre_normal',
  arbuste: 'arbuste_bush',
  fleur: 'fleur_clump',
  legume: 'fleur_plant',
};

// Matériaux de feuillage : teintés par la saison + animés par le vent.
// (bark/tronc : matériaux partagés, non teintés.)
const REGEX_FEUILLE = /leaf|leaves|grass|flower|petal/i;

// ── Chargement des gabarits (1 requête par fichier, partagé entre instances) ──
const loaderGLTF = new GLTFLoader();
const gabarits = new Map(); // clé → Promise<tpl | null>

function obtenirGabarit(cle) {
  if (!gabarits.has(cle)) {
    const url = URLS_MODELES[cle];
    gabarits.set(
      cle,
      new Promise((resoudre) => {
        loaderGLTF.load(
          url,
          (gltf) => {
            const racine = gltf.scene;
            racine.updateWorldMatrix(true, true);
            const boite = new THREE.Box3().setFromObject(racine);
            // Certains GLB Quaternius placent le modèle loin de l'origine :
            // recentrer le pivot sur le centre XZ de la boîte (le sol reste y=0).
            const centre = boite.getCenter(new THREE.Vector3());
            racine.position.x -= centre.x;
            racine.position.z -= centre.z;
            racine.position.y -= boite.min.y;
            // Le GLB Quaternius embarque un noeud racine "Root_Scene" décalé
            // (ici x=-210.8) : LE recentrer aussi, sinon tous les clones
            // héritent d'un offset monde énorme (le gabarit lui-même = la
            // hiérarchie Root_Scene ; le "racine" clone est ce Root_Scene).
            racine.traverse((n) => {
              if (Math.abs(n.position.x) > 10) n.position.x = 0;
              if (Math.abs(n.position.z) > 10) n.position.z = 0;
            });
            racine.updateWorldMatrix(true, true);
            const boite2 = new THREE.Box3().setFromObject(racine);
            const hauteur = Math.max(0.001, boite2.max.y - boite2.min.y);
            resoudre({ racine, hauteur });
          },
          undefined,
          () => resoudre(null) // échec de chargement → repli primitives
        );
      })
    );
  }
  return gabarits.get(cle);
}

// ── Vent : oscillation sinusoïdale dans le vertex shader ──
// Un uniform de temps partagé par toutes les instances ; l'amplitude est
// proportionnelle à la hauteur du modèle (unités locales ≈ cm chez Quaternius).
const uTemps = { value: 0 };

function appliquerVent(materiau, phase, amplitude) {
  materiau.onBeforeCompile = (shader) => {
    shader.uniforms.uTemps = uTemps;
    shader.uniforms.uPhase = { value: phase };
    shader.uniforms.uAmp = { value: amplitude };
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        '#include <common>\nuniform float uTemps;\nuniform float uPhase;\nuniform float uAmp;'
      )
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
  transformed.x += sin(uTemps * 1.6 + uPhase) * uAmp;
  transformed.z += cos(uTemps * 1.15 + uPhase * 1.7) * uAmp * 0.7;`
      );
  };
  materiau.customProgramCacheKey = () => 'vent-feuillage';
}

/** Horloge du vent — appelée chaque frame par appliquerEtat. */
export function majVent(tSecondes) {
  uTemps.value = tSecondes;
}

// ── Habillage d'une instance du moteur existant ──
/**
 * Remplace (asynchrone, sans bloquer) les primitives d'une instance créée par
 * creerInstancePlante par un clone du gabarit GLTF de son espèce.
 * Une fois posé : inst.vegActif = true, et appliquerEtat pilote teinte +
 * masse foliaire du modèle via majVegetation. Échec de chargement : repli
 * silencieux sur les primitives d'origine.
 */
export function habillerInstance(inst) {
  const plante = inst.plante;
  const cle = ESPECE_VERS_MODELE[plante.id] || TYPE_VERS_MODELE[plante.type] || 'arbre_normal';
  obtenirGabarit(cle).then((tpl) => {
    if (!tpl) return;
    if (!inst.group.parent) return; // instance déjà arrachée pendant le chargement

    const cl = tpl.racine.clone(true);

    // Taille : hauteur monde cible = min(tailleMatureM, 7) m, la croissance
    // (échelle du groupe instance) s'applique ensuite par-dessus.
    const cible = Math.min(plante.tailleMatureM || 2, 7);
    const facteur = cible / tpl.hauteur;
    cl.scale.setScalar(facteur);

    // Matériaux de feuillage : 1 clone par instance (teinte saisonnière
    // indépendante), animés par le vent avec une phase propre.
    const leafMats = [];
    const leafMeshes = [];
    const phase = (inst.rotationY || 0) * 7.3 + cl.position.x * 1.7;
    const amplitude = tpl.hauteur * 0.012; // ~1,2 % de la hauteur en unités locales
    cl.traverse((o) => {
      if (!o.isMesh) return;
      const nom = o.material?.name || '';
      if (REGEX_FEUILLE.test(nom)) {
        const m = o.material.clone();
        m.color = new THREE.Color(0x4a7d34); // teintée par la saison à chaque frame
        m.side = THREE.DoubleSide; // quads de feuilles Quaternius : visibles de dessous
        appliquerVent(m, phase, amplitude);
        o.material = m;
        o.frustumCulled = false; // boundingSphere radius 0 du GLB fausse le culling
        leafMats.push(m);
        leafMeshes.push({ mesh: o, base: o.scale.clone() });
      }
    });

    inst.group.add(cl);

    // Fleurs / fruits (petits marqueurs du moteur d'origine) : repositionnés
    // sur le houppier du modèle ; neige et primitives cachées.
    const boite = new THREE.Box3().setFromObject(cl);
    const h = Math.max(0.1, boite.max.y - boite.min.y);
    inst.parties.fleurs.position.y = h * 0.62;
    inst.parties.fruits.position.y = h * 0.5;
    inst.parties.fleurs.scale.setScalar(Math.max(0.15, (h * 0.4) / 0.7));
    inst.parties.fruits.scale.setScalar(Math.max(0.15, (h * 0.36) / 0.55));

    // Le modèle encode déjà la taille adulte de l'espèce : la croissance
    // pluri-annuelle (stades 0..1) pilote seule l'échelle.
    inst.echelleBase = 1;
    inst.veg = { groupe: cl, leafMats, leafMeshes };
    inst.vegActif = true;
  });
}

/**
 * Applique l'état saisonnier au modèle 3D d'une instance (appelée par
 * appliquerEtat une fois vegActif) : teinte du feuillage + masse foliaire
 * (les feuilles rétrécissent vers 0 en hiver → arbre nu, sans swap brutal).
 */
export function majVegetation(inst, et) {
  const veg = inst.veg;
  if (!veg) return;
  for (const m of veg.leafMats) m.color.copy(et.couleur);
  const masse = et.masseFoliaire;
  const k = masse <= 0.03 ? 0.0001 : 0.12 + 0.88 * masse;
  for (const rec of veg.leafMeshes) {
    rec.mesh.scale.copy(rec.base).multiplyScalar(k);
  }
}
