// Couche onirique — shaders custom GLSL qui donnent l'ambiance « rêve éveillé » :
//  - herbe instanciée (milliers de brins, ondulation multi-octaves au vent) ;
//  - bassin : eau avec caustiques, fresnel et vagues douces ;
//  - particules saisonnières : pollen (printemps), pétales (automne),
//    lucioles (nuits d'été) — points souples additifs, dérive lente ;
//  - rais de lumière : plans billboardés additifs à travers les houppiers,
//    intenses aux heures dorées, éteints la nuit.
// Tout est piloté par le moteur existant (soleil, saison, météo) — aucune
// modification du socle : la couche s'ajoute, elle ne remplace rien.
import * as THREE from 'three';

// ── Ondulation de brins : vertex shader partagé (herbe) ─────────────────────
const VERT_HERBE = /* glsl */`
  uniform float uTemps;
  uniform float uVent;
  attribute float aPhase;
  attribute float aHauteur;
  varying float vHauteur;
  varying float vVariation;
  varying vec3 vPositionMonde;

  void main() {
    vHauteur = position.y;                 // 0 (sol) → 1 (pointe)
    vVariation = fract(aPhase * 7.31);
    vec3 p = position;
    // Origine de l'instance pour déphaser l'onde dans l'espace.
    vec3 origine = vec3(0.0);
    #ifdef USE_INSTANCING
      origine = instanceMatrix[3].xyz;
    #endif
    // Le brin fléchit vers la pointe (jamais à la base) — houle lente.
    float flexion = vHauteur * vHauteur;
    float t = uTemps;
    float onde = sin(t * 1.1 + aPhase * 6.2831 + origine.x * 0.45)
               + 0.5 * sin(t * 2.3 + aPhase * 12.566 + origine.z * 0.6)
               + 0.25 * sin(t * 4.3 + aPhase * 25.13);
    p.x += onde * uVent * flexion * 0.24;
    p.z += onde * uVent * flexion * 0.16;

    vec4 monde = modelMatrix * instanceMatrix * vec4(p * vec3(1.0, aHauteur, 1.0), 1.0);
    vPositionMonde = monde.xyz;
    gl_Position = projectionMatrix * viewMatrix * monde;
  }
`;

const FRAG_HERBE = /* glsl */`
  uniform vec3 uCouleur1;        // pointes
  uniform vec3 uCouleur2;        // bases
  uniform vec3 uCouleurLumiere;
  uniform vec3 uSoleilDir;
  uniform vec3 uFogColor;
  uniform float uFogDensity;
  varying float vHauteur;
  varying float vVariation;
  varying vec3 vPositionMonde;

  void main() {
    vec3 base = mix(uCouleur2, uCouleur1, vHauteur * 0.8 + vVariation * 0.2);
    // Diffus doux : les brins sont fins, pas d'ombre propre ici.
    float diff = 0.72 + 0.28 * max(normalize(uSoleilDir).y, 0.0);
    vec3 couleur = base * diff * mix(vec3(1.0), uCouleurLumiere, 0.35);
    float profondeur = distance(cameraPosition, vPositionMonde);
    float fog = 1.0 - exp(-profondeur * uFogDensity);
    couleur = mix(couleur, uFogColor, fog);
    gl_FragColor = vec4(couleur, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

/** Brin unitaire : triangle fin incurvé (4 sommets, 2 triangles). */
function geometrieBrin() {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
    -0.03, 0.0, 0.0, 0.03, 0.0, 0.0, 0.015, 0.55, 0.01, -0.005, 1.0, 0.02,
  ]), 3));
  g.setIndex([0, 1, 2, 1, 3, 2]);
  g.computeVertexNormals();
  return g;
}

// Palette d'herbe par saison (pointes / bases).
const HERBE_SAISONS = {
  printemps: ['#b4d878', '#4f8034'],
  ete: ['#9ecb5f', '#3e6b2a'],
  automne: ['#c9a95f', '#77682f'],
  hiver: ['#c4cdd6', '#7e8a96'],
};

/**
 * Champ d'herbe couvrant TOUTE la pelouse (le jardin est une prairie libre,
 * sans grille de parcelles). `nombre` = brins (réduit par ?herbe=N pour les
 * validations headless). Les brins près des dalles/passage restent possibles :
 * les pas japonais sont posés à y=0.03 et l'herbe y plie, effet naturel.
 */
function creerHerbe(scene, nombre, { demi = 23.5 } = {}) {
  const geo = geometrieBrin();
  // RNG déterministe : positions stables entre les builds.
  let a = 1337;
  const rnd = () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const uniforms = {
    uTemps: { value: 0 },
    uVent: { value: 0.5 },
    uCouleur1: { value: new THREE.Color(HERBE_SAISONS.printemps[0]) },
    uCouleur2: { value: new THREE.Color(HERBE_SAISONS.printemps[1]) },
    uCouleurLumiere: { value: new THREE.Color('#fff2d8') },
    uSoleilDir: { value: new THREE.Vector3(0.4, 0.8, 0.3) },
    uFogColor: { value: new THREE.Color('#dfe8ee') },
    uFogDensity: { value: 0.004 },
  };
  const mat = new THREE.ShaderMaterial({
    vertexShader: VERT_HERBE, fragmentShader: FRAG_HERBE,
    uniforms, side: THREE.DoubleSide,
  });
  const mesh = new THREE.InstancedMesh(geo, mat, nombre);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), eul = new THREE.Euler();
  const pos = new THREE.Vector3(), ech = new THREE.Vector3();
  const phases = new Float32Array(nombre), hauteurs = new Float32Array(nombre);
  let poses = 0, gardes = 0;
  while (poses < nombre && gardes < nombre * 40) {
    gardes++;
    const x = (rnd() * 2 - 1) * demi;
    const z = (rnd() * 2 - 1) * demi;
    // Prairie continue : pas de zone d'exclusion (le bassin repose au-dessus).
    eul.set((rnd() - 0.5) * 0.3, rnd() * Math.PI * 2, (rnd() - 0.5) * 0.3);
    q.setFromEuler(eul);
    const h = 0.28 + rnd() * 0.42;
    pos.set(x, 0, z); ech.set(1, h, 1);
    m.compose(pos, q, ech);
    mesh.setMatrixAt(poses, m);
    phases[poses] = rnd(); hauteurs[poses] = h;
    poses++;
  }
  mesh.count = poses; // brins réellement posés
  geo.setAttribute('aPhase', new THREE.InstancedBufferAttribute(phases, 1));
  geo.setAttribute('aHauteur', new THREE.InstancedBufferAttribute(hauteurs, 1));
  mesh.instanceMatrix.needsUpdate = true;
  mesh.frustumCulled = false;
  mesh.renderOrder = 1; // après le sol, avant l'eau
  scene.add(mesh);
  return { mesh, uniforms, brins: poses };
}

// ── Bassin : eau aux caustiques + fond sombre + anneau de pierre ────────────
const VERT_EAU = /* glsl */`
  uniform float uTemps;
  varying vec2 vUv;
  varying vec3 vPositionMonde;
  varying vec3 vNormale;

  void main() {
    vUv = uv;
    vec3 p = position;
    // Vagues douces : deux trains croisés, amplitude centimétrique.
    float h = sin(p.x * 1.8 + uTemps * 0.7) * 0.03
            + cos(p.y * 2.2 - uTemps * 0.55) * 0.025
            + sin((p.x + p.y) * 3.1 + uTemps * 0.9) * 0.01;
    p.z += h; // le plan est tourné : z local = hauteur monde
    float dx = cos(p.x * 1.8 + uTemps * 0.7) * 0.03 * 1.8
             + cos((p.x + p.y) * 3.1 + uTemps * 0.9) * 0.01 * 3.1;
    float dy = -sin(p.y * 2.2 - uTemps * 0.55) * 0.025 * 2.2
             + cos((p.x + p.y) * 3.1 + uTemps * 0.9) * 0.01 * 3.1;
    vNormale = normalize(vec3(-dx, -dy, 1.0));
    vec4 monde = modelMatrix * vec4(p, 1.0);
    vPositionMonde = monde.xyz;
    gl_Position = projectionMatrix * viewMatrix * monde;
  }
`;

const FRAG_EAU = /* glsl */`
  uniform float uTemps;
  uniform vec3 uCouleurProfonde;
  uniform vec3 uCouleurSurface;
  uniform vec3 uCouleurLumiere;
  uniform vec3 uSoleilDir;
  uniform vec3 uCiel;
  uniform vec3 uFogColor;
  uniform float uFogDensity;
  varying vec2 vUv;
  varying vec3 vPositionMonde;
  varying vec3 vNormale;

  // Caustiques douces : interférence de sinus itérée (pas de bords durs).
  float caustique(vec2 p, float t) {
    vec2 i = p;
    float c = 1.0;
    for (int n = 0; n < 3; n++) {
      float tt = t * (1.0 - (3.5 / float(n + 1)));
      i = p + vec2(cos(tt - i.x) + sin(tt + i.y), sin(tt - i.y) + cos(tt + i.x));
      c += 1.0 / length(vec2(p.x / (sin(i.x + tt) / 0.28), p.y / (cos(i.y + tt) / 0.28)));
    }
    c /= 3.0;
    c = 1.17 - pow(c, 1.4);
    return pow(abs(c), 8.0);
  }

  void main() {
    vec3 n = normalize(vNormale);
    vec3 vue = normalize(cameraPosition - vPositionMonde);
    float fresnel = pow(1.0 - clamp(dot(n, vue), 0.0, 1.0), 3.0);
    float c1 = caustique(vUv * 9.0 + vec2(uTemps * 0.02, uTemps * 0.013), uTemps * 0.35);
    float c2 = caustique(vUv * 6.0 - vec2(uTemps * 0.017, -uTemps * 0.021), uTemps * 0.27 + 5.0);
    float caustiques = (c1 + c2) * 0.5;
    vec3 couleur = mix(uCouleurProfonde, uCouleurSurface, 0.35 + 0.3 * n.z);
    couleur = mix(couleur, uCiel, fresnel * 0.75);
    vec3 reflet = reflect(-normalize(uSoleilDir), n);
    float spec = pow(max(dot(reflet, vue), 0.0), 90.0);
    couleur += uCouleurLumiere * spec * 0.9;
    couleur += uCouleurLumiere * caustiques * 0.25;
    float profondeur = distance(cameraPosition, vPositionMonde);
    float fog = 1.0 - exp(-profondeur * uFogDensity);
    couleur = mix(couleur, uFogColor, fog);
    gl_FragColor = vec4(couleur, 0.93);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

/** Bassin posé dans un angle de la pelouse (hors grille, hors allées). */
function creerBassin(scene, x, z, rayon = 2.8) {
  const groupe = new THREE.Group();
  // Fond sombre (silt) — visible à travers l'eau semi-transparente.
  const fond = new THREE.Mesh(
    new THREE.CircleGeometry(rayon, 40),
    new THREE.MeshStandardMaterial({ color: 0x1a3238, roughness: 1 })
  );
  fond.rotation.x = -Math.PI / 2;
  fond.position.y = 0.02;
  groupe.add(fond);
  // Surface d'eau (shader).
  const matEau = new THREE.ShaderMaterial({
    vertexShader: VERT_EAU, fragmentShader: FRAG_EAU,
    uniforms: {
      uTemps: { value: 0 },
      uCouleurProfonde: { value: new THREE.Color('#1d4d52') },
      uCouleurSurface: { value: new THREE.Color('#5fb8a8') },
      uCouleurLumiere: { value: new THREE.Color('#fff2d8') },
      uSoleilDir: { value: new THREE.Vector3(0.4, 0.8, 0.3) },
      uCiel: { value: new THREE.Color('#9cc7f0') },
      uFogColor: { value: new THREE.Color('#dfe8ee') },
      uFogDensity: { value: 0.004 },
    },
    transparent: true,
  });
  const eau = new THREE.Mesh(new THREE.CircleGeometry(rayon, 48), matEau);
  eau.rotation.x = -Math.PI / 2;
  eau.position.y = 0.14;
  eau.renderOrder = 2;
  groupe.add(eau);
  // Anneau de pierres (bordure).
  const pierres = new THREE.Mesh(
    new THREE.RingGeometry(rayon, rayon + 0.35, 40),
    new THREE.MeshStandardMaterial({ color: 0x8b8d90, roughness: 0.95 })
  );
  pierres.rotation.x = -Math.PI / 2;
  pierres.position.y = 0.05;
  pierres.receiveShadow = true;
  groupe.add(pierres);
  groupe.position.set(x, 0, z);
  scene.add(groupe);
  return { uniforms: matEau.uniforms, x, z, rayon: rayon + 0.5 };
}

// ── Particules saisonnières ─────────────────────────────────────────────────
function textureParticule() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.4, 'rgba(255,255,255,0.55)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const PARAMS_PARTICULES = {
  pollen:   { taille: 9,  couleur: '#ffe9a8', opacite: 0.55, hautMax: 8 },
  petales:  { taille: 16, couleur: '#f0c9a0', opacite: 0.70, hautMax: 7 },
  lucioles: { taille: 11, couleur: '#d7f5a3', opacite: 0.85, hautMax: 3.2 },
};

function creerSystemeParticules(scene, mode, { N = 500, zone = 24 } = {}) {
  const p = PARAMS_PARTICULES[mode];
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  const seed = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    pos[i * 3] = (Math.random() * 2 - 1) * zone;
    pos[i * 3 + 1] = mode === 'lucioles' ? 0.4 + Math.random() * 2.8 : Math.random() * p.hautMax;
    pos[i * 3 + 2] = (Math.random() * 2 - 1) * zone;
    seed[i] = Math.random() * Math.PI * 2;
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aSeed', new THREE.BufferAttribute(seed, 1));
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uTemps: { value: 0 },
      uTaille: { value: p.taille },
      uCouleur: { value: new THREE.Color(p.couleur) },
      uOpacite: { value: 0 },
      uPixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
      uTexture: { value: textureParticule() },
    },
    vertexShader: /* glsl */`
      uniform float uTemps;
      uniform float uTaille;
      uniform float uPixelRatio;
      attribute float aSeed;
      varying float vScintille;
      void main() {
        vec3 p = position;
        // Dérive lente en houle — chaque particule a sa phase.
        p.x += sin(uTemps * 0.32 + aSeed * 3.0) * 2.0;
        p.z += cos(uTemps * 0.26 + aSeed * 5.0) * 2.0;
        p.y += sin(uTemps * 0.2 + aSeed * 7.0) * 0.9;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        vScintille = 0.65 + 0.35 * sin(uTemps * 1.6 + aSeed * 11.0);
        gl_PointSize = uTaille * uPixelRatio * (30.0 / -mv.z) * vScintille;
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: /* glsl */`
      uniform vec3 uCouleur;
      uniform float uOpacite;
      uniform sampler2D uTexture;
      varying float vScintille;
      void main() {
        vec4 tex = texture2D(uTexture, gl_PointCoord);
        gl_FragColor = vec4(uCouleur * vScintille, tex.a * uOpacite);
        if (gl_FragColor.a < 0.01) discard;
      }
    `,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.visible = false;
  scene.add(points);
  return { points, mat, mode };
}

// ── Rais de lumière (god rays « poétiques », pas physiques) ─────────────────
const VERT_RAYON = /* glsl */`
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;
const FRAG_RAYON = /* glsl */`
  uniform float uIntensite;
  uniform float uTemps;
  uniform vec3 uCouleur;
  varying vec2 vUv;
  void main() {
    // Doux bords horizontaux + fondu vertical (lumière qui tombe).
    float bord = smoothstep(0.0, 0.35, vUv.x) * smoothstep(1.0, 0.65, vUv.x);
    float vertical = smoothstep(0.0, 0.25, vUv.y) * smoothstep(1.0, 0.45, vUv.y);
    // Stries douces qui descendent lentement (feuillage qui bouge).
    float stries = 0.75 + 0.25 * sin(vUv.x * 18.0 + uTemps * 0.35)
                            * sin(vUv.y * 6.0 - uTemps * 0.22);
    float alpha = bord * vertical * stries * uIntensite;
    gl_FragColor = vec4(uCouleur, alpha);
  }
`;

function creerRaisLumiere(scene, { N = 7, zone = 17 } = {}) {
  const groupe = new THREE.Group();
  const mats = [];
  let a = 4242;
  const rnd = () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  for (let i = 0; i < N; i++) {
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT_RAYON, fragmentShader: FRAG_RAYON,
      uniforms: {
        uIntensite: { value: 0 },
        uTemps: { value: 0 },
        uCouleur: { value: new THREE.Color('#ffe8b8') },
      },
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    mats.push(mat);
    const plan = new THREE.Mesh(new THREE.PlaneGeometry(1.1 + rnd() * 0.9, 4.5 + rnd() * 2.5), mat);
    plan.position.set((rnd() * 2 - 1) * zone, 2.4 + rnd() * 1.4, (rnd() * 2 - 1) * zone);
    plan.frustumCulled = false;
    plan.renderOrder = 3;
    groupe.add(plan);
  }
  scene.add(groupe);
  return { groupe, mats };
}

// ── Intégrateur de la couche ────────────────────────────────────────────────
/**
 * Crée toute la couche onirique. Options :
 *   brins    : nombre de brins d'herbe (défaut 26000 ; ?herbe=N pour tester)
 *   bassin   : { x, z, rayon } (défaut angle sud-ouest de la pelouse)
 * Retourne { update(etat), infos } — update est appelée chaque frame par main.js.
 */
export function creerOnirique(scene, opts = {}) {
  const brins = opts.brins ?? 26000;
  const bassinOpts = opts.bassin ?? { x: -20.3, z: 20.3, rayon: 2.8 };
  const herbe = creerHerbe(scene, brins);
  const bassin = creerBassin(scene, bassinOpts.x, bassinOpts.z, bassinOpts.rayon);
  const particules = {
    pollen: creerSystemeParticules(scene, 'pollen'),
    petales: creerSystemeParticules(scene, 'petales'),
    lucioles: creerSystemeParticules(scene, 'lucioles'),
  };
  const rais = creerRaisLumiere(scene);

  const _fog = new THREE.Color();
  const _soleil = new THREE.Vector3();
  let t = 0;

  /**
   * etat = {
   *   delta         : secondes écoulées,
   *   soleilDir     : Vector3 direction du soleil,
   *   couleurLumiere: Color du soleil,
   *   nuit          : bool,
   *   hauteurNorm   : hauteur du soleil 0..1,
   *   eclat         : météo 0..1,
   *   saison        : 'printemps'|'ete'|'automne'|'hiver',
   *   camera        : caméra courante (billboard des rais),
   *   fog           : THREE.FogExp2 de la scène (couleur/densité partagées),
   * }
   */
  function update(etat) {
    t += etat.delta;
    _soleil.copy(etat.soleilDir).normalize();
    _fog.copy(etat.fog?.color ?? 0xdfe8ee);
    const densite = Math.max(0.002, Math.min(0.02, etat.fog?.density ?? 0.004));

    // Herbe : temps, vent doux, teintes saisonnières, brume partagée.
    const uh = herbe.uniforms;
    uh.uTemps.value = t;
    uh.uVent.value = 0.45 + (etat.eclat ?? 0.8) * 0.25;
    uh.uSoleilDir.value.copy(_soleil);
    uh.uCouleurLumiere.value.copy(etat.couleurLumiere ?? 0xfff2d8);
    uh.uFogColor.value.copy(_fog);
    uh.uFogDensity.value = densite;
    const [c1, c2] = HERBE_SAISONS[etat.saison] ?? HERBE_SAISONS.printemps;
    uh.uCouleur1.value.set(c1);
    uh.uCouleur2.value.set(c2);

    // Eau : temps, soleil, couleur de ciel réfléchie = couleur de brume (jour).
    const ue = bassin.uniforms;
    ue.uTemps.value = t;
    ue.uSoleilDir.value.copy(_soleil);
    ue.uCouleurLumiere.value.copy(etat.couleurLumiere ?? 0xfff2d8);
    ue.uFogColor.value.copy(_fog);
    ue.uFogDensity.value = densite;
    ue.uCiel.value.copy(etat.nuit ? _fog.clone().multiplyScalar(0.25) : _fog).lerp(uh.uCouleur1.value, 0.15);

    // Particules : intensité saisonnière (fondu doux vers la cible).
    const cible = { pollen: 0, petales: 0, lucioles: 0 };
    if (!etat.nuit) {
      if (etat.saison === 'printemps') cible.pollen = 0.85 * (etat.eclat ?? 0.8);
      if (etat.saison === 'automne') cible.petales = 0.8;
    } else if (etat.saison === 'ete') {
      cible.lucioles = 0.9;
    }
    for (const sys of Object.values(particules)) {
      const u = sys.mat.uniforms;
      u.uTemps.value = t;
      const actuel = u.uOpacite.value;
      const cibleOp = cible[sys.mode] * PARAMS_PARTICULES[sys.mode].opacite;
      u.uOpacite.value = actuel + (cibleOp - actuel) * Math.min(1, etat.delta * 1.5);
      sys.points.visible = u.uOpacite.value > 0.02;
    }

    // Rais de lumière : max aux heures dorées (soleil bas), éteints la nuit
    // et atténués par le couvert. Billboard vers la caméra courante.
    const h = etat.hauteurNorm ?? 0;
    const doree = Math.max(0, 1 - Math.abs(h - 0.16) / 0.30); // cloche autour de 9°
    const inten = (etat.nuit ? 0 : doree) * (etat.eclat ?? 0.8) * 0.16;
    for (const mat of rais.mats) {
      mat.uniforms.uTemps.value = t;
      mat.uniforms.uIntensite.value = inten;
      mat.uniforms.uCouleur.value.copy(etat.couleurLumiere ?? 0xffe8b8);
    }
    if (inten > 0.001 && etat.camera) {
      rais.groupe.visible = true;
      for (const enfant of rais.groupe.children) {
        enfant.quaternion.copy(etat.camera.quaternion);
      }
    } else {
      rais.groupe.visible = false;
    }
  }

  return {
    update,
    infos: {
      get brins() { return herbe.brins; },
      bassin: { x: bassin.x, z: bassin.z, r: bassin.rayon },
      get raisVisibles() { return rais.groupe.visible; },
      particules: particules,
    },
  };
}

// Obstacle de marche : le bassin est solide (exporté pour FpsControls).
export const OBSTACLES_STATIQUES = [{ x: -20.3, z: 20.3, r: 3.3 }];
