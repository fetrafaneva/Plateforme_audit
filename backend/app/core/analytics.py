"""Construction des profils comportementaux et détection d'anomalies.

Méthode retenue (cf. chapitre 9 du mémoire) : la baseline d'un agent est la
moyenne et l'écart-type de son volume d'accès journalier, calculés sur son
historique. Un jour est jugé anormal si son volume s'écarte de plus de
`seuil_z` écarts-types de la moyenne (méthode de contrôle statistique par
z-score, équivalente à une carte de contrôle). Volontairement simple et
interprétable plutôt qu'un modèle de machine learning — conforme à la
recommandation du document de cadrage d'éviter la complexité inutile.
"""

import pandas as pd
from sqlalchemy.orm import Session

from app.models.analyse import ProfilComportemental, ScoreAnomalie
from app.models.audit import JournalAcces

SEUIL_Z_PAR_DEFAUT = 3.0


def _historique_utilisateur(db: Session, id_utilisateur: int) -> pd.DataFrame:
    lignes = (
        db.query(JournalAcces).filter(JournalAcces.id_utilisateur == id_utilisateur).all()
    )
    data = [
        {
            "date": ligne.horodatage.date(),
            "heure": ligne.horodatage.hour,
            "id_ressource": ligne.id_ressource,
        }
        for ligne in lignes
    ]
    return pd.DataFrame(data)


def construire_profil(
    db: Session, id_utilisateur: int, periode_reference: str
) -> ProfilComportemental:
    df = _historique_utilisateur(db, id_utilisateur)
    if df.empty:
        raise ValueError(
            "Aucun historique d'accès pour cet utilisateur — impossible de construire un profil."
        )

    volume_par_jour = df.groupby("date").size()
    volume_moyen = float(volume_par_jour.mean())

    heure_min = int(df["heure"].quantile(0.05))
    heure_max = int(df["heure"].quantile(0.95))
    horaires_habituels = f"{heure_min:02d}:00-{heure_max:02d}:00"

    ressources_frequentes = df["id_ressource"].value_counts().head(3).index.tolist()
    perimetre_habituel = ",".join(str(r) for r in ressources_frequentes)

    profil = ProfilComportemental(
        id_utilisateur=id_utilisateur,
        periode_reference=periode_reference,
        volume_moyen=volume_moyen,
        horaires_habituels=horaires_habituels,
        perimetre_habituel=perimetre_habituel,
    )
    db.add(profil)
    db.commit()
    db.refresh(profil)
    return profil


def detecter_anomalie(
    db: Session, id_entree_journal: int, seuil_z: float = SEUIL_Z_PAR_DEFAUT
) -> ScoreAnomalie:
    entree = db.get(JournalAcces, id_entree_journal)
    if entree is None:
        raise ValueError("Entrée de journal introuvable.")

    profil = (
        db.query(ProfilComportemental)
        .filter(ProfilComportemental.id_utilisateur == entree.id_utilisateur)
        .order_by(ProfilComportemental.date_calcul.desc())
        .first()
    )
    if profil is None:
        raise ValueError(
            "Aucun profil comportemental pour cet utilisateur — appelle "
            "construire_profil() (POST /analyse/profils/{id_utilisateur}) d'abord."
        )

    df = _historique_utilisateur(db, entree.id_utilisateur)
    volume_par_jour = df.groupby("date").size()
    ecart_type = float(volume_par_jour.std(ddof=0)) or 1.0  # évite une division par zéro

    jour_entree = entree.horodatage.date()
    volume_du_jour = int(volume_par_jour.get(jour_entree, 0))

    z_score = (volume_du_jour - profil.volume_moyen) / ecart_type

    score = ScoreAnomalie(
        id_entree_journal=id_entree_journal,
        id_profil_reference=profil.id_profil,
        z_score=z_score,
        methode_utilisee="z-score volume journalier",
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score