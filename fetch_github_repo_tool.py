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
            # If no extensions specified, use intelligent filtering (empty list)
            if extensions is None:
                extensions = []
            
            # Call extraction function
            files = gitAPI.get_repository_data(
                repo_full_name=repository,
                token=github_token,
                allowed_exts=extensions
            )
            
            if not files:
                return {
                    "status": "error",
                    "message": "No se encontraron archivos válidos en el repositorio",
                    "repo": repository,
                    "file_count": 0,
                    "files": []
                }
            
            return {
                "status": "success",
                "repo": repository,
                "file_count": len(files),
                "files": files,
                "message": f"Extracción exitosa: {len(files)} archivos procesados"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error al extraer repositorio: {str(e)}",
                "repo": repository,
                "file_count": 0,
                "files": []
            }


def fetch_github_repo_tool(
    repository: str,
    github_token: str,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Función wrapper para usar directamente con frameworks de agentes.
    
    Esta es la función principal que debes usar para integrar con LangChain,
    CrewAI o cualquier otro framework de agentes.
    
    Args:
        repository: Nombre completo del repositorio (usuario/repo)
        github_token: Token de autenticación de GitHub
        extensions: Lista opcional de extensiones a filtrar
        
    Returns:
        dict: Resultado de la extracción con archivos y metadatos
        
    Example:
        >>> result = fetch_github_repo_tool(
        ...     repository="Ok-Andre/Pagina-web",
        ...     github_token="ghp_xxxxx",
        ...     extensions=[".html", ".css", ".js"]
        ... )
        >>> print(f"Status: {result['status']}")
        >>> print(f"Archivos: {result['file_count']}")
    """
    tool = GitHubRepoTool()
    return tool.run(repository, github_token, extensions)


# Ejemplo de integración con LangChain (requiere langchain instalado)
def create_langchain_tool():
    """
    Crea una herramienta compatible con LangChain.
    
    Requiere: pip install langchain
    
    Returns:
        StructuredTool: Herramienta lista para usar con agentes de LangChain
    """
    try:
        from langchain.tools import StructuredTool
        from pydantic import BaseModel, Field
        
        class GitHubRepoInput(BaseModel):
            repository: str = Field(description="Nombre del repositorio (usuario/repo)")
            github_token: str = Field(description="Token de GitHub")
            extensions: Optional[List[str]] = Field(
                default=None,
                description="Lista de extensiones (opcional)"
            )
        
        return StructuredTool.from_function(
            func=fetch_github_repo_tool,
            name="fetch_github_repo",
            description=GitHubRepoTool.description,
            args_schema=GitHubRepoInput
        )
    except ImportError:
        raise ImportError(
            "LangChain no está instalado. "
            "Instala con: pip install langchain"
        )


# Ejemplo de integración con CrewAI (requiere crewai instalado)
def create_crewai_tool():
    """
    Crea una herramienta compatible con CrewAI.
    
    Requiere: pip install crewai crewai-tools
    
    Returns:
        Tool: Herramienta lista para usar con agentes de CrewAI
    """
    try:
        from crewai_tools import tool
        
        @tool("fetch_github_repo")
        def github_repo_tool(
            repository: str,
            github_token: str,
            extensions: list = None
        ) -> dict:
            """Extrae código fuente de un repositorio de GitHub."""
            return fetch_github_repo_tool(repository, github_token, extensions)
        
        return github_repo_tool
    except ImportError:
        raise ImportError(
            "CrewAI is not installed. "
            "Install with: pip install crewai crewai-tools"
        )


    
    print("\n=== Ejemplo 2: Con filtrado inteligente (sin extensiones) ===")
    result2 = fetch_github_repo_tool(
        repository="Ok-Andre/Pagina-web",
        github_token=token,
        extensions=None  # Usa filtrado inteligente por MIME type
    )
    print(f"Status: {result2['status']}")
    print(f"Archivos procesados: {result2['file_count']}")
    
    print("\n=== Ejemplo 3: Uso con clase ===")
    tool = GitHubRepoTool()
    result3 = tool.run(
        repository="Ok-Andre/Pagina-web",
        github_token=token,
        extensions=[".py"]
    )
    print(f"Status: {result3['status']}")
    print(f"Mensaje: {result3['message']}")

# Made with Bob