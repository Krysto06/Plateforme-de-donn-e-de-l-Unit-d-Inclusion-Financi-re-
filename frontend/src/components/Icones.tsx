// Icônes au trait (décoratives : aria-hidden)
type P = { taille?: number };
const base = (taille: number) => ({
  width: taille, height: taille, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
  strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true,
});

export const IconeTableau = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></svg>
);
export const IconeConnexion = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><path d="M9 2v6" /><path d="M15 2v6" /><path d="M6 8h12v4a6 6 0 0 1-12 0z" /><path d="M12 18v4" /></svg>
);
export const IconeBouclier = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z" /><path d="m9 12 2 2 4-4" /></svg>
);
export const IconeDepot = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M20 16v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3" /></svg>
);
export const IconeCatalogue = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><path d="M4 4h10a4 4 0 0 1 4 4v12H8a4 4 0 0 1-4-4z" /><path d="M4 16a4 4 0 0 1 4-4h10" /></svg>
);
export const IconeRapport = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z" /><path d="M14 3v5h5" /><path d="M9 13h6" /><path d="M9 17h6" /></svg>
);
export const IconeSortie = ({ taille = 18 }: P) => (
  <svg {...base(taille)}><path d="M9 21H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h4" /><path d="m16 17 5-5-5-5" /><path d="M21 12H9" /></svg>
);
export const IconeMenu = ({ taille = 22 }: P) => (
  <svg {...base(taille)}><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /></svg>
);
export const IconeFermer = ({ taille = 22 }: P) => (
  <svg {...base(taille)}><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
);
export const IconeAttention = ({ taille = 20 }: P) => (
  <svg {...base(taille)}><path d="M12 9v4" /><path d="M12 17h.01" /><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg>
);
