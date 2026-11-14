"""Adresse IP du client, lue côté serveur.

Règle : l'adresse enregistrée dans le journal, dans les tentatives de connexion ou dans
les traces d'audit vient de la connexion réelle, jamais d'une valeur envoyée par le
client (corps de la requête ou en-tête quelconque), car il pourrait y mettre n'importe quoi.

Derrière un proxy inverse (nginx...), `request.client.host` est l'adresse du proxy. Uvicorn
remplace cette valeur par celle de l'en-tête X-Forwarded-For seulement si la connexion
vient d'un proxy de confiance (option `--forwarded-allow-ips`, par défaut 127.0.0.1).
Ne lis donc jamais cet en-tête toi-même.
"""

from fastapi import Request


def ip_du_client(request: Request) -> str:
    return request.client.host if request.client else "inconnue"