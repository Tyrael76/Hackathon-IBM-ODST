"""
Custom Tool para Agentes: Ingesta Dinámica de Repositorios GitHub
Herramienta genérica compatible con LangChain, CrewAI y otros frameworks de agentes.

INSTRUCCIONES IMPLEMENTADAS:
1. Ingesta Dinámica y "Tools" de Agentes - Provee el código fuente al sistema de manera ágil
2. La Herramienta LangChain/CrewAI - Envuelve la lógica en una función invocable
3. Filtrado Inteligente sin Tokens - Usa mimetypes para descartar binarios, imágenes y compilados
"""

import gitAPI
from typing import Optional, List, Dict, Any


class GitHubRepoTool:
    """
    Custom Tool para extraer código fuente de repositorios GitHub.
    
    Esta herramienta permite a los agentes descargar y analizar repositorios
    de GitHub de manera dinámica, aplicando filtrado inteligente para excluir
    binarios, imágenes y compilados.
    
    Características:
    - Filtrado inteligente por MIME type (sin necesidad de tokens)
    - Caché local para optimizar llamadas
    - Extracción de dependencias
    - Exclusión automática de directorios comunes (node_modules, etc.)
    
    Uso con LangChain:
        from langchain.tools import StructuredTool
        
        tool = StructuredTool.from_function(
            func=fetch_github_repo_tool,
            name="fetch_github_repo",
            description="Extrae código fuente de un repositorio de GitHub"
        )
    
    Uso con CrewAI:
        from crewai_tools import tool
        
        @tool("fetch_github_repo")
        def github_tool(repository: str, github_token: str, extensions: list = None):
            return fetch_github_repo_tool(repository, github_token, extensions)
    
    Uso directo:
        result = fetch_github_repo_tool(
            repository="usuario/repo",
            github_token="ghp_xxxxx",
            extensions=[".py", ".js"]  # Opcional
        )
    """
    
    name: str = "fetch_github_repo"
    description: str = """
    Útil para extraer el código fuente de un repositorio de GitHub.
    Proporciona el nombre del repositorio (formato: 'usuario/repo') y el token de GitHub.
    Opcionalmente, especifica extensiones de archivo a filtrar.
    Retorna una lista de archivos con su contenido, dependencias y metadatos.
    """
    
    @staticmethod
    def run(
        repository: str,
        github_token: str,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la extracción del repositorio.
        
        Args:
            repository: Nombre completo del repositorio (usuario/repo)
            github_token: Token de autenticación de GitHub
            extensions: Lista opcional de extensiones a filtrar (ej. [".py", ".js"])
                       Si es None o vacía, usa filtrado inteligente por MIME type
            
        Returns:
            dict: Diccionario con status, información del repo y archivos extraídos
            
        Example:
            >>> tool = GitHubRepoTool()
            >>> result = tool.run(
            ...     repository="Ok-Andre/Pagina-web",
            ...     github_token="ghp_xxxxx",
            ...     extensions=[".html", ".css", ".js"]
            ... )
            >>> print(f"Archivos extraídos: {result['file_count']}")
        """
        try:
            # Si no se especifican extensiones, usar filtrado inteligente (lista vacía)
            if extensions is None:
                extensions = []
            
            # Llamar a la función de extracción
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
            "CrewAI no está instalado. "
            "Instala con: pip install crewai crewai-tools"
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
