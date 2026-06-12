import os
import logging
import platform

# Prevent Windows WMI/COM hang in python's platform module
platform.win32_ver = lambda *a, **k: ('10', '10.0.22631', '', 'Multiprocessor Free')
platform.system = lambda *a, **k: 'Windows'
def _mock_uname(*a, **k):
    from collections import namedtuple
    UnameResult = namedtuple('uname_result', 'system node release version machine processor')
    return UnameResult(system='Windows', node='DESKTOP', release='10', version='10.0.22631', machine='AMD64', processor='Intel')
platform.uname = _mock_uname
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.agent.movie_agent import run_movie_agent

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Interactive Movie Recommendation Agent",
    description="A ReAct Agent that translates query constraints and searches TMDB/local DB for recommendations.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str = Field(..., description="The recommendation query, e.g., 'Recommend a horror movie from the 90s rated R.'")

class StatusResponse(BaseModel):
    status: str
    gemini_key_configured: bool
    tmdb_key_configured: bool

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Check if API Keys are configured in the environment."""
    gemini_configured = False
    try:
        settings.get_gemini_api_key()
        gemini_configured = True
    except ValueError:
        pass
        
    return {
        "status": "healthy",
        "gemini_key_configured": gemini_configured,
        "tmdb_key_configured": settings.TMDB_API_KEY is not None and len(settings.TMDB_API_KEY) > 0
    }

@app.post("/api/recommend")
async def recommend_movies(payload: QueryRequest):
    """
    Run the ReAct agent on the user's movie query and return
    the reasoning steps, final recommendation, and structured movie metadata.
    """
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        # Check API key first
        settings.get_gemini_api_key()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    logger.info(f"Received recommendation request: {payload.query}")
    result = run_movie_agent(payload.query)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
        
    return result

# --- Mount Static Frontend ---
# Make sure frontend folders exist
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
static_dir = os.path.join(frontend_dir, "static")
os.makedirs(static_dir, exist_ok=True)

# Serve static files (style.css, app.js, etc.)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    """Serve the single-page application index.html."""
    index_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_path):
        # Create a dummy index file if it doesn't exist yet
        logger.warning("index.html not found, serving default message.")
        return {"message": "Frontend files are loading. Please refresh in a moment."}
    return FileResponse(index_path)
