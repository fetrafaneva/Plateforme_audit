from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    matricule: str
    mot_de_passe: str
    id_service: int
    id_role: int


class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str


class UserOut(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: str
    email: EmailStr
    matricule: str
    id_service: int
    id_role: int
    statut: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"