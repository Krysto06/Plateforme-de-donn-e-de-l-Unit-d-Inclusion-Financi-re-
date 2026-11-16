import os

# Les tests utilisent une base en mémoire : ils ne touchent jamais la vraie base.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
