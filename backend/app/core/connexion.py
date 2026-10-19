"""Limitation des tentatives de connexion.

Règle : au bout de MAX_ECHECS_COMPTE échecs en FENETRE pour une même adresse e-mail
(ou MAX_ECHECS_IP pour une même adresse IP), la connexion est refusée jusqu'à ce que
le plus ancien de ces échecs sorte de la fenêtre. Pendant le blocage, même le bon mot
de passe est refusé : sinon un attaquant pourrait continuer à tester des mots de passe.

Le blocage vise l'adresse saisie, qu'un compte existe ou non, pour ne pas révéler quelles
adresses sont valides. Un administrateur peut débloquer un compte à la main.
"""

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.connexion import EchecConnexion

FENETRE = timedelta(minutes=15)
MAX_ECHECS_COMPTE = 5
MAX_ECHECS_IP = 30
CONSERVATION = timedelta(days=30)


def normaliser_email(email: str | None) -> str:
    return (email or "").strip().lower()


def attente_apres(dates_recentes: list[datetime], maximum: int, maintenant: datetime) -> float:
    """Secondes d'attente restantes (0 si pas de blocage).

    `dates_recentes` : dates des échecs de la fenêtre, de la plus récente à la plus ancienne.
    Le blocage tombe quand l'échec de rang `maximum` sort de la fenêtre.
    """
    if len(dates_recentes) < maximum:
        return 0.0
    deblocage = dates_recentes[maximum - 1] + FENETRE
    return max(0.0, (deblocage - maintenant).total_seconds())


def _dates_echecs(db: Session, colonne, valeur: str, limite: int, debut: datetime) -> list[datetime]:
    lignes = (
        db.query(EchecConnexion.date_echec)
        .filter(colonne == valeur, EchecConnexion.date_echec >= debut)
        .order_by(EchecConnexion.date_echec.desc())
        .limit(limite)
        .all()
    )
    return [ligne[0] for ligne in lignes]


def secondes_avant_deblocage(db: Session, email: str, adresse_ip: str) -> int:
    maintenant = datetime.now(timezone.utc)
    debut = maintenant - FENETRE
    attentes = [
        attente_apres(
            _dates_echecs(db, EchecConnexion.email, email, MAX_ECHECS_COMPTE, debut),
            MAX_ECHECS_COMPTE,
            maintenant,
        ),
        attente_apres(
            _dates_echecs(db, EchecConnexion.adresse_ip, adresse_ip, MAX_ECHECS_IP, debut),
            MAX_ECHECS_IP,
            maintenant,
        ),
    ]
    return math.ceil(max(attentes))


def enregistrer_echec(db: Session, email: str, adresse_ip: str) -> None:
    db.add(EchecConnexion(email=email, adresse_ip=adresse_ip))
    # Ménage : on ne garde pas l'historique indéfiniment.
    db.query(EchecConnexion).filter(
        EchecConnexion.date_echec < datetime.now(timezone.utc) - CONSERVATION
    ).delete(synchronize_session=False)


def effacer_echecs(db: Session, email: str) -> None:
    """Remet le compteur à zéro (connexion réussie, déblocage ou nouveau mot de passe)."""
    db.query(EchecConnexion).filter(EchecConnexion.email == email).delete(
        synchronize_session=False
    )


def emails_bloques(db: Session) -> set[str]:
    """Adresses actuellement bloquées (pour l'affichage dans la page des comptes)."""
    debut = datetime.now(timezone.utc) - FENETRE
    lignes = (
        db.query(EchecConnexion.email)
        .filter(EchecConnexion.date_echec >= debut)
        .group_by(EchecConnexion.email)
        .having(func.count(EchecConnexion.id) >= MAX_ECHECS_COMPTE)
        .all()
    )
    return {ligne[0] for ligne in lignes}