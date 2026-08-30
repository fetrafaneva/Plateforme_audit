from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.journal import router as journal_router
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


@app.get("/health")
def health_check():
    return {"status": "ok"}