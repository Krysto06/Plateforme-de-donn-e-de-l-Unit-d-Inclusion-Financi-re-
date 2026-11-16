"""Mots de passe (hachés, jamais stockés en clair) et jetons de connexion."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

ITERATIONS = 390_000


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    sel = secrets.token_hex(16)
    empreinte = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), bytes.fromhex(sel), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${sel}${empreinte}"


def verifier_mot_de_passe(mot_de_passe: str, stocke: str) -> bool:
    try:
        _, iterations, sel, empreinte = stocke.split("$")
    except ValueError:
        return False
    calcul = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), bytes.fromhex(sel), int(iterations)).hex()
    return hmac.compare_digest(calcul, empreinte)


def mot_de_passe_acceptable(mot_de_passe: str) -> str | None:
    if len(mot_de_passe) < 12:
        return "Le mot de passe doit contenir au moins 12 caractères."
    return None


def creer_jeton(identifiant: str, role: str) -> str:
    reglages = get_settings()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=reglages.duree_session_minutes)
    return jwt.encode({"sub": identifiant, "role": role, "exp": expiration}, reglages.secret_key, algorithm="HS256")


def lire_jeton(jeton: str) -> dict | None:
    try:
        return jwt.decode(jeton, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
