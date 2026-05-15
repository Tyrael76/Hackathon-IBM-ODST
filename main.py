from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import gitAPI  # Importamos tu script anterior

app = FastAPI(title="Extractor API para Bob")

# CONFIGURACIÓN DE CORS: Vital para que el Front-end de Rafiki no sea bloqueado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL del Front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definimos qué datos esperamos recibir del Front
class RepoRequest(BaseModel):
    github_token: str
    repository: str
    extensions: List[str] | None = None

@app.get("/")
def home():
    return {"message": "Servidor de Extracción Activo"}

@app.post("/extract")
async def extract_repository(request: RepoRequest):
    """
    Recibe el token, el repo y las extensiones desde el Front.
    """
    try:
        # Llamamos a tu lógica (asegúrate de que get_repository_data acepte estos parámetros)
        data = gitAPI.get_repository_data(
            repo_full_name=request.repository,
            token=request.github_token,
            allowed_exts=request.extensions
        )
        
        if not data:
            raise HTTPException(status_code=404, detail="No se encontraron archivos con esas extensiones.")
            
        return {
            "status": "success",
            "repo": request.repository,
            "file_count": len(data),
            "files": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))