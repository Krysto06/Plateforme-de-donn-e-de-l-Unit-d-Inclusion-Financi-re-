"""Les 6 règles de contrôle qualité. Chacune rend « réussi », « alerte » ou « échec » avec un détail lisible.

Règles 1, 2, 3 et 6 : sur le fichier tel qu'il arrive (colonnes du modèle).
Règles 4 et 5 : sur les données normalisées (format standard), juste avant le chargement.
"""
import re
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from app.quality.modeles import Modele

REUSSI, ALERTE, ECHEC = "réussi", "alerte", "échec"

SEXES_PERMIS = {"F", "H", "Total"}
RE_GROUPE_AGE = re.compile(r"^(\d{1,3})(-\d{1,3}|\+)$")


@dataclass
class Resultat:
    regle: str
    resultat: str
    detail: str


@dataclass
class InfosIndicateur:
    unite: str
    additif: bool
    seuil_variation_pct: float


@dataclass
class Contexte:
    """Ce que les règles doivent savoir de la base : codes permis et caractéristiques des indicateurs."""

    pays: set[str]
    departements: set[str]
    indicateurs: dict[str, InfosIndicateur]
    # Fonction qui rend la valeur courante en base pour une clé normalisée à une année donnée (règle 5)
    valeur_en_base: Callable[[dict, int], float | None] = field(default=lambda cle, annee: None)


def _exemples(valeurs, n: int = 5) -> str:
    valeurs = list(dict.fromkeys(str(v) for v in valeurs))
    suite = f" (+{len(valeurs) - n} autres)" if len(valeurs) > n else ""
    return ", ".join(valeurs[:n]) + suite


def _phrase(texte: str) -> str:
    """Met une majuscule au début sans toucher au reste (codes, noms de pays)."""
    return texte[:1].upper() + texte[1:]


def _vide(serie: pd.Series) -> pd.Series:
    return serie.isna() | (serie.astype("string").str.strip() == "")


# ------------------------------------------------------------------ Règle 1


def regle_format(df: pd.DataFrame, modele: Modele, ctx: Contexte) -> Resultat:
    problemes: list[str] = []
    manquantes = [c for c in modele.noms_colonnes if c not in df.columns and c in modele.obligatoires]
    if manquantes:
        return Resultat("1. Format", ECHEC, f"Colonnes obligatoires absentes : {', '.join(manquantes)}. "
                        f"Colonnes attendues : {', '.join(modele.noms_colonnes)}.")
    inconnues = [c for c in df.columns if c not in modele.noms_colonnes]
    if inconnues:
        problemes.append(f"colonnes non prévues par le modèle : {', '.join(map(str, inconnues))}")

    for col in modele.colonnes:
        if col.nom not in df.columns:
            continue
        serie = df[col.nom][~_vide(df[col.nom])]
        if serie.empty:
            continue
        if col.type in ("entier", "nombre"):
            nums = pd.to_numeric(serie, errors="coerce")
            mauvais = serie[nums.isna()]
            if col.type == "entier":
                mauvais = pd.concat([mauvais, serie[nums.notna() & (nums % 1 != 0)]])
            if not mauvais.empty:
                problemes.append(f"« {col.nom} » doit être un {col.type} : {_exemples(mauvais)}")
                continue
        texte = serie.astype("string").str.strip()
        permis: set[str] | None = None
        if col.codes == "pays":
            permis = ctx.pays
        elif col.codes == "departement":
            permis = ctx.departements
        elif col.codes == "sexe":
            permis = SEXES_PERMIS
        elif col.codes == "indicateur":
            permis = set(modele.indicateurs_autorises) if modele.indicateurs_autorises else set(ctx.indicateurs)
        elif col.codes == "trimestre":
            permis = {"1", "2", "3", "4"}
            texte = pd.to_numeric(texte, errors="coerce").astype("Int64").astype("string")
        if permis is not None:
            hors = texte[~texte.isin(permis)]
            if not hors.empty:
                problemes.append(f"codes inconnus dans « {col.nom} » : {_exemples(hors)}")
        if col.codes == "groupe_age":
            hors = texte[~texte.str.match(RE_GROUPE_AGE)]
            if not hors.empty:
                problemes.append(f"tranches d'âge mal écrites (attendu 0-4, 80+) : {_exemples(hors)}")

    if "annee" in df.columns:
        annees = pd.to_numeric(df["annee"], errors="coerce").dropna()
        hors = annees[(annees < 1960) | (annees > pd.Timestamp.now().year + 1)]
        if not hors.empty:
            problemes.append(f"années invraisemblables : {_exemples(hors.astype(int))}")

    if not problemes:
        return Resultat("1. Format", REUSSI, "Colonnes, types et codes conformes au modèle "
                        f"« {modele.libelle} » ({modele.version}).")
    return Resultat("1. Format", ECHEC, _phrase(" ; ".join(problemes)) + ".")


# ------------------------------------------------------------------ Règle 2


SEUIL_ALERTE_VIDES = 0.10  # au-delà de 10 % de cellules vides dans une colonne obligatoire : échec


def regle_completude(df: pd.DataFrame, modele: Modele, ctx: Contexte) -> Resultat:
    if df.empty:
        return Resultat("2. Complétude", ECHEC, "Le fichier ne contient aucune ligne de données.")
    details, pire = [], 0.0
    for col in modele.obligatoires:
        if col not in df.columns:
            continue
        part = float(_vide(df[col]).mean())
        if part > 0:
            details.append(f"« {col} » : {part:.0%} de cellules vides")
            pire = max(pire, part)
    if pire == 0:
        return Resultat("2. Complétude", REUSSI, f"Aucune cellule vide dans les colonnes obligatoires ({len(df)} lignes).")
    if pire <= SEUIL_ALERTE_VIDES:
        return Resultat("2. Complétude", ALERTE, "; ".join(details) + ". Les lignes incomplètes seront ignorées.")
    return Resultat("2. Complétude", ECHEC, "; ".join(details) + f" (seuil : {SEUIL_ALERTE_VIDES:.0%}).")


# ------------------------------------------------------------------ Règle 3


def regle_doublons(df: pd.DataFrame, modele: Modele, ctx: Contexte) -> Resultat:
    cle = [c for c in modele.cle if c in df.columns]
    if df.empty or not cle:
        return Resultat("3. Doublons", REUSSI, "Rien à vérifier.")
    normalise = df[cle].astype("string").apply(lambda s: s.str.strip()).fillna("")
    doublons = normalise[normalise.duplicated(keep=False)]
    if doublons.empty:
        return Resultat("3. Doublons", REUSSI, f"Une seule ligne par clé ({', '.join(cle)}).")
    exemples = doublons.drop_duplicates().head(3).apply(lambda r: " / ".join(v for v in r if v), axis=1)
    return Resultat("3. Doublons", ECHEC, f"{len(doublons)} lignes en double sur la clé ({', '.join(cle)}). "
                    f"Exemples : {_exemples(exemples, 3)}.")


# ------------------------------------------------------------------ Règle 4

TOLERANCE_TOTAL = 0.005  # 0,5 % d'écart toléré entre F + H et Total (arrondis)


def regle_coherence(std: pd.DataFrame, ctx: Contexte) -> Resultat:
    if std.empty:
        return Resultat("4. Cohérence", REUSSI, "Rien à vérifier.")
    problemes: list[str] = []

    pct = std[std["indicateur"].map(lambda c: ctx.indicateurs.get(c) and ctx.indicateurs[c].unite.strip() == "%")
              .fillna(False).astype(bool)]
    hors = pct[(pct["valeur"] < 0) | (pct["valeur"] > 100)]
    if not hors.empty:
        problemes.append("pourcentages hors de 0–100 : " + _exemples(
            hors.apply(lambda r: f"{r['indicateur']} {r['pays']} {r['annee']} = {r['valeur']}", axis=1)))

    additifs = std[std["indicateur"].map(lambda c: bool(ctx.indicateurs.get(c) and ctx.indicateurs[c].additif))]
    if not additifs.empty:
        cle = ["indicateur", "pays", "departement", "annee", "trimestre", "institution"]
        tableau = additifs.pivot_table(index=cle, columns="sexe", values="valeur", aggfunc="first", dropna=False)
        if {"F", "H", "Total"} <= set(tableau.columns):
            complet = tableau.dropna(subset=["F", "H", "Total"])
            ecart = (complet["F"] + complet["H"] - complet["Total"]).abs()
            faux = complet[ecart > TOLERANCE_TOTAL * complet["Total"].abs().clip(lower=1)]
            if not faux.empty:
                exemples = [f"{i[0]} {i[1]} {i[2] or ''} {i[3]} : F+H={r['F'] + r['H']:g} ≠ Total={r['Total']:g}"
                            for i, r in faux.head(3).iterrows()]
                problemes.append(f"{len(faux)} cas où femmes + hommes ≠ total ({'; '.join(exemples)})")

    if not problemes:
        return Resultat("4. Cohérence", REUSSI, "Totaux et pourcentages cohérents.")
    return Resultat("4. Cohérence", ECHEC, _phrase(" ; ".join(problemes)) + ".")


# ------------------------------------------------------------------ Règle 5


def regle_variation(std: pd.DataFrame, ctx: Contexte) -> Resultat:
    """Compare chaque valeur nouvelle ou modifiée à celle de l'année précédente (même clé), dans l'envoi ou en base.

    Une valeur identique à celle déjà en base a déjà été contrôlée : elle n'est pas réexaminée.
    """
    if std.empty:
        return Resultat("5. Variation inhabituelle", REUSSI, "Rien à vérifier.")
    cle_cols = ["indicateur", "pays", "departement", "sexe", "trimestre", "institution", "source"]
    index = {tuple(r[c] for c in cle_cols) + (int(r["annee"]),): float(r["valeur"]) for _, r in std.iterrows()}
    cas = []
    for _, r in std.iterrows():
        infos = ctx.indicateurs.get(r["indicateur"])
        if infos is None:
            continue
        cle = tuple(r[c] for c in cle_cols)
        cle_dict = dict(zip(cle_cols, cle))
        annee = int(r["annee"])
        deja = ctx.valeur_en_base(cle_dict, annee)
        if deja is not None and abs(deja - float(r["valeur"])) <= 1e-9 * max(1.0, abs(deja)):
            continue
        precedente = index.get(cle + (annee - 1,))
        if precedente is None:
            precedente = ctx.valeur_en_base(cle_dict, annee - 1)
        if precedente is None or precedente == 0:
            continue
        variation = (float(r["valeur"]) - precedente) / abs(precedente) * 100
        if abs(variation) > infos.seuil_variation_pct:
            cas.append(f"{r['indicateur']} {r['pays']}{' ' + r['departement'] if r['departement'] else ''}"
                       f"{'' if r['sexe'] == 'Total' else ' ' + r['sexe']} {annee - 1}→{annee} : "
                       f"{precedente:g} → {float(r['valeur']):g} ({variation:+.0f} %, seuil ±{infos.seuil_variation_pct:g} %)")
    if not cas:
        return Resultat("5. Variation inhabituelle", REUSSI, "Aucune variation au-delà des seuils.")
    return Resultat("5. Variation inhabituelle", ALERTE,
                    f"{len(cas)} variation(s) au-delà du seuil, à confirmer : " + " ; ".join(cas[:8])
                    + (f" ; … (+{len(cas) - 8})" if len(cas) > 8 else "") + ".")


# ------------------------------------------------------------------ Règle 6

RE_COLONNE_NOMINATIVE = re.compile(
    r"(^|[_\s-])(nom|noms|prenom|prénom|name|first|last|nif|cin|ninu|passeport|compte|account|iban|"
    r"telephone|téléphone|tel|phone|adresse|address|email|courriel|client|naissance|birth)([_\s-]|$)",
    re.IGNORECASE,
)
RE_VALEURS_NOMINATIVES = {
    "un NIF (000-000-000-0)": re.compile(r"\b\d{3}-\d{3}-\d{3}-\d\b"),
    "un numéro de compte ou d'identité (9 chiffres ou plus)": re.compile(r"\b\d{9,}\b"),
    "une adresse électronique": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "un numéro de téléphone": re.compile(r"\+?509[\s-]?\d{4}[\s-]?\d{4}"),
}


def regle_nominatif(df: pd.DataFrame, modele: Modele, ctx: Contexte) -> Resultat:
    problemes = [f"la colonne « {c} » ressemble à une donnée personnelle"
                 for c in df.columns if RE_COLONNE_NOMINATIVE.search(str(c))]
    # Les colonnes de mesure (valeur, population) contiennent légitimement de grands nombres
    colonnes_mesure = {c.nom for c in modele.colonnes if c.type in ("nombre", "entier")}
    for col in df.columns:
        if col in colonnes_mesure:
            continue
        texte = df[col].dropna().astype("string")
        for libelle, motif in RE_VALEURS_NOMINATIVES.items():
            touches = texte[texte.str.contains(motif, regex=True)]
            if not touches.empty:
                problemes.append(f"« {col} » contient {len(touches)} valeur(s) qui ressemblent à {libelle}")
    if not problemes:
        return Resultat("6. Données nominatives", REUSSI, "Aucune colonne ni valeur d'apparence nominative.")
    return Resultat("6. Données nominatives", ECHEC, "Fichier refusé : " + " ; ".join(problemes)
                    + ". La PDIF n'accepte que des données agrégées.")
