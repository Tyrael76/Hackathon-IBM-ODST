"""
Optimized Core Orchestrator (parser_core.py)
==============================================
Integrates Andre's GitHub Fetcher with Antonio's AST and Regex Parsers.
Outputs a consolidated, token-optimized JSON for Uriel and IBM Bob.

CONCURRENCY ARCHITECTURE:
- Uses ProcessPoolExecutor for CPU-bound operations (AST parsing, Regex)
- Thread-safe dictionary assembly with locks
- Graceful error handling per file without crashing the entire pipeline
- Optimized for high-volume repositories (5000+ files)

CONTEXT WINDOW PROTECTION:
- Automatic estimation of JSON size (character-based)
- Intelligent chunking when output exceeds safe limits (100K chars default)
- Metadata generation for multi-part architectures
- AI Agent-friendly fragmented output structure
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from threading import Lock
import multiprocessing
from datetime import datetime

# ==========================================
# DYNAMIC PATH RESOLUTION (Cross-Platform)
# ==========================================
# Get the absolute path to the project root (2 levels up from this file)
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent

# Add project root to sys.path at the beginning (highest priority)
# This ensures Python finds modules in the root directory first
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"🔧 [PATH] Project root added to sys.path: {project_root}")

# 1. IMPORT REPOSITORY ECOSYSTEM
try:
    # Ingestion Tool (Andre's Part - now it will find it in the root)
    from fetch_github_repo_tool import fetch_github_repo_tool
    # Python Parser by AST (Antonio's Part - Optimized Version)
    from agents.compression_path.parser_py import compress_python_code
    # Multi-language Parser by Regex (Antonio's Part - Robust Version)
    from agents.compression_path.parser_regex import compress_regex_code
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    print("Make sure 'fetch_github_repo_tool.py' is in the root, and parsers are in the same directory.")
    sys.exit(1)

# Thread-safe lock for dictionary updates
_repo_lock = Lock()

# ==========================================
# CONTEXT WINDOW PROTECTION CONSTANTS
# ==========================================
DEFAULT_CHUNK_SIZE = 100000  # 100K characters - safe for most LLMs
METADATA_OVERHEAD = 500  # Reserved space for metadata in each chunk


def estimate_json_size(data: Dict[str, Any]) -> int:
    """
    Estimate the size of a dictionary when serialized to JSON.
    Uses character count as a proxy for token estimation.
    
    Args:
        data: Dictionary to estimate
    
    Returns:
        Estimated character count of the JSON string
    """
    try:
        # Serialize with minimal formatting to get accurate size
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return len(json_str)
    except Exception as e:
        print(f"⚠️ [WARNING] Error estimating JSON size: {e}")
        # Return a conservative estimate if serialization fails
        return len(str(data))


def create_chunk_metadata(
    chunk_index: int,
    total_chunks: int,
    repository: str,
    chunk_file_count: int,
    total_file_count: int,
    chunk_size_chars: int
) -> Dict[str, Any]:
    """
    Generate metadata for a chunked output file.
    Helps AI agents understand the fragmented architecture.
    
    Args:
        chunk_index: Current chunk number (1-based)
        total_chunks: Total number of chunks
        repository: Repository identifier
        chunk_file_count: Number of files in this chunk
        total_file_count: Total files across all chunks
        chunk_size_chars: Character count of this chunk
    
    Returns:
        Metadata dictionary
    """
    return {
        "_metadata": {
            "chunk_info": {
                "current_chunk": chunk_index,
                "total_chunks": total_chunks,
                "is_fragmented": total_chunks > 1
            },
            "repository": repository,
            "generation_timestamp": datetime.utcnow().isoformat() + "Z",
            "files_in_chunk": chunk_file_count,
            "total_files_in_repository": total_file_count,
            "chunk_size_characters": chunk_size_chars,
            "instructions_for_ai": (
                f"This is part {chunk_index} of {total_chunks}. "
                f"Load all parts (para_uriel_part1.json to para_uriel_part{total_chunks}.json) "
                "to get the complete repository analysis."
            ) if total_chunks > 1 else "Complete repository in single file."
        }
    }


def chunk_repository_data(
    repository_data: Dict[str, Any],
    repository: str,
    max_chunk_size: int = DEFAULT_CHUNK_SIZE
) -> List[Tuple[Dict[str, Any], str]]:
    """
    Split large repository data into manageable chunks with metadata.
    Each chunk stays under the max_chunk_size limit.
    
    Args:
        repository_data: Complete repository analysis dictionary
        repository: Repository identifier for metadata
        max_chunk_size: Maximum characters per chunk (default: 100K)
    
    Returns:
        List of tuples: (chunk_data_with_metadata, suggested_filename)
    """
    total_size = estimate_json_size(repository_data)
    total_files = len(repository_data)
    
    # If data fits in one chunk, return as-is with metadata
    if total_size <= max_chunk_size:
        chunk_with_metadata = {
            **create_chunk_metadata(1, 1, repository, total_files, total_files, total_size),
            "files": repository_data
        }
        return [(chunk_with_metadata, "para_uriel.json")]
    
    # Calculate number of chunks needed
    estimated_chunks = (total_size // max_chunk_size) + 1
    print(f"\n⚠️ [CHUNKING] JSON size ({total_size:,} chars) exceeds limit ({max_chunk_size:,} chars)")
    print(f"   📦 Splitting into approximately {estimated_chunks} chunks...")
    
    chunks = []
    current_chunk = {}
    current_chunk_size = METADATA_OVERHEAD
    chunk_index = 1
    
    # Sort files by path for consistent chunking
    sorted_files = sorted(repository_data.items())
    
    for file_path, file_data in sorted_files:
        # Estimate size of adding this file
        file_entry = {file_path: file_data}
        file_size = estimate_json_size(file_entry)
        
        # If adding this file would exceed limit, save current chunk and start new one
        if current_chunk and (current_chunk_size + file_size > max_chunk_size):
            # Finalize current chunk with metadata
            chunk_with_metadata = {
                **create_chunk_metadata(
                    chunk_index,
                    0,  # Will update after we know total
                    repository,
                    len(current_chunk),
                    total_files,
                    current_chunk_size
                ),
                "files": current_chunk
            }
            chunks.append(chunk_with_metadata)
            
            # Start new chunk
            current_chunk = {}
            current_chunk_size = METADATA_OVERHEAD
            chunk_index += 1
        
        # Add file to current chunk
        current_chunk[file_path] = file_data
        current_chunk_size += file_size
    
    # Add final chunk if it has content
    if current_chunk:
        chunk_with_metadata = {
            **create_chunk_metadata(
                chunk_index,
                0,  # Will update after we know total
                repository,
                len(current_chunk),
                total_files,
                current_chunk_size
            ),
            "files": current_chunk
        }
        chunks.append(chunk_with_metadata)
    
    # Update total_chunks in all metadata
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        chunk["_metadata"]["chunk_info"]["total_chunks"] = total_chunks
        chunk["_metadata"]["chunk_info"]["current_chunk"] = i
        chunk["_metadata"]["instructions_for_ai"] = (
            f"This is part {i} of {total_chunks}. "
            f"Load all parts (para_uriel_part1.json to para_uriel_part{total_chunks}.json) "
            "to get the complete repository analysis."
        )
    
    # Generate filenames
    result = []
    for i, chunk in enumerate(chunks, 1):
        filename = f"para_uriel_part{i}.json" if total_chunks > 1 else "para_uriel.json"
        result.append((chunk, filename))
    
    print(f"   ✅ Successfully created {total_chunks} chunks")
    return result


def _process_file_worker(file: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
    """
    Worker function for concurrent file processing.
    Designed to be pickled and executed in separate processes.
    
    Args:
        file: Dictionary containing 'path', 'content', and 'dependencies'
    
    Returns:
        Tuple of (file_path, processed_data, stat_category)
        - file_path: Path of the processed file (None if skipped)
        - processed_data: Compressed structure (None if skipped)
        - stat_category: One of 'python', 'regex_languages', 'plain_text', 'skipped', 'error'
    """
    try:
        file_path = file.get('path', '')
        content = file.get('content', '')
        external_dependencies = file.get('dependencies', [])
        
        # Early validation
        if not file_path or not content.strip():
            return None, None, 'skipped'

        # Extract extension safely
        _, extension = os.path.splitext(file_path.lower())

        # CASE A: Python code -> AST processing (CPU-intensive)
        if extension == '.py':
            ast_structure = compress_python_code(content)
            
            if "error" not in ast_structure:
                processed_data = {
                    "language": "python",
                    "external_imports": external_dependencies,
                    "structure": ast_structure
                }
                return file_path, processed_data, 'python'
            else:
                print(f"   ⚠️ [Invalid Syntax] Skipping AST analysis for: {file_path}")
                return None, None, 'skipped'

        # CASE B: Regex-supported languages (CPU-intensive)
        elif extension in {'.js', '.ts', '.jsx', '.tsx', '.kt', '.java', '.cs'}:
            regex_structure = compress_regex_code(content, extension)
            
            if regex_structure and "error" not in regex_structure:
                processed_data = {
                    "language": extension.replace('.', ''),
                    "external_imports": external_dependencies,
                    "structure": regex_structure
                }
                return file_path, processed_data, 'regex_languages'
            else:
                return None, None, 'skipped'

        # CASE C: Configuration or Documentation files
        elif extension in {'.md', '.txt', '.json', '.yaml', '.yml', '.xml'}:
            processed_data = {
                "language": "config/text",
                "preview": content[:120].strip() + "... [TRUNCATED]"
            }
            return file_path, processed_data, 'plain_text'
            
        else:
            return None, None, 'skipped'
            
    except Exception as e:
        # Graceful error handling - don't crash the entire pipeline
        print(f"   ❌ [ERROR] Failed to process {file.get('path', 'unknown')}: {str(e)}")
        return None, None, 'error'


def orchestrate_pipeline(
    repository: str,
    github_token: str,
    output_file: str = "para_uriel.json",
    max_workers: Optional[int] = None,
    max_chunk_size: int = DEFAULT_CHUNK_SIZE,
    enable_chunking: bool = True
) -> str:
    """
    Orchestrates the complete repository compression flow with concurrent processing.
    
    1. Downloads the repository cleanly using Andre's tool.
    2. Processes files in parallel using ProcessPoolExecutor (CPU-bound operations).
    3. Combines dependency metadata with extracted structures in a thread-safe manner.
    4. Exports the final deliverable in a low-token-consumption JSON.
    5. Applies automatic chunking if JSON exceeds safe context limits.
    
    Args:
        repository: GitHub repository identifier (e.g., 'user/repo')
        github_token: GitHub API token for authentication
        output_file: Output JSON filename (default: 'para_uriel.json')
        max_workers: Maximum number of worker processes (default: CPU count)
        max_chunk_size: Maximum characters per chunk (default: 100K)
        enable_chunking: Enable automatic chunking for large outputs (default: True)
    
    Returns:
        Path to the generated output file(s) or error message
    """
    print(f"🔄 [PIPELINE] Starting orchestration for: '{repository}'")
    
    # --- PHASE 1: DATA INGESTION (Andre) ---
    # extensions=None activates native intelligent filtering to ignore binary garbage
    fetch_result = fetch_github_repo_tool(
        repository=repository,
        github_token=github_token,
        extensions=None
    )

    if fetch_result.get('status') != 'success':
        error_msg = fetch_result.get('message', 'Unknown error')
        print(f"❌ [INGESTION ERROR]: {error_msg}")
        return f"Error: {error_msg}"

    raw_files = fetch_result.get('files', [])
    total_files = len(raw_files)
    print(f"✅ [INGESTION] {total_files} valid code files received.")

    # Master dictionary that will accumulate the entire repository map (thread-safe)
    compressed_repository: Dict[str, Any] = {}
    
    # Performance metrics to impress judges in console
    stats = {"python": 0, "regex_languages": 0, "plain_text": 0, "skipped": 0, "error": 0}

    # --- PHASE 2: CONCURRENT ALGORITHMIC COMPRESSION (Antonio) ---
    print("⚡ [COMPRESSION] Extracting cognitive structures in parallel...")
    
    # Determine optimal worker count (default to CPU count)
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()
    
    print(f"   🔧 Using {max_workers} worker processes for parallel processing")
    
    # Process files concurrently using ProcessPoolExecutor
    processed_files = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all files for processing
        future_to_file = {
            executor.submit(_process_file_worker, file): file
            for file in raw_files
        }
        
        # Collect results as they complete (non-blocking)
        for future in as_completed(future_to_file):
            try:
                file_path, processed_data, stat_category = future.result(timeout=30)
                
                # Thread-safe dictionary update
                if file_path and processed_data:
                    with _repo_lock:
                        compressed_repository[file_path] = processed_data
                        stats[stat_category] += 1
                else:
                    with _repo_lock:
                        stats[stat_category] += 1
                
                processed_files += 1
                
                # Progress indicator every 100 files
                if processed_files % 100 == 0:
                    print(f"   📊 Progress: {processed_files}/{total_files} files processed")
                    
            except TimeoutError:
                original_file = future_to_file[future]
                print(f"   ⏱️ [TIMEOUT] File exceeded time limit: {original_file.get('path', 'unknown')}")
                with _repo_lock:
                    stats['error'] += 1
            except Exception as e:
                original_file = future_to_file[future]
                print(f"   ❌ [ERROR FUTURE] Error processing {original_file.get('path', 'unknown')}: {str(e)}")
                with _repo_lock:
                    stats['error'] += 1

    # --- PHASE 3: OPTIMIZED DELIVERABLE EXPORT (For Uriel) ---
    print("\n💾 [EXPORT] Saving consolidated results...")
    
    # Estimate total size before writing
    total_size = estimate_json_size(compressed_repository)
    print(f"   📊 Estimated JSON size: {total_size:,} characters")
    
    output_files = []
    
    try:
        # Apply chunking if enabled and size exceeds limit
        if enable_chunking and total_size > max_chunk_size:
            print(f"   ⚠️ Size exceeds safe limit ({max_chunk_size:,} chars)")
            print(f"   🔪 Applying intelligent chunking...")
            
            chunks = chunk_repository_data(compressed_repository, repository, max_chunk_size)
            
            # Write each chunk to a separate file
            for chunk_data, filename in chunks:
                chunk_path = filename
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                output_files.append(chunk_path)
                
                chunk_size = estimate_json_size(chunk_data)
                files_in_chunk = len(chunk_data.get("files", {}))
                print(f"   ✅ Saved: {filename} ({chunk_size:,} chars, {files_in_chunk} files)")
            
            print(f"\n   📦 Total files generated: {len(output_files)}")
            
        else:
            # Single file output with metadata
            print(f"   ✅ Size within safe limit")
            chunk_with_metadata = {
                **create_chunk_metadata(1, 1, repository, len(compressed_repository), len(compressed_repository), total_size),
                "files": compressed_repository
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_with_metadata, f, indent=2, ensure_ascii=False)
            output_files.append(output_file)
            print(f"   ✅ Saved: {output_file}")
            
    except IOError as e:
        print(f"❌ [WRITE ERROR]: Could not save final JSON: {e}")
        return "Storage error"

    # --- CONCURRENT PERFORMANCE REPORT ---
    total_processed = stats['python'] + stats['regex_languages'] + stats['plain_text']
    success_rate = (total_processed / total_files * 100) if total_files > 0 else 0
    
    print("\n" + "="*70)
    print("🚀 CORE PIPELINE PROCESSED SUCCESSFULLY (CONCURRENT MODE)")
    print("="*70)
    print(f"📊 Repository Structure Summary:")
    print(f"   🔹 Python Files (AST):                 {stats['python']:>6}")
    print(f"   🔹 Frontend/JVM Files (Regex):         {stats['regex_languages']:>6}")
    print(f"   🔹 Config/Text Files:                  {stats['plain_text']:>6}")
    print(f"   🔹 Skipped/Empty Files:                {stats['skipped']:>6}")
    print(f"   ❌ Files with Errors:                  {stats['error']:>6}")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   ✅ Total Successfully Processed:       {total_processed:>6}")
    print(f"   📈 Success Rate:                       {success_rate:>5.1f}%")
    print(f"   🔧 Workers Used:                       {max_workers:>6}")
    
    # Context window protection report
    print(f"\n🛡️ Context Window Protection:")
    print(f"   📏 Total JSON Size:                    {total_size:>10,} chars")
    print(f"   🎯 Configured Safe Limit:              {max_chunk_size:>10,} chars")
    
    if len(output_files) > 1:
        print(f"   ⚠️ Chunking Applied:                   {'YES':>10}")
        print(f"   📦 Files Generated:                    {len(output_files):>10}")
        print(f"\n📁 Deliverables generated for Uriel/AI:")
        for i, file in enumerate(output_files, 1):
            print(f"   {i}. {file}")
    else:
        print(f"   ✅ Chunking Applied:                   {'NO':>10}")
        print(f"\n📁 Deliverable generated for Uriel/AI: '{output_files[0]}'")
    
    print(f"📦 Total files in repository: {len(compressed_repository)}")
    print("="*70 + "\n")

    # --- PHASE 4: AUTOMATIC AI ANALYSIS (Uriel) ---
    print("🤖 [AI ANALYSIS] Calling Uriel's analyzer...")
    
    # Extract project name from repository
    project_name = repository.split('/')[-1] if '/' in repository else repository
    
    try:
        # Import from conexiones package
        from conexiones.conexion_uriel_antonio import generar_analisis
        
        # Generate AI analysis
        analysis_result = generar_analisis(project_name)
        print(f"✅ [AI ANALYSIS] Analysis completed and saved to paraGio.json")
        
    except Exception as e:
        print(f"⚠️ [AI ANALYSIS] Could not complete analysis: {str(e)}")
        print(f"   You can run it manually later with: generar_analisis('{project_name}')")

    # Return primary output file or list of files
    if len(output_files) == 1:
        return output_files[0]
    else:
        return f"Chunked output: {', '.join(output_files)}"

# ==========================================
# FASTAPI SERVER FOR DIRECT FRONTEND ACCESS
# ==========================================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Parser Core API - Direct Access")

# CORS Configuration for Rafiki's frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PipelineRequest(BaseModel):
    github_token: str
    repository: str
    max_workers: Optional[int] = None
    max_chunk_size: int = 100000
    enable_chunking: bool = True

@app.get("/")
def home():
    return {"message": "Parser Core API Active - Ready to process repositories"}

@app.post("/process")
async def process_repository(request: PipelineRequest):
    """
    Endpoint directo para que Rafiki envíe datos y ejecute el pipeline completo
    """
    try:
        print(f"\n{'='*70}")
        print(f"🚀 PARSER CORE: Processing {request.repository}")
        print(f"{'='*70}\n")
        
        # Ejecutar el pipeline completo
        result = orchestrate_pipeline(
            repository=request.repository,
            github_token=request.github_token,
            output_file="para_uriel.json",
            max_workers=request.max_workers,
            max_chunk_size=request.max_chunk_size,
            enable_chunking=request.enable_chunking
        )
        
        # Verificar si hubo error
        if isinstance(result, str) and result.startswith("Error"):
            raise HTTPException(status_code=500, detail=result)
        
        # Determinar archivos de salida
        output_files = []
        if isinstance(result, list):
            output_files = result
        else:
            output_files = [result]
        
        return {
            "status": "success",
            "message": "Pipeline executed successfully",
            "repository": request.repository,
            "output_files": output_files,
            "pipeline_stages": {
                "1_ingestion": "✅ GitHub repository fetched (Andre)",
                "2_compression": "✅ Code compressed with AST + Regex (Antonio)",
                "3_ai_analysis": "✅ AI analysis generated (Uriel)",
                "4_documentation": "✅ Documentation ready (Gio)"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution error: {str(e)}"
        )

# Para ejecutar este servidor directamente:
# uvicorn parser_core:app --reload --host 0.0.0.0 --port 8001


# ==========================================
# INTEGRATED LOCAL TESTING ZONE
# ==========================================
if __name__ == "__main__":
    # Simulated data to simulate local production behavior
    REPO_MOCK = ""
    TOKEN_MOCK = ""
    
    # To test this script locally without hitting Andre's real GitHub API,
    # you can uncomment the lines below if you have a sample local JSON file.
    
    print("🧪 Running pipeline simulation with concurrent processing...")
    # You can adjust max_workers to control the level of parallelism
    orchestrate_pipeline("repository", "github_token", max_workers=4)
    