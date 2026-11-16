import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, telecharger, type Carte } from "../api";
import { nombre } from "../format";
import { Bandeau, Bouton, EnTete, Section } from "../components/Layout";
import { IconeAttention } from "../components/Icones";
import KpiCard from "../components/KpiCard";
import StatusBadge, { tonDe } from "../components/StatusBadge";
import { theme } from "../theme";

type TableauDeBord = { cartes: Carte[]; resume: { kpi_total: number; kpi_disponibles: number } };
type Serie = { libelle: string; unite: string; points: { annee: number; valeur: number; source: string }[] };
type Comparaison = { libelle: string; unite: string; source: string | null; annee: number | null;
  pays: { pays: string; nom: string; annee: number; valeur: number; principal: boolean; agregat: boolean }[] };
type Departement = { code: string; nom: string };

const ANNEES = Array.from({ length: new Date().getFullYear() - 2004 + 1 }, (_, i) => new Date().getFullYear() - i);

function Filtre({ libelle, valeur, onChange, options }:
  { libelle: string; valeur: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-semibold text-discret">
      {libelle}
      <select className="champ font-normal" value={valeur} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
      </select>
    </label>
  );
}

export default function Dashboard() {
  const [annee, setAnnee] = useState("");
  const [departement, setDepartement] = useState("");
  const [sexe, setSexe] = useState("Total");
  const [donnees, setDonnees] = useState<TableauDeBord | null>(null);
  const [departements, setDepartements] = useState<Departement[]>([]);
  const [choix, setChoix] = useState("USA-01");
  const [serie, setSerie] = useState<Serie | null>(null);
  const [comparaison, setComparaison] = useState<Comparaison | null>(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    api<{ departements: Departement[] }>("/api/referentiels").then((r) => setDepartements(r.departements)).catch(() => {});
  }, []);

  useEffect(() => {
    const p = new URLSearchParams({ sexe });
    if (annee) p.set("annee", annee);
    if (departement) p.set("departement", departement);
    api<TableauDeBord>(`/api/tableau-de-bord?${p}`).then(setDonnees).catch((e) => setErreur(e.message));
  }, [annee, departement, sexe]);

  useEffect(() => {
    const p = new URLSearchParams({ sexe });
    if (departement) p.set("departement", departement);
    api<Serie>(`/api/kpi/${choix}/serie?${p}`).then(setSerie).catch(() => setSerie(null));
    api<Comparaison>(`/api/kpi/${choix}/comparaison${annee ? `?annee=${annee}` : ""}`).then(setComparaison).catch(() => setComparaison(null));
  }, [choix, annee, departement, sexe]);

  const cartes = donnees?.cartes ?? [];
  const principales = cartes.filter((c) => ["ACC-01", "USA-01", "PRO-01", "USA-04", "GEN-02", "EF-02"].includes(c.code));
  const carteChoisie = cartes.find((c) => c.code === choix);

  // Une seule source par graphique d'évolution : la source affichée sur la carte
  const points = useMemo(() => {
    if (!serie?.points) return [];
    const source = carteChoisie?.source ?? serie.points.at(-1)?.source;
    return serie.points.filter((p) => p.source === source && (!annee || p.annee <= Number(annee))).slice(-12);
  }, [serie, carteChoisie, annee]);

  const maxComparaison = Math.max(...(comparaison?.pays?.map((p) => p.valeur) ?? [1]), 1);
  const paysSeuls = comparaison?.pays?.filter((p) => !p.agregat) ?? [];
  const rangHaiti = [...paysSeuls].reverse().findIndex((p) => p.principal) + 1;

  return (
    <>
      <EnTete titre="Tableau de bord de l'inclusion financière" sousTitre="KPI de la SNIF et du PNEF, mis à jour à chaque chargement validé">
        <div className="flex flex-wrap items-end gap-3">
          <Filtre libelle="Période" valeur={annee} onChange={setAnnee}
            options={[["", "Dernière disponible"], ...ANNEES.map((a): [string, string] => [String(a), String(a)])]} />
          <Filtre libelle="Département" valeur={departement} onChange={setDepartement}
            options={[["", "Tout le pays"], ...departements.map((d): [string, string] => [d.code, d.nom])]} />
          <Filtre libelle="Sexe" valeur={sexe} onChange={setSexe} options={[["Total", "Tous"], ["F", "Femmes"], ["H", "Hommes"]]} />
          <Bouton variante="or" onClick={() => telecharger("/api/exports/observations?format=xlsx", "pdif.xlsx")}>Exporter</Bouton>
        </div>
      </EnTete>

      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}
      {donnees && donnees.resume.kpi_disponibles < donnees.resume.kpi_total && (
        <Bandeau>
          <span className="mt-px flex-none text-[#8a5a00]"><IconeAttention /></span>
          <span>
            {donnees.resume.kpi_disponibles} KPI sur {donnees.resume.kpi_total} ont une valeur
            {departement || sexe !== "Total" ? " pour ces filtres" : ""}. Les KPI marqués « À collecter » attendent
            leur source (direction, formulaire UIF ou enquête). Les séries du FMI pour Haïti s'arrêtent souvent avant l'année en cours.
          </span>
        </Bandeau>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {principales.map((c) => <KpiCard key={c.code} carte={c} actif={c.code === choix} onClick={() => setChoix(c.code)} />)}
      </div>

      <div className="flex flex-wrap gap-4">
        <Section className="flex-[1_1_420px]" titre={`Évolution : ${serie?.libelle ?? choix}`}
          sousTitre={`${serie?.unite ?? ""} · ${carteChoisie?.source_nom ?? "—"} · Haïti${departement ? ` (${departements.find((d) => d.code === departement)?.nom})` : ""}`}>
          {points.length === 0 ? (
            <p className="m-0 text-sm text-discret">Aucune valeur pour ce KPI avec ces filtres.</p>
          ) : (
            <div className="h-[240px]" role="img" aria-label={`Évolution de ${serie?.libelle} : ${points.map((p) => `${p.annee} ${nombre(p.valeur)}`).join(", ")}`}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={points} margin={{ top: 20, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#e6ebf2" />
                  <XAxis dataKey="annee" tickLine={false} axisLine={{ stroke: theme.couleurs.bordureChamp }} tick={{ fontSize: 12, fill: theme.couleurs.texteDiscret }} />
                  <YAxis tickLine={false} axisLine={false} width={48} tick={{ fontSize: 12, fill: theme.couleurs.texteDiscret }}
                    tickFormatter={(v) => nombre(v)} />
                  <Tooltip cursor={{ fill: "#eef3f9" }} formatter={(v) => [nombre(Number(v), serie?.unite), "Valeur"]}
                    labelFormatter={(a) => `Année ${a}`} />
                  <Bar dataKey="valeur" radius={[4, 4, 0, 0]} maxBarSize={44} isAnimationActive={false}
                    label={{ position: "top", fontSize: 11, fill: theme.couleurs.texteDiscret, formatter: (v: unknown) => nombre(Number(v)) }}>
                    {points.map((p, i) => <Cell key={p.annee} fill={i === points.length - 1 ? theme.couleurs.marine : "#9fb4d3"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Section>

        <Section className="flex-[1_1_420px]" titre="Comparaison avec les pays de référence"
          sousTitre={comparaison?.source ? `${comparaison.libelle} · dernière année disponible par pays · source ${comparaison.source}` : "—"}>
          {!comparaison?.pays || comparaison.pays.length === 0 ? (
            <p className="m-0 text-sm text-discret">Pas de données de comparaison pour ce KPI.</p>
          ) : (
            <>
              <ul className="m-0 flex list-none flex-col gap-3.5 p-0">
                {[...comparaison.pays].reverse().map((p) => (
                  <li key={p.pays} className="flex flex-col gap-1.5">
                    <div className="flex justify-between gap-3 text-sm">
                      <span className={p.principal ? "font-semibold" : ""}>{p.agregat ? "Moyenne Amérique latine et Caraïbes" : p.nom} <span className="text-xs text-discret">({p.annee}{p.agregat ? ", agrégat régional" : ""})</span></span>
                      <span className={p.principal ? "font-semibold" : ""}>{nombre(p.valeur, comparaison.unite)}</span>
                    </div>
                    <div className="h-3.5 rounded-[7px] bg-fond">
                      <div className="h-3.5 rounded-[7px]" style={{ width: `${Math.max(2, (p.valeur / maxComparaison) * 100)}%`,
                        background: p.principal ? theme.couleurs.or : p.agregat
                          ? `repeating-linear-gradient(45deg, ${theme.couleurs.marine} 0 4px, ${theme.couleurs.contexte} 4px 8px)`
                          : theme.couleurs.contexte }} />
                    </div>
                  </li>
                ))}
              </ul>
              {rangHaiti > 0 && <span className="text-xs text-discret">Haïti est {rangHaiti}<sup>e</sup> sur {paysSeuls.length} pays comparés
                {comparaison.pays.some((p) => p.agregat) ? " (barre hachurée : moyenne régionale de la Banque mondiale, hors classement)" : ""}.</span>}
            </>
          )}
        </Section>
      </div>

      <Section titre="État du référentiel des KPI" action={<Link to="/catalogue" className="text-sm font-semibold text-marine">Voir le catalogue</Link>}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-discret">
                {["Code", "Indicateur", "Valeur", "Source", "Statut"].map((t) => <th key={t} className="border-b border-bordure px-3 py-2.5 font-semibold">{t}</th>)}
              </tr>
            </thead>
            <tbody>
              {cartes.map((c) => (
                <tr key={c.code} className="border-b border-fond">
                  <td className="px-3 py-2.5 font-semibold">
                    <button type="button" onClick={() => setChoix(c.code)} className="min-h-[32px] font-semibold text-marine underline-offset-2 hover:underline">{c.code}</button>
                  </td>
                  <td className="px-3 py-2.5">{c.libelle}</td>
                  <td className="px-3 py-2.5 whitespace-nowrap">{nombre(c.valeur, c.unite)}</td>
                  <td className="px-3 py-2.5">{c.source_nom ?? c.source_attendue}</td>
                  <td className="px-3 py-2.5"><StatusBadge texte={c.valeur === null ? `À collecter${c.phase > 1 ? ` (phase ${c.phase})` : ""}` : c.anciennete.libelle}
                    ton={c.valeur === null ? "info" : tonDe(c.anciennete.code)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  );
}
