// Appels à l'API FastAPI. Le jeton de connexion est gardé pour la session du navigateur.
const CLE_JETON = "pdif.jeton";

export class ErreurApi extends Error {
  constructor(public statut: number, message: string) {
    super(message);
  }
}

export function lireJeton(): string | null {
  try {
    return sessionStorage.getItem(CLE_JETON);
  } catch {
    return null;
  }
}

export function enregistrerJeton(jeton: string | null) {
  try {
    if (jeton) sessionStorage.setItem(CLE_JETON, jeton);
    else sessionStorage.removeItem(CLE_JETON);
  } catch {
    /* navigation privée : la session ne survivra pas au rechargement */
  }
}

async function messageErreur(r: Response): Promise<string> {
  try {
    const corps = await r.json();
    if (typeof corps.detail === "string") return corps.detail;
    if (Array.isArray(corps.detail)) return corps.detail.map((d: { msg: string }) => d.msg).join(" ; ");
  } catch {
    /* corps non JSON */
  }
  return `Erreur ${r.status}`;
}

export async function api<T>(chemin: string, options: RequestInit = {}): Promise<T> {
  const entetes = new Headers(options.headers);
  const jeton = lireJeton();
  if (jeton) entetes.set("Authorization", `Bearer ${jeton}`);
  if (options.body && !(options.body instanceof FormData)) entetes.set("Content-Type", "application/json");
  const r = await fetch(chemin, { ...options, headers: entetes });
  if (r.status === 401 && jeton) {
    enregistrerJeton(null);
    window.dispatchEvent(new Event("pdif:deconnexion"));
  }
  if (!r.ok) throw new ErreurApi(r.status, await messageErreur(r));
  return (await r.json()) as T;
}

// Téléchargement d'un fichier protégé (export, modèle Excel)
export async function telecharger(chemin: string, nomParDefaut: string) {
  const jeton = lireJeton();
  const r = await fetch(chemin, { headers: jeton ? { Authorization: `Bearer ${jeton}` } : {} });
  if (!r.ok) throw new ErreurApi(r.status, await messageErreur(r));
  const nom = /filename="([^"]+)"/.exec(r.headers.get("Content-Disposition") ?? "")?.[1] ?? nomParDefaut;
  const url = URL.createObjectURL(await r.blob());
  const lien = document.createElement("a");
  lien.href = url;
  lien.download = nom;
  lien.click();
  URL.revokeObjectURL(url);
}

// ---- Types renvoyés par l'API
export type Utilisateur = {
  identifiant: string;
  nom: string;
  role: "admin_uif" | "cadre_uif" | "point_focal";
  role_libelle: string;
  espace: "uif" | "direction";
  direction: { id: number; nom: string } | null;
};

export type Carte = {
  code: string;
  libelle: string;
  dimension: string;
  unite: string;
  phase: number;
  source_attendue: string | null;
  valeur: number | null;
  annee: number | null;
  source: string | null;
  source_nom: string | null;
  chargement_id: number | null;
  autres_sources: { source: string; valeur: number }[];
  anciennete: { code: "recente" | "a_surveiller" | "ancienne" | "a_collecter"; libelle: string };
};

export type Controle = { regle: string; resultat: "réussi" | "alerte" | "échec"; detail: string };

export type Chargement = {
  id: number;
  source: string;
  source_nom: string;
  cree_le: string;
  termine_le: string | null;
  declencheur: string;
  auteur: string;
  fichier_nom: string | null;
  nb_lignes: number;
  nb_nouvelles: number;
  nb_modifiees: number;
  nb_inchangees: number;
  statut: string;
  message: string | null;
  decision_par: string | null;
  decision_commentaire: string | null;
  attend_validation: boolean;
  controles?: Controle[];
  apercu?: Record<string, string | number>[];
  nb_valeurs_en_attente?: number;
  depot?: { direction: string; type_donnees: string; periode: string; institution: string | null; commentaire: string | null };
};

export type EtatSource = {
  code: string;
  nom: string;
  mode: string;
  url: string | null;
  statut: string;
  en_retard: boolean;
  nb_observations: number;
  calendrier_cron: string | null;
  delai_alerte_jours: number | null;
  derniere_maj_reussie: string | null;
  dernier_chargement: { id: number; statut: string; cree_le: string; message: string | null } | null;
};

export type Kpi = {
  code: string;
  libelle: string;
  dimension: string;
  unite: string;
  formule: string | null;
  calcul: string | null;
  source_attendue: string | null;
  source_preferee: string | null;
  frequence: string;
  phase: number;
  est_kpi: boolean;
  seuil_variation_pct: number;
  actif: boolean;
  series: { source: string; code_serie: string; sexe: string; verifie_le: string | null }[];
  couverture?: { source: string; nb_valeurs: number; annee_min: number; annee_max: number; nb_pays: number }[];
  nb_valeurs?: number;
};
