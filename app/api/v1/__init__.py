"""API v1 routes"""
from fastapi import APIRouter
from app.api.v1 import auth, trips, activities, memories, expenses, packing, seed

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(trips.router, prefix="/trips", tags=["trips"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(packing.router, prefix="/packing", tags=["packing"])
api_router.include_router(seed.router, prefix="/seed", tags=["seed"])
