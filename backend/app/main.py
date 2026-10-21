import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.routers import activities, health, me, trips

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app.request")

settings = get_settings()

app = FastAPI(title="Travel Itinerary Planner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s -> %s (%.0f ms)",
        request_id, request.method, request.url.path, response.status_code, ms,
    )
    return response


app.include_router(health.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(trips.router, prefix="/api")
app.include_router(activities.router, prefix="/api")
from fastapi.responses import RedirectResponse


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")