"""Lecture de la configuration depuis le fichier .env (jamais de secret dans le code)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PDIF"
    environment: str = "developpement"
    # SQLite en développement ; PostgreSQL sur le serveur BRH, par ex. postgresql+psycopg://...
    database_url: str = "sqlite:///./pdif.db"
    # Adresse de l'interface autorisée à appeler l'API (CORS)
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
