"""Création de notifications.

Ces fonctions n'appellent pas `db.commit()` : la notification est enregistrée dans
la même transaction que l'action qui la provoque (soumission, validation...), donc
elle existe si, et seulement si, l'action a réussi.
"""

from sqlalchemy.orm import Session

from app.models.identity import Role, Utilisateur
from app.models.notifications import Notification


def notifier(
    db: Session,
    id_utilisateur: int,
    type_notification: str,
    message: str,
    lien: str | None = None,
) -> None:
    db.add(
        Notification(
            id_utilisateur=id_utilisateur,
            type_notification=type_notification,
            message=message[:500],
            lien=lien,
        )
    )


def notifier_administrateurs(
    db: Session,
    type_notification: str,
    message: str,
    lien: str | None = None,
    sauf: int | None = None,
) -> None:
    """Notifie tous les administrateurs actifs (sauf l'utilisateur `sauf`)."""
    administrateurs = (
        db.query(Utilisateur)
        .join(Role, Role.id_role == Utilisateur.id_role)
        .filter(Role.nom_role == "administrateur", Utilisateur.statut == "actif")
        .all()
    )
    for admin in administrateurs:
        if admin.id_utilisateur != sauf:
            notifier(db, admin.id_utilisateur, type_notification, message, lien)