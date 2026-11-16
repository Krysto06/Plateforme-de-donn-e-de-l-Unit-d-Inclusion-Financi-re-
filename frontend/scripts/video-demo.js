// Scénario de la vidéo de démonstration de la PDIF (mode démonstration, données publiques)
// Utilisation : lancer « npm run demo -- --port 5174 » dans frontend/, puis « node scripts/video-demo.js <dossier> ».
// Conversion en MP4 : ffmpeg -i <fichier>.webm -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart PDIF_demonstration.mp4
const { chromium } = require('playwright');
const DOSSIER = process.argv[2];
const URL = 'http://localhost:5174';

const AJOUTS = `
(() => {
  const css = document.createElement('style');
  css.textContent = \`
    #v-curseur{position:fixed;z-index:99999;width:22px;height:22px;border-radius:50%;background:rgba(184,134,11,.85);
      border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.35);pointer-events:none;transform:translate(-50%,-50%);
      transition:width .15s,height .15s;left:-50px;top:-50px}
    #v-curseur.clic{width:34px;height:34px;background:rgba(184,134,11,.55)}
    #v-legende{position:fixed;z-index:99998;left:calc(50% + 140px);bottom:16px;transform:translateX(-50%);max-width:900px;
      background:rgba(18,40,74,.94);color:#fff;font:600 19px/1.3 'IBM Plex Sans',system-ui,sans-serif;
      padding:11px 24px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.3);text-align:center;
      opacity:0;transition:opacity .4s}
    #v-legende small{display:block;font-weight:400;font-size:15px;color:#c9d6ea;margin-top:4px}
    #v-carton{position:fixed;inset:0;z-index:100000;background:#1a365d;color:#fff;display:flex;flex-direction:column;
      align-items:center;justify-content:center;gap:18px;font-family:'IBM Plex Sans',system-ui,sans-serif;
      text-align:center;padding:40px;transition:opacity .6s}
    #v-carton .logo{width:84px;height:84px;border-radius:18px;background:#b8860b;color:#1a365d;display:flex;
      align-items:center;justify-content:center;font-weight:700;font-size:24px}
    #v-carton h1{margin:0;font-size:60px;font-weight:700;letter-spacing:.02em}
    #v-carton p{margin:0;font-size:24px;color:#c9d6ea;max-width:900px}
    #v-carton .note{font-size:16px;color:#9fb4d3;margin-top:18px}\`;
  document.head.appendChild(css);
  const c = document.createElement('div'); c.id = 'v-curseur'; document.body.appendChild(c);
  const l = document.createElement('div'); l.id = 'v-legende'; document.body.appendChild(l);
  addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => c.classList.add('clic'), true);
  addEventListener('mouseup', () => c.classList.remove('clic'), true);
  window.__legende = (titre, detail) => {
    l.style.opacity = 0;
    setTimeout(() => { l.innerHTML = titre + (detail ? '<small>' + detail + '</small>' : ''); l.style.opacity = titre ? 1 : 0; }, 250);
  };
  window.__carton = (html) => {
    let k = document.getElementById('v-carton');
    if (!html) { if (k) { k.style.opacity = 0; setTimeout(() => k.remove(), 600); } return; }
    if (!k) { k = document.createElement('div'); k.id = 'v-carton'; document.body.appendChild(k); }
    k.innerHTML = html; k.style.opacity = 1;
  };
})();`;

(async () => {
  const navigateur = await chromium.launch();
  const contexte = await navigateur.newContext({
    viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1,
    recordVideo: { dir: DOSSIER, size: { width: 1280, height: 720 } },
  });
  const p = await contexte.newPage();
  const pause = (ms) => p.waitForTimeout(ms);
  const legende = (t, d = '') => p.evaluate(([t, d]) => window.__legende(t, d), [t, d]);
  const carton = (h) => p.evaluate((h) => window.__carton(h), h);
  let x = 640, y = 360;
  async function viser(selecteur) {
    const el = p.locator(selecteur).first();
    await el.scrollIntoViewIfNeeded();
    const b = await el.boundingBox();
    const cx = b.x + b.width / 2, cy = b.y + Math.min(b.height / 2, 30);
    await p.mouse.move(cx, cy, { steps: 25 }); x = cx; y = cy;
    return el;
  }
  async function cliquer(selecteur) { await viser(selecteur); await pause(300); await p.mouse.down(); await pause(120); await p.mouse.up(); await p.locator(selecteur).first().click(); }
  async function defiler(total, pas = 6) { for (let i = 0; i < pas; i++) { await p.mouse.wheel(0, total / pas); await pause(220); } }
  async function menu(texte) { await cliquer(`nav a:has-text("${texte}")`); await pause(900); await p.evaluate(() => scrollTo(0, 0)); }

  await p.goto(URL + '/');
  await p.waitForSelector('text=Comparaison avec les pays de référence');
  await p.evaluate(AJOUTS);
  await p.mouse.move(x, y);

  // Carton d'ouverture
  await carton(`<div class="logo">PDIF</div><h1>PDIF</h1>
    <p>Plateforme de données de l'inclusion financière</p>
    <p style="font-size:20px">Collecter · Contrôler · Historiser · Restituer les KPI de la SNIF et du PNEF</p>
    <p class="note">Prototype de démonstration non officiel — données publiques du FMI et de la Banque mondiale</p>`);
  await pause(4500);
  await carton(null); await pause(700);

  // 1. Tableau de bord
  await legende('Le tableau de bord', 'Chaque KPI avec sa valeur, sa source, son année et un badge d’ancienneté');
  await viser('button:has-text("Agences bancaires pour 100 000 adultes")'); await pause(2500);
  await viser('button:has-text("Part des adultes ayant un compte")'); await pause(2200);
  await legende('Deux sources, gardées séparément', 'Ici le FMI (2,67) et la Banque mondiale (2,67) pour les agences bancaires');
  await viser('text=Autre source : WB'); await pause(3000);
  await cliquer('button:has-text("Agences bancaires pour 100 000 adultes")'); await pause(600);
  await legende('Évolution dans le temps et comparaison régionale', 'Haïti face à 6 pays de référence et à la moyenne Amérique latine et Caraïbes');
  await defiler(480); await pause(1500);
  await viser('text=Moyenne Amérique latine et Caraïbes'); await pause(4000);
  await cliquer('button:has-text("Déposants des banques commerciales pour 1 000 adultes")'); await pause(500);
  await legende('Un clic sur un KPI change les graphiques', 'Les déposants reculent : 353 pour 1 000 adultes en 2009, 257 en 2020');
  await defiler(480); await pause(4200);
  await legende('L’état des 19 KPI du référentiel', 'Ce qui est déjà alimenté, et ce qui reste à collecter (directions, formulaires UIF, enquêtes)');
  await defiler(900, 8); await pause(3500);

  // 2. Sources et connexions
  await menu('Sources et connexions');
  await legende('Sources et connexions', 'FMI et Banque mondiale par API, IHSI par fichier — état et date de chaque mise à jour');
  await viser('button:has-text("Banque mondiale")'); await pause(2800);
  await legende('Tout est tracé', 'Chaque chargement garde sa date, son auteur et son résultat');
  await defiler(700, 7); await pause(3200);

  // 3. Contrôle qualité
  await menu('Contrôle qualité');
  await legende('Le contrôle qualité', '6 règles automatiques avant tout chargement : un échec bloque, une alerte attend une validation');
  await pause(2500);
  await viser('text=6. Données nominatives'); await pause(2200);
  await legende('Aucune donnée personnelle acceptée', 'Les fichiers contenant des noms, NIF ou numéros de compte sont refusés');
  await pause(2500);
  await viser('text=5. Variation inhabituelle');
  await legende('Les variations suspectes sont signalées', 'Le seuil se règle pour chaque KPI ; la décision humaine est enregistrée');
  await pause(3800);

  // 4. Dépôt
  await menu('Dépôt de données');
  await legende('Le dépôt par les directions (phase 2)', 'Modèle Excel par type de données, case « données agrégées uniquement », contrôle automatique');
  await viser('select >> nth=1'); await pause(2600);
  await viser('text=Je certifie que ce fichier contient uniquement'); await pause(3000);

  // 5. Catalogue
  await menu('Catalogue des données');
  await legende('Le catalogue des données', 'Le référentiel des KPI : modifiable sans toucher au code, avec la couverture de chaque source');
  await pause(1500); await defiler(600, 6); await pause(2800);

  // 6. Rapports
  await menu('Rapports et exports');
  await legende('Rapports et exports', 'Excel ou CSV, avec la source et le numéro de chargement de chaque valeur');
  await viser('button:has-text("Exporter en Excel")'); await pause(3500);

  // Carton de fin
  await legende('');
  await carton(`<div class="logo">PDIF</div><h1>Merci</h1>
    <p>Prochaines étapes : validation du référentiel des KPI, hébergement sur un serveur de la BRH, ouverture du dépôt aux directions</p>
    <p class="note">Prototype de démonstration non officiel — données publiques du FMI et de la Banque mondiale au 16/11/2026</p>`);
  await pause(5000);
  await contexte.close(); await navigateur.close();
})();
