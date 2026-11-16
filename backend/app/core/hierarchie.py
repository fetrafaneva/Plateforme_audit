"""Parcours de la hiérarchie des services (services_communes.id_service_parent).

Utilisé par la vue « Mon service » et par le benchmarking, qui ont tous deux
besoin du périmètre d'un responsable : son service et tous ses sous-services.
"""

from sqlalchemy.orm import Session

from app.models.identity import ServiceCommune


def perimetre(db: Session, id_racine: int) -> list[ServiceCommune]:
    """Le service `id_racine` et tous ses descendants, racine en premier.

    Retourne une liste vide si le service n'existe pas. Un éventuel cycle dans
    la hiérarchie (service parent de lui-même, directement ou non) ne provoque
    pas de boucle infinie : chaque service n'est visité qu'une fois.
    """
    tous = db.query(ServiceCommune).all()
    par_id = {s.id_service: s for s in tous}
    if id_racine not in par_id:
        return []

    enfants: dict[int, list[int]] = {}
    for s in tous:
        if s.id_service_parent is not None:
            enfants.setdefault(s.id_service_parent, []).append(s.id_service)

    ordre: list[int] = []
    vus: set[int] = set()
    pile = [id_racine]
    while pile:
        courant = pile.pop()
        if courant in vus:
            continue
        vus.add(courant)
        ordre.append(courant)
        pile.extend(enfants.get(courant, []))
    return [par_id[i] for i in ordre]
