"""Insère les données de référence minimales (rôles + un service) pour pouvoir tester l'API.

Usage : python seed_data.py
"""

from app import models  # noqa: F401 — enregistre les modèles sur Base
from app.db.base import SessionLocal
from app.models.identity import Role, ServiceCommune
from app.models.ressources import RessourceSensible


def seed():
    db = SessionLocal()
    try:
        if db.query(Role).count() == 0:
            db.add_all(
                [
                    Role(nom_role="agent", niveau_acces="standard"),
                    Role(nom_role="auditeur", niveau_acces="eleve"),
                    Role(nom_role="responsable_hierarchique", niveau_acces="eleve"),
                    Role(nom_role="administrateur", niveau_acces="total"),
                ]
            )

        if db.query(ServiceCommune).count() == 0:
            db.add(ServiceCommune(nom_service="MID - Direction Générale", type="ministere"))
        db.commit()

        if db.query(RessourceSensible).count() == 0:
            service = db.query(ServiceCommune).first()
            db.add(
                RessourceSensible(
                    type_ressource="dossier identité",
                    niveau_sensibilite="eleve",
                    id_service_proprietaire=service.id_service,
                )
            )

        db.commit()

        print("Données de référence :")
        for role in db.query(Role).all():
            print(f"  Rôle {role.id_role}: {role.nom_role}")
        for service in db.query(ServiceCommune).all():
            print(f"  Service {service.id_service}: {service.nom_service}")
        for ressource in db.query(RessourceSensible).all():
            print(f"  Ressource {ressource.id_ressource}: {ressource.type_ressource}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()