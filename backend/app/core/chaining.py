import hashlib
from datetime import datetime, timezone

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

    L'horodatage est ramené en UTC avant le calcul. Sans cela, PostgreSQL peut
    renvoyer la même date avec un autre fuseau (ex. +03:00) selon la configuration
    du serveur : le texte isoformat() changerait, et /journal/verify signalerait
    une corruption alors que rien n'a été modifié. Pour une date déjà en UTC le
    résultat est identique à l'ancien calcul : les hash existants restent valides.
    """
    if horodatage.tzinfo is None:
        horodatage = horodatage.replace(tzinfo=timezone.utc)
    horodatage_utc = horodatage.astimezone(timezone.utc)

    payload = (
        f"{id_utilisateur}|{id_ressource}|{type_action}|"
        f"{horodatage_utc.isoformat()}|{hash_precedent}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()