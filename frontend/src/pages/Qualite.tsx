import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Chargement } from "../api";
import { useAuth } from "../auth";
import { dateHeure, nombre } from "../format";
import { Bandeau, Bouton, EnTete, Section } from "../components/Layout";
import StatusBadge from "../components/StatusBadge";

export default function Qualite() {
  const { utilisateur } = useAuth();
  const admin = utilisateur?.role === "admin_uif";
  const [params, setParams] = useSearchParams();
  const [liste, setListe] = useState<Chargement[]>([]);
  const [detail, setDetail] = useState<Chargement | null>(null);
  const [commentaire, setCommentaire] = useState("");
  const [message, setMessage] = useState<{ ton: "succes" | "danger"; texte: string } | null>(null);
  const [occupe, setOccupe] = useState(false);
  const idChoisi = Number(params.get("chargement")) || null;

  const recharger = useCallback(() => {
    api<Chargement[]>("/api/chargements").then((l) => {
      setListe(l);
      if (!idChoisi) {
        const premier = l.find((c) => c.attend_validation) ?? l[0];
        if (premier) setParams({ chargement: String(premier.id) }, { replace: true });
      }
    }).catch((e) => setMessage({ ton: "danger", texte: e.message }));
  }, [idChoisi, setParams]);

  useEffect(recharger, [recharger]);
  useEffect(() => {
    setCommentaire("");
    if (idChoisi) api<Chargement>(`/api/chargements/${idChoisi}`).then(setDetail).catch(() => setDetail(null));
  }, [idChoisi]);

  const decider = async (decision: "accepter" | "renvoyer") => {
    if (!detail) return;
    setOccupe(true);
    try {
      const c = await api<Chargement>(`/api/chargements/${detail.id}/decision`, {
        method: "POST", body: JSON.stringify({ decision, commentaire: commentaire || null }),
      });
      setMessage({ ton: decision === "accepter" ? "succes" : "danger",
        texte: `Chargement #${c.id} ${decision === "accepter" ? "accepté" : "renvoyé"} : ${c.message ?? ""}` });
      setDetail(await api<Chargement>(`/api/chargements/${detail.id}`));
      recharger();
    } catch (e) { setMessage({ ton: "danger", texte: (e as Error).message }); }
    finally { setOccupe(false); }
  };

  const enAttente = liste.filter((c) => c.attend_validation);
  const colonnesApercu = detail?.apercu?.[0] ? Object.keys(detail.apercu[0]) : [];

  return (
    <>
      <EnTete titre="Contrôle qualité" sousTitre="Chaque envoi passe 6 règles. Un échec bloque ; une alerte attend votre décision." />
      {message && <Bandeau ton={message.ton}>{message.texte}</Bandeau>}
      {enAttente.length > 0 && <Bandeau>{enAttente.length} envoi(s) attendent une validation humaine.</Bandeau>}

      <div className="flex flex-wrap gap-4">
        <Section className="flex-[1_1_300px]" titre="Envois récents">
          <ul className="m-0 flex max-h-[560px] list-none flex-col gap-2 overflow-y-auto p-0">
            {liste.map((c) => (
              <li key={c.id}>
                <button type="button" onClick={() => setParams({ chargement: String(c.id) })} aria-current={c.id === idChoisi}
                  className={`flex min-h-[44px] w-full flex-col gap-1 rounded-lg border px-3 py-2.5 text-left text-sm ${c.id === idChoisi ? "border-marine bg-fond" : "border-bordure hover:border-marine"}`}>
                  <span className="flex items-center justify-between gap-2">
                    <span className="font-semibold">#{c.id} · {c.source}</span>
                    <StatusBadge texte={c.attend_validation ? "à valider" : c.statut} ton={c.attend_validation ? "attention" : undefined} />
                  </span>
                  <span className="text-xs text-discret">{dateHeure(c.cree_le)} · {c.fichier_nom ?? c.declencheur} · {c.auteur}</span>
                </button>
              </li>
            ))}
            {liste.length === 0 && <li className="text-sm text-discret">Aucun envoi pour l'instant.</li>}
          </ul>
        </Section>

        <div className="flex min-w-0 flex-[3_1_520px] flex-col gap-4">
          {detail ? (
            <>
              <Section titre={`Envoi #${detail.id} — ${detail.source_nom}`}
                sousTitre={`${dateHeure(detail.cree_le)} · ${detail.declencheur} · par ${detail.auteur}${detail.fichier_nom ? ` · ${detail.fichier_nom}` : ""}`}
                action={<StatusBadge texte={detail.statut} />}>
                {detail.depot && (
                  <p className="m-0 text-sm">Dépôt de <strong>{detail.depot.direction}</strong> — {detail.depot.type_donnees}, période {detail.depot.periode}
                    {detail.depot.institution ? `, ${detail.depot.institution}` : ""}{detail.depot.commentaire ? ` — « ${detail.depot.commentaire} »` : ""}</p>
                )}
                <p className="m-0 text-sm text-discret">{detail.message}</p>
                <ol className="m-0 flex list-none flex-col gap-2 p-0">
                  {(detail.controles ?? []).map((k) => (
                    <li key={k.regle} className="flex flex-col gap-1.5 rounded-lg border border-bordure p-3 sm:flex-row sm:items-start sm:gap-3">
                      <span className="sm:w-28 sm:flex-none"><StatusBadge texte={k.resultat} /></span>
                      <span className="flex flex-col gap-0.5 text-sm"><strong>{k.regle}</strong><span className="text-discret">{k.detail}</span></span>
                    </li>
                  ))}
                  {(detail.controles ?? []).length === 0 && <li className="text-sm text-discret">Pas de contrôle (erreur avant réception des données).</li>}
                </ol>
                {detail.decision_par && (
                  <p className="m-0 text-sm">Décision de <strong>{detail.decision_par}</strong>{detail.decision_commentaire ? ` : « ${detail.decision_commentaire} »` : ""}</p>
                )}
                {detail.attend_validation && admin && (
                  <div className="flex flex-col gap-3 rounded-lg bg-fond p-4">
                    <label className="flex flex-col gap-1 text-xs font-semibold text-discret">
                      Commentaire (obligatoire pour renvoyer)
                      <textarea className="champ min-h-[80px] font-normal" value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Bouton onClick={() => decider("accepter")} disabled={occupe}>Accepter et charger {nombre(detail.nb_valeurs_en_attente ?? 0)} valeurs</Bouton>
                      <Bouton variante="danger" onClick={() => decider("renvoyer")} disabled={occupe || !commentaire.trim()}>Renvoyer avec commentaire</Bouton>
                    </div>
                  </div>
                )}
              </Section>
              {detail.apercu && detail.apercu.length > 0 && (
                <Section titre="Aperçu des valeurs en attente" sousTitre={`50 premières sur ${nombre(detail.nb_valeurs_en_attente ?? 0)}`}>
                  <div className="max-h-[360px] overflow-auto">
                    <table className="w-full border-collapse text-sm">
                      <thead><tr className="text-left text-xs uppercase text-discret">{colonnesApercu.map((c) => <th key={c} className="sticky top-0 border-b border-bordure bg-white px-2 py-2">{c}</th>)}</tr></thead>
                      <tbody>{detail.apercu.map((l, i) => (
                        <tr key={i} className="border-b border-fond">{colonnesApercu.map((c) => <td key={c} className="px-2 py-1.5">{String(l[c] ?? "")}</td>)}</tr>))}
                      </tbody>
                    </table>
                  </div>
                </Section>
              )}
            </>
          ) : <Section titre="Détail"><p className="m-0 text-sm text-discret">Choisissez un envoi.</p></Section>}
        </div>
      </div>
    </>
  );
}
