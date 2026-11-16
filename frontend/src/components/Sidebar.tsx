import type { ReactElement } from "react";
import { NavLink } from "react-router-dom";
import { DEMO } from "../api";
import { useAuth } from "../auth";
import {
  IconeCatalogue, IconeConnexion, IconeBouclier, IconeDepot, IconeFermer, IconeRapport, IconeSortie, IconeTableau,
} from "./Icones";

type Lien = { vers: string; libelle: string; icone: ReactElement };

const LIENS_UIF: Lien[] = [
  { vers: "/", libelle: "Tableau de bord", icone: <IconeTableau /> },
  { vers: "/connexions", libelle: "Sources et connexions", icone: <IconeConnexion /> },
  { vers: "/qualite", libelle: "Contrôle qualité", icone: <IconeBouclier /> },
  { vers: "/depot", libelle: "Dépôt de données", icone: <IconeDepot /> },
  { vers: "/catalogue", libelle: "Catalogue des données", icone: <IconeCatalogue /> },
  { vers: "/rapports", libelle: "Rapports et exports", icone: <IconeRapport /> },
];
const LIENS_DIRECTION: Lien[] = [{ vers: "/depot", libelle: "Dépôt de données", icone: <IconeDepot /> }];

function initiales(nom: string) {
  return nom.split(/\s+/).filter(Boolean).map((m) => m[0]).slice(0, 2).join("").toUpperCase();
}

export default function Sidebar({ ouvert, fermer }: { ouvert: boolean; fermer: () => void }) {
  const { utilisateur, deconnecter } = useAuth();
  if (!utilisateur) return null;
  const liens = utilisateur.espace === "uif" ? LIENS_UIF : LIENS_DIRECTION;

  return (
    <>
      {ouvert && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={fermer} aria-hidden="true" />}
      {/* Colonne bleu marine sur toute la hauteur de la page ; le menu y reste visible au défilement */}
      <div className="lg:w-[280px] lg:flex-none lg:bg-marine">
      <aside
        id="menu-principal"
        className={`fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col gap-7 overflow-y-auto bg-marine px-[18px] py-7 text-white transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${ouvert ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex flex-col gap-3.5 px-1.5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 flex-none items-center justify-center rounded-[10px] bg-or text-sm font-bold text-marine">{DEMO ? "PDIF" : "BRH"}</div>
              <span className="text-xs leading-snug text-menu">
                {DEMO ? <>Prototype de démonstration<br />non officiel</> : <>Banque de la République d'Haïti<br />Unité d'Inclusion Financière</>}
              </span>
            </div>
            <button type="button" onClick={fermer} aria-label="Fermer le menu" className="flex h-11 w-11 items-center justify-center rounded-lg text-menu-lien lg:hidden">
              <IconeFermer />
            </button>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[26px] font-bold tracking-wide">PDIF</span>
            <span className="text-[13px] text-menu">Plateforme de données de l'inclusion financière</span>
          </div>
        </div>

        <nav aria-label="Navigation principale" className="flex flex-col gap-1">
          <span className="px-3.5 pb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#9fb4d3]">
            {utilisateur.espace === "uif" ? "Espace UIF" : "Espace direction"}
          </span>
          {liens.map((l) => (
            <NavLink
              key={l.vers}
              to={l.vers}
              end={l.vers === "/"}
              onClick={fermer}
              className={({ isActive }) =>
                `flex min-h-[44px] items-center gap-3 rounded-lg px-3.5 py-3 text-[15px] no-underline ${isActive ? "bg-white font-semibold text-marine" : "text-menu-lien hover:bg-marine-clair"}`
              }
            >
              {l.icone}
              <span>{l.libelle}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto flex items-center gap-3 rounded-[10px] bg-marine-fonce p-3.5">
          <div className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-full bg-marine-clair text-[13px] font-semibold">
            {initiales(utilisateur.nom)}
          </div>
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="truncate text-sm font-semibold">{utilisateur.nom}</span>
            <span className="truncate text-xs text-menu">{utilisateur.direction?.nom ?? utilisateur.role_libelle}</span>
          </div>
          {!DEMO && <button type="button" onClick={deconnecter} aria-label="Se déconnecter" className="flex h-11 w-11 flex-none items-center justify-center rounded-lg text-menu-lien hover:bg-marine-clair">
            <IconeSortie />
          </button>}
        </div>
      </aside>
      </div>
    </>
  );
}
