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

def get_repository_data(repo_full_name, token, allowed_exts):
    """
    Main extraction engine.
    Receives dynamic parameters from FastAPI endpoint.
    """
    print(f"\n{'='*70}")
    print(f"🔍 [GITAPI] Starting extraction for: {repo_full_name}")
    print(f"{'='*70}")
    
    try:
        print(f"🔑 [GITAPI] Authenticating with GitHub...")
        g = Github(token)
        
        # Test authentication
        try:
            user = g.get_user()
            print(f"✅ [GITAPI] Authenticated as: {user.login}")
        except Exception as auth_error:
            print(f"❌ [GITAPI] Authentication failed: {str(auth_error)}")
            raise Exception(f"GitHub authentication failed: {str(auth_error)}")
        
        cache_name = f"cache_{repo_full_name.replace('/', '_')}.json"
        
        if os.path.exists(cache_name):
            print(f"💾 [GITAPI] Loading {repo_full_name} from local cache")
            with open(cache_name, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            print(f"✅ [GITAPI] Cache loaded: {len(cached_data)} files")
            return cached_data

        print(f"☁️ [GITAPI] Downloading {repo_full_name} from GitHub...")
        
        try:
            repo = g.get_repo(repo_full_name)
            print(f"✅ [GITAPI] Repository found: {repo.full_name}")
            print(f"   📊 Stars: {repo.stargazers_count} | Forks: {repo.forks_count}")
        except Exception as repo_error:
            print(f"❌ [GITAPI] Repository not found or inaccessible: {str(repo_error)}")
            raise Exception(f"Cannot access repository '{repo_full_name}': {str(repo_error)}")
        
        all_files = []
        
        try:
            print(f"📂 [GITAPI] Fetching repository contents...")
            contents = repo.get_contents("")
            print(f"✅ [GITAPI] Root contents fetched: {len(contents)} items")
        except Exception as contents_error:
            print(f"❌ [GITAPI] Failed to fetch contents: {str(contents_error)}")
            raise Exception(f"Cannot fetch repository contents: {str(contents_error)}")

        files_processed = 0
        files_skipped = 0
        dirs_processed = 0
        
        while contents:
            file_item = contents.pop(0)
            
            if file_item.type == "dir":
                dirs_processed += 1
                # If folder is in blacklist, skip it
                if file_item.name in BLACKLIST_DIRS:
                    print(f"⏭️ [GITAPI] Skipping blacklisted dir: {file_item.path}")
                    continue
                
                try:
                    dir_contents = repo.get_contents(file_item.path)
                    contents.extend(dir_contents)
                    if dirs_processed % 10 == 0:
                        print(f"📁 [GITAPI] Processed {dirs_processed} directories, {files_processed} files so far...")
                except Exception as dir_error:
                    print(f"⚠️ [GITAPI] Cannot access directory {file_item.path}: {str(dir_error)}")
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
                    files_processed += 1
                    if files_processed % 50 == 0:
                        print(f"✅ [GITAPI] Processed {files_processed} files...")
                except Exception as e:
                    print(f"⚠️ [GITAPI] Error processing {file_item.path}: {str(e)}")
                    files_skipped += 1
            else:
                files_skipped += 1

        print(f"\n{'='*70}")
        print(f"📊 [GITAPI] Extraction Summary:")
        print(f"   ✅ Files processed: {files_processed}")
        print(f"   ⏭️ Files skipped: {files_skipped}")
        print(f"   📁 Directories scanned: {dirs_processed}")
        print(f"{'='*70}\n")

        if files_processed == 0:
            print(f"⚠️ [GITAPI] WARNING: No files were processed!")
            print(f"   This could mean:")
            print(f"   - Repository is empty")
            print(f"   - All files are binary/too large")
            print(f"   - Extension filter is too restrictive")
            return []

        # Save cache and deliver
        print(f"💾 [GITAPI] Saving cache to {cache_name}...")
        try:
            with open(cache_name, 'w', encoding='utf-8') as f:
                json.dump(all_files, f, indent=4, ensure_ascii=False)
            print(f"✅ [GITAPI] Cache saved successfully")
        except Exception as cache_error:
            print(f"⚠️ [GITAPI] Failed to save cache: {str(cache_error)}")
        
        return all_files

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ [GITAPI] CRITICAL ERROR")
        print(f"{'='*70}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"{'='*70}\n")
        raise e  # Re-raise so FastAPI can capture the error