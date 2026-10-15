from pydantic import BaseModel, Field


class DistrictUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=200)
    region: str | None = Field(default=None, max_length=200)
    province: str | None = Field(default=None, max_length=200)
    electrifie: bool | None = None


class TypeActiviteUpdate(BaseModel):
    libelle: str = Field(min_length=1, max_length=200)


class ImportDistrictsOut(BaseModel):
    crees: int
    ignores: int  # déjà présents (même nom) ou répétés dans le fichier
    erreurs: list[str]