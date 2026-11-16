"""Fabrication des modèles Excel de transmission (un par type de données, versionné)."""
import io
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Departement, Indicateur
from app.quality.modeles import IHSI_POPULATION, MODELES_DEPOT, Modele

DOSSIER_TEMPLATES = Path(__file__).resolve().parents[3] / "templates"
MARINE = "1A365D"


def nom_fichier(modele: Modele) -> str:
    return f"{modele.code}_{modele.version}.xlsx"


def generer(modele: Modele, session: Session) -> bytes:
    wb = Workbook()
    donnees = wb.active
    donnees.title = "Données"
    donnees.append(modele.noms_colonnes)
    for cellule in donnees[1]:
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = PatternFill("solid", fgColor=MARINE)
    for i, _ in enumerate(modele.colonnes, start=1):
        donnees.column_dimensions[chr(64 + i)].width = 18

    aide = wb.create_sheet("Instructions")
    aide.append([f"PDIF — modèle « {modele.libelle} » ({modele.code}, {modele.version})"])
    aide["A1"].font = Font(bold=True, size=13, color=MARINE)
    aide.append(["Remplir l'onglet « Données » à partir de la ligne 2, sans changer les en-têtes."])
    aide.append(["DONNÉES AGRÉGÉES UNIQUEMENT : aucun nom, NIF, numéro de compte ou téléphone de client."])
    aide.append([])
    aide.append(["Colonne", "Obligatoire", "Type", "Aide"])
    for c in modele.colonnes:
        aide.append([c.nom, "oui" if c.obligatoire else "non", c.type, c.aide])
    aide.column_dimensions["A"].width = 18
    aide.column_dimensions["D"].width = 60

    codes = wb.create_sheet("Codes")
    codes.append(["Département (code)", "Nom", "", "Sexe", "", "Indicateur (code)", "Libellé"])
    deps = list(session.scalars(select(Departement).order_by(Departement.code)))
    inds = list(session.scalars(select(Indicateur).where(Indicateur.code.in_(modele.indicateurs_autorises))
                                .order_by(Indicateur.ordre))) if modele.indicateurs_autorises else []
    sexes = ["F", "H", "Total"]
    for i in range(max(len(deps), len(inds), len(sexes))):
        codes.append([
            deps[i].code if i < len(deps) else None, deps[i].nom if i < len(deps) else None, None,
            sexes[i] if i < len(sexes) else None, None,
            inds[i].code if i < len(inds) else None, inds[i].libelle if i < len(inds) else None,
        ])
    codes.column_dimensions["B"].width = 16
    codes.column_dimensions["G"].width = 55

    flux = io.BytesIO()
    wb.save(flux)
    return flux.getvalue()


def ecrire_tous(session: Session) -> list[Path]:
    DOSSIER_TEMPLATES.mkdir(exist_ok=True)
    chemins = []
    for modele in [IHSI_POPULATION, *MODELES_DEPOT.values()]:
        chemin = DOSSIER_TEMPLATES / nom_fichier(modele)
        chemin.write_bytes(generer(modele, session))
        chemins.append(chemin)
    return chemins
