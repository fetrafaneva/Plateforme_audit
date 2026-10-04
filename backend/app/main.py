from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyse import router as analyse_router
from app.api.auth import router as auth_router
from app.api.journal import router as journal_router
from app.api.missions import (
    router as missions_router,
    axes_router,
    equipes_router,
    participants_router,
    districts_router,
)
from app.core.config import settings

app = FastAPI(title="Plateforme d'audit comportemental")

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


@app.get("/health")
def health_check():
    return {"status": "ok"}