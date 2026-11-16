"""Modèles de données attendus (colonnes, types, codes) pour chaque type d'envoi.

Un « modèle » décrit un fichier : ses colonnes, si elles sont obligatoires, leur type et la liste de codes
permise. Les contrôles qualité (règles 1, 2, 3 et 6) s'appuient sur ces descriptions.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Colonne:
    nom: str
    type: str  # texte | entier | nombre
    obligatoire: bool = True
    codes: str | None = None  # pays | departement | sexe | indicateur | trimestre | groupe_age
    aide: str = ""


@dataclass(frozen=True)
class Modele:
    code: str
    libelle: str
    version: str
    colonnes: tuple[Colonne, ...]
    cle: tuple[str, ...]  # colonnes qui identifient une ligne (règle 3)
    indicateurs_autorises: tuple[str, ...] = field(default_factory=tuple)  # vide = tous

    @property
    def noms_colonnes(self) -> list[str]:
        return [c.nom for c in self.colonnes]

    @property
    def obligatoires(self) -> list[str]:
        return [c.nom for c in self.colonnes if c.obligatoire]


# Format normalisé interne : toutes les sources y sont ramenées avant chargement.
STANDARD = Modele(
    code="standard",
    libelle="Format normalisé de la PDIF",
    version="v1",
    colonnes=(
        Colonne("indicateur", "texte", codes="indicateur"),
        Colonne("pays", "texte", codes="pays"),
        Colonne("departement", "texte", obligatoire=False, codes="departement"),
        Colonne("sexe", "texte", codes="sexe"),
        Colonne("annee", "entier"),
        Colonne("trimestre", "entier", obligatoire=False, codes="trimestre"),
        Colonne("institution", "texte", obligatoire=False),
        Colonne("valeur", "nombre"),
    ),
    cle=("indicateur", "pays", "departement", "sexe", "annee", "trimestre", "institution"),
)

IHSI_POPULATION = Modele(
    code="ihsi_population",
    libelle="IHSI — Population par département, sexe et âge",
    version="v1",
    colonnes=(
        Colonne("departement", "texte", codes="departement", aide="Code ISO du département, ex. HT-OU"),
        Colonne("sexe", "texte", codes="sexe", aide="F, H ou Total"),
        Colonne("groupe_age", "texte", codes="groupe_age", aide="Tranche d'âge, ex. 0-4, 15-19, 80+"),
        Colonne("annee", "entier", aide="Année de référence, ex. 2024"),
        Colonne("population", "nombre", aide="Effectif"),
    ),
    cle=("departement", "sexe", "groupe_age", "annee"),
)


def _modele_depot(code: str, libelle: str, indicateurs: tuple[str, ...]) -> Modele:
    return Modele(
        code=code,
        libelle=libelle,
        version="v1",
        colonnes=(
            Colonne("indicateur", "texte", codes="indicateur", aide="Code du KPI, voir l'onglet Codes"),
            Colonne("departement", "texte", obligatoire=False, codes="departement", aide="Vide = tout le pays"),
            Colonne("sexe", "texte", codes="sexe", aide="F, H ou Total"),
            Colonne("annee", "entier", aide="Année, ex. 2025"),
            Colonne("trimestre", "entier", obligatoire=False, codes="trimestre", aide="1 à 4, vide si annuel"),
            Colonne("valeur", "nombre", aide="Valeur agrégée (jamais de donnée de client)"),
        ),
        cle=("indicateur", "departement", "sexe", "annee", "trimestre"),
        indicateurs_autorises=indicateurs,
    )


# Types de données que les directions peuvent déposer (phase 2). Un modèle Excel par type, versionné.
MODELES_DEPOT: dict[str, Modele] = {
    m.code: m
    for m in (
        _modele_depot("acces_usage", "Accès et usage (agrégats par département)", ("ACC-04", "USA-01", "USA-02")),
        _modele_depot("plaintes", "Plaintes des consommateurs", ("CON-01",)),
        _modele_depot("credit_vert", "Crédit vert", ("VER-01",)),
        _modele_depot("garanties_mpme", "Crédits garantis aux MPME", ("MPM-02",)),
        _modele_depot("education_financiere", "Éducation financière (UIF)", ("EF-01", "EF-02")),
    )
}

TOUS_LES_MODELES: dict[str, Modele] = {STANDARD.code: STANDARD, IHSI_POPULATION.code: IHSI_POPULATION, **MODELES_DEPOT}
