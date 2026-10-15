from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.identity import Utilisateur
from app.models.notifications import Notification
from app.schemas.notifications import NotificationOut, NotificationsOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _non_lues(db: Session, user: Utilisateur) -> int:
    return (
        db.query(func.count(Notification.id))
        .filter(Notification.id_utilisateur == user.id_utilisateur, Notification.lue.is_(False))
        .scalar()
    )


@router.get("/", response_model=NotificationsOut)
def lister_notifications(
    limite: int = Query(30, ge=1, le=100),
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Les notifications de l'utilisateur connecté, les plus récentes d'abord."""
    notifications = (
        db.query(Notification)
        .filter(Notification.id_utilisateur == current_user.id_utilisateur)
        .order_by(Notification.id.desc())
        .limit(limite)
        .all()
    )
    return NotificationsOut(
        non_lues=_non_lues(db, current_user),
        notifications=[NotificationOut.model_validate(n) for n in notifications],
    )


@router.post("/tout-lire", response_model=NotificationsOut)
def tout_marquer_lu(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.id_utilisateur == current_user.id_utilisateur,
        Notification.lue.is_(False),
    ).update({"lue": True})
    db.commit()
    return lister_notifications(30, current_user, db)


@router.post("/{id_notification}/lue", response_model=NotificationOut)
def marquer_lue(
    id_notification: int,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.get(Notification, id_notification)
    # Une notification d'un autre utilisateur est traitée comme inexistante.
    if notification is None or notification.id_utilisateur != current_user.id_utilisateur:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    notification.lue = True
    db.commit()
    db.refresh(notification)
    return notification