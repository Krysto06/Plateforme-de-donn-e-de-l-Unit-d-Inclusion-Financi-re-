import { useEffect, useState } from "react";
import { api, telecharger, type Kpi } from "../api";
import { Bandeau, Bouton, EnTete, Section } from "../components/Layout";

type Pays = { code: string; nom: string };

export default function Rapports() {
  const [kpis, setKpis] = useState<Kpi[]>([]);
  const [pays, setPays] = useState<Pays[]>([]);
  const [choixKpi, setChoixKpi] = useState<string[]>([]);
  const [choixPays, setChoixPays] = useState<string[]>([]);
  const [debut, setDebut] = useState("");
  const [fin, setFin] = useState("");
  const [auxiliaires, setAuxiliaires] = useState(false);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    api<Kpi[]>("/api/kpi").then(setKpis).catch((e) => setErreur(e.message));
    api<{ pays: Pays[] }>("/api/referentiels").then((r) => setPays(r.pays)).catch(() => {});
  }, []);

  const exporter = async (format: "csv" | "xlsx") => {
    const p = new URLSearchParams({ format });
    choixKpi.forEach((k) => p.append("indicateurs", k));
    choixPays.forEach((k) => p.append("pays", k));
    if (debut) p.set("annee_debut", debut);
    if (fin) p.set("annee_fin", fin);
    if (auxiliaires) p.set("avec_auxiliaires", "true");
    setErreur("");
    try { await telecharger(`/api/exports/observations?${p}`, `pdif.${format}`); }
    catch (e) { setErreur((e as Error).message); }
  };

  const basculer = (liste: string[], set: (l: string[]) => void, v: string) =>
    set(liste.includes(v) ? liste.filter((x) => x !== v) : [...liste, v]);

  return (
    <>
      <EnTete titre="Rapports et exports" sousTitre="Exporter les valeurs courantes avec leur source et leur numéro de chargement" />
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      <Section titre="Export des observations" sousTitre="Sans sélection : tous les KPI et tous les pays.">
        <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
          <legend className="mb-2 text-xs font-semibold text-discret">Indicateurs</legend>
          <div className="flex flex-wrap gap-2">
            {kpis.filter((k) => k.est_kpi).map((k) => (
              <label key={k.code} title={k.libelle} className={`flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border px-3 text-sm ${choixKpi.includes(k.code) ? "border-marine bg-fond" : "border-bordure"}`}>
                <input type="checkbox" className="h-4 w-4 accent-[#1a365d]" checked={choixKpi.includes(k.code)} onChange={() => basculer(choixKpi, setChoixKpi, k.code)} />
                {k.code}
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
          <legend className="mb-2 text-xs font-semibold text-discret">Pays</legend>
          <div className="flex flex-wrap gap-2">
            {pays.map((p) => (
              <label key={p.code} className={`flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border px-3 text-sm ${choixPays.includes(p.code) ? "border-marine bg-fond" : "border-bordure"}`}>
                <input type="checkbox" className="h-4 w-4 accent-[#1a365d]" checked={choixPays.includes(p.code)} onChange={() => basculer(choixPays, setChoixPays, p.code)} />
                {p.nom}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs font-semibold text-discret">De l'année
            <input className="champ w-28 font-normal" inputMode="numeric" value={debut} onChange={(e) => setDebut(e.target.value)} placeholder="2010" /></label>
          <label className="flex flex-col gap-1 text-xs font-semibold text-discret">À l'année
            <input className="champ w-28 font-normal" inputMode="numeric" value={fin} onChange={(e) => setFin(e.target.value)} placeholder="2025" /></label>
          <label className="flex min-h-[44px] items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4 accent-[#1a365d]" checked={auxiliaires} onChange={(e) => setAuxiliaires(e.target.checked)} />
            Inclure les séries auxiliaires (population, emprunteurs)
          </label>
        </div>
        <div className="flex flex-wrap gap-2">
          <Bouton onClick={() => exporter("xlsx")}>Exporter en Excel</Bouton>
          <Bouton variante="secondaire" onClick={() => exporter("csv")}>Exporter en CSV</Bouton>
        </div>
      </Section>
      <Section titre="Questionnaire FAS du FMI" sousTitre="Prévu plus tard : pré-remplissage du questionnaire annuel à partir des données des directions (phase 2).">
        <p className="m-0 text-sm text-discret">Non disponible en phase 1.</p>
      </Section>
    </>
  );
}
