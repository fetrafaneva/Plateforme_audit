"""Règle de création d'une alerte de sécurité à partir d'un score d'anomalie.

Les seuils viennent de la politique de conformité la plus récente
(`politiques_conformite.seuils_configures`, un JSON sérialisé). Exemple :

    {"seuil_alerte": 3.0, "seuil_moyen": 4.5, "seuil_critique": 6.0}

- |z| < seuil_alerte                 : pas d'alerte
- seuil_alerte <= |z| < seuil_moyen  : gravité "faible"
- seuil_moyen  <= |z| < seuil_critique : gravité "moyen"
- |z| >= seuil_critique              : gravité "critique"

Sans politique en base, aucune alerte n'est créée.
"""

import json

from sqlalchemy.orm import Session

from app.models.analyse import ScoreAnomalie
from app.models.securite import AlerteSecurite, PolitiqueConformite

SEUILS_PAR_DEFAUT = {"seuil_alerte": 3.0, "seuil_moyen": 4.5, "seuil_critique": 6.0}


def _politique_en_vigueur(db: Session) -> PolitiqueConformite | None:
    return (
        db.query(PolitiqueConformite)
        .order_by(
            PolitiqueConformite.date_effective.desc(),
            PolitiqueConformite.id_politique.desc(),
        )
        .first()
    )


def _lire_seuils(politique: PolitiqueConformite) -> dict[str, float]:
    seuils = dict(SEUILS_PAR_DEFAUT)
    try:
        lus = json.loads(politique.seuils_configures)
        if isinstance(lus, dict):
            for cle in seuils:
                if isinstance(lus.get(cle), (int, float)):
                    seuils[cle] = float(lus[cle])
    except (ValueError, TypeError):
        pass  # JSON invalide : on garde les seuils par défaut
    return seuils


def evaluer_alerte(db: Session, score: ScoreAnomalie) -> AlerteSecurite | None:
    politique = _politique_en_vigueur(db)
    if politique is None:
        return None

    seuils = _lire_seuils(politique)
    z = abs(score.z_score)
    if z < seuils["seuil_alerte"]:
        return None

    # Une seule alerte par score, même si l'analyse est relancée.
    existante = (
        db.query(AlerteSecurite).filter(AlerteSecurite.id_score == score.id_score).first()
    )
    if existante is not None:
        return existante

    if z >= seuils["seuil_critique"]:
        gravite = "critique"
    elif z >= seuils["seuil_moyen"]:
        gravite = "moyen"
    else:
        gravite = "faible"

    alerte = AlerteSecurite(
        id_score=score.id_score,
        id_politique=politique.id_politique,
        niveau_gravite=gravite,
    )
    db.add(alerte)
    db.commit()
    db.refresh(alerte)
    return alerte