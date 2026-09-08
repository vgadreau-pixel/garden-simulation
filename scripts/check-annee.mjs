// Vérifie que le multi-pas couvre l'année en 12,6 s même à bas fps
for (const fps of [2, 3, 4, 5]) {
  const delta = 1000 / fps;
  const total = Math.min(delta, 1000);
  const jParSec = (total / 1000) * 30 * fps;
  console.log(`fps ${fps} → ${jParSec.toFixed(1)} j/s effectifs → ${(365 / jParSec).toFixed(1)} s pour une année`);
}
