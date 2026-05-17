from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
import json
import io
import secrets
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeTimedSerializer

# Fix for Windows console emoji printing (UnicodeEncodeError)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add root directory to sys.path to ensure we can import agents
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.compression_path.parser_core import orchestrate_pipeline
from conexiones.conexion_uriel_antonio import generar_analisis

app = FastAPI(title="GitHub Repository Extractor API")

# Environment variables
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_hex(32))

# Session serializer for secure token storage
serializer = URLSafeTimedSerializer(SESSION_SECRET_KEY)

# In-memory storage for user sessions (use Redis in production)
user_sessions: Dict[str, dict] = {}
task_results: Dict[str, dict] = {}

# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define what data we expect to receive from frontend
class RepoRequest(BaseModel):
    github_token: str
    repository: str
    branch: Optional[str] = None
    filters: Optional[dict] = None
    extensions: Optional[List[str]] = None

@app.get("/")
def home():
    return {"message": "GitHub Repository Extractor API"}

# ============================================
# OAUTH 2.0 ENDPOINTS
# ============================================

@app.get("/auth/github")
async def github_login():
    """Initiate GitHub OAuth flow"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build GitHub authorization URL
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/auth/github/callback",
        "scope": "repo read:user",
        "state": state
    }
    
    github_auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    return RedirectResponse(url=github_auth_url)

@app.get("/auth/github/callback")
async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback"""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    try:
        # Exchange code for access token
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{BACKEND_URL}/auth/github/callback"
            }
        )
        
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth failed"))
        
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        user_data = user_response.json()
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        user_sessions[session_id] = {
            "github_token": access_token,
            "username": user_data.get("login"),
            "user_id": user_data.get("id")
        }
        
        # Redirect to frontend with session ID
        redirect_url = f"{FRONTEND_URL}/procesando?session={session_id}"
        return RedirectResponse(url=redirect_url)
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")

@app.get("/auth/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    session = user_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "username": session.get("username"),
        "authenticated": True
    }

# ============================================
# EXTRACTION ENDPOINTS
# ============================================

class ExtractionRequest(BaseModel):
    session_id: str
    repository: str
    branch: Optional[str] = None

@app.post("/api/extract")
async def extract_repository(request: ExtractionRequest):
    """Extract repository using OAuth session"""
    # Get session
    session = user_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    github_token = session.get("github_token")
    
    try:
        # Generate task ID
        task_id = secrets.token_urlsafe(16)
        
        # Store initial task status
        task_results[task_id] = {
            "status": "processing",
            "repository": request.repository,
            "progress": 0
        }
        
        # Start extraction in background (simplified for now)
        output_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "compression_path", "para_uriel.json")
        
        # Step 1: Extract and compress repository
        orchestrate_pipeline(
            repository=request.repository,
            github_token=github_token,
            output_file=output_json,
            max_workers=2
        )
        
        task_results[task_id]["status"] = "analyzing"
        task_results[task_id]["progress"] = 50
        
        # Step 2: Analyze with AI and generate documentation
        frontend_docs = generar_analisis(project_name=request.repository)
        
        # Store results
        task_results[task_id] = {
            "status": "completed",
            "repository": request.repository,
            "progress": 100,
            "result": frontend_docs
        }
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": frontend_docs
        }
        
    except Exception as e:
        if task_id:
            task_results[task_id] = {
                "status": "failed",
                "error": str(e)
            }
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """Get extraction task status"""
    task = task_results.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@app.get("/api/results/{task_id}")
async def get_task_results(task_id: str):
    """Get extraction results"""
    task = task_results.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    return task.get("result", {})