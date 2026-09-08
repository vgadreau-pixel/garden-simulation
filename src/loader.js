// Écran de chargement : fondu d'entrée zen pendant l'initialisation WebGL,
// retiré progressivement dès que la première frame est rendue.
const HTML = `
  <div id="loader">
    <div class="loader-interieur">
      <div class="loader-feuille">🌱</div>
      <div class="loader-titre">Jardin des Saisons</div>
      <div class="loader-sous-titre">Le jardin s'éveille…</div>
      <div class="loader-barre"><div class="loader-remplissage"></div></div>
    </div>
  </div>
`;

const STYLES = `
  #loader {
    position: fixed; inset: 0; z-index: 100;
    background: linear-gradient(160deg, #20301c 0%, #2c4023 60%, #3a5230 100%);
    display: flex; align-items: center; justify-content: center;
    color: #eaf3df; font-family: system-ui, sans-serif;
    opacity: 1; transition: opacity 0.9s ease;
  }
  #loader.parti { opacity: 0; pointer-events: none; }
  .loader-interieur { text-align: center; }
  .loader-feuille { font-size: 52px; animation: osciller 2.6s ease-in-out infinite; }
  .loader-titre { font-size: 26px; font-weight: 600; letter-spacing: 0.06em; margin-top: 14px; }
  .loader-sous-titre { font-size: 13.5px; opacity: 0.75; margin-top: 6px; font-style: italic; }
  .loader-barre {
    width: 210px; height: 3px; margin: 22px auto 0; border-radius: 2px;
    background: rgba(255, 255, 255, 0.14); overflow: hidden;
  }
  .loader-remplissage {
    width: 40%; height: 100%; border-radius: 2px;
    background: #9fc06c; animation: balayer 1.4s ease-in-out infinite;
  }
  @keyframes balayer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(260%); }
  }
  @keyframes osciller {
    0%, 100% { transform: rotate(-6deg) scale(1); }
    50% { transform: rotate(6deg) scale(1.06); }
  }
`;

export function creerEcranChargement() {
  const style = document.createElement('style');
  style.textContent = STYLES;
  document.head.appendChild(style);

  const racine = document.createElement('div');
  racine.id = 'loader';
  racine.innerHTML = HTML;
  document.body.appendChild(racine);

  let parti = false;
  return {
    /**
     * Fait disparaître l'écran (fondu 0,9 s puis suppression du DOM).
     * Idempotent : peut être appelé plusieurs fois sans effet de bord.
     */
      retirer() {
      if (parti) return;
      parti = true;
      racine.classList.add('parti');
      setTimeout(() => racine.remove(), 1000);
    },
  };
}
