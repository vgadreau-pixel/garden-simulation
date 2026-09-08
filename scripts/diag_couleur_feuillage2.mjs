// Reproduction complète de couleurFeuillage avec les couleurs exactes du
// catalogue cerisier, pour vérifier la teinte calculée à 289 j.
const DAYS_PER_YEAR = 365;

const moisVersJours = (m) => ((m - 0.5) * DAYS_PER_YEAR) / 12;

function deltaCycle(a, b) {
  let d = a - b;
  if (d > DAYS_PER_YEAR / 2) d -= DAYS_PER_YEAR;
  if (d < -DAYS_PER_YEAR / 2) d += DAYS_PER_YEAR;
  return d;
}

function smoothstep(t) {
  const x = Math.min(1, Math.max(0, t));
  return x * x * (3 - 2 * x);
}

const pts = [
  { j: moisVersJours(4), c: '#8fc94b', nom: 'printemps' },
  { j: moisVersJours(7), c: '#3f7d2c', nom: 'été' },
  { j: moisVersJours(10), c: '#d98032', nom: 'automne' },
  { j: moisVersJours(1), c: null, nom: 'hiver' },
];

const hex = (r, g, b) => '#' + [r, g, b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');

for (const jours of [106.5, 197.7, 250, 289, 15.2]) {
  let i0 = pts.length - 1;
  for (let i = 0; i < pts.length; i++) {
    if (deltaCycle(jours, pts[i].j) >= 0 && deltaCycle(pts[(i + 1) % 4].j, jours) > 0) { i0 = i; break; }
  }
  const i1 = (i0 + 1) % 4;
  const span = deltaCycle(pts[i1].j, pts[i0].j);
  const t = smoothstep(deltaCycle(jours, pts[i0].j) / (span || 1));
  const colA = pts[i0].c, colB = pts[i1].c;
  let out;
  if (colA && colB) {
    const pa = parseInt(colA.slice(1), 16), pb = parseInt(colB.slice(1), 16);
    const ar = (pa >> 16) / 255, ag = ((pa >> 8) & 255) / 255, ab = (pa & 255) / 255;
    const br = (pb >> 16) / 255, bg = ((pb >> 8) & 255) / 255, bb = (pb & 255) / 255;
    out = hex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t);
  } else if (colA) {
    const pa = parseInt(colA.slice(1), 16);
    const ar = (pa >> 16) / 255, ag = ((pa >> 8) & 255) / 255, ab = (pa & 255) / 255;
    const br = 0x6e / 255, bg = 0x55 / 255, bb = 0x3a / 255;
    out = hex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t);
  } else {
    out = '#6e553a';
  }
  console.log(`jours=${jours} segment=[${pts[i0].nom}->${pts[i1].nom}] t=${t.toFixed(3)} -> ${out}`);
}
