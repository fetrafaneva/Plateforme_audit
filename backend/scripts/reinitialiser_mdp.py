"""Réinitialise le mot de passe d'un compte depuis le serveur (secours).

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.reinitialiser_mdp adresse@mail.mg

Pour le cas où aucun administrateur ne peut traiter la demande : par exemple l'unique
administrateur a perdu son mot de passe. Le mot de passe temporaire est affiché dans
la console, une seule fois, et le compte est débloqué.

Cette commande demande un accès au serveur et à la base : elle n'est pas disponible
depuis l'application.
"""

import sys

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.core.connexion import effacer_echecs, normaliser_email
from app.core.mots_de_passe import generer_mot_de_passe
from app.core.security import hash_password
from app.db.base import SessionLocal
from app.models.identity import Utilisateur


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage : python -m scripts.reinitialiser_mdp adresse@mail.mg")

    db = SessionLocal()
    try:
        utilisateur = (
            db.query(Utilisateur)
            .filter(Utilisateur.email == sys.argv[1])
            .first()
        )
        if utilisateur is None:
            sys.exit(f"Aucun compte avec l'adresse {sys.argv[1]}.")

        print(f"Compte : {utilisateur.prenom} {utilisateur.nom} ({utilisateur.email}), statut {utilisateur.statut}")
        if input("Taper OUI pour générer un nouveau mot de passe : ").strip() != "OUI":
            sys.exit("Annulé.")

        mot_de_passe = generer_mot_de_passe()
        utilisateur.mot_de_passe_hash = hash_password(mot_de_passe)
        effacer_echecs(db, normaliser_email(utilisateur.email))
        db.commit()
        print(f"\nMot de passe temporaire : {mot_de_passe}")
        print("Il ne sera plus affiché : note-le et communique-le à la personne.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()