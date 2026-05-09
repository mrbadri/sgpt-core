"""HTTP ingress for Bale platform updates (webhook mode).

Long-polling is started from ``app.main`` via ``integrations.bale.bot_service``;
register routes here when switching to webhook delivery.
"""

from fastapi import APIRouter

router = APIRouter()
