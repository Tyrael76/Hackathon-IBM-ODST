from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
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
    extensions: List[str] | None = None

@app.get("/")
def home():
    return {"message": "Extraction Server Active"}

@app.post("/extract")
async def extract_repository(request: RepoRequest):
    """
    Receives token, repo and extensions from frontend.
    """
    try:
        # Run the complete pipeline (Fetch, Compress, AI Analyze, Markdown Format)
        orchestrate_pipeline(
            repository=request.repository,
            github_token=request.github_token,
            max_workers=2 # keep workers reasonable to avoid heavy CPU usage
        )
        
        # Load the generated documentation
        frontend_docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conexiones", "frontend_docs.json")
        
        if not os.path.exists(frontend_docs_path):
            raise HTTPException(status_code=500, detail="Documentation generation failed.")
            
        with open(frontend_docs_path, 'r', encoding='utf-8') as f:
            frontend_docs = json.load(f)
            
        return {
            "status": "success",
            "repo": request.repository,
            "frontend_docs": frontend_docs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))