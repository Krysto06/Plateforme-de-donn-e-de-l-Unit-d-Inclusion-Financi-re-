"""Étapes 4 et 5 : connecteurs Banque mondiale et FMI, sur de vraies réponses enregistrées le 16/11/2026."""
import httpx
import pytest
from sqlalchemy import func, select

from app.connectors.base import ErreurSource, obtenir_json
from app.connectors.imf import ConnecteurFMI, decoder_sdmx
from app.connectors.worldbank import ConnecteurBanqueMondiale
from app.models import Observation
from app.services.chargement import decider
from app.services.mises_a_jour import mettre_a_jour
from tests.conftest import valeur

TOLERANCE = 0.05


def charger(session, code, client):
    c = mettre_a_jour(session, code, "manuel", "test", client=client)
    if c.statut == "en contrôle":  # alertes de variation : validation humaine simulée
        decider(session, c, "accepter", "validé pendant le test", "test")
    assert c.statut == "chargé", c.message
    return c


def nb_observations(session, courantes=True):
    q = select(func.count()).select_from(Observation)
    return session.scalar(q.where(Observation.est_courante) if courantes else q)


# ------------------------------------------------------------------ Banque mondiale


def test_banque_mondiale_charge_haiti_et_les_comparateurs(session, faux_reseau):
    charger(session, "WB", faux_reseau)
    for pays in ("HTI", "DOM", "JAM", "NIC", "BRA", "FRA", "CAN"):
        assert valeur(session, "ACC-01", "WB", 2020, pays) is not None, pays


def test_banque_mondiale_valeur_actuelle_agences_2020(session, faux_reseau):
    charger(session, "WB", faux_reseau)
    assert valeur(session, "ACC-01", "WB", 2020) == pytest.approx(2.67, abs=TOLERANCE)


def test_banque_mondiale_valeur_de_la_fiche_agences_2020(session, faux_reseau):
    # Valeur de contrôle de la fiche (2,62). L'API publie 2,6655 le 16/11/2026 : écart de 0,046, dans la tolérance.
    charger(session, "WB", faux_reseau)
    assert valeur(session, "ACC-01", "WB", 2020) == pytest.approx(2.62, abs=TOLERANCE)


def test_banque_mondiale_relance_sans_doublon(session, faux_reseau):
    charger(session, "WB", faux_reseau)
    avant = nb_observations(session, courantes=False)
    c = mettre_a_jour(session, "WB", "manuel", "test", client=faux_reseau)
    assert c.statut == "chargé"  # rien de neuf : pas d'alerte, chargement direct
    assert c.nb_nouvelles == 0 and c.nb_modifiees == 0 and c.nb_inchangees > 0
    assert nb_observations(session, courantes=False) == avant


def test_findex_par_sexe_et_ecart_gen01(session, faux_reseau):
    charger(session, "WB", faux_reseau)
    f, h = valeur(session, "USA-04", "WB", 2017, sexe="F"), valeur(session, "USA-04", "WB", 2017, sexe="H")
    assert valeur(session, "GEN-01", "WB", 2017) == pytest.approx(h - f)


def test_banque_mondiale_pagination(session):
    pages = {
        1: [{"page": 1, "pages": 2}, [{"countryiso3code": "HTI", "date": "2020", "value": 1.0}]],
        2: [{"page": 2, "pages": 2}, [{"countryiso3code": "HTI", "date": "2019", "value": 2.0}]],
    }
    client = httpx.Client(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json=pages[int(r.url.params["page"])])))
    lignes = ConnecteurBanqueMondiale(session, client)._pages("https://api.worldbank.org/v2/x", {})
    assert [l["date"] for l in lignes] == ["2020", "2019"]


def test_code_inconnu_signale_clairement(session, faux_reseau):
    from app.models import SerieSource, Source

    wb = session.scalar(select(Source).where(Source.code == "WB"))
    session.add(SerieSource(indicateur_id=1, source=wb, code_serie="CODE.INVENTE", verifie_le="2026-11-16"))
    session.commit()
    resultat = ConnecteurBanqueMondiale(session, faux_reseau).tester()
    assert not resultat.ok and any("CODE.INVENTE : INCONNU" in d for d in resultat.details)


def test_reessaie_apres_une_erreur_reseau():
    appels = []

    def serveur(requete):
        appels.append(1)
        if len(appels) < 3:
            raise httpx.ReadTimeout("trop lent", request=requete)
        return httpx.Response(200, json={"ok": True})

    assert obtenir_json(httpx.Client(transport=httpx.MockTransport(serveur)), "https://x/y") == {"ok": True}
    assert len(appels) == 3


def test_abandonne_apres_trois_essais_et_trace_l_erreur(session):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    with pytest.raises(ErreurSource, match="après 3 essais"):
        obtenir_json(client, "https://x/y")
    c = mettre_a_jour(session, "WB", "manuel", "test", client=client)
    assert c.statut == "erreur" and "503" in c.message


# ------------------------------------------------------------------ FMI


def test_fmi_valeurs_de_controle(session, faux_reseau):
    charger(session, "FMI", faux_reseau)
    assert valeur(session, "ACC-01", "FMI", 2020) == pytest.approx(2.67, abs=TOLERANCE)
    assert valeur(session, "USA-01", "FMI", 2020) == pytest.approx(257.05, abs=TOLERANCE)
    assert valeur(session, "PRO-01", "FMI", 2020) == pytest.approx(20.25, abs=TOLERANCE)


def test_deux_sources_gardees_separees(session, faux_reseau):
    charger(session, "FMI", faux_reseau)
    charger(session, "WB", faux_reseau)
    assert valeur(session, "ACC-01", "FMI", 2020) is not None
    assert valeur(session, "ACC-01", "WB", 2020) is not None


def test_fmi_relance_sans_doublon(session, faux_reseau):
    charger(session, "FMI", faux_reseau)
    avant = nb_observations(session, courantes=False)
    c = mettre_a_jour(session, "FMI", "manuel", "test", client=faux_reseau)
    assert c.statut == "chargé" and c.nb_nouvelles == 0
    assert nb_observations(session, courantes=False) == avant


def test_fmi_part_des_femmes_parmi_les_emprunteurs(session, faux_reseau):
    charger(session, "FMI", faux_reseau)
    f, h = valeur(session, "AUX-EMP", "FMI", 2020, sexe="F"), valeur(session, "AUX-EMP", "FMI", 2020, sexe="H")
    assert valeur(session, "GEN-02", "FMI", 2020) == pytest.approx(100 * f / (f + h))


def test_decodage_sdmx():
    import json

    from tests.conftest import FIXTURES

    lignes = decoder_sdmx(json.loads((FIXTURES / "imf" / "fas_comparateurs.json").read_text()))
    cles = {(l["pays"], l["code_serie"], l["annee"]) for l in lignes}
    assert ("HTI", "FA22.COMBANK._Z._T.PHTADLT_NUM", "2020") in cles


def test_nouvelle_valeur_cree_une_version_sans_ecraser(session, faux_reseau):
    import pandas as pd

    from app.quality.modeles import STANDARD
    from app.services.chargement import traiter_envoi

    charger(session, "FMI", faux_reseau)
    revise = pd.DataFrame([{"indicateur": "ACC-01", "pays": "HTI", "departement": "", "sexe": "Total", "annee": "2020",
                            "trimestre": "", "institution": "", "valeur": "2.70"}])
    c = traiter_envoi(session, source_code="FMI", df_brut=revise, modele=STANDARD,
                      normaliser=lambda d: d.assign(source="FMI"), declencheur="manuel", auteur="test")
    assert c.nb_modifiees == 1
    versions = session.scalars(select(Observation).where(Observation.cle == "ACC-01|HTI|-|Total|2020|-|FMI")
                               .order_by(Observation.version)).all()
    assert [(v.version, v.est_courante) for v in versions] == [(1, False), (2, True)]
    assert versions[0].valeur == pytest.approx(2.6655, abs=1e-3)  # l'ancienne valeur est conservée
