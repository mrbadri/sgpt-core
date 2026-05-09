"""Aggregate routers for API version 1 (web and mobile clients)."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

router = APIRouter()

router.include_router(health.router)
