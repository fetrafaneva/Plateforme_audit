"""Crée deux sous-services de démonstration et y répartit des comptes.

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.seed_services

Résultat :
    Direction Générale MID (racine)
      ├── District d'Ambovombe : agent@test.mg, tech@test.mg
      └── District de Toliara I : chef@test.mg
Le responsable (et l'administrateur) restent à la racine : ils voient tout le
périmètre, ce qui permet de montrer le classement des services.

Ne supprime rien et peut être relancé. À relancer après seed_demo.py, qui
recrée les comptes.
"""

import sys

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.db.base import SessionLocal, engine
from app.models.identity import ServiceCommune, Utilisateur

BASE_ATTENDUE = "audit_comportemental"

SOUS_SERVICES = {
    "District d'Ambovombe": ["agent@test.mg", "tech@test.mg"],
    "District de Toliara I": ["chef@test.mg"],
}


def main() -> None:
    if engine.url.database != BASE_ATTENDUE:
        sys.exit(f"Refus : la base ciblée est '{engine.url.database}', pas '{BASE_ATTENDUE}'.")

    db = SessionLocal()
    try:
        responsable = db.query(Utilisateur).filter(Utilisateur.email == "responsable@test.mg").first()
        if responsable is None:
            sys.exit("Compte responsable@test.mg introuvable : lance d'abord seed_demo.py.")
        racine_id = responsable.id_service

        for nom, emails in SOUS_SERVICES.items():
            service = db.query(ServiceCommune).filter(ServiceCommune.nom_service == nom).first()
            if service is None:
                service = ServiceCommune(nom_service=nom, type="district", id_service_parent=racine_id)
                db.add(service)
                db.flush()
                print(f"Service créé : {nom}")
            for email in emails:
                user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
                if user is None:
                    print(f"  compte {email} introuvable, ignoré")
                    continue
                user.id_service = service.id_service
                print(f"  {email} -> {nom}")
        db.commit()
        print("Terminé.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()