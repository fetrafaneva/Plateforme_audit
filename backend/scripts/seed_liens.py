"""Lie des comptes de démonstration à des participants de missions.

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.seed_liens

Pour chaque compte de démo, ajoute un participant lié à ce compte dans une
équipe existante (l'agent participe à deux missions). Ne supprime rien :
on peut le relancer sans créer de doublon. À relancer après seed_demo.py,
qui efface les participants.

Les fonctions affichées sont inventées.
"""

import sys

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.db.base import SessionLocal, engine
from app.models.identity import Utilisateur
from app.models.missions import Equipe, Participant

BASE_ATTENDUE = "audit_comportemental"

FONCTIONS = {
    "agent@test.mg": "Agent de terrain",
    "tech@test.mg": "Technicien serveur",
    "chef@test.mg": "Chef de mission",
    "responsable@test.mg": "Superviseur",
}
DEUX_MISSIONS = {"agent@test.mg"}


def main() -> None:
    if engine.url.database != BASE_ATTENDUE:
        sys.exit(f"Refus : la base ciblée est '{engine.url.database}', pas '{BASE_ATTENDUE}'.")

    db = SessionLocal()
    try:
        equipes = db.query(Equipe).order_by(Equipe.id).all()
        if not equipes:
            sys.exit("Aucune équipe en base : lance d'abord seed_demo.py.")

        crees = 0
        for i, (email, fonction) in enumerate(FONCTIONS.items()):
            user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
            if user is None:
                print(f"  compte {email} introuvable, ignoré")
                continue

            cibles = [equipes[i % len(equipes)]]
            if email in DEUX_MISSIONS and equipes[-1].id != cibles[0].id:
                cibles.append(equipes[-1])  # la dernière équipe : en général une autre mission

            for equipe in cibles:
                deja = (
                    db.query(Participant)
                    .filter(
                        Participant.equipe_id == equipe.id,
                        Participant.id_utilisateur == user.id_utilisateur,
                    )
                    .first()
                )
                if deja is not None:
                    print(f"  {email} déjà lié à l'équipe {equipe.id}")
                    continue
                db.add(
                    Participant(
                        equipe_id=equipe.id,
                        nom=f"{user.prenom} {user.nom}",
                        fonction=fonction,
                        id_utilisateur=user.id_utilisateur,
                    )
                )
                crees += 1
                print(f"  {email} -> équipe {equipe.id} ({equipe.type_equipe or 'sans type'})")

        db.commit()
        print(f"{crees} participant(s) lié(s) à un compte.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()