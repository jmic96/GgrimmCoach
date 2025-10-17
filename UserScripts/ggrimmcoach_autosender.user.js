// ==UserScript==
// @name         GgrimmCoach Auto-Sender + Team Uploader (Types Required)
// @namespace    ggrimmcoach
// @version      3.0
// @description  Auto POST preview/turn logs to GgrimmCoach; Alt+T to paste Import/Export.
// @match        https://play.pokemonshowdown.com/*
// @match        https://*.pokemonshowdown.com/*
// @match        https://*.psim.us/*
// @match        https://psim.us/*
// @grant        none
// ==/UserScript==

(function () {
  const POST_LOG  = 'http://localhost:6060/log';
  const POST_TEAM = 'http://localhost:6060/team';
  const POLL_MS   = 1200;
  const TURN_RE      = /\|turn\|(\d+)/gi;
  const TURN_TEXT_RE = /\bTurn\s+(\d+)\b/gi;

  let lastTurnSent = null, previewSent = false;

  function getLogText() {
    const selectors = ['.battle-log','.battle','.innerbattle','.battle-history','#room-battle .battle-log','.battle-log-add','.log','.battle-log .inner'];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText && el.innerText.trim().length > 30) return el.innerText;
    }
    const maybe = [...document.querySelectorAll('*')].find(n => /Turn\s+\d+/.test(n.innerText || ''));
    return maybe ? maybe.innerText : '';
  }
  function phaseAndTurn(txt) {
    if (!txt) return { phase: 'other', turn: null };
    const hasPreview = txt.includes('|teampreview|') || (txt.includes('Start of battle') && !TURN_RE.test(txt));
    if (hasPreview) return { phase: 'preview', turn: null };
    let m = [...txt.matchAll(TURN_RE)]; if (m.length) return { phase: 'turn', turn: parseInt(m[m.length - 1][1], 10) };
    m = [...txt.matchAll(TURN_TEXT_RE)]; if (m.length) return { phase: 'turn', turn: parseInt(m[m.length - 1][1], 10) };
    return { phase: 'other', turn: null };
  }
  async function post(url, body) {
    try { await fetch(url, { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body }); }
    catch {}
  }
  async function tick() {
    const txt = getLogText(); if (!txt) return;
    const { phase, turn } = phaseAndTurn(txt);
    if (phase === 'preview' && !previewSent) { previewSent = true; lastTurnSent = null; await post(POST_LOG, txt); return; }
    if (phase === 'turn' && Number.isInteger(turn)) {
      if (lastTurnSent === null || turn > lastTurnSent) { lastTurnSent = turn; await post(POST_LOG, txt); return; }
    }
  }
  window.addEventListener('keydown', async (e) => {
    if (e.altKey && e.key.toLowerCase() === 't') {
      const example = `Paste your team (Types REQUIRED unless packs include species_types).
Corviknight @ Leftovers
Type: Flying/Steel
Ability: Pressure
EVs: 252 HP / 4 Def / 252 SpD
Careful Nature
- Brave Bird
- U-turn
- Defog
- Roost`;
      let txt = prompt(example, '');
      if (txt && txt.trim().length > 0) {
        try { await fetch(POST_TEAM, { method:'POST', headers:{'Content-Type':'text/plain'}, body:txt }); alert('Team uploaded.'); } catch { alert('Upload failed.'); }
      }
    }
  });
  function reset(){ lastTurnSent = null; previewSent = false; }
  window.addEventListener('popstate', reset); window.addEventListener('hashchange', reset);
  setInterval(tick, POLL_MS);
})();
