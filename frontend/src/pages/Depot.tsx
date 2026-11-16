import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { api, telecharger, type Chargement } from "../api";
import { dateHeure } from "../format";
import { Bandeau, Bouton, EnTete, Section } from "../components/Layout";
import StatusBadge from "../components/StatusBadge";

type Parametres = {
  depots_ouverts: boolean;
  directions: { id: number; nom: string }[];
  types_institution: { id: number; libelle: string }[];
  institutions: { id: number; nom: string; type_institution_id: number }[];
  types_donnees: { code: string; libelle: string; version: string; indicateurs: string[]; fichier: string }[];
};
type DepotLigne = { id: number; direction: string; institution: string | null; type_donnees_libelle: string; periode: string;
  fichier_nom: string; statut: string; cree_le: string; auteur: string };

function Champ({ libelle, children }: { libelle: string; children: ReactNode }) {
  return <label className="flex flex-col gap-1.5 text-xs font-semibold text-discret">{libelle}{children}</label>;
}

export default function Depot() {
  const [p, setP] = useState<Parametres | null>(null);
  const [depots, setDepots] = useState<DepotLigne[]>([]);
  const [direction, setDirection] = useState("");
  const [typeInst, setTypeInst] = useState("");
  const [institution, setInstitution] = useState("");
  const [typeDonnees, setTypeDonnees] = useState("");
  const [periode, setPeriode] = useState(String(new Date().getFullYear() - 1));
  const [commentaire, setCommentaire] = useState("");
  const [fichier, setFichier] = useState<File | null>(null);
  const [certifie, setCertifie] = useState(false);
  const [resultat, setResultat] = useState<Chargement | null>(null);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  const recharger = () => api<DepotLigne[]>("/api/depots").then(setDepots).catch(() => {});
  useEffect(() => {
    api<Parametres>("/api/depots/parametres").then((r) => {
      setP(r);
      if (r.directions.length === 1) setDirection(String(r.directions[0].id));
    }).catch((e) => setErreur(e.message));
    recharger();
  }, []);

  const institutions = useMemo(() => p?.institutions.filter((i) => String(i.type_institution_id) === typeInst) ?? [], [p, typeInst]);
  const modele = p?.types_donnees.find((t) => t.code === typeDonnees);
  const nom = (liste: { id: number; nom?: string; libelle?: string }[] | undefined, id: string) =>
    liste?.find((x) => String(x.id) === id)?.nom ?? liste?.find((x) => String(x.id) === id)?.libelle ?? "—";
  const pret = direction && typeInst && typeDonnees && /^\d{4}(-T[1-4])?$/.test(periode) && fichier && certifie;

  const deposer = async (e: FormEvent) => {
    e.preventDefault();
    if (!pret || !fichier) return;
    setEnvoi(true); setErreur(""); setResultat(null);
    const corps = new FormData();
    corps.append("direction_id", direction);
    corps.append("type_institution_id", typeInst);
    if (institution) corps.append("institution_id", institution);
    corps.append("type_donnees", typeDonnees);
    corps.append("periode", periode);
    if (commentaire) corps.append("commentaire", commentaire);
    corps.append("certifie_agrege", "true");
    corps.append("fichier", fichier);
    try {
      const r = await api<{ chargement: Chargement }>("/api/depots", { method: "POST", body: corps });
      setResultat(r.chargement);
      recharger();
    } catch (err) { setErreur((err as Error).message); }
    finally { setEnvoi(false); }
  };

  return (
    <>
      <EnTete titre="Dépôt de données" sousTitre="Transmettre un fichier agrégé selon le modèle du type de données choisi" />
      {p && !p.depots_ouverts && (
        <Bandeau>Le dépôt par les directions ne sera ouvert qu'une fois la plateforme hébergée sur un serveur de la BRH. Vous pouvez déjà télécharger les modèles.</Bandeau>
      )}
      {erreur && <Bandeau ton="danger">{erreur}</Bandeau>}

      <div className="flex flex-wrap gap-4">
        <Section className="flex-[2_1_480px]" titre="Nouvel envoi">
          <form onSubmit={deposer} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Champ libelle="Direction">
                <select className="champ font-normal" value={direction} onChange={(e) => setDirection(e.target.value)} required>
                  <option value="">Choisir…</option>
                  {p?.directions.map((d) => <option key={d.id} value={d.id}>{d.nom}</option>)}
                </select>
              </Champ>
              <Champ libelle="Type d'institution">
                <select className="champ font-normal" value={typeInst} onChange={(e) => { setTypeInst(e.target.value); setInstitution(""); }} required>
                  <option value="">Choisir…</option>
                  {p?.types_institution.map((t) => <option key={t.id} value={t.id}>{t.libelle}</option>)}
                </select>
              </Champ>
              <Champ libelle="Institution (facultatif : vide = ensemble du type)">
                <select className="champ font-normal" value={institution} onChange={(e) => setInstitution(e.target.value)} disabled={!typeInst}>
                  <option value="">Toutes</option>
                  {institutions.map((i) => <option key={i.id} value={i.id}>{i.nom}</option>)}
                </select>
              </Champ>
              <Champ libelle="Type de données">
                <select className="champ font-normal" value={typeDonnees} onChange={(e) => setTypeDonnees(e.target.value)} required>
                  <option value="">Choisir…</option>
                  {p?.types_donnees.map((t) => <option key={t.code} value={t.code}>{t.libelle}</option>)}
                </select>
              </Champ>
              <Champ libelle="Période (AAAA ou AAAA-T1 à T4)">
                <input className="champ font-normal" value={periode} onChange={(e) => setPeriode(e.target.value.trim())} pattern="\d{4}(-T[1-4])?" required />
              </Champ>
              <Champ libelle="Fichier (.xlsx ou .csv, 10 Mo au plus)">
                <input className="champ font-normal" type="file" accept=".xlsx,.csv" onChange={(e) => setFichier(e.target.files?.[0] ?? null)} required />
              </Champ>
            </div>
            {modele && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-fond p-4 text-sm">
                <span>Modèle à utiliser : <strong>{modele.fichier}</strong> — indicateurs acceptés : {modele.indicateurs.join(", ")}</span>
                <Bouton variante="secondaire" onClick={() => telecharger(`/api/depots/modeles/${modele.code}`, modele.fichier)}>Télécharger le modèle</Bouton>
              </div>
            )}
            <Champ libelle="Commentaire (facultatif)">
              <textarea className="champ min-h-[72px] font-normal" value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
            </Champ>
            <label className="flex min-h-[44px] items-start gap-3 text-sm">
              <input type="checkbox" className="mt-0.5 h-5 w-5 flex-none accent-[#1a365d]" checked={certifie} onChange={(e) => setCertifie(e.target.checked)} />
              <span>Je certifie que ce fichier contient uniquement des <strong>données agrégées</strong> : aucun nom, NIF, numéro de compte ou téléphone de client.</span>
            </label>
            <div><Bouton type="submit" disabled={!pret || envoi || !p?.depots_ouverts}>{envoi ? "Envoi et contrôle…" : "Déposer et lancer les contrôles"}</Bouton></div>
          </form>
        </Section>

        <Section className="flex-[1_1_280px]" titre="Récapitulatif de l'envoi">
          <dl className="m-0 flex flex-col gap-2.5 text-sm">
            {[["Direction", nom(p?.directions, direction)], ["Type d'institution", nom(p?.types_institution, typeInst)],
              ["Institution", institution ? nom(institutions, institution) : "Toutes"], ["Type de données", modele?.libelle ?? "—"],
              ["Version du modèle", modele?.version ?? "—"], ["Période", periode || "—"], ["Fichier", fichier?.name ?? "—"],
              ["Données agrégées", certifie ? "Certifié" : "Non certifié"]].map(([t, v]) => (
              <div key={t} className="flex justify-between gap-3 border-b border-fond pb-2"><dt className="text-discret">{t}</dt><dd className="m-0 text-right font-semibold">{v}</dd></div>
            ))}
          </dl>
        </Section>
      </div>

      {resultat && (
        <Section titre={`Résultat de l'envoi #${resultat.id}`} action={<StatusBadge texte={resultat.attend_validation ? "en attente de validation UIF" : resultat.statut} ton={resultat.attend_validation ? "attention" : undefined} />}>
          <p className="m-0 text-sm">{resultat.message}</p>
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {resultat.controles?.map((k) => (
              <li key={k.regle} className="flex flex-col gap-1 text-sm sm:flex-row sm:gap-3">
                <span className="sm:w-24 sm:flex-none"><StatusBadge texte={k.resultat} /></span><span><strong>{k.regle}</strong> — {k.detail}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section titre="Mes envois">
        {depots.length === 0 ? <p className="m-0 text-sm text-discret">Aucun envoi pour l'instant.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-sm">
              <thead><tr className="text-left text-xs uppercase tracking-wide text-discret">
                {["N°", "Date", "Type de données", "Période", "Fichier", "Statut"].map((t) => <th key={t} className="border-b border-bordure px-3 py-2.5 font-semibold">{t}</th>)}
              </tr></thead>
              <tbody>{depots.map((d) => (
                <tr key={d.id} className="border-b border-fond">
                  <td className="px-3 py-2.5 font-semibold">#{d.id}</td><td className="px-3 py-2.5 whitespace-nowrap">{dateHeure(d.cree_le)}</td>
                  <td className="px-3 py-2.5">{d.type_donnees_libelle}</td><td className="px-3 py-2.5">{d.periode}</td>
                  <td className="px-3 py-2.5">{d.fichier_nom}</td><td className="px-3 py-2.5"><StatusBadge texte={d.statut} /></td>
                </tr>))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </>
  );
}
