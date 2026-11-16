"""Étape 7 : les 6 règles de contrôle qualité, sur des fichiers bons et mauvais."""
import pandas as pd
import pytest

from app.quality import regles
from app.quality.modeles import MODELES_DEPOT, STANDARD
from app.services.chargement import construire_contexte, controler, frame_standard

MODELE = MODELES_DEPOT["education_financiere"]


def bon_fichier() -> pd.DataFrame:
    return pd.DataFrame({
        "indicateur": ["EF-02"] * 3 + ["EF-01"],
        "departement": ["HT-OU"] * 3 + [""],
        "sexe": ["F", "H", "Total", "Total"],
        "annee": ["2025"] * 4,
        "trimestre": [""] * 4,
        "valeur": ["1200", "800", "2000", "350"],
    })


def normaliser(df):
    return df.assign(pays="HTI", institution="", source="UIF")


@pytest.fixture()
def ctx(session):
    return construire_contexte(session)


def resultat(resultats, numero):
    return next(r for r in resultats if r.regle.startswith(f"{numero}.")).resultat


def test_bon_fichier_passe_les_6_regles(ctx):
    resultats, std = controler(bon_fichier(), MODELE, normaliser, ctx)
    assert [r.resultat for r in resultats] == ["réussi"] * 6
    assert len(std) == 4


# Règle 1 — format
def test_colonne_manquante(ctx):
    r = regles.regle_format(bon_fichier().drop(columns=["valeur"]), MODELE, ctx)
    assert r.resultat == "échec" and "valeur" in r.detail


def test_code_departement_inconnu(ctx):
    df = bon_fichier()
    df.loc[0, "departement"] = "HT-XX"
    r = regles.regle_format(df, MODELE, ctx)
    assert r.resultat == "échec" and "HT-XX" in r.detail


def test_indicateur_non_autorise_pour_ce_type(ctx):
    df = bon_fichier()
    df.loc[0, "indicateur"] = "ACC-01"
    assert regles.regle_format(df, MODELE, ctx).resultat == "échec"


def test_valeur_non_numerique(ctx):
    df = bon_fichier()
    df.loc[1, "valeur"] = "beaucoup"
    r = regles.regle_format(df, MODELE, ctx)
    assert r.resultat == "échec" and "beaucoup" in r.detail


# Règle 2 — complétude
def test_quelques_vides_donnent_une_alerte(ctx):
    df = pd.concat([bon_fichier()] * 3, ignore_index=True)
    df["annee"] = [str(2014 + i) for i in range(len(df))]
    df.loc[0, "valeur"] = ""
    assert regles.regle_completude(df, MODELE, ctx).resultat == "alerte"


def test_trop_de_vides_donnent_un_echec(ctx):
    df = bon_fichier()
    df.loc[[0, 1], "valeur"] = ""
    assert regles.regle_completude(df, MODELE, ctx).resultat == "échec"


# Règle 3 — doublons
def test_doublon_sur_la_cle(ctx):
    df = pd.concat([bon_fichier(), bon_fichier().iloc[[0]]], ignore_index=True)
    assert regles.regle_doublons(df, MODELE, ctx).resultat == "échec"


# Règle 4 — cohérence
def test_femmes_plus_hommes_different_du_total(ctx):
    df = bon_fichier()
    df.loc[2, "valeur"] = "2500"
    r = regles.regle_coherence(frame_standard(normaliser(df)), ctx)
    assert r.resultat == "échec" and "≠" in r.detail


def test_pourcentage_hors_bornes(ctx):
    std = frame_standard([{"indicateur": "USA-04", "pays": "HTI", "sexe": "Total", "annee": 2025, "valeur": 120,
                           "source": "WB"}])
    assert regles.regle_coherence(std, ctx).resultat == "échec"


def test_pourcentage_du_pib_peut_depasser_100(ctx):
    std = frame_standard([{"indicateur": "PRO-01", "pays": "CAN", "sexe": "Total", "annee": 2020, "valeur": 135,
                           "source": "FMI"}])
    assert regles.regle_coherence(std, ctx).resultat == "réussi"


# Règle 5 — variation inhabituelle
def test_variation_au_dela_du_seuil(ctx):
    std = frame_standard([
        {"indicateur": "ACC-01", "pays": "HTI", "sexe": "Total", "annee": 2019, "valeur": 2.0, "source": "FMI"},
        {"indicateur": "ACC-01", "pays": "HTI", "sexe": "Total", "annee": 2020, "valeur": 4.0, "source": "FMI"},
    ])
    r = regles.regle_variation(std, ctx)
    assert r.resultat == "alerte" and "+100 %" in r.detail


def test_variation_dans_le_seuil(ctx):
    std = frame_standard([
        {"indicateur": "ACC-01", "pays": "HTI", "sexe": "Total", "annee": 2019, "valeur": 2.0, "source": "FMI"},
        {"indicateur": "ACC-01", "pays": "HTI", "sexe": "Total", "annee": 2020, "valeur": 2.2, "source": "FMI"},
    ])
    assert regles.regle_variation(std, ctx).resultat == "réussi"


def test_seuil_reglable_par_indicateur(session):
    from app.models import Indicateur

    session.query(Indicateur).filter_by(code="ACC-01").one().seuil_variation_pct = 150
    session.commit()
    std = frame_standard([
        {"indicateur": "ACC-01", "pays": "HTI", "sexe": "Total", "annee": 2019, "valeur": 2.0, "source": "FMI"},
        {"indicateur": "ACC-01", "pays": "HTI", "sexe": "Total", "annee": 2020, "valeur": 4.0, "source": "FMI"},
    ])
    assert regles.regle_variation(std, construire_contexte(session)).resultat == "réussi"


# Règle 6 — données nominatives
@pytest.mark.parametrize("colonne", ["nom_client", "NIF", "numero_compte", "Telephone", "prénom"])
def test_colonne_nominative_refusee(ctx, colonne):
    df = bon_fichier().assign(**{colonne: "x"})
    assert regles.regle_nominatif(df, MODELE, ctx).resultat == "échec"


@pytest.mark.parametrize("valeur", ["003-456-789-1", "1234567890123", "client@exemple.ht", "+509 3712 3456"])
def test_valeur_nominative_refusee(ctx, valeur):
    df = bon_fichier()
    df["departement"] = df["departement"].astype(object)
    df.loc[0, "departement"] = valeur
    assert regles.regle_nominatif(df, MODELE, ctx).resultat == "échec"


def test_echec_bloque_le_chargement(session):
    from app.services.chargement import traiter_envoi

    df = bon_fichier().assign(nom_client="Jean")
    c = traiter_envoi(session, source_code="UIF", df_brut=df, modele=MODELE, normaliser=normaliser,
                      declencheur="manuel", auteur="test")
    assert c.statut == "rejeté" and c.nb_nouvelles == 0
    assert len(c.controles) == 4  # règles 4 et 5 non exécutées sur un fichier refusé


def test_alerte_demande_une_validation_puis_renvoi_avec_commentaire(session):
    from app.services.chargement import decider, traiter_envoi

    df = pd.concat([bon_fichier()] * 3, ignore_index=True)
    df["annee"] = [str(2014 + i) for i in range(len(df))]
    df.loc[0, "valeur"] = ""
    c = traiter_envoi(session, source_code="UIF", df_brut=df, modele=MODELE, normaliser=normaliser,
                      declencheur="manuel", auteur="test")
    assert c.statut == "en contrôle"
    with pytest.raises(ValueError, match="commentaire"):
        decider(session, c, "renvoyer", "", "admin")
    decider(session, c, "renvoyer", "Merci de compléter la valeur manquante.", "admin")
    assert c.statut == "rejeté" and c.decision_commentaire.startswith("Merci")
