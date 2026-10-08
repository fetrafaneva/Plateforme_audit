from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.base import get_db
from app.models.identity import Role, ServiceCommune, Utilisateur
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut, UserMeOut

router = APIRouter(prefix="/auth", tags=["authentification"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("administrateur"))],
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    ...
    existing = db.query(Utilisateur).filter(Utilisateur.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    if not db.query(Role).filter(Role.id_role == payload.id_role).first():
        raise HTTPException(status_code=400, detail="Rôle introuvable")

    if not db.query(ServiceCommune).filter(ServiceCommune.id_service == payload.id_service).first():
        raise HTTPException(status_code=400, detail="Service/commune introuvable")

    user = Utilisateur(
        nom=payload.nom,
        prenom=payload.prenom,
        email=payload.email,
        matricule=payload.matricule,
        mot_de_passe_hash=hash_password(payload.mot_de_passe),
        id_service=payload.id_service,
        id_role=payload.id_role,
        statut="actif",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(Utilisateur).filter(Utilisateur.email == payload.email).first()
    if not user or not verify_password(payload.mot_de_passe, user.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if user.statut != "actif":
        raise HTTPException(status_code=403, detail="Compte désactivé")

    access_token = create_access_token(data={"sub": str(user.id_utilisateur)})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserMeOut)
def read_current_user(current_user: Utilisateur = Depends(get_current_user)):
    return UserMeOut(
        **UserOut.model_validate(current_user).model_dump(),
        role=current_user.role.nom_role,
    )