"""Crée les 12 tables du MCD sur la base pointée par DATABASE_URL (.env).

Usage : python create_tables.py
"""

from app import models  # noqa: F401 — importe les 12 modèles pour les enregistrer sur Base
from app.db.base import Base, engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès :")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")