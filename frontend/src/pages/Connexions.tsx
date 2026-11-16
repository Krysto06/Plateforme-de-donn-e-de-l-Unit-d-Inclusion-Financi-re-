import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, telecharger, type Chargement, type EtatSource } from "../api";
import { useAuth } from "../auth";
import { dateHeure, nombre } from "../format";
import { Bandeau, Bouton, EnTete, Section } from "../components/Layout";
import StatusBadge from "../components/StatusBadge";

type Test = { ok: boolean; message: string; details: string[] };

const DESCRIPTIONS: Record<string, string> = {
  WB: "API Indicators v2, sans clé. WDI et Global Findex.",
  FMI: "API SDMX 3.0, jeu de données IMF.STA:FAS.",
  IHSI: "Pas d'API publique : import de fichiers Excel ou CSV.",
};

export default function Connexions() {
  const { utilisateur } = useAuth();
  const admin = utilisateur?.role === "admin_uif";
  const [sources, setSources] = useState<EtatSource[]>([]);
  const [choisie, setChoisie] = useState("WB");
  const [historique, setHistorique] = useState<Chargement[]>([]);
  const [test, setTest] = useState<Test | null>(null);
  const [message, setMessage] = useState<{ ton: "succes" | "danger" | "info"; texte: string } | null>(null);
  const [occupe, setOccupe] = useState(false);
  const fichier = useRef<HTMLInputElement>(null);

  const recharger = useCallback(() => {
    api<EtatSource[]>("/api/sources").then(setSources).catch((e) => setMessage({ ton: "danger", texte: e.message }));
    api<Chargement[]>(`/api/sources/${choisie}/historique`).then(setHistorique).catch(() => setHistorique([]));
  }, [choisie]);

  useEffect(() => { recharger(); setTest(null); }, [recharger]);

  // Pendant une mise à jour, on actualise toutes les 5 secondes
  const enCours = sources.some((s) => s.statut === "en cours");
  useEffect(() => {
    if (!enCours) return;
    const t = setInterval(recharger, 5000);
    return () => clearInterval(t);
  }, [enCours, recharger]);

  const source = sources.find((s) => s.code === choisie);
  const estApi = choisie === "WB" || choisie === "FMI";

  const tester = async () => {
    setOccupe(true); setTest(null);
    try { setTest(await api<Test>(`/api/sources/${choisie}/tester`, { method: "POST" })); }
    catch (e) { setMessage({ ton: "danger", texte: (e as Error).message }); }
    finally { setOccupe(false); }
  };

  const mettreAJour = async () => {
    setOccupe(true);
    try {
      const r = await api<{ chargement_id: number }>(`/api/sources/${choisie}/mettre-a-jour`, { method: "POST" });
      setMessage({ ton: "info", texte: `Mise à jour lancée (chargement #${r.chargement_id}). L'état s'actualise automatiquement.` });
      recharger();
    } catch (e) { setMessage({ ton: "danger", texte: (e as Error).message }); }
    finally { setOccupe(false); }
  };

  const importer = async () => {
    const f = fichier.current?.files?.[0];
    if (!f) return;
    setOccupe(true);
    const corps = new FormData();
    corps.append("fichier", f);
    try {
      const c = await api<Chargement>("/api/sources/IHSI/import", { method: "POST", body: corps });
      setMessage({ ton: c.statut === "rejeté" ? "danger" : "succes", texte: `Import #${c.id} : ${c.statut}. ${c.message ?? ""}` });
      if (fichier.current) fichier.current.value = "";
      recharger();
    } catch (e) { setMessage({ ton: "danger", texte: (e as Error).message }); }
    finally { setOccupe(false); }
  };

  return (
    <>
      <EnTete titre="Sources et connexions" sousTitre="État de chaque source, test de connexion, mise à jour et historique" />
      {message && <Bandeau ton={message.ton}>{message.texte}</Bandeau>}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {["FMI", "WB", "IHSI"].map((code) => {
          const s = sources.find((x) => x.code === code);
          return (
            <button key={code} type="button" onClick={() => setChoisie(code)} aria-pressed={choisie === code}
              className={`flex min-h-[44px] flex-col gap-2 rounded-xl border bg-white p-5 text-left ${choisie === code ? "border-marine ring-2 ring-marine/20" : "border-bordure hover:border-marine"}`}>
              <span className="text-base font-semibold text-marine">{s?.nom ?? code}</span>
              <span className="text-[13px] text-discret">{DESCRIPTIONS[code]}</span>
              <span className="text-xs text-discret">{nombre(s?.nb_observations ?? 0)} valeurs · dernière mise à jour réussie : {dateHeure(s?.derniere_maj_reussie)}</span>
              {s && <StatusBadge texte={s.statut} />}
            </button>
          );
        })}
      </div>

      {source && (
        <Section titre={`Détail : ${source.nom}`} sousTitre={source.url ?? "Chargement par fichier"}
          action={admin && (
            <div className="flex flex-wrap gap-2">
              {estApi && <Bouton variante="secondaire" onClick={tester} disabled={occupe}>Tester la connexion</Bouton>}
              {estApi && <Bouton onClick={mettreAJour} disabled={occupe || source.statut === "en cours"}>Lancer une mise à jour</Bouton>}
            </div>
          )}>
          <dl className="m-0 grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
            <div><dt className="text-xs font-semibold text-discret">Calendrier automatique</dt><dd className="m-0">{source.calendrier_cron ? `cron « ${source.calendrier_cron} »` : "Manuel"}</dd></div>
            <div><dt className="text-xs font-semibold text-discret">Alerte de retard après</dt><dd className="m-0">{source.delai_alerte_jours ? `${source.delai_alerte_jours} jours` : "—"}</dd></div>
            <div><dt className="text-xs font-semibold text-discret">Dernier chargement</dt><dd className="m-0">{source.dernier_chargement ? `#${source.dernier_chargement.id} — ${source.dernier_chargement.statut}` : "Aucun"}</dd></div>
          </dl>
          {test && (
            <Bandeau ton={test.ok ? "succes" : "danger"}>
              <div className="flex flex-col gap-1"><strong>{test.message}</strong>
                <ul className="m-0 pl-5">{test.details.map((d) => <li key={d}>{d}</li>)}</ul></div>
            </Bandeau>
          )}
          {choisie === "IHSI" && admin && (
            <div className="flex flex-wrap items-end gap-3 rounded-lg border border-dashed border-champ p-4">
              <label className="flex flex-col gap-1 text-xs font-semibold text-discret">
                Fichier de population (modèle ihsi_population v1)
                <input ref={fichier} type="file" accept=".xlsx,.csv" className="champ font-normal" />
              </label>
              <Bouton onClick={importer} disabled={occupe}>Importer et contrôler</Bouton>
              <Bouton variante="secondaire" onClick={() => telecharger("/api/depots/modeles/ihsi_population", "ihsi_population_v1.xlsx")}>Télécharger le modèle</Bouton>
            </div>
          )}
        </Section>
      )}

      <Section titre="Toutes les sources">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead><tr className="text-left text-xs uppercase tracking-wide text-discret">
              {["Source", "Mode", "Valeurs", "Dernière mise à jour réussie", "Statut"].map((t) => <th key={t} className="border-b border-bordure px-3 py-2.5 font-semibold">{t}</th>)}
            </tr></thead>
            <tbody>{sources.map((s) => (
              <tr key={s.code} className="border-b border-fond">
                <td className="px-3 py-2.5"><span className="font-semibold">{s.code}</span> — {s.nom}</td>
                <td className="px-3 py-2.5">{s.mode}</td>
                <td className="px-3 py-2.5">{nombre(s.nb_observations)}</td>
                <td className="px-3 py-2.5">{dateHeure(s.derniere_maj_reussie)}</td>
                <td className="px-3 py-2.5"><StatusBadge texte={s.statut} /></td>
              </tr>))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section titre={`Historique : ${choisie}`} sousTitre="50 derniers chargements">
        {historique.length === 0 ? <p className="m-0 text-sm text-discret">Aucun chargement pour l'instant.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-sm">
              <thead><tr className="text-left text-xs uppercase tracking-wide text-discret">
                {["N°", "Date", "Déclencheur", "Auteur", "Résultat", "Statut"].map((t) => <th key={t} className="border-b border-bordure px-3 py-2.5 font-semibold">{t}</th>)}
              </tr></thead>
              <tbody>{historique.map((c) => (
                <tr key={c.id} className="border-b border-fond align-top">
                  <td className="px-3 py-2.5"><Link to={`/qualite?chargement=${c.id}`} className="font-semibold text-marine">#{c.id}</Link></td>
                  <td className="px-3 py-2.5 whitespace-nowrap">{dateHeure(c.cree_le)}</td>
                  <td className="px-3 py-2.5">{c.declencheur}</td>
                  <td className="px-3 py-2.5">{c.auteur}</td>
                  <td className="px-3 py-2.5 text-discret">{c.message}</td>
                  <td className="px-3 py-2.5"><StatusBadge texte={c.statut} /></td>
                </tr>))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </>
  );
}
