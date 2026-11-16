import { useEffect, useState } from "react";
import { api, type Kpi } from "../api";
import { useAuth } from "../auth";
import { nombre } from "../format";
import { Bandeau, Bouton, EnTete, Section } from "../components/Layout";
import StatusBadge from "../components/StatusBadge";

type Edition = { code: string; libelle: string; seuil_variation_pct: number; source_preferee: string; actif: boolean };

export default function Catalogue() {
  const { utilisateur } = useAuth();
  const admin = utilisateur?.role === "admin_uif";
  const [kpis, setKpis] = useState<Kpi[]>([]);
  const [filtre, setFiltre] = useState("");
  const [edition, setEdition] = useState<Edition | null>(null);
  const [message, setMessage] = useState<{ ton: "succes" | "danger"; texte: string } | null>(null);

  const recharger = () => api<Kpi[]>("/api/catalogue").then(setKpis).catch((e) => setMessage({ ton: "danger", texte: e.message }));
  useEffect(() => { recharger(); }, []);

  const enregistrer = async () => {
    if (!edition) return;
    try {
      await api(`/api/kpi/${edition.code}`, { method: "PATCH", body: JSON.stringify({
        libelle: edition.libelle, seuil_variation_pct: edition.seuil_variation_pct,
        source_preferee: edition.source_preferee || null, actif: edition.actif }) });
      setMessage({ ton: "succes", texte: `${edition.code} mis à jour (tracé dans le journal).` });
      setEdition(null);
      recharger();
    } catch (e) { setMessage({ ton: "danger", texte: (e as Error).message }); }
  };

  const visibles = kpis.filter((k) => `${k.code} ${k.libelle} ${k.dimension}`.toLowerCase().includes(filtre.toLowerCase()));

  return (
    <>
      <EnTete titre="Catalogue des données" sousTitre="Référentiel des KPI, séries suivies chez chaque source et couverture de l'entrepôt">
        <label className="flex flex-col gap-1 text-xs font-semibold text-discret">
          Rechercher
          <input className="champ font-normal" value={filtre} onChange={(e) => setFiltre(e.target.value)} placeholder="Code, libellé, dimension" />
        </label>
      </EnTete>
      {message && <Bandeau ton={message.ton}>{message.texte}</Bandeau>}

      {edition && (
        <Section titre={`Modifier ${edition.code}`} sousTitre="Le référentiel est une table : ces changements ne demandent aucune modification du code.">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-xs font-semibold text-discret sm:col-span-2">Libellé
              <input className="champ font-normal" value={edition.libelle} onChange={(e) => setEdition({ ...edition, libelle: e.target.value })} /></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-discret">Seuil de variation inhabituelle (%)
              <input className="champ font-normal" type="number" min={1} value={edition.seuil_variation_pct}
                onChange={(e) => setEdition({ ...edition, seuil_variation_pct: Number(e.target.value) })} /></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-discret">Source affichée en priorité
              <select className="champ font-normal" value={edition.source_preferee} onChange={(e) => setEdition({ ...edition, source_preferee: e.target.value })}>
                <option value="">Aucune</option>{["FMI", "WB", "IHSI", "UIF", "DIR"].map((s) => <option key={s}>{s}</option>)}
              </select></label>
            <label className="flex min-h-[44px] items-center gap-3 text-sm">
              <input type="checkbox" className="h-5 w-5 accent-[#1a365d]" checked={edition.actif} onChange={(e) => setEdition({ ...edition, actif: e.target.checked })} />
              KPI actif (décoché : retiré du tableau de bord, valeurs conservées)
            </label>
          </div>
          <div className="flex gap-2"><Bouton onClick={enregistrer}>Enregistrer</Bouton><Bouton variante="secondaire" onClick={() => setEdition(null)}>Annuler</Bouton></div>
        </Section>
      )}

      <Section titre={`${visibles.length} indicateurs`} sousTitre="Les séries « auxiliaires » servent aux calculs (dénominateurs, parts) et ne sont pas des KPI.">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] border-collapse text-sm">
            <thead><tr className="text-left text-xs uppercase tracking-wide text-discret">
              {["Code", "Indicateur", "Unité", "Séries suivies", "Couverture", "Statut", ""].map((t, i) => <th key={i} className="border-b border-bordure px-3 py-2.5 font-semibold">{t}</th>)}
            </tr></thead>
            <tbody>{visibles.map((k) => (
              <tr key={k.code} className="border-b border-fond align-top">
                <td className="px-3 py-2.5 font-semibold">{k.code}</td>
                <td className="px-3 py-2.5"><div>{k.libelle}</div><div className="text-xs text-discret">{k.dimension} · {k.formule}{k.calcul ? ` · calcul : ${k.calcul}` : ""}</div></td>
                <td className="px-3 py-2.5">{k.unite}</td>
                <td className="px-3 py-2.5 text-xs">{k.series.length === 0 ? <span className="text-discret">{k.source_attendue}</span> :
                  k.series.map((s) => <div key={s.code_serie}><strong>{s.source}</strong> {s.code_serie}{s.sexe !== "Total" ? ` (${s.sexe})` : ""}</div>)}</td>
                <td className="px-3 py-2.5 text-xs">{(k.couverture ?? []).length === 0 ? "—" :
                  k.couverture!.map((c) => <div key={c.source}>{c.source} : {nombre(c.nb_valeurs)} valeurs, {c.annee_min}–{c.annee_max}, {c.nb_pays} pays</div>)}</td>
                <td className="px-3 py-2.5"><StatusBadge texte={!k.actif ? "retiré" : !k.est_kpi ? "auxiliaire" : (k.nb_valeurs ?? 0) > 0 ? "alimenté" : `à collecter${k.phase > 1 ? ` (phase ${k.phase})` : ""}`}
                  ton={!k.actif ? "neutre" : !k.est_kpi ? "neutre" : (k.nb_valeurs ?? 0) > 0 ? "succes" : "info"} /></td>
                <td className="px-3 py-2.5">{admin && <Bouton variante="secondaire" onClick={() => setEdition({ code: k.code, libelle: k.libelle,
                  seuil_variation_pct: k.seuil_variation_pct, source_preferee: k.source_preferee ?? "", actif: k.actif })}>Modifier</Bouton>}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  );
}
