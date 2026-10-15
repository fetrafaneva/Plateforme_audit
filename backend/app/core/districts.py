"""Import de districts depuis un fichier CSV.

Colonnes acceptées (la première ligne contient les noms de colonnes) :
    nom (obligatoire), region, province, electrifie (oui/non)
Le séparateur est « ; » ou « , », l'encodage UTF-8 (avec ou sans BOM) ou Windows-1252.
"""

import csv
import io

from sqlalchemy.orm import Session

from app.models.missions import District

OUI = {"oui", "o", "true", "vrai", "1", "x", "yes"}
ALIAS = {"région": "region"}


def normaliser(texte: str | None) -> str:
    """Forme de comparaison d'un nom : espaces réduits, sans différence de casse."""
    return " ".join((texte or "").split()).casefold()


def lire_csv(contenu: bytes) -> list[dict]:
    try:
        texte = contenu.decode("utf-8-sig")
    except UnicodeDecodeError:
        texte = contenu.decode("cp1252")

    echantillon = texte[:2048]
    delimiteur = ";" if echantillon.count(";") >= echantillon.count(",") else ","
    lecteur = csv.DictReader(io.StringIO(texte), delimiter=delimiteur)

    colonnes = {}
    for brute in lecteur.fieldnames or []:
        cle = (brute or "").strip().lower()
        colonnes[ALIAS.get(cle, cle)] = brute
    if "nom" not in colonnes:
        raise ValueError(
            "La colonne « nom » est obligatoire. Colonnes acceptées : nom, region, province, electrifie."
        )

    def valeur(ligne: dict, cle: str) -> str:
        brute = colonnes.get(cle)
        return (ligne.get(brute) or "").strip() if brute else ""

    return [
        {
            "nom": valeur(ligne, "nom"),
            "region": valeur(ligne, "region") or None,
            "province": valeur(ligne, "province") or None,
            "electrifie": valeur(ligne, "electrifie").lower() in OUI,
        }
        for ligne in lecteur
    ]


def importer_districts(db: Session, lignes: list[dict]) -> dict:
    """Ajoute les districts absents. Ne valide pas la transaction (commit par l'appelant)."""
    connus = {normaliser(nom) for (nom,) in db.query(District.nom).all()}
    crees = ignores = 0
    erreurs: list[str] = []

    for numero, ligne in enumerate(lignes, start=2):  # la ligne 1 est l'en-tête
        nom = " ".join(ligne["nom"].split())
        if not nom:
            erreurs.append(f"Ligne {numero} : le nom est vide")
            continue
        if len(nom) > 200:
            erreurs.append(f"Ligne {numero} : nom trop long")
            continue
        if normaliser(nom) in connus:
            ignores += 1
            continue
        connus.add(normaliser(nom))
        db.add(
            District(
                nom=nom,
                region=ligne.get("region"),
                province=ligne.get("province"),
                electrifie=bool(ligne.get("electrifie")),
            )
        )
        crees += 1

    return {"crees": crees, "ignores": ignores, "erreurs": erreurs[:50]}