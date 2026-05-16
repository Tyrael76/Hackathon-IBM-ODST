from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json
import io

# Fix for Windows console emoji printing (UnicodeEncodeError)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add root directory to sys.path to ensure we can import agents
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.compression_path.parser_core import orchestrate_pipeline
from conexiones.conexion_uriel_antonio import generar_analisis

app = FastAPI(title="GitHub Extractor API for Bob")

# CORS CONFIGURATION: Essential for Rafiki's frontend to not be blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific URL in production
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
    return {"message": "Extraction Server Active"}

@app.post("/extract")
async def extract_repository(request: RepoRequest):
    """
    Receives token, repo and extensions from frontend.
    """
    try:
        output_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "compression_path", "para_uriel.json")
        
        # Step 1: Extract and compress repository
        orchestrate_pipeline(
            repository=request.repository,
            github_token=request.github_token,
            output_file=output_json,
            max_workers=2 # keep workers reasonable to avoid heavy CPU usage
        )
        
        # Step 2: Analyze with AI and generate documentation
        frontend_docs = generar_analisis(project_name=request.repository)
            
        return {
            "status": "success",
            "repo": request.repository,
            "frontend_docs": frontend_docs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))