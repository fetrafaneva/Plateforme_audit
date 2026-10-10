from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.analyse import router as analyse_router
from app.api.auth import router as auth_router
from app.api.journal import router as journal_router
from app.api.audit import router as audit_router
from app.api.utilisateurs import router as utilisateurs_router
from app.api.missions import (
    router as missions_router,
    axes_router,
    equipes_router,
    participants_router,
    districts_router,
    missions_districts_router,
    types_activite_router,
    phases_router,
    journees_router,
    livrables_router,
    indicateurs_router,
)
from app.core.config import settings

app = FastAPI(title="Plateforme d'audit comportemental")

@app.exception_handler(IntegrityError)
def handle_integrity_error(request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Donnée invalide : référence inexistante ou valeur en double."},
    )
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(journal_router)
app.include_router(analyse_router)
app.include_router(missions_router)
app.include_router(axes_router)
app.include_router(equipes_router)
app.include_router(participants_router)
app.include_router(districts_router)
app.include_router(missions_districts_router)
app.include_router(types_activite_router)
app.include_router(phases_router)
app.include_router(journees_router)
app.include_router(livrables_router)
app.include_router(indicateurs_router)
app.include_router(audit_router)
app.include_router(utilisateurs_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}