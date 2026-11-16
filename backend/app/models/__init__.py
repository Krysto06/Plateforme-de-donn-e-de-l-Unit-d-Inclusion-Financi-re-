"""Tables de la PDIF. Le détail de chaque table et variable est dans docs/dictionnaire.md."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def maintenant() -> datetime:
    return datetime.now(timezone.utc)


# Valeurs permises (gardées en texte pour rester lisibles dans la base)
SEXES = ("F", "H", "Total")
STATUTS_CHARGEMENT = ("reçu", "en contrôle", "accepté", "rejeté", "chargé", "erreur")
RESULTATS_CONTROLE = ("réussi", "alerte", "échec")
ROLES = ("admin_uif", "cadre_uif", "point_focal")


# ---------------------------------------------------------------- Référentiels


class Pays(Base):
    __tablename__ = "pays"
    id: Mapped[int] = mapped_column(primary_key=True)
    code_iso3: Mapped[str] = mapped_column(String(3), unique=True)
    nom: Mapped[str] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))


class Departement(Base):
    __tablename__ = "departement"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)  # ISO 3166-2:HT, ex. HT-OU
    nom: Mapped[str] = mapped_column(String(80))


class Periode(Base):
    __tablename__ = "periode"
    __table_args__ = (UniqueConstraint("annee", "trimestre", name="uq_periode"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    annee: Mapped[int] = mapped_column(Integer)
    trimestre: Mapped[int | None] = mapped_column(Integer)  # 1 à 4, vide si annuelle
    type: Mapped[str] = mapped_column(String(15))  # annuelle | trimestrielle

    @property
    def libelle(self) -> str:
        return f"{self.annee}" if self.trimestre is None else f"{self.annee}-T{self.trimestre}"


class Direction(Base):
    __tablename__ = "direction"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    nom: Mapped[str] = mapped_column(String(200))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class TypeInstitution(Base):
    __tablename__ = "type_institution"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    libelle: Mapped[str] = mapped_column(String(120))


class Institution(Base):
    __tablename__ = "institution"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), unique=True)
    type_institution_id: Mapped[int] = mapped_column(ForeignKey("type_institution.id"))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    type_institution: Mapped[TypeInstitution] = relationship()


class Source(Base):
    __tablename__ = "source"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # WB, FMI, IHSI, UIF, DIR-xxx
    nom: Mapped[str] = mapped_column(String(200))
    mode: Mapped[str] = mapped_column(String(20))  # api | fichier | formulaire | depot
    url: Mapped[str | None] = mapped_column(String(300))
    calendrier_cron: Mapped[str | None] = mapped_column(String(50))  # ex. "0 3 1 * *" = le 1er du mois à 3 h
    delai_alerte_jours: Mapped[int | None] = mapped_column(Integer)  # au-delà : « en retard »
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class Indicateur(Base):
    """Référentiel des KPI : une ligne par indicateur, modifiable sans toucher au code."""

    __tablename__ = "indicateur"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    libelle: Mapped[str] = mapped_column(String(250))
    dimension: Mapped[str] = mapped_column(String(60))  # Accès, Usage, Profondeur, Genre, MPME, ...
    unite: Mapped[str] = mapped_column(String(60))  # « pour 100 000 adultes », « % », « nombre », ...
    formule: Mapped[str | None] = mapped_column(Text)  # définition lisible
    calcul: Mapped[str | None] = mapped_column(String(250))  # ex. « USA-04[H] - USA-04[F] » (KPI calculés)
    source_attendue: Mapped[str | None] = mapped_column(String(200))
    source_preferee: Mapped[str | None] = mapped_column(String(20))  # code de la source affichée en premier
    frequence: Mapped[str] = mapped_column(String(30), default="annuelle")
    phase: Mapped[int] = mapped_column(Integer, default=1)
    est_kpi: Mapped[bool] = mapped_column(Boolean, default=True)  # False = série auxiliaire (ex. population)
    additif: Mapped[bool] = mapped_column(Boolean, default=False)  # True si F + H = Total doit tenir
    seuil_variation_pct: Mapped[float] = mapped_column(Float, default=50.0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    ordre: Mapped[int] = mapped_column(Integer, default=0)

    series: Mapped[list["SerieSource"]] = relationship(back_populates="indicateur", cascade="all, delete-orphan")


class SerieSource(Base):
    """Correspondance entre un indicateur et le code de la série chez une source (vérifié, voir docs/sources.md)."""

    __tablename__ = "serie_source"
    __table_args__ = (UniqueConstraint("source_id", "code_serie", name="uq_serie_source"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    indicateur_id: Mapped[int] = mapped_column(ForeignKey("indicateur.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    code_serie: Mapped[str] = mapped_column(String(120))
    sexe: Mapped[str] = mapped_column(String(5), default="Total")
    verifie_le: Mapped[str | None] = mapped_column(String(10))  # date de vérification par l'API
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    indicateur: Mapped[Indicateur] = relationship(back_populates="series")
    source: Mapped[Source] = relationship()


# ----------------------------------------------------------- Faits et suivi


class Chargement(Base):
    __tablename__ = "chargement"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
    termine_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declencheur: Mapped[str] = mapped_column(String(15))  # automatique | manuel
    auteur: Mapped[str] = mapped_column(String(120))
    fichier_nom: Mapped[str | None] = mapped_column(String(250))
    nb_lignes: Mapped[int] = mapped_column(Integer, default=0)
    nb_nouvelles: Mapped[int] = mapped_column(Integer, default=0)
    nb_modifiees: Mapped[int] = mapped_column(Integer, default=0)
    nb_inchangees: Mapped[int] = mapped_column(Integer, default=0)
    statut: Mapped[str] = mapped_column(String(15), default="reçu")
    message: Mapped[str | None] = mapped_column(Text)
    # Lignes normalisées en attente de validation (JSON). Données agrégées uniquement.
    donnees_json: Mapped[str | None] = mapped_column(Text)
    decision_par: Mapped[str | None] = mapped_column(String(120))
    decision_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_commentaire: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()
    controles: Mapped[list["Controle"]] = relationship(back_populates="chargement", cascade="all, delete-orphan")


class Controle(Base):
    __tablename__ = "controle"
    id: Mapped[int] = mapped_column(primary_key=True)
    chargement_id: Mapped[int] = mapped_column(ForeignKey("chargement.id"))
    regle: Mapped[str] = mapped_column(String(40))
    resultat: Mapped[str] = mapped_column(String(10))
    detail: Mapped[str | None] = mapped_column(Text)
    chargement: Mapped[Chargement] = relationship(back_populates="controles")


class Observation(Base):
    """Une valeur publiée. Jamais écrasée : une nouvelle valeur crée une nouvelle version."""

    __tablename__ = "observation"
    __table_args__ = (UniqueConstraint("cle", "version", name="uq_observation_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    cle: Mapped[str] = mapped_column(String(200), index=True)  # indicateur|pays|dep|sexe|période|institution|source
    version: Mapped[int] = mapped_column(Integer, default=1)
    est_courante: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    indicateur_id: Mapped[int] = mapped_column(ForeignKey("indicateur.id"), index=True)
    pays_id: Mapped[int] = mapped_column(ForeignKey("pays.id"))
    departement_id: Mapped[int | None] = mapped_column(ForeignKey("departement.id"))
    sexe: Mapped[str] = mapped_column(String(5), default="Total")
    periode_id: Mapped[int] = mapped_column(ForeignKey("periode.id"))
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institution.id"))
    valeur: Mapped[float] = mapped_column(Float)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    chargement_id: Mapped[int] = mapped_column(ForeignKey("chargement.id"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)

    indicateur: Mapped[Indicateur] = relationship()
    pays: Mapped[Pays] = relationship()
    departement: Mapped[Departement | None] = relationship()
    periode: Mapped[Periode] = relationship()
    institution: Mapped[Institution | None] = relationship()
    source: Mapped[Source] = relationship()


class Depot(Base):
    __tablename__ = "depot"
    id: Mapped[int] = mapped_column(primary_key=True)
    direction_id: Mapped[int] = mapped_column(ForeignKey("direction.id"))
    type_institution_id: Mapped[int] = mapped_column(ForeignKey("type_institution.id"))
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institution.id"))
    type_donnees: Mapped[str] = mapped_column(String(50))
    version_modele: Mapped[str] = mapped_column(String(10))
    periode: Mapped[str] = mapped_column(String(10))  # 2025 ou 2025-T3
    fichier_nom: Mapped[str] = mapped_column(String(250))
    commentaire: Mapped[str | None] = mapped_column(Text)
    certifie_agrege: Mapped[bool] = mapped_column(Boolean, default=False)
    statut: Mapped[str] = mapped_column(String(15), default="reçu")
    auteur: Mapped[str] = mapped_column(String(120))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
    chargement_id: Mapped[int | None] = mapped_column(ForeignKey("chargement.id"))

    direction: Mapped[Direction] = relationship()
    type_institution: Mapped[TypeInstitution] = relationship()
    institution: Mapped[Institution | None] = relationship()
    chargement: Mapped[Chargement | None] = relationship()


class Role(Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    libelle: Mapped[str] = mapped_column(String(80))


class Utilisateur(Base):
    __tablename__ = "utilisateur"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifiant: Mapped[str] = mapped_column(String(120), unique=True)
    nom: Mapped[str] = mapped_column(String(200))
    mot_de_passe_hash: Mapped[str] = mapped_column(String(300))
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    direction_id: Mapped[int | None] = mapped_column(ForeignKey("direction.id"))  # pour un point focal
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)

    role: Mapped[Role] = relationship()
    direction: Mapped[Direction | None] = relationship()


class Journal(Base):
    __tablename__ = "journal"
    id: Mapped[int] = mapped_column(primary_key=True)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant, index=True)
    utilisateur: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(60))
    objet: Mapped[str | None] = mapped_column(String(120))
    detail: Mapped[str | None] = mapped_column(Text)
