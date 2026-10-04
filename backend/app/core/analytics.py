"""Construction des profils comportementaux et détection d'anomalies.

Méthode retenue (cf. chapitre 9 du mémoire) : la baseline d'un agent est la
moyenne et l'écart-type de son volume d'accès journalier. Pour éviter
qu'un jour anormal ne contamine sa propre détection (limite identifiée
lors des premiers tests — la baseline incluait le pic dans son propre
calcul), la baseline est calculée par exclusion itérative des jours
aberrants : on calcule moyenne/écart-type, on retire les jours à plus de
`seuil_exclusion` écarts-types, on recalcule sur le reste, et on répète
jusqu'à stabilisation. Volontairement simple et interprétable plutôt
qu'un modèle de machine learning — conforme à la recommandation du
document de cadrage d'éviter la complexité inutile.
"""

import pandas as pd
from sqlalchemy.orm import Session

from app.models.analyse import ProfilComportemental, ScoreAnomalie
from app.models.audit import JournalAcces

SEUIL_Z_PAR_DEFAUT = 3.0
SEUIL_EXCLUSION_BASELINE = 2.5


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


def calculer_baseline_robuste(
    volume_par_jour: pd.Series,
    seuil_exclusion: float = SEUIL_EXCLUSION_BASELINE,
    max_iterations: int = 5,
) -> tuple[float, float]:
    """Moyenne et écart-type du volume journalier, en excluant itérativement
    les jours aberrants avant de recalculer. Retourne (moyenne, ecart_type).
    """
    jours_retenus = volume_par_jour.copy()
    for _ in range(max_iterations):
        moyenne = jours_retenus.mean()
        ecart_type = jours_retenus.std(ddof=0) or 1.0
        z = (jours_retenus - moyenne) / ecart_type
        jours_normaux = jours_retenus[z.abs() <= seuil_exclusion]
        if len(jours_normaux) == len(jours_retenus) or len(jours_normaux) == 0:
            break
        jours_retenus = jours_normaux

    moyenne_finale = float(jours_retenus.mean())
    ecart_type_final = float(jours_retenus.std(ddof=0) or 1.0)
    return moyenne_finale, ecart_type_final


def construire_profil(
    db: Session, id_utilisateur: int, periode_reference: str
) -> ProfilComportemental:
    df = _historique_utilisateur(db, id_utilisateur)
    if df.empty:
        raise ValueError(
            "Aucun historique d'accès pour cet utilisateur — impossible de construire un profil."
        )

    volume_par_jour = df.groupby("date").size()
    volume_moyen, _ = calculer_baseline_robuste(volume_par_jour)

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
    # Écart-type recalculé par la même méthode robuste que la baseline,
    # pour que la détection ne soit pas polluée par les jours aberrants.
    _, ecart_type = calculer_baseline_robuste(volume_par_jour)

    jour_entree = entree.horodatage.date()
    volume_du_jour = int(volume_par_jour.get(jour_entree, 0))

    z_score = (volume_du_jour - profil.volume_moyen) / ecart_type

    score = ScoreAnomalie(
        id_entree_journal=id_entree_journal,
        id_profil_reference=profil.id_profil,
        z_score=z_score,
        methode_utilisee="z-score volume journalier (baseline robuste)",
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score