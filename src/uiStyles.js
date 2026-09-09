// Styles des panneaux intégration (catalogue + renforts HUD), thème zen
// cohérent avec climateStyles.js : fond sombre translucide, verts doux.

export const STYLES_INTEGRATION = `
  /* ── Panneau catalogue (gauche) ── */
  #catalogue-panel {
    position: fixed;
    top: 8px;
    left: 8px;
    z-index: 20;
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 218px;
    max-height: calc(100vh - 140px);
    background: rgba(24, 34, 18, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 8px 10px;
    color: #eaf3df;
    font-size: 12.5px;
    user-select: none;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
  }
  #catalogue-panel .catalogue-titre {
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 10.5px;
    opacity: 0.75;
  }
  #catalogue-recherche {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 8px;
    color: #eaf3df;
    padding: 4px 8px;
    font-size: 12px;
    outline: none;
  }
  #catalogue-recherche::placeholder { color: rgba(234, 243, 223, 0.5); }
  #catalogue-liste {
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding-right: 2px;
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.25) transparent;
  }
  .cat-item {
    position: relative;
    display: flex;
    align-items: center;
    gap: 7px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #eaf3df;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 12px;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s ease;
  }
  .cat-item:hover { background: rgba(255, 255, 255, 0.16); }
  .cat-item.selected {
    background: #7da24c;
    border-color: #9fc06c;
    color: #fff;
  }
  .cat-item .cat-icone { flex: 0 0 auto; }
  .cat-item .cat-nom {
    flex: 1 1 auto;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .cat-item .cat-alerte {
    flex: 0 0 auto;
    font-size: 10px;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  .cat-item.inadapte .cat-alerte { opacity: 0.95; }
  .cat-item.inadapte:not(.selected) { background: rgba(150, 90, 60, 0.25); }
  #catalogue-pied {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    margin-top: 2px;
    font-size: 11.5px;
    opacity: 0.95;
    font-variant-numeric: tabular-nums;
  }
  #catalogue-vider {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #eaf3df;
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 11.5px;
    cursor: pointer;
    transition: background 0.15s ease;
    white-space: nowrap;
  }
  #catalogue-vider:hover { background: rgba(217, 136, 128, 0.35); }

  /* ── Barre audio (zenAudio) : hôte repositionné, contenu stylé à l'identique ── */
  /* Positionnée à gauche de la timebar (timebar centrée, audio calé au coin). */
  #audio-host {
    position: fixed;
    left: 8px;
    bottom: 14px;
    z-index: 30;
  }
  #audio-host .zen-audio-ui {
    position: static !important;
    left: auto !important;
    bottom: auto !important;
    background: rgba(24, 34, 18, 0.82) !important;
    border-radius: 12px !important;
  }
  #audio-host .zen-audio-ui button {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #eaf3df;
  }
  #audio-host .zen-audio-ui button:hover { background: rgba(255, 255, 255, 0.2); }

  /* ── Aide à la plantation (notification discrète au-dessus de la timebar) ── */
  #hint-plantation {
    position: fixed;
    left: 50%;
    bottom: 64px;
    transform: translateX(-50%);
    z-index: 20;
    background: rgba(24, 34, 18, 0.7);
    color: #eaf3df;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 12px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.6s ease;
  }
  #hint-plantation.visible { opacity: 1; }
`;
