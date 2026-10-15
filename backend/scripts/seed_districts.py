"""Charge la liste des districts de Madagascar (ou un autre fichier CSV).

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.seed_districts                      # data/districts_madagascar.csv
    python -m scripts.seed_districts chemin/vers/liste.csv

Ne supprime rien : un district dont le nom existe déjà est ignoré, donc le script
peut être relancé sans créer de doublon. Le fichier fourni est une liste de départ,
à comparer avec la liste officielle (voir data/LISEZ-MOI.txt).
"""

import sys
from pathlib import Path

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.core.districts import importer_districts, lire_csv
from app.db.base import SessionLocal, engine

BASE_ATTENDUE = "audit_comportemental"
FICHIER_PAR_DEFAUT = Path(__file__).resolve().parent.parent / "data" / "districts_madagascar.csv"


def main() -> None:
    if engine.url.database != BASE_ATTENDUE:
        sys.exit(f"Refus : la base ciblée est '{engine.url.database}', pas '{BASE_ATTENDUE}'.")

    chemin = Path(sys.argv[1]) if len(sys.argv) > 1 else FICHIER_PAR_DEFAUT
    if not chemin.is_file():
        sys.exit(f"Fichier introuvable : {chemin}")

    lignes = lire_csv(chemin.read_bytes())
    db = SessionLocal()
    try:
        resultat = importer_districts(db, lignes)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"{resultat['crees']} district(s) créé(s), {resultat['ignores']} déjà présent(s).")
    for erreur in resultat["erreurs"]:
        print("  ", erreur)


if __name__ == "__main__":
    main()