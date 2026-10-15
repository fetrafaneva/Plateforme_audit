r"""Sauvegarde et vérification des données de la plateforme.

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.sauvegarde                       # sauvegarde complète
    python -m scripts.sauvegarde --dossier D:\sauvegardes   # ailleurs que backend\sauvegardes
    python -m scripts.sauvegarde --verifier            # contrôle des pièces jointes seulement

Une sauvegarde est un dossier horodaté contenant :
    base.dump        export PostgreSQL (pg_dump, format personnalisé)
    uploads.zip      toutes les pièces jointes des rapports
    manifeste.json   date, version des migrations, liste des fichiers avec leur SHA-256

La base et les pièces jointes forment un tout : sauvegarder l'une sans l'autre donne
des rapports dont les fichiers manquent. Ce script prend les deux en même temps.

Restauration (écrase les données actuelles, à faire avec prudence) :
    pg_restore -h localhost -p 5433 -U postgres -d audit_comportemental --clean --if-exists base.dump
    Expand-Archive uploads.zip -DestinationPath backend\uploads -Force
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.core.config import settings
from app.core.pieces import dossier_base, sha256_fichier, verifier_pieces
from app.db.base import SessionLocal, engine


def trouver_pg_dump() -> str:
    trouve = shutil.which("pg_dump")
    if trouve:
        return trouve
    candidats = sorted(glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe"), reverse=True)
    if candidats:
        return candidats[0]
    sys.exit("pg_dump introuvable : ajoute le dossier bin de PostgreSQL au PATH.")


def exporter_base(destination: Path) -> None:
    url = make_url(settings.database_url)
    environnement = dict(os.environ)
    if url.password:
        environnement["PGPASSWORD"] = url.password  # jamais dans la ligne de commande
    commande = [
        trouver_pg_dump(),
        "-h", url.host or "localhost",
        "-p", str(url.port or 5432),
        "-U", url.username or "postgres",
        "-Fc",
        "-f", str(destination),
        url.database,
    ]
    resultat = subprocess.run(commande, env=environnement, capture_output=True)
    if resultat.returncode != 0:
        sys.exit("pg_dump a échoué :\n" + resultat.stderr.decode("utf-8", errors="replace"))


def archiver_pieces(destination: Path) -> list[dict]:
    base = dossier_base()
    fichiers: list[dict] = []
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        if base.is_dir():
            for chemin in sorted(base.rglob("*")):
                if chemin.is_file():
                    relatif = chemin.relative_to(base)
                    archive.write(chemin, relatif)
                    fichiers.append(
                        {
                            "chemin": str(relatif).replace("\\", "/"),
                            "taille": chemin.stat().st_size,
                            "sha256": sha256_fichier(chemin),
                        }
                    )
    return fichiers


def sauvegarder(dossier_parent: Path) -> None:
    maintenant = datetime.now(timezone.utc)
    dossier = dossier_parent / maintenant.astimezone().strftime("%Y-%m-%d_%H%M%S")
    dossier.mkdir(parents=True, exist_ok=False)

    print(f"Sauvegarde dans {dossier}")
    print("  export de la base...")
    exporter_base(dossier / "base.dump")
    print("  archivage des pièces jointes...")
    fichiers = archiver_pieces(dossier / "uploads.zip")

    with engine.connect() as connexion:
        version = connexion.execute(text("SELECT version_num FROM alembic_version")).scalar()

    manifeste = {
        "date_utc": maintenant.isoformat(),
        "base": engine.url.database,
        "version_migrations": version,
        "nb_fichiers": len(fichiers),
        "fichiers": fichiers,
    }
    (dossier / "manifeste.json").write_text(
        json.dumps(manifeste, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    taille = sum(f.stat().st_size for f in dossier.iterdir()) / (1024 * 1024)
    print(f"Terminé : {len(fichiers)} fichier(s) joint(s), {taille:.1f} Mo au total.")
    print("Copie ce dossier hors de cet ordinateur (disque externe, autre machine).")


def verifier() -> int:
    db = SessionLocal()
    try:
        resultat = verifier_pieces(db)
    finally:
        db.close()

    print(f"{resultat['nb_verifiees']} pièce(s) vérifiée(s).")
    for p in resultat["manquantes"]:
        print(f"  MANQUANTE : {p['nom_original']} (rapport {p['id_rapport']}, pièce {p['id_piece']})")
    for p in resultat["alterees"]:
        print(f"  ALTÉRÉE   : {p['nom_original']} (rapport {p['id_rapport']}, pièce {p['id_piece']})")
    for chemin in resultat["orphelins"]:
        print(f"  ORPHELIN  : {chemin} (sur le disque, absent de la base)")

    if resultat["manquantes"] or resultat["alterees"]:
        return 1
    print("Toutes les pièces enregistrées sont présentes et intactes.")
    return 0


def main() -> None:
    parseur = argparse.ArgumentParser(description="Sauvegarde et contrôle des pièces jointes")
    parseur.add_argument("--dossier", help="dossier où créer la sauvegarde")
    parseur.add_argument("--verifier", action="store_true", help="contrôler les pièces jointes seulement")
    arguments = parseur.parse_args()

    if arguments.verifier:
        sys.exit(verifier())
    sauvegarder(Path(arguments.dossier) if arguments.dossier else Path("sauvegardes"))


if __name__ == "__main__":
    main()