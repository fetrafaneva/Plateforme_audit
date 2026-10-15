"""Administration des référentiels : districts et types d'activité.

La création et la liste existent déjà dans api/missions.py (POST et GET /districts/,
/types-activite/). Ce module ajoute l'import CSV, la modification et la suppression,
réservées à l'administrateur. Une suppression est refusée tant que l'élément est utilisé.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.districts import importer_districts, lire_csv, normaliser
from app.db.base import get_db
from app.models.missions import District, MissionDistrict, Phase, TypeActivite
from app.schemas.missions import DistrictOut, TypeActiviteOut
from app.schemas.referentiels import DistrictUpdate, ImportDistrictsOut, TypeActiviteUpdate

router = APIRouter(tags=["référentiels"], dependencies=[Depends(require_role("administrateur"))])

TAILLE_MAX_IMPORT = 1024 * 1024  # 1 Mo
LIGNES_MAX_IMPORT = 1000


@router.post("/districts/import", response_model=ImportDistrictsOut)
def importer_fichier_districts(fichier: UploadFile = File(...), db: Session = Depends(get_db)):
    contenu = fichier.file.read(TAILLE_MAX_IMPORT + 1)
    if len(contenu) > TAILLE_MAX_IMPORT:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (1 Mo maximum)")
    try:
        lignes = lire_csv(contenu)
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))
    if len(lignes) > LIGNES_MAX_IMPORT:
        raise HTTPException(status_code=400, detail=f"{LIGNES_MAX_IMPORT} lignes au maximum")

    resultat = importer_districts(db, lignes)
    db.commit()
    return resultat


@router.patch("/districts/{id_district}", response_model=DistrictOut)
def modifier_district(id_district: int, payload: DistrictUpdate, db: Session = Depends(get_db)):
    district = db.get(District, id_district)
    if district is None:
        raise HTTPException(status_code=404, detail="District introuvable")

    modifications = payload.model_dump(exclude_unset=True)
    if "nom" in modifications:
        modifications["nom"] = " ".join(modifications["nom"].split())
        if not modifications["nom"]:
            raise HTTPException(status_code=400, detail="Le nom ne peut pas être vide")
        autres = db.query(District).filter(District.id != id_district).all()
        if any(normaliser(d.nom) == normaliser(modifications["nom"]) for d in autres):
            raise HTTPException(status_code=400, detail="Un district porte déjà ce nom")
    for champ, valeur in modifications.items():
        setattr(district, champ, valeur)
    db.commit()
    db.refresh(district)
    return district


@router.delete("/districts/{id_district}", status_code=204)
def supprimer_district(id_district: int, db: Session = Depends(get_db)):
    district = db.get(District, id_district)
    if district is None:
        raise HTTPException(status_code=404, detail="District introuvable")
    utilise = (
        db.query(func.count(MissionDistrict.id))
        .filter(MissionDistrict.district_id == id_district)
        .scalar()
    )
    if utilise:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible : ce district est lié à {utilise} axe(s) de mission",
        )
    db.delete(district)
    db.commit()


@router.patch("/types-activite/{id_type}", response_model=TypeActiviteOut)
def modifier_type_activite(id_type: int, payload: TypeActiviteUpdate, db: Session = Depends(get_db)):
    type_activite = db.get(TypeActivite, id_type)
    if type_activite is None:
        raise HTTPException(status_code=404, detail="Type d'activité introuvable")
    libelle = " ".join(payload.libelle.split())
    if not libelle:
        raise HTTPException(status_code=400, detail="Le libellé ne peut pas être vide")
    autres = db.query(TypeActivite).filter(TypeActivite.id != id_type).all()
    if any(normaliser(t.libelle) == normaliser(libelle) for t in autres):
        raise HTTPException(status_code=400, detail="Un type d'activité porte déjà ce libellé")
    type_activite.libelle = libelle
    db.commit()
    db.refresh(type_activite)
    return type_activite


@router.delete("/types-activite/{id_type}", status_code=204)
def supprimer_type_activite(id_type: int, db: Session = Depends(get_db)):
    type_activite = db.get(TypeActivite, id_type)
    if type_activite is None:
        raise HTTPException(status_code=404, detail="Type d'activité introuvable")
    utilise = (
        db.query(func.count(Phase.id)).filter(Phase.type_activite_id == id_type).scalar()
    )
    if utilise:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible : ce type d'activité est utilisé par {utilise} phase(s)",
        )
    db.delete(type_activite)
    db.commit()