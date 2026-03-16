"""
FastAPI application entry point for the AI Consciousness & Metacognition Evaluation System.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from app.config import APP_TITLE, APP_VERSION, PORTER_CREDIT, SCIENTIFIC_DISCLAIMER, BASE_DIR
from app.storage.database import init_db
from app.routes.evaluation import router as eval_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting AI Consciousness Evaluation System...")
    # Initialize database
    init_db()
    logger.info("Database initialized.")
    # Load sample session if DB is fresh
    _ensure_sample_session()
    logger.info("App ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=f"{SCIENTIFIC_DISCLAIMER}\n\n{PORTER_CREDIT}",
    lifespan=lifespan,
)

# CORS (for dev/API access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Register evaluation API routes
app.include_router(eval_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def serve_spa(request: Request):
    """Serve the single-page application."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_title": APP_TITLE,
            "porter_credit": PORTER_CREDIT,
            "disclaimer": SCIENTIFIC_DISCLAIMER,
            "version": APP_VERSION,
        },
    )


def _ensure_sample_session():
    """Load sample session into DB if it doesn't already exist."""
    import json
    from app.storage.session_store import list_sessions, create_session, update_session
    from app.config import SAMPLE_SESSIONS_DIR

    sample_path = SAMPLE_SESSIONS_DIR / "sample_session.json"
    if not sample_path.exists():
        return

    sessions = list_sessions()
    if any(s.get("is_demo") for s in sessions):
        return  # Demo already loaded

    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            sample = json.load(f)

        uid = create_session({**sample.get("metadata", {}), "is_demo": True})
        update_session(uid, {
            "selected_questions": sample.get("selected_questions", []),
            "answers": sample.get("answers", {}),
            "porter_result": sample.get("porter_result", {}),
            "indicator_scores": sample.get("indicator_scores", {}),
            "overall_score": sample.get("overall_score", 0),
            "adjusted_score": sample.get("adjusted_score", 0),
            "reliability_label": sample.get("reliability_label", "Medium"),
            "reliability_score": sample.get("reliability_score", 0.6),
            "narrative_summary": sample.get("narrative_summary", ""),
            "full_analysis": sample.get("full_analysis", {}),
        })
        logger.info(f"Sample session loaded: {uid}")
    except Exception as e:
        logger.warning(f"Could not load sample session: {e}")
