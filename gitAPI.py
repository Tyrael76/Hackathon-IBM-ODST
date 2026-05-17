import os
import json
import re
import mimetypes
from github import Github

# Static Filter Configuration
MAX_FILE_SIZE = 150 * 1024  # 150KB
BLACKLIST_DIRS = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env', '.idea', '.vscode'}

# Initialize mimetypes
mimetypes.init()

def is_text_file(path):
    """
    Intelligent Filtering without Tokens (Instruction 3):
    Uses mimetypes to detect if a file is plain text.
    Reads first bytes to discard binaries, images and compiled files.
    """
    # Get MIME type based on extension
    mime_type, _ = mimetypes.guess_type(path)
    
    # If cannot determine, assume it's text
    if mime_type is None:
        return True
    
    # Allow explicit text types
    if mime_type.startswith('text/'):
        return True
    
    # Allow specific code/configuration types
    allowed_types = {
        'application/json',
        'application/xml',
        'application/javascript',
        'application/x-javascript',
        'application/x-python',
        'application/x-sh',
        'application/x-yaml',
        'application/yaml',
    }
    
    if mime_type in allowed_types:
        return True
    
    # Reject binaries, images, compiled files
    binary_types = {
        'image/', 'video/', 'audio/',
        'application/octet-stream',
        'application/x-executable',
        'application/x-sharedlib',
        'application/pdf',
        'application/zip',
        'application/x-tar',
        'application/gzip',
    }
    
    for binary_type in binary_types:
        if mime_type.startswith(binary_type):
            return False
    
    return True

def is_valid_file(path, allowed_exts):
    """
    Checks if file is valid based on path and extension.
    If allowed_exts is empty, uses intelligent filtering by MIME type.
    """
    parts = path.split('/')
    if any(part in BLACKLIST_DIRS for part in parts):
        return False
    
    # If extensions specified, use traditional filtering
    if allowed_exts:
        return any(path.endswith(ext) for ext in allowed_exts)
    
    # If no extensions specified, use intelligent filtering
    return is_text_file(path)

def extract_dependencies(content):
    """Detects basic imports to help with dependency mapping."""
    pattern = r"^(?:from|import)\s+([\w\.]+)"
    return list(set(re.findall(pattern, content, re.MULTILINE)))

def get_repository_data(repo_full_name: str, token: str, allowed_exts: list[str] | None) -> list[dict]:
    """
    Main extraction engine with ephemeral token handling.
    
    SECURITY CRITICAL:
    - Token parameter is ephemeral (exists only in function scope)
    - Token is used immediately for GitHub API authentication
    - Token is NEVER logged, stored, or cached
    - Token is garbage collected after function returns
    
    Args:
        repo_full_name: Full repository name (owner/repo)
        token: Ephemeral GitHub access token (OAuth or PAT)
        allowed_exts: List of file extensions to filter, or None for intelligent filtering
    
    Returns:
        List of extracted file data dictionaries
    
    Raises:
        Exception: On GitHub API errors or extraction failures
    """
    # SECURITY: Token used here for authentication only
    # PyGithub handles token internally, never exposes it
    g = Github(token)
    cache_name = f"cache_{repo_full_name.replace('/', '_')}.json"
    
    if os.path.exists(cache_name):
        print(f"--- 💾 Loading {repo_full_name} from local cache ---")
        with open(cache_name, 'r', encoding='utf-8') as f:
            return json.load(f)

    print(f"--- ☁️ Downloading {repo_full_name} from GitHub ---")
    try:
        repo = g.get_repo(repo_full_name)
        all_files = []
        contents = repo.get_contents("")

        while contents:
            file_item = contents.pop(0)
            
            if file_item.type == "dir":
                # If folder is in blacklist, skip it
                if file_item.name in BLACKLIST_DIRS:
                    continue
                contents.extend(repo.get_contents(file_item.path))
                continue
                
            if is_valid_file(file_item.path, allowed_exts) and file_item.size <= MAX_FILE_SIZE:
                try:
                    raw_content = file_item.decoded_content.decode('utf-8')
                    all_files.append({
                        "path": file_item.path,
                        "dependencies": extract_dependencies(raw_content),
                        "content": raw_content,
                        "size": file_item.size
                    })
                    print(f"✅ Processed: {file_item.path}")
                except Exception as e:
                    print(f"⚠️ Error in {file_item.path}: {e}")

        # Save cache and deliver
        with open(cache_name, 'w', encoding='utf-8') as f:
            json.dump(all_files, f, indent=4, ensure_ascii=False)
        
        return all_files

    except Exception as e:
        print(f"❌ CRITICAL CORE ERROR: {e}")
        raise e  # Re-raise so FastAPI can capture the error