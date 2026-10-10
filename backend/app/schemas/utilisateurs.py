from pydantic import BaseModel


class UtilisateurResume(BaseModel):
    """Informations minimales pour choisir un compte (ex. lier un participant).

    Ni email ni mot de passe : seulement ce qui permet de distinguer deux homonymes.
    """

    id_utilisateur: int
    nom: str
    prenom: str
    matricule: str
    role: str