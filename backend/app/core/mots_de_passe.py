"""Génération des mots de passe temporaires."""

import secrets

MAJUSCULES = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # sans I ni O, faciles à confondre
MINUSCULES = "abcdefghijkmnpqrstuvwxyz"  # sans l
CHIFFRES = "23456789"  # sans 0 ni 1


def generer_mot_de_passe(longueur: int = 12) -> str:
    """Mot de passe aléatoire (module `secrets`), avec majuscule, minuscule et chiffre.

    Les caractères ambigus sont exclus pour qu'il puisse être dicté ou recopié sans erreur.
    """
    tous = MAJUSCULES + MINUSCULES + CHIFFRES
    while True:
        mot_de_passe = "".join(secrets.choice(tous) for _ in range(longueur))
        if (
            any(c in MAJUSCULES for c in mot_de_passe)
            and any(c in MINUSCULES for c in mot_de_passe)
            and any(c in CHIFFRES for c in mot_de_passe)
        ):
            return mot_de_passe