"""
Quick start script for running the Odyssey backend
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Odyssey Backend API")
    print("=" * 60)
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"Database: {settings.DATABASE_HOST}/{settings.DATABASE_NAME}")
    print(f"API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Debug: {settings.DEBUG}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
