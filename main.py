from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import os
import sys
import json
import io
from dotenv import load_dotenv

# Fix for Windows console emoji printing (UnicodeEncodeError)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add root directory to sys.path to ensure we can import agents
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

from agents.compression_path.parser_core import orchestrate_pipeline
from agents.crew_agents import run_crew_analysis, explain_file_direct, generate_full_documentation

app = FastAPI(title="GitHub Extractor API for Bob")

# CORS CONFIGURATION: Essential for Rafiki's frontend to not be blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# Define what data we expect to receive from the frontend
class RepoRequest(BaseModel):
    repository: str
    branch: str | None = None
    filters: dict | None = None
    extensions: List[str] | None = None

class ExplainRequest(BaseModel):
    file_path: str
    file_content: str

@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "index.html"))

@app.post("/extract")
async def extract_repository(request: RepoRequest):
    """
    Receives repo and extensions from frontend. Token is loaded server-side.
    """
    print(f"\n{'='*70}")
    print(f"🌐 [MAIN API] New extraction request received")
    print(f"{'='*70}")
    print(f"   Repository: {request.repository}")
    print(f"   Branch: {request.branch or 'default'}")
    print(f"   Filters: {request.filters}")
    print(f"   Extensions: {request.extensions}")
    print(f"{'='*70}\n")
    
    try:
        # Validate inputs
        if not GITHUB_TOKEN:
            error_msg = "GitHub token is not configured on the server. Set GITHUB_TOKEN in .env"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        if not request.repository:
            error_msg = "Repository name is required"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if '/' not in request.repository:
            error_msg = f"Invalid repository format. Expected 'owner/repo', got '{request.repository}'"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        output_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "compression_path", "para_uriel.json")
        print(f"📁 [MAIN API] Output will be saved to: {output_json}")
        
        # Increase workers for faster processing (uses available CPU cores)
        import multiprocessing
        max_workers = min(multiprocessing.cpu_count(), 8)  # Maximum 8 workers
        
        print(f"\n{'='*70}")
        print(f"⚡ [MAIN API] Starting pipeline orchestration")
        print(f"   Workers: {max_workers}")
        print(f"{'='*70}\n")
        
        result = orchestrate_pipeline(
            repository=request.repository,
            github_token=GITHUB_TOKEN,
            output_file=output_json,
            max_workers=max_workers
        )
        
        # Check if orchestrate_pipeline returned an error
        if isinstance(result, str) and result.startswith("Error"):
            error_msg = f"Pipeline failed: {result}"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Load the generated AST
        if not os.path.exists(output_json):
            error_msg = f"AST generation failed - output file not created at: {output_json}"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"✅ [MAIN API] AST file generated, loading...")
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                ast_data = json.load(f)
            print(f"✅ [MAIN API] AST loaded successfully")
        except json.JSONDecodeError as json_error:
            error_msg = f"Failed to parse AST JSON: {str(json_error)}"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"\n{'='*70}")
        print(f"🤖 [MAIN API] Running CrewAI analysis")
        print(f"{'='*70}\n")
        
        # Call CrewAI orchestration
        filters = request.filters or {}
        try:
            crew_results = run_crew_analysis(ast_data, filters)
            print(f"✅ [MAIN API] CrewAI analysis complete!")
        except Exception as crew_error:
            error_msg = f"CrewAI analysis failed: {str(crew_error)}"
            print(f"❌ [MAIN API] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"\n{'='*70}")
        print(f"✅ [MAIN API] EXTRACTION COMPLETE")
        print(f"   Repository: {request.repository}")
        print(f"   Results: {len(crew_results)} pages generated")
        print(f"{'='*70}\n")
        
        return {
            "status": "success",
            "repo": request.repository,
            "frontend_docs": {"pages": crew_results}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        print(f"\n{'='*70}")
        print(f"❌ [MAIN API] UNHANDLED EXCEPTION")
        print(f"{'='*70}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nFull traceback:")
        print(error_trace)
        print(f"{'='*70}\n")
        
        error_detail = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": error_trace
        }
        raise HTTPException(status_code=500, detail=json.dumps(error_detail, indent=2))

@app.post("/explain-file")
async def explain_file(request: ExplainRequest):
    """
    Explains a specific file content directly using the LLM for token efficiency.
    """
    try:
        explanation = explain_file_direct(request.file_path, request.file_content)
        return {
            "status": "success",
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-docs")
async def download_documentation(request: RepoRequest):
    """
    Generates and downloads complete technical documentation in Markdown format.
    Includes Mermaid diagrams and mitigation section.
    
    Zero Waste: Direct download without intermediate storage.
    """
    print(f"\n{'='*70}")
    print(f"📥 [DOWNLOAD DOCS] New documentation download request")
    print(f"{'='*70}")
    print(f"   Repository: {request.repository}")
    print(f"   Branch: {request.branch or 'default'}")
    print(f"   Filters: {request.filters}")
    print(f"{'='*70}\n")
    
    try:
        # Validate inputs
        if not GITHUB_TOKEN:
            error_msg = "GitHub token is not configured on the server. Set GITHUB_TOKEN in .env"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        if not request.repository:
            error_msg = "Repository name is required"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if '/' not in request.repository:
            error_msg = f"Invalid repository format. Expected 'owner/repo', got '{request.repository}'"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Step 1: Run AST pipeline (reuse /extract logic)
        output_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "compression_path", "para_uriel.json")
        print(f"📁 [DOWNLOAD DOCS] AST output: {output_json}")
        
        import multiprocessing
        max_workers = min(multiprocessing.cpu_count(), 8)
        
        print(f"\n{'='*70}")
        print(f"⚡ [DOWNLOAD DOCS] Starting AST pipeline")
        print(f"   Workers: {max_workers}")
        print(f"{'='*70}\n")
        
        result = orchestrate_pipeline(
            repository=request.repository,
            github_token=GITHUB_TOKEN,
            output_file=output_json,
            max_workers=max_workers
        )
        
        # Verify pipeline result
        if isinstance(result, str) and result.startswith("Error"):
            error_msg = f"Pipeline failed: {result}"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Load generated AST
        if not os.path.exists(output_json):
            error_msg = f"AST generation failed - output file not created"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"✅ [DOWNLOAD DOCS] AST file generated, loading...")
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                ast_data = json.load(f)
            print(f"✅ [DOWNLOAD DOCS] AST loaded successfully")
        except json.JSONDecodeError as json_error:
            error_msg = f"Failed to parse AST JSON: {str(json_error)}"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Step 2: Generate full documentation
        print(f"\n{'='*70}")
        print(f"📝 [DOWNLOAD DOCS] Generating full documentation")
        print(f"{'='*70}\n")
        
        filters = request.filters or {}
        try:
            markdown_content = generate_full_documentation(ast_data, filters)
            print(f"✅ [DOWNLOAD DOCS] Documentation generated!")
            print(f"   Length: {len(markdown_content)} characters")
        except Exception as doc_error:
            error_msg = f"Documentation generation failed: {str(doc_error)}"
            print(f"❌ [DOWNLOAD DOCS] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Step 3: Prepare download response
        # Convert string to bytes for StreamingResponse
        markdown_bytes = markdown_content.encode('utf-8')
        markdown_stream = io.BytesIO(markdown_bytes)
        
        # Generate filename based on the repository
        repo_name = request.repository.replace('/', '_')
        filename = f"ODST_Technical_Documentation_{repo_name}.md"
        
        print(f"\n{'='*70}")
        print(f"✅ [DOWNLOAD DOCS] DOCUMENTATION READY FOR DOWNLOAD")
        print(f"   Repository: {request.repository}")
        print(f"   Filename: {filename}")
        print(f"   Size: {len(markdown_bytes)} bytes")
        print(f"{'='*70}\n")
        
        # Return StreamingResponse with appropriate headers
        return StreamingResponse(
            markdown_stream,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(markdown_bytes)),
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        print(f"\n{'='*70}")
        print(f"❌ [DOWNLOAD DOCS] UNHANDLED EXCEPTION")
        print(f"{'='*70}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nFull traceback:")
        print(error_trace)
        print(f"{'='*70}\n")
        
        error_detail = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": error_trace
        }
        raise HTTPException(status_code=500, detail=json.dumps(error_detail, indent=2))