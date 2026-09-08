// Vérif arithmétique du time-lapse
const attendu = 12.6 * 30;
const mesure = 7 * 12.6 * (0.143 * 30);
console.log('attendu 12.6s:', attendu, 'jours');
console.log('mesure theorie (7fps):', Math.round(mesure), 'jours');
