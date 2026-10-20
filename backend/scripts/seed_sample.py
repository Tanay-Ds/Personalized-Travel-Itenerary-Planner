"""Creates a hand-written sample trip for usera@test.com.

Run from backend\ with the venv active:
    python scripts\seed_sample.py

It signs in as usera, so RLS applies exactly as it does for the real app.
Password comes from the SEED_PASSWORD environment variable (set below).
"""
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

EMAIL = os.environ.get("SEED_EMAIL", "usera@test.com")
PASSWORD = os.environ.get("SEED_PASSWORD")
if not PASSWORD:
    sys.exit("Set SEED_PASSWORD first. In PowerShell: $env:SEED_PASSWORD='your-usera-password'")

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
session = client.auth.sign_in_with_password({"email": EMAIL, "password": PASSWORD})
user_id = session.user.id

trip = (
    client.table("trips")
    .insert(
        {
            "owner_id": user_id,
            "title": "Sample: Jaipur weekend",
            "destination": "Jaipur",
            "start_date": "2026-11-14",
            "end_date": "2026-11-15",
            "budget": 15000,
            "currency": "INR",
            "group_size": 2,
            "travel_style": "balanced",
            "interests": ["history", "food"],
            "status": "ready",
        }
    )
    .execute()
    .data[0]
)

plan = [
    {
        "day_number": 1,
        "date": "2026-11-14",
        "summary": "Forts and old city",
        "activities": [
            ("meal", "Breakfast at hotel", "Hotel", "08:00", "09:00", 400, 26.9124, 75.7873),
            ("attraction", "Amber Fort", "Amber Fort", "09:30", "12:30", 1000, 26.9855, 75.8513),
            ("meal", "Lunch at Laxmi Misthan Bhandar", "Johari Bazaar", "13:00", "14:00", 800, 26.9196, 75.8235),
            ("attraction", "City Palace", "City Palace", "15:00", "17:30", 1400, 26.9258, 75.8237),
            ("meal", "Dinner at Chokhi Dhani", "Chokhi Dhani", "19:30", "21:30", 2400, 26.7721, 75.8456),
        ],
    },
    {
        "day_number": 2,
        "date": "2026-11-15",
        "summary": "Hawa Mahal and shopping",
        "activities": [
            ("attraction", "Hawa Mahal", "Hawa Mahal", "09:00", "10:30", 400, 26.9239, 75.8267),
            ("attraction", "Jantar Mantar", "Jantar Mantar", "10:45", "12:00", 500, 26.9247, 75.8246),
            ("meal", "Lunch at Rawat Misthan Bhandar", "Station Road", "12:30", "13:30", 700, 26.9189, 75.7915),
            ("other", "Shopping at Bapu Bazaar", "Bapu Bazaar", "15:00", "17:00", 1500, 26.9170, 75.8000),
            ("transport", "Taxi to railway station", "Jaipur Junction", "18:00", "18:45", 500, 26.9196, 75.7878),
        ],
    },
]

for d in plan:
    day_cost = sum(a[5] for a in d["activities"])
    day = (
        client.table("itinerary_days")
        .insert(
            {
                "trip_id": trip["id"],
                "day_number": d["day_number"],
                "date": d["date"],
                "summary": d["summary"],
                "estimated_cost": day_cost,
            }
        )
        .execute()
        .data[0]
    )
    rows = [
        {
            "day_id": day["id"],
            "position": i,
            "type": a[0],
            "title": a[1],
            "location_name": a[2],
            "start_time": a[3],
            "end_time": a[4],
            "estimated_cost": a[5],
            "lat": a[6],
            "lng": a[7],
        }
        for i, a in enumerate(d["activities"])
    ]
    client.table("activities").insert(rows).execute()

print(f"Created trip {trip['id']} with {len(plan)} days.")