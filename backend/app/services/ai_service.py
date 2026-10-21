import json
import os
from datetime import date, time, timedelta
from pathlib import Path

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
ALLOWED_TYPES = {"attraction", "meal", "stay", "transport", "other"}


def _env(name: str, default: str = "") -> str:
    """Read from the environment, then fall back to backend/.env."""
    value = os.environ.get(name)
    if value:
        return value
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == name:
                return val.strip().strip('"').strip("'") or default
    return default


class GenActivity(BaseModel):
    type: str = "other"
    title: str
    description: str | None = None
    location_name: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    estimated_cost: float = 0

    @field_validator("type", mode="before")
    @classmethod
    def type_ok(cls, v):
        v = str(v or "other").strip().lower()
        return v if v in ALLOWED_TYPES else "other"

    @field_validator("title", mode="before")
    @classmethod
    def title_ok(cls, v):
        v = str(v or "").strip()[:200]
        if not v:
            raise ValueError("title required")
        return v

    @field_validator("description", mode="before")
    @classmethod
    def desc_ok(cls, v):
        return str(v).strip()[:2000] if v else None

    @field_validator("location_name", mode="before")
    @classmethod
    def loc_ok(cls, v):
        return str(v).strip()[:200] if v else None

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def time_ok(cls, v):
        if not v:
            return None
        try:
            h, m = str(v).strip().split(":")[:2]
            return time(int(h), int(m))
        except Exception:
            return None

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def cost_ok(cls, v):
        try:
            return max(0.0, float(v))
        except Exception:
            return 0.0


class GenDay(BaseModel):
    summary: str | None = None
    activities: list[GenActivity] = Field(min_length=1)


class GenItinerary(BaseModel):
    days: list[GenDay] = Field(min_length=1)


def _build_prompt(trip: dict, num_days: int, only_day: int | None = None) -> str:
    interests = ", ".join(trip.get("interests") or []) or "general sightseeing"
    return f"""You are a travel planner. Create a {num_days}-day itinerary.

Destination: {trip['destination']}
Dates: {trip['start_date']} to {trip['end_date']}
Total budget for the whole group: {trip['budget']} {trip['currency']}
Group size: {trip['group_size']}
Travel style: {trip['travel_style']} (relaxed = 3 activities/day, balanced = 4-5, packed = 6-7)
Interests: {interests}
Notes: {trip.get('notes') or 'none'}

Rules:
- Return EXACTLY {num_days} days, in order.
- Each activity "estimated_cost" is the TOTAL cost for the whole group in {trip['currency']}. Use 0 for free things.
- Keep the total cost within the budget.
- "type" must be one of: attraction, meal, stay, transport, other.
- Times are 24-hour "HH:MM". end_time must be after start_time.
- Use real places in {trip['destination']}.
- Keep every "description" under 20 words and every "summary" under 15 words.

Return ONLY JSON in this exact shape:
{{"days":[{{"summary":"one sentence","activities":[{{"type":"attraction","title":"...","description":"...","location_name":"...","start_time":"09:00","end_time":"11:00","estimated_cost":500}}]}}]}}"""


def _call_gemini(prompt: str) -> str:
    key = _env("LLM_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not set")
    model = _env("LLM_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        },
    }
    try:
        res = httpx.post(url, json=body, headers={"x-goog-api-key": key}, timeout=90)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI request failed: {e}")
    if res.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"AI provider error {res.status_code}: {res.text[:300]}"
        )
    data = res.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ValueError("AI returned no text")


def _call_llm(prompt: str) -> str:
    provider = _env("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return _call_gemini(prompt)
    raise HTTPException(status_code=500, detail=f"Unsupported LLM_PROVIDER: {provider}")


def generate_itinerary(trip: dict, num_days: int) -> GenItinerary:
    """Calls the LLM, validates the JSON, retries once on bad output."""
    prompt = _build_prompt(trip, num_days)
    last_error = "unknown"
    for _ in range(2):
        try:
            text = _call_llm(prompt).strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = GenItinerary.model_validate(json.loads(text))
            if len(result.days) < num_days:
                raise ValueError(f"expected {num_days} days, got {len(result.days)}")
            result.days = result.days[:num_days]
            return result
        except HTTPException:
            raise
        except (ValueError, ValidationError, json.JSONDecodeError) as e:
            last_error = str(e)[:200]
    raise HTTPException(
        status_code=502, detail=f"AI returned invalid itinerary twice: {last_error}"
    )
    

def _build_day_prompt(
    trip: dict, day_number: int, num_days: int, avoid_titles: list[str]
) -> str:
    interests = ", ".join(trip.get("interests") or []) or "general sightseeing"
    day_date = date.fromisoformat(str(trip["start_date"])[:10]) + timedelta(days=day_number - 1)
    per_day_budget = round(float(trip["budget"]) / max(num_days, 1))
    avoid = "; ".join(avoid_titles[:30]) or "none"
    return f"""You are a travel planner. Create ONE new day (day {day_number} of {num_days}) of an itinerary.

Destination: {trip['destination']}
Date of this day: {day_date}
Total trip budget for the whole group: {trip['budget']} {trip['currency']} (about {per_day_budget} {trip['currency']} per day)
Group size: {trip['group_size']}
Travel style: {trip['travel_style']} (relaxed = 3 activities/day, balanced = 4-5, packed = 6-7)
Interests: {interests}
Notes: {trip.get('notes') or 'none'}

Do NOT repeat any of these places or activities from the other days: {avoid}

Rules:
- Each activity "estimated_cost" is the TOTAL cost for the whole group in {trip['currency']}. Use 0 for free things.
- Keep this day's total near {per_day_budget} {trip['currency']} or less.
- "type" must be one of: attraction, meal, stay, transport, other.
- Times are 24-hour "HH:MM". end_time must be after start_time.
- Use real places in {trip['destination']}.
- Keep every "description" under 20 words and the "summary" under 15 words.

Return ONLY JSON in this exact shape:
{{"summary":"one sentence","activities":[{{"type":"attraction","title":"...","description":"...","location_name":"...","start_time":"09:00","end_time":"11:00","estimated_cost":500}}]}}"""


def generate_single_day(
    trip: dict, day_number: int, num_days: int, avoid_titles: list[str] | None = None
) -> GenDay:
    """Asks the LLM for one replacement day. Retries once on bad output."""
    prompt = _build_day_prompt(trip, day_number, num_days, avoid_titles or [])
    last_error = "unknown"
    for _ in range(2):
        try:
            text = _call_llm(prompt).strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return GenDay.model_validate(json.loads(text))
        except HTTPException:
            raise
        except (ValueError, ValidationError, json.JSONDecodeError) as e:
            last_error = str(e)[:200]
    raise HTTPException(
        status_code=502, detail=f"AI returned invalid day twice: {last_error}"
    )