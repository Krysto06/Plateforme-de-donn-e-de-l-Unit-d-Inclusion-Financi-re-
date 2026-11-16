"""Commandes d'exploitation.  Lancer depuis le dossier backend :

    python -m app.cli init                       # référentiels + modèles Excel (après « alembic upgrade head »)
    python -m app.cli init --forcer              # réapplique les fichiers CSV de app/data (écrase les modifications)
    python -m app.cli creer-utilisateur IDENTIFIANT "Nom" admin_uif   # demande le mot de passe
    python -m app.cli maj WB                     # mise à jour Banque mondiale (ou FMI)
    python -m app.cli importer-ihsi fichier.xlsx
    python -m app.cli chargements                # derniers chargements et leur statut
"""
import argparse
import getpass
import sys
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.cli", description="Commandes de la PDIF")
    sous = p.add_subparsers(dest="commande", required=True)
    i = sous.add_parser("init", help="Charger les référentiels et écrire les modèles Excel")
    i.add_argument("--forcer", action="store_true")
    u = sous.add_parser("creer-utilisateur", help="Créer un compte")
    u.add_argument("identifiant")
    u.add_argument("nom")
    u.add_argument("role", choices=["admin_uif", "cadre_uif", "point_focal"])
    u.add_argument("--direction", help="Code de la direction (point focal)")
    m = sous.add_parser("maj", help="Mettre à jour une source API")
    m.add_argument("source", choices=["WB", "FMI"])
    f = sous.add_parser("importer-ihsi", help="Importer un fichier de population de l'IHSI")
    f.add_argument("fichier")
    sous.add_parser("chargements", help="Lister les derniers chargements")
    d = sous.add_parser("exporter-demo", help="Figer les données publiques pour le mode démonstration de l'interface")
    d.add_argument("dossier", nargs="?", default="../frontend/public/demo")
    args = p.parse_args(argv)

    with SessionLocal() as session:
        if args.commande == "init":
            from app.services.modeles_excel import ecrire_tous
            from app.services.referentiel import charger_referentiel

            bilan = charger_referentiel(session, forcer=args.forcer)
            for nom, (ajoutes, modifies) in bilan.items():
                print(f"  {nom:18} {ajoutes:3} ajouté(s) {modifies:3} mis à jour")
            for chemin in ecrire_tous(session):
                print(f"  modèle écrit : {chemin.name}")
        elif args.commande == "creer-utilisateur":
            from app.services.comptes import creer_compte

            mdp = getpass.getpass("Mot de passe (12 caractères au moins) : ")
            if mdp != getpass.getpass("Confirmer : "):
                print("Les deux saisies diffèrent.")
                return 1
            try:
                creer_compte(session, args.identifiant, args.nom, args.role, mdp, args.direction, auteur="cli")
            except ValueError as exc:
                print(f"Erreur : {exc}")
                return 1
            print(f"Compte {args.identifiant} créé ({args.role}).")
        elif args.commande == "maj":
            from app.services.mises_a_jour import mettre_a_jour

            c = mettre_a_jour(session, args.source, declencheur="manuel", auteur="cli")
            print(f"Chargement #{c.id} : {c.statut} — {c.message}")
            for k in c.controles:
                print(f"  [{k.resultat:7}] {k.regle} : {k.detail[:200]}")
        elif args.commande == "importer-ihsi":
            from app.connectors.base import lire_tableau
            from app.connectors.ihsi import ConnecteurIHSI
            from app.services.chargement import traiter_envoi

            chemin = Path(args.fichier)
            con = ConnecteurIHSI()
            c = traiter_envoi(session, source_code="IHSI", df_brut=lire_tableau(chemin.read_bytes(), chemin.name),
                              modele=con.modele, normaliser=con.normaliser, declencheur="manuel", auteur="cli",
                              fichier_nom=chemin.name)
            print(f"Chargement #{c.id} : {c.statut} — {c.message}")
            for k in c.controles:
                print(f"  [{k.resultat:7}] {k.regle} : {k.detail[:200]}")
        elif args.commande == "exporter-demo":
            from app.services.demo import exporter_demo

            for chemin in exporter_demo(session, Path(args.dossier)):
                print(f"  {chemin}")
        elif args.commande == "chargements":
            from app.models import Chargement

            for c in session.scalars(select(Chargement).order_by(Chargement.id.desc()).limit(20)):
                print(f"#{c.id:<4} {c.cree_le:%Y-%m-%d %H:%M} {c.source.code:5} {c.statut:12} {c.message or ''}"[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
