"""Seed data endpoints"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from faker import Faker
from datetime import datetime, timedelta
from decimal import Decimal
import random
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.activity import Activity
from app.models.memory import Memory

router = APIRouter()
fake = Faker()

# Sample Unsplash image URLs for trips
SAMPLE_TRIP_IMAGES = [
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800",  # Nature landscape
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",  # Mountain
    "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=800",  # Beach
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800",  # Lake
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800",  # Paris
    "https://images.unsplash.com/photo-1504019347908-b45f9b0b8dd5?w=800",  # City skyline
]

# Sample memory image URLs
SAMPLE_MEMORY_IMAGES = [
    "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=400",
    "https://images.unsplash.com/photo-1464207687429-7505649dae38?w=400",
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=400",
    "https://images.unsplash.com/photo-1519904981063-b0cf448d479e?w=400",
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=400",
]

ACTIVITY_CATEGORIES = ["food", "travel", "stay", "explore"]
TRIP_STATUSES = ["planned", "ongoing", "completed"]


@router.post("/demo-data", status_code=status.HTTP_201_CREATED)
async def create_demo_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate sample trips, activities, and memories for demo/testing

    Creates:
    - 5 sample trips with realistic data
    - 3-5 activities per trip
    - 2-4 memories (photo locations) per trip

    **Note:** This endpoint is for demo purposes only
    """
    created_trips = []

    # Create 5 sample trips
    for i in range(5):
        # Generate dates
        start_date = fake.date_between(start_date='-6M', end_date='+6M')
        end_date = start_date + timedelta(days=random.randint(3, 14))

        # Create trip
        trip = Trip(
            user_id=current_user.id,
            title=f"{fake.city()} Adventure",
            description=fake.paragraph(nb_sentences=3),
            cover_image_url=random.choice(SAMPLE_TRIP_IMAGES),
            start_date=start_date,
            end_date=end_date,
            status=random.choice(TRIP_STATUSES),
            tags=[fake.word(), fake.word(), fake.word()]
        )
        db.add(trip)
        db.flush()  # Get the trip ID

        # Create 3-5 activities for this trip
        num_activities = random.randint(3, 5)
        for j in range(num_activities):
            activity_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            activity_time = datetime.combine(
                activity_date,
                datetime.min.time().replace(
                    hour=random.randint(8, 20),
                    minute=random.choice([0, 15, 30, 45])
                )
            )

            activity = Activity(
                trip_id=trip.id,
                title=fake.sentence(nb_words=4).rstrip('.'),
                description=fake.paragraph(nb_sentences=2),
                scheduled_time=activity_time,
                category=random.choice(ACTIVITY_CATEGORIES),
                sort_order=j,
                latitude=Decimal(str(fake.latitude())),
                longitude=Decimal(str(fake.longitude()))
            )
            db.add(activity)

        # Create 2-4 memories for this trip
        num_memories = random.randint(2, 4)
        for k in range(num_memories):
            memory_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            memory_time = datetime.combine(
                memory_date,
                datetime.min.time().replace(hour=random.randint(9, 18))
            )

            memory = Memory(
                trip_id=trip.id,
                photo_url=random.choice(SAMPLE_MEMORY_IMAGES),
                latitude=Decimal(str(fake.latitude())),
                longitude=Decimal(str(fake.longitude())),
                caption=fake.sentence(),
                taken_at=memory_time
            )
            db.add(memory)

        created_trips.append({
            "id": str(trip.id),
            "title": trip.title,
            "status": trip.status
        })

    db.commit()

    return {
        "message": "Demo data created successfully",
        "created_trips": created_trips,
        "total_trips": len(created_trips),
        "total_activities": sum([random.randint(3, 5) for _ in range(5)]),
        "total_memories": sum([random.randint(2, 4) for _ in range(5)])
    }
