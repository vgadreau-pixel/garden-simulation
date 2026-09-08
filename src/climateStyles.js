// Styles du panneau climat (injectés dans index.html).
// Séparés ici pour garder index.html lisible.

export const STYLES_CLIMAT = `
  /* ── Panneau climat ── */
  #climat-panel {
    position: fixed;
    top: 8px;
    right: 8px;
    z-index: 20;
    display: flex;
    flex-direction: column;
    gap: 5px;
    background: rgba(24, 34, 18, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 8px 10px;
    color: #eaf3df;
    font-size: 12.5px;
    user-select: none;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
    min-width: 170px;
  }
  #climat-panel .climat-titre {
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 10.5px;
    opacity: 0.75;
  }
  #climat-panel .cbtn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #eaf3df;
    border-radius: 8px;
    padding: 4px 9px;
    font-size: 12.5px;
    cursor: pointer;
    transition: background 0.15s ease;
    text-align: left;
  }
  #climat-panel .cbtn:hover { background: rgba(255, 255, 255, 0.18); }
  #climat-panel .cbtn.active {
    background: #7da24c;
    border-color: #9fc06c;
    color: #fff;
  }
  #climat-infos {
    font-variant-numeric: tabular-nums;
    opacity: 0.9;
    font-size: 11.5px;
    margin-top: 2px;
  }
`;
