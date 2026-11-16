import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, DEMO, enregistrerJeton, lireJeton, type Utilisateur } from "./api";

const VISITEUR: Utilisateur = {
  identifiant: "visiteur", nom: "Visiteur", role: "cadre_uif", role_libelle: "Démonstration (lecture seule)",
  espace: "uif", direction: null,
};

type Auth = {
  utilisateur: Utilisateur | null;
  pret: boolean;
  connecter: (identifiant: string, motDePasse: string) => Promise<Utilisateur>;
  deconnecter: () => void;
};

const Contexte = createContext<Auth | null>(null);

export function FournisseurAuth({ children }: { children: ReactNode }) {
  const [utilisateur, setUtilisateur] = useState<Utilisateur | null>(DEMO ? VISITEUR : null);
  const [pret, setPret] = useState(DEMO);

  useEffect(() => {
    if (DEMO) return;
    if (!lireJeton()) {
      setPret(true);
      return;
    }
    api<Utilisateur>("/api/auth/moi")
      .then(setUtilisateur)
      .catch(() => enregistrerJeton(null))
      .finally(() => setPret(true));
  }, []);

  const deconnecter = useCallback(() => {
    enregistrerJeton(null);
    setUtilisateur(null);
  }, []);

  useEffect(() => {
    window.addEventListener("pdif:deconnexion", deconnecter);
    return () => window.removeEventListener("pdif:deconnexion", deconnecter);
  }, [deconnecter]);

  const connecter = async (identifiant: string, motDePasse: string) => {
    const r = await api<{ jeton: string; utilisateur: Utilisateur }>("/api/auth/connexion", {
      method: "POST",
      body: JSON.stringify({ identifiant, mot_de_passe: motDePasse }),
    });
    enregistrerJeton(r.jeton);
    setUtilisateur(r.utilisateur);
    return r.utilisateur;
  };

  return <Contexte.Provider value={{ utilisateur, pret, connecter, deconnecter }}>{children}</Contexte.Provider>;
}

export function useAuth(): Auth {
  const ctx = useContext(Contexte);
  if (!ctx) throw new Error("useAuth doit être utilisé dans FournisseurAuth");
  return ctx;
}
