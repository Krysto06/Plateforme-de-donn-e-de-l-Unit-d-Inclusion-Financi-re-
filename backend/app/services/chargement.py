"""Circuit de chargement commun à toutes les sources.

    envoi reçu → contrôles qualité → (échec : rejeté) | (alerte : en attente de validation) | (tout réussi : chargé)

Un chargement garde la trace de tout : source, date, déclencheur, auteur, résultats des contrôles, décision.
Les valeurs ne sont jamais écrasées : une nouvelle valeur pour une même clé devient une nouvelle version.
"""
import json
from collections.abc import Callable
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Chargement,
    Controle,
    Departement,
    Indicateur,
    Institution,
    Observation,
    Pays,
    Periode,
    Source,
)
from app.quality import regles
from app.quality.modeles import Modele
from app.services import calculs
from app.services.journal import tracer

COLONNES_STD = ["indicateur", "pays", "departement", "sexe", "annee", "trimestre", "institution", "valeur", "source"]
TOLERANCE_IDENTIQUE = 1e-9


def maintenant() -> datetime:
    return datetime.now(timezone.utc)


def frame_standard(lignes: list[dict] | pd.DataFrame) -> pd.DataFrame:
    """Met des données au format normalisé : valeurs vides remplacées par "" (texte) ou 0 (trimestre)."""
    df = pd.DataFrame(lignes).copy()
    for col in COLONNES_STD:
        if col not in df.columns:
            df[col] = None
    df = df[COLONNES_STD]
    for col in ("indicateur", "pays", "departement", "sexe", "institution", "source"):
        df[col] = df[col].astype("object").where(df[col].notna(), "").map(lambda v: str(v).strip())
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
    df["trimestre"] = pd.to_numeric(df["trimestre"], errors="coerce").fillna(0).astype(int)
    df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce")
    df = df.dropna(subset=["annee", "valeur"])
    df["annee"] = df["annee"].astype(int)
    return df.reset_index(drop=True)


def cle_observation(indicateur: str, pays: str, departement: str, sexe: str, annee: int, trimestre: int,
                    institution: str, source: str) -> str:
    periode = f"{annee}" if not trimestre else f"{annee}-T{trimestre}"
    return "|".join([indicateur, pays, departement or "-", sexe, periode, institution or "-", source])


# ------------------------------------------------------------------ Contexte des contrôles


def construire_contexte(session: Session) -> regles.Contexte:
    indicateurs = {
        i.code: regles.InfosIndicateur(i.unite, i.additif, i.seuil_variation_pct)
        for i in session.scalars(select(Indicateur).where(Indicateur.actif))
    }

    def valeur_en_base(cle: dict, annee: int) -> float | None:
        texte = cle_observation(cle["indicateur"], cle["pays"], cle["departement"], cle["sexe"], annee,
                                cle["trimestre"], cle["institution"], cle["source"])
        return session.scalar(select(Observation.valeur).where(Observation.cle == texte, Observation.est_courante))

    return regles.Contexte(
        pays=set(session.scalars(select(Pays.code_iso3))),
        departements=set(session.scalars(select(Departement.code))),
        indicateurs=indicateurs,
        valeur_en_base=valeur_en_base,
    )


def controler(df_brut: pd.DataFrame, modele: Modele, normaliser: Callable[[pd.DataFrame], pd.DataFrame],
              ctx: regles.Contexte) -> tuple[list[regles.Resultat], pd.DataFrame | None]:
    """Applique les 6 règles. Rend les résultats et les données normalisées (None si le fichier est inutilisable)."""
    resultats = [
        regles.regle_nominatif(df_brut, modele, ctx),
        regles.regle_format(df_brut, modele, ctx),
        regles.regle_completude(df_brut, modele, ctx),
        regles.regle_doublons(df_brut, modele, ctx),
    ]
    if any(r.resultat == regles.ECHEC for r in resultats[:2]):
        return resultats, None  # fichier nominatif ou mal formé : on ne va pas plus loin
    std = frame_standard(normaliser(df_brut))
    resultats.append(regles.regle_coherence(std, ctx))
    resultats.append(regles.regle_variation(std, ctx))
    return resultats, std


# ------------------------------------------------------------------ Circuit


def traiter_envoi(
    session: Session,
    *,
    source_code: str,
    df_brut: pd.DataFrame,
    modele: Modele,
    normaliser: Callable[[pd.DataFrame], pd.DataFrame],
    declencheur: str,
    auteur: str,
    fichier_nom: str | None = None,
    chargement: Chargement | None = None,
) -> Chargement:
    source = session.scalar(select(Source).where(Source.code == source_code))
    if source is None:
        raise ValueError(f"Source inconnue : {source_code}")
    if chargement is None:
        chargement = Chargement(source=source, declencheur=declencheur, auteur=auteur, fichier_nom=fichier_nom)
        session.add(chargement)
    chargement.statut = "en contrôle"
    chargement.nb_lignes = len(df_brut)
    session.flush()

    resultats, std = controler(df_brut, modele, normaliser, construire_contexte(session))
    for r in resultats:
        chargement.controles.append(Controle(regle=r.regle, resultat=r.resultat, detail=r.detail))

    echecs = [r for r in resultats if r.resultat == regles.ECHEC]
    alertes = [r for r in resultats if r.resultat == regles.ALERTE]
    if echecs:
        chargement.statut = "rejeté"
        chargement.message = f"Rejeté par les contrôles : {', '.join(r.regle for r in echecs)}."
        chargement.termine_le = maintenant()
    elif alertes:
        chargement.statut = "en contrôle"
        chargement.donnees_json = std.to_json(orient="records", force_ascii=False)
        chargement.message = (f"{len(std)} valeurs en attente de validation humaine "
                              f"({', '.join(r.regle for r in alertes)}).")
    else:
        chargement.statut = "accepté"
        _charger(session, chargement, std)
    tracer(session, auteur, "chargement", f"chargement #{chargement.id}",
           f"{source_code} — {chargement.statut} — {chargement.message or ''}")
    session.commit()
    return chargement


def decider(session: Session, chargement: Chargement, decision: str, commentaire: str | None, auteur: str) -> Chargement:
    """Validation humaine d'un envoi en alerte : « accepter » charge les données, « renvoyer » les rejette."""
    if chargement.statut != "en contrôle" or not chargement.donnees_json:
        raise ValueError("Ce chargement n'attend pas de validation.")
    if decision == "renvoyer" and not (commentaire or "").strip():
        raise ValueError("Un commentaire est obligatoire pour renvoyer un envoi.")
    chargement.decision_par = auteur
    chargement.decision_le = maintenant()
    chargement.decision_commentaire = commentaire
    if decision == "accepter":
        chargement.statut = "accepté"
        std = frame_standard(pd.DataFrame(json.loads(chargement.donnees_json)))
        _charger(session, chargement, std)
    elif decision == "renvoyer":
        chargement.statut = "rejeté"
        chargement.message = f"Renvoyé par {auteur} : {commentaire}"
        chargement.termine_le = maintenant()
    else:
        raise ValueError("Décision attendue : accepter ou renvoyer.")
    tracer(session, auteur, f"validation:{decision}", f"chargement #{chargement.id}", commentaire)
    session.commit()
    return chargement


# ------------------------------------------------------------------ Écriture des observations


class _Resolveur:
    """Trouve (ou crée pour les périodes) les identifiants à partir des codes, avec un petit cache."""

    def __init__(self, session: Session):
        self.s = session
        self.indicateurs = {i.code: i.id for i in session.scalars(select(Indicateur))}
        self.pays = {p.code_iso3: p.id for p in session.scalars(select(Pays))}
        self.departements = {d.code: d.id for d in session.scalars(select(Departement))}
        self.institutions = {i.nom: i.id for i in session.scalars(select(Institution))}
        self.sources = {s.code: s.id for s in session.scalars(select(Source))}
        self.periodes = {(p.annee, p.trimestre or 0): p.id for p in session.scalars(select(Periode))}

    def periode(self, annee: int, trimestre: int) -> int:
        cle = (annee, trimestre)
        if cle not in self.periodes:
            p = Periode(annee=annee, trimestre=trimestre or None, type="trimestrielle" if trimestre else "annuelle")
            self.s.add(p)
            self.s.flush()
            self.periodes[cle] = p.id
        return self.periodes[cle]


def _ecrire(session: Session, res: _Resolveur, chargement: Chargement, r: dict, compteurs: dict) -> None:
    cle = cle_observation(r["indicateur"], r["pays"], r["departement"], r["sexe"], int(r["annee"]),
                          int(r["trimestre"]), r["institution"], r["source"])
    courante = session.scalar(select(Observation).where(Observation.cle == cle, Observation.est_courante))
    valeur = float(r["valeur"])
    if courante is not None and abs(courante.valeur - valeur) <= TOLERANCE_IDENTIQUE * max(1.0, abs(valeur)):
        compteurs["inchangees"] += 1
        return
    version = 1
    if courante is not None:
        courante.est_courante = False  # l'ancienne valeur reste en base, simplement plus « courante »
        version = courante.version + 1
        compteurs["modifiees"] += 1
    else:
        compteurs["nouvelles"] += 1
    session.add(Observation(
        cle=cle, version=version, est_courante=True,
        indicateur_id=res.indicateurs[r["indicateur"]],
        pays_id=res.pays[r["pays"]],
        departement_id=res.departements.get(r["departement"]) if r["departement"] else None,
        sexe=r["sexe"],
        periode_id=res.periode(int(r["annee"]), int(r["trimestre"])),
        institution_id=res.institutions.get(r["institution"]) if r["institution"] else None,
        valeur=valeur,
        source_id=res.sources[r["source"]],
        chargement_id=chargement.id,
    ))
    session.flush()


def _charger(session: Session, chargement: Chargement, std: pd.DataFrame) -> None:
    res = _Resolveur(session)
    compteurs = {"nouvelles": 0, "modifiees": 0, "inchangees": 0}
    for r in std.to_dict(orient="records"):
        _ecrire(session, res, chargement, r, compteurs)
    derives = _calculer_derives(session, res, chargement, set(std["source"]) if not std.empty else set(), compteurs)
    chargement.nb_nouvelles = compteurs["nouvelles"]
    chargement.nb_modifiees = compteurs["modifiees"]
    chargement.nb_inchangees = compteurs["inchangees"]
    chargement.statut = "chargé"
    chargement.termine_le = maintenant()
    chargement.donnees_json = None
    chargement.message = (f"{len(std)} valeurs reçues : {compteurs['nouvelles']} nouvelles, "
                          f"{compteurs['modifiees']} modifiées (ancienne version conservée), "
                          f"{compteurs['inchangees']} inchangées" + (f" ; {derives} KPI calculés mis à jour" if derives else "") + ".")


def _calculer_derives(session: Session, res: _Resolveur, chargement: Chargement, sources: set[str],
                      compteurs: dict) -> int:
    """Recalcule les KPI définis par une formule (colonne « calcul ») pour les sources concernées."""
    nb = 0
    for ind in session.scalars(select(Indicateur).where(Indicateur.actif, Indicateur.calcul.is_not(None))):
        if not ind.calcul:
            continue
        refs = calculs.references(ind.calcul)
        codes = {c for c, _ in refs}
        ids = [res.indicateurs[c] for c in codes if c in res.indicateurs]
        lignes = session.execute(
            select(Observation, Indicateur.code, Source.code, Pays.code_iso3, Periode.annee, Periode.trimestre)
            .join(Indicateur, Observation.indicateur_id == Indicateur.id)
            .join(Source, Observation.source_id == Source.id)
            .join(Pays, Observation.pays_id == Pays.id)
            .join(Periode, Observation.periode_id == Periode.id)
            .where(Observation.est_courante, Observation.indicateur_id.in_(ids), Source.code.in_(sources))
        ).all()
        groupes: dict[tuple, dict] = {}
        for obs, code_ind, code_src, pays, annee, trimestre in lignes:
            dep = next((c for c, i in res.departements.items() if i == obs.departement_id), "")
            inst = next((n for n, i in res.institutions.items() if i == obs.institution_id), "")
            groupes.setdefault((pays, dep, annee, trimestre or 0, inst, code_src), {})[(code_ind, obs.sexe)] = obs.valeur
        for (pays, dep, annee, trimestre, inst, src), valeurs in groupes.items():
            valeur = calculs.evaluer(ind.calcul, valeurs)
            if valeur is None:
                continue
            avant = dict(compteurs)
            _ecrire(session, res, chargement, {
                "indicateur": ind.code, "pays": pays, "departement": dep, "sexe": "Total", "annee": annee,
                "trimestre": trimestre, "institution": inst, "valeur": round(valeur, 10), "source": src,
            }, compteurs)
            if compteurs != avant and compteurs["inchangees"] == avant["inchangees"]:
                nb += 1
            # Les valeurs calculées ne comptent pas dans les compteurs de l'envoi
            compteurs.update(avant)
    return nb
