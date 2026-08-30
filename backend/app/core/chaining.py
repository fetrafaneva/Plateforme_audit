import hashlib
from datetime import datetime

# Hash de départ, avant toute entrée réelle dans le journal (bloc "genèse")
GENESIS_HASH = "0" * 64


def compute_hash(
    id_utilisateur: int,
    id_ressource: int,
    type_action: str,
    horodatage: datetime,
    hash_precedent: str,
) -> str:
    """Calcule le hash SHA-256 d'une entrée de journal, lié cryptographiquement
    au hash de l'entrée précédente. Toute modification d'une entrée passée change
    son hash, donc casse la chaîne pour toutes les entrées suivantes.
    """
    payload = (
        f"{id_utilisateur}|{id_ressource}|{type_action}|"
        f"{horodatage.isoformat()}|{hash_precedent}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()