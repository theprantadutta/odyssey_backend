"""API v1 routes"""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    auth_google,
    trips,
    activities,
    memories,
    expenses,
    packing,
    documents,
    sharing,
    templates,
    weather,
    currency,
    achievements,
    statistics,
    seed,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(auth_google.router, prefix="/auth", tags=["google-auth"])
# Sharing router must be registered BEFORE trips router
# because it has routes like /trips/shared-with-me that would otherwise
# be caught by trips router's /{trip_id} route
api_router.include_router(sharing.router, tags=["sharing"])
api_router.include_router(trips.router, prefix="/trips", tags=["trips"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(packing.router, prefix="/packing", tags=["packing"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(weather.router, tags=["weather"])
api_router.include_router(currency.router, tags=["currency"])
api_router.include_router(achievements.router, tags=["achievements"])
api_router.include_router(statistics.router, tags=["statistics"])
api_router.include_router(seed.router, prefix="/seed", tags=["seed"])
