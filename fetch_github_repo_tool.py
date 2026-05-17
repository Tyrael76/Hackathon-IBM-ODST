"""
Custom Tool for Agents: Dynamic GitHub Repository Ingestion
Generic tool compatible with LangChain, CrewAI and other agent frameworks.

IMPLEMENTED INSTRUCTIONS:
1. Dynamic Ingestion and Agent "Tools" - Provides source code to the system in an agile way
2. LangChain/CrewAI Tool - Wraps logic in an invocable function
3. Intelligent Filtering without Tokens - Uses mimetypes to discard binaries, images and compiled files
"""

import gitAPI
from typing import Optional, List, Dict, Any


class GitHubRepoTool:
    """
    Custom Tool to extract source code from GitHub repositories.
    
    This tool allows agents to download and analyze GitHub repositories
    dynamically, applying intelligent filtering to exclude binaries,
    images and compiled files.
    
    Features:
    - Intelligent filtering by MIME type (no tokens needed)
    - Local cache to optimize calls
    - Dependency extraction
    - Automatic exclusion of common directories (node_modules, etc.)
    
    Usage with LangChain:
        from langchain.tools import StructuredTool
        
        tool = StructuredTool.from_function(
            func=fetch_github_repo_tool,
            name="fetch_github_repo",
            description="Extracts source code from a GitHub repository"
        )
    
    Usage with CrewAI:
        from crewai_tools import tool
        
        @tool("fetch_github_repo")
        def github_tool(repository: str, github_token: str, extensions: list = None):
            return fetch_github_repo_tool(repository, github_token, extensions)
    
    Direct usage:
        result = fetch_github_repo_tool(
            repository="user/repo",
            github_token="ghp_xxxxx",
            extensions=[".py", ".js"]  # Optional
        )
    """
    
    name: str = "fetch_github_repo"
    description: str = """
    Useful for extracting source code from a GitHub repository.
    Provide the repository name (format: 'user/repo') and GitHub token.
    Optionally, specify file extensions to filter.
    Returns a list of files with their content, dependencies and metadata.
    """
    
    @staticmethod
    def run(
        repository: str,
        github_token: str,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes repository extraction.
        
        Args:
            repository: Full repository name (user/repo)
            github_token: GitHub authentication token
            extensions: Optional list of extensions to filter (e.g. [".py", ".js"])
                       If None or empty, uses intelligent filtering by MIME type
            
        Returns:
            dict: Dictionary with status, repo info and extracted files
            
        Example:
            >>> tool = GitHubRepoTool()
            >>> result = tool.run(
            ...     repository="Ok-Andre/Pagina-web",
            ...     github_token="ghp_xxxxx",
            ...     extensions=[".html", ".css", ".js"]
            ... )
            >>> print(f"Files extracted: {result['file_count']}")
        """
        try:
            print(f"\n{'='*70}")
            print(f"🚀 [FETCH_TOOL] Starting extraction for: {repository}")
            print(f"{'='*70}")
            
            # If no extensions specified, use intelligent filtering (empty list)
            if extensions is None:
                extensions = []
                print(f"🔧 [FETCH_TOOL] Using intelligent MIME-type filtering")
            else:
                print(f"🔧 [FETCH_TOOL] Using extension filter: {extensions}")
            
            # Validate token format
            if not github_token or len(github_token) < 10:
                error_msg = "Invalid GitHub token format. Token must be at least 10 characters."
                print(f"❌ [FETCH_TOOL] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "repo": repository,
                    "file_count": 0,
                    "files": [],
                    "error_type": "INVALID_TOKEN"
                }
            
            # Validate repository format
            if '/' not in repository:
                error_msg = f"Invalid repository format. Expected 'owner/repo', got '{repository}'"
                print(f"❌ [FETCH_TOOL] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "repo": repository,
                    "file_count": 0,
                    "files": [],
                    "error_type": "INVALID_REPO_FORMAT"
                }
            
            # Call extraction function
            print(f"📡 [FETCH_TOOL] Calling gitAPI.get_repository_data...")
            files = gitAPI.get_repository_data(
                repo_full_name=repository,
                token=github_token,
                allowed_exts=extensions
            )
            
            print(f"✅ [FETCH_TOOL] gitAPI returned {len(files) if files else 0} files")
            
            if not files:
                error_msg = "No valid files were found in the repository. Possible causes: empty repository, all files are binaries, or the extension filter is too restrictive."
                print(f"⚠️ [FETCH_TOOL] {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "repo": repository,
                    "file_count": 0,
                    "files": [],
                    "error_type": "NO_FILES_FOUND"
                }
            
            print(f"\n{'='*70}")
            print(f"✅ [FETCH_TOOL] Extraction successful!")
            print(f"   Repository: {repository}")
            print(f"   Files extracted: {len(files)}")
            print(f"{'='*70}\n")
            
            return {
                "status": "success",
                "repo": repository,
                "file_count": len(files),
                "files": files,
                "message": f"Extraction successful: {len(files)} files processed"
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            
            print(f"\n{'='*70}")
            print(f"❌ [FETCH_TOOL] EXCEPTION CAUGHT")
            print(f"{'='*70}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"\nFull traceback:")
            print(error_trace)
            print(f"{'='*70}\n")
            
            return {
                "status": "error",
                "message": f"Error extracting repository: {str(e)}",
                "repo": repository,
                "file_count": 0,
                "files": [],
                "error_type": type(e).__name__,
                "error_details": error_trace
            }


def fetch_github_repo_tool(
    repository: str,
    github_token: str,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Wrapper function to use directly with agent frameworks.
    
    This is the main function to integrate with LangChain,
    CrewAI or any other agent framework.
    
    Args:
        repository: Full repository name (user/repo)
        github_token: GitHub authentication token
        extensions: Optional list of extensions to filter
        
    Returns:
        dict: Extraction result with files and metadata
        
    Example:
        >>> result = fetch_github_repo_tool(
        ...     repository="Ok-Andre/Pagina-web",
        ...     github_token="ghp_xxxxx",
        ...     extensions=[".html", ".css", ".js"]
        ... )
        >>> print(f"Status: {result['status']}")
        >>> print(f"Files: {result['file_count']}")
    """
    tool = GitHubRepoTool()
    return tool.run(repository, github_token, extensions)


# Ejemplo de integración con LangChain (requiere langchain instalado)
def create_langchain_tool():
    """
    Creates a tool compatible with LangChain.
    
    Requires: pip install langchain
    
    Returns:
        StructuredTool: Ready to use tool with LangChain agents
    """
    try:
        from langchain.tools import StructuredTool
        from pydantic import BaseModel, Field
        
        class GitHubRepoInput(BaseModel):
            repository: str = Field(description="Repository name (user/repo)")
            github_token: str = Field(description="GitHub token")
            extensions: Optional[List[str]] = Field(
                default=None,
                description="List of extensions (optional)"
            )
        
        return StructuredTool.from_function(
            func=fetch_github_repo_tool,
            name="fetch_github_repo",
            description=GitHubRepoTool.description,
            args_schema=GitHubRepoInput
        )
    except ImportError:
        raise ImportError(
            "LangChain is not installed. "
            "Install with: pip install langchain"
        )


# Ejemplo de integración con CrewAI (requiere crewai instalado)
def create_crewai_tool():
    """
    Creates a tool compatible with CrewAI.
    
    Requires: pip install crewai crewai-tools
    
    Returns:
        Tool: Ready to use tool with CrewAI agents
    """
    try:
        from crewai_tools import tool
        
        @tool("fetch_github_repo")
        def github_repo_tool(
            repository: str,
            github_token: str,
            extensions: list = None
        ) -> dict:
            """Extracts source code from a GitHub repository."""
            return fetch_github_repo_tool(repository, github_token, extensions)
        
        return github_repo_tool
    except ImportError:
        raise ImportError(
            "CrewAI is not installed. "
            "Install with: pip install crewai crewai-tools"
        )




# Made with Bob