from fastapi import FastAPI

app = FastAPI(title="Travel Itinerary Planner API")


@app.get("/api/health")
def health():
    return {"status": "ok"}