"""Runs all M3 checks automatically. Server must be running on port 8000.
Run from backend\ with the venv active:  python scripts\check_m3.py
"""
import getpass
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()
API = "http://localhost:8000/api"
SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_ANON_KEY"]

results = []


def check(name, ok, extra=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"   ({extra})" if not ok and extra else ""))


def sign_in(email, password):
    r = httpx.post(
        f"{SB_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SB_KEY},
        json={"email": email, "password": password},
        timeout=20,
    )
    if r.status_code != 200:
        sys.exit(f"Could not sign in as {email}: {r.text}")
    return r.json()["access_token"]


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


def sb_insert(token, table, rows):
    r = httpx.post(
        f"{SB_URL}/rest/v1/{table}",
        headers={**hdr(token), "apikey": SB_KEY, "Prefer": "return=representation"},
        json=rows,
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


print("Sign in (passwords are hidden while you type)")
a_email = input("User A email [usera@test.com]: ") or "usera@test.com"
a_pass = input("User A password (visible): ")
b_email = input("User B email [userb@test.com]: ") or "userb@test.com"
b_pass = input("User B password (visible): ")
A = sign_in(a_email, a_pass)
B = sign_in(b_email, b_pass)
print()

c = httpx.Client(base_url=API, timeout=20)
trip_id = None
try:
    # No token
    r = c.get("/trips")
    check("No token -> 401", r.status_code == 401, r.status_code)

    # Create
    body = {"destination": "Goa", "start_date": "2026-12-01", "end_date": "2026-12-05",
            "budget": 25000, "group_size": 2, "interests": ["beaches", "food"]}
    r = c.post("/trips", json=body, headers=hdr(A))
    check("A creates trip -> 201", r.status_code == 201, r.text)
    trip = r.json()
    trip_id = trip.get("id")
    check("Title defaults to 'Trip to Goa'", trip.get("title") == "Trip to Goa")
    check("Status is 'ready'", trip.get("status") == "ready")

    # Invalid dates
    bad = {**body, "start_date": "2026-12-05", "end_date": "2026-12-01"}
    r = c.post("/trips", json=bad, headers=hdr(A))
    check("End before start -> 422", r.status_code == 422, r.status_code)
    check("Error uses standard shape", r.json().get("error", {}).get("code") == "validation_error")

    # List
    r = c.get("/trips", headers=hdr(A))
    check("A lists trips, sees new trip", r.status_code == 200 and trip_id in [t["id"] for t in r.json()])

    # Get, no days yet
    r = c.get(f"/trips/{trip_id}", headers=hdr(A))
    check("A gets trip, empty days", r.status_code == 200 and r.json()["days"] == [])

    # Add days and activities (deliberately out of order, wrong day cost)
    d1 = sb_insert(A, "itinerary_days", {"trip_id": trip_id, "day_number": 1, "date": "2026-12-01",
                                         "summary": "Day one", "estimated_cost": 0})[0]
    d2 = sb_insert(A, "itinerary_days", {"trip_id": trip_id, "day_number": 2, "date": "2026-12-02",
                                         "summary": "Day two", "estimated_cost": 999})[0]
    sb_insert(A, "activities", [
        {"day_id": d1["id"], "position": 1, "type": "meal", "title": "Second", "estimated_cost": 50},
        {"day_id": d1["id"], "position": 0, "type": "attraction", "title": "First", "estimated_cost": 200},
    ])
    sb_insert(A, "activities", [
        {"day_id": d2["id"], "position": 0, "type": "other", "title": "Only", "estimated_cost": 100},
    ])
    r = c.get(f"/trips/{trip_id}", headers=hdr(A))
    t = r.json()
    check("Nested days in order", [d["day_number"] for d in t["days"]] == [1, 2])
    check("Activities in order", [x["title"] for x in t["days"][0]["activities"]] == ["First", "Second"])
    check("Day costs recomputed (250, 100)", [d["estimated_cost"] for d in t["days"]] == [250, 100])
    check("Trip total is 350", t["total_estimated_cost"] == 350)

    # Update
    r = c.patch(f"/trips/{trip_id}", json={"title": "Goa getaway"}, headers=hdr(A))
    check("A renames trip -> 200", r.status_code == 200 and r.json().get("title") == "Goa getaway")
    r = c.patch(f"/trips/{trip_id}", json={"end_date": "2027-01-30"}, headers=hdr(A))
    check("Too-long trip via PATCH -> 422", r.status_code == 422, r.status_code)

    # User B must be blocked
    r = c.get("/trips", headers=hdr(B))
    check("B list does not contain A's trip", r.status_code == 200 and trip_id not in [x["id"] for x in r.json()])
    r = c.get(f"/trips/{trip_id}", headers=hdr(B))
    check("B get A's trip -> 404", r.status_code == 404, r.status_code)
    r = c.patch(f"/trips/{trip_id}", json={"title": "Hacked"}, headers=hdr(B))
    check("B patch A's trip -> 404/403", r.status_code in (404, 403), r.status_code)
    r = c.delete(f"/trips/{trip_id}", headers=hdr(B))
    check("B delete A's trip -> 404", r.status_code == 404, r.status_code)
    r = c.get(f"/trips/{trip_id}", headers=hdr(A))
    check("Trip untouched after B's attempts", r.status_code == 200 and r.json()["title"] == "Goa getaway")

    # Delete
    r = c.delete(f"/trips/{trip_id}", headers=hdr(A))
    check("A deletes trip -> 204", r.status_code == 204, r.status_code)
    r = c.get(f"/trips/{trip_id}", headers=hdr(A))
    check("Deleted trip -> 404", r.status_code == 404, r.status_code)
    trip_id = None
except httpx.ConnectError:
    sys.exit("Cannot connect. Is the server running in the other tab?")
finally:
    if trip_id:
        c.delete(f"/trips/{trip_id}", headers=hdr(A))

print(f"\n{sum(results)} of {len(results)} checks passed")