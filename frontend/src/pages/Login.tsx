import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Login() {
  const { utilisateur, connecter } = useAuth();
  const naviguer = useNavigate();
  const [identifiant, setIdentifiant] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  if (utilisateur) return <Navigate to={utilisateur.espace === "uif" ? "/" : "/depot"} replace />;

  const soumettre = async (e: FormEvent) => {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const u = await connecter(identifiant, motDePasse);
      naviguer(u.espace === "uif" ? "/" : "/depot", { replace: true });
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Connexion impossible.");
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <div className="flex flex-col justify-between gap-8 bg-marine px-8 py-10 text-white lg:w-[44%] lg:px-14 lg:py-14">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-[10px] bg-or text-sm font-bold text-marine">BRH</div>
          <span className="text-sm leading-snug text-menu">Banque de la République d'Haïti<br />Unité d'Inclusion Financière</span>
        </div>
        <div className="flex flex-col gap-3">
          <h1 className="m-0 text-4xl font-bold tracking-wide">PDIF</h1>
          <p className="m-0 max-w-md text-lg text-menu">
            Plateforme de données de l'inclusion financière : les KPI de la SNIF et du PNEF, leurs sources et leur contrôle qualité.
          </p>
        </div>
        <p className="m-0 text-xs text-menu">Usage interne. Données agrégées uniquement.</p>
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-10">
        <form onSubmit={soumettre} className="flex w-full max-w-sm flex-col gap-5" noValidate>
          <div className="flex flex-col gap-1">
            <h2 className="m-0 text-2xl font-semibold text-marine">Connexion</h2>
            <p className="m-0 text-sm text-discret">Votre espace (UIF ou direction) dépend de votre rôle.</p>
          </div>
          <label className="flex flex-col gap-1.5 text-sm font-semibold text-discret">
            Identifiant
            <input className="champ font-normal" autoComplete="username" value={identifiant}
              onChange={(e) => setIdentifiant(e.target.value)} required />
          </label>
          <label className="flex flex-col gap-1.5 text-sm font-semibold text-discret">
            Mot de passe
            <input className="champ font-normal" type="password" autoComplete="current-password" value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)} required />
          </label>
          {erreur && <p role="alert" className="m-0 rounded-lg bg-[#fde7e2] px-3 py-2 text-sm text-[#7d1d0b]">{erreur}</p>}
          <button type="submit" disabled={envoi || !identifiant || !motDePasse}
            className="min-h-[44px] rounded-lg bg-marine px-4 text-[15px] font-semibold text-white hover:bg-marine-fonce disabled:opacity-50">
            {envoi ? "Connexion…" : "Se connecter"}
          </button>
          <p className="m-0 text-xs text-discret">Mot de passe oublié : contacter l'administratrice de l'UIF.</p>
        </form>
      </div>
    </div>
  );
}
