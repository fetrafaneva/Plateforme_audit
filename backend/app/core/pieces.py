"""Accès aux pièces jointes sur disque et vérification de leur intégrité."""

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rapports import PieceJointe


def dossier_base() -> Path:
    return Path(settings.uploads_dir).resolve()


def chemin_absolu(chemin_stockage: str) -> Path | None:
    """Chemin réel du fichier, ou None s'il sortait du dossier des pièces jointes."""
    base = dossier_base()
    chemin = (base / chemin_stockage).resolve()
    return chemin if base in chemin.parents else None


def sha256_fichier(chemin: Path) -> str:
    empreinte = hashlib.sha256()
    with chemin.open("rb") as fichier:
        for bloc in iter(lambda: fichier.read(1024 * 1024), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def verifier_pieces(db: Session) -> dict:
    """Compare chaque pièce enregistrée en base au fichier présent sur le disque.

    - manquantes : enregistrée en base, mais fichier absent ;
    - alterees   : fichier présent, mais son empreinte SHA-256 ne correspond plus ;
    - orphelins  : fichier sur le disque qu'aucune pièce n'enregistre.
    """
    pieces = db.query(PieceJointe).order_by(PieceJointe.id).all()
    manquantes: list[dict] = []
    alterees: list[dict] = []
    connus: set[Path] = set()

    for p in pieces:
        description = {
            "id_piece": p.id,
            "id_rapport": p.id_rapport,
            "nom_original": p.nom_original,
            "type_piece": p.type_piece,
        }
        chemin = chemin_absolu(p.chemin_stockage)
        if chemin is None or not chemin.is_file():
            manquantes.append(description)
            continue
        connus.add(chemin)
        if sha256_fichier(chemin) != p.empreinte_sha256:
            alterees.append(description)

    orphelins: list[str] = []
    base = dossier_base()
    if base.is_dir():
        for fichier in sorted(base.rglob("*")):
            if fichier.is_file() and fichier.resolve() not in connus:
                orphelins.append(str(fichier.relative_to(base)).replace("\\", "/"))

    return {
        "nb_verifiees": len(pieces),
        "manquantes": manquantes,
        "alterees": alterees,
        "orphelins": orphelins[:100],
    }