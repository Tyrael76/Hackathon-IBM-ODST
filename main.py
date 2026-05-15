from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import gitAPI

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
        # Call extraction logic
        data = gitAPI.get_repository_data(
            repo_full_name=request.repository,
            token=request.github_token,
            allowed_exts=request.extensions
        )
        
        if not data:
            raise HTTPException(status_code=404, detail="No files found with those extensions.")
            
        return {
            "status": "success",
            "repo": request.repository,
            "file_count": len(data),
            "files": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))