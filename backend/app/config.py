"""Lecture de la configuration depuis le fichier .env (jamais de secret dans le code)."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PDIF"
    environment: str = "developpement"
    # SQLite en développement ; PostgreSQL sur le serveur BRH, par ex. postgresql+psycopg://...
    database_url: str = "sqlite:///./pdif.db"
    # Adresse de l'interface autorisée à appeler l'API (CORS)
    frontend_origin: str = "http://localhost:5173"

    # Sécurité : clé de signature des jetons de connexion. OBLIGATOIRE, uniquement dans .env.
    secret_key: str = Field(min_length=32)
    duree_session_minutes: int = 480

    # Pays suivis : Haïti + comparateurs (décision du 16/11/2026)
    pays_principal: str = "HTI"
    pays_comparaison: str = "DOM,JAM,NIC,BRA,FRA,CAN"
    # Agrégats régionaux de la Banque mondiale (le FMI n'en publie pas). LCN = Amérique latine et Caraïbes.
    agregats_regionaux: str = "LCN"

    # API publiques (adresses vérifiées le 16/11/2026, voir docs/sources.md)
    wb_base_url: str = "https://api.worldbank.org/v2"
    imf_base_url: str = "https://api.imf.org/external/sdmx/3.0"
    imf_agence: str = "IMF.STA"
    imf_jeu_fas: str = "FAS"
    http_timeout_secondes: float = 25.0
    http_essais: int = 5
    http_attente_secondes: float = 2.0  # attente avant le 2e essai, doublée ensuite
    annee_debut: int = 2004

    # Mises à jour planifiées (étape 14)
    planification_active: bool = False

    # Le dépôt par les directions n'est ouvert qu'une fois la plateforme hébergée à la BRH (règle n° 1)
    depots_directions_ouverts: bool = False

    @property
    def tous_les_pays(self) -> list[str]:
        autres = [p.strip().upper() for p in self.pays_comparaison.split(",") if p.strip()]
        return [self.pays_principal.upper(), *[p for p in autres if p != self.pays_principal.upper()]]

    @property
    def agregats(self) -> list[str]:
        return [p.strip().upper() for p in self.agregats_regionaux.split(",") if p.strip()]

    @property
    def pays_banque_mondiale(self) -> list[str]:
        """Pays + agrégats régionaux : seule la Banque mondiale publie ces agrégats."""
        return [*self.tous_les_pays, *[a for a in self.agregats if a not in self.tous_les_pays]]


@lru_cache
def get_settings() -> Settings:
    return Settings()
